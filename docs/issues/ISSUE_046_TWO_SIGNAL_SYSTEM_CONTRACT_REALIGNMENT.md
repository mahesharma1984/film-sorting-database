# Issue #46: Two-Signal System Contract Realignment (Data, Routing, Workflow)

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P1-Critical |
| Date Opened | 2026-03-05 |
| Component | Classifier Orchestration / Satellite Rules / Signals / Dashboard / Documentation |
| Change Type | Refactor / Architecture Alignment |
| Estimated Effort | 2-4 days |
| Blocked By | None |
| Blocks | #45 implementation, workflow-safe dashboard operation |
| Supersedes | None |

---

## 1. Manager Summary

**Problem:** The repository currently has a contract split between stated architecture and runtime behavior. Two-signal theory says both signals are independently computed and integrated, but movement-category structural behavior, corpus loading, dashboard routing, and several docs still reflect older assumptions.

**Impact if unfixed:** Classification quality signals remain misleading (`both_agree` semantics and movement signal participation), corpus ground truth stays effectively offline in standard runs, and dashboard workflow confusion/unsafe writes persist. This blocks reliable refactor decisions and curation.

**Risk if fixed wrong:** Over-broad movement structural gates could inflate false positives, and incorrect contract rewiring could regress current satellite routing or overwrite operational manifests from the dashboard.

**Estimated effort:** 2-4 days, medium confidence (depends on dashboard UI guardrails and doc convergence breadth).

---

## 2. Evidence

### Observation

1. Manifest + reason code output proves two-signal reasons are active, but movement categories are still mostly director-only in structural practice.
2. Corpus files exist (`data/corpora/*.csv`, 117 entries total), but `classify.py` normal run loads zero corpus entries with current config path contract.
3. Dashboard still treats most CSVs as equivalent manifests and can write edits back to `output/sorting_manifest.csv` regardless of loaded file context.
4. Documentation is internally inconsistent: canonical two-signal docs coexist with legacy sequential/stage language and director-only movement guidance.

### Data

Snapshot from current local run artifacts (`output/sorting_manifest.csv`, modified 2026-03-05 11:27):

| Metric | Value |
|---|---|
| Manifest rows | 1255 |
| Reason top 5 | explicit_lookup 389, structural_signal 212, unsorted_no_year 173, unsorted_insufficient_data 106, unsorted_no_match 97 |
| Readiness | R3 814, R0 276, R1 131, R2 34 |
| `both_agree` total | 23 |
| `both_agree` in movement categories | 1 FNW (keyword-tier B case), 0 AmNH, 0 JNW, 0 HK New Wave, 0 HK Cat III |

Movement signal examples:

| Film | Structural matches | Integrated result |
|---|---|---|
| Taxi Driver (US, 1976, Scorsese) | `[]` | `director_signal` -> Satellite/American New Hollywood/1970s/ (0.65) |
| Jules and Jim (FR, 1962, Truffaut) | EuroSex + Indie | `director_disambiguates` -> Satellite/French New Wave/1960s/ (0.75) |
| Boat People (HK, 1982, Ann Hui) | `[]` | no HK New Wave structural signal |

Signal semantics edge case:
- `A Woman is a Woman (1961)` structural matches `French New Wave` (keyword tier B) + `European Sexploitation` + `Indie Cinema`, yet integration returns `both_agree` (0.85). This overstates agreement under structural overlap.

Corpus availability vs runtime use:

| Check | Value |
|---|---|
| Corpus files present under `data/corpora/` | 5 files, 117 entries |
| `corpus_lookup` reason in current manifest | 0 |
| Corpus matches detectable against current manifest titles/years | 79 hits (48 currently explicit_lookup, 31 currently heuristic/staging) |

Root contract mismatch causing corpus disablement:
- `config_external.yaml` sets `project_path: .../docs`.
- `classify.py` resolves corpora as `project_path / data / corpora`.
- Effective lookup becomes `docs/data/corpora` (missing), so corpus layer is disabled.

Dashboard routing evidence:
- `dashboard.find_manifests(output/)` top list currently starts with diagnostic files: `lookup_coverage.csv`, `evidence_trails.csv`, `review_queue.csv`, then `sorting_manifest.csv`.
- Loading `reaudit_report.csv` through `dashboard.load_manifest()` yields `tier='Unsorted'` for all rows -> "classified %" displayed as 0.0%.
- Edit save path remains hardcoded to `output/sorting_manifest.csv`.

Cache/data availability:

| Cache | Total | Null | Null % |
|---|---|---|---|
| TMDb | 971 | 214 | 22.0% |
| OMDb | 974 | 254 | 26.1% |
| Both null on same key | 160 |  |  |

---

## 3. Root Cause Analysis

### RC-1: Config/path contract drift disables corpus in normal classifier runs
**Location:** `config_external.yaml` + `classify.py` -> `FilmClassifier._setup_components()`
**Mechanism:** `project_path` is treated as docs root for lookup/core files and as repo root for corpora. This mixed interpretation causes `corpora_dir` to resolve to a non-existent path and silently disable corpus lookup.

### RC-2: Movement structural participation is not explicitly modeled; data shape encodes policy implicitly
**Location:** `lib/constants.py` -> `SATELLITE_ROUTING_RULES`; `lib/satellite.py` -> `classify_structural()` and `classify()`
**Mechanism:** Movement categories still use `country_codes: []` and `genres: []`, which makes structural gate checks fail except keyword-tier B fallthroughs. Policy ("director-only", "candidate structural", "manual-only") is encoded indirectly via empty lists instead of explicit routing mode fields.

### RC-3: `both_agree` integration logic does not enforce structural uniqueness
**Location:** `lib/signals.py` -> `integrate_signals()`
**Mechanism:** P2 uses "any structural match equals director category" as sufficient for `both_agree`, even when multiple structural categories also match. This can label ambiguous structural contexts as highest-confidence agreement.

### RC-4: Dashboard dataset typing and write contract remain workflow-agnostic
**Location:** `dashboard.py` -> `find_manifests()`, `load_manifest()`, `save_edited_csv()`
**Mechanism:** Generic CSV listing + schema coercion makes diagnostics look like manifests; edit-save path writes to `sorting_manifest.csv` regardless of selected context.

### RC-5: Documentation convergence failure
**Location:** `README.md`, `docs/CURATOR_WORKFLOW.md`, `docs/architecture/RECURSIVE_CURATION_MODEL.md`, `CLAUDE.md`, `docs/SATELLITE_CATEGORIES.md`
**Mechanism:** Issue #42 architecture and reason-code model were added, but several user-facing docs and rule notes still describe pre-#42 stage chains and director-only movement semantics.

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| Config path -> classifier setup | `config_external.yaml` | `classify.py:_setup_components()` | Yes |
| Corpus files -> corpus lookup layer | `data/corpora/*.csv` | `lib/corpus.py:CorpusLookup` | No (path resolution only) |
| Satellite rule definitions -> structural scoring | `lib/constants.py:SATELLITE_ROUTING_RULES` | `lib/satellite.py:classify_structural()` | Yes |
| Satellite rule definitions -> director registry semantics | `lib/constants.py:_build_director_registry()` | `lib/signals.py:score_director()` | Yes |
| Signal outputs -> integration confidence class | `score_director()` + `score_structure()` | `integrate_signals()` | Yes |
| Manifest discovery -> dashboard context | `output/*.csv` | `dashboard.py` sidebar and panels | Yes |
| Dashboard edit output -> move workflow | `dashboard.py:save_edited_csv()` | `move.py` reading `sorting_manifest.csv` | Yes |
| Architecture docs -> curator/operator decisions | docs + issue specs | human workflow and future issues | Yes |

**Gate impact:**  
- Re-enabling corpus changes stage-2.5 high-trust routing volume.  
- Movement structural policy changes reason-code mix (`director_signal` vs `director_disambiguates`/`both_agree`/`review_flagged`).  
- Integration semantics change confidence distribution for overlapping structural matches.  
- Dashboard guardrails change which files are editable and where writes are allowed.

**Downstream consumers of changed output:**
- `move.py` (operational manifest consumer; must not receive accidental edits from diagnostic contexts)
- `scripts/reaudit.py` (accuracy accounting by reason code)
- `scripts/analyze_cohorts.py` and `scripts/unsorted_readiness.py` (triage outputs depend on manifest/evidence semantics)
- Curator workflow docs and manual decision loops (`CURATOR_WORKFLOW.md`, `SORTING_DATABASE.md` practices)

---

## 5. Proposed Fix

### Fix Description
Refactor the system around explicit, aligned contracts: path contracts (repo root vs docs path), explicit movement/tradition signal policy, stricter integration semantics for true agreement, dashboard dataset typing with safe write boundaries, and documentation convergence on one architecture narrative.

### Execution Order

1. **Step 1:** Fix path contracts in classifier config plumbing
   - **What to change:** Add explicit config semantics (`project_root`, `docs_path`) with backward-compatible fallback; load corpora from repo-root `data/corpora`.
   - **Verify:** instantiate classifier and confirm `corpus_lookup.get_stats()['total_entries'] == 117`.

2. **Step 2:** Make movement/tradition semantics explicit in routing rules
   - **What to change:** Introduce explicit fields (`is_tradition`, and/or explicit structural participation mode) in `SATELLITE_ROUTING_RULES`; stop deriving semantics from `bool(country_codes)`.
   - **Verify:** smoke tests for FNW/AmNH/JNW/HK New Wave/HK Cat III structural behavior match intended policy.

3. **Step 3:** Tighten integration semantics for `both_agree`
   - **What to change:** In `integrate_signals()`, require structural uniqueness for `both_agree`; multi-structural overlap with director should route as disambiguation/review path, not max-confidence agreement.
   - **Verify:** `A Woman is a Woman (1961)` no longer returns `both_agree` under multi-structural overlap.

4. **Step 4:** Dashboard dataset typing and safe write routing
   - **What to change:** Typed dataset discovery (operational vs diagnostic), context banners, edit/export lockouts for non-operational datasets, and save target bound to selected editable dataset.
   - **Verify:** `reaudit_report.csv` and `evidence_trails.csv` load read-only; no hardcoded overwrite of `sorting_manifest.csv` from other contexts.

5. **Step 5:** Align triage/analysis scripts with current contracts
   - **What to change:** Update `scripts/unsorted_readiness.py` to use same API-cleaning/cache-key logic as classifier; ensure reaudit confidence/reason mapping uses current reason set.
   - **Verify:** readiness counts align with manifest `data_readiness`; no stale legacy reason assumptions in outputs.

6. **Step 6:** Documentation convergence pass
   - **What to change:** Update architecture + workflow docs to one authoritative model and deprecate legacy stage-chain language in user-facing docs.
   - **Verify:** targeted grep on key docs for stale terms (`core_director`, `tmdb_satellite`, `country_satellite`, "first match wins") returns 0 where the docs are intended to be current architecture references.

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `classify.py` | Modify | path contract resolution for docs vs repo-root resources; corpus loading path fix |
| `config_external.yaml` and `config.yaml` | Modify | explicit path keys and comments |
| `lib/constants.py` | Modify | explicit routing semantics fields; director registry semantics source |
| `lib/satellite.py` | Modify | structural behavior tied to explicit mode fields |
| `lib/signals.py` | Modify | `both_agree` uniqueness guard and overlap handling |
| `dashboard.py` | Modify | typed dataset discovery, context banners, safe edit/write gates |
| `scripts/unsorted_readiness.py` | Modify | cache key cleaning parity with classifier |
| `scripts/reaudit.py` | Modify | remove stale legacy confidence map assumptions |
| `README.md` | Update | modern reason codes and architecture summary |
| `docs/CURATOR_WORKFLOW.md` | Update | reason codes and workflow data contract |
| `docs/architecture/RECURSIVE_CURATION_MODEL.md` | Update | routing narrative aligned to unified two-signal model |
| `CLAUDE.md` | Update | remove/clarify stale movement director-only notes and stage references |
| `docs/SATELLITE_CATEGORIES.md` | Update | explicit movement structural policy and rationale |
| `tests/test_signals.py` | Update | assert overlap behavior and agreement semantics |
| `tests/test_satellite_director_routing.py` | Update | movement/tradition semantic coverage |
| `tests/test_dashboard_validation.py` (or new test file) | Add/Update | dataset typing and safe save behavior |

---

## 6. Scope Boundaries

**In scope:**
- Path/data contracts required for classifier correctness (including corpus activation).
- Two-signal integration semantics and movement/tradition explicit policy modeling.
- Dashboard data-contract safety for manifest selection and writes.
- Convergence updates for core architecture/workflow docs.

**NOT in scope:**
- Adding new satellite categories or large director-list expansions (Issue #44 domain).
- Large-scale taxonomy redesign of satellite categories.
- Re-scoring historical manifests as part of this issue (measurement only unless explicitly requested).
- Network/API vendor changes or cache backend redesign.

**Deferred to:**  
- #45 final policy choice details if movement structural participation requires per-category curation experiments.  
- Follow-up issue for broader archival docs cleanup outside core user/operator docs.

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Corpus entries loaded in normal classifier init | 0 | 117 | python classifier init probe |
| `corpus_lookup` reason count in baseline dataset | 0 | >=20 (same source snapshot) | count in `output/sorting_manifest.csv` |
| `both_agree` under multi-structural overlap | present (e.g., A Woman is a Woman) | 0 | targeted integration smoke test |
| Dashboard default operational context | no (diagnostic CSV often first) | yes (`sorting_manifest.csv` or `library_audit.csv`) | `dashboard.find_manifests()` + UI check |
| Diagnostic CSV editable/writeable to operational manifest | yes | no | load diagnostic, attempt edit/save |
| Architecture doc drift on key docs | high | low | targeted grep on selected docs |

**Pin baseline before implementing:**
```bash
git tag pre-issue-046
python3 - <<'PY'
import csv
from collections import Counter
rows=list(csv.DictReader(open('output/sorting_manifest.csv')))
print('reasons', Counter(r['reason'] for r in rows).most_common(12))
PY
python scripts/reaudit.py
```

---

## 8. Validation Sequence

```bash
# Step 1: Run targeted tests first
pytest tests/test_signals.py tests/test_satellite_director_routing.py -v

# Step 2: Validate classifier path contracts and corpus availability
python3 - <<'PY'
from pathlib import Path
from classify import FilmClassifier
fc = FilmClassifier(Path('config_external.yaml'), no_tmdb=True)
print(fc.corpus_lookup.get_stats())
PY

# Step 3: Validate movement/overlap integration behavior
python3 - <<'PY'
from types import SimpleNamespace
from pathlib import Path
from lib.satellite import SatelliteClassifier
from lib.popcorn import PopcornClassifier
from lib.core_directors import CoreDirectorDatabase
from lib.signals import score_director, score_structure, integrate_signals
sc=SatelliteClassifier(); pc=PopcornClassifier(); core=CoreDirectorDatabase(Path('docs/CORE_DIRECTOR_WHITELIST_FINAL.md'))
meta=SimpleNamespace(title='A Woman is a Woman', year=1961, country='FR', director='Jean-Luc Godard')
tmdb={'countries':['FR','IT'],'genres':['Comedy','Drama','Romance'],'keywords':['french new wave']}
d=score_director(meta.director, meta.year, core)
s=score_structure(meta, tmdb, sc, pc)
r=integrate_signals(d, s, '1960s', 'R3')
print(r.reason, r.destination, r.confidence)
PY

# Step 4: Validate dashboard dataset typing and safety behavior
python3 - <<'PY'
from pathlib import Path
import dashboard
print([p.name for p in dashboard.find_manifests(Path('output'))[:10]])
PY

# Step 5: Run broader regression checks
pytest tests/ -q
python audit.py
python scripts/reaudit.py
python scripts/unsorted_readiness.py
```

**Expected results:**
- Step 1: targeted tests pass with updated semantics.
- Step 2: corpus stats report non-zero entries (117 in current local corpus set).
- Step 3: multi-structural overlap case does not return `both_agree`.
- Step 4: operational manifests are clearly prioritized/typed; diagnostics are not unsafe edit contexts.
- Step 5: no net regression in re-audit confirmed totals; no new systemic misrouting cluster.

**If any step fails:** Stop and report failing command output plus the exact contract boundary that failed.

---

## 9. Rollback Plan

**Detection:**  
- Reaudit confirmed score drops below pre-issue baseline.  
- Movement categories show widespread false-positive structural routing.  
- Dashboard edits can still overwrite operational manifest from diagnostic context.  
- Corpus layer unexpectedly routes incorrect categories at confidence 1.0.

**Recovery:**
```bash
git revert [issue-046-commit-hash]
python scripts/reaudit.py
python scripts/unsorted_readiness.py
```

If movement policy sub-step is isolated and fails, revert only constants/signals/satellite commits first.

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-046
```

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `CLAUDE.md` Rule 5 (Map before modify): this issue resolves mapped contract drift before new feature work.
- `CLAUDE.md` Rule 6 (Evidence architecture): restores consistent evidence semantics across classifier and dashboard outputs.
- `exports/knowledge-base/system-boundary-theory.md`: boundary contracts (config/path/routing/UI) must be explicit, not inferred from incidental data shape.
- `exports/knowledge-base/exploration-theory.md`: staged, measurement-anchored refactor after drift diagnosis.

**Architecture reference:**
- `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` - canonical signal model and reason-code semantics.
- `docs/architecture/VALIDATION_ARCHITECTURE.md` - layered trust model and diagnostic contracts.
- `docs/architecture/RECURSIVE_CURATION_MODEL.md` - workflow and routing context (to be converged with canonical two-signal model).

**Related issues:**
- #42 (unified two-signal architecture): implemented core model; this issue resolves downstream contract drift.
- #43 (dashboard manifest routing clarity): directly addressed as part of dataset typing and safe writes.
- #45 (movement structural signal alignment): addressed via explicit movement/tradition policy modeling and integration semantics.

---

### Section Checklist (for spec author)

- [x] §1 Manager Summary is readable without code knowledge
- [x] §3 Root causes reference specific files and functions
- [x] §4 ALL downstream consumers are listed (not just the obvious ones)
- [x] §5 Execution Order has verify commands for each step
- [x] §5 Files to Modify is complete (no surprise files during implementation)
- [x] §6 NOT in scope is populated (prevents scope creep)
- [x] §7 Measurement Story has concrete before/after numbers
- [x] §8 Validation Sequence commands are copy-pasteable
- [x] §9 Baseline is pinned before implementation starts
- [x] §10 Theory grounding exists (change is justified by documented principles)
