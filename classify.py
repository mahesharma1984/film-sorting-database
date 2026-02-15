#!/usr/bin/env python3
"""
classify.py - Film Classification Pipeline (v1.0)

NEVER moves files. Only reads filenames and writes CSV.

Classification priority order:
1. [PRECISION] Parse filename → FilmMetadata
2. [PRECISION] TMDb enrichment → canonical director, country, genre (cached, optional)
3. [PRECISION] Explicit lookup → SORTING_DATABASE.md (human-curated, highest trust)
4. [REASONING] Core director check → whitelist exact match
5. [REASONING] Reference canon check → 50-film hardcoded list in constants.py
6. [PRECISION] User tag recovery → trust previous human classification
7. [REASONING] Language/country → Satellite routing (decade-bounded)
8. [REASONING] Satellite classification → TMDb data (country + genre + decade)
9. [PRECISION] Default → Unsorted with detailed reason code
"""

import sys
import csv
import re
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
from lib.satellite import SatelliteClassifier
from lib.normalization import normalize_for_lookup
from lib.constants import REFERENCE_CANON, COUNTRY_TO_WAVE

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of classifying one film"""
    filename: str
    title: str
    year: Optional[int]
    director: Optional[str]
    language: Optional[str]
    country: Optional[str]
    user_tag: Optional[str]
    tier: str
    decade: Optional[str]
    subdirectory: Optional[str]
    destination: str
    confidence: float
    reason: str


def get_decade(year: int) -> str:
    """Convert year to decade string"""
    return f"{(year // 10) * 10}s"


def load_config(config_path: Path) -> dict:
    """Load configuration from YAML file"""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


class FilmClassifier:
    """Main film classification engine — v1.0"""

    def __init__(self, config_path: Path, no_tmdb: bool = False):
        self.config = load_config(config_path)
        self.stats = defaultdict(int)
        self.no_tmdb = no_tmdb
        self._setup_components()

    def _setup_components(self):
        """Initialize all classification components"""
        project_path = Path(self.config['project_path'])

        self.parser = FilenameParser()

        # TMDb client with caching (optional — graceful degradation)
        tmdb_key = self.config.get('tmdb_api_key')
        if tmdb_key and not self.no_tmdb:
            self.tmdb = TMDbClient(
                api_key=tmdb_key,
                cache_path=Path('output/tmdb_cache.json')
            )
            logger.info("TMDb API enrichment enabled (with caching)")
        else:
            self.tmdb = None
            if self.no_tmdb:
                logger.info("TMDb API enrichment disabled (--no-tmdb flag)")
            else:
                logger.warning("TMDb API enrichment disabled (no API key in config)")

        # Explicit lookup database — checked BEFORE all heuristics
        self.lookup_db = SortingDatabaseLookup(
            project_path / 'SORTING_DATABASE.md'
        )
        lookup_stats = self.lookup_db.get_stats()
        logger.info(f"Loaded explicit lookup table: {lookup_stats['total_entries']} films")

        # Core director database — exact match only
        self.core_db = CoreDirectorDatabase(
            project_path / 'CORE_DIRECTOR_WHITELIST_FINAL.md'
        )

        # Satellite classifier (TMDb-based rules)
        self.satellite_classifier = SatelliteClassifier()

    def _build_destination(self, tier: str, decade: Optional[str], subdirectory: Optional[str]) -> str:
        """Build destination path string from classification components (tier-first)"""
        if tier == 'Unsorted':
            return 'Unsorted/'
        elif tier == 'Core' and decade and subdirectory:
            return f'Core/{decade}/{subdirectory}/'
        elif tier == 'Reference' and decade:
            return f'Reference/{decade}/'
        elif tier == 'Satellite' and decade and subdirectory:
            return f'Satellite/{subdirectory}/{decade}/'  # Category-first structure (Issue #6)
        elif tier == 'Popcorn' and decade:
            return f'Popcorn/{decade}/'
        elif tier == 'Staging':
            return f'Staging/{subdirectory or "Unknown"}/'
        else:
            return 'Unsorted/'

    def _parse_destination_path(self, path: str) -> dict:
        """Parse a destination path from SORTING_DATABASE.md into components (supports both formats)"""
        parts = path.strip('/').split('/')
        result = {'tier': 'Unknown', 'decade': None, 'subdirectory': None}

        if not parts:
            return result

        first = parts[0]

        # Tier-first format (PREFERRED): "Core/1960s/Director", "Reference/1960s", "Satellite/Category/1970s"
        if first in ('Core', 'Reference', 'Satellite', 'Popcorn', 'Staging', 'Unsorted'):
            result['tier'] = first
            if len(parts) > 1 and re.match(r'\d{4}s$', parts[1]):
                result['decade'] = parts[1]
                if len(parts) > 2:
                    result['subdirectory'] = '/'.join(parts[2:])
            elif len(parts) > 1:
                result['subdirectory'] = '/'.join(parts[1:])
        # Legacy decade-first format (for backward compatibility): "1960s/Core/Director"
        elif re.match(r'\d{4}s$', first):
            result['decade'] = first
            if len(parts) > 1:
                result['tier'] = parts[1]
            if len(parts) > 2:
                result['subdirectory'] = '/'.join(parts[2:])

        return result

    def _parse_user_tag(self, tag: str) -> dict:
        """Parse user tag like 'Popcorn-1970s' or 'Core-1960s-Jacques Demy' into components"""
        parts = tag.split('-')
        result = {}

        remaining_parts = []
        for part in parts:
            if re.match(r'(19|20)\d{2}s', part):
                result['decade'] = part
            elif part in ('Core', 'Reference', 'Satellite', 'Popcorn', 'Unsorted'):
                result['tier'] = part
            else:
                remaining_parts.append(part)

        if remaining_parts:
            result['extra'] = ' '.join(remaining_parts)

        return result

    def classify(self, metadata: FilmMetadata) -> ClassificationResult:
        """
        Main classification pipeline — priority-ordered checks.

        Each check is a separate method with declared failure behavior:
        - Explicit lookup: soft gate (no match → continue)
        - Core director: soft gate (no match → continue)
        - Reference canon: soft gate (no match → continue)
        - User tag: soft gate (no tag → continue)
        - Country/decade satellite: soft gate (no match → continue)
        - TMDb satellite: soft gate (no data → continue)
        - No year: hard gate (cannot route to decade → Unsorted)
        """

        # === Stage 1: TMDb enrichment (optional) ===
        tmdb_data = None
        if self.tmdb and metadata.title and metadata.year:
            # Clean title for TMDb query (remove user tags, format signals, but keep proper title structure)
            clean_title = metadata.title
            # Remove user tag brackets [...]
            clean_title = re.sub(r'\s*\[.+?\]\s*', ' ', clean_title)
            # Remove format signals using shared normalization (but not full normalization to preserve punctuation)
            from lib.normalization import _strip_format_signals
            clean_title = _strip_format_signals(clean_title)
            # Clean up extra spaces and parentheses artifacts
            clean_title = re.sub(r'\s*\(\s*\)', '', clean_title)  # Remove empty parens like "Criterion ("
            clean_title = ' '.join(clean_title.split())

            tmdb_data = self.tmdb.search_film(clean_title.strip(), metadata.year)
            if tmdb_data:
                # Enrich metadata with TMDb director if we don't have one
                if not metadata.director and tmdb_data.get('director'):
                    metadata.director = tmdb_data['director']
                # Enrich country if not detected from filename
                if not metadata.country and tmdb_data.get('countries'):
                    metadata.country = tmdb_data['countries'][0] if tmdb_data['countries'] else None

        # === Stage 2: Explicit lookup (highest trust — human-curated) ===
        if metadata.title:
            dest = self.lookup_db.lookup(metadata.title, metadata.year)
            if dest:
                self.stats['explicit_lookup'] += 1
                parsed = self._parse_destination_path(dest)

                # Track satellite counts for cap enforcement
                if parsed['tier'] == 'Satellite' and parsed.get('subdirectory'):
                    self.satellite_classifier.increment_count(parsed['subdirectory'])

                return ClassificationResult(
                    filename=metadata.filename, title=metadata.title,
                    year=metadata.year, director=metadata.director,
                    language=metadata.language, country=metadata.country,
                    user_tag=metadata.user_tag,
                    tier=parsed['tier'], decade=parsed['decade'],
                    subdirectory=parsed.get('subdirectory'),
                    destination=dest,
                    confidence=1.0, reason='explicit_lookup'
                )

        # === Hard gate: no year = cannot route to decade ===
        if not metadata.year:
            self.stats['unsorted_no_year'] += 1
            return ClassificationResult(
                filename=metadata.filename, title=metadata.title,
                year=None, director=metadata.director,
                language=metadata.language, country=metadata.country,
                user_tag=metadata.user_tag,
                tier='Unsorted', decade=None, subdirectory=None,
                destination='Unsorted/',
                confidence=0.0, reason='unsorted_no_year'
            )

        decade = get_decade(metadata.year)

        # === Stage 3: Core director check ===
        if metadata.director and self.core_db.is_core_director(metadata.director):
            canonical = self.core_db.get_canonical_name(metadata.director)
            director_decade = self.core_db.get_director_decade(metadata.director, metadata.year)

            if canonical and director_decade:
                self.stats['core_director'] += 1
                dest = f'Core/{director_decade}/{canonical}/'
                return ClassificationResult(
                    filename=metadata.filename, title=metadata.title,
                    year=metadata.year, director=canonical,
                    language=metadata.language, country=metadata.country,
                    user_tag=metadata.user_tag,
                    tier='Core', decade=director_decade, subdirectory=canonical,
                    destination=dest,
                    confidence=1.0, reason='core_director'
                )

        # === Stage 4: Reference canon check (constants.py hardcoded list) ===
        normalized_title = normalize_for_lookup(metadata.title, strip_format_signals=True)
        ref_key = (normalized_title, metadata.year)
        if ref_key in REFERENCE_CANON:
            self.stats['reference_canon'] += 1
            dest = f'Reference/{decade}/'
            return ClassificationResult(
                filename=metadata.filename, title=metadata.title,
                year=metadata.year, director=metadata.director,
                language=metadata.language, country=metadata.country,
                user_tag=metadata.user_tag,
                tier='Reference', decade=decade, subdirectory=None,
                destination=dest,
                confidence=1.0, reason='reference_canon'
            )

        # === Stage 5: User tag recovery ===
        if metadata.user_tag:
            parsed_tag = self._parse_user_tag(metadata.user_tag)
            if 'tier' in parsed_tag and 'decade' in parsed_tag:
                tier = parsed_tag['tier']
                tag_decade = parsed_tag['decade']
                extra = parsed_tag.get('extra', '')

                if tier == 'Core' and extra:
                    dest = f'Core/{tag_decade}/{extra}/'
                elif tier == 'Satellite' and extra:
                    dest = f'Satellite/{extra}/{tag_decade}/'  # Category-first (Issue #6)
                elif tier in ('Reference', 'Popcorn'):
                    dest = f'{tier}/{tag_decade}/'
                else:
                    dest = f'{tier}/'

                self.stats['user_tag_recovery'] += 1
                return ClassificationResult(
                    filename=metadata.filename, title=metadata.title,
                    year=metadata.year, director=metadata.director,
                    language=metadata.language, country=metadata.country,
                    user_tag=metadata.user_tag,
                    tier=tier, decade=tag_decade, subdirectory=extra or None,
                    destination=dest,
                    confidence=0.8, reason='user_tag_recovery'
                )

        # === Stage 6: Language/country → Satellite routing (from filename) ===
        if metadata.country and metadata.country in COUNTRY_TO_WAVE:
            wave_config = COUNTRY_TO_WAVE[metadata.country]
            if decade in wave_config['decades']:
                category = wave_config['category']
                self.stats['country_satellite'] += 1
                dest = f'Satellite/{category}/{decade}/'  # Category-first (Issue #6)
                return ClassificationResult(
                    filename=metadata.filename, title=metadata.title,
                    year=metadata.year, director=metadata.director,
                    language=metadata.language, country=metadata.country,
                    user_tag=metadata.user_tag,
                    tier='Satellite', decade=decade, subdirectory=category,
                    destination=dest,
                    confidence=0.7, reason='country_satellite'
                )

        # === Stage 7: TMDb-based satellite classification ===
        if tmdb_data:
            satellite_cat = self.satellite_classifier.classify(metadata, tmdb_data)
            if satellite_cat:
                self.stats['tmdb_satellite'] += 1
                dest = f'Satellite/{satellite_cat}/{decade}/'  # Category-first (Issue #6)
                return ClassificationResult(
                    filename=metadata.filename, title=metadata.title,
                    year=metadata.year, director=metadata.director,
                    language=metadata.language, country=metadata.country,
                    user_tag=metadata.user_tag,
                    tier='Satellite', decade=decade, subdirectory=satellite_cat,
                    destination=dest,
                    confidence=0.7, reason='tmdb_satellite'
                )

        # === Stage 8: Unsorted (default) ===
        reason_parts = []
        if not metadata.director:
            reason_parts.append('no_director')
        if metadata.director:
            reason_parts.append('no_match')
        reason = f"unsorted_{'_'.join(reason_parts)}" if reason_parts else 'unsorted_unknown'

        self.stats[reason] += 1
        return ClassificationResult(
            filename=metadata.filename, title=metadata.title,
            year=metadata.year, director=metadata.director,
            language=metadata.language, country=metadata.country,
            user_tag=metadata.user_tag,
            tier='Unsorted', decade=decade, subdirectory=None,
            destination='Unsorted/',
            confidence=0.0, reason=reason
        )

    def process_directory(self, source_dir: Path) -> List[ClassificationResult]:
        """Process all video files in directory"""
        video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.m4v', '.mpg',
                          '.mpeg', '.wmv', '.ts', '.m2ts'}
        video_files = []

        for file_path in source_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                if not file_path.name.startswith('._'):
                    video_files.append(file_path)

        logger.info(f"Found {len(video_files)} video files")

        results = []
        for i, file_path in enumerate(video_files, 1):
            if i % 100 == 0:
                logger.info(f"Processing {i}/{len(video_files)}...")

            try:
                metadata = self.parser.parse(file_path.name)
                result = self.classify(metadata)
                results.append(result)
            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                self.stats['errors'] += 1

        return results

    def write_manifest(self, results: List[ClassificationResult], output_path: Path):
        """Write classification results to properly-quoted CSV manifest"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            fieldnames = [
                'filename', 'title', 'year', 'director',
                'language', 'country', 'user_tag',
                'tier', 'decade', 'subdirectory',
                'destination', 'confidence', 'reason'
            ]
            writer = csv.DictWriter(f, fieldnames=fieldnames, quoting=csv.QUOTE_ALL)
            writer.writeheader()

            for result in results:
                writer.writerow({
                    'filename': result.filename,
                    'title': result.title,
                    'year': result.year or '',
                    'director': result.director or '',
                    'language': result.language or '',
                    'country': result.country or '',
                    'user_tag': result.user_tag or '',
                    'tier': result.tier,
                    'decade': result.decade or '',
                    'subdirectory': result.subdirectory or '',
                    'destination': result.destination,
                    'confidence': result.confidence,
                    'reason': result.reason,
                })

        logger.info(f"Wrote manifest to {output_path}")

    def write_staging_report(self, results: List[ClassificationResult], output_path: Path):
        """Write staging report for films needing manual review"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        staging = [r for r in results if r.tier == 'Unsorted']

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("FILMS REQUIRING MANUAL REVIEW\n")
            f.write("=" * 60 + "\n\n")
            f.write(f"Total: {len(staging)} films\n\n")

            for film in staging:
                f.write(f"File: {film.filename}\n")
                f.write(f"Title: {film.title}\n")
                f.write(f"Year: {film.year or 'UNKNOWN'}\n")
                f.write(f"Director: {film.director or 'UNKNOWN'}\n")
                f.write(f"Reason: {film.reason}\n")
                f.write("-" * 60 + "\n")

        logger.info(f"Wrote staging report to {output_path}")

    def print_stats(self, results: List[ClassificationResult]):
        """Print classification statistics"""
        tier_counts = defaultdict(int)
        for r in results:
            tier_counts[r.tier] += 1

        total = len(results)
        classified = total - tier_counts.get('Unsorted', 0)

        print("\n" + "=" * 60)
        print("CLASSIFICATION STATISTICS (v1.0)")
        print("=" * 60)
        print(f"Total films processed: {total}\n")

        print("BY TIER:")
        for tier in ['Core', 'Reference', 'Satellite', 'Popcorn', 'Unsorted']:
            count = tier_counts.get(tier, 0)
            pct = (count / total * 100) if total > 0 else 0
            print(f"  {tier:15s}: {count:4d} ({pct:5.1f}%)")

        print(f"\nBY REASON:")
        for reason, count in sorted(self.stats.items(), key=lambda x: -x[1]):
            if reason != 'errors':
                print(f"  {reason:30s}: {count:4d}")

        classification_rate = (classified / total * 100) if total > 0 else 0
        print(f"\nClassification rate: {classification_rate:.1f}% ({classified}/{total})")

        if self.stats.get('errors'):
            print(f"Errors: {self.stats['errors']}")

        if self.tmdb:
            cache_stats = self.tmdb.get_cache_stats()
            print(f"\nTMDb: {cache_stats['misses']} API queries, "
                  f"{cache_stats['hits']} cache hits "
                  f"({cache_stats['hit_rate']:.0f}% hit rate)")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Classify films and generate sorting manifest (v1.0)',
        epilog="""
NEVER moves files. Only reads filenames and writes CSV.

Examples:
  python classify.py /path/to/films
  python classify.py /path/to/films --no-tmdb
  python classify.py /path/to/films --output output/my_manifest.csv
        """
    )
    parser.add_argument('source_dir', type=Path,
                       help='Directory containing film files')
    parser.add_argument('--output', '-o', type=Path,
                       default=Path('output/sorting_manifest.csv'),
                       help='Output CSV manifest path (default: output/sorting_manifest.csv)')
    parser.add_argument('--config', type=Path, default=Path('config_external.yaml'),
                       help='Configuration file (default: config_external.yaml)')
    parser.add_argument('--no-tmdb', action='store_true',
                       help='Disable TMDb API enrichment (offline classification)')

    args = parser.parse_args()

    if not args.source_dir.exists():
        logger.error(f"Source directory does not exist: {args.source_dir}")
        sys.exit(1)

    if not args.config.exists():
        logger.error(f"Config file not found: {args.config}")
        sys.exit(1)

    # Initialize classifier
    classifier = FilmClassifier(args.config, no_tmdb=args.no_tmdb)

    # Process
    logger.info(f"Scanning: {args.source_dir}")
    results = classifier.process_directory(args.source_dir)

    # Write outputs
    classifier.write_manifest(results, args.output)

    staging_path = args.output.parent / 'staging_report.txt'
    classifier.write_staging_report(results, staging_path)

    # Print stats
    classifier.print_stats(results)

    return 0


if __name__ == '__main__':
    sys.exit(main())
