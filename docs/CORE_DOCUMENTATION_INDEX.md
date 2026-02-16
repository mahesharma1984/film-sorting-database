# CORE DOCUMENTATION INDEX

**Purpose:** Central metadata registry for the RAG (Retrieval-Augmented Generation) query system. This file defines document authority levels, provides quick reference lookups, and maps concepts to their canonical sources.

**Version:** 1.0
**Last Updated:** 2026-02-16
**Status:** AUTHORITATIVE

---

## Quick Reference

Fast deterministic lookup for common questions. The RAG system checks this table first before falling back to semantic search.

| Question | Answer | Source |
|---|---|---|
| How do I classify a film? | Run classify.py on source directory | `docs/DEVELOPER_GUIDE.md` |
| What are the satellite categories? | 12 categories with decade boundaries | `docs/SATELLITE_CATEGORIES.md` |
| How do I find a film's classification? | Search SORTING_DATABASE.md | `docs/SORTING_DATABASE.md` |
| What directors are in Core? | 38-43 directors by decade | `docs/CORE_DIRECTOR_WHITELIST_FINAL.md` |
| What is the Reference canon? | 50-film hardcoded list | `docs/REFERENCE_CANON_LIST.md` |
| What are the 4 tiers? | Core, Reference, Satellite, Popcorn | `docs/theory/TIER_ARCHITECTURE.md` |
| How do satellite decade boundaries work? | Historically bounded categories | `docs/theory/MARGINS_AND_TEXTURE.md` |
| How do I run tests? | pytest tests/ | `docs/DEVELOPER_GUIDE.md` |
| What is the R/P Split? | Reasoning vs Precision separation | `CLAUDE.md` |
| How do I commit changes? | Use git commit workflow | `docs/DEVELOPER_GUIDE.md` |

---

## Canonical Sources

Maps concepts to their authoritative documentation. Documents tagged **AUTHORITATIVE** rank highest in RAG results.

| Concept | Canonical Source | Status |
|---|---|---|
| **Classification system** | `docs/DEVELOPER_GUIDE.md` | AUTHORITATIVE |
| **Tier architecture** | `docs/theory/TIER_ARCHITECTURE.md` | AUTHORITATIVE |
| **Satellite categories** | `docs/SATELLITE_CATEGORIES.md` | AUTHORITATIVE |
| **Core directors** | `docs/CORE_DIRECTOR_WHITELIST_FINAL.md` | AUTHORITATIVE |
| **Reference canon** | `docs/REFERENCE_CANON_LIST.md` | AUTHORITATIVE |
| **Film classifications** | `docs/SORTING_DATABASE.md` | AUTHORITATIVE |
| **Satellite margins** | `docs/theory/MARGINS_AND_TEXTURE.md` | AUTHORITATIVE |
| **Decade theory** | `docs/theory/DECADE_WAVE_THEORY.md` | AUTHORITATIVE |
| **Auteur criteria** | `docs/theory/AUTEUR_CRITERIA.md` | AUTHORITATIVE |
| **Popcorn theory** | `docs/theory/POPCORN_WAVES.md` | AUTHORITATIVE |
| **Format curation** | `docs/theory/FORMAT_AS_INTENTION.md` | AUTHORITATIVE |
| **Collection identity** | `docs/theory/COLLECTION_IDENTITY.md` | AUTHORITATIVE |
| **Project summary** | `docs/PROJECT_COMPLETE_SUMMARY.md` | STABLE |
| **Debug runbook** | `docs/DEBUG_RUNBOOK.md` | AUTHORITATIVE |
| **Methodology** | `CLAUDE.md` | AUTHORITATIVE |

---

## RAG Query Examples

```bash
# Basic queries
python -m lib.rag.query "How to classify Italian thriller from 1989?"
python -m lib.rag.query "Films by Lucio Fulci"

# Filtered queries
python -m lib.rag.query "Satellite decade boundaries" --filter AUTHORITATIVE
```
