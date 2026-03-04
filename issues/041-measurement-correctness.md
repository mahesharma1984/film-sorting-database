# Issue #41: Measurement Correctness — Closing the Three-Layer Validation Loop

**Type:** Feature + Data — measurement infrastructure
**Severity:** High (without this, Phase 2 improvements are unmeasured and accuracy is circular)
**Discovered via:** Investigation session 2026-03-04 (work router + RAG query on measurement architecture)
**Depends on:** Issue #38 (corpus infrastructure), Issue #40 (Phase 2 gate reorder — makes evidence trails accurate)
**Blocks:** Accurate per-stage accuracy trend tracking
**Issue spec:** `docs/issues/ISSUE_041_MEASUREMENT_CORRECTNESS.md`

---

## Problem

The classification pipeline cannot correctly measure its own accuracy. Three root causes:

1. **RC-1:** `reaudit_report.csv` lacks `classified_reason` for discrepancy films → Population A (lookup) and C (pipeline) are conflated → true pipeline accuracy (~91%) is hidden behind lookup-inflated combined score
2. **RC-2:** Corpus covers 2/796 organised films (0.25%) → circular measurement problem is essentially unaddressed → "confirmed" means self-consistent, not correct
3. **RC-3:** Cohort analysis is stale (2026-02-25, pre-Phase 2) → tradition-category director failures were miscounted as `data_gap` instead of `director_gap` due to `not_applicable` gate evidence before the Phase 2 gate reorder

## Three-Phase Fix

1. **Phase 1 (free):** Regenerate cohorts — `python scripts/analyze_cohorts.py` after re-running classify. Validates Phase 2 impact.
2. **Phase 2 (~2 hours):** Add `classified_reason` to `reaudit_report.csv` + two-population accuracy summary + `accuracy_baseline.json`. Scripts: `scripts/reaudit.py` only.
3. **Phase 3 (1-2 days/category):** Build corpora for Blaxploitation, AmExploit, HK Action, BrExploit using sources already cited in Issue #40 Phase 1.

## Measurement Targets

| Metric | Before | Target |
|---|---|---|
| corpus_confirmed | 2 / 796 | ~50 / 796 |
| Discrepancies with reason code | 0% | 100% |
| Population A accuracy visible | No | Yes (100.0%) |
| Population C accuracy visible | No | Yes (~91%) |
| Categories with external standard | 1 (Giallo) | 5 |
