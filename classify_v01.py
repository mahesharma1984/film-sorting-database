#!/usr/bin/env python3
"""
classify_v01.py - Two-Pass Binary Film Classification (v0.1 Simplification)

Pass 1: Known films (exact matches only)
  - Core director exact match → Core/{Decade}/{Director}/
  - Explicit lookup in SORTING_DATABASE.md → specified path

Pass 2: Simple signals or Unsorted
  - Format signals → Popcorn/{Decade}/
  - Everything else → Unsorted/

During classification, encodes destination into filename as a tag:
  - Breathless (1960).mkv → Breathless (1960) [Core-1960s-Jean-Luc Godard].mkv
  - Random Film.mkv → Random Film [Unsorted].mkv

NO fuzzy matching. NO API calls. NO caps. NO confidence scores.
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

from lib.parser import FilenameParser, FilmMetadata
from lib.lookup import SortingDatabaseLookup
from lib.core_directors_v01 import CoreDirectorDatabase

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Classification result for one film"""
    original_filename: str
    new_filename: str
    title: str
    year: Optional[int]
    director: Optional[str]
    tier: str
    destination: str
    reason: str  # core_director_exact | explicit_lookup | format_signal | unsorted_*

    def to_csv_row(self, metadata: Optional[FilmMetadata] = None) -> Dict:
        """Convert to CSV row with optional metadata for new v0.2 fields"""
        row = {
            'original_filename': self.original_filename,
            'new_filename': self.new_filename,
            'title': self.title,
            'year': self.year or '',
            'director': self.director or '',
            'language': getattr(metadata, 'language', '') or '' if metadata else '',
            'country': getattr(metadata, 'country', '') or '' if metadata else '',
            'user_tag': getattr(metadata, 'user_tag', '') or '' if metadata else '',
            'tier': self.tier,
            'destination': self.destination,
            'reason': self.reason
        }
        return row


class FilmClassifierV01:
    """Two-pass binary film classifier with filename tagging"""

    def __init__(self, project_path: Path):
        self.project_path = project_path
        self.parser = FilenameParser()

        # Load databases
        self.lookup_db = SortingDatabaseLookup(
            project_path / 'docs' / 'SORTING_DATABASE.md'
        )

        self.core_db = CoreDirectorDatabase(
            project_path / 'docs' / 'CORE_DIRECTOR_WHITELIST_FINAL.md'
        )

        # Statistics
        self.stats = defaultdict(int)

    def _get_decade(self, year: int) -> str:
        """Convert year to decade string"""
        return f"{(year // 10) * 10}s"

    def _parse_tier_from_path(self, path: str) -> str:
        """Extract tier from destination path"""
        parts = path.strip('/').split('/')

        # Check for tier keywords
        for part in parts:
            if part in ['Core', 'Reference', 'Satellite', 'Popcorn', 'Staging']:
                return part

        return 'Unknown'

    def _parse_user_tag(self, tag: str) -> Dict[str, str]:
        """Parse user tag into components

        Examples:
          - "Popcorn-1970s" → {tier: "Popcorn", decade: "1970s"}
          - "Core-1960s-Jacques Demy" → {tier: "Core", decade: "1960s", director: "Jacques Demy"}
          - "1980s-Satellite-Brazilian" → {decade: "1980s", tier: "Satellite", category: "Brazilian"}
        """
        parts = tag.split('-')
        result = {}

        for part in parts:
            # Check if decade
            if re.match(r'(19|20)\d{2}s', part):
                result['decade'] = part
            # Check if tier
            elif part in ['Core', 'Reference', 'Satellite', 'Popcorn', 'Unsorted']:
                result['tier'] = part
            else:
                # Category or director name (accumulate multi-word names)
                if 'category' not in result and 'director' not in result:
                    result['category'] = part
                elif 'director' in result:
                    result['director'] += f' {part}'
                elif 'category' in result:
                    result['category'] += f' {part}'
                else:
                    result['director'] = part

        return result

    def classify(self, metadata: FilmMetadata) -> ClassificationResult:
        """
        Two-pass classification

        Pass 1: Exact matches (Core director + explicit lookup)
        Pass 2: Simple signals (format detection) or Unsorted
        """

        # === PASS 1: EXACT MATCHES ===

        # Check 1: Core director exact match
        if metadata.director and metadata.year:
            if self.core_db.is_core_director(metadata.director):
                canonical_director = self.core_db.get_canonical_name(metadata.director)
                decade = self.core_db.get_director_decade(metadata.director, metadata.year)

                if canonical_director and decade:
                    self.stats['core_director_exact'] += 1
                    destination = f'Core/{decade}/{canonical_director}/'

                    return ClassificationResult(
                        original_filename=metadata.filename,
                        new_filename='',  # Will be set later
                        title=metadata.title,
                        year=metadata.year,
                        director=canonical_director,
                        tier='Core',
                        destination=destination,
                        reason='core_director_exact'
                    )

        # Check 2: Explicit lookup in SORTING_DATABASE.md
        if metadata.year:  # Lookup requires year for disambiguation
            dest = self.lookup_db.lookup(metadata.title, metadata.year)
            if dest:
                self.stats['explicit_lookup'] += 1
                tier = self._parse_tier_from_path(dest)

                return ClassificationResult(
                    original_filename=metadata.filename,
                    new_filename='',  # Will be set later
                    title=metadata.title,
                    year=metadata.year,
                    director=metadata.director,
                    tier=tier,
                    destination=dest,
                    reason='explicit_lookup'
                )
            else:
                # Log lookup failures for debugging (especially for films with format signals)
                if metadata.format_signals:
                    logger.debug(
                        f"Database lookup failed for '{metadata.title}' ({metadata.year}) "
                        f"with format signals: {metadata.format_signals}"
                    )

        # === NEW v0.2: Check 2.5: User tag recovery ===
        if metadata.user_tag:
            parsed_tag = self._parse_user_tag(metadata.user_tag)

            if 'tier' in parsed_tag and 'decade' in parsed_tag:
                tier = parsed_tag['tier']
                decade = parsed_tag['decade']

                # Build destination from tag components
                if tier == 'Core' and 'director' in parsed_tag:
                    destination = f"{decade}/{tier}/{parsed_tag['director']}/"
                elif tier in ['Satellite', 'Popcorn']:
                    category = parsed_tag.get('category', '')
                    destination = f"{decade}/{tier}/{category}/" if category else f"{decade}/{tier}/"
                elif tier == 'Reference':
                    destination = f"{decade}/{tier}/"
                else:
                    destination = f"{tier}/"

                self.stats['user_tag_recovery'] += 1
                return ClassificationResult(
                    original_filename=metadata.filename,
                    new_filename='',
                    title=metadata.title,
                    year=metadata.year,
                    director=metadata.director,
                    tier=tier,
                    destination=destination,
                    reason='user_tag_recovery'
                )

        # === NEW v0.2: Check 3: Reference canon hardcoded lookup ===
        if metadata.year:
            from lib.normalization import normalize_for_lookup
            from lib.constants import REFERENCE_CANON

            normalized_title = normalize_for_lookup(metadata.title, strip_format_signals=True)
            lookup_key = (normalized_title, metadata.year)

            if lookup_key in REFERENCE_CANON:
                decade = self._get_decade(metadata.year)
                destination = f'{decade}/Reference/'

                self.stats['reference_canon'] += 1
                return ClassificationResult(
                    original_filename=metadata.filename,
                    new_filename='',
                    title=metadata.title,
                    year=metadata.year,
                    director=metadata.director,
                    tier='Reference',
                    destination=destination,
                    reason='reference_canon'
                )

        # === NEW v0.2: Check 4: Language/Country → Satellite wave routing ===
        if metadata.country and metadata.year:
            from lib.constants import COUNTRY_TO_WAVE

            if metadata.country in COUNTRY_TO_WAVE:
                wave_config = COUNTRY_TO_WAVE[metadata.country]
                decade = self._get_decade(metadata.year)

                # Conservative: only route if decade matches wave definition
                if decade in wave_config['decades']:
                    category = wave_config['category']
                    destination = f'{decade}/Satellite/{category}/'

                    self.stats['country_decade_satellite'] += 1
                    return ClassificationResult(
                        original_filename=metadata.filename,
                        new_filename='',
                        title=metadata.title,
                        year=metadata.year,
                        director=metadata.director,
                        tier='Satellite',
                        destination=destination,
                        reason='country_decade_satellite'
                    )

        # === PASS 2: UNSORTED ===

        # REMOVED: Format signal → Popcorn classification
        # Rationale: Format signals (Criterion, 35mm, 4K) are EDITION metadata,
        # not TIER classification. A 35mm scan of Breathless is Core, not Popcorn.
        # Films with format signals that don't match Pass 1 go to Unsorted for
        # manual review, which is the correct v0.1 behavior.

        # Default: Unsorted (for manual review)
        self.stats['unsorted'] += 1

        # Build detailed reason
        reason_parts = []
        if not metadata.year:
            reason_parts.append('no_year')
        if not metadata.director:
            reason_parts.append('no_director')
        if metadata.year and metadata.director:
            reason_parts.append('no_match')

        reason = f"unsorted_{'_'.join(reason_parts) if reason_parts else 'unknown'}"

        return ClassificationResult(
            original_filename=metadata.filename,
            new_filename='',  # Will be set later
            title=metadata.title,
            year=metadata.year,
            director=metadata.director,
            tier='Unsorted',
            destination='Unsorted/',
            reason=reason
        )

    def build_destination_tag(self, result: ClassificationResult) -> str:
        """
        Build destination tag from classification result

        Examples:
          - Core/1960s/Jean-Luc Godard/ → [Core-1960s-Jean-Luc Godard]
          - Popcorn/1980s/ → [Popcorn-1980s]
          - Unsorted/ → [Unsorted]
        """
        dest = result.destination.strip('/')
        parts = dest.split('/')

        # Sanitize parts for filename safety
        sanitized_parts = []
        for part in parts:
            # Remove or replace unsafe characters
            safe_part = part.replace('/', '-').replace('\\', '-')
            safe_part = re.sub(r'[<>:"|?*]', '', safe_part)
            sanitized_parts.append(safe_part)

        tag = '-'.join(sanitized_parts)
        return f"[{tag}]"

    def tag_filename(self, original_filename: str, tag: str) -> str:
        """
        Insert destination tag into filename before extension

        Examples:
          - "Breathless (1960).mkv" + "[Core-1960s-Jean-Luc Godard]"
            → "Breathless (1960) [Core-1960s-Jean-Luc Godard].mkv"
          - "Film.mp4" + "[Unsorted]"
            → "Film [Unsorted].mp4"
        """
        # Strip existing tags first (in case of re-classification)
        name_without_tags = re.sub(r'\s*\[.*?\]\s*', ' ', original_filename)
        name_without_tags = ' '.join(name_without_tags.split())  # Collapse whitespace

        # Split into stem and extension
        path = Path(name_without_tags)
        stem = path.stem
        ext = path.suffix

        # Build new filename
        new_filename = f"{stem} {tag}{ext}"

        return new_filename

    def process_directory(self, source_dir: Path) -> List[ClassificationResult]:
        """Process all video files in directory"""
        video_extensions = {'.mkv', '.mp4', '.avi', '.mov', '.m4v', '.mpg', '.mpeg', '.wmv', '.ts', '.m2ts'}
        video_files = []

        for file_path in source_dir.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in video_extensions:
                if not file_path.name.startswith('._'):  # Skip macOS resource forks
                    video_files.append(file_path)

        logger.info(f"Found {len(video_files)} video files")

        results = []
        metadata_list = []  # Store metadata separately for CSV writing
        for i, file_path in enumerate(video_files, 1):
            if i % 100 == 0:
                logger.info(f"Processing {i}/{len(video_files)}...")

            try:
                # Parse filename
                metadata = self.parser.parse(file_path.name)

                # Classify
                result = self.classify(metadata)

                # Build destination tag and create new filename
                tag = self.build_destination_tag(result)
                new_filename = self.tag_filename(file_path.name, tag)

                result.new_filename = new_filename

                results.append(result)
                metadata_list.append(metadata)

            except Exception as e:
                logger.error(f"Error processing {file_path.name}: {e}")
                continue

        return results, metadata_list

    def write_manifest(self, results: List[ClassificationResult], metadata_list: List[FilmMetadata], output_path: Path):
        """Write classification results to CSV manifest"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=[
                'original_filename', 'new_filename', 'title', 'year', 'director',
                'language', 'country', 'user_tag',
                'tier', 'destination', 'reason'
            ])
            writer.writeheader()

            for result, metadata in zip(results, metadata_list):
                writer.writerow(result.to_csv_row(metadata))

        logger.info(f"Wrote manifest to {output_path}")

    def print_stats(self):
        """Print classification statistics"""
        total = sum(self.stats.values())

        print("\n" + "=" * 60)
        print("CLASSIFICATION STATISTICS (v0.2)")
        print("=" * 60)
        print(f"Total films processed: {total}")
        print()
        print("PASS 1: Exact Matches")
        print(f"  Core director (exact):     {self.stats['core_director_exact']:4d}")
        print(f"  Explicit lookup:           {self.stats['explicit_lookup']:4d}")
        print()
        print("NEW v0.2: Enhanced Classification")
        print(f"  User tag recovery:         {self.stats['user_tag_recovery']:4d}")
        print(f"  Reference canon:           {self.stats['reference_canon']:4d}")
        print(f"  Country/decade → Satellite: {self.stats['country_decade_satellite']:4d}")
        print()
        classified = (self.stats['core_director_exact'] +
                     self.stats['explicit_lookup'] +
                     self.stats['user_tag_recovery'] +
                     self.stats['reference_canon'] +
                     self.stats['country_decade_satellite'])
        print(f"  Total classified:          {classified:4d}")
        print()
        print("PASS 2: Unsorted (for manual review)")
        print(f"  Needs manual review:       {self.stats['unsorted']:4d}")
        print()
        accuracy_pct = classified / total * 100 if total > 0 else 0
        print(f"Classification rate: {accuracy_pct:.1f}% ({classified}/{total})")
        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description='v0.1 Two-Pass Film Classification')
    parser.add_argument('source_dir', type=Path, help='Directory containing film files')
    parser.add_argument('--output', '-o', type=Path,
                        default=Path('output/sorting_manifest_v01.csv'),
                        help='Output CSV manifest path')

    args = parser.parse_args()

    if not args.source_dir.exists():
        logger.error(f"Source directory does not exist: {args.source_dir}")
        return 1

    # Initialize classifier
    project_path = Path(__file__).parent
    classifier = FilmClassifierV01(project_path)

    # Process files
    logger.info(f"Scanning directory: {args.source_dir}")
    results, metadata_list = classifier.process_directory(args.source_dir)

    # Write manifest
    classifier.write_manifest(results, metadata_list, args.output)

    # Print statistics
    classifier.print_stats()

    return 0


if __name__ == '__main__':
    sys.exit(main())
