#!/usr/bin/env python3
"""
scripts/prefetch_satellite_cache.py — Populate TMDb/OMDb cache for organized Satellite films

Organized Satellite films were sorted before classify.py existed, so they have no
cache entries. This means rank_category_tentpoles.py can't score keywords, vote counts,
or text signals — all films are capped at director:3 + decade:2 = 5.

This script iterates library_audit.csv, finds Satellite films with cache misses,
and queries TMDb + OMDb to populate both caches. Uses the same client and cache
key format as classify.py.

Usage:
    python scripts/prefetch_satellite_cache.py                    # all Satellite categories
    python scripts/prefetch_satellite_cache.py --category Giallo  # one category
    python scripts/prefetch_satellite_cache.py --dry-run          # show what would be fetched

NEVER moves files. Read-only except for cache writes.
"""

import sys
import csv
import re
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.parser import FilenameParser
from lib.tmdb import TMDbClient
from lib.omdb import OMDbClient


# ---------------------------------------------------------------------------
# Title cleaning — mirrors classify.py._clean_title_for_api()
# ---------------------------------------------------------------------------

def _clean_title_for_api(title: str) -> str:
    from lib.normalization import _strip_format_signals, strip_release_tags

    clean = re.sub(r'\s*\[.+?\]\s*', ' ', title)
    clean = _strip_format_signals(clean)
    clean = strip_release_tags(clean)

    residual_patterns = [
        r'\b(metro|pc|sr|moc|kl|doc|vo)\b',
        r'\b\d{3,4}p\b',
        r'\b(spanish|french|italian|german|japanese|chinese|vostfr)\b',
        r'\b(itunes|upscale|uncensored|satrip|vhsrip|xvid|mp3|2audio)\b',
    ]
    for pattern in residual_patterns:
        clean = re.sub(pattern, '', clean, flags=re.IGNORECASE)

    clean = re.sub(r'\s*\(\s*\)', '', clean)
    return ' '.join(clean.split()).strip()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description='Prefetch TMDb/OMDb cache for organized Satellite films'
    )
    parser.add_argument('--category', help='Limit to one Satellite category')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print what would be fetched without calling APIs')
    parser.add_argument('--retry-nulls', action='store_true',
                        help='Re-query films with cached null results (prior failed lookups)')
    parser.add_argument('--audit', default='output/library_audit.csv')
    parser.add_argument('--config', default='config.yaml')
    args = parser.parse_args()

    audit_path = Path(args.audit)
    if not audit_path.exists():
        print(f"Error: {audit_path} not found — run audit.py first", file=sys.stderr)
        sys.exit(1)

    # Load config
    import yaml
    config_path = Path(args.config)
    if not config_path.exists():
        config_path = Path('config_external.yaml')
    config = yaml.safe_load(open(config_path))

    tmdb_key = config.get('tmdb_api_key')
    omdb_key = config.get('omdb_api_key')

    if not tmdb_key and not omdb_key:
        print("Error: no API keys found in config", file=sys.stderr)
        sys.exit(1)

    tmdb_cache_path = Path('output/tmdb_cache.json')
    omdb_cache_path = Path('output/omdb_cache.json')

    tmdb = TMDbClient(tmdb_key, tmdb_cache_path) if tmdb_key else None
    omdb = OMDbClient(omdb_key, omdb_cache_path) if omdb_key else None

    # Load audit and find Satellite films with cache misses
    film_parser = FilenameParser()
    rows = []
    with open(audit_path, encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row.get('tier') != 'Satellite':
                continue
            if args.category and row.get('subdirectory') != args.category:
                continue
            rows.append(row)

    print(f"Satellite films in audit: {len(rows)}")

    # Identify cache misses (and optionally cached nulls)
    to_fetch = []
    already_cached = 0
    cached_null = 0
    unparseable = 0

    for row in rows:
        fname = row['filename']
        try:
            metadata = film_parser.parse(fname)
        except Exception:
            unparseable += 1
            continue

        if not metadata.title or not metadata.year:
            unparseable += 1
            continue

        clean_title = _clean_title_for_api(metadata.title)
        cache_key = f"{clean_title}|{metadata.year}"

        # A "hit" means the key exists AND the value is non-null
        tmdb_in_cache = tmdb and cache_key in tmdb.cache
        omdb_in_cache = omdb and cache_key in omdb.cache
        tmdb_null = tmdb_in_cache and not tmdb.cache.get(cache_key)
        omdb_null = omdb_in_cache and not omdb.cache.get(cache_key)

        need_tmdb = tmdb and (not tmdb_in_cache or (args.retry_nulls and tmdb_null))
        need_omdb = omdb and (not omdb_in_cache or (args.retry_nulls and omdb_null))

        if not need_tmdb and not need_omdb:
            if tmdb_null or omdb_null:
                cached_null += 1
            else:
                already_cached += 1
            continue

        if tmdb_null or omdb_null:
            cached_null += 1  # count even if we're going to retry

        to_fetch.append({
            'filename': fname,
            'category': row.get('subdirectory', ''),
            'title': clean_title,
            'year': metadata.year,
            'cache_key': cache_key,
            'need_tmdb': need_tmdb,
            'need_omdb': need_omdb,
            'is_retry': tmdb_null or omdb_null,
        })

    print(f"Already cached (non-null): {already_cached}")
    print(f"Cached null (prior failed lookups): {cached_null}")
    print(f"Unparseable (no title/year): {unparseable}")
    print(f"To fetch: {len(to_fetch)}" + (" (includes null retries)" if args.retry_nulls else ""))

    if args.dry_run:
        print()
        for film in to_fetch:
            apis = []
            if film['need_tmdb']:
                apis.append('TMDb')
            if film['need_omdb']:
                apis.append('OMDb')
            retry_label = ' [retry null]' if film.get('is_retry') else ''
            print(f"  [{film['category']}] {film['title']} ({film['year']}) — {', '.join(apis)}{retry_label}")
        return

    if not to_fetch:
        print("Nothing to fetch.")
        return

    # Fetch
    print()
    tmdb_ok = tmdb_null = omdb_ok = omdb_null = 0

    for i, film in enumerate(to_fetch, 1):
        title, year = film['title'], film['year']
        category = film['category']
        print(f"[{i}/{len(to_fetch)}] {category} | {title} ({year})", end='', flush=True)

        if film['need_tmdb'] and tmdb:
            # Remove stale null entry so search_film doesn't short-circuit on it
            if film['cache_key'] in tmdb.cache and not tmdb.cache[film['cache_key']]:
                del tmdb.cache[film['cache_key']]
            result = tmdb.search_film(title, year)
            if result:
                tmdb_ok += 1
                kw = len(result.get('keywords') or [])
                print(f"  tmdb:ok(kw={kw})", end='')
            else:
                tmdb_null += 1
                print(f"  tmdb:null", end='')

        if film['need_omdb'] and omdb:
            if film['cache_key'] in omdb.cache and not omdb.cache[film['cache_key']]:
                del omdb.cache[film['cache_key']]
            result = omdb.search_film(title, year)
            if result:
                omdb_ok += 1
                print(f"  omdb:ok", end='')
            else:
                omdb_null += 1
                print(f"  omdb:null", end='')

        print()

        # Save periodically
        if i % 25 == 0:
            if tmdb:
                tmdb._save_cache()
            if omdb:
                omdb._save_cache()
            print(f"  [checkpoint saved at {i}]")

    # Final save
    if tmdb:
        tmdb._save_cache()
    if omdb:
        omdb._save_cache()

    print()
    print(f"Done. TMDb: {tmdb_ok} found, {tmdb_null} null. OMDb: {omdb_ok} found, {omdb_null} null.")
    print(f"Re-run rank_category_tentpoles.py --all to update rankings.")


if __name__ == '__main__':
    main()
