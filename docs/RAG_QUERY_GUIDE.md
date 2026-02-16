# RAG Query Guide

**Purpose:** Query the film classification knowledge base using semantic search + keyword matching.

**Status:** Stage 1 Complete (Research Assistant)
**Version:** 0.2
**Last Updated:** 2026-02-16

---

## Quick Start

```bash
# Install dependencies (one-time)
pip install -r requirements_rag.txt

# Query the knowledge base
python -m lib.rag.query "How to classify Italian giallo from 1970s"

# Get more results
python -m lib.rag.query "Films by Jean-Luc Godard" --top 10

# Filter by authority level
python -m lib.rag.query "Satellite decade boundaries" --filter AUTHORITATIVE
```

---

## What Can You Query?

The RAG system indexes **769 chunks** from your documentation:

| Content Type | Count | Examples |
|--------------|-------|----------|
| **Film entries** | 276 films | Godard, Kubrick, Scorsese filmographies |
| **Theory essays** | ~50 sections | Tier architecture, satellite margins, auteur criteria |
| **Category definitions** | 12 categories | Giallo, Brazilian Exploitation, Pinku Eiga |
| **Developer docs** | ~400 sections | Classification workflow, debug runbook, folder structure |
| **Issue history** | ~30 sections | Past bugs, architectural decisions |

---

## Common Query Patterns

### 1. Find Similar Films

```bash
# Find films by a specific director
python -m lib.rag.query "Films by Jean-Luc Godard" --top 5

# Find films in a category
python -m lib.rag.query "Brazilian exploitation films from 1970s"

# Find films with similar themes
python -m lib.rag.query "Italian horror thrillers about art and murder"
```

**Example Output:**
```
1. [1.10] SORTING_DATABASE.md § Passion (1982)
   docs/SORTING_DATABASE.md:305-305
   semantic=0.59, keyword=1.00, authority=3.00

2. [1.09] SORTING_DATABASE.md § La Chinoise (1967)
   docs/SORTING_DATABASE.md:55-55
   semantic=0.59, keyword=0.97, authority=3.00
```

### 2. Classification Questions

```bash
# How to classify a specific type of film
python -m lib.rag.query "How to classify Italian giallo from 1970s"

# Understand category boundaries
python -m lib.rag.query "What years are valid for Hong Kong Action category"

# Tier placement questions
python -m lib.rag.query "Should a Kubrick masterpiece go in Core or Reference"
```

### 3. Category Research

```bash
# Get category definition
python -m lib.rag.query "What is Giallo category definition"

# Understand decade boundaries
python -m lib.rag.query "Satellite decade boundaries"

# Find directors in a category
python -m lib.rag.query "Which directors are in Giallo satellite"
```

### 4. Theory & Design Decisions

```bash
# Understand tier architecture
python -m lib.rag.query "Why are tiers organized Core Reference Satellite Popcorn"

# Learn about format signals
python -m lib.rag.query "How are 35mm and Criterion tags handled"

# Understand R/P Split
python -m lib.rag.query "What is R/P Split reasoning vs precision"
```

### 5. Debug & Troubleshooting

```bash
# Past bugs and fixes
python -m lib.rag.query "Director lookup bugs in v0.1"

# Classification issues
python -m lib.rag.query "Films stuck in Unsorted"

# TMDb API issues
python -m lib.rag.query "TMDb enrichment failures"
```

---

## CLI Options

```bash
python -m lib.rag.query [OPTIONS] "your query"

Options:
  --top N                 Number of results (default: 5)
  --filter STATUS [...]   Filter by document authority level
                          Options: AUTHORITATIVE, STABLE, unmarked, ARCHIVED
  --json                  Output as JSON for scripting
  -h, --help             Show help message
```

### Authority Levels

Documents are ranked by authority:

| Status | Meaning | Boost |
|--------|---------|-------|
| **AUTHORITATIVE** | Canonical, actively maintained | 1.0x |
| **STABLE** | Reliable but not primary | 0.7x |
| **unmarked** | No status declared | 0.4x |
| **ARCHIVED** | Historical, may be outdated | 0.1x |

**Example:**
```bash
# Only show canonical sources
python -m lib.rag.query "Classification workflow" --filter AUTHORITATIVE

# Exclude archived docs
python -m lib.rag.query "Satellite categories" --filter AUTHORITATIVE STABLE unmarked
```

---

## Understanding Results

Each result shows:

```
1. [0.92] SATELLITE_CATEGORIES.md § GIALLO / ITALIAN HORROR-THRILLER
   docs/SATELLITE_CATEGORIES.md:13-40
   semantic=0.60, keyword=1.60, authority=0.40
```

**Score breakdown:**
- `[0.92]` - **Final score** (higher = more relevant)
- `semantic=0.60` - Embedding similarity (meaning-based matching)
- `keyword=1.60` - BM25 keyword matching (exact term overlap)
- `authority=0.40` - Document authority boost

**Hybrid scoring:** 60% semantic + 25% keyword + 15% authority

---

## Practical Workflows

### Workflow 1: Manual Curation (Current)

When reviewing Unsorted films:

```bash
# 1. Get film details
python classify.py /path/to/unsorted --dry-run

# 2. Query for similar films or categories
python -m lib.rag.query "Italian thriller from 1989 by unknown director"

# 3. Check category boundaries
python -m lib.rag.query "Giallo decade boundaries"

# 4. Make classification decision based on RAG context
# 5. Manually move file or update SORTING_DATABASE.md
```

### Workflow 2: Category Research

Before adding films to a satellite category:

```bash
# Check current films in category
python -m lib.rag.query "Films in Brazilian Exploitation category"

# Verify decade boundaries
python -m lib.rag.query "Brazilian Exploitation valid decades"

# Check capacity (cap)
python -m lib.rag.query "Brazilian Exploitation category cap limit"
```

### Workflow 3: Director Research

When encountering an unfamiliar director:

```bash
# Check if director is in Core whitelist
python -m lib.rag.query "Is Lucio Fulci a Core director"

# Find existing films by director
python -m lib.rag.query "Films by Dario Argento"

# Understand auteur criteria
python -m lib.rag.query "Core director whitelist criteria"
```

---

## When to Rebuild the Index

Rebuild after editing these files:

```bash
# Rebuild index (takes ~5 minutes)
python -m lib.rag.indexer

# Files that require rebuild:
# - docs/SORTING_DATABASE.md (film entries added/changed)
# - docs/SATELLITE_CATEGORIES.md (category definitions changed)
# - docs/theory/*.md (theory essays updated)
# - docs/CORE_DIRECTOR_WHITELIST_FINAL.md (directors added)
# - Any other markdown in docs/
```

**Index freshness check:**
```bash
# Compare timestamps
ls -lt docs/SORTING_DATABASE.md output/rag/index.jsonl

# If docs/ is newer, rebuild
python -m lib.rag.indexer
```

---

## JSON Output for Scripting

```bash
# Get JSON output
python -m lib.rag.query "Films by Godard" --json > results.json

# Parse with jq
python -m lib.rag.query "Giallo films" --json | jq '.results[0].content'
```

**JSON format:**
```json
{
  "query": "Films by Godard",
  "results": [
    {
      "score": 1.10,
      "source": "docs/SORTING_DATABASE.md",
      "heading": "Passion (1982)",
      "content": "- Passion (1982) → 1980s/Core/Jean-Luc Godard/",
      "line_range": "305-305",
      "metadata": {
        "type": "film_entry",
        "title": "Passion",
        "year": 1982,
        "tier": "1980s",
        "subdirectory": "Jean-Luc Godard"
      },
      "scores": {
        "semantic": 0.59,
        "keyword": 1.00,
        "authority": 3.00
      }
    }
  ]
}
```

---

## Performance

| Metric | Target | Actual |
|--------|--------|--------|
| **Query latency** | <1 second | ~0.3-0.5 seconds (after model load) |
| **Index build time** | <15 seconds | ~4.5 minutes (one-time) |
| **Index size** | <20MB | ~15MB (index.jsonl + embeddings.npy) |
| **Chunk count** | 350-450 | 769 chunks |
| **RAM usage** | <300MB | ~250MB |

**First query:** Slower (~3-5 seconds) due to model loading. Subsequent queries are fast.

---

## Troubleshooting

### Warning: "Could not find Quick Reference table"

**Issue:** Quick Reference layer detection failed
**Impact:** None - core functionality works fine
**Fix:** Ignore or update [docs/CORE_DOCUMENTATION_INDEX.md](docs/CORE_DOCUMENTATION_INDEX.md) formatting

### No Results for a Query

**Possible causes:**
1. **Data doesn't exist** - Check if films/docs are in the knowledge base
2. **Query too specific** - Try broader terms
3. **Index outdated** - Rebuild with `python -m lib.rag.indexer`

**Example:**
```bash
# ❌ No results (Fulci not in database)
python -m lib.rag.query "Films by Lucio Fulci"

# ✅ Works (Godard is in database)
python -m lib.rag.query "Films by Jean-Luc Godard"
```

### RuntimeWarning: 'lib.rag.query' found in sys.modules

**Issue:** Python module import warning
**Impact:** Cosmetic only - doesn't affect functionality
**Fix:** Ignore - this is a harmless warning from running as `python -m lib.rag.query`

---

## What's Next?

This is **Stage 1: Research Assistant**. Future stages:

- **Stage 2:** Decision Logging - Track all classification decisions in SQLite
- **Stage 3:** RAG-Assisted Classification - Integrate RAG into `classify.py` for automatic suggestions
- **Stage 4:** LLM Curatorial Assistant - Use Claude API for high-value manual curation

See [Issue #007](../issues/007-rag-enhanced-classification-system.md) for full roadmap.

---

## Examples by Use Case

### Use Case 1: "I found an Italian horror film from 1975 - where does it go?"

```bash
python -m lib.rag.query "Italian horror from 1975 classification"
```

**Returns:** Giallo category definition, decade boundaries (1960s-1980s), sample films

### Use Case 2: "How many Brazilian Exploitation films do I have?"

```bash
python -m lib.rag.query "Brazilian Exploitation films" --top 20
```

**Returns:** List of Brazilian Exploitation films from SORTING_DATABASE.md

### Use Case 3: "What's the difference between Core and Reference?"

```bash
python -m lib.rag.query "Core vs Reference tier difference"
```

**Returns:** TIER_ARCHITECTURE.md sections explaining tier definitions

### Use Case 4: "Why is this film stuck in Unsorted?"

```bash
python -m lib.rag.query "Common reasons for Unsorted films"
```

**Returns:** Debug runbook sections, past issue resolutions

### Use Case 5: "What directors are in the Core whitelist?"

```bash
python -m lib.rag.query "Core director whitelist" --filter AUTHORITATIVE
```

**Returns:** CORE_DIRECTOR_WHITELIST_FINAL.md sections

---

## Tips & Best Practices

1. **Start broad, then narrow:**
   - ❌ "1975 Italian giallo by Argento with blue lighting"
   - ✅ "Italian giallo from 1970s" → then refine

2. **Use natural language:**
   - ✅ "How to classify Brazilian exploitation from 1980s"
   - ✅ "Films by Jean-Luc Godard"
   - ✅ "What is the Giallo category"

3. **Check multiple results:**
   - Use `--top 10` to see more context
   - Lower scores may still be relevant

4. **Filter by authority for canonical answers:**
   - Use `--filter AUTHORITATIVE` for official definitions
   - Omit filter for broader context including theory essays

5. **Combine with grep for precision:**
   - RAG for semantic discovery
   - `grep` for exact string matching

---

## Technical Details

**Architecture:** DMK RAG (Design Methodology Kernel)

**Components:**
- **Embeddings:** sentence-transformers `all-MiniLM-L6-v2` (384-dim, offline)
- **Keyword matching:** BM25Okapi algorithm (rank-bm25)
- **Storage:** JSONL index + NumPy embeddings (no database)
- **Hybrid scoring:** 60% semantic + 25% keyword + 15% authority

**Film-Specific Customizations:**
- Symmetric normalization using `lib/normalization.normalize_for_lookup()`
- Custom chunking for SORTING_DATABASE.md (1 film = 1 chunk)
- Custom chunking for SATELLITE_CATEGORIES.md (category metadata extraction)
- Protected keywords: satellite, director, decade, tier, category, giallo, exploitation
- Film abbreviations: HK, BR, JP, IT, giallo, pinku, WIP

**Protected Headings:** Small sections with these keywords are never merged:
- satellite, director, decade, tier, category, giallo, exploitation, canon

**Index Files:**
- `output/rag/index.jsonl` - Chunk metadata + content
- `output/rag/embeddings.npy` - 384-dim sentence embeddings
- `output/rag/build_log.jsonl` - Index build metadata

---

## Support

- **Documentation bugs:** Update this file or [CORE_DOCUMENTATION_INDEX.md](CORE_DOCUMENTATION_INDEX.md)
- **RAG bugs:** See [lib/rag/](../lib/rag/) source code
- **Classification questions:** Query the RAG system itself!

```bash
python -m lib.rag.query "How does the RAG system work"
```
