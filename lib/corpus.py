#!/usr/bin/env python3
"""
lib/corpus.py — Per-category ground truth corpus lookup (Issue #38)

Loads all CSV files from data/corpora/ and provides title+year → category
lookups as an authoritative pre-heuristic classification stage.

Each CSV has columns:
    title, year, imdb_id, director, country, canonical_tier, source, notes

CorpusLookup is the Layer 1 external standard against which heuristic routing
(Stages 3-9) is measured. A corpus hit is a classification with confidence=1.0.

Pattern follows lib/lookup.py (SortingDatabaseLookup).
"""

import csv
import logging
from pathlib import Path
from typing import Optional, Dict, Tuple

from lib.normalization import normalize_for_lookup

logger = logging.getLogger(__name__)


class CorpusLookup:
    """
    Load all per-category corpus CSV files and provide title+year → category lookups.

    Lookup priority:
      1. IMDb ID match (highest confidence — format-proof)
      2. Normalized title + year match

    Returns a dict with:
        category:       Satellite subcategory name (e.g. 'Giallo')
        imdb_id:        tt... string or empty
        canonical_tier: 1=core canon, 2=important reference, 3=texture
        source:         citation string
        director:       director from corpus row
    """

    def __init__(self, corpora_dir: Path):
        # (normalized_title, year) → entry dict
        self._title_index: Dict[Tuple[str, int], Dict] = {}
        # imdb_id → entry dict
        self._imdb_index: Dict[str, Dict] = {}
        self._count = 0
        self._categories: set = set()

        if corpora_dir.exists():
            self._load_all(corpora_dir)
        else:
            logger.info(f"Corpora directory not found: {corpora_dir} — corpus lookup disabled")

    def _load_all(self, corpora_dir: Path) -> None:
        for csv_path in sorted(corpora_dir.glob('*.csv')):
            # Derive category name from filename: giallo.csv → Giallo
            # Multi-word: brazilian-exploitation.csv → Brazilian Exploitation
            category = csv_path.stem.replace('-', ' ').title()
            count = self._load_category(csv_path, category)
            logger.info(f"Loaded corpus: {category} ({count} entries from {csv_path.name})")

    def _load_category(self, path: Path, category: str) -> int:
        count = 0
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    title = row.get('title', '').strip()
                    year_str = row.get('year', '').strip()
                    if not title or not year_str:
                        continue
                    try:
                        year = int(year_str)
                    except ValueError:
                        continue

                    entry = {
                        'category': category,
                        'imdb_id': row.get('imdb_id', '').strip(),
                        'canonical_tier': self._parse_tier(row.get('canonical_tier', '')),
                        'source': row.get('source', '').strip(),
                        'director': row.get('director', '').strip(),
                    }

                    # Title+year index
                    key = (normalize_for_lookup(title), year)
                    if key not in self._title_index:
                        self._title_index[key] = entry
                        count += 1

                    # IMDb ID index (takes priority over title match)
                    imdb_id = entry['imdb_id']
                    if imdb_id and imdb_id not in self._imdb_index:
                        self._imdb_index[imdb_id] = entry

                    self._categories.add(category)
                    self._count += 1

        except Exception as e:
            logger.error(f"Error loading corpus {path}: {e}")
        return count

    def _parse_tier(self, tier_str: str) -> int:
        try:
            t = int(tier_str)
            return t if t in (1, 2, 3) else 2
        except (ValueError, TypeError):
            return 2  # Default to reference tier

    def lookup(self, title: str, year: Optional[int], imdb_id: Optional[str] = None) -> Optional[Dict]:
        """
        Look up film in corpus.

        Returns entry dict if found, None if no match.
        IMDb ID match takes priority over title+year match.
        """
        # IMDb ID match (format-proof, highest confidence)
        if imdb_id and imdb_id in self._imdb_index:
            logger.debug(f"Corpus IMDb hit: {imdb_id} → {self._imdb_index[imdb_id]['category']}")
            return self._imdb_index[imdb_id]

        # Title + year match
        if year is not None:
            key = (normalize_for_lookup(title), year)
            if key in self._title_index:
                entry = self._title_index[key]
                logger.debug(f"Corpus title hit: '{title}' ({year}) → {entry['category']}")
                return entry

        return None

    def get_stats(self) -> Dict:
        return {
            'total_entries': self._count,
            'categories': sorted(self._categories),
            'title_index_size': len(self._title_index),
            'imdb_index_size': len(self._imdb_index),
        }
