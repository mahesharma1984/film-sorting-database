#!/usr/bin/env python3
"""
scripts/build_corpus.py — Corpus builder + anomaly detector (Issue #38)

Two modes:

  --audit CATEGORY   Read current folder contents, cross-reference cache data,
                     flag films that don't match the category's routing gates.
                     Output: anomaly report + draft CSV rows for unresolved films.

  --add TITLE YEAR   Look up film in caches, prompt for canonical_tier + source
                     citation, append to the appropriate corpora CSV.

Usage:
    python scripts/build_corpus.py --audit Giallo
    python scripts/build_corpus.py --add "Deep Red" 1975 --category Giallo
    python scripts/build_corpus.py --audit "Brazilian Exploitation"
"""

import sys
import csv
import json
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.parser import FilenameParser
from lib.normalization import normalize_for_lookup
from lib.constants import SATELLITE_ROUTING_RULES

logging.basicConfig(level=logging.WARNING, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent.parent
CORPORA_DIR = PROJECT_ROOT / 'data' / 'corpora'
AUDIT_CSV = PROJECT_ROOT / 'output' / 'library_audit.csv'
TMDB_CACHE = PROJECT_ROOT / 'output' / 'tmdb_cache.json'
OMDB_CACHE = PROJECT_ROOT / 'output' / 'omdb_cache.json'

CORPUS_FIELDS = ['title', 'year', 'imdb_id', 'director', 'country', 'canonical_tier', 'source', 'notes']


# ---------------------------------------------------------------------------
# Cache reader
# ---------------------------------------------------------------------------

def _load_caches() -> tuple[Dict, Dict]:
    """Load TMDb and OMDb caches. Returns (tmdb_cache, omdb_cache)."""
    tmdb: Dict = {}
    omdb: Dict = {}
    if TMDB_CACHE.exists():
        with open(TMDB_CACHE, 'r', encoding='utf-8') as f:
            tmdb = json.load(f)
    if OMDB_CACHE.exists():
        with open(OMDB_CACHE, 'r', encoding='utf-8') as f:
            omdb = json.load(f)
    return tmdb, omdb


def _lookup_in_caches(title: str, year: Optional[int], tmdb: Dict, omdb: Dict) -> Dict:
    """
    Look up film data from caches. Returns dict with director, countries, genres, imdb_id.
    Follows the same merge priority as classify.py: OMDb > TMDb for director/country.
    """
    result = {'director': None, 'countries': [], 'genres': [], 'imdb_id': None}

    cache_key = f"{title}|{year if year else 'None'}"
    tmdb_data = tmdb.get(cache_key)
    omdb_data = omdb.get(cache_key)

    if tmdb_data:
        result['director'] = tmdb_data.get('director')
        result['countries'] = tmdb_data.get('countries', [])
        result['genres'] = tmdb_data.get('genres', [])

    if omdb_data:
        if omdb_data.get('director'):
            result['director'] = omdb_data['director']  # OMDb wins
        if omdb_data.get('countries'):
            result['countries'] = omdb_data['countries']  # OMDb wins
        if omdb_data.get('imdb_id'):
            result['imdb_id'] = omdb_data['imdb_id']

    return result


# ---------------------------------------------------------------------------
# Anomaly detection
# ---------------------------------------------------------------------------

CATEGORY_ALIASES = {
    'giallo': 'Giallo',
    'brazilian exploitation': 'Brazilian Exploitation',
    'american exploitation': 'American Exploitation',
    'european sexploitation': 'European Sexploitation',
    'blaxploitation': 'Blaxploitation',
    'pinku eiga': 'Pinku Eiga',
    'hong kong action': 'Hong Kong Action',
    'japanese exploitation': 'Japanese Exploitation',
    'french new wave': 'French New Wave',
    'indie cinema': 'Indie Cinema',
    'classic hollywood': 'Classic Hollywood',
    'american new hollywood': 'American New Hollywood',
    'japanese new wave': 'Japanese New Wave',
    'hong kong new wave': 'Hong Kong New Wave',
    'hong kong category iii': 'Hong Kong Category III',
    'cult oddities': 'Cult Oddities',
    'music films': 'Music Films',
    'giallo': 'Giallo',
}


def _normalize_category(name: str) -> str:
    key = name.strip().lower()
    return CATEGORY_ALIASES.get(key, name.strip())


def _check_anomaly(title: str, year: Optional[int], cache_data: Dict, category: str) -> List[tuple]:
    """
    Check whether a film's cache data violates the category's routing gates.
    Returns a list of (severity, message) tuples:
      severity='HARD' — structural gate failure (country/decade), strong evidence of misrouting
      severity='SOFT' — director not in routing list (weak signal; routing list is not exhaustive)
    Empty list = no anomaly detected.
    """
    rules = SATELLITE_ROUTING_RULES.get(category, {})
    if not rules:
        return []

    anomalies = []
    country_codes = rules.get('country_codes', [])
    decades = rules.get('decades', [])
    directors = rules.get('directors', [])

    countries = cache_data.get('countries', [])
    director = (cache_data.get('director') or '').lower()
    decade = f"{(year // 10) * 10}s" if year else None

    # Country gate (skip if category has no country restriction)
    if country_codes and countries:
        if not any(c in country_codes for c in countries):
            anomalies.append((
                'HARD',
                f"country={','.join(countries)} not in expected {country_codes}"
            ))

    # Decade gate
    if decade and decades and decade not in decades:
        anomalies.append(('HARD', f"decade={decade} outside expected {decades}"))

    # Director check — SOFT signal only.
    # The routing director list is not exhaustive; many legitimate films by
    # unlisted directors belong in the category. Flag for human review only.
    if director and directors:
        director_match = any(d in director for d in directors)
        if not director_match:
            anomalies.append((
                'SOFT',
                f"director='{cache_data.get('director')}' not in {category} routing list"
            ))

    return anomalies


# ---------------------------------------------------------------------------
# Corpus file helpers
# ---------------------------------------------------------------------------

def _corpus_path(category: str) -> Path:
    slug = category.lower().replace(' ', '-').replace('/', '-')
    return CORPORA_DIR / f"{slug}.csv"


def _load_corpus(category: str) -> List[Dict]:
    path = _corpus_path(category)
    if not path.exists():
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def _corpus_imdb_ids(category: str) -> set:
    return {r['imdb_id'] for r in _load_corpus(category) if r.get('imdb_id')}


def _append_to_corpus(category: str, row: Dict) -> None:
    path = _corpus_path(category)
    is_new = not path.exists()
    CORPORA_DIR.mkdir(parents=True, exist_ok=True)
    with open(path, 'a', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CORPUS_FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow({k: row.get(k, '') for k in CORPUS_FIELDS})
    print(f"  → Appended to {path.relative_to(PROJECT_ROOT)}")


# ---------------------------------------------------------------------------
# --audit mode
# ---------------------------------------------------------------------------

def cmd_audit(category: str) -> None:
    category = _normalize_category(category)
    print(f"\n=== Corpus Audit: {category} ===\n")

    if not AUDIT_CSV.exists():
        print(f"ERROR: {AUDIT_CSV} not found. Run: python audit.py")
        sys.exit(1)

    tmdb, omdb = _load_caches()
    parser = FilenameParser()

    # Load existing corpus to mark what's already confirmed
    existing_corpus = _load_corpus(category)
    corpus_imdb_ids = {r['imdb_id'] for r in existing_corpus if r.get('imdb_id')}
    corpus_keys = {
        (normalize_for_lookup(r['title']), int(r['year']))
        for r in existing_corpus
        if r.get('title') and r.get('year')
    }

    # Read audit CSV — filter to this category
    films = []
    with open(AUDIT_CSV, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row.get('subdirectory') == category and row.get('tier') == 'Satellite':
                films.append(row)

    if not films:
        print(f"No films found in Satellite/{category}/ in library_audit.csv")
        print("Run: python audit.py  to rebuild the audit CSV first.")
        return

    print(f"Found {len(films)} films in Satellite/{category}/\n")

    anomalies = []
    confirmed = []
    unresolvable = []
    draft_rows = []

    for row in films:
        filename = row['filename']
        meta = parser.parse(filename)
        title = meta.title
        year = meta.year

        # Prefer IMDb ID from filename
        imdb_id = meta.imdb_id

        # Try cache lookup
        cache_data = _lookup_in_caches(title, year, tmdb, omdb)
        if cache_data.get('imdb_id'):
            imdb_id = cache_data['imdb_id']

        # Check if already in corpus
        key = (normalize_for_lookup(title), year) if year else None
        in_corpus = (imdb_id and imdb_id in corpus_imdb_ids) or (key and key in corpus_keys)

        # Run anomaly check
        flags = _check_anomaly(title, year, cache_data, category)

        entry = {
            'filename': filename,
            'title': title,
            'year': year,
            'director': cache_data.get('director'),
            'countries': ','.join(cache_data.get('countries', [])),
            'genres': ','.join(cache_data.get('genres', [])),
            'imdb_id': imdb_id or '',
            'in_corpus': in_corpus,
            'anomalies': flags,
        }

        has_hard = any(sev == 'HARD' for sev, _ in flags)
        if has_hard:
            anomalies.append(entry)
        elif flags:  # SOFT-only
            confirmed.append(entry)  # tentatively OK, soft flags stored in anomalies field
            entry['soft_flags'] = flags
        elif cache_data.get('director') or cache_data.get('countries'):
            confirmed.append(entry)
        else:
            unresolvable.append(entry)

        # Build draft CSV row for films not yet in corpus
        if not in_corpus:
            draft_rows.append({
                'title': title or '',
                'year': year or '',
                'imdb_id': imdb_id or '',
                'director': cache_data.get('director') or '',
                'country': (cache_data.get('countries') or [''])[0],
                'canonical_tier': '',
                'source': '',
                'notes': 'DRAFT — needs curation',
            })

    # Print HARD anomalies
    if anomalies:
        print(f"{'='*60}")
        print(f"HARD ANOMALIES — structural gate failures ({len(anomalies)} films):")
        print(f"{'='*60}")
        for e in anomalies:
            print(f"\n  {e['title']} ({e['year']})")
            print(f"    File: {e['filename']}")
            print(f"    Dir:  {e['director']}  |  Countries: {e['countries']}  |  Genres: {e['genres']}")
            if e['imdb_id']:
                print(f"    IMDb: {e['imdb_id']}")
            for sev, msg in e['anomalies']:
                prefix = '*** HARD' if sev == 'HARD' else '  ~ SOFT'
                print(f"    {prefix}: {msg}")
    else:
        print("No hard anomalies detected (country/decade gates all pass).")

    # Print SOFT flags (director not in routing list)
    soft_films = [e for e in confirmed if e.get('soft_flags')]
    if soft_films:
        print(f"\n{'='*60}")
        print(f"SOFT FLAGS — director not in routing list ({len(soft_films)} films, needs review):")
        print(f"{'='*60}")
        for e in soft_films:
            print(f"  {e['title']} ({e['year']}) — dir: {e['director']} — {e['countries']}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"SUMMARY")
    print(f"{'='*60}")
    print(f"  Total in folder:    {len(films)}")
    print(f"  Anomalies:          {len(anomalies)}")
    print(f"  Confirmed (no flag):{len(confirmed)}")
    print(f"  Unresolvable:       {len(unresolvable)}  (no cache data)")
    print(f"  Already in corpus:  {sum(1 for f in films if _in_corpus_check(f, corpus_imdb_ids, corpus_keys, parser))}")

    # Write draft rows
    if draft_rows:
        draft_path = PROJECT_ROOT / 'output' / f"corpus_draft_{category.lower().replace(' ', '_')}.csv"
        with open(draft_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CORPUS_FIELDS)
            writer.writeheader()
            writer.writerows(draft_rows)
        print(f"\n  Draft CSV (films not yet in corpus): {draft_path.relative_to(PROJECT_ROOT)}")
        print(f"  Edit canonical_tier + source fields, then use --add to load them.")


def _in_corpus_check(row: Dict, corpus_imdb_ids: set, corpus_keys: set, parser: FilenameParser) -> bool:
    meta = parser.parse(row['filename'])
    key = (normalize_for_lookup(meta.title), meta.year) if meta.year else None
    imdb_id = meta.imdb_id
    return (imdb_id and imdb_id in corpus_imdb_ids) or (key and key in corpus_keys)


# ---------------------------------------------------------------------------
# --add mode
# ---------------------------------------------------------------------------

def cmd_add(title: str, year: int, category: str) -> None:
    category = _normalize_category(category)
    print(f"\n=== Add to Corpus: {category} ===")
    print(f"Film: {title} ({year})\n")

    tmdb, omdb = _load_caches()
    cache_data = _lookup_in_caches(title, year, tmdb, omdb)

    print(f"Cache data found:")
    print(f"  Director:  {cache_data.get('director') or '(not found)'}")
    print(f"  Countries: {cache_data.get('countries') or '(not found)'}")
    print(f"  Genres:    {cache_data.get('genres') or '(not found)'}")
    print(f"  IMDb ID:   {cache_data.get('imdb_id') or '(not found)'}")

    # Check for anomalies against category gates
    flags = _check_anomaly(title, year, cache_data, category)
    if flags:
        print(f"\n  *** Potential anomaly for {category}: ***")
        for flag in flags:
            print(f"      {flag}")
        confirm = input("\n  Add anyway? [y/N]: ").strip().lower()
        if confirm != 'y':
            print("  Cancelled.")
            return

    # Get canonical_tier
    print("\nCanonical tier:")
    print("  1 = core canon (must-have genre exemplars)")
    print("  2 = important reference (significant but secondary)")
    print("  3 = genre texture (fills out the movement)")
    tier_input = input("Tier [1/2/3]: ").strip()
    if tier_input not in ('1', '2', '3'):
        print("Invalid tier. Cancelled.")
        return

    # Get source citation
    source = input("Source citation (e.g. 'Koven 2006 p.34', 'Wikipedia giallo list'): ").strip()
    if not source:
        print("Source required. Cancelled.")
        return

    notes = input("Notes (optional): ").strip()

    # Get IMDb ID if not in cache
    imdb_id = cache_data.get('imdb_id') or ''
    if not imdb_id:
        imdb_id = input("IMDb ID (e.g. tt0065472, or blank): ").strip()

    # Confirm country
    countries = cache_data.get('countries', [])
    country = countries[0] if countries else ''
    if not country:
        country = input("Primary country (ISO 2-letter, e.g. IT): ").strip()

    row = {
        'title': title,
        'year': year,
        'imdb_id': imdb_id,
        'director': cache_data.get('director') or '',
        'country': country,
        'canonical_tier': tier_input,
        'source': source,
        'notes': notes,
    }

    print(f"\nAdding: {row}")
    confirm = input("Confirm? [Y/n]: ").strip().lower()
    if confirm in ('', 'y'):
        _append_to_corpus(category, row)
        print(f"Done. Added '{title} ({year})' to {category} corpus.")
    else:
        print("Cancelled.")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Build and audit per-category corpora')
    sub = parser.add_subparsers(dest='cmd')

    audit_p = sub.add_parser('--audit', help='Audit current folder against category gates')
    audit_p.add_argument('category', help='Category name (e.g. Giallo)')

    add_p = sub.add_parser('--add', help='Add a film to corpus interactively')
    add_p.add_argument('title', help='Film title')
    add_p.add_argument('year', type=int, help='Release year')
    add_p.add_argument('--category', required=True, help='Target category')

    # Support argparse-style: python build_corpus.py --audit Giallo
    args = sys.argv[1:]
    if len(args) >= 2 and args[0] == '--audit':
        cmd_audit(' '.join(args[1:]))
    elif len(args) >= 3 and args[0] == '--add':
        # --add TITLE YEAR [--category CAT]
        title_parts = []
        year_val = None
        category = None
        i = 1
        while i < len(args):
            if args[i] == '--category' and i + 1 < len(args):
                category = args[i + 1]
                i += 2
            elif year_val is None and args[i].isdigit() and len(args[i]) == 4:
                year_val = int(args[i])
                i += 1
            else:
                title_parts.append(args[i])
                i += 1
        if not category:
            print("--add requires --category CATEGORY")
            sys.exit(1)
        if not year_val:
            print("--add requires a 4-digit year argument")
            sys.exit(1)
        cmd_add(' '.join(title_parts), year_val, category)
    else:
        print(__doc__)
        sys.exit(1)


if __name__ == '__main__':
    main()
