"""RAG system configuration.

CUSTOMIZE: This file contains all tunable parameters. Most defaults work well
out of the box. The sections marked CUSTOMIZE are the ones you'll want to edit
for your project.
"""
from pathlib import Path

# =============================================================================
# CUSTOMIZE: Paths
# =============================================================================
# Where your documentation lives and where the index should be stored.

DOCS_ROOT = Path("docs")
ADDITIONAL_DOCS_ROOTS = [
    Path("exports/skills"),         # Methodology skill docs (9 skills)
    Path("exports/knowledge-base"), # Theoretical foundations (8 docs)
]
OUTPUT_DIR = Path("output/rag")  # Film project uses output/ not outputs/
INDEX_FILE = OUTPUT_DIR / "index.jsonl"
EMBEDDINGS_FILE = OUTPUT_DIR / "embeddings.npy"
BUILD_LOG_FILE = OUTPUT_DIR / "build_log.jsonl"
CORE_DOC_INDEX = DOCS_ROOT / "CORE_DOCUMENTATION_INDEX.md"

# =============================================================================
# Model settings (usually no change needed)
# =============================================================================

EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384

# =============================================================================
# Scoring weights
# =============================================================================
# How much each signal contributes to the final ranking.
# Semantic: embedding similarity (captures meaning)
# Keyword: BM25 exact term matching (captures precision)
# Authority: document status and freshness (captures trust)

SEMANTIC_WEIGHT = 0.6
KEYWORD_WEIGHT = 0.25
AUTHORITY_WEIGHT = 0.15

# =============================================================================
# Authority boost values
# =============================================================================
# CUSTOMIZE: Define authority levels for your documentation.
# Documents in CORE_DOCUMENTATION_INDEX.md can be tagged with status.
# Higher boost = more likely to appear in results.

AUTHORITY_BOOST = {
    "AUTHORITATIVE": 1.0,   # Canonical, actively maintained docs
    "STABLE": 0.7,          # Reliable but not primary
    "unmarked": 0.4,        # No status declared
    "ARCHIVED": 0.1         # Historical, may be outdated
}
CANONICAL_BOOST = 0.2       # Extra boost for canonical sources
MAX_AUTHORITY_SCORE = 1.2

# =============================================================================
# Chunking parameters
# =============================================================================

MIN_CHUNK_LINES = 20       # Merge chunks smaller than this into parent
MAX_CHUNK_LINES = 500      # Warning threshold (not enforced)
MIN_SECTION_FREQ = 1       # Include all sections

# CUSTOMIZE: Keywords that prevent chunk merging.
# Chunks containing these words in their heading are kept atomic even if small.
# Add domain-specific terms for sections that should never be merged.
PROTECTED_HEADING_KEYWORDS = [
    "stage", "contract", "api", "endpoint",  # DMK defaults
    "satellite", "director", "decade", "tier",  # Film-specific
    "category", "giallo", "exploitation", "canon"  # Film categories
]

# =============================================================================
# Query parameters
# =============================================================================

DEFAULT_TOP_K = 5
VERIFIED_DATE_DECAY_DAYS = 60   # Freshness half-life in days

# =============================================================================
# Layer 1: Quick Reference
# =============================================================================

QUICK_REFERENCE_EMBEDDINGS_FILE = OUTPUT_DIR / "quick_reference_embeddings.npy"
QUICK_REFERENCE_INDEX_FILE = OUTPUT_DIR / "quick_reference_index.json"
QUICK_REFERENCE_THRESHOLD = 0.65
QUICK_REFERENCE_TOP_K = 3
ENABLE_QUICK_REFERENCE = True

# =============================================================================
# Layer 2: Canonical Source Boosting
# =============================================================================

CANONICAL_BOOST_MULTIPLIER = 5.0
ENABLE_CANONICAL_BOOST = True

# =============================================================================
# Layer 3: Routing Suppression
# =============================================================================
# Patterns that identify "routing" content (docs that point to other docs).
# If a routing doc and the doc it points to both appear in results, the
# routing doc is suppressed in favor of the actual content.

ROUTING_PATTERNS = [
    r"See \[?([A-Z_][A-Za-z_]+\.md)\]?",
    r"\[([A-Z_]+\.md)\]\([^)]+\)",
    r"See ([A-Z_]+\.md) \u00a7",
    r"Details:\s*See \[?([A-Z_]+\.md)\]?",
]
ENABLE_ROUTING_SUPPRESSION = True

# =============================================================================
# CUSTOMIZE: Indexing exclusions
# =============================================================================
# Paths under DOCS_ROOT to skip during indexing.
# Typically: issue trackers, generated reports, vendor docs.

EXCLUDED_PATHS = [
    # "docs/issues/",  # Uncomment to exclude issues (we'll include them for now)
    # "docs/generated/",
    ".git",  # Skip git metadata
    "docs/archive/",  # Historical artifacts — 17 docs archived after consolidation
]

# =============================================================================
# Phase A: Precision Filter (R/P Split Retrieval)
# =============================================================================

ENABLE_PRECISION_FILTER = True
PRECISION_MIN_KEYWORD_OVERLAP = 0.3
PRECISION_SUPPRESS_NAVIGATION = True
PRECISION_EXCLUDED_PATTERNS = [
    # r'docs/reports/.*\.md',
]

# =============================================================================
# Structured Lookup (deterministic keyword matching before embeddings)
# =============================================================================

ENABLE_STRUCTURED_LOOKUP = True

# Quick Reference matching
STRUCTURED_QR_THRESHOLD = 0.4
STRUCTURED_QR_PHRASE_BOOST_BIGRAM = 0.3
STRUCTURED_QR_PHRASE_BOOST_TRIGRAM = 0.5
STRUCTURED_QR_MIN_PHRASE_LENGTH = 6

# Canonical Sources matching
STRUCTURED_CANONICAL_THRESHOLD = 0.8

# Within-file scoring weights
STRUCTURED_WITHIN_FILE_SEMANTIC_WEIGHT = 0.7
STRUCTURED_WITHIN_FILE_KEYWORD_WEIGHT = 0.3
STRUCTURED_WITHIN_FILE_AUTHORITY_WEIGHT = 0.0
