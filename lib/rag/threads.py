"""
Thread discovery using keyword overlap (Jaccard similarity)

PRECISION layer: Jaccard computation
REASONING layer: Threshold tuning, connection ranking
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class ThreadDiscovery:
    """Discover thematic threads using keyword overlap"""

    def __init__(self, index_path: Path):
        """
        Args:
            index_path: Path to thread_keywords.json
        """
        self.index_path = index_path
        self.index = self._load_index()

    def _load_index(self) -> Dict:
        """Load keyword index from JSON"""
        if not self.index_path.exists():
            raise FileNotFoundError(
                f"Thread index not found: {self.index_path}\n"
                "Run: python scripts/build_thread_index.py"
            )

        with open(self.index_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def query_thread(
        self,
        category: str,
        film_keywords: List[str],
        min_overlap: float = 0.15
    ) -> Optional[Dict]:
        """
        Score a film's connection to a Satellite category

        Args:
            category: Satellite category name (e.g., 'Giallo')
            film_keywords: List of TMDb keywords from film
            min_overlap: Minimum Jaccard score to return result (0.0-1.0)

        Returns:
            {
                'category': 'Giallo',
                'jaccard_score': 0.25,
                'overlap_count': 5,
                'shared_keywords': ['murder', 'mystery', 'psycho-killer'],
                'category_keyword_count': 45,
                'film_keyword_count': 12
            }
            or None if no overlap or below threshold
        """
        if category not in self.index:
            logger.warning(f"Category not in index: {category}")
            return None

        category_data = self.index[category]
        category_keywords = {kw['keyword'] for kw in category_data['keywords']}

        if not category_keywords or not film_keywords:
            return None

        # Normalize to lowercase
        film_kw_set = {kw.lower() for kw in film_keywords}

        # Jaccard similarity: |A ∩ B| / |A ∪ B|
        intersection = category_keywords & film_kw_set
        union = category_keywords | film_kw_set

        if not union or not intersection:
            return None

        jaccard = len(intersection) / len(union)

        if jaccard < min_overlap:
            return None

        return {
            'category': category,
            'jaccard_score': jaccard,
            'overlap_count': len(intersection),
            'shared_keywords': sorted(list(intersection)),
            'category_keyword_count': len(category_keywords),
            'film_keyword_count': len(film_kw_set)
        }

    def discover_threads_for_film(
        self,
        film_keywords: List[str],
        min_overlap: float = 0.15,
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find all Satellite threads for a film, ranked by Jaccard score

        Args:
            film_keywords: List of TMDb keywords from film
            min_overlap: Minimum Jaccard score threshold
            top_k: Maximum number of threads to return

        Returns:
            List of thread connections, sorted by jaccard_score descending
        """
        threads = []

        for category in self.index.keys():
            result = self.query_thread(category, film_keywords, min_overlap)
            if result:
                threads.append(result)

        # Sort by Jaccard score (descending)
        threads.sort(key=lambda x: x['jaccard_score'], reverse=True)

        return threads[:top_k]

    def get_category_keywords(self, category: str, top_k: int = 20) -> List[Dict]:
        """
        Get top keywords for a category by frequency

        Args:
            category: Satellite category name
            top_k: Number of keywords to return

        Returns:
            List of keyword dicts from index
        """
        if category not in self.index:
            return []

        return self.index[category]['keywords'][:top_k]
