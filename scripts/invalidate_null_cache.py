#!/usr/bin/env python3
"""
Invalidate null/empty cache entries to force re-query with cleaned titles.
Run this AFTER deploying Phase 1 title cleaning changes.

Usage:
    python scripts/invalidate_null_cache.py conservative      # Recommended
    python scripts/invalidate_null_cache.py aggressive        # If conservative doesn't improve enough
    python scripts/invalidate_null_cache.py --validate-matches  # Report suspect title mismatches (Issue #21)
"""
import difflib
import json
import shutil
from pathlib import Path
from datetime import datetime


def backup_cache(cache_path):
    """Backup cache to cache_backups/ before modification"""
    backup_dir = Path('output/cache_backups')
    backup_dir.mkdir(exist_ok=True, parents=True)

    cache_name = Path(cache_path).stem
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f"{cache_name}_backup_{timestamp}.json"
    backup_path = backup_dir / backup_filename

    shutil.copy2(cache_path, backup_path)
    print(f"✓ Backed up to {backup_path}")
    return backup_path


def invalidate_null_entries(cache_path, aggressive=False):
    """
    Remove null cache entries to force re-query.

    Conservative: Only remove entries where director=None AND countries=[]
    Aggressive: Remove ALL null entries
    """
    with open(cache_path) as f:
        cache = json.load(f)

    original_count = len(cache)
    removed = []

    for key, value in list(cache.items()):
        should_remove = False

        if value is None or value == {}:
            should_remove = True
        elif aggressive:
            # Aggressive: remove any entry missing critical data
            if not value.get('director') or not value.get('countries'):
                should_remove = True
        else:
            # Conservative: only remove entries missing BOTH director AND country
            if not value.get('director') and not value.get('countries', []):
                should_remove = True

        if should_remove:
            removed.append(key)
            del cache[key]

    # Write updated cache
    with open(cache_path, 'w') as f:
        json.dump(cache, f, indent=2)

    print(f"✓ Removed {len(removed)} entries from {cache_path}")
    print(f"  Before: {original_count} entries")
    print(f"  After: {len(cache)} entries")

    return removed


def _title_similarity(a: str, b: str) -> float:
    """Normalised title similarity using difflib SequenceMatcher."""
    return difflib.SequenceMatcher(None, a.lower().strip(), b.lower().strip()).ratio()


def validate_matches(cache_path: str, threshold: float = 0.6):
    """
    Scan TMDb cache for entries where the cached film title doesn't match
    the query title in the cache key. Reports suspect entries — does not delete.

    Cache key format: "query_title|year"
    Cached value contains 'title' (TMDb canonical title).

    Issue #21: wrong-match entries from the old results[0]-no-validation code.
    """
    with open(cache_path) as f:
        cache = json.load(f)

    suspect = []
    skipped_null = 0

    for key, value in cache.items():
        if value is None:
            skipped_null += 1
            continue

        # Parse cache key: "title|year"
        parts = key.split('|', 1)
        query_title = parts[0]
        cached_title = value.get('title', '') or value.get('tmdb_title', '')

        if not cached_title:
            continue

        sim = _title_similarity(query_title, cached_title)
        if sim < threshold:
            suspect.append({
                'cache_key': key,
                'query_title': query_title,
                'cached_title': cached_title,
                'similarity': round(sim, 3),
                'tmdb_id': value.get('tmdb_id'),
            })

    print(f"\nValidate-Matches Report: {cache_path}")
    print(f"  Total entries scanned: {len(cache)}")
    print(f"  Null entries skipped:  {skipped_null}")
    print(f"  Suspect entries (similarity < {threshold}): {len(suspect)}\n")

    if suspect:
        suspect.sort(key=lambda x: x['similarity'])
        for entry in suspect:
            print(
                f"  [{entry['similarity']:.2f}] query='{entry['query_title']}' "
                f"→ cached='{entry['cached_title']}' "
                f"(tmdb_id={entry['tmdb_id']}, key='{entry['cache_key']}')"
            )
        print(
            f"\nTo remove these entries and force re-query:\n"
            f"  Run conservative or aggressive mode, or manually delete the keys listed above."
        )
    else:
        print("  No suspect entries found — all cached titles match their query keys.")

    return suspect


if __name__ == '__main__':
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else 'conservative'

    if mode == '--validate-matches':
        tmdb_cache = Path('output/tmdb_cache.json')
        if not tmdb_cache.exists():
            print(f"TMDb cache not found at {tmdb_cache}. Run classify.py first.")
            sys.exit(1)
        validate_matches(str(tmdb_cache))
        sys.exit(0)

    if mode not in ['conservative', 'aggressive']:
        print("Usage: python scripts/invalidate_null_cache.py [conservative|aggressive|--validate-matches]")
        print("\nconservative:       Remove entries missing both director AND country (recommended)")
        print("aggressive:         Remove entries missing director OR country")
        print("--validate-matches: Report cached entries where title doesn't match the query (Issue #21)")
        sys.exit(1)

    print(f"Cache Invalidation Mode: {mode}\n")

    # Check if cache files exist
    tmdb_cache = Path('output/tmdb_cache.json')
    omdb_cache = Path('output/omdb_cache.json')

    if not tmdb_cache.exists():
        print(f"⚠️  TMDb cache not found at {tmdb_cache}")
        print("   This is expected if you haven't run classify.py yet.")

    if not omdb_cache.exists():
        print(f"⚠️  OMDb cache not found at {omdb_cache}")
        print("   This is expected if you haven't run classify.py with OMDb enabled.")

    # Backup first
    tmdb_removed = []
    omdb_removed = []

    if tmdb_cache.exists():
        print("\n=== TMDb Cache ===")
        backup_cache(str(tmdb_cache))
        aggressive = (mode == 'aggressive')
        tmdb_removed = invalidate_null_entries(str(tmdb_cache), aggressive)

    if omdb_cache.exists():
        print("\n=== OMDb Cache ===")
        backup_cache(str(omdb_cache))
        aggressive = (mode == 'aggressive')
        omdb_removed = invalidate_null_entries(str(omdb_cache), aggressive)

    print(f"\n{'='*60}")
    print(f"✓ Total invalidated: {len(tmdb_removed) + len(omdb_removed)} entries")
    print(f"{'='*60}")
    print("\nNext steps:")
    print("1. Run classify.py to re-query with cleaned titles")
    print("2. Compare new manifest against baseline")
    print(f"3. Check TMDb/OMDb success rates improved")
