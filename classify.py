#!/usr/bin/env python3
"""
classify.py - Classify films and generate sorting manifest

NEVER moves files. Only reads filenames and writes CSV.

Classification priority order:
1. Parse filename → FilmMetadata
2. TMDb lookup → canonical metadata (cached)
3. **Explicit lookup** from SORTING_DATABASE.md → if found, DONE
4. Core director check → Core/{decade}/{Director}/
5. Reference canon check → Reference/{decade}/
6. Satellite classification (TMDb data) → {decade}/Satellite/{Category}/
7. Popcorn check (format signals + lookup) → Popcorn/{decade}/
8. Staging assignment → Staging/Borderline or Staging/Unknown
"""

import sys
import csv
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from collections import defaultdict

import yaml

from lib.parser import FilenameParser, FilmMetadata
from lib.tmdb import TMDbClient
from lib.lookup import SortingDatabaseLookup
from lib.core_directors import CoreDirectorDatabase
from lib.reference_canon import ReferenceCanonDatabase
from lib.satellite import SatelliteClassifier
from lib.popcorn import PopcornClassifier

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SortingDecision:
    """Container for sorting decision and destination path"""
    tier: str  # Core, Reference, Satellite, Popcorn, Staging
    decade: Optional[str] = None
    subdirectory: Optional[str] = None  # Director for Core, Category for Satellite
    confidence: float = 1.0
    reason: str = ""

    @classmethod
    def from_path(cls, path: str, confidence: float = 1.0, reason: str = ""):
        """Create SortingDecision from destination path"""
        parts = path.strip('/').split('/')

        # Parse path to extract tier, decade, subdirectory
        # Tier-first: Core/1960s/Jean-Luc Godard
        # Tier-first: Reference/1960s
        # Tier-first: Popcorn/1980s
        # Decade-first (SORTING_DATABASE.md format): 1960s/Core/Jean-Luc Godard
        # Decade-first (Satellite): 1970s/Satellite/Brazilian Exploitation
        # Staging: Staging/Borderline

        if len(parts) >= 2:
            first_part = parts[0]

            # Check if tier-first (Core, Reference, Popcorn)
            if first_part in ['Core', 'Reference', 'Popcorn']:
                tier = first_part
                decade = parts[1] if len(parts) > 1 else None
                subdirectory = parts[2] if len(parts) > 2 else None
                return cls(tier=tier, decade=decade, subdirectory=subdirectory,
                          confidence=confidence, reason=reason)

            # Check if Staging
            elif first_part == 'Staging':
                subdirectory = parts[1] if len(parts) > 1 else None
                return cls(tier='Staging', subdirectory=subdirectory,
                          confidence=confidence, reason=reason)

            # Check if decade-first format (1970s, 1960s, etc.)
            elif first_part.endswith('s') and len(first_part) == 5:  # 1970s format
                decade = first_part

                # Decade-first Satellite: 1970s/Satellite/Category
                if len(parts) > 1 and parts[1] == 'Satellite':
                    subdirectory = parts[2] if len(parts) > 2 else None
                    return cls(tier='Satellite', decade=decade, subdirectory=subdirectory,
                              confidence=confidence, reason=reason)

                # Decade-first Core/Reference/Popcorn: 1960s/Core/Director or 1960s/Reference
                elif len(parts) > 1 and parts[1] in ['Core', 'Reference', 'Popcorn']:
                    tier = parts[1]
                    subdirectory = parts[2] if len(parts) > 2 else None
                    return cls(tier=tier, decade=decade, subdirectory=subdirectory,
                              confidence=confidence, reason=reason)

        # Fallback - couldn't parse
        return cls(tier='Staging', subdirectory='Unknown',
                  confidence=0.0, reason=f'Could not parse path: {path}')


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def get_decade(year: int) -> str:
    """Convert year to decade string"""
    decade = (year // 10) * 10
    return f"{decade}s"


class FilmClassifier:
    """Main film classification engine"""

    def __init__(self, config_path: Path):
        self.config = load_config(config_path)
        self.stats = defaultdict(int)
        self._setup_components()

    def _setup_components(self):
        """Initialize all classification components"""
        project_path = Path(self.config['project_path'])

        self.parser = FilenameParser()

        # TMDb client with caching
        tmdb_key = self.config.get('tmdb_api_key')
        if tmdb_key:
            self.tmdb = TMDbClient(
                api_key=tmdb_key,
                cache_path=Path('output/tmdb_cache.json')
            )
            logger.info("✓ TMDb API enrichment enabled (with caching)")
        else:
            self.tmdb = None
            logger.warning("⚠ TMDb API enrichment disabled (no API key)")

        # Explicit lookup database (CRITICAL - checked before all heuristics)
        self.lookup_db = SortingDatabaseLookup(
            project_path / 'SORTING_DATABASE.md'
        )
        lookup_stats = self.lookup_db.get_stats()
        logger.info(f"✓ Loaded explicit lookup table: {lookup_stats['total_entries']} films")

        # Core director database
        self.core_db = CoreDirectorDatabase(
            project_path / 'CORE_DIRECTOR_WHITELIST_FINAL.md'
        )

        # Reference canon database
        self.reference_db = ReferenceCanonDatabase(
            project_path / 'REFERENCE_CANON_LIST.md'
        )

        # Satellite classifier (TMDb-based, not keyword matching)
        self.satellite_classifier = SatelliteClassifier()

        # Popcorn classifier
        self.popcorn_classifier = PopcornClassifier(lookup_db=self.lookup_db)

    def classify_film(self, metadata: FilmMetadata) -> SortingDecision:
        """
        Main classification pipeline

        Priority order:
        1. TMDb enrichment (if available)
        2. Explicit lookup (SORTING_DATABASE.md)
        3. Core director check
        4. Reference canon check
        5. Satellite classification
        6. Popcorn check
        7. Staging
        """

        # Stage 1: TMDb enrichment
        tmdb_data = None
        if self.tmdb and metadata.year:
            tmdb_data = self.tmdb.search_film(metadata.title, metadata.year)
            if tmdb_data and tmdb_data.get('director'):
                metadata.director = tmdb_data['director']
                logger.debug(f"TMDb enriched: {metadata.title} → director: {metadata.director}")

        # Stage 2: Explicit lookup (PRIORITY - bypasses all heuristics)
        explicit_dest = self.lookup_db.lookup(metadata.title, metadata.year)
        if explicit_dest:
            self.stats['explicit_lookup'] += 1
            decision = SortingDecision.from_path(
                explicit_dest,
                confidence=1.0,
                reason='Explicit lookup: SORTING_DATABASE.md'
            )

            # Track satellite counts for cap enforcement
            if decision.tier == 'Satellite' and decision.subdirectory:
                self.satellite_classifier.increment_count(decision.subdirectory)

            return decision

        # Must have year for decade-based classification
        if not metadata.year:
            self.stats['no_year'] += 1
            return SortingDecision(
                tier='Staging',
                subdirectory='Unknown',
                confidence=0.0,
                reason='No year found in filename'
            )

        decade = get_decade(metadata.year)

        # Stage 3: Core director check
        if metadata.director and self.core_db.is_core_director(metadata.director):
            self.stats['core'] += 1
            # Get canonical director name for folder
            canonical_director = self.core_db.get_canonical_director_name(metadata.director)

            return SortingDecision(
                tier='Core',
                decade=decade,
                subdirectory=canonical_director,
                confidence=1.0,
                reason=f'Core director: {canonical_director}'
            )

        # Stage 4: Reference canon check
        if self.reference_db.is_reference_film(metadata.title, metadata.year):
            self.stats['reference'] += 1
            return SortingDecision(
                tier='Reference',
                decade=decade,
                confidence=1.0,
                reason='Reference canon'
            )

        # Stage 5: Satellite classification (TMDb structured data)
        satellite_cat = self.satellite_classifier.classify(metadata, tmdb_data)
        if satellite_cat:
            self.stats['satellite'] += 1
            return SortingDecision(
                tier='Satellite',
                decade=decade,
                subdirectory=satellite_cat,
                confidence=0.8,
                reason=f'Satellite: {satellite_cat} (TMDb data)'
            )

        # Stage 6: Popcorn check
        if self.popcorn_classifier.is_popcorn(metadata):
            self.stats['popcorn'] += 1
            return SortingDecision(
                tier='Popcorn',
                decade=decade,
                confidence=0.7,
                reason='Format signals or explicit Popcorn lookup'
            )

        # Stage 7: Staging
        if metadata.director:
            self.stats['staging_borderline'] += 1
            return SortingDecision(
                tier='Staging',
                subdirectory='Borderline',
                confidence=0.0,
                reason=f'Has director ({metadata.director}) but no tier match'
            )
        else:
            self.stats['staging_unknown'] += 1
            return SortingDecision(
                tier='Staging',
                subdirectory='Unknown',
                confidence=0.0,
                reason='Missing metadata (no director, no TMDb match)'
            )

    def get_destination_path(self, decision: SortingDecision) -> Path:
        """Calculate destination path based on sorting decision"""
        library_path = Path(self.config['library_path'])

        if decision.tier == 'Staging':
            return library_path / 'Staging' / (decision.subdirectory or 'Unknown')

        elif decision.tier == 'Core':
            # Core/1960s/Jean-Luc Godard/
            return library_path / 'Core' / decision.decade / (decision.subdirectory or '')

        elif decision.tier == 'Reference':
            # Reference/1960s/
            return library_path / 'Reference' / decision.decade

        elif decision.tier == 'Popcorn':
            # Popcorn/1980s/
            return library_path / 'Popcorn' / decision.decade

        elif decision.tier == 'Satellite':
            # 1970s/Satellite/Brazilian Exploitation/
            return library_path / decision.decade / 'Satellite' / (decision.subdirectory or '')

        else:
            # Fallback
            return library_path / 'Staging' / 'Unknown'

    def process_directory(self, source_dir: Path) -> List[Dict]:
        """Process all video files in directory"""

        logger.info(f"Processing directory: {source_dir}")

        # Get all video files
        video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.m4v', '.mpg', '.mpeg', '.wmv'}
        video_files = []

        for file_path in source_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                # Skip macOS resource fork files
                if file_path.name.startswith('._'):
                    continue
                video_files.append(file_path)

        logger.info(f"Found {len(video_files)} video files")

        # Process each file
        results = []

        for i, source_file in enumerate(video_files, 1):
            if i % 50 == 0:
                logger.info(f"Processing {i}/{len(video_files)}...")

            try:
                # Parse metadata
                metadata = self.parser.parse(source_file.name)

                # Classify film
                decision = self.classify_film(metadata)

                # Calculate destination
                dest_path = self.get_destination_path(decision)

                # Store result
                results.append({
                    'filename': str(source_file.relative_to(source_dir)),  # Store relative path from source_dir
                    'title': metadata.title,
                    'year': metadata.year,
                    'director': metadata.director or '',
                    'tier': decision.tier,
                    'decade': decision.decade or '',
                    'subdirectory': decision.subdirectory or '',
                    'confidence': decision.confidence,
                    'reason': decision.reason,
                    'destination': str(dest_path)
                })

            except Exception as e:
                logger.error(f"Error processing {source_file.name}: {e}")
                self.stats['error'] += 1

        return results

    def generate_manifest(self, results: List[Dict], output_path: Path):
        """Generate properly-quoted CSV manifest"""

        manifest_file = output_path / 'sorting_manifest.csv'

        with open(manifest_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'filename', 'title', 'year', 'director', 'tier',
                'decade', 'subdirectory', 'confidence', 'reason', 'destination'
            ]

            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)

            writer.writeheader()
            writer.writerows(results)

        logger.info(f"Generated manifest: {manifest_file}")

    def generate_staging_report(self, results: List[Dict], output_path: Path):
        """Generate staging report for manual review"""

        staging_films = [r for r in results if r['tier'] == 'Staging']
        staging_file = output_path / 'staging_report.txt'

        with open(staging_file, 'w', encoding='utf-8') as f:
            f.write("FILMS REQUIRING MANUAL REVIEW\n")
            f.write("=" * 60 + "\n\n")

            for film in staging_films:
                f.write(f"File: {film['filename']}\n")
                f.write(f"Title: {film['title']}\n")
                f.write(f"Year: {film['year']}\n")
                f.write(f"Director: {film['director']}\n")
                f.write(f"Reason: {film['reason']}\n")
                f.write(f"Destination: {film['destination']}\n")
                f.write("-" * 60 + "\n")

        logger.info(f"Generated staging report: {staging_file}")

    def print_statistics(self, results: List[Dict]):
        """Print classification statistics"""

        tier_counts = defaultdict(int)
        for result in results:
            tier_counts[result['tier']] += 1

        total = len(results)

        print("\n" + "=" * 60)
        print("CLASSIFICATION STATISTICS")
        print("=" * 60)

        for tier in ['Core', 'Reference', 'Satellite', 'Popcorn', 'Staging']:
            count = tier_counts.get(tier, 0)
            percentage = (count / total * 100) if total > 0 else 0
            print(f"  {tier:15s}: {count:4d} ({percentage:5.1f}%)")

        print(f"  {'TOTAL':15s}: {total:4d}")

        # Staging rate
        staging_count = tier_counts.get('Staging', 0)
        staging_rate = (staging_count / total * 100) if total > 0 else 0
        print(f"\nStaging rate: {staging_rate:.1f}% (target: <30%)")

        # Explicit lookup rate
        explicit_count = self.stats.get('explicit_lookup', 0)
        explicit_rate = (explicit_count / total * 100) if total > 0 else 0
        print(f"Explicit lookups: {explicit_count} ({explicit_rate:.1f}%)")

        # TMDb cache stats
        if self.tmdb:
            cache_stats = self.tmdb.get_cache_stats()
            print(f"\nTMDb API: {cache_stats['misses']} queries, {cache_stats['hits']} cache hits")
            print(f"  Hit rate: {cache_stats['hit_rate']:.1f}%")

        print()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Classify films and generate sorting manifest',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Example:
  python classify.py "/Volumes/One Touch/movies/unsorted" --config config_external.yaml

This will classify all films and generate:
  - output/sorting_manifest.csv (properly quoted)
  - output/staging_report.txt (films needing review)
  - output/tmdb_cache.json (TMDb response cache)

IMPORTANT: This script NEVER moves files. It only reads filenames and writes CSV.
        """
    )
    parser.add_argument('source', help='Source directory containing films')
    parser.add_argument('--config', default='config_external.yaml',
                       help='Configuration file (default: config_external.yaml)')
    parser.add_argument('--output', default='output',
                       help='Output directory for reports (default: output)')

    args = parser.parse_args()

    # Check paths
    source_path = Path(args.source)
    if not source_path.exists():
        logger.error(f"Source directory not found: {source_path}")
        sys.exit(1)

    config_path = Path(args.config)
    if not config_path.exists():
        logger.error(f"Configuration file not found: {config_path}")
        sys.exit(1)

    output_path = Path(args.output)
    output_path.mkdir(exist_ok=True)

    # Initialize classifier
    try:
        classifier = FilmClassifier(config_path)
    except Exception as e:
        logger.error(f"Failed to initialize classifier: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Process directory
    try:
        results = classifier.process_directory(source_path)

        # Generate outputs
        classifier.generate_manifest(results, output_path)
        classifier.generate_staging_report(results, output_path)

        # Print statistics
        classifier.print_statistics(results)

        logger.info("Classification completed successfully!")

    except Exception as e:
        logger.error(f"Classification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
