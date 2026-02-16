#!/usr/bin/env python3
"""
TMDb API client with persistent JSON caching
"""

import json
import logging
from pathlib import Path
from typing import Optional, Dict, List

import requests

logger = logging.getLogger(__name__)


class TMDbClient:
    """Interface to The Movie Database API with persistent caching"""

    def __init__(self, api_key: str, cache_path: Path):
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
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
                logger.info(f"Loaded TMDb cache with {len(cache)} entries")
                return cache
            except Exception as e:
                logger.warning(f"Could not load cache: {e}. Starting fresh.")
                return {}
        return {}

    def _save_cache(self):
        """Save cache to JSON file"""
        try:
            # Ensure output directory exists
            self.cache_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.cache_path, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved TMDb cache with {len(self.cache)} entries")
        except Exception as e:
            logger.error(f"Could not save cache: {e}")

    def _make_cache_key(self, title: str, year: Optional[int]) -> str:
        """Generate cache key from title and year"""
        return f"{title}|{year if year else 'None'}"

    def search_film(self, title: str, year: Optional[int] = None) -> Optional[Dict]:
        """
        Search for film and return metadata (with caching)

        Returns dict with keys: title, year, director, genres, countries,
        cast, popularity, vote_count, keywords
        or None if not found
        """
        if not self.api_key:
            return None

        cache_key = self._make_cache_key(title, year)

        # Check cache first
        if cache_key in self.cache:
            self.cache_hits += 1
            logger.debug(f"Cache hit: {title} ({year})")
            return self.cache[cache_key]

        # Cache miss - query API
        self.cache_misses += 1
        logger.debug(f"Cache miss: {title} ({year}) - querying TMDb")

        result = self._query_api(title, year)

        # Cache result (even if None)
        self.cache[cache_key] = result
        self._save_cache()

        return result

    def _query_api(self, title: str, year: Optional[int]) -> Optional[Dict]:
        """Make actual API request to TMDb"""
        try:
            # Search for movie
            params = {
                'api_key': self.api_key,
                'query': title,
                'include_adult': True
            }

            if year:
                params['year'] = year

            response = requests.get(
                f"{self.base_url}/search/movie",
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            if not data.get('results'):
                logger.debug(f"No TMDb results for '{title}' ({year})")
                return None

            # Get first result
            film_data = data['results'][0]
            film_id = film_data['id']

            # Get detailed movie payload + credits + keywords in one call
            details_response = requests.get(
                f"{self.base_url}/movie/{film_id}",
                params={'api_key': self.api_key, 'append_to_response': 'credits,keywords'},
                timeout=10
            )
            details_response.raise_for_status()
            details_data = details_response.json()

            # Extract director
            director = None
            credits_data = details_data.get('credits', {})
            for crew_member in credits_data.get('crew', []):
                if crew_member['job'] == 'Director':
                    director = crew_member['name']
                    break

            # Extract genres from detail payload
            full_genres = [
                genre.get('name') for genre in details_data.get('genres', [])
                if genre.get('name')
            ]

            # Fallback for legacy cached/partial responses
            if not full_genres and film_data.get('genre_ids'):
                for genre_id in film_data['genre_ids']:
                    genre_name = self._get_genre_name(genre_id)
                    if genre_name:
                        full_genres.append(genre_name)

            # Extract countries (production + origin fallback)
            countries = []
            for country in details_data.get('production_countries', []):
                code = country.get('iso_3166_1')
                if code and code not in countries:
                    countries.append(code)

            for country in details_data.get('origin_country', []):
                if country not in countries:
                    countries.append(country)

            if not countries:
                for country in film_data.get('origin_country', []):
                    if country not in countries:
                        countries.append(country)

            # Top-billed cast names for Popcorn signal
            cast = [
                person.get('name') for person in credits_data.get('cast', [])[:8]
                if person.get('name')
            ]

            # Extract keywords from nested TMDb structure (Issue #12)
            keywords = []
            keywords_data = details_data.get('keywords', {})
            if keywords_data:
                # TMDb returns: {'keywords': [{'id': 123, 'name': 'murder'}, ...]}
                keyword_list = keywords_data.get('keywords', [])
                keywords = [kw.get('name') for kw in keyword_list if kw.get('name')]

            release_date = details_data.get('release_date') or film_data.get('release_date')

            # Build result
            result = {
                'title': details_data.get('title') or film_data.get('title', title),
                'year': int(release_date[:4]) if release_date else year,
                'director': director,
                'genres': full_genres,
                'countries': countries,
                'cast': cast,
                'popularity': details_data.get('popularity'),
                'vote_count': details_data.get('vote_count'),
                'original_language': details_data.get('original_language') or film_data.get('original_language'),
                'keywords': keywords
            }

            logger.info(f"TMDb: '{title}' ({year}) → '{result['title']}' dir:{director} countries:{countries}")

            return result

        except requests.exceptions.Timeout:
            logger.warning(f"TMDb API timeout for '{title}' ({year})")
            return None
        except requests.exceptions.HTTPError as e:
            logger.warning(f"TMDb API HTTP error for '{title}': {e}")
            return None
        except Exception as e:
            logger.debug(f"TMDb API error for '{title}': {e}")
            return None

    def _get_genre_name(self, genre_id: int) -> Optional[str]:
        """Map TMDb genre ID to name"""
        # TMDb genre IDs (as of 2024)
        genre_map = {
            28: 'Action',
            12: 'Adventure',
            16: 'Animation',
            35: 'Comedy',
            80: 'Crime',
            99: 'Documentary',
            18: 'Drama',
            10751: 'Family',
            14: 'Fantasy',
            36: 'History',
            27: 'Horror',
            10402: 'Music',
            9648: 'Mystery',
            10749: 'Romance',
            878: 'Science Fiction',
            10770: 'TV Movie',
            53: 'Thriller',
            10752: 'War',
            37: 'Western'
        }
        return genre_map.get(genre_id)

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
