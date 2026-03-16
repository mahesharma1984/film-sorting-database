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

### WF-THEORY-CHECK: Investigate a theory problem

**When:** Classification logic is wrong — wrong tier priority, wrong category routing, wrong decade bounds. The code does something, but the governing principle is incorrect or unenforced.
**Steps:**
1. Identify which `CLAUDE.md` Rule or `docs/theory/` essay governs this behavior.
2. Read the relevant section — does it define the correct behavior?
3. If yes → code drifted from theory. Fix code to match.
4. If no → theory needs updating. Update theory first, then code.
5. Check: is the theory grounded in scholarship? (Domain Grounding — `CLAUDE.md` Rule 4)
**Verify:** Code change references the theory doc that required it.

### WF-ARCH-CHECK: Investigate an architecture problem

**When:** A handoff between pipeline stages is wrong — data lost between stages, wrong format, contract violation.
**Steps:**
1. Find the relevant stage in `docs/architecture/RECURSIVE_CURATION_MODEL.md`.
2. Verify: does the upstream stage output what the contract says?
3. Verify: does the downstream stage read what the contract says?
4. Run `python scripts/validate_handoffs.py` — checks all stage boundaries.
5. If mismatch → fix the stage that violates the contract.
**Verify:** `python scripts/validate_handoffs.py` passes with no contract failures.

### WF-DATA-TRACE: Trace a film through the pipeline

**When:** You need to understand how a specific film (or film type) moves through the classification pipeline — to diagnose a misrouting or understand stage interactions.
**Steps:**
1. Start at the stage where the problem is visible (check `reason` code in manifest).
2. Trace backward: what does this stage consume? From where?
3. Trace forward: what does this stage produce? Who consumes it?
4. Document: reads / produces / ignores (the "ignores" dimension reveals drift).
5. This is a PRECISION task — observe the code deterministically, do not interpret yet.

Key pipeline flow:
```
filename → Normaliser (Stage 0) → Parser → API enrichment → R1 promotion (if needed)
    → [explicit_lookup → corpus_lookup → reference_canon → two-signal → popcorn → user_tag] → Unsorted
                                                               ↑
                                               score_director + score_structure → integrate_signals
```
**Verify:** Every stage boundary is accounted for with a reads/produces/ignores triple.

### WF-DRIFT-AUDIT: Audit a component for upstream drift

**When:** A component hasn't been updated in a while, or a new upstream stage was added. Looking for cases where new data is available but a downstream component ignores it.
**Steps:**
1. Identify the component + the issue/commit it was designed for.
2. Map what it reads, produces, and ignores (`WF-DATA-TRACE`).
3. Check: did any upstream stages add data since this component was designed?
4. Check: does the component consume that new data, or ignore it?
5. If ignoring new upstream data → likely highest-leverage fix.

Common drift patterns in this project:
- New API field added (e.g. keywords) but satellite routing doesn't check it
- New corpus added but reaudit script doesn't check that category
- SORTING_DATABASE entry format changed but lookup parser still uses old format
**Verify:** Component design date matches latest upstream contract that affects it.

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
