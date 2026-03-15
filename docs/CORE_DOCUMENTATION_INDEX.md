# CORE DOCUMENTATION INDEX

**Purpose:** Central metadata registry for the RAG (Retrieval-Augmented Generation) query system. This file defines document authority levels, provides quick reference lookups, and maps concepts to their canonical sources.

**Version:** 1.2
**Last Updated:** 2026-03-15
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
| Why does the pipeline keep hitting dead ends? | Information destruction at every stage; single-loop learning | `docs/architecture/VALIDATION_ARCHITECTURE.md` §2 |
| How does the classifier decide between director vs structural evidence? | Two-signal architecture: score_director + score_structure → integrate_signals priority table (P1–P10) | `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md`, `lib/signals.py` |
| How do I populate director lists for a Satellite category? | Literature review: structural bounds → published scholarship → extract director roster → apply SATELLITE_DEPTH §3 gates | `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` §4 |
| What are the heuristic reason codes? | `both_agree`, `director_signal`, `structural_signal`, `director_disambiguates`, `review_flagged`, `reference_canon`, `user_tag_recovery`, `popcorn_*` | `lib/signals.py` |
| What does `review_flagged` mean? | Multiple structural categories matched, no director to resolve — routed to highest priority but flagged for curator review | `lib/signals.py integrate_signals()` P8 |
| What does `both_agree` mean? | Director identity + structural triangulation independently matched same Satellite category — highest confidence heuristic classification | `lib/signals.py integrate_signals()` P2 |
| What is the DIRECTOR_REGISTRY? | Single lookup index of all satellite directors built from SATELLITE_ROUTING_RULES at import time; keyed by normalized name | `lib/constants.py DIRECTOR_REGISTRY` |
| What is evidence architecture? | Per-film evidence trails, failure cohorts, hypothesis generation | `docs/architecture/VALIDATION_ARCHITECTURE.md` §2 |
| What are ground truth corpora? | Scholarship-sourced per-category CSV files for external validation | `docs/architecture/VALIDATION_ARCHITECTURE.md` §3 |
| How do I add entries to a corpus? | `build_corpus.py --add TITLE YEAR --category CAT` | `docs/architecture/VALIDATION_ARCHITECTURE.md` §6 |
| What is the accuracy of the organised library? | Three populations: lookup (100%), corpus (1.0), pipeline (~91.2%) | `docs/architecture/VALIDATION_ARCHITECTURE.md` §4 |
| How is classification accuracy measured? | Re-run classifier on organised films; compare to current location | `docs/architecture/VALIDATION_ARCHITECTURE.md` §4 |
| What is double-loop learning? | Questioning governing variables, not just fixing instances | `docs/theory/THEORETICAL_GROUNDING.md` §8 |
| How do I re-audit existing library films? | Re-classification audit (Issue #31) | `docs/theory/REFINEMENT_AND_EMERGENCE.md` §4a |
| How does filename normalisation work? | Three systems: normalizer (dot-separated), parser._clean_title (space-separated), normalization.py (lookup). Unified token lists in Issue #52. | `docs/architecture/RECURSIVE_CURATION_MODEL.md` §2a |
| What are RELEASE_TAGS vs DOT_SEPARATOR_TAGS? | RELEASE_TAGS: parser-safe tokens for both systems. DOT_SEPARATOR_TAGS: normaliser-only tokens unsafe in space-separated titles. | `lib/constants.py`, `docs/DEVELOPER_GUIDE.md` |
| What is Stage 0 normalisation? | classify.py calls normalizer.normalize() before parser.parse() — cleans filenames in memory, no disk renames | `docs/architecture/RECURSIVE_CURATION_MODEL.md` §2a |
| What is R1 promotion? | Subtitle truncation: try shorter title prefixes as API queries for R1 films with 5+ word titles | `docs/architecture/RECURSIVE_CURATION_MODEL.md` §2a |
| How do I run tests? | pytest tests/ | `docs/DEVELOPER_GUIDE.md` |
| What is the R/P Split? | Reasoning vs Precision separation | `CLAUDE.md` |
| How do I commit changes? | Use git commit workflow | `docs/DEVELOPER_GUIDE.md` |
| How do I discover film threads? | Use thread_query.py CLI | `docs/THREAD_DISCOVERY_GUIDE.md` |
| What are tentpole films? | Canonical films anchoring categories | `docs/THREAD_DISCOVERY_GUIDE.md` |
| How do I rank films within a Satellite category? | Run rank_category_tentpoles.py → output/tentpole_rankings.md | `docs/AI_TENTPOLE_RANKING.md` |
| Which films to cut when a category is over cap? | Run ranking, cut from Texture (0–4) bottom-up | `docs/theory/MARGINS_AND_TEXTURE.md` §9 |
| What is Category Core vs Category Reference? | Recursive depth hierarchy within each Satellite | `docs/theory/SATELLITE_DEPTH.md` §3–4 |
| I don't know what's wrong — how do I start investigating? | Problem classification decision tree + component lookup | `docs/WORK_ROUTER.md` §0.1–§0.2 |
| How do I trace data flow through the pipeline? | Map reads/produces/ignores; check §0.5 | `docs/WORK_ROUTER.md` §0.5 |
| How do I write an issue spec? | 10-section mandatory template (Type 1/2/3) | `docs/ISSUE_SPEC_TEMPLATE.md` |
| How do I run named engineering workflows? | Use atomic/composed procedures in workflow registry | `docs/WORKFLOW_REGISTRY.md` |
| How do I map an existing system before changing it? | Exploration-First: map→audit→probe→build | `exports/skills/exploration-first.md` |
| Why does map-before-modify prevent regressions? | Structured investigation theory | `exports/knowledge-base/exploration-theory.md` |
| How do I prevent theory and code from drifting apart? | Governance Chain: 5-level constraint architecture (Theory→Architecture→Components→Dev Rules→Code) | `docs/theory/GOVERNANCE_CHAIN_THEORY.md` |
| Why doesn't good documentation alone prevent code divergence? | L3 (Components) is the enforcement layer; without it, docs and code drift | `docs/theory/GOVERNANCE_CHAIN_THEORY.md` |
| How do I audit governance levels in this pipeline? | L3 = lib/pipeline_types.py; L4 = DEVELOPER_GUIDE §Governance Chain | `docs/DEVELOPER_GUIDE.md` §Governance Chain Architecture |
| What are the L4 dev rules for the governance chain? | GC-1 through GC-6: one result site, resolvers return Resolution, no metadata mutation in merge, etc. | `docs/DEVELOPER_GUIDE.md` §Governance Chain Architecture |

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
| **Validation architecture** | `docs/architecture/VALIDATION_ARCHITECTURE.md` | AUTHORITATIVE |
| **Ground truth corpora** | `data/corpora/*.csv` | AUTHORITATIVE |
| **Satellite depth** | `docs/theory/SATELLITE_DEPTH.md` | AUTHORITATIVE |
| **Curator workflow** | `docs/CURATOR_WORKFLOW.md` | AUTHORITATIVE |
| **Thread discovery** | `docs/THREAD_DISCOVERY_GUIDE.md` | AUTHORITATIVE |
| **Tentpole ranking procedure** | `docs/AI_TENTPOLE_RANKING.md` | AUTHORITATIVE |
| **Debug runbook** | `docs/DEBUG_RUNBOOK.md` | AUTHORITATIVE |
| **Workflow registry** | `docs/WORKFLOW_REGISTRY.md` | AUTHORITATIVE |
| **Methodology** | `CLAUDE.md` | AUTHORITATIVE |
| **Development skills** | `exports/skills/README.md` | STABLE |
| **Theoretical foundations** | `exports/knowledge-base/` | STABLE |
| **Exploration-First skill** | `exports/skills/exploration-first.md` | STABLE |
| **Exploration theory** | `exports/knowledge-base/exploration-theory.md` | STABLE |
| **Governance Chain skill** | `exports/skills/governance-chain.md` | STABLE |
| **Governance Chain theory (project)** | `docs/theory/GOVERNANCE_CHAIN_THEORY.md` | AUTHORITATIVE |
| **Governance Chain theory (general)** | `exports/knowledge-base/governance-chain-theory.md` | STABLE |
| **Pipeline types (L3 enforcement)** | `lib/pipeline_types.py` | AUTHORITATIVE |
| **Director matching (L3 enforcement)** | `lib/director_matching.py` | AUTHORITATIVE |
| **Issue specification standard** | `docs/ISSUE_SPEC_TEMPLATE.md` | STABLE |
| **Two-signal architecture** | `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` | AUTHORITATIVE |
| **Two-signal implementation** | `lib/signals.py` | AUTHORITATIVE |
| **Filename normalisation** | `lib/normalizer.py` | AUTHORITATIVE |
| **Lookup normalisation** | `lib/normalization.py` | AUTHORITATIVE |
| **Token lists (RELEASE_TAGS, DOT_SEPARATOR_TAGS)** | `lib/constants.py` | AUTHORITATIVE |
| **RAG query guide** | `docs/RAG_QUERY_GUIDE.md` | STABLE |

---

## RAG Query Examples

```bash
# Basic queries
python -m lib.rag.query "How to classify Italian thriller from 1989?"
python -m lib.rag.query "Films by Lucio Fulci"

# Filtered queries
python -m lib.rag.query "Satellite decade boundaries" --filter AUTHORITATIVE
python -m lib.rag.query "governance chain routing" --level 1 2 4

# Thread discovery
python scripts/thread_query.py --discover "Deep Red (1975)"
python scripts/thread_query.py --thread "Giallo"
python scripts/thread_query.py --list --verbose
```
