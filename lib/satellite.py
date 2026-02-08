#!/usr/bin/env python3
"""
Satellite category classification using TMDb structured data

MAJOR REFACTOR: Replaces keyword matching on titles with TMDb country/genre data
"""

import logging
from typing import Optional, Dict
from collections import defaultdict

logger = logging.getLogger(__name__)


class SatelliteClassifier:
    """Classify films into Satellite categories using TMDb structured data"""

    def __init__(self, categories_file=None):
        """
        Initialize classifier with category definitions and caps

        Note: categories_file parameter kept for compatibility but not used
        (categories are now defined inline based on TMDb data rules)
        """
        self.caps = {
            'Giallo': 30,
            'Pinku Eiga': 35,
            'Brazilian Exploitation': 45,
            'Hong Kong Action': 65,
            'American Exploitation': 80,
            'European Sexploitation': 25,
            'Blaxploitation': 20,
            'Music Films': 20,
            'Cult Oddities': 50,
        }
        self.counts = defaultdict(int)  # Track category counts

        # Known directors for specific categories
        self.director_mappings = {
            'Giallo': ['bava', 'argento', 'fulci', 'martino', 'soavi', 'lenzi'],
            'Pinku Eiga': ['wakamatsu', 'kumashiro', 'tanaka'],
            'American Exploitation': ['russ meyer', 'abel ferrara', 'larry cohen', 'herschell gordon lewis'],
            'European Sexploitation': ['borowczyk', 'metzger', 'brass'],
            'Blaxploitation': ['gordon parks', 'jack hill'],
            'Hong Kong Action': ['tsui hark', 'ringo lam', 'john woo'],
        }

    def classify(self, metadata, tmdb_data: Optional[Dict]) -> Optional[str]:
        """
        Classify using TMDb structured data + director rules

        NO keyword matching on title text. Only TMDb country/genre data.

        Args:
            metadata: FilmMetadata object
            tmdb_data: TMDb data dict with keys: title, year, director, genres, countries

        Returns:
            Category name if classified, None otherwise
        """
        if not tmdb_data:
            return None

        # Extract structured data
        countries = tmdb_data.get('countries', [])
        genres = tmdb_data.get('genres', [])
        director = tmdb_data.get('director', '') or ''
        year = tmdb_data.get('year')
        director_lower = director.lower()

        # BRAZILIAN EXPLOITATION
        # Country: BR + Year: 1970-1989 + exploitation-adjacent genres
        if 'BR' in countries and year and 1970 <= year <= 1989:
            exploitation_genres = {'Drama', 'Crime', 'Thriller', 'Horror', 'Romance'}
            if any(g in genres for g in exploitation_genres):
                return self._check_cap('Brazilian Exploitation')

        # PINKU EIGA
        # Country: JP + Year: 1960-1989 + adult/erotic indicators
        # Note: TMDb doesn't have "adult" genre reliably, so also check director
        if 'JP' in countries and year and 1960 <= year <= 1989:
            # Check known Pinku directors
            if any(d in director_lower for d in self.director_mappings['Pinku Eiga']):
                return self._check_cap('Pinku Eiga')
            # Drama/Romance from Japan in this era likely Pinku
            if 'Drama' in genres or 'Romance' in genres:
                return self._check_cap('Pinku Eiga')

        # GIALLO
        # Country: IT + Year: 1960-1989 + horror/thriller/mystery
        if 'IT' in countries and year and 1960 <= year <= 1989:
            giallo_genres = {'Horror', 'Thriller', 'Mystery'}
            if any(g in genres for g in giallo_genres):
                # Extra confidence if known giallo director
                if any(d in director_lower for d in self.director_mappings['Giallo']):
                    return self._check_cap('Giallo')
                # Or just by genre
                return self._check_cap('Giallo')

        # HONG KONG ACTION
        # Country: HK (or CN with specific directors) + action/crime/thriller
        if 'HK' in countries or 'CN' in countries:
            action_genres = {'Action', 'Crime', 'Thriller'}
            if any(g in genres for g in action_genres):
                return self._check_cap('Hong Kong Action')
            # Also martial arts, but TMDb doesn't have that genre - check directors
            if any(d in director_lower for d in self.director_mappings['Hong Kong Action']):
                return self._check_cap('Hong Kong Action')

        # BLAXPLOITATION
        # Country: US + Year: 1970-1979 + action/crime
        # This is tricky - need additional signals beyond just genre
        if 'US' in countries and year and 1970 <= year <= 1979:
            if 'Action' in genres or 'Crime' in genres:
                # Check for known Blaxploitation directors
                if any(d in director_lower for d in self.director_mappings['Blaxploitation']):
                    return self._check_cap('Blaxploitation')
                # Note: Most Blaxploitation films should be in explicit lookup table
                # to avoid false positives

        # AMERICAN EXPLOITATION
        # Country: US + Year: 1960-1989 + known exploitation directors
        if 'US' in countries and year and 1960 <= year <= 1989:
            if any(d in director_lower for d in self.director_mappings['American Exploitation']):
                return self._check_cap('American Exploitation')

        # EUROPEAN SEXPLOITATION
        # Countries: FR, IT, DE + Year: 1960-1980 + Drama/Romance + known directors
        if any(c in countries for c in ['FR', 'IT', 'DE', 'BE']) and year and 1960 <= year <= 1980:
            if 'Drama' in genres or 'Romance' in genres:
                if any(d in director_lower for d in self.director_mappings['European Sexploitation']):
                    return self._check_cap('European Sexploitation')

        # MUSIC FILMS
        # Genre: Music, Documentary (music), Musical
        music_genres = {'Music', 'Musical'}
        if any(g in genres for g in music_genres):
            return self._check_cap('Music Films')
        # Documentary about music
        if 'Documentary' in genres and 'Music' in genres:
            return self._check_cap('Music Films')

        # CULT ODDITIES
        # Catch-all for weird films that don't fit elsewhere
        # This would require additional heuristics or should come from explicit lookup

        return None

    def _check_cap(self, category: str) -> Optional[str]:
        """Check if category has reached cap"""
        if category not in self.caps:
            return category

        if self.counts[category] >= self.caps[category]:
            logger.warning(f"Category '{category}' at cap ({self.caps[category]})")
            return None

        self.counts[category] += 1
        return category

    def increment_count(self, category: str):
        """Manually increment category count (for explicit lookups)"""
        self.counts[category] += 1

    def get_stats(self) -> Dict:
        """Get category classification statistics"""
        return {
            'counts': dict(self.counts),
            'caps': self.caps,
            'available': {cat: self.caps[cat] - self.counts[cat] for cat in self.caps}
        }
