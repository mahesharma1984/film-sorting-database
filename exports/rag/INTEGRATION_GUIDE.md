# RAG Integration Guide

Step-by-step instructions for adding the RAG verification layer to your project.

**Prerequisites:**
- Python 3.8+
- A `docs/` directory with markdown files
- A `docs/CORE_DOCUMENTATION_INDEX.md` (from DMK templates)

**Time:** ~15 minutes for setup, ~5 minutes for customization

---

## Step 1: Copy the Package (2 minutes)

```bash
# From your project root
cp -r path/to/exports/rag/rag/ ./rag/
```

Your project structure should look like:
```
your-project/
├── CLAUDE.md
├── docs/
│   ├── CORE_DOCUMENTATION_INDEX.md
│   ├── DEVELOPER_GUIDE.md
│   └── ...
├── rag/                    # <- New
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py
│   ├── chunker.py
│   ├── metadata.py
│   ├── indexer.py
│   ├── retriever.py
│   ├── precision_filter.py
│   ├── structured_lookup.py
│   └── query.py
└── ...
```

## Step 2: Install Dependencies (1 minute)

```bash
pip install sentence-transformers rank-bm25 numpy
```

Or add to your `requirements.txt`:
```
sentence-transformers>=2.2.0
rank-bm25>=0.2.2
numpy>=1.24.0
```

**Optional:** `pip install tqdm` for progress bars during indexing.

## Step 3: Customize Configuration (5 minutes)

Edit `rag/config.py`. The key sections to customize:

### 3a. Paths (if non-standard)

```python
# Only change if your docs aren't in docs/
DOCS_ROOT = Path("docs")
CORE_DOC_INDEX = DOCS_ROOT / "CORE_DOCUMENTATION_INDEX.md"
```

### 3b. Protected Heading Keywords

```python
# Keywords that prevent chunk merging.
# Add domain terms for sections that should stay atomic.
PROTECTED_HEADING_KEYWORDS = ["stage", "contract", "api", "endpoint"]
```

### 3c. Excluded Paths

```python
# Skip these directories during indexing
EXCLUDED_PATHS = [
    "docs/issues/",        # Issue tracker files
    "docs/generated/",     # Auto-generated docs
]
```

### 3d. Abbreviation Map (in precision_filter.py)

Edit `rag/precision_filter.py` to add your project's abbreviations:

```python
ABBREVIATION_MAP = {
    # Keep the common ones
    'api': 'application programming interface',
    'llm': 'large language model',
    'ci': 'continuous integration',

    # Add your project-specific ones
    'auth': 'authentication',
    'db': 'database',
    'mdd': 'measurement driven development',
    'rp': 'reasoning precision',
}
```

### 3e. Query Type Patterns (in precision_filter.py)

Edit `rag/precision_filter.py` to define your project's query categories:

```python
QUERY_TYPE_PATTERNS = {
    'architecture': {
        'keywords': {'architecture', 'pipeline', 'system', 'component'},
        'canonical_file': 'docs/architecture/SYSTEM_ARCHITECTURE.md'
    },
    'debugging': {
        'keywords': {'debug', 'error', 'bug', 'fix', 'broken'},
        'canonical_file': 'docs/DEBUG_RUNBOOK.md'
    },
    # Add your domain-specific categories
    'metrics': {
        'keywords': {'metric', 'measurement', 'score', 'quality'},
        'canonical_file': 'docs/architecture/METRICS.md'
    },
}
```

## Step 4: Ensure CORE_DOCUMENTATION_INDEX.md Has the Right Tables

The RAG system reads two tables from your `CORE_DOCUMENTATION_INDEX.md`:

### Quick Reference Table

Used for structured lookup (fast, deterministic matching):

```markdown
## Quick Reference

| Question | Answer | Source |
|---|---|---|
| How do I set up the project? | See setup guide | `docs/DEVELOPER_GUIDE.md` |
| What's the architecture? | Component overview | `docs/architecture/SYSTEM_ARCHITECTURE.md` |
| How do I debug an issue? | Follow triage flow | `docs/DEBUG_RUNBOOK.md` |
```

**The parser extracts the Question and the file path in backticks.**

### Canonical Sources Table

Used for concept-to-file routing:

```markdown
## Canonical Sources

| Concept | Canonical Source | Status |
|---|---|---|
| **System architecture** | `docs/architecture/SYSTEM_ARCHITECTURE.md` | AUTHORITATIVE |
| **Development guide** | `docs/DEVELOPER_GUIDE.md` | AUTHORITATIVE |
| **Debugging procedures** | `docs/DEBUG_RUNBOOK.md` | AUTHORITATIVE |
```

**The parser maps bold concept names to file paths.**

Both tables are already in the DMK template for `CORE_DOCS_INDEX.md`. Just fill them in with your project's actual docs.

## Step 5: Build the Index (1 minute)

```bash
python -m rag.indexer
```

Output:
```
Building RAG index...
Loading metadata from docs/CORE_DOCUMENTATION_INDEX.md...
  Loaded metadata for 8 files
Discovering markdown files in docs/...
  Found 25 files (0 excluded)
Chunked 25 files into 120 chunks
Generating embeddings...
  Generated 120 embeddings (384-dim)
Writing index to outputs/rag/index.jsonl...
Building Quick Reference index...
  Found 6 Quick Reference entries

Index build complete!
  Files processed: 25
  Chunks created: 120
  Avg chunk size: 32 lines
  Build time: 18.3s
```

**Add to .gitignore:**
```
outputs/rag/
```

## Step 6: Test It (2 minutes)

```bash
# Basic query
python -m rag.query "How does the system handle errors?"

# JSON output (for scripting)
python -m rag.query "deployment procedure" --json

# Filter by authority
python -m rag.query "API contracts" --filter AUTHORITATIVE

# More results
python -m rag.query "testing strategy" --top 10
```

**Programmatic usage:**
```python
from rag.query import query_docs

results = query_docs("How does authentication work?", top_k=3)
for r in results:
    print(f"[{r['final_score']:.2f}] {r['section_reference']}")
```

## Step 7: Add to CLAUDE.md (2 minutes)

Add a RAG section to your CLAUDE.md so Claude Code knows to use it:

```markdown
## Documentation Search

Query the RAG index for task-relevant documentation:

- **RAG doc search:** `python -m rag.query "your question"`
  - Semantic search across all docs
  - Returns: Top-5 ranked sections with scores
  - <100ms, $0 cost (local embeddings)
  - **When to use:** Cross-cutting queries, quick lookups, methodology verification
  - **When NOT to use:** Learning architecture from scratch (use WORK_ROUTER.md)

- **Rebuild index** (after adding/changing docs): `python -m rag.indexer --force`
```

## Step 8: Rebuild When Docs Change

The index doesn't auto-update. Rebuild after significant doc changes:

```bash
python -m rag.indexer --force
```

**When to rebuild:**
- After adding new documentation files
- After major edits to existing docs
- After updating CORE_DOCUMENTATION_INDEX.md

**When NOT to rebuild:**
- After minor typo fixes
- After code-only changes (docs unchanged)

---

## Troubleshooting

### "No results found"
- Is the index built? Check `outputs/rag/index.jsonl` exists
- Are your docs in `docs/`? Check `DOCS_ROOT` in config.py
- Rebuild: `python -m rag.indexer --force`

### Results seem irrelevant
- Add project-specific abbreviations to `ABBREVIATION_MAP`
- Add query type patterns to `QUERY_TYPE_PATTERNS`
- Check that your `CORE_DOCUMENTATION_INDEX.md` has accurate canonical sources

### "sentence-transformers not found"
- Install: `pip install sentence-transformers numpy`
- The first run downloads the model (~90MB). Needs internet connection.

### Index build is slow
- Normal: ~20-30 seconds for 50-100 files
- The model download (first time only) takes 1-2 minutes
- Progress bars: `pip install tqdm`

---

## Advanced: Authority Metadata

For best results, add status metadata to your docs. The RAG system reads two sources:

### 1. CORE_DOCUMENTATION_INDEX.md tables (recommended)

Status in the Canonical Sources table is automatically parsed.

### 2. File headers (fallback)

If a file isn't in the index, the parser checks the first 50 lines for:

```markdown
**Version:** 2.0
**Last Updated:** 2026-02-15
**Status:** AUTHORITATIVE
**Purpose:** System architecture and contracts
```

### Authority Levels

| Level | Boost | When to Use |
|---|---|---|
| AUTHORITATIVE | 1.0x | Canonical, actively maintained |
| STABLE | 0.7x | Reliable but not primary |
| unmarked | 0.4x | No status declared |
| ARCHIVED | 0.1x | Historical, may be outdated |

Documents tagged AUTHORITATIVE will consistently rank above unmarked docs for the same query. This prevents stale or peripheral docs from crowding out the canonical sources.
