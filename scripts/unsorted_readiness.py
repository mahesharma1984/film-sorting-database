#!/usr/bin/env python3
"""
scripts/unsorted_readiness.py — Data-readiness report for the Unsorted queue

Groups Unsorted films by how much data is available, from most actionable
(year + director + API data) down to least (no year at all). Helps the
curator prioritise which films to work on next.

Usage:
    python scripts/unsorted_readiness.py                    # print summary + markdown
    python scripts/unsorted_readiness.py --csv              # also write CSV
    python scripts/unsorted_readiness.py --no-year-too      # include no-year group

Output:
    output/unsorted_readiness.md — grouped markdown report
"""

import sys
import csv
import json
import argparse
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_manifest(path: Path):
    if not path.exists():
        print(f"Manifest not found: {path} — run classify.py first")
        sys.exit(1)
    rows = []
    with open(path, encoding='utf-8') as f:
        for r in csv.DictReader(f):
            rows.append(r)
    return rows


def load_cache(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}


def cache_key(title: str, year) -> str:
    return f"{title}|{year if year else 'None'}"


# ---------------------------------------------------------------------------
# Readiness levels
# ---------------------------------------------------------------------------

# R0 — no year extracted
# R1 — year only (no director, no API data)
# R2a — year + director from filename, no API data
# R2b — year + API data (country or genres), but no director
# R3 — year + director + country/genres from API (full data, no rule matched)

def classify_readiness(row: dict, tmdb_cache: dict, omdb_cache: dict) -> dict:
    """Return enriched dict with readiness level and available data fields."""
    reason = row.get('reason', '')
    title = row.get('title', '')
    year = row.get('year', '')
    director = row.get('director', '') or ''
    filename = row.get('filename', '')

    # Pull API data from caches
    key = cache_key(title, year)
    tmdb = tmdb_cache.get(key) or {}
    omdb = omdb_cache.get(key) or {}

    has_year = bool(year)
    has_director = bool(director)
    api_countries = tmdb.get('countries') or omdb.get('countries') or []
    api_genres = tmdb.get('genres') or []
    api_director = tmdb.get('director') or omdb.get('director') or ''
    has_api_country = bool(api_countries)
    has_api_genres = bool(api_genres)
    has_api_data = bool(tmdb or omdb)

    # Determine level
    if not has_year:
        level = 'R0'
        label = 'No year'
        priority = 0
    elif reason == 'unsorted_no_match':
        if has_api_country and has_api_genres:
            level = 'R3'
            label = 'Year + director + country + genres — no rule matched'
            priority = 4
        elif has_api_data:
            level = 'R2b'
            label = 'Year + director + partial API data — no rule matched'
            priority = 3
        else:
            level = 'R2a'
            label = 'Year + director (filename only) — no rule matched'
            priority = 2
    elif reason in ('unsorted_insufficient_data', 'unsorted_no_director'):
        if has_api_data:
            level = 'R1+'
            label = 'Year + API data but no director'
            priority = 1
        else:
            level = 'R1'
            label = 'Year only — no API data, no director'
            priority = 1
    else:
        level = 'R0'
        label = 'No year'
        priority = 0

    return {
        'filename': filename,
        'title': title,
        'year': year,
        'director': director or api_director,
        'countries': ','.join(api_countries[:3]),
        'genres': ','.join(api_genres[:3]),
        'reason': reason,
        'level': level,
        'label': label,
        'priority': priority,
    }


# ---------------------------------------------------------------------------
# Report generation
# ---------------------------------------------------------------------------

LEVEL_ORDER = ['R3', 'R2b', 'R2a', 'R1+', 'R1', 'R0']

LEVEL_DESCRIPTIONS = {
    'R3':  'Year + director + country + genres — most actionable (taxonomy gap only)',
    'R2b': 'Year + director + partial API data — needs routing rule',
    'R2a': 'Year + director (filename) — API missed, may respond to --enrich',
    'R1+': 'Year + API country/genre, no director — Satellite routing degraded',
    'R1':  'Year only — no API data, no director — manual enrichment needed',
    'R0':  'No year — supplements, trailers, interviews',
}


def write_report(enriched: list, output_path: Path, include_r0: bool,
                 non_film_count: int = 0):
    by_level = defaultdict(list)
    for r in enriched:
        by_level[r['level']].append(r)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    total = len(enriched)
    actionable = sum(len(by_level[l]) for l in ('R3', 'R2b', 'R2a'))

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Unsorted Queue — Data Readiness Report\n\n")
        f.write("Generated by `scripts/unsorted_readiness.py`\n\n")
        f.write(f"**{total} films | {actionable} actionable (have year + director)**\n\n")
        if non_film_count:
            f.write(f"*{non_film_count} non-film supplements/trailers excluded from counts — "
                    f"use `park_supplements.py` to move them.*\n\n")
        f.write("---\n\n")

        # Summary table
        f.write("## Summary\n\n")
        f.write("| Level | Count | Description |\n")
        f.write("|---|---|---|\n")
        for level in LEVEL_ORDER:
            if level == 'R0' and not include_r0:
                count = len(by_level.get(level, []))
                f.write(f"| {level} | {count} | {LEVEL_DESCRIPTIONS[level]} (omitted — use --no-year-too) |\n")
                continue
            count = len(by_level.get(level, []))
            if count:
                f.write(f"| {level} | {count} | {LEVEL_DESCRIPTIONS[level]} |\n")

        f.write("\n---\n\n")

        # Detail sections
        for level in LEVEL_ORDER:
            if level == 'R0' and not include_r0:
                continue
            rows = sorted(by_level.get(level, []), key=lambda r: (r['director'] or r['title']))
            if not rows:
                continue

            f.write(f"## {level} — {LEVEL_DESCRIPTIONS[level]}\n\n")
            f.write(f"{len(rows)} films\n\n")

            if level in ('R3', 'R2b', 'R2a'):
                f.write("| Director | Title | Year | Country | Genres | Action |\n")
                f.write("|---|---|---|---|---|---|\n")
                for r in rows:
                    action = _suggest_action(r)
                    f.write(f"| {r['director']} | {r['title']} | {r['year']} | "
                            f"{r['countries'] or '—'} | {r['genres'] or '—'} | {action} |\n")
            elif level in ('R1+', 'R1'):
                f.write("| Title | Year | Country | Genres | Note |\n")
                f.write("|---|---|---|---|---|\n")
                for r in rows:
                    note = 'Has country/genre' if (r['countries'] or r['genres']) else 'Run --enrich'
                    f.write(f"| {r['title']} | {r['year']} | "
                            f"{r['countries'] or '—'} | {r['genres'] or '—'} | {note} |\n")
            else:
                f.write("| Filename |\n")
                f.write("|---|\n")
                for r in rows:
                    f.write(f"| {r['filename']} |\n")

            f.write("\n")

    print(f"Wrote readiness report to {output_path}")


def _suggest_action(row: dict) -> str:
    """Suggest a curatorial action for R2/R3 films."""
    director = row.get('director', '').lower()
    countries = row.get('countries', '')
    year = row.get('year', '')
    genres = row.get('genres', '')

    # Known non-film content
    if director.startswith('trailer'):
        return 'Exclude (trailer)'

    return 'Add SORTING_DATABASE entry'


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Data-readiness report for Unsorted queue'
    )
    parser.add_argument('--manifest', default='output/sorting_manifest.csv')
    parser.add_argument('--output', default='output/unsorted_readiness.md')
    parser.add_argument('--csv', action='store_true', help='Also write CSV output')
    parser.add_argument('--no-year-too', action='store_true',
                        help='Include R0 (no-year) films in the report')
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    output_path = Path(args.output)

    manifest = load_manifest(manifest_path)
    tmdb_cache = load_cache(Path('output/tmdb_cache.json'))
    omdb_cache = load_cache(Path('output/omdb_cache.json'))

    # Non-film supplements (filtered from pipeline by non-film pre-filter, Issue #33)
    non_films = [r for r in manifest if r.get('reason') == 'non_film_supplement'
                 or r.get('tier') == 'Non-Film']

    # Only process Unsorted films (tier = Unsorted)
    unsorted = [r for r in manifest if r.get('tier') == 'Unsorted']
    print(f"Processing {len(unsorted)} Unsorted films"
          + (f" ({len(non_films)} non-film supplements excluded)" if non_films else "") + "...")

    enriched = [classify_readiness(r, tmdb_cache, omdb_cache) for r in unsorted]

    # Summary to stdout
    from collections import Counter
    counts = Counter(r['level'] for r in enriched)
    print()
    print("=" * 50)
    print("UNSORTED DATA READINESS")
    print("=" * 50)
    for level in LEVEL_ORDER:
        if counts.get(level):
            print(f"  {level:<5} {counts[level]:>4}  {LEVEL_DESCRIPTIONS[level][:55]}")
    print(f"  {'Total':<5} {len(enriched):>4}")
    if non_films:
        print(f"  {'Non-Film':<5} {len(non_films):>4}  Supplements/trailers (excluded from readiness counts)")
    print("=" * 50)
    print()

    write_report(enriched, output_path, include_r0=args.no_year_too,
                 non_film_count=len(non_films))

    if args.csv:
        csv_path = output_path.with_suffix('.csv')
        fieldnames = ['level', 'priority', 'director', 'title', 'year',
                      'countries', 'genres', 'reason', 'filename']
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL,
                                    extrasaction='ignore')
            writer.writeheader()
            writer.writerows(sorted(enriched, key=lambda r: (-r['priority'], r['director'] or r['title'])))
        print(f"Wrote CSV to {csv_path}")


if __name__ == '__main__':
    main()
