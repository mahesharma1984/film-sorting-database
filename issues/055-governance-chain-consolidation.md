# Issue #55: Governance Chain Consolidation — Unified Pipeline + Integrated Doc Routing

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P1-Critical |
| Date Opened | 2026-03-16 |
| Component | classify.py / lib/signals.py / lib/rag/ / docs/WORK_ROUTER.md / docs/WORKFLOW_REGISTRY.md |
| Change Type | Refactor |
| Estimated Effort | 3-5 days |
| Blocked By | None |
| Blocks | All future pipeline work |
| Supersedes | None (builds on #42, #54) |

---

## 1. Manager Summary

**Problem:** The project has accumulated parallel systems that overlap without composing. The classification pipeline smuggles 5 subsystems through 2 functions. The doc-routing layer has 4 independent systems (Work Router, RAG, CORE_DOCUMENTATION_INDEX, Workflow Registry) doing overlapping work with no shared contract. The governance chain model (L1-L5) is documented but not structurally applied to these systems.

**Impact if unfixed:** Every future change requires understanding all parallel systems. New features add complexity to the wrong layer. The pipeline asks `integrate_signals()` to handle lookups, signal integration, AND fallback routing — responsibilities that belong at different architectural levels.

**Risk if fixed wrong:** Classification regressions (91.2% pipeline accuracy is the floor). RAG system breaks. Work Router becomes harder to navigate.

**Estimated effort:** 3-5 days across two phases (pipeline first, doc-routing second).

---

## 2. Evidence

### Observation

**Classification pipeline (3,500 lines across 6 modules):**
- `integrate_signals()` has 10 priority levels (P1-P10), but P1 (Reference canon) is a lookup, P9 (Popcorn) is a separate tier system, and P3/P8 handle conflicts. Only P2/P4/P5/P6/P7 are actual signal integration.
- `score_structure()` calls 4 different subsystems: Reference canon, COUNTRY_TO_WAVE, `satellite.classify_structural()` (14 categories × 6 gates), and `popcorn.classify_reason()`. These aren't "structural scoring."
- `_gather_evidence()` (160 lines) re-runs satellite classification read-only as a shadow pass after classification completes. Duplicates routing logic for diagnostics.
- Satellite caps enforced AFTER signal integration — architectural state leaking across component boundaries.
- `_resolve_user_tag()` is legacy compatibility (0.8 confidence) that 0 films currently use in practice.
- `_attempt_r1_promotion()` promoted 13/491 films — marginal value, 70 lines of code.

**Doc-routing layer (4 parallel systems):**

| System | Lines | Overlap |
|---|---|---|
| Work Router | 400 | Routes problems → docs. §0.3-§0.6 duplicate Workflow Registry procedures |
| RAG (lib/rag/) | 2,924 | Searches docs semantically. Has authority levels, governance filtering — but nothing consumes output programmatically |
| CORE_DOCUMENTATION_INDEX | 136 | 72 Q&A pairs. RAG indexes these AND has its own structured_lookup that duplicates them |
| Workflow Registry | 149 | Named procedures. Some overlap with Work Router checklists |

**Governance chain diagnostic:**

| Symptom | Present | Missing Level |
|---|---|---|
| Same concept reimplemented differently | YES — 4 doc-routing systems | L3 (no shared routing component) |
| L1→L5 complexity jump | YES — RAG has no L2/L3 architecture doc | L2 + L3 |
| Docs say "MVP-first" but implementation is maximal | YES — 2,924 lines to search 57 files | L4 enforcement gap |
| 5 subsystems hidden in 2 function names | YES — `score_structure()` + `integrate_signals()` | L3 (component boundaries wrong) |

### Data

**What worked (pattern from successful past issues):**

| Issue | What It Did | Lines Changed | Result |
|---|---|---|---|
| #54 | Typed boundaries (EnrichedFilm, Resolution), single _build_result() | +82 (pipeline_types.py) | Zero output diff, 402 tests pass |
| #42 | Replaced 6 sequential stages with 2 signals + integration | Net reduction | 373 tests, accuracy held |
| #52 | Unified token lists, Stage 0 integration | Reused existing | 4 new correct classifications |

**Pattern:** Every successful change reduced system count and reused components. Every complexity addition (evidence trails, R1 promotion) created maintenance burden for marginal gain.

---

## 3. Root Cause Analysis

### RC-1: Signal integration scope creep
**Location:** `lib/signals.py` → `integrate_signals()` (lines 242-386) and `score_structure()` (lines 176-235)
**Mechanism:** Reference canon, Popcorn threshold, and conflict resolution were added to the signal integration layer because they needed to participate in priority ordering. But they aren't signals — they're lookups and tier checks. The two-signal model (director + structure) is correct at L1 theory; L5 implementation has absorbed non-signal responsibilities.

### RC-2: Doc-routing systems grew independently
**Location:** `docs/WORK_ROUTER.md`, `lib/rag/`, `docs/CORE_DOCUMENTATION_INDEX.md`, `docs/WORKFLOW_REGISTRY.md`
**Mechanism:** Each system was built to solve a real problem (find docs, route problems, define procedures, enable semantic search). But no L3 component contract connects them. RAG doesn't serve Work Router programmatically. Workflow Registry procedures aren't surfaced through RAG. CORE_DOCUMENTATION_INDEX is both a RAG data source AND a standalone lookup — two roles with no defined boundary.

### RC-3: Evidence trails as shadow pass
**Location:** `classify.py` → `_gather_evidence()` (lines 1092-1250)
**Mechanism:** Diagnostic evidence requires re-running satellite classification read-only after the real classification. This duplicates routing logic and couples the evidence system to satellite internals. Evidence should be a byproduct of classification, not a separate pass.

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| signals.py → classify.py | `integrate_signals()` returns `IntegrationResult` | `_resolve_two_signal()` reads tier/category/confidence | Yes — narrower scope |
| score_structure() → integrate_signals() | Returns `StructuralMatch` list | Integration reads match_type/category | Yes — Reference + Popcorn removed |
| classify.py → evidence | `_gather_evidence()` reads satellite internals | `write_evidence_trails()` | Yes — inline vs shadow |
| Work Router → RAG | §0.8 says "run RAG query" (manual) | Human reads output | Yes — programmatic link |
| CORE_DOCUMENTATION_INDEX → RAG | RAG indexes Quick Reference table | retriever.py reads chunks | No change |

**Gate impact:** Signal integration priority table (P1-P10) changes to narrower scope. Downstream reason codes unchanged — `both_agree`, `director_signal`, `structural_signal`, `review_flagged` all preserved. `reference_canon` reason code preserved but produced by `_resolve_reference()` instead of signal integration.

**Downstream consumers of changed output:**
- `dashboard.py` reads reason codes from manifest — codes preserved, no change
- `scripts/reaudit.py` reads reason codes for stage grouping — codes preserved
- `move.py` reads destination paths from manifest — construction unchanged via `_build_result()`
- `tests/test_signals.py` — needs updating for narrower signal scope

---

## 5. Proposed Fix

### Fix Description

Apply governance chain model to both the classification pipeline and doc-routing layer. MVP-first: strip signal integration to actual signals only, move lookups to the resolve chain where they belong. Connect RAG as the engine behind Work Router instead of parallel to it.

### Phase 1: Classification Pipeline (MVP)

**Principle:** `integrate_signals()` does signals only. Everything else lives in the `_resolve_*()` priority chain.

**Current resolve chain:**
```
P1: _resolve_explicit_lookup()     → SORTING_DATABASE
P2: _resolve_corpus()              → ground truth corpora
    [hard gate: no year]
P3: _resolve_two_signal()          → score_director + score_structure + integrate_signals
P4: _resolve_user_tag()            → filename tag parsing
P5: _resolve_unsorted()            → fallback
```

**Proposed resolve chain:**
```
P1: _resolve_explicit_lookup()     → SORTING_DATABASE (unchanged)
P2: _resolve_corpus()              → ground truth corpora (unchanged)
P3: _resolve_reference()           → REFERENCE_CANON check (NEW — extracted from score_structure)
    [hard gate: no year]
P4: _resolve_two_signal()          → score_director + score_structure + integrate_signals (NARROWED)
P5: _resolve_popcorn()             → Popcorn threshold check (NEW — extracted from score_structure)
P6: _resolve_user_tag()            → filename tag parsing (unchanged, may defer)
P7: _resolve_unsorted()            → fallback (unchanged)
```

**What changes in signals.py:**
- `score_structure()` removes Reference canon check and Popcorn check — returns only Satellite structural matches
- `integrate_signals()` removes P1 (Reference), P9 (Popcorn) — becomes P1-P6 table for director × structure combinations only
- Priority table shrinks from 10 to ~6 entries: both_agree, director_signal (satellite), director_signal (core), structural_signal, review_flagged (conflict), review_flagged (ambiguous), no_match

**Evidence trails:**
- Defer to Phase 2 or make evidence a byproduct of gate evaluation (each `evaluate_category()` call already produces gate results — collect them during classification, don't re-run)

### Phase 1 Execution Order

1. **Step 1:** Add `_resolve_reference()` to `classify.py`
   - Extract Reference canon check from `score_structure()` into a standalone resolver
   - Returns `Resolution(tier='Reference', confidence=1.0, reason='reference_canon')` or None
   - **Verify:** `pytest tests/ -k reference`

2. **Step 2:** Add `_resolve_popcorn()` to `classify.py`
   - Extract Popcorn check from `score_structure()` into a standalone resolver
   - Returns `Resolution(tier='Popcorn', confidence=0.65, reason='popcorn_*')` or None
   - **Verify:** `pytest tests/ -k popcorn`

3. **Step 3:** Narrow `score_structure()` in `lib/signals.py`
   - Remove Reference canon lookup and Popcorn classification
   - Returns only Satellite structural matches (from `classify_structural()`)
   - **Verify:** `pytest tests/test_signals.py`

4. **Step 4:** Narrow `integrate_signals()` in `lib/signals.py`
   - Remove P1 (Reference) and P9 (Popcorn) from priority table
   - Renumber remaining priorities
   - **Verify:** `pytest tests/test_signals.py`

5. **Step 5:** Update resolve chain ordering in `classify.py`
   - Insert `_resolve_reference()` at P3, `_resolve_popcorn()` at P5
   - Shift user_tag to P6, unsorted to P7
   - **Verify:** `pytest tests/ -v` (full suite)

6. **Step 6:** Collect evidence inline (if time permits, else defer)
   - Have `evaluate_category()` return gate results as classification byproduct
   - Remove `_gather_evidence()` shadow pass
   - **Verify:** `pytest tests/test_evidence_trails.py`

7. **Step 7:** Full validation
   - **Verify:** `python classify.py <source>` → diff manifest against baseline
   - **Verify:** `python scripts/reaudit.py --review` → confirmed count ≥ baseline

### Phase 2: Doc-Routing Integration

**Principle:** Work Router = single interface. RAG = engine. Index + Registry = data sources.

1. **Step 1:** Define L3 contract for RAG-as-engine
   - Create `lib/rag/contracts.py` with typed query/response interfaces
   - `route_problem(symptom: str) -> List[DocPointer]`
   - `governance_preflight(component: str) -> GovernanceContext`
   - `find_workflow(task: str) -> Optional[Workflow]`
   - **Verify:** Unit tests for contract functions

2. **Step 2:** Wire Work Router §0.8 through RAG contract
   - Replace manual "run this RAG query" instruction with programmatic call
   - Workflow Registry procedures discoverable through same interface
   - **Verify:** `python3 -m lib.rag.query "governance chain" --level 1 2 3 4` still works

3. **Step 3:** Consolidate Work Router
   - Move §0.3-§0.6 checklists into Workflow Registry as named atomic workflows
   - Keep §0.1 decision tree, §0.2 component lookup, §0.8 governance preflight
   - **Verify:** No broken doc references

4. **Step 4:** Update CORE_DOCUMENTATION_INDEX
   - Mark it as RAG's authority data source (its existing role)
   - Remove any routing responsibility that duplicates Work Router
   - **Verify:** RAG index rebuild works

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `lib/signals.py` | Modify | Remove Reference + Popcorn from `score_structure()` and `integrate_signals()` |
| `classify.py` | Modify | Add `_resolve_reference()`, `_resolve_popcorn()`, reorder chain |
| `lib/rag/contracts.py` | Create | L3 typed interfaces for RAG-as-engine |
| `docs/WORK_ROUTER.md` | Modify | Move §0.3-§0.6 to Workflow Registry, tighten scope |
| `docs/WORKFLOW_REGISTRY.md` | Modify | Add WF-THEORY-CHECK, WF-ARCH-CHECK, WF-DATA-TRACE, WF-DRIFT-AUDIT |
| `tests/test_signals.py` | Modify | Update for narrower signal scope |
| `tests/test_classify.py` | Modify | Update for new resolve chain ordering |

---

## 6. Scope Boundaries

**In scope:**
- Extracting Reference and Popcorn from signal integration into resolve chain
- Narrowing `integrate_signals()` to actual two-signal combinations
- Defining L3 contract for RAG-as-engine
- Consolidating Work Router checklists into Workflow Registry
- Preserving all existing reason codes and classification outputs

**NOT in scope:**
- Removing R1 promotion (marginal but functional — defer)
- Removing user tag recovery (legacy but functional — defer)
- Rewriting RAG internals (system works, just needs contract layer)
- Changing satellite routing rules or category definitions
- Modifying SORTING_DATABASE or corpus data
- Dashboard changes

**Deferred to:** Future issue — evidence trails as inline byproduct (Phase 1 Step 6 is stretch goal)

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Pipeline accuracy | 91.2% | ≥ 91.2% (zero regression) | `python scripts/reaudit.py` |
| Test count | 402 passed, 1 skipped | ≥ 402 passed | `pytest tests/` |
| `integrate_signals()` priority levels | 10 (P1-P10) | ≤ 6 | Code inspection |
| `score_structure()` subsystem calls | 4 (Reference, COUNTRY_TO_WAVE, satellite, popcorn) | 1-2 (satellite structural only) | Code inspection |
| Doc-routing systems | 4 independent | 1 interface + 1 engine + 2 data sources | Architecture inspection |
| Manifest reason codes | All current codes | Identical set | Manifest diff |
| Classification output | Current manifest | Identical manifest (zero diff) | `diff` baseline vs result |

**Pin baseline before implementing:**
```bash
git tag pre-issue-055
cp output/sorting_manifest.csv output/sorting_manifest_pre055.csv
python scripts/reaudit.py > output/pre-055-reaudit.txt
```

---

## 8. Validation Sequence

```bash
# Phase 1 validation
# Step 1: Run full test suite
pytest tests/ -v

# Step 2: Validate handoffs
python scripts/validate_handoffs.py

# Step 3: Classify and diff against baseline
python classify.py <source_directory> --output output/sorting_manifest_post055.csv
diff <(sort output/sorting_manifest_pre055.csv) <(sort output/sorting_manifest_post055.csv)

# Step 4: Reaudit — confirm no regressions
python scripts/reaudit.py --review

# Phase 2 validation
# Step 5: RAG contract tests
pytest tests/test_rag_contracts.py -v

# Step 6: RAG still works end-to-end
python3 -m lib.rag.query "How does satellite routing work?" --top 5
```

**Expected results:**
- Step 1: ≥ 402 tests pass
- Step 2: All gates pass
- Step 3: Zero diff on manifest output (same classifications, same reason codes)
- Step 4: Confirmed count ≥ baseline
- Step 5: Contract tests pass
- Step 6: Relevant results returned

---

## 9. Rollback Plan

**Detection:** Manifest diff shows changed classifications. Reaudit confirmed count drops.

**Recovery:**
```bash
git revert [commit-hash]
```

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-055
```

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `CLAUDE.md` Rule 13 — Governance Chain: fix at highest divergent level; components are enforcement layer; handoff composition > individual complexity; MVP-first
- `CLAUDE.md` Rule 2 — Pattern-First: two-signal architecture is the pattern; Reference and Popcorn are not signals
- `CLAUDE.md` Rule 5 — Constraint Gates: find binding constraint before optimising
- `exports/knowledge-base/governance-chain-theory.md` — L3 components make theory mechanical; without them, docs and code drift

**Architecture reference:**
- `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` — defines two signals as director + structure; Reference and Popcorn are not part of this architecture
- `docs/architecture/RECURSIVE_CURATION_MODEL.md` — stage model; resolve chain is the correct architectural home for priority ordering

**Related issues:**
- #42 — Created two-signal architecture (this issue refines it to match its own theory)
- #54 — Created governance chain L3 types (this issue extends L3 to doc-routing)
- #51 — Removed catch-all categories (same principle: strip to what's structurally justified)
