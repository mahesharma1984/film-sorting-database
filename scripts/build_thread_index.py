#!/usr/bin/env python3
"""
Build thread keyword index from Satellite tentpole films

This script:
1. Loads tentpole films from constants.SATELLITE_TENTPOLES
2. Queries TMDb for each film (uses cache)
3. Aggregates keywords by category with frequency counts
4. Outputs JSON index for thread discovery

PRECISION task: keyword extraction and aggregation
"""

import json
import logging
from pathlib import Path
from collections import defaultdict
import sys

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.tmdb import TMDbClient
from lib.constants import SATELLITE_TENTPOLES
from lib.normalization import normalize_for_lookup

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s'
)
logger = logging.getLogger(__name__)


class ThreadIndexBuilder:
    """Build keyword index from tentpole films"""

    def __init__(self, config_path: Path):
        self.config = self._load_config(config_path)

        # Initialize TMDb client with cache
        project_path = Path(self.config['project_path'])
        tmdb_key = self.config.get('tmdb_api_key')
        if not tmdb_key:
            raise ValueError("TMDb API key required for thread indexing")

        cache_path = project_path / self.config.get('tmdb_cache', 'output/tmdb_cache.json')
        self.tmdb = TMDbClient(tmdb_key, cache_path)

        self.output_path = project_path / 'output' / 'thread_keywords.json'

    def _load_config(self, config_path: Path) -> dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def build_index(self) -> dict:
        """
        Build keyword index from all tentpole films

        Returns:
            {
                'Giallo': {
                    'keywords': [
                        {'keyword': 'murder', 'count': 5, 'films': ['Deep Red', ...]},
                        {'keyword': 'mystery', 'count': 4, 'films': [...]},
                    ],
                    'tentpole_count': 5,
                    'tentpole_films': [
                        {'title': 'Deep Red', 'year': 1975, 'director': 'Dario Argento'}
                    ]
                },
                ...
            }
        """
        index = {}

        for category, tentpoles in SATELLITE_TENTPOLES.items():
            logger.info(f"Processing {category} ({len(tentpoles)} tentpoles)")

            category_data = {
                'keywords': [],
                'tentpole_count': len(tentpoles),
                'tentpole_films': [],
                'query_failures': []
            }

            # Track keyword frequencies across all tentpoles
            keyword_counts = defaultdict(int)
            keyword_films = defaultdict(list)

            for title, year, director in tentpoles:
                # Query TMDb (uses cache if available)
                clean_title = normalize_for_lookup(title)
                tmdb_data = self.tmdb.search_film(clean_title, year)

                if tmdb_data and tmdb_data.get('keywords'):
                    keywords = tmdb_data['keywords']
                    logger.info(f"  {title} ({year}): {len(keywords)} keywords")

                    # Aggregate keywords
                    for keyword in keywords:
                        keyword_lower = keyword.lower()
                        keyword_counts[keyword_lower] += 1
                        keyword_films[keyword_lower].append(title)

                    # Store tentpole metadata
                    category_data['tentpole_films'].append({
                        'title': tmdb_data.get('title', title),
                        'year': year,
                        'director': director,
                        'keyword_count': len(keywords)
                    })
                else:
                    logger.warning(f"  {title} ({year}): No TMDb data or keywords")
                    category_data['query_failures'].append(f"{title} ({year})")

            # Sort keywords by frequency (descending)
            sorted_keywords = sorted(
                keyword_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )

            # Build keyword list with metadata
            category_data['keywords'] = [
                {
                    'keyword': keyword,
                    'count': count,
                    'films': keyword_films[keyword]
                }
                for keyword, count in sorted_keywords
            ]

            index[category] = category_data
            logger.info(f"  Total unique keywords: {len(sorted_keywords)}")

        return index

    def save_index(self, index: dict):
        """Save index to JSON file"""
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.output_path, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved thread index to {self.output_path}")

    def print_summary(self, index: dict):
        """Print human-readable summary"""
        print("\n=== THREAD KEYWORD INDEX SUMMARY ===\n")

        total_keywords = 0
        total_tentpoles = 0
        total_failures = 0

        for category, data in index.items():
            print(f"{category}:")
            print(f"  Tentpoles: {data['tentpole_count']}")
            print(f"  Unique keywords: {len(data['keywords'])}")

            failures = len(data.get('query_failures', []))
            if failures > 0:
                print(f"  Query failures: {failures}")
                for failure in data['query_failures']:
                    print(f"    - {failure}")

            # Show top 10 keywords
            if data['keywords']:
                print(f"  Top keywords:")
                for kw in data['keywords'][:10]:
                    print(f"    - {kw['keyword']} (count: {kw['count']})")
            print()

            total_keywords += len(data['keywords'])
            total_tentpoles += data['tentpole_count']
            total_failures += failures

        print(f"TOTALS:")
        print(f"  Categories: {len(index)}")
        print(f"  Tentpole films: {total_tentpoles}")
        print(f"  Total unique keywords: {total_keywords}")
        print(f"  Query failures: {total_failures}")


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Build thread keyword index from Satellite tentpoles"
    )
    parser.add_argument(
        '--config',
        type=Path,
        default=Path('config.yaml'),
        help='Path to config file (default: config.yaml)'
    )
    parser.add_argument(
        '--summary',
        action='store_true',
        help='Print summary after building'
    )

    args = parser.parse_args()

    try:
        builder = ThreadIndexBuilder(args.config)
        index = builder.build_index()
        builder.save_index(index)

        if args.summary:
            builder.print_summary(index)

        # Print cache stats
        stats = builder.tmdb.get_cache_stats()
        print(f"\nTMDb Cache Stats:")
        print(f"  Hits: {stats['hits']}")
        print(f"  Misses: {stats['misses']}")
        print(f"  Hit rate: {stats['hit_rate']:.1f}%")

    except Exception as e:
        logger.error(f"Error building thread index: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
