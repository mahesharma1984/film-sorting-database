# Core Documentation Index

**Version:** 1.0
**Updated:** 2025-02-14
**Purpose:** Quick reference for finding any documentation in this project.

---

## Quick Reference

| Question | Answer | Source |
|---|---|---|
| How do I set up the project? | Clone repo, install requirements, add API key to config | `README.md` |
| What's the project architecture? | 3-script pipeline: scaffold → classify → move | `REFACTOR_PLAN.md` |
| How do I debug an issue? | Follow the triage flow | `docs/DEBUG_RUNBOOK.md` |
| What are the development rules? | See §3 Decision Rules | `CLAUDE.md` |
| How do I classify new films? | `python classify.py <dir>` then review manifest | `docs/DEVELOPER_GUIDE.md` |
| How do I move classified films? | `python move.py --dry-run` then `--execute` | `docs/DEVELOPER_GUIDE.md` |
| What changed recently? | See git log and issue files | `issues/` |
| Which directors are Core? | 38-43 directors across decades | `docs/CORE_DIRECTOR_WHITELIST_FINAL.md` |
| What are the satellite categories? | 12 categories with caps totaling ~410 | `docs/SATELLITE_CATEGORIES.md` |
| What's in the Reference canon? | 50 canonical films | `docs/REFERENCE_CANON_LIST.md` |
| Where are all the known film mappings? | 200+ human-curated entries | `docs/SORTING_DATABASE.md` |
| Why is the system designed this way? | Read the theory essays | `docs/theory/README.md` |

---

## Canonical Sources

Each concept has ONE authoritative document. When information conflicts, defer to the canonical source.

| Concept | Canonical Source | Status |
|---|---|---|
| Classification pipeline design | `REFACTOR_PLAN.md` | AUTHORITATIVE |
| Tier priority order & decision rules | `CLAUDE.md § 3` | AUTHORITATIVE |
| Core directors (whitelist) | `docs/CORE_DIRECTOR_WHITELIST_FINAL.md` | AUTHORITATIVE |
| Reference canon (50 films) | `docs/REFERENCE_CANON_LIST.md` | AUTHORITATIVE |
| Satellite categories & caps | `docs/SATELLITE_CATEGORIES.md` | AUTHORITATIVE |
| Popcorn rules & boundaries | `docs/POPCORN_RULES.md` | AUTHORITATIVE |
| Known film→destination mappings | `docs/SORTING_DATABASE.md` | AUTHORITATIVE |
| Shared constants | `lib/constants.py` | AUTHORITATIVE |
| Normalization rules | `lib/normalization.py` | AUTHORITATIVE |
| Development procedures | `docs/DEVELOPER_GUIDE.md` | AUTHORITATIVE |
| Safety guardrails | `docs/CI_RULES.md` | AUTHORITATIVE |
| Debugging procedures | `docs/DEBUG_RUNBOOK.md` | AUTHORITATIVE |
| Symptom-based routing | `docs/WORK_ROUTER.md` | AUTHORITATIVE |
| Curatorial theory | `docs/theory/` (7 essays) | AUTHORITATIVE |

---

## Document Categories

### Navigation (How to find things)
- `CLAUDE.md` — AI assistant instructions and work modes
- `docs/CORE_DOCUMENTATION_INDEX.md` — This file (Q&A lookup)
- `docs/WORK_ROUTER.md` — Symptom-based routing to the right doc

### Architecture (How the system works)
- `REFACTOR_PLAN.md` — v1.0 three-script pipeline design
- `docs/IMPLEMENTATION_GUIDE.md` — Original implementation details
- `docs/IMPLEMENTATION_READY_FINAL.md` — Pre-refactor architecture notes

### Operations (How to do things)
- `docs/DEVELOPER_GUIDE.md` — Change management and testing
- `docs/CI_RULES.md` — Safety guardrails
- `docs/DEBUG_RUNBOOK.md` — Triage and diagnosis
- `README.md` — Project overview and setup

### Curatorial Reference (What belongs where)
- `docs/CORE_DIRECTOR_WHITELIST_FINAL.md` — 38-43 directors by decade
- `docs/REFERENCE_CANON_LIST.md` — 50 canonical films
- `docs/SATELLITE_CATEGORIES.md` — 12 exploitation/margins categories
- `docs/POPCORN_RULES.md` — Tonight-test films, format curation
- `docs/SORTING_DATABASE.md` — Human-curated film→destination mappings
- `docs/POPCORN_SORTING.md` — Popcorn sorting decisions
- `docs/SATELLITE_SORTING.md` — Satellite sorting decisions
- `docs/REFERENCE_SORTING.md` — Reference sorting decisions
- `docs/CORE_SORTING_BREAKDOWN.md` — Core sorting decisions

### Curatorial Theory (Why we do things this way)
- `docs/theory/COLLECTION_IDENTITY.md` — Master thesis: personal cinema museum
- `docs/theory/TIER_ARCHITECTURE.md` — Why 4 tiers, why this priority order
- `docs/theory/DECADE_WAVE_THEORY.md` — Why decades, not movements
- `docs/theory/AUTEUR_CRITERIA.md` — How directors earn Core status
- `docs/theory/MARGINS_AND_TEXTURE.md` — Satellite as exploitation archaeology
- `docs/theory/POPCORN_WAVES.md` — Popcorn as parallel studio cinema history
- `docs/theory/FORMAT_AS_INTENTION.md` — Format signals as curatorial metadata
- `docs/theory/README.md` — Reading order and cross-references

### Issues and History
- `issues/001-simplify-classification-to-v0.1.md` — v0→v0.1 simplification
- `issues/002-v01-fails-reasoning-and-precision-audit.md` — R/P audit findings
- `issues/003-v02-parser-fixes-language-country-extraction.md` — v0.2 parser fixes
- `issues/classification_effectiveness_report.md` — Classification effectiveness analysis
- `docs/PROJECT_COMPLETE_SUMMARY.md` — Collection stats and outcomes
- `docs/PHASE_1_COMPLETE.md` — Phase 1 completion notes
- `docs/PHASE_2_SORTING_MASTER.md` — Phase 2 sorting plan

### Project Meta
- `docs/QUICK_REFERENCE_CHECKLIST.md` — Quick sorting checklist
- `docs/FINAL_SORTING_MANIFEST.md` — Final sorting manifest overview
- `docs/CORE_FILM_COUNT.md` — Core film count tracking
- `docs/FOLLOWUP_REFERENCE_WISHLIST.md` — Reference wishlist for future additions
- `docs/FUTURE_POPCORN_THESIS.md` — Extended Popcorn thesis notes
- `EXTERNAL_DRIVE_GUIDE.md` — External drive setup
- `PERFORMANCE_ISSUE_REPORT.md` — Performance analysis (copy2 vs rename)
- `FIX_VALIDATION_REPORT.md` — Fix validation tracking
