#!/usr/bin/env python3
"""
OMDb API client with persistent JSON caching
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict

import requests

logger = logging.getLogger(__name__)


class OMDbClient:
    """Interface to the Open Movie Database API with persistent caching"""

    def __init__(self, api_key: str, cache_path: Path):
        self.api_key = api_key
        self.base_url = "http://www.omdbapi.com/"
        self.cache_path = cache_path
        self.cache = self._load_cache()
        self.cache_hits = 0
        self.cache_misses = 0

    def _load_cache(self) -> Dict:
        """Load cache from JSON file"""
        if self.cache_path.exists():
            try:
                with open(self.cache_path, 'r', encoding='utf-8') as f:
                    cache = json.load(f)
                logger.info(f"Loaded OMDb cache with {len(cache)} entries")
                return cache
            except Exception as e:
                logger.warning(f"Could not load OMDb cache: {e}. Starting fresh.")
                return {}
        return {}

    def _save_cache(self):
        """Save cache to JSON file"""
        try:
            # Ensure output directory exists
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved OMDb cache with {len(self.cache)} entries")
        except Exception as e:
            logger.error(f"Could not save OMDb cache: {e}")

    def _make_cache_key(self, title: str, year: Optional[int]) -> str:
        """Generate cache key from title and year"""
        return f"{title}|{year if year else 'None'}"

    def search_film(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Search for film and return metadata (with caching)

        Returns dict with keys: title, year, director, genres, countries
        or None if not found
        """
        if not self.api_key:
            return None

        cache_key = self._make_cache_key(title, year)

        # Check cache first
        if cache_key in self.cache:
            self.cache_hits += 1
            logger.debug(f"OMDb cache hit: {title} ({year})")
            return self.cache[cache_key]

        # Cache miss - query API
        self.cache_misses += 1
        logger.debug(f"OMDb cache miss: {title} ({year}) - querying OMDb")

        result = self._query_api(title, year)

        # Cache result (even if None)
        self.cache[cache_key] = result
        self._save_cache()

        return result

    def _query_api(self, title: str, year: Optional[int]) -> Optional[Dict]:
        """Make actual API request to OMDb"""
        try:
            # Build request params
            params = {
                'apikey': self.api_key,
                't': title,
                'type': 'movie'
            }

            if year:
                params['y'] = str(year)

            response = requests.get(
                self.base_url,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            # Check if film was found
            if data.get('Response') == 'False':
                logger.debug(f"No OMDb results for '{title}' ({year}): {data.get('Error', 'Unknown error')}")
                return None

            # Extract director
            director = None
            if data.get('Director') and data['Director'] != 'N/A':
                # OMDb returns comma-separated directors if multiple
                directors = data['Director'].split(', ')
                director = directors[0]  # Take first director

            # Extract countries
            countries = []
            if data.get('Country') and data['Country'] != 'N/A':
                # OMDb returns comma-separated countries
                country_names = data['Country'].split(', ')
                # Map to ISO codes (approximate - we'll use first country)
                countries = self._map_countries_to_codes(country_names)

            # Extract genres
            genres = []
            if data.get('Genre') and data['Genre'] != 'N/A':
                # OMDb returns comma-separated genres
                genres = [g.strip() for g in data['Genre'].split(',')]

            # Extract year from response
            film_year = year
            if data.get('Year') and data['Year'] != 'N/A':
                # OMDb returns year as string, sometimes with range like "2019-2020"
                year_str = data['Year'].split('–')[0].split('-')[0]  # Take first year
                try:
                    film_year = int(year_str)
                except ValueError:
                    pass

            # Build result (matching TMDb format)
            result = {
                'title': data.get('Title', title),
                'year': film_year,
                'director': director,
                'genres': genres,
                'countries': countries,
                'original_language': None  # OMDb doesn't provide original language
            }

            logger.info(f"OMDb: '{title}' ({year}) → '{result['title']}' dir:{director} countries:{countries}")

            return result

        except requests.exceptions.Timeout:
            logger.warning(f"OMDb API timeout for '{title}' ({year})")
            return None
        except requests.exceptions.HTTPError as e:
            logger.warning(f"OMDb API HTTP error for '{title}': {e}")
            return None
        except Exception as e:
            logger.debug(f"OMDb API error for '{title}': {e}")
            return None

    def _map_countries_to_codes(self, country_names: list) -> list:
        """Map country names to ISO codes (simplified mapping for common countries)"""
        country_map = {
            'Italy': 'IT',
            'France': 'FR',
            'Japan': 'JP',
            'Brazil': 'BR',
            'USA': 'US',
            'United States': 'US',
            'UK': 'GB',
            'United Kingdom': 'GB',
            'Germany': 'DE',
            'West Germany': 'DE',
            'Spain': 'ES',
            'Hong Kong': 'HK',
            'South Korea': 'KR',
            'Mexico': 'MX',
            'Argentina': 'AR',
            'Canada': 'CA',
            'Australia': 'AU',
            'Sweden': 'SE',
            'Denmark': 'DK',
            'Norway': 'NO',
            'Poland': 'PL',
            'Russia': 'RU',
            'Soviet Union': 'SU',
            'China': 'CN',
            'India': 'IN',
            'Netherlands': 'NL',
            'Belgium': 'BE',
            'Switzerland': 'CH',
            'Austria': 'AT',
            'Greece': 'GR',
            'Turkey': 'TR',
            'Finland': 'FI',
            'Czechoslovakia': 'CS',
            'Czech Republic': 'CZ',
            'Yugoslavia': 'YU',
            'Ireland': 'IE',
            'Portugal': 'PT',
            'New Zealand': 'NZ',
            'Thailand': 'TH',
            'Philippines': 'PH',
            'Indonesia': 'ID',
            'Taiwan': 'TW',
            'Singapore': 'SG',
            'Malaysia': 'MY',
            'Vietnam': 'VN',
            'Cuba': 'CU',
            'Chile': 'CL',
            'Colombia': 'CO',
            'Peru': 'PE',
            'Venezuela': 'VE',
        }

        codes = []
        for name in country_names:
            name = name.strip()
            if name in country_map:
                codes.append(country_map[name])
            else:
                # Unknown country - just use first 2 letters uppercase as fallback
                codes.append(name[:2].upper() if len(name) >= 2 else name.upper())

        return codes

    def get_cache_stats(self) -> Dict:
        """Get cache performance statistics"""
        total = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total * 100) if total > 0 else 0

        return {
            'hits': self.cache_hits,
            'misses': self.cache_misses,
            'total_queries': total,
            'hit_rate': hit_rate,
            'cache_size': len(self.cache)
        }
