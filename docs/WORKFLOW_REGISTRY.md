# Workflow Registry

**Purpose:** Named, repeatable procedures for engineering and curation work in this repository.

---

## Section 1: Atomic Workflows

### WF-GOV-PREFLIGHT: Governance chain preflight

**When:** Before changing classification, routing, validation, or reporting logic.
**Command:**
```bash
python3 -m lib.rag.query "governance chain for this task" --top 8 --level 1 2 3 4
```
**Output:** Ranked governance-context sections (theory, architecture, component-facing docs, dev rules).
**Verify:** Results include `exports/knowledge-base/governance-chain-theory.md` and at least one `docs/architecture/*` and `docs/DEVELOPER_GUIDE.md`/`docs/WORK_ROUTER.md` hit.

### WF-TEST-UNIT: Run unit tests

**When:** After code changes.
**Command:**
```bash
pytest tests/
```
**Output:** Test report.
**Verify:** All required tests pass.

### WF-HANDOFF-VALIDATE: Validate stage handoffs

**When:** After enrichment/routing contract changes.
**Command:**
```bash
python scripts/validate_handoffs.py
```
**Output:** Handoff validation report.
**Verify:** No contract-breaking failures.

### WF-CLASSIFY-RUN: Run classification

**When:** Processing new films or validating routing changes.
**Command:**
```bash
python classify.py <source_directory>
```
**Output:** `output/sorting_manifest.csv` and evidence artifacts.
**Verify:** Manifest generated and reason/tier fields populated.

### WF-REAUDIT-REVIEW: Run reaudit review

**When:** Validating organised-library correctness after rule changes.
**Command:**
```bash
python scripts/reaudit.py --review
```
**Output:** `output/reaudit_review.md`.
**Verify:** Expected discrepancy cohorts are reduced or explained.

### WF-BASELINE-PIN: Pin baseline before risky changes

**When:** Before medium/large changes.
**Command:**
```bash
cp output/sorting_manifest.csv output/sorting_manifest_backup.csv
```
**Output:** Baseline manifest copy.
**Verify:** `output/sorting_manifest_backup.csv` exists and is non-empty.

### WF-MANIFEST-COMPARE: Compare manifests

**When:** After routing logic updates.
**Command:**
```bash
python compare_manifests.py output/sorting_manifest_backup.csv output/sorting_manifest.csv
```
**Output:** Before/after routing diff.
**Verify:** Deltas are expected and justified.

---

## Section 2: Composed Workflows

### CW-GOVERNED-CHANGE: Make and validate a governed code change

**When:** Any non-trivial pipeline logic change.
**Steps:**
1. `WF-GOV-PREFLIGHT` — read chain context in level order.
2. `WF-BASELINE-PIN` — pin current routing state.
3. Implement change.
4. `WF-TEST-UNIT` — verify local correctness.
5. `WF-HANDOFF-VALIDATE` — verify stage contracts.
6. `WF-CLASSIFY-RUN` — generate new manifest.
7. `WF-MANIFEST-COMPARE` — review routing deltas.
8. `WF-REAUDIT-REVIEW` — confirm organised-library impact.

### CW-FIX-REGRESSION: Regression diagnosis and recovery

**When:** Classification rate or quality drops after a change.
**Steps:**
1. `WF-MANIFEST-COMPARE` — identify changed films/reasons.
2. Diagnose via `docs/WORK_ROUTER.md` Category 0.
3. Apply fix at highest divergent level (theory/architecture/component/rule/code).
4. `WF-TEST-UNIT` and `WF-HANDOFF-VALIDATE`.
5. `WF-CLASSIFY-RUN` and `WF-MANIFEST-COMPARE` again.

### CW-CURATION-CYCLE: End-to-end classify and curate loop

**When:** Regular curation pass.
**Steps:**
1. `WF-CLASSIFY-RUN`.
2. Run `python audit.py` to refresh library-wide inventory.
3. `WF-REAUDIT-REVIEW`.
4. Act on high-confidence discrepancy cohorts.
5. Re-run `WF-CLASSIFY-RUN` and `WF-REAUDIT-REVIEW` to verify closure.

---

## Section 3: Cross-Cutting Patterns

### Pattern 1: Governance Order Is Mandatory

Before code changes, read constraints in this order:
1. Theory (L1)
2. Architecture (L2)
3. Components/contracts (L3)
4. Dev rules/workflows (L4)
5. Code (L5)

### Pattern 2: Depth Then Breadth

After a change:
1. Validate target case(s) first.
2. Validate broader corpus second.
3. Stabilize only when both are acceptable.

### Pattern 3: Fix Upstream, Not Downstream

When output is wrong:
1. Trace to producer stage.
2. Fix producer contract/logic.
3. Re-run downstream checks to confirm propagation.

### Pattern 4: Baseline Before Edit

For risky work:
1. Pin baseline manifest.
2. Change code/docs.
3. Compare after-state against baseline.
