# Debug Runbook

<!--
  TEMPLATE: Map symptoms to diagnoses to actions.
  Replace [PLACEHOLDER] values. Add your project-specific symptoms.
  Goal: Any developer can diagnose common issues in <10 minutes.
-->

**Purpose:** Triage → Diagnosis → Action mapping for common failures.

---

## Triage Order

1. **Identify the symptom** — What's actually wrong? (Use symptom table below)
2. **Trace to component** — Which stage/module produces the bad output?
3. **Diagnose root cause** — Why is it producing bad output?
4. **Fix upstream** — Fix the root cause, not the symptoms downstream

**Key principle:** Fix upstream, not downstream. If Stage 3 produces bad output because Stage 1's input was wrong, fix Stage 1.

---

## Symptom Table

| # | Symptom | Quick Check | Likely Cause | Fix |
|---|---|---|---|---|
| 1 | [SYMPTOM] | [COMMAND TO CHECK] | [ROOT CAUSE] | [ACTION] |
| 2 | [SYMPTOM] | [COMMAND TO CHECK] | [ROOT CAUSE] | [ACTION] |
| 3 | [SYMPTOM] | [COMMAND TO CHECK] | [ROOT CAUSE] | [ACTION] |

<!--
  EXAMPLE SYMPTOMS (replace with yours):

  | 1 | Output is empty | `wc -l output.json` | Input file missing or malformed | Check input exists and passes validation |
  | 2 | Scores dropped | `diff prev_report.json new_report.json` | Recent code change broke contract | Git bisect to find breaking commit |
  | 3 | Stage N crashes | Check error log | Missing dependency from Stage N-1 | Re-run Stage N-1, verify checkpoint |
  | 4 | Slow performance | `time python run.py` | API rate limiting or large input | Check API logs, consider batching |
  | 5 | Invalid output format | `python -m json.tool output.json` | Schema changed without updating generator | Align generator with current schema |
-->

---

## Diagnostic Procedures

### Procedure 1: Output Quality Investigation

```
1. What metric/score dropped?
   → Check measurement report or output comparison

2. Which component produces this metric?
   → Trace through pipeline stages

3. What changed since it last worked?
   → git log --oneline -10
   → git diff HEAD~5..HEAD -- [relevant files]

4. Is it a task allocation issue (R/P Split)?
   → Is a precision task assigned to the LLM?
   → Is a reasoning task handled by inflexible code?

5. Is it a dependency issue (Pattern-First)?
   → Is a downstream stage depending on upstream data that changed?
   → Are stage boundaries still clean?
```

### Procedure 2: Pipeline Failure Investigation

```
1. Which stage failed?
   → Check error output, last successful checkpoint

2. Is the input valid?
   → Validate input against stage contract (expected fields, format)

3. Is the dependency present?
   → Check that prior stage checkpoint exists and is valid

4. Is it a hard gate or soft gate failure?
   → Hard gate: Fix the violation
   → Soft gate: Assess if output is still acceptable
```

### Procedure 3: Regression Investigation

```
1. What was the last known good state?
   → Check measurement history or recent commits

2. What changed between good and bad?
   → git log, config changes, data changes

3. Is the regression universal or case-specific?
   → Run across multiple cases to check breadth

4. Can we roll back?
   → If recent: git revert
   → If not: fix forward using diagnosis
```

---

## Escalation Rules

1. **Level 0 failure** (data integrity) → Stop everything, fix immediately
2. **Hard gate failure** → Fix before proceeding
3. **Soft gate failure** → Assess impact, fix if quality unacceptable
4. **Accumulated soft failures** → Investigate systemic cause

---

## Recovery Templates

### Minimal Recovery: Re-run from checkpoint

```bash
# [YOUR COMMAND TO RE-RUN FROM SPECIFIC STAGE]
# Example: python run_pipeline.py --start-from stage3
```

### Full Recovery: Clean re-run

```bash
# [YOUR COMMAND TO DO A CLEAN RUN]
# Example: python run_pipeline.py --clean
```

### Rollback: Restore previous output

```bash
# [YOUR COMMAND TO RESTORE FROM BACKUP]
# Example: cp backups/last_good_output.json output.json
```
