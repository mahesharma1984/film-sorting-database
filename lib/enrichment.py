#!/usr/bin/env python3
"""
lib/enrichment.py - Manual enrichment data source

Loads curator-provided metadata for films API cannot enrich.
Read from output/manual_enrichment.csv (columns: filename, director, country, genres).

CSV format:
  filename,director,country,genres
  "The Hustler (1961).mkv","Robert Rossen","US","Drama"
  "Hiroshima Mon Amour (1959).mkv","Alain Resnais","FR","Drama,Romance"

Trust level: same as API data (below SORTING_DATABASE, above filename-only).
Fills empty fields only — does not override existing metadata values.
"""

import csv
from pathlib import Path
from typing import Dict, Optional

from lib.normalization import normalize_for_lookup


class ManualEnrichmentSource:
    """Load curator-provided metadata for films API cannot enrich."""

    def __init__(self, path: Path):
        self.entries: Dict[str, Dict] = {}
        self._path = path
        if path.exists():
            self._load(path)

    def _load(self, path: Path):
        with open(path, encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                filename = row.get('filename', '').strip()
                if not filename:
                    continue
                key = normalize_for_lookup(filename)
                self.entries[key] = {
                    'director': row.get('director', '').strip() or None,
                    'country': row.get('country', '').strip() or None,
                    'genres': [
                        g.strip() for g in row.get('genres', '').split(',')
                        if g.strip()
                    ] or None,
                }

    def get(self, filename: str) -> Optional[Dict]:
        """Return enrichment data for a filename, or None if not found."""
        return self.entries.get(normalize_for_lookup(filename))

    def __len__(self) -> int:
        return len(self.entries)
