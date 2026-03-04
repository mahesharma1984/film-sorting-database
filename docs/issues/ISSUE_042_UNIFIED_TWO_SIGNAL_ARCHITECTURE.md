# Issue #42: Unified Two-Signal Classification Architecture

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P1-Critical |
| Date Opened | 2026-03-04 |
| Component | Satellite / Core / Popcorn / classify.py |
| Change Type | Refactor |
| Estimated Effort | 2-3 days |
| Blocked By | None |
| Blocks | Accurate per-signal accuracy measurement |
| Supersedes | Issue #40 Phase 3 (integration function — never implemented) |

---

## 1. Manager Summary

**Problem:** The classification pipeline uses 6 separate code paths (Stages 3-8) to assign films to tiers, each with its own logic and priority rules. The two-signal architecture (director identity vs structural triangulation) was implemented only inside one stage (Stage 5/satellite.py), while the other five stages still operate independently. As a result, the system can't report *why* a film was classified — whether by director signal, structural signal, or both — and 76% of organized Satellite films depend entirely on human-curated SORTING_DATABASE entries rather than automated signals.

**Impact if unfixed:** The pipeline continues to work but remains unmeasurable at the signal level. You can't answer "how many films does director identity classify?" vs "how many does structural matching classify?" No path to improving coverage without knowing which signal to invest in.

**Risk if fixed wrong:** Regression in the 91.5% pipeline accuracy. Existing correctly-classified films misroute. Tests fail.

**Estimated effort:** 2-3 days across 5 phases. Phase 1 (data work) is lowest risk. Phase 4 (integration function) is highest risk.

---

## 2. Evidence

### Observation

Reaudit (2026-03-04, commit 6609b2c) shows 6 different reason codes for heuristic classifications, each from a separate code path:

```
Population C — pipeline heuristics: 375/410 = 91.5%
  by stage:
    core_director               :   25/26   =  96.2%
    country_satellite           :   50/50   = 100.0%
    popcorn_cast_popularity     :   21/21   = 100.0%
    reference_canon             :   10/10   = 100.0%
    tmdb_satellite              :  239/240  =  99.6%
    unsorted_insufficient_data  :    0/7    =   0.0%
    unsorted_no_match           :    0/24   =   0.0%
    user_tag_recovery           :   30/32   =  93.8%
```

### Data

From `INVESTIGATION_TWO_SIGNAL_ARCHITECTURE.md` §5 (Signal Reachability Analysis):

- 506 organized Satellite films total
- ~120 films (24%) reachable by either automated signal
- ~386 films (76%) depend entirely on `explicit_lookup` (SORTING_DATABASE)
- `both_pass = 0` across all categories — no film currently has both director AND structural match for the same category

From current `classify.py` (lines 490-839):

| Stage | Code path | Signal type | Lines |
|---|---|---|---|
| Stage 3 | Reference canon check | Structural (title+year lookup) | 635-653 |
| Stage 4 | country_satellite | Structural (country→COUNTRY_TO_WAVE) | 655-681 |
| Stage 5 | tmdb_satellite via satellite.py | Both (director + structural inside satellite.py) | 683-711 |
| Stage 6 | User tag recovery | Neither (legacy metadata) | 713-765 |
| Stage 7 | Core director check | Director identity (whitelist) | 768-792 |
| Stage 8 | Popcorn check | Structural (popularity threshold) | 794-812 |

Each stage exits on first match. A film classified by Stage 4 (country_satellite) never reaches Stage 5 (where the two-signal logic lives) or Stage 7 (Core director check).

---

## 3. Root Cause Analysis

### RC-1: Sequential first-match-wins architecture
**Location:** `classify.py` → `classify()` method, lines 490-839
**Mechanism:** Each stage is a separate if-block that returns immediately on match. Stages 3-8 are independent code paths that don't share signal computation. A film matched by Stage 4 (country_satellite) never has its director checked. A film matched by Stage 7 (core_director) never has its structural coordinates evaluated. The two signals are never computed together for the same film.

### RC-2: Director identity is split across two unconnected registries
**Location:** `lib/constants.py` (SATELLITE_ROUTING_RULES[*]['directors']) and `lib/core_directors.py` (CoreDirectorDatabase)
**Mechanism:** The Core director whitelist and Satellite director lists are separate data structures, queried at different stages with different APIs. A director like Scorsese appears in both Core whitelist and AmNH directors list, but the system doesn't know this — it depends on stage ordering to get the right answer.

### RC-3: Confidence is category-fixed, not evidence-dependent
**Location:** `lib/constants.py` → `CATEGORY_CERTAINTY_TIERS` and `TIER_CONFIDENCE`
**Mechanism:** A Giallo classification always gets confidence 0.8 (Tier 1 category), regardless of whether it matched via director + structure (strong evidence) or structure alone (weaker evidence). The confidence score carries no information about signal quality.

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| satellite.py → classify.py | `satellite.py:classify()` returns `Optional[str]` | `classify.py` Stage 5 reads category name | Yes — returns signal data instead |
| core_directors → classify.py | `core_directors.py:is_core_director()` returns `bool` | `classify.py` Stage 7 reads bool | Yes — queried as part of Signal 1 |
| classify.py → reaudit.py | `ClassificationResult.reason` field | `reaudit.py:_STAGE_GROUPS` maps reason → stage | Yes — new reason codes |
| classify.py → move.py | `ClassificationResult.destination` field | `move.py` reads destination path | No — destinations unchanged |

**Gate impact:** Reason codes change, so `reaudit.py`'s `_STAGE_GROUPS` and `_POPULATION_A_REASONS` must be updated. `accuracy_baseline.json` schema gains new stage keys.

**Downstream consumers of changed output:**
- `move.py` — reads `destination` from manifest. Path format unchanged. No impact.
- `scripts/reaudit.py` — reads `classified_reason`. Must map new reason codes to Population A/C split. **Must update.**
- `scripts/analyze_cohorts.py` — reads `classified_reason`. Must handle new codes. **Must update.**
- `scripts/unsorted_readiness.py` — reads reason codes for unsorted films. Must handle new unsorted codes. **Must update.**
- `output/accuracy_baseline.json` — consumed by human review. New `by_stage` keys appear. **Automatically handled** by `_compute_accuracy_summary()`.

---

## 5. Proposed Fix

### Fix Description

Replace Stages 3-8 in `classify.py` with three layers: (1) compute director signal against a unified director registry, (2) compute structural signal against all structural rules, (3) integrate both signals using an evidence-based decision table. Human overrides (Stages 1-2.5) and hard gates (no year) are unchanged.

### Execution Order

**Phase 1: Unified director registry**

1. **Step 1:** Add `DIRECTOR_REGISTRY` to `lib/constants.py`
   - **What to change:** New dict: `normalized_director_name → [{tier, category, decades, source}]`
   - Merge Core whitelist entries (from `CORE_DIRECTOR_WHITELIST_FINAL.md`) and all Satellite `directors` lists (from `SATELLITE_ROUTING_RULES`)
   - A director can have multiple entries (e.g. Scorsese: Core + AmNH Satellite)
   - **Verify:** `python3 -c "from lib.constants import DIRECTOR_REGISTRY; print(len(DIRECTOR_REGISTRY))"`
   - **Verify:** Spot-check: `DIRECTOR_REGISTRY['godard']` returns both Core entry and FNW Satellite entry

2. **Step 2:** Add `score_director()` function to new file `lib/signals.py`
   - **What to change:** New function: `score_director(director_name: str, year: int) → list[DirectorMatch]`
   - Looks up director in `DIRECTOR_REGISTRY`, returns all matches with tier/category/confidence
   - Decade filtering: Satellite movement entries only match within their declared decades; Core and tradition entries match any decade
   - **Verify:** `pytest tests/test_signals.py -v` (new test file)

**Phase 2: Structural scorer**

3. **Step 3:** Add `score_structure()` function to `lib/signals.py`
   - **What to change:** New function: `score_structure(country_codes, decade, genres, keywords, popularity, vote_count, title, year) → list[StructuralMatch]`
   - Checks: COUNTRY_TO_WAVE, SATELLITE_ROUTING_RULES (country+genre+decade), Reference canon (title+year), Popcorn (popularity threshold)
   - Returns ALL matches, not just first
   - **Depends on:** Nothing (can be built in parallel with Phase 1)
   - **Verify:** `pytest tests/test_signals.py -v`

**Phase 3: Integration function**

4. **Step 4:** Add `integrate_signals()` function to `lib/signals.py`
   - **What to change:** New function: `integrate_signals(director_matches, structural_matches) → IntegrationResult`
   - Implements the decision table from §7 of `INVESTIGATION_TWO_SIGNAL_ARCHITECTURE.md`
   - Returns: tier, category, decade, confidence, reason_code, explanation
   - **Depends on:** Steps 2, 3
   - **Verify:** `pytest tests/test_signals.py -v`

**Phase 4: Replace Stages 3-8**

5. **Step 5:** Modify `classify.py` → `classify()` method
   - **What to change:** Replace Stages 3-8 (lines 635-839) with:
     ```python
     # Compute both signals
     director_matches = score_director(metadata.director, metadata.year)
     structural_matches = score_structure(...)
     # Integrate
     integration = integrate_signals(director_matches, structural_matches)
     # User tag recovery (fallback if integration returns Unsorted)
     if integration.tier == 'Unsorted' and metadata.user_tag:
         # existing user_tag_recovery logic
     ```
   - **Depends on:** Steps 2, 3, 4
   - **Verify:** `pytest tests/ -v` — all existing tests must pass

6. **Step 6:** Update `scripts/reaudit.py`
   - **What to change:** `_STAGE_GROUPS` and `_POPULATION_A_REASONS` to map new reason codes
   - New stage groups: `both_agree`, `director_signal`, `structural_signal`, `director_disambiguates`, `review_flagged`
   - **Depends on:** Step 5
   - **Verify:** `python audit.py && python scripts/reaudit.py --review` — accuracy ≥ 91.5%

**Phase 5: Documentation**

7. **Step 7:** Update documentation
   - `CLAUDE.md` §3 Rule 2 — update pipeline description
   - `docs/DEVELOPER_GUIDE.md` — update classification pipeline section
   - `docs/UNSORTED_ANALYSIS.md` — update pipeline stages description
   - `MEMORY.md` — record new architecture
   - **Verify:** `python3 -m lib.rag.indexer --force` to rebuild RAG index

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `lib/constants.py` | Add | `DIRECTOR_REGISTRY` — unified director lookup (merge Core + Satellite lists) |
| `lib/signals.py` | New | `score_director()`, `score_structure()`, `integrate_signals()` |
| `classify.py` | Modify | `classify()` — replace Stages 3-8 with signal computation + integration |
| `scripts/reaudit.py` | Modify | `_STAGE_GROUPS`, `_POPULATION_A_REASONS` — new reason codes |
| `scripts/analyze_cohorts.py` | Modify | Handle new reason codes |
| `scripts/unsorted_readiness.py` | Modify | Handle new reason codes |
| `tests/test_signals.py` | New | Tests for director scorer, structural scorer, integration function |
| `tests/test_classify.py` | Modify | Update expected reason codes in existing tests |
| `CLAUDE.md` | Update | §3 Rule 2 pipeline description |
| `docs/DEVELOPER_GUIDE.md` | Update | Classification pipeline section |

---

## 6. Scope Boundaries

**In scope:**
- Unified director registry (`DIRECTOR_REGISTRY` in constants.py)
- Signal computation functions (score_director, score_structure)
- Integration function with evidence-based confidence
- New reason codes (both_agree, director_signal, structural_signal, director_disambiguates)
- Replacing classify.py Stages 3-8 with signal + integration
- Updating reaudit.py and downstream scripts for new reason codes

**NOT in scope:**
- Parser changes (lib/parser.py) — signal architecture doesn't change how filenames are parsed
- API enrichment changes (lib/tmdb.py, lib/omdb.py) — signal architecture doesn't change data collection
- SORTING_DATABASE changes — human override layer is unchanged
- Corpus changes (lib/corpus.py) — scholarship layer is unchanged
- Director list expansion — the registry merges EXISTING lists; adding new directors is separate work
- Folder structure changes — tier-first structure is unchanged
- move.py changes — destination path format is unchanged

**Deferred to:** Future issue — director list expansion (adding Group A disambiguators from INVESTIGATION_TWO_SIGNAL_ARCHITECTURE.md §6). This issue builds the architecture; populating it with more directors is separate.

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Pipeline accuracy (Pop C) | 375/410 = 91.5% | ≥ 375/410 = 91.5% | `python scripts/reaudit.py --review` |
| Lookup accuracy (Pop A) | 370/386 = 95.9% | ≥ 370/386 = 95.9% | `python scripts/reaudit.py --review` |
| Reason codes: `both_agree` | 0 | >0 (measurable) | `output/accuracy_baseline.json` |
| Reason codes: `director_signal` | 0 | >0 (measurable) | `output/accuracy_baseline.json` |
| Reason codes: `structural_signal` | 0 | >0 (measurable) | `output/accuracy_baseline.json` |
| Test suite | 290+ passing | 290+ passing | `pytest tests/ -v` |

**Pin baseline before implementing:**
```bash
git tag pre-issue-042
cp output/accuracy_baseline.json output/accuracy_baseline_pre042.json
python scripts/reaudit.py --review > output/pre-042-reaudit.txt
```

---

## 8. Validation Sequence

```bash
# Step 1: Pin baseline
git tag pre-issue-042
cp output/accuracy_baseline.json output/accuracy_baseline_pre042.json

# Step 2: Run full test suite after each phase
pytest tests/ -v

# Step 3: After Phase 4 (classify.py change) — regression check
python audit.py && python scripts/reaudit.py --review

# Step 4: Compare accuracy
python3 -c "
import json
pre = json.load(open('output/accuracy_baseline_pre042.json'))
post = json.load(open('output/accuracy_baseline.json'))
print(f'Pipeline accuracy: {pre[\"pipeline_accuracy\"][\"score\"]:.4f} → {post[\"pipeline_accuracy\"][\"score\"]:.4f}')
print(f'Lookup accuracy:   {pre[\"lookup_accuracy\"][\"score\"]:.4f} → {post[\"lookup_accuracy\"][\"score\"]:.4f}')
print(f'New stages: {list(post[\"by_stage\"].keys())}')
"

# Step 5: Verify new reason codes appear
grep -c "both_agree\|director_signal\|structural_signal\|director_disambiguates" output/reaudit_report.csv
```

**Expected results:**
- Step 2: All tests pass (0 new failures)
- Step 3: Confirmed count ≥ 745; no new wrong_tier/wrong_category
- Step 4: Pipeline accuracy ≥ 0.9146; lookup accuracy ≥ 0.9585
- Step 5: At least one new reason code appears in the report

**If any step fails:** Stop. Do not proceed. Report the failure output.

---

## 9. Rollback Plan

**Detection:** Pipeline accuracy drops below 91.0% in reaudit, OR test suite has >2 new failures, OR any organized film that was `confirmed` becomes `wrong_tier`.

**Recovery:**
```bash
git revert [commit-hash]
# No cache impact — this change doesn't modify API caches
```

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-042
```

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `CLAUDE.md` §3 Rule 2 (Pattern-First) — the 4-tier hierarchy is the pattern. This refactor makes the pattern explicit: every film is scored against all tiers simultaneously via two signals, rather than checked sequentially by 6 independent code paths.
- `CLAUDE.md` §3 Rule 1 (R/P Split) — Signal computation (which director list matches, which structural region matches) is PRECISION work. Integration (what does director + structure together mean?) is REASONING work. The current pipeline entangles them.
- `CLAUDE.md` §3 Rule 7 (Measurement-Driven) — The new reason codes enable per-signal accuracy measurement for the first time. This is a prerequisite for data-driven improvement of either signal.
- `CLAUDE.md` §3 Rule 11 (Certainty-First) — Integration table classifies "both agree" (highest certainty) before "director only" before "structure only" (decreasing certainty with increasing gates).

**Theory documents:**
- `docs/theory/COLLECTION_THESIS.md` §7 — "Directors are the primary units of cinema evolution." The unified director registry makes this thesis executable, not decorative.
- `docs/theory/TIER_ARCHITECTURE.md` §13 — "The whitelist is the thesis." The unified registry extends this: the director registry IS the curatorial thesis about which directors belong to which traditions.
- `docs/theory/MARGINS_AND_TEXTURE.md` §8 — Positive-space vs negative-space categories. Director signal applies to positive-space (named traditions). Structural signal alone handles negative-space (Indie Cinema, Popcorn).

**Architecture reference:**
- `docs/architecture/VALIDATION_ARCHITECTURE.md` §2 — Evidence trails. `evidence_classify()` already computes both signals independently — this issue promotes that shadow computation to the primary routing path.
- `docs/issues/INVESTIGATION_TWO_SIGNAL_ARCHITECTURE.md` — Full investigation: signal definitions, precision maps, reachability analysis, integration table, priority tiers for director expansion.
- `docs/issues/INVESTIGATION_DIRECTOR_FIRST_ROUTING.md` — Precursor investigation: root cause analysis showing implementation drift from founding thesis.

**Related issues:**
- Issue #40 — implemented two-signal architecture inside satellite.py only. This issue extends it to the whole pipeline. Supersedes #40 Phase 3 (integration function).
- Issue #35 — built `evidence_classify()` and `GateResult`/`CategoryEvidence` dataclasses. This issue uses that infrastructure.
- Issue #41 — measurement correctness. The new reason codes directly address RC-1 (Population A/C conflation).
- Issue #25 — established Satellite-before-Core priority. This issue preserves that priority via the integration table (director signal for Satellite movement directors takes precedence over Core tier within movement decades).

---

### Section Checklist

- [x] §1 Manager Summary is readable without code knowledge
- [x] §3 Root causes reference specific files and functions
- [x] §4 ALL downstream consumers are listed
- [x] §5 Execution Order has verify commands for each step
- [x] §5 Files to Modify is complete
- [x] §6 NOT in scope is populated
- [x] §7 Measurement Story has concrete before/after numbers
- [x] §8 Validation Sequence commands are copy-pasteable
- [x] §9 Baseline is pinned before implementation starts
- [x] §10 Theory grounding exists
