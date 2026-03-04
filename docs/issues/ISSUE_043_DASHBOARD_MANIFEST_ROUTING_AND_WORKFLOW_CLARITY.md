# Issue #43: Dashboard Manifest Routing and Workflow Clarity

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P2-High |
| Date Opened | 2026-03-05 |
| Component | Dashboard / Audit / Workflow Routing |
| Change Type | Feature / Refactor |
| Estimated Effort | 1-2 days |
| Blocked By | None |
| Blocks | Cleaner Workflow A/B adoption and safer curator operations |
| Supersedes | None |

---

## 1. Manager Summary

**Problem:** The dashboard manifest picker treats almost any CSV in `output/` as equivalent, so users routinely load diagnostic artifacts (`evidence_trails.csv`, `reaudit_report.csv`, `corpus_check_report.csv`) as if they were classification manifests. This blurs Workflow A (Unsorted queue operations) and Workflow B (organised library diagnostics), making routing metrics and two-signal interpretation confusing.

**Impact if unfixed:** Curators make decisions from the wrong dataset, see misleading "Classified %" values (including false 0% views), and risk writing edits to the wrong operational contract (`sorting_manifest.csv` overwrite from non-manifest context). Two-signal layering remains implemented in code but poorly observable in UI.

**Risk if fixed wrong:** Dashboard users could lose access to useful diagnostic CSV views, or edit safety could become overly restrictive and slow curator workflows.

**Estimated effort:** 1-2 days, medium confidence. Core logic change is small; the main effort is workflow-safe UI behavior and validation.

---

## 2. Evidence

### Observation

1. Dashboard sidebar currently auto-lists `output/*.csv` by newest modification time and allows any of them to be selected as the primary "Manifest."
2. Loader coerces missing `tier` to `Unsorted`, so non-manifest CSVs get interpreted as classification manifests and produce misleading global metrics.
3. Edit mode always saves to `output/sorting_manifest.csv` even if the user loaded a different CSV.
4. Project docs explicitly state two canonical dataset contexts:
   - Workflow A queue context: `sorting_manifest.csv`
   - Full library context: `library_audit.csv`
   but UI behavior does not enforce or communicate this boundary.

### Data

Snapshot (2026-03-05, local `output/`):

| Metric | Value |
|---|---|
| Newest CSVs in picker order | `evidence_trails.csv`, `review_queue.csv`, `sorting_manifest.csv`, `reaudit_report.csv`, `corpus_check_report.csv` |
| `sorting_manifest.csv` rows | 361 |
| `sorting_manifest.csv` classified % | 3.9% (14/361) |
| `library_audit.csv` rows | 1080 |
| `library_audit.csv` classified % | 73.7% |
| `reaudit_report.csv` rows | 796 |
| `reaudit_report.csv` classified % in current dashboard interpretation | 0.0% (all tiers backfilled to `Unsorted`) |

Reason-code distribution from current queue manifest (`output/sorting_manifest.csv`):

| Reason | Count |
|---|---|
| `unsorted_no_year` | 173 |
| `unsorted_insufficient_data` | 106 |
| `unsorted_no_match` | 68 |
| `structural_signal` | 10 |
| `review_flagged` | 2 |
| `director_signal` | 2 |

This confirms two-signal output exists, but dashboard context ambiguity reduces interpretability.

---

## 3. Root Cause Analysis

### RC-1: Manifest discovery is schema-agnostic and workflow-agnostic
**Location:** `dashboard.py` -> `find_manifests()`, `render_sidebar()`
**Mechanism:** All CSVs >1KB under `output/` are treated as equivalent "manifest" candidates and sorted by mtime. Diagnostic and audit artifacts appear before operational manifests, steering users into invalid context.

### RC-2: Loader normalizes heterogeneous CSVs into a classification schema
**Location:** `dashboard.py` -> `load_manifest()`
**Mechanism:** Missing classification columns are injected with defaults (including blank `tier` -> `Unsorted`). Files such as `reaudit_report.csv` and `corpus_check_report.csv` become pseudo-manifests with misleading aggregate stats.

### RC-3: Edit save target is hardcoded
**Location:** `dashboard.py` -> `save_edited_csv()`
**Mechanism:** Save path always points to `output/sorting_manifest.csv`, regardless of selected source file. Users can edit data from one context and silently overwrite the Workflow A contract file.

### RC-4: Workflow contracts are documented but not enforced in UI
**Location:** `docs/WORK_ROUTER.md`, `docs/CURATOR_WORKFLOW.md`, `docs/architecture/RECURSIVE_CURATION_MODEL.md` vs dashboard behavior
**Mechanism:** Documentation defines Workflow A and B boundaries, but dashboard has no concept of "queue manifest," "library inventory," "diagnostic report," or "read-only artifact."

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| Workflow A classify output -> dashboard | `classify.py` -> `output/sorting_manifest.csv` | `dashboard.py` overview/triage/edit | Yes (manifest typing + guardrails) |
| Workflow B audit output -> dashboard | `audit.py` -> `output/library_audit.csv` | `dashboard.py` collection overview/browser | Yes (explicit library mode) |
| Reaudit diagnostics -> dashboard | `scripts/reaudit.py` -> `output/reaudit_report.csv` | `dashboard.py` picker/load path | Yes (read-only diagnostic mode or exclusion from manifest picker) |
| Evidence trails -> dashboard | `classify.py` -> `output/evidence_trails.csv` | `dashboard.py` picker/load path | Yes (read-only diagnostic mode or exclusion from manifest picker) |
| Dashboard edit -> queue manifest | `dashboard.py` edit mode | `move.py` consumes `sorting_manifest.csv` | Yes (safe write target enforcement) |
| Two-signal reasons -> signal panel | `classify.py` reason codes (`both_agree`, `director_signal`, etc.) | `dashboard.py` "Classification Signal Quality" | Yes (show panel only for compatible manifest types) |

**Gate impact:** Changes UI-level data-contract gates between workflow artifacts. No classification logic changes, but operator-facing gates become explicit (editable vs read-only datasets).

**Downstream consumers of changed output:**
- `move.py` reads `sorting_manifest.csv`; must remain unchanged and protected from accidental cross-context overwrite.
- Curator manual workflow (`curate.py`, `SORTING_DATABASE.md` updates) depends on reliable queue context from `sorting_manifest.csv` and `review_queue.csv`.
- Diagnostic scripts (`reaudit.py`, `analyze_cohorts.py`) remain producers only; dashboard should consume them in clearly read-only context.

---

## 5. Proposed Fix

### Fix Description

Introduce explicit dataset typing and workflow modes in the dashboard: queue-manifest mode (Workflow A), library-inventory mode (Workflow B), and diagnostic read-only mode. Enforce safe edit/write behavior so only eligible datasets can be edited and written, while preserving access to diagnostics.

### Execution Order

1. **Step 1:** Add dataset classification and picker guardrails in `dashboard.py`
   - **What to change:** Replace raw `find_manifests()` listing with typed discovery:
     - Primary operational files: `sorting_manifest.csv`, `library_audit.csv`
     - Secondary diagnostics: `review_queue.csv`, `reaudit_report.csv`, `evidence_trails.csv`, `corpus_check_report.csv`, corpus drafts
   - **Behavior:** Default picker should prefer `sorting_manifest.csv` or `library_audit.csv` (if present), not newest arbitrary CSV.
   - **Verify:** Run dashboard; confirm default is operational manifest and diagnostic files are clearly separated/labeled.

2. **Step 2:** Add workflow context banners and metric semantics
   - **What to change:** In render path, show explicit context labels:
     - `Queue Manifest (Workflow A)`
     - `Library Audit (Workflow B)`
     - `Diagnostic Report (Read-only)`
   - **Behavior:** Disable or adapt metrics/panels that assume classification schema when schema is diagnostic.
   - **Verify:** Loading `reaudit_report.csv` no longer shows misleading "Classified %" based on coerced tiers.

3. **Step 3:** Lock edit/export modes by dataset type
   - **What to change:** Restrict Edit/Export modes to `sorting_manifest.csv` and optionally `library_audit.csv` (read-only by default unless explicitly enabled).
   - **Behavior:** For diagnostic CSVs, show read-only warning and disable write actions.
   - **Verify:** Attempt editing when `reaudit_report.csv` selected -> blocked with explicit message.

4. **Step 4:** Make save target context-aware and safe
   - **What to change:** Update `save_edited_csv()` to write back to selected editable source path (or an explicit safe derivative file), never silently hardcode `sorting_manifest.csv`.
   - **Behavior:** Add confirmation guard before overwriting an operational manifest.
   - **Verify:** Edit in queue mode updates queue file intentionally; no cross-file overwrite.

5. **Step 5:** Update docs to align workflow/UI contract
   - **What to change:** Update:
     - `docs/WORK_ROUTER.md` dashboard section
     - `docs/CURATOR_WORKFLOW.md` troubleshooting/dashboard notes
     - `README.md` (remove stale pipeline ordering references and clarify dashboard dataset types)
   - **Verify:** `rg` check confirms no stale "any CSV manifest" guidance remains.

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `dashboard.py` | Modify | Typed manifest discovery, workflow context, read-only guards, safer save target |
| `docs/WORK_ROUTER.md` | Update | Dashboard usage reflects typed workflow modes |
| `docs/CURATOR_WORKFLOW.md` | Update | Clarify dashboard contexts and edit-safe behavior |
| `README.md` | Update | Align high-level pipeline/dashboard explanation with two-workflow and two-signal reality |

---

## 6. Scope Boundaries

**In scope:**
- Dashboard dataset typing and picker behavior.
- UI guardrails for workflow context and edit safety.
- Documentation updates for dashboard/workflow usage.

**NOT in scope:**
- Changes to classification routing logic (`classify.py`, `lib/signals.py`).
- Changes to reaudit algorithm or cohort generation logic.
- Full integrated multi-layer analytics dashboard (Issue #41 deferred concept).

**Deferred to:** Follow-up issue for unified analytics view combining `sorting_manifest.csv`, `reaudit_report.csv`, `corpus_check_report.csv`, and `evidence_trails.csv` in one curated analytics surface.

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Default selected CSV in dashboard | Often non-operational (`evidence_trails.csv` currently newest) | Operational default (`sorting_manifest.csv` or `library_audit.csv`) | Launch dashboard, inspect default selection |
| Misleading 0% classified views from diagnostic CSVs | Present (e.g. `reaudit_report.csv` coerced to Unsorted) | Eliminated or clearly labeled as non-classification metric | Load `reaudit_report.csv` and verify context + metrics |
| Cross-context accidental overwrite risk | High (`save_edited_csv()` always writes `sorting_manifest.csv`) | Removed (context-aware write + edit locks) | Attempt edit in diagnostic mode, verify blocked |
| Two-signal panel context correctness | May render on incompatible inputs | Renders only on compatible classification manifests | Load compatible vs incompatible CSVs and compare behavior |

**Pin baseline before implementing:**
```bash
git tag pre-issue-043
python3 - <<'PY'
from pathlib import Path
import dashboard
print([p.name for p in dashboard.find_manifests(Path('output'))[:5]])
PY
```

---

## 8. Validation Sequence

```bash
# Step 1: Run dashboard-related tests (if present) and general suite
pytest tests/ -v

# Step 2: Static sanity checks for dashboard behavior
python3 - <<'PY'
from pathlib import Path
import dashboard
files = dashboard.find_manifests(Path('output'))
print("Top manifests:", [f.name for f in files[:5]])
PY

# Step 3: Manual UI checks
# - Open dashboard
# - Verify default manifest is operational
# - Verify diagnostic CSV loads in read-only mode with correct banner
# - Verify edit mode blocked for diagnostic datasets
# - Verify edit mode saves only in allowed context
streamlit run dashboard.py

# Step 4: Regression check on queue/library contracts
python audit.py
python scripts/reaudit.py --review
```

**Expected results:**
- Step 1: Tests pass (existing baseline pass count, no new failures).
- Step 2: Finder output prioritizes operational manifests over arbitrary newest CSV.
- Step 3: No misleading "manifest" behavior for diagnostic files; no unsafe overwrite path.
- Step 4: No change to classifier/audit/reaudit output schemas from dashboard changes.

**If any step fails:** Stop. Do not proceed. Report failure output and exact selected dataset context.

---

## 9. Rollback Plan

**Detection:** Any of the following after deployment:
- Dashboard no longer allows expected queue editing for `sorting_manifest.csv`.
- Operational manifest selection breaks or omits `library_audit.csv`.
- User workflows blocked due over-restrictive mode guards.

**Recovery:**
```bash
git revert [dashboard-issue-043-commit]
```

If needed, restore prior dashboard file directly from pre-tag:
```bash
git checkout pre-issue-043 -- dashboard.py docs/WORK_ROUTER.md docs/CURATOR_WORKFLOW.md README.md
```

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-043
```

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `CLAUDE.md` Rule 5 (Map before modify): The issue addresses architectural drift between intended workflow contracts and UI behavior.
- `CLAUDE.md` Rule 6 (Evidence architecture): UI should preserve evidence context, not collapse heterogeneous artifacts into one pseudo-manifest.

**Architecture reference:**
- `docs/architecture/RECURSIVE_CURATION_MODEL.md` §Tooling Status: Workflow A/B boundaries and current refine-stage wiring gap.
- `docs/CURATOR_WORKFLOW.md` §Two Workflows + Troubleshooting: queue manifest vs full library inventory.
- `docs/architecture/VALIDATION_ARCHITECTURE.md` §Validation layers: evidence/corpus/accuracy artifacts are distinct layers, not interchangeable manifest contracts.

**Related issues:**
- #41 (Measurement correctness): complementary, not superseded. This issue handles dashboard data-contract clarity; #41 handles measurement model correctness.
- #42 (Unified two-signal architecture): already implemented in classifier layer; this issue improves observability/operability of that layering in UI workflow.

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

