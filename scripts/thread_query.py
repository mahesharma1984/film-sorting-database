#!/usr/bin/env python3
"""
Thread query CLI for discovering Satellite connections

Usage:
    # Discover threads for a film
    python scripts/thread_query.py --discover "Deep Red (1975)"
    python scripts/thread_query.py --discover "Faster Pussycat Kill Kill" --year 1965

    # Query thread category keywords
    python scripts/thread_query.py --thread "Giallo"
    python scripts/thread_query.py --thread "Pinku Eiga" --top 30

    # List all categories
    python scripts/thread_query.py --list
"""

import argparse
import json
import sys
import re
from pathlib import Path
from typing import Optional, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.rag.query import discover_threads, query_thread_category
from lib.constants import SATELLITE_TENTPOLES


def parse_title_year(title_str: str) -> Tuple[str, Optional[int]]:
    """
    Parse 'Title (Year)' format

    Examples:
        'Deep Red (1975)' -> ('Deep Red', 1975)
        'Deep Red' -> ('Deep Red', None)
    """
    match = re.search(r'\((\d{4})\)\s*$', title_str)
    if match:
        year = int(match.group(1))
        title = title_str[:match.start()].strip()
        return title, year

    return title_str.strip(), None


def cmd_discover(args):
    """Discover threads for a film"""
    title, year = parse_title_year(args.discover)

    if args.year:
        year = args.year

    print(f"\nDiscovering threads for: {title}" + (f" ({year})" if year else ""))
    print(f"Minimum overlap threshold: {args.min_overlap}\n")

    try:
        threads = discover_threads(title, year, min_overlap=args.min_overlap)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nRun: python scripts/build_thread_index.py")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not threads:
        print("No threads found above threshold.")
        print("\nTroubleshooting:")
        print("  - Check if film exists in TMDb")
        print("  - Lower --min-overlap threshold (default: 0.15)")
        print("  - Run: python scripts/build_thread_index.py")
        sys.exit(0)

    print(f"Found {len(threads)} thread connection(s):\n")

    for i, thread in enumerate(threads, 1):
        category = thread['category']
        score = thread['jaccard_score']
        overlap = thread['overlap_count']
        shared = thread['shared_keywords']

        print(f"{i}. {category}")
        print(f"   Jaccard score: {score:.3f}")
        print(f"   Shared keywords ({overlap}): {', '.join(shared[:10])}")
        if len(shared) > 10:
            print(f"   ... and {len(shared) - 10} more")
        print()


def cmd_thread(args):
    """Query thread category keywords"""
    category = args.thread

    # Validate category exists
    if category not in SATELLITE_TENTPOLES:
        print(f"Error: Unknown category '{category}'")
        print(f"\nAvailable categories:")
        for cat in SATELLITE_TENTPOLES.keys():
            print(f"  - {cat}")
        sys.exit(1)

    print(f"\nThread: {category}")
    print(f"Top {args.top} keywords:\n")

    try:
        data = query_thread_category(category, top_k=args.top)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("\nRun: python scripts/build_thread_index.py")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

    if not data['keywords']:
        print("No keywords found for this category.")
        sys.exit(0)

    for i, kw in enumerate(data['keywords'], 1):
        keyword = kw['keyword']
        count = kw['count']
        films = kw['films']

        print(f"{i:2d}. {keyword:25s} (count: {count}, in: {', '.join(films[:3])})")
        if len(films) > 3:
            print(f"    ... and {len(films) - 3} more")


def cmd_list(args):
    """List all Satellite categories with tentpole counts"""
    print("\nSatellite Categories:\n")

    for category, tentpoles in SATELLITE_TENTPOLES.items():
        count = len(tentpoles)
        print(f"  {category:30s} ({count} tentpoles)")

        if args.verbose:
            for title, year, director in tentpoles:
                print(f"    - {title} ({year}) — {director}")
            print()


def main():
    parser = argparse.ArgumentParser(
        description="Query Satellite thread connections",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    # Mutually exclusive commands
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        '--discover',
        metavar='FILM',
        help='Discover threads for a film (format: "Title" or "Title (Year)")'
    )
    group.add_argument(
        '--thread',
        metavar='CATEGORY',
        help='Query keywords for a Satellite category'
    )
    group.add_argument(
        '--list',
        action='store_true',
        help='List all Satellite categories'
    )

    # Optional arguments
    parser.add_argument(
        '--year',
        type=int,
        help='Film year (if not in title)'
    )
    parser.add_argument(
        '--min-overlap',
        type=float,
        default=0.15,
        help='Minimum Jaccard overlap threshold (default: 0.15)'
    )
    parser.add_argument(
        '--top',
        type=int,
        default=20,
        help='Number of top keywords to show (default: 20)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help='Output as JSON'
    )

    args = parser.parse_args()

    # Route to command handler
    if args.discover:
        cmd_discover(args)
    elif args.thread:
        cmd_thread(args)
    elif args.list:
        cmd_list(args)


if __name__ == '__main__':
    main()
