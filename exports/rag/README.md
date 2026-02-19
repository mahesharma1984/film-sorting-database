# RAG Verification Layer

**Purpose:** Turn your methodology documentation from passive reference into an active, queryable verification tool.

---

## The Problem This Solves

The DMK knowledge base, skills, and templates get you to **~80% methodology alignment**. You read the theory, adopt the skills, set up the documentation structure, and your project follows the principles.

The last **10-20% is the hard part**:
- Subtle violations that aren't obvious by reading docs manually
- Drift over time as the codebase grows and principles get forgotten
- Cross-cutting concerns where two principles interact (e.g., R/P split + measurement-driven development touching the same code)
- New team members who've read the docs but don't know which principle applies to a specific decision

Without RAG, your methodology docs are **passive** — you read them, internalize what you can, and hope you don't drift. With RAG, they become **active** — you can interrogate them at decision points.

## What It Does

RAG indexes your `docs/` directory and provides semantic search with:

- **Hybrid scoring**: Embedding similarity (meaning) + BM25 (exact terms) + authority weighting (trust)
- **Authority-aware ranking**: AUTHORITATIVE docs rank above STABLE, which rank above unmarked
- **Structured lookup**: Deterministic keyword matching before falling back to embeddings
- **Routing suppression**: Filters out navigation docs when the actual content doc is in results

## When to Add It

Add RAG to your project when:

| Signal | What It Means |
|---|---|
| Your `docs/` directory has 15+ files | Manual navigation becomes unreliable |
| You catch yourself re-reading docs to find "that section about X" | You need search, not browsing |
| Team members apply principles inconsistently | They need a queryable oracle, not just docs to read |
| Your WORK_ROUTER.md keeps growing | The manual routing layer isn't scaling |
| You want to verify "does my code follow principle Y?" | You need the 80% -> 90% verification tool |

**Don't add it** if your project has fewer than 10 docs — WORK_ROUTER.md is sufficient at that scale.

## Example Queries

Once set up, you can ask questions like:

```bash
# Verify methodology compliance
python -m rag.query "Does error handling follow hard/soft gate pattern?"

# Find the right doc for a decision
python -m rag.query "How should I split this task between LLM and code?"

# Cross-cutting principle lookup
python -m rag.query "What does measurement-driven development say about regression testing?"

# Architecture verification
python -m rag.query "What are the API contract requirements?"

# Debugging guidance
python -m rag.query "Authentication failing after deployment"
```

## Architecture

```
docs/ (your markdown files)
  |
  v
chunker.py (split at heading boundaries)
  |
  v
metadata.py (extract authority from CORE_DOCUMENTATION_INDEX.md)
  |
  v
indexer.py (generate embeddings with sentence-transformers)
  |
  v
outputs/rag/ (index.jsonl + embeddings.npy)
  |
  v
retriever.py (hybrid scoring engine)
  |
  v
query.py (CLI + programmatic interface)
```

**Query pipeline (R/P Split applied):**

1. **Structured Lookup** (PRECISION — code): Deterministic keyword matching against Quick Reference and Canonical Sources tables
2. **Phase A** (PRECISION — code): Abbreviation expansion, keyword extraction, query classification, chunk filtering
3. **Phase B** (REASONING — embeddings): Semantic ranking of filtered candidates with authority weighting

## Performance

- **Index build**: ~20-30 seconds for 50-100 doc files
- **Query latency**: <100ms (local embeddings, no API calls)
- **Cost**: $0 (all local, no cloud services)
- **Dependencies**: 3 packages (sentence-transformers, rank-bm25, numpy)

## Quick Start

See [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for step-by-step setup.

```bash
# 1. Copy the rag/ package into your project
cp -r exports/rag/rag/ ./rag/

# 2. Install dependencies
pip install sentence-transformers rank-bm25 numpy

# 3. Build the index
python -m rag.indexer

# 4. Query
python -m rag.query "How does authentication work?"
```

## Relationship to DMK Layers

```
Layer 0: KNOWLEDGE BASE (understand why)     <- RAG indexes this
Layer 1: SKILLS (know how)                   <- RAG indexes this
Layer 2: TEMPLATES (implement)               <- RAG indexes this
Layer 3: RAG VERIFICATION (verify)           <- THIS LAYER
```

RAG is the feedback loop. Layers 0-2 give you the principles. Layer 3 lets you continuously verify you're following them.
