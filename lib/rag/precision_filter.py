"""Phase A: Precision Filter for RAG Retrieval.

Implements R/P Split by separating precision tasks (keyword matching, abbreviation
expansion, query classification) from reasoning tasks (semantic ranking).

Architecture: Phase A (PRECISION - code) -> Phase B (REASONING - embeddings)

CUSTOMIZE: Edit ABBREVIATION_MAP and QUERY_TYPE_PATTERNS for your project's
domain-specific terms and document structure.
"""
import re
from typing import Dict, List, Optional, Set, Tuple


# =============================================================================
# Stopwords
# =============================================================================
# Common English stopwords for keyword extraction.
# These are filtered out when extracting meaningful query terms.

STOPWORDS = {
    'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
    'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
    'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
    'could', 'should', 'may', 'might', 'shall', 'can', 'this', 'that',
    'these', 'those', 'it', 'its', 'not', 'no', 'if', 'so', 'as', 'about',
    'what', 'which', 'who', 'whom', 'how', 'when', 'where', 'why', 'all',
    'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some', 'such',
    'than', 'too', 'very', 'just', 'also', 'into', 'out', 'up', 'down',
    'then', 'here', 'there', 'any', 'only', 'own', 'same', 'above', 'below',
}


# =============================================================================
# CUSTOMIZE: Abbreviation Expansion
# =============================================================================
# Map project-specific abbreviations to their full forms.
# The RAG system expands these during query processing so both the
# abbreviation and its expansion contribute to matching.
#
# Example: If your project uses "MDD" for "measurement-driven development",
# add it here so queries like "MDD cycle" also match docs about
# "measurement-driven development".

ABBREVIATION_MAP = {
    # Common technical abbreviations (keep these)
    'api': 'application programming interface',
    'json': 'javascript object notation',
    'llm': 'large language model',
    'cli': 'command line interface',
    'ci': 'continuous integration',
    'cd': 'continuous deployment',

    # Film classification abbreviations
    'hk': 'hong kong',
    'br': 'brazil brazilian',
    'jp': 'japan japanese',
    'it': 'italy italian',
    'tmdb': 'the movie database',
    'wip': 'women in prison',
    'pinku': 'pinku eiga pink film',
}


def expand_abbreviations(query_text: str) -> str:
    """Expand known abbreviations in query text.

    Keeps original + adds expansion (doesn't replace). This ensures both the
    abbreviation and its expansion contribute to keyword matching.

    Args:
        query_text: Raw query from user

    Returns:
        Query with abbreviations expanded

    Example:
        "API endpoint issues" -> "API application programming interface endpoint issues"
    """
    query_lower = query_text.lower()
    expanded = query_text

    for abbrev, expansion in ABBREVIATION_MAP.items():
        pattern = r'\b' + re.escape(abbrev) + r'\b'
        if re.search(pattern, query_lower):
            expanded = re.sub(
                pattern,
                f"{abbrev} {expansion}",
                expanded,
                flags=re.IGNORECASE
            )

    return expanded


# =============================================================================
# Keyword Extraction
# =============================================================================

def extract_query_keywords(query_text: str, min_length: int = 3) -> Set[str]:
    """Extract meaningful keywords from query.

    Args:
        query_text: Query text (after abbreviation expansion)
        min_length: Minimum keyword length (default: 3)

    Returns:
        Set of lowercase keywords (stopwords removed)

    Example:
        "How does the authentication flow work?" -> {"authentication", "flow", "work"}
    """
    text_lower = query_text.lower()

    # Tokenize (keep version numbers and dotted numbers together)
    words = re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", text_lower)

    keywords = set()
    for word in words:
        if len(word) >= min_length and word not in STOPWORDS:
            keywords.add(word)

            # Add stemmed versions
            if word.endswith('ing'):
                keywords.add(word[:-3])
            elif word.endswith('ed'):
                keywords.add(word[:-2])

    return keywords


# =============================================================================
# CUSTOMIZE: Query Classification
# =============================================================================
# Define query types for your project. Each type maps to keywords and
# optionally a canonical file where answers are most likely found.
#
# This helps the precision filter prioritize the right documents.
# Remove or modify these examples for your domain.

QUERY_TYPE_PATTERNS = {
    # Film classification query types
    'classification': {
        'keywords': {'classify', 'classification', 'sort', 'sorting', 'route', 'routing', 'organize'},
        'canonical_file': 'docs/DEVELOPER_GUIDE.md'
    },
    'satellite': {
        'keywords': {'satellite', 'giallo', 'exploitation', 'pinku', 'category', 'decade', 'boundaries'},
        'canonical_file': 'docs/SATELLITE_CATEGORIES.md'
    },
    'director': {
        'keywords': {'director', 'auteur', 'core', 'whitelist', 'filmography'},
        'canonical_file': 'docs/CORE_DIRECTOR_WHITELIST_FINAL.md'
    },
    'tier': {
        'keywords': {'tier', 'reference', 'canon', 'popcorn', 'unsorted', 'hierarchy'},
        'canonical_file': 'docs/theory/TIER_ARCHITECTURE.md'
    },
    'theory': {
        'keywords': {'theory', 'curatorial', 'margins', 'texture', 'wave', 'identity'},
        'canonical_file': 'docs/theory/README.md'
    },
    'film_lookup': {
        'keywords': {'film', 'films', 'movie', 'movies', 'title'},
        'patterns': [r'\b\d{4}\b'],  # Year patterns like "1975"
        'canonical_file': 'docs/SORTING_DATABASE.md'
    },
    'debugging': {
        'keywords': {'debug', 'error', 'bug', 'fix', 'broken', 'failing', 'crash', 'issue'},
        'canonical_file': 'docs/DEBUG_RUNBOOK.md'
    },
}


def classify_query_type(
    query_text: str,
    keywords: Set[str]
) -> Tuple[str, Optional[str]]:
    """Classify query type and identify canonical source.

    Args:
        query_text: Original query
        keywords: Extracted keywords

    Returns:
        (query_type, canonical_file_path)

    Example:
        "authentication error in login" -> ('debugging', 'docs/DEBUG_RUNBOOK.md')
    """
    query_lower = query_text.lower()

    for qtype, qtype_config in QUERY_TYPE_PATTERNS.items():
        # Check regex patterns first (more precise)
        if 'patterns' in qtype_config:
            for pattern in qtype_config['patterns']:
                if re.search(pattern, query_lower):
                    return (qtype, qtype_config.get('canonical_file'))

        # Check keyword overlap
        if 'keywords' in qtype_config:
            overlap = keywords & qtype_config['keywords']
            if overlap:
                return (qtype, qtype_config.get('canonical_file'))

    return ('general', None)


# =============================================================================
# Chunk Filtering
# =============================================================================

# CUSTOMIZE: Patterns for files to exclude from precision filter results
EXCLUDED_PATTERNS = [
    # r'docs/reports/.*\.md',
    # r'docs/generated/.*\.md',
]

# CUSTOMIZE: Navigation docs to suppress for concept queries
# These docs route to other docs rather than containing content themselves.
NAVIGATION_DOCS = [
    'docs/WORK_ROUTER.md',
    'docs/CORE_DOCUMENTATION_INDEX.md',
]

# CUSTOMIZE: Query types where navigation docs should be suppressed
CONCEPT_QUERY_TYPES = ['architecture', 'debugging', 'workflow']


def filter_chunks_by_precision(
    chunks: List[Dict],
    query_keywords: Set[str],
    query_type: str,
    canonical_file: Optional[str] = None,
    suppress_navigation: bool = True,
    min_keyword_overlap: float = 0.3
) -> List[int]:
    """Filter chunks using precision rules before embedding search.

    Reduces the candidate set from hundreds/thousands to ~50-100 chunks,
    making the subsequent semantic ranking faster and more accurate.

    Args:
        chunks: Full chunk list from index
        query_keywords: Extracted keywords
        query_type: Classified query type
        canonical_file: Canonical source file if detected
        suppress_navigation: Exclude navigation docs for concept queries
        min_keyword_overlap: Minimum fraction of keywords that must appear

    Returns:
        List of chunk indices that passed precision filters
    """
    candidate_indices = []

    for i, chunk in enumerate(chunks):
        source_file = chunk.get('source_file', '')
        content = chunk.get('content', '').lower()
        heading = chunk.get('heading_text', '').lower()

        # ========== Exclusion Filters ==========

        # Skip excluded file patterns
        if any(re.search(pattern, source_file) for pattern in EXCLUDED_PATTERNS):
            continue

        # Skip navigation docs for concept queries
        if suppress_navigation and query_type in CONCEPT_QUERY_TYPES:
            if any(nav_doc in source_file for nav_doc in NAVIGATION_DOCS):
                continue

        # ========== Inclusion Filters ==========

        # If canonical file detected, always include its chunks
        if canonical_file and canonical_file in source_file:
            candidate_indices.append(i)
            continue

        # Keyword presence filter
        combined_text = content + ' ' + heading
        keyword_hits = sum(1 for kw in query_keywords if kw in combined_text)

        min_keywords = max(1, len(query_keywords) * min_keyword_overlap)
        if keyword_hits >= min_keywords:
            candidate_indices.append(i)

    return candidate_indices
