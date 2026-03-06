# Issue #48: Scholarship-Only Routing Contract — Decommission Core/Reference/Explicit Lookup

| Field | Value |
|---|---|
| Status | SPEC |
| Priority | P1-Critical |
| Date Opened | 2026-03-05 |
| Component | Classifier / Signals / Validation / Dashboard |
| Change Type | Architecture Refactor |
| Estimated Effort | 1-2 days |
| Blocked By | None |
| Blocks | Scholarship baseline re-measurement and corpus-first routing rollout |
| Supersedes | None |

---

## 1. Manager Summary

**Problem:** The active classification contract is still dominated by human intervention layers (`explicit_lookup`, Core whitelist routing, Reference canon), so current accuracy appears high while the scholarship-grounded two-signal system remains under-exercised.

**Impact if unfixed:** We cannot measure or improve the real two-signal system credibly because curated overrides pre-empt routing on a large fraction of films. Baselines stay inflated by manual decisions.

**Risk if fixed wrong:** Immediate quality regression in production manifests (more `DISAGREE`/`UNSORTED`) and downstream workflow disruption (`move.py`, dashboard expectations, curator routines) if legacy tiers are removed without contract updates.

**Estimated effort:** 1-2 days, medium confidence. Core logic changes are straightforward; most effort is contract migration, measurement updates, and downstream compatibility.

---

## 2. Evidence

### Observation

Current outputs show the classifier is not primarily operating as a scholarship-only system:

- `explicit_lookup` remains the largest reason in queue classification.
- `Core` and `Reference` still receive active routing outcomes.
- Explicit-lookup bypass audit shows the two-signal layer disagrees or fails on most pinned films.

### Data

From `output/sorting_manifest.csv`:

| Metric | Value |
|---|---|
| Total films | 1255 |
| `explicit_lookup` reason count | 389 |
| `reference_canon` reason count | 10 |
| `Core` tier count | 138 |
| `Reference` tier count | 38 |

Top reasons (manifest):
- `explicit_lookup`: 389
- `structural_signal`: 212
- `unsorted_no_year`: 173
- `unsorted_insufficient_data`: 106
- `unsorted_no_match`: 97

From `output/lookup_coverage.csv` (bypass audit on 389 explicit pins):

| Verdict | Count | Rate |
|---|---:|---:|
| AGREE | 122 | 31.4% |
| DISAGREE | 172 | 44.2% |
| UNSORTED | 95 | 24.4% |

From `output/reaudit_report.csv`:

| Metric | Value |
|---|---|
| Total audited films | 796 |
| Confirmed | 718 |
| Discrepancies | 78 |
| `classified_reason=explicit_lookup` | 386 |

Interpretation: current confirmation metrics include a large curated population and are not a clean baseline for autonomous scholarship-layer performance.

---

## 3. Root Cause Analysis

### RC-1: Explicit lookup pre-empts two-signal routing
**Location:** `classify.py` -> `FilmClassifier.classify()` Stage 2 (`explicit_lookup`)
**Mechanism:** Stage 2 returns before signal scoring/integration, so pinned films never exercise `score_director()`/`score_structure()`/`integrate_signals()`.

### RC-2: Core and Reference are still active decision layers
**Location:** `lib/signals.py` -> `score_director()`, `score_structure()`, `integrate_signals()`
**Mechanism:** Core whitelist matches and Reference canon matches still produce first-class routing outcomes (`Core`, `Reference`) in the same decision path as scholarship-driven satellite/popcorn routing.

### RC-3: Measurement workflow still treats intervention layers as normal routing
**Location:** `scripts/reaudit.py`, `dashboard.py`
**Mechanism:** Accuracy/readout flows consume mixed-contract manifests by default; this blends curated overrides with autonomous outputs and obscures the true scholarship-only baseline.

### RC-4: Dataset selection in dashboard increases workflow ambiguity
**Location:** `dashboard.py` -> `find_manifests()` / sidebar selector
**Mechanism:** Newest CSV selection encourages mixing diagnostics and queue manifests, making contract interpretation inconsistent across runs.

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| Lookup -> Classifier decision | `classify.py` Stage 2 (`lookup_db.lookup`) | `classify.py` final result | Yes |
| Core whitelist -> Director signal | `lib/core_directors.py`, `lib/signals.py:score_director()` | `integrate_signals()` | Yes |
| Reference canon -> Structural signal | `lib/constants.py:REFERENCE_CANON`, `lib/signals.py:score_structure()` | `integrate_signals()` | Yes |
| Signal integration -> Manifest schema semantics | `lib/signals.py:integrate_signals()` | `output/sorting_manifest.csv` | Yes |
| Manifest -> Move workflow | `classify.py` output | `move.py` | Yes |
| Manifest -> Audit/visualization | `classify.py` output | `scripts/reaudit.py`, `dashboard.py` | Yes |

**Gate impact:**
- Reason-code distribution will shift materially; old baselines are invalid after this change.
- Tier contract changes from 4+intervention layers to scholarship-only routing tiers.
- Regression gate changes from “confirmed >= 718” to “stable scholarship-only baseline and improving over iterations.”

**Downstream consumers of changed output:**
- `move.py` (reads `destination`, tier paths)
- `scripts/reaudit.py` (population segmentation and reason grouping)
- `dashboard.py` (tier charts, reason confidence mapping, edit/export assumptions)
- Curator docs and runbooks (`README.md`, `docs/DEVELOPER_GUIDE.md`, `docs/CURATOR_WORKFLOW.md`, `docs/architecture/*`)

---

## 5. Proposed Fix

### Fix Description

Adopt a scholarship-only routing contract in the classifier: remove `explicit_lookup`, Core tier routing, and Reference tier routing from the active decision path. Keep corpus lookup (`corpus_lookup`) as the scholarship-grounded high-trust layer, then route via two-signal (Satellite/Popcorn/Unsorted). Update measurement and dashboard workflows so baselines no longer mix curated intervention with autonomous routing.

### Execution Order

1. **Step 1:** Add routing contract mode to classifier entrypoints
   - **What to change:** `classify.py` CLI/config supports `routing_contract` with values:
     - `legacy` (current behavior, temporary compatibility only)
     - `scholarship_only` (new contract)
   - **Verify:** `python classify.py <source_dir> --routing-contract scholarship_only --output output/scholarship_manifest.csv`

2. **Step 2:** Disable explicit lookup in scholarship-only mode
   - **What to change:** `classify.py` Stage 2 (`explicit_lookup`) bypassed when `routing_contract=scholarship_only`.
   - **Depends on:** Step 1
   - **Verify:** `rg -n \"explicit_lookup\" output/scholarship_manifest.csv` returns 0 data rows.

3. **Step 3:** Remove Core/Reference routing paths in scholarship-only mode
   - **What to change:**
     - `lib/signals.py:score_director()` does not emit Core matches in scholarship-only mode.
     - `lib/signals.py:score_structure()` does not emit Reference canon matches in scholarship-only mode.
     - `lib/signals.py:integrate_signals()` returns only Satellite/Popcorn/Unsorted outcomes under scholarship-only contract.
     - `classify.py` user-tag recovery no longer routes to `Core`/`Reference` in scholarship-only mode.
   - **Depends on:** Step 1
   - **Verify:** manifest has no `tier=Core` and no `tier=Reference`; no `reason=reference_canon`.

4. **Step 4:** Update measurement scripts for scholarship baseline
   - **What to change:** `scripts/reaudit.py` supports `--routing-contract scholarship_only` and writes contract metadata + baseline summary (including reason/tier distributions under new contract).
   - **Depends on:** Steps 1-3
   - **Verify:** `python scripts/reaudit.py --routing-contract scholarship_only --review` runs and writes updated summary.

5. **Step 5:** Update dashboard workflow labeling and defaults
   - **What to change:** `dashboard.py` detects contract type from manifest metadata or filename convention and labels views accordingly; avoid implying legacy-tier semantics on scholarship-only manifests.
   - **Depends on:** Step 4
   - **Verify:** scholarship manifest loads with correct context banner and tier/reason interpretation.

6. **Step 6:** Update docs to new contract
   - **What to change:** `README.md`, `docs/DEVELOPER_GUIDE.md`, `docs/CURATOR_WORKFLOW.md`, `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md`, `docs/architecture/VALIDATION_ARCHITECTURE.md`.
   - **Verify:** grep for stale “explicit_lookup-first/Core/Reference active routing” statements in canonical docs.

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `classify.py` | Modify | Add routing contract mode; skip Stage 2 explicit lookup; disable Core/Reference fallbacks in scholarship mode |
| `lib/signals.py` | Modify | Gate Core/Reference emissions by routing contract |
| `scripts/reaudit.py` | Modify | Contract-aware baseline and reporting |
| `dashboard.py` | Modify | Contract-aware dataset semantics and labeling |
| `README.md` | Update | Pipeline order and tier semantics |
| `docs/DEVELOPER_GUIDE.md` | Update | New execution/validation workflow |
| `docs/CURATOR_WORKFLOW.md` | Update | Curator expectations under scholarship-only contract |
| `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` | Update | Remove legacy intervention-first contract from canonical path |
| `docs/architecture/VALIDATION_ARCHITECTURE.md` | Update | New baseline definitions and success criteria |

---

## 6. Scope Boundaries

**In scope:**
- Decommission `explicit_lookup`, Core routing, and Reference routing from active classifier contract (scholarship-only mode).
- Contract-aware measurement and dashboard updates.
- Documentation updates for new canonical pipeline.

**NOT in scope:**
- Physically migrating existing organized library folders from `Core/` and `Reference/` to other tiers.
- Deleting `SORTING_DATABASE.md`, `CORE_DIRECTOR_WHITELIST_FINAL.md`, or `REFERENCE_CANON` data sources from the repository.
- Expanding corpus coverage content itself (new scholarship CSV entries).

**Deferred to:** Follow-up migration issue for library folder reorganization and historical Core/Reference inventory reassignment.

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---:|---:|---|
| `explicit_lookup` reason count (manifest) | 389 | 0 | `python classify.py ... --routing-contract scholarship_only` + reason count |
| `reference_canon` reason count (manifest) | 10 | 0 | same manifest reason count |
| `Core` tier rows (manifest) | 138 | 0 | tier count in scholarship manifest |
| `Reference` tier rows (manifest) | 38 | 0 | tier count in scholarship manifest |
| Explicit-bypass dependency | AGREE 31.4%, FAIL 68.6% | Baseline captured in scholarship run (no bypass layer) | `python scripts/audit_lookup_coverage.py` + scholarship manifest |
| Reaudit contract clarity | mixed (explicit_lookup 386/796) | 0 curated-override reasons in scholarship run | `python scripts/reaudit.py --routing-contract scholarship_only` |

**Pin baseline before implementing:**
```bash
git tag pre-issue-048
python scripts/reaudit.py --review > output/pre-048-reaudit.txt
python scripts/audit_lookup_coverage.py > output/pre-048-lookup-coverage.txt
```

---

## 8. Validation Sequence

```bash
# Step 1: Full tests
pytest tests/ -v

# Step 2: Contract handoff validation
python scripts/validate_handoffs.py

# Step 3: Scholarship-only classification run
python classify.py <source_directory> --routing-contract scholarship_only --output output/scholarship_manifest.csv

# Step 4: Verify removal of legacy intervention reasons/tiers
python3 - <<'PY'
import csv
from collections import Counter
rows=list(csv.DictReader(open('output/scholarship_manifest.csv')))
r=Counter(x['reason'] for x in rows); t=Counter(x['tier'] for x in rows)
assert r['explicit_lookup']==0, r['explicit_lookup']
assert r['reference_canon']==0, r['reference_canon']
assert t['Core']==0, t['Core']
assert t['Reference']==0, t['Reference']
print('legacy layers removed in scholarship manifest')
PY

# Step 5: Scholarship-only reaudit
python scripts/reaudit.py --routing-contract scholarship_only --review
```

**Expected results:**
- Tests pass.
- Scholarship manifest contains no `explicit_lookup`, no `reference_canon`, no `Core` tier, no `Reference` tier.
- Reaudit runs with scholarship-only contract and reports contract-aware metrics.

**If any step fails:** Stop and report the failing command output before proceeding.

---

## 9. Rollback Plan

**Detection:**
- `move.py` cannot consume scholarship manifest destinations.
- Dashboard/reaudit fails to parse new contract semantics.
- Scholarship manifest writes unexpected legacy tiers/reasons.

**Recovery:**
```bash
git revert <issue-048-commit-hash>

# Temporary operational fallback:
python classify.py <source_directory> --routing-contract legacy --output output/sorting_manifest.csv
python scripts/reaudit.py --review
```

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-048
```

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `CLAUDE.md` Rule 4 (Domain Grounding): routing should be anchored to scholarship-defined categories, not curator-only override layers.
- `CLAUDE.md` Rule 7 (Measurement-Driven Development): establish truthful baselines before optimization.
- `CLAUDE.md` Rule 6 (Boundary-Aware Measurement): separate intervention-layer effects from heuristic-system performance.

**Architecture reference:**
- `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md`: signal computation and integration contracts.
- `docs/architecture/VALIDATION_ARCHITECTURE.md`: population-aware measurement and audit semantics.
- `docs/WORK_ROUTER.md` §0.7: investigation -> spec workflow before implementation.

**Related issues:**
- #42 — unified two-signal architecture (introduced current integration backbone).
- #45 — movement structural signal activation (expanded structural participation).
- #46 — contract realignment (identified architecture/measurement drift).
- #47 — Core-director overlap bug (symptom-level conflict within mixed contract).

---
