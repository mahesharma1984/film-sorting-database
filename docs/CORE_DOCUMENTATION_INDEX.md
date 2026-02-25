# CORE DOCUMENTATION INDEX

**Purpose:** Central metadata registry for the RAG (Retrieval-Augmented Generation) query system. This file defines document authority levels, provides quick reference lookups, and maps concepts to their canonical sources.

**Version:** 1.2
**Last Updated:** 2026-02-17
**Status:** AUTHORITATIVE

---

## Quick Reference

Fast deterministic lookup for common questions. The RAG system checks this table first before falling back to semantic search.

| Question | Answer | Source |
|---|---|---|
| How do I classify a film? | Run classify.py on source directory | `docs/DEVELOPER_GUIDE.md` |
| How do I see the full library state? | Run audit.py → load library_audit.csv in dashboard | `audit.py`, `docs/WORK_ROUTER.md` |
| Why does the dashboard show 0% classified? | sorting_manifest.csv = Unsorted queue only; use library_audit.csv | `docs/WORK_ROUTER.md` |
| What are the satellite categories? | 17 categories with decade boundaries | `docs/SATELLITE_CATEGORIES.md` |
| How do I find a film's classification? | Search SORTING_DATABASE.md | `docs/SORTING_DATABASE.md` |
| What directors are in Core? | 38-43 directors by decade | `docs/CORE_DIRECTOR_WHITELIST_FINAL.md` |
| What is the Reference canon? | 50-film hardcoded list | `docs/REFERENCE_CANON_LIST.md` |
| What are the 4 tiers? | Core, Reference, Satellite, Popcorn | `docs/theory/TIER_ARCHITECTURE.md` |
| How do satellite decade boundaries work? | Historically bounded categories | `docs/theory/MARGINS_AND_TEXTURE.md` |
| What is the curatorial lifecycle? | Define → Cluster → Refine → Retain/Discard → Reinforce | `docs/theory/REFINEMENT_AND_EMERGENCE.md` §4a |
| How does the whole system fit together? | Recursive curation model — unified architecture | `docs/architecture/RECURSIVE_CURATION_MODEL.md` |
| What are data readiness levels? | R0–R3: No year → Full enrichment | `docs/architecture/RECURSIVE_CURATION_MODEL.md` §2 |
| What are certainty tiers? | Tier 1–4 based on independent gate count | `docs/architecture/RECURSIVE_CURATION_MODEL.md` §5 |
| How does the curation loop work? | Accept/Override/Enrich/Defer → review queue | `docs/architecture/RECURSIVE_CURATION_MODEL.md` §7 |
| How do I use the system end-to-end? | Two workflows: Unsorted→Organised (Workflow A) and Organised→Reorganised (Workflow B) | `docs/CURATOR_WORKFLOW.md` |
| Where does learning happen in the recursive model? | REFINE+REINFORCE gap: cohort hypotheses → rule changes → next classify run | `docs/CURATOR_WORKFLOW.md` §Where Learning Happens |
| What are the cohort types? | cap_exceeded, director_gap, data_gap, gate_design_gap, taxonomy_gap | `docs/CURATOR_WORKFLOW.md` Phase B3 |
| How do I find and fix systematic routing failures? | Run analyze_cohorts.py after classify; act on HIGH-confidence hypotheses | `docs/CURATOR_WORKFLOW.md` Phase B3–B4 |
| What published research grounds the frameworks? | Deming, Ranganathan, Settles, Bourdieu, Bowker & Star, signal detection | `docs/theory/THEORETICAL_GROUNDING.md` |
| Why does the pipeline keep hitting dead ends? | Information destruction at every stage; single-loop learning | `docs/architecture/EVIDENCE_ARCHITECTURE.md` §1 |
| What is evidence architecture? | Per-film evidence trails, failure cohorts, hypothesis generation | `docs/architecture/EVIDENCE_ARCHITECTURE.md` §3 |
| What is double-loop learning? | Questioning governing variables, not just fixing instances | `docs/theory/THEORETICAL_GROUNDING.md` §8 |
| How do I re-audit existing library films? | Re-classification audit (Issue #31) | `docs/theory/REFINEMENT_AND_EMERGENCE.md` §4a |
| How do I run tests? | pytest tests/ | `docs/DEVELOPER_GUIDE.md` |
| What is the R/P Split? | Reasoning vs Precision separation | `CLAUDE.md` |
| How do I commit changes? | Use git commit workflow | `docs/DEVELOPER_GUIDE.md` |
| How do I discover film threads? | Use thread_query.py CLI | `docs/THREAD_DISCOVERY_GUIDE.md` |
| What are tentpole films? | Canonical films anchoring categories | `docs/THREAD_DISCOVERY_GUIDE.md` |

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
| **Collection thesis** | `docs/theory/COLLECTION_THESIS.md` | AUTHORITATIVE |
| **Category refinement** | `docs/theory/REFINEMENT_AND_EMERGENCE.md` | AUTHORITATIVE |
| **Recursive curation model** | `docs/architecture/RECURSIVE_CURATION_MODEL.md` | AUTHORITATIVE |
| **Theoretical grounding** | `docs/theory/THEORETICAL_GROUNDING.md` | AUTHORITATIVE |
| **Evidence architecture** | `docs/architecture/EVIDENCE_ARCHITECTURE.md` | AUTHORITATIVE |
| **Satellite depth** | `docs/theory/SATELLITE_DEPTH.md` | AUTHORITATIVE |
| **Curator workflow** | `docs/CURATOR_WORKFLOW.md` | AUTHORITATIVE |
| **Thread discovery** | `docs/THREAD_DISCOVERY_GUIDE.md` | AUTHORITATIVE |
| **Debug runbook** | `docs/DEBUG_RUNBOOK.md` | AUTHORITATIVE |
| **Methodology** | `CLAUDE.md` | AUTHORITATIVE |
| **Development skills** | `exports/skills/README.md` | STABLE |
| **Theoretical foundations** | `exports/knowledge-base/` | STABLE |
| **RAG query guide** | `docs/RAG_QUERY_GUIDE.md` | STABLE |

---

## RAG Query Examples

```bash
# Basic queries
python -m lib.rag.query "How to classify Italian thriller from 1989?"
python -m lib.rag.query "Films by Lucio Fulci"

# Filtered queries
python -m lib.rag.query "Satellite decade boundaries" --filter AUTHORITATIVE

# Thread discovery
python scripts/thread_query.py --discover "Deep Red (1975)"
python scripts/thread_query.py --thread "Giallo"
python scripts/thread_query.py --list --verbose
```
