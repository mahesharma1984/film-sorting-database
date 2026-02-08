#!/usr/bin/env python3
"""
Reference canon film list with fuzzy matching
Extracted from film_sorter.py lines 290-327
"""

import re
import logging
from pathlib import Path
from typing import List, Dict

from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)


class ReferenceCanonDatabase:
    """Load and query Reference canon films"""

    def __init__(self, canon_file: Path):
        self.reference_films: List[Dict] = []
        self._load_canon(canon_file)

    def _load_canon(self, file_path: Path):
        """Parse Reference canon markdown file"""
        if not file_path.exists():
            logger.error(f"Reference canon file not found: {file_path}")
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Extract numbered film entries
            pattern = r'\d+\.\s*\*\*([^*]+)\*\*\s*\((\d{4})\)'
            matches = re.findall(pattern, content)

            for title, year in matches:
                self.reference_films.append({
                    'title': title.strip(),
                    'year': int(year)
                })

            logger.info(f"Loaded {len(self.reference_films)} reference films")

        except Exception as e:
            logger.error(f"Error loading reference canon: {e}")

    def is_reference_film(self, title: str, year: int) -> bool:
        """Check if film is in Reference canon"""
        if not year:
            return False

        for ref_film in self.reference_films:
            title_match = fuzz.ratio(title.lower(), ref_film['title'].lower()) > 85
            year_match = year == ref_film['year']

            if title_match and year_match:
                return True

        return False
