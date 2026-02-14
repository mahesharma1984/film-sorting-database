# Workflow Registry

<!--
  TEMPLATE: Define atomic workflows (single operations) and composed workflows (multi-step).
  Replace [PLACEHOLDER] values. Add your project-specific workflows.
  Goal: Named, repeatable procedures that anyone can follow.
-->

**Purpose:** Named, repeatable procedures for common operations.

---

## Section 1: Atomic Workflows

Atomic workflows are single operations. They can be composed into larger procedures.

<!--
  Define your atomic workflows using this pattern:

  ### WF-[CATEGORY]-[NAME]: [Description]
  **When:** [When to use this]
  **Command:** [Exact command to run]
  **Output:** [What it produces]
  **Verify:** [How to check it worked]
-->

### WF-BUILD-RUN: Run the pipeline

**When:** Processing new input or re-running after changes
**Command:**
```bash
[YOUR PIPELINE COMMAND]
```
**Output:** [DESCRIBE OUTPUT]
**Verify:** [HOW TO VERIFY]

### WF-TEST-UNIT: Run unit tests

**When:** After code changes
**Command:**
```bash
[YOUR TEST COMMAND]
```
**Output:** Test results
**Verify:** All tests pass

### WF-MEASURE-SINGLE: Measure single case quality

**When:** After pipeline run, to assess output quality
**Command:**
```bash
[YOUR MEASUREMENT COMMAND]
```
**Output:** Quality report
**Verify:** Scores are within expected ranges

### WF-BACKUP-STATE: Backup current state

**When:** Before risky changes
**Command:**
```bash
[YOUR BACKUP COMMAND]
```
**Output:** Backup files in [LOCATION]
**Verify:** Backup files exist and are non-empty

<!-- ADD MORE ATOMIC WORKFLOWS -->

---

## Section 2: Composed Workflows

Composed workflows combine atomic workflows into multi-step procedures.

### CW-CHANGE-VALIDATE: Make and validate a change

**When:** Making any pipeline change
**Steps:**
1. `WF-BACKUP-STATE` — Backup current state
2. `WF-MEASURE-SINGLE` — Baseline measurement (before)
3. Make the change
4. `WF-TEST-UNIT` — Run tests
5. `WF-BUILD-RUN` — Re-run pipeline
6. `WF-MEASURE-SINGLE` — Compare measurement (after)
7. Compare before/after — did it improve?

### CW-FIX-REGRESSION: Fix a quality regression

**When:** Quality dropped after a change
**Steps:**
1. Identify what changed (git log)
2. `WF-MEASURE-SINGLE` — Confirm regression with measurement
3. Diagnose root cause (see DEBUG_RUNBOOK.md)
4. Apply fix
5. `WF-MEASURE-SINGLE` — Verify fix (depth)
6. `WF-MEASURE-SINGLE` on other cases — Check no new regressions (breadth)

### CW-ROLLBACK: Emergency rollback

**When:** Change caused serious regression, need to revert fast
**Steps:**
1. `git log --oneline -5` — Identify the breaking commit
2. `git revert [commit]` — Revert the change
3. `WF-BUILD-RUN` — Re-run pipeline
4. `WF-MEASURE-SINGLE` — Verify quality restored

<!-- ADD MORE COMPOSED WORKFLOWS -->

---

## Section 3: Cross-Cutting Patterns

Patterns that apply across multiple workflows.

### Pattern 1: Depth-Then-Breadth

After any change:
1. Measure the target case (depth) — did it improve?
2. Measure other cases (breadth) — did anything regress?
3. Only stabilize when both axes are aligned

### Pattern 2: Fix Upstream, Not Downstream

When output is wrong:
1. Trace to the component that produces it
2. Fix that component, not downstream consumers
3. Re-run downstream to verify the fix propagated

### Pattern 3: Level 0 Gates Everything

Before measuring quality:
1. Verify data integrity (Level 0)
2. Only proceed to quality metrics if Level 0 passes
3. If Level 0 fails, fix data integrity first

### Pattern 4: Pin Baseline Before Changes

Before making risky changes:
1. Measure and record current state
2. Pin/tag the current version
3. Make changes
4. Compare against pinned baseline

<!-- ADD MORE CROSS-CUTTING PATTERNS -->
