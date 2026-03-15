# Issue #54: Governance Chain Pipeline Consolidation

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P1-Critical |
| Date Opened | 2026-03-15 |
| Component | classify.py / lib/satellite.py / lib/signals.py |
| Change Type | Refactor |
| Estimated Effort | 2-3 days |
| Blocked By | None |
| Blocks | Curation Loop implementation, future category additions |
| Supersedes | None |

---

## 1. Manager Summary

**Problem:** The classification pipeline has 5 parallel code paths that each build results independently, plus 2 duplicate implementations of satellite routing logic (`classify()` and `classify_structural()`), plus 3 separate director-matching implementations. These parallel paths share no enforced contracts — when one is updated, the others drift.

**Impact if unfixed:** Every future change (new categories, routing rule adjustments, new data sources) must be applied to multiple code paths simultaneously. Bugs from missed updates are inevitable and have already occurred (Issue #33 `_parse_destination()`, Issue #51 requiring changes to both `classify()`/`classify_structural()`). Evidence trails run as a separate shadow pass that can silently diverge from actual classification.

**Risk if fixed wrong:** Classification results change for existing films. The refactor must be behavior-preserving — same inputs produce same outputs. The test suite (373 tests) and reaudit baseline are the verification gates.

**Estimated effort:** 2-3 days. Phase 1 (L3 components) is the bulk; Phases 2-4 are mechanical once types exist.

---

## 2. Evidence

### Observation

A governance chain audit (Theory → Architecture → Components → Dev Rules → Code) reveals that L1 (Theory) and L2 (Architecture) are strong across all proven practices, but **L3 (Components) and L4 (Dev Rules) are systematically absent**. This is the exact failure mode described in `exports/knowledge-base/governance-chain-theory.md`: good docs, no mechanical enforcement, code drifts.

### Data

**Traceability matrix (12 proven practices audited):**

| Practice | L1 | L2 | L3 | L4 | L5 | Status |
|---|---|---|---|---|---|---|
| Two-Signal Classification | Y | Y | Partial | Missing | Partial | PARTIAL |
| Satellite Routing Rules | Y | Y | **Divergent** | Missing | **Divergent** | DIVERGENT |
| Data Readiness (R0-R3) | Y | Y | Missing | Missing | **Divergent** | DIVERGENT |
| Failure Gates | Y | Y | Missing | Missing | Partial | PARTIAL |
| Symmetric Normalization | Y | Y | Y | Y | Y | FAITHFUL |
| API Enrichment & Merge | Y | Y | Missing | Missing | Partial | PARTIAL |
| Constants (Single Source) | Y | Y | Partial | Y | Partial | PARTIAL |
| Decade Bounding | Y | Y | Partial | Missing | **Divergent** | DIVERGENT |
| Director Matching | Y | Y | **Divergent** | Missing | **Divergent** | DIVERGENT |
| Evidence Trails | Y | Y | Partial | Missing | Y | PARTIAL |
| Curation Loop | Y | Y | Missing | Missing | Missing | MISSING |
| R/P Split | Y | Y | Missing | Y | Partial | PARTIAL |

**Result:** 0/12 fully faithful (excluding normalization, which was fixed after a v0.1 bug forced the full chain). 4/12 divergent. 7/12 partial. 1/12 missing implementation entirely.

**Concrete divergences:**

1. **5 independent `ClassificationResult` construction sites** in `classify.py`:
   - Line 641–654 (explicit_lookup)
   - Line 671–683 (corpus_lookup)
   - Line 741–754 (two-signal integration)
   - Line 801–813 (user_tag_recovery)
   - Line 829–841 (unsorted default)

2. **2 implementations of satellite routing** in `lib/satellite.py`:
   - `classify()` — full routing with director checks
   - `classify_structural()` — structure-only routing, different code path
   - Both check the same `SATELLITE_ROUTING_RULES` with different inline logic for `is_tradition` ordering and decade validation

3. **3 implementations of director matching:**
   - `lib/satellite.py:_director_matches()` — substring/whole-word matching
   - `lib/signals.py:score_director()` — iterates `DIRECTOR_REGISTRY`
   - `classify.py:_merge_api_results()` — implicit director comparison for field priority

4. **`_merge_api_results()` mutates `metadata` as side effect** (lines 448–470):
   - Updates `metadata.director` and `metadata.country` inline
   - Mixes PRECISION (data transformation) with REASONING (field priority decisions)
   - No typed output — returns raw dict

5. **User tag recovery bypasses readiness gate:**
   - R1 films skip Stages 3-8 (correct per Rule 10)
   - But `user_tag_recovery` (line 760) fires for R1 films with no readiness check
   - Theory says R1 = insufficient data for routing; code allows tag-based routing anyway

---

## 3. Root Cause Analysis

### RC-1: No L3 enforcement layer (Component contracts absent)

**Location:** System-wide — no `lib/contracts.py` or typed stage boundaries exist
**Mechanism:** Each classification path (explicit_lookup, corpus, two-signal, user_tag, unsorted) constructs `ClassificationResult` inline with ~15 field assignments. No shared function enforces that all paths produce consistent output. When a new field is added (e.g., `data_readiness` in Issue #30, `evidence_trail` in Issue #35), it must be added to all 5 sites manually.

### RC-2: `classify()` / `classify_structural()` duplication

**Location:** `lib/satellite.py` — two methods (~200 lines each) implementing the same routing rules
**Mechanism:** `classify_structural()` was added for Issue #42 (two-signal architecture) to provide director-excluded structural matching. Instead of parameterizing the existing `classify()` method, a parallel implementation was created. The two methods check the same `SATELLITE_ROUTING_RULES` data but with different control flow for `is_tradition` categories, decade validation ordering, and keyword routing.

### RC-3: No typed stage boundaries

**Location:** `classify.py:classify()` — stages connected by raw dicts and side effects
**Mechanism:** Stage 1 (API enrichment) returns a raw `dict` or `None`. Stage 2 (lookup) returns a destination `str` or `None`. Stages 3-8 (signals) return `IntegrationResult`. No shared type system connects these. Data flows via `metadata` mutation (side effects) and local variables. Adding a new stage or data source requires reading all of `classify()` to understand what's available.

### RC-4: Evidence trails as parallel reimplementation

**Location:** `classify.py:_gather_evidence()` — shadow pass after classification
**Mechanism:** Evidence trails re-run all routing logic read-only to produce gate-by-gate results. This is architecturally a second implementation of the classification pipeline. If routing logic changes, `_gather_evidence()` must change too. The shadow pass and the real pipeline can produce different results with no cross-validation.

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| Parse → Enrich | `lib/parser.py:parse()` | `classify.py:_query_apis()` | No (FilmMetadata stays) |
| Enrich → Resolve | `classify.py:_merge_api_results()` | `classify.py:classify()` routing | **Yes** — raw dict → `EnrichedFilm` |
| Resolve → Result | 5 inline construction sites | `classify.py:write_manifest()` | **Yes** — 5 sites → 1 `build_result()` |
| Satellite routing | `lib/satellite.py:classify()` + `classify_structural()` | `lib/signals.py:score_structure()` | **Yes** — 2 methods → 1 `evaluate_category()` |
| Evidence → CSV | `classify.py:_gather_evidence()` | `output/evidence_trails.csv` | **Yes** — shadow pass eliminated; evidence = non-winning Resolutions |

**Gate impact:** No gate thresholds change. Gate enforcement points move from inline `if` statements to typed stage boundaries, but the logic is identical.

**Downstream consumers of changed output:**
- `move.py` — reads `sorting_manifest.csv` (format unchanged)
- `scripts/reaudit.py` — reads manifest + walks library (format unchanged)
- `dashboard.py` — reads manifest CSV (format unchanged)
- `tests/` — call `classify()`, `score_director()`, `score_structure()`, `integrate_signals()`, `SatelliteClassifier.classify()` directly (signatures change for satellite; others preserved via wrapper)

---

## 5. Proposed Fix

### Fix Description

Consolidate 5 parallel classification paths into one priority chain with typed stage boundaries. Extract L3 components (shared functions with enforced contracts) so that all paths go through the same code. Eliminate the `classify()`/`classify_structural()` duplication in `lib/satellite.py`. Kill the evidence shadow pass by making evidence a natural byproduct of the priority chain.

### Execution Order

**Phase 1: L3 Component Extraction**

1. **Step 1:** Create `lib/pipeline_types.py` — stage boundary dataclasses
   - `EnrichedFilm` — output of enrichment stage (title, year, director, countries, genres, keywords, readiness, tmdb_id, sources)
   - `Resolution` — output of any classification source (tier, category, decade, confidence, reason, source_name)
   - **Verify:** `pytest tests/ -v` (no behavior change, just new types)

2. **Step 2:** Extract `build_result()` function in `classify.py`
   - Single function: `build_result(metadata, enriched, resolution) -> ClassificationResult`
   - Replace all 5 inline construction sites with calls to `build_result()`
   - **Verify:** `pytest tests/ -v` — all tests pass, identical CSV output

3. **Step 3:** Extract `match_director()` in `lib/director_matching.py`
   - Single function: `match_director(query: str, candidate: str) -> bool`
   - Replace usage in `satellite.py:_director_matches()`, `signals.py:score_director()`, `classify.py:_merge_api_results()`
   - **Verify:** `pytest tests/ -v` — identical behavior

4. **Step 4:** Unify `classify()`/`classify_structural()` in `lib/satellite.py`
   - New: `evaluate_category(film_data, category_rules, include_director=True) -> Optional[CategoryMatch]`
   - Both old methods become thin wrappers calling `evaluate_category()` (preserve external API during transition)
   - **Verify:** `pytest tests/test_satellite.py -v && pytest tests/test_signals.py -v`

**Phase 2: Consolidate RESOLVE**

5. **Step 5:** Refactor `classify()` in `classify.py` as priority chain
   - Each source (explicit_lookup, corpus, two-signal, user_tag) becomes a function returning `Optional[Resolution]`
   - Main loop: iterate sources in priority order, first non-None wins
   - All sources fire (producing Resolution or None); winning Resolution = classification, rest = evidence trail
   - **Verify:** `pytest tests/ -v` — all tests pass
   - **Verify:** `python classify.py "/Volumes/One Touch/Movies/Organized/Unsorted" && diff output/sorting_manifest.csv output/sorting_manifest.csv.bak` (save backup first)

6. **Step 6:** Kill evidence shadow pass
   - Remove `_gather_evidence()` method
   - Evidence trail = list of all Resolutions (winning + non-winning) from priority chain
   - Update `evidence_trails.csv` writer to consume Resolution list
   - **Verify:** `pytest tests/test_evidence_trails.py -v`

**Phase 3: Consolidate ENRICH**

7. **Step 7:** Refactor `_merge_api_results()` → returns `EnrichedFilm`
   - Stop mutating `metadata.director` and `metadata.country`
   - Field priorities become a declarative spec (dict of field → source priority list)
   - `EnrichedFilm` carries provenance (which API provided which field)
   - **Verify:** `pytest tests/ -v`

8. **Step 8:** Add readiness gate to user_tag_recovery
   - R1 films cannot use user_tag_recovery (consistent with Rule 10)
   - R2 films can use tags but confidence capped at 0.6
   - **Verify:** `pytest tests/ -v` — add test for R1 tag bypass prevention

**Phase 4: L4 Dev Rules + Wiring**

9. **Step 9:** Update `docs/DEVELOPER_GUIDE.md`
   - Add dev rules: "All classification goes through priority chain in `resolve()`"
   - Add dev rules: "All director comparison uses `match_director()`"
   - Add dev rules: "New classification sources return `Optional[Resolution]`"
   - Add dev rules: "Stage boundaries use typed dataclasses, not raw dicts"

10. **Step 10:** Update `CLAUDE.md`
    - Add Rule 13: Governance Chain reference
    - Update Rule 2 (Pattern-First) to reference consolidated pipeline
    - Update §5 (Key Commands) if any change

11. **Step 11:** Update `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md`
    - Two-signal is now P3 in the priority chain, not a standalone pipeline
    - Signal integration unchanged; its position in the priority order is now explicit

12. **Step 12:** Migrate exports governance-chain files into project docs
    - Copy `exports/knowledge-base/governance-chain-theory.md` → `docs/theory/GOVERNANCE_CHAIN_THEORY.md`
    - Copy `exports/skills/governance-chain.md` → reference from `docs/CORE_DOCUMENTATION_INDEX.md`
    - Update `docs/theory/README.md` reading order

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `lib/pipeline_types.py` | **Create** | `EnrichedFilm`, `Resolution` dataclasses |
| `lib/director_matching.py` | **Create** | `match_director()` — unified director comparison |
| `classify.py` | Modify | `classify()` → priority chain; `_merge_api_results()` → returns `EnrichedFilm`; `build_result()` extracted; `_gather_evidence()` removed |
| `lib/satellite.py` | Modify | `evaluate_category()` replaces `classify()`/`classify_structural()` duplication |
| `lib/signals.py` | Modify | `score_director()` uses `match_director()`; `score_structure()` uses `evaluate_category()` |
| `docs/DEVELOPER_GUIDE.md` | Update | L4 dev rules for governance chain |
| `CLAUDE.md` | Update | Rule 13 (Governance Chain), Rule 2 update |
| `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` | Update | Priority chain positioning |
| `docs/theory/GOVERNANCE_CHAIN_THEORY.md` | **Create** | Migrated from exports |
| `docs/theory/README.md` | Update | Reading order |
| `docs/CORE_DOCUMENTATION_INDEX.md` | Update | New file entries |
| `tests/test_pipeline_types.py` | **Create** | Type contract tests |
| `tests/test_director_matching.py` | **Create** | Unified matching tests |

---

## 6. Scope Boundaries

**In scope:**
- L3 component extraction (typed boundaries, shared functions)
- Consolidating 5 result-building sites → 1
- Unifying `classify()`/`classify_structural()` → 1 parameterized function
- Unifying director matching → 1 shared function
- Eliminating evidence shadow pass (evidence = non-winning Resolutions)
- L4 dev rules in DEVELOPER_GUIDE.md
- Governance chain theory migration into project docs
- Readiness gate on user_tag_recovery

**NOT in scope:**
- Curation Loop implementation (Override/Enrich/Defer tools) — real feature work, needs its own spec
- Schema validation at stage boundaries — add after types exist, separate issue
- Country code validation — add as gate inside ENRICH, separate issue
- Dashboard changes — downstream consumer, format unchanged
- New categories or routing rules — separate from structural refactor
- Changes to `move.py`, `audit.py`, `scaffold.py` — unchanged consumers
- Performance optimization — not the goal; correctness preservation is

**Deferred to:** Future issue for schema validation gates at typed boundaries (cheap to add once types exist)

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Test suite | 373 passed, 1 skipped | 373+ passed, 1 skipped | `pytest tests/ -v` |
| Classification output | sorting_manifest.csv baseline | **Identical** CSV output | `diff` against pre-refactor manifest |
| Reaudit confirmed | Current baseline | **Identical** | `python scripts/reaudit.py` |
| Result construction sites | 5 | 1 | `grep -c "ClassificationResult(" classify.py` |
| Satellite routing implementations | 2 (`classify` + `classify_structural`) | 1 (`evaluate_category`) | Code inspection |
| Director matching implementations | 3 | 1 (`match_director()`) | `grep -rn "director.*match\|_director_matches\|director.*lower" lib/` |

**This is a behavior-preserving refactor.** The primary metric is: identical outputs before and after. Any classification change is a regression.

**Pin baseline before implementing:**
```bash
git tag pre-issue-054
cp output/sorting_manifest.csv output/sorting_manifest_pre054.csv
python scripts/reaudit.py > output/pre-054-reaudit.txt
```

---

## 8. Validation Sequence

```bash
# Step 0: Pin baseline
git tag pre-issue-054
cp output/sorting_manifest.csv output/sorting_manifest_pre054.csv
python scripts/reaudit.py > output/pre-054-reaudit.txt

# After each phase:

# Step 1: Run full test suite
pytest tests/ -v

# Step 2: Classify and diff against baseline
python classify.py "/Volumes/One Touch/Movies/Organized/Unsorted" --output output/sorting_manifest_054.csv
diff <(sort output/sorting_manifest_pre054.csv) <(sort output/sorting_manifest_054.csv)

# Step 3: Reaudit regression check
python audit.py && python scripts/reaudit.py

# Step 4: Verify structural goals
grep -c "ClassificationResult(" classify.py  # Should be 1 (in build_result)
grep -c "def evaluate_category" lib/satellite.py  # Should be 1
grep -c "def match_director" lib/director_matching.py  # Should be 1
```

**Expected results:**
- Step 1: All tests pass (373+, 1 skipped)
- Step 2: **Zero diff** — identical classification output
- Step 3: Confirmed count identical to baseline; no new wrong_tier/wrong_category
- Step 4: Structural consolidation verified

**If any step fails:** Stop. Do not proceed. The refactor introduced a behavior change — find and fix before continuing.

---

## 9. Rollback Plan

**Detection:** Any diff in Step 2 (classification output changed) or reaudit regression in Step 3.

**Recovery:**
```bash
git revert [commit-hash]
# Restore baseline manifest:
cp output/sorting_manifest_pre054.csv output/sorting_manifest.csv
```

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-054
```

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `exports/knowledge-base/governance-chain-theory.md` — the five-level constraint chain; L3 (Components) as enforcement layer; "fix at the highest divergent level"
- `exports/skills/governance-chain.md` — Step 1 (Audit), Step 2 (Fill top-down), Step 3 (Wire into workflow); Migration protocol; MVP-First (Rule 1), Import-Don't-Rebuild (Rule 2)
- `CLAUDE.md` Rule 1 (R/P Split) — `_merge_api_results()` mixes R and P; refactor separates them
- `CLAUDE.md` Rule 2 (Pattern-First) — priority chain IS the pattern; all sources are instances
- `CLAUDE.md` Rule 3 (Failure Gates) — gates move from inline `if` to typed boundaries
- `CLAUDE.md` Rule 5 (Constraint Gates) — director matching identified as binding constraint; now unified
- `CLAUDE.md` Rule 8 (Prototype Building) — MVP-first: consolidate structure before adding features

**Architecture reference:**
- `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` — two-signal becomes P3 in priority chain (position explicit, logic unchanged)
- `docs/architecture/VALIDATION_ARCHITECTURE.md` — evidence trails become natural byproduct (no shadow pass)

**Related issues:**
- #42 — Two-signal architecture (created `classify_structural()` duplication; this issue resolves it)
- #35 — Evidence architecture (created shadow pass; this issue eliminates it)
- #51 — Catch-all removal (required changes to both `classify()`/`classify_structural()`; proves the duplication cost)
- #52 — Normalisation unification (precedent: unified a duplicated concern into single pipeline stage)
- #30 — Data readiness (created `_assess_readiness()` as private method; this issue promotes it to L3 component)
