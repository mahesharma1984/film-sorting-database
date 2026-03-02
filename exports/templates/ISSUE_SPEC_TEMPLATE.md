# Issue Specification Standard

<!--
  TEMPLATE: Mandatory template for all issue specs.
  Replace all [PLACEHOLDER] values with your project specifics.
  Delete anti-pattern examples that don't apply to your project.
  This template ensures every implementation spec has the five dimensions
  that predict first-attempt success.
-->

**Purpose:** Ensure every issue spec provides enough detail for an implementer to execute the entire change without reading code or asking clarifying questions.

---

## Why This Template Exists

Issue specs fail when they're missing one or more of these five dimensions:

1. **Execution ordering** — which files to change, in what order
2. **Affected handoffs** — which component boundaries are impacted
3. **Measurement story** — before/after metric targets
4. **Validation commands** — exact commands to verify success
5. **Downstream consumer impact** — what breaks if this component's output changes

Specs that cover all five have high first-attempt success rates. Specs that miss two or more typically spawn follow-up issues.

Additionally, **rollback plans** and **manager-readable summaries** are frequently absent from failed specs.

---

## Document Types

Three document types cover the full lifecycle of an issue:

| Type | When | Purpose |
|---|---|---|
| **Issue Spec** (Type 1) | Before implementation | Complete specification for the implementer |
| **Session Handoff** (Type 2) | Between work sessions | Eliminate re-investigation at session start |
| **Completion Report** (Type 3) | After implementation | Record what changed, measurements, lessons |

---

## TYPE 1: Issue Spec (Pre-Implementation)

Every section below is **mandatory** unless marked (optional). The implementer should be able to execute the entire change from this document alone.

---

```markdown
# Issue #NNN: [Title]

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P1-Critical / P2-High / P3-Medium |
| Date Opened | YYYY-MM-DD |
| Component | [Which component/stage/module] |
| Change Type | Bug Fix / Feature / Refactor / Infrastructure |
| Estimated Effort | [hours or days] |
| Blocked By | #NNN (or "None") |
| Blocks | #NNN (or "None") |
| Supersedes | #NNN (or "None") |

---

## 1. Manager Summary

<!-- NON-CODER READABLE. No code references. Answer these four questions: -->

**Problem:** [1-2 sentences describing what's broken or missing]

**Impact if unfixed:** [what degrades, breaks, or is blocked]

**Risk if fixed wrong:** [what could regress — name the specific components or outputs at risk]

**Estimated effort:** [hours/days, with confidence: "~4 hours" or "1-2 days, depends on X"]

---

## 2. Evidence

<!-- Concrete data showing the problem. Output samples, measurements,
     error messages. The manager should be able to see the problem
     from this section alone. -->

### Observation
[What you see in the outputs — describe in plain English]

### Data
[Tables, JSON excerpts, measurement values, error messages]
[Include: which inputs, which checkpoint, which measurement run]

---

## 3. Root Cause Analysis

<!-- Numbered root causes with code references. Trace from symptom to origin.
     Each RC should identify the specific file and function where the
     problem originates. -->

### RC-1: [Description]
**Location:** `path/to/file.py` → `function_name()`
**Mechanism:** [How this code produces the observed symptom]

### RC-2: [Description] (if applicable)
**Location:** `path/to/file.py` → `function_name()`
**Mechanism:** [How this contributes to the problem]

---

## 4. Affected Handoffs

<!-- Which component boundaries does this change cross? This section prevents
     the pattern where a well-specified change breaks an unmentioned
     downstream consumer. -->

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| [Component A → B] | `file.py:function()` | `consumer.py:function()` | Yes/No |

**Gate impact:** [Does this affect any hard gates, validation rules, or thresholds? If no gates are affected, state "No gate impact."]

**Downstream consumers of changed output:**
<!-- List ALL components/tools/scripts that read the output being modified -->
- [consumer 1 — what it reads and why]
- [consumer 2 — what it reads and why]

---

## 5. Proposed Fix

### Fix Description
[What to change and why — 2-3 sentences]

### Execution Order
<!-- Numbered steps. Each step = one atomic change that can be verified
     independently. The implementer will follow these step-by-step.
     Include exact file paths, function names, and what to change. -->

1. **Step 1:** Modify `path/to/file.py` — [describe the change]
   - **What to change:** [specific function/section]
   - **Verify:** `[command to verify this step worked]`

2. **Step 2:** Modify `path/to/other_file.py` — [describe the change]
   - **Depends on:** Step 1
   - **What to change:** [specific function/section]
   - **Verify:** `[command to verify this step worked]`

3. **Step 3:** Update documentation — [which doc, which section]
   - **Verify:** [how to check the doc update is correct]

### Files to Modify
<!-- Complete list. The implementer should not need to discover additional
     files during implementation. -->

| File | Change Type | What Changes |
|---|---|---|
| `path/to/file.py` | Modify | `function_name()` — [description] |
| `path/to/other.py` | Modify | `other_function()` — [description] |
| `docs/[ARCHITECTURE_DOC]` | Update | § [relevant section] |

---

## 6. Scope Boundaries

<!-- Explicitly state what this issue does NOT cover. This prevents
     scope creep from forcing follow-up issues. -->

**In scope:**
- [item 1]
- [item 2]

**NOT in scope:**
- [item 1 — why excluded]
- [item 2 — why excluded]

**Deferred to:** #NNN (if follow-up work is anticipated)

---

## 7. Measurement Story

<!-- Before/after metrics. The manager should be able to verify success
     from measurement output alone, without reading code. -->

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| [KPI or gate] | [current value] | [target value] | `[measurement command]` |

**Recording instruction:** After fix, run:
```bash
[YOUR MEASUREMENT COMMAND]
```
Verify measurement is logged. Compare to pre-fix baseline.

**Pin baseline before implementing:**
```bash
[YOUR BASELINE PINNING COMMAND, or "git tag pre-issue-NNN"]
```

---

## 8. Validation Sequence

<!-- Exact commands to run after implementation, in order. The manager
     should be able to copy-paste these and interpret the results. -->

```bash
# Step 1: Run relevant tests
[YOUR TEST COMMAND]

# Step 2: Validate component boundaries (if applicable)
[YOUR VALIDATION COMMAND]

# Step 3: Measure quality
[YOUR MEASUREMENT COMMAND]

# Step 4: Regression check (if architecture/component change)
[YOUR REGRESSION CHECK COMMAND]
```

**Expected results:**
- Step 1: All tests pass (0 failures)
- Step 2: All gates pass (no errors)
- Step 3: [metric] ≥ [threshold]
- Step 4: No regressions detected

**If any step fails:** Stop. Do not proceed to next steps. Report the failure output.

---

## 9. Rollback Plan

<!-- If the fix breaks something, how to recover. Every implementation
     should have an escape hatch. -->

**Detection:** [How you'd notice the fix is wrong — what output symptom to watch for]

**Recovery:**
```bash
git revert [commit-hash]
# OR specific undo steps if revert is insufficient:
# [step 1]
# [step 2]
```

**Pre-implementation checkpoint:**
```bash
[YOUR BASELINE COMMAND, or "git tag pre-issue-NNN"]
```

---

## 10. Theory & Architecture Grounding

<!-- Which methodology and architecture docs justify this change? This creates
     traceability from code back to first principles. -->

**Methodology basis:**
- `docs/[methodology_doc]` § [section] — [how it applies]

**Architecture reference:**
- `docs/[architecture_doc]` § [section] — [what contract is relevant]

**Related issues:**
- #NNN — [relationship: blocks/blocked-by/supersedes/related-to]

---
```

### Section Checklist (for spec author)

Before marking the spec as ready for implementation, verify:

- [ ] §1 Manager Summary is readable without code knowledge
- [ ] §3 Root causes reference specific files and functions
- [ ] §4 ALL downstream consumers are listed (not just the obvious ones)
- [ ] §5 Execution Order has verify commands for each step
- [ ] §5 Files to Modify is complete (no surprise files during implementation)
- [ ] §6 NOT in scope is populated (prevents scope creep)
- [ ] §7 Measurement Story has concrete before/after numbers
- [ ] §8 Validation Sequence commands are copy-pasteable
- [ ] §9 Baseline is pinned before implementation starts
- [ ] §10 Theory grounding exists (change is justified by documented principles)

---

## TYPE 2: Session Handoff (Between Work Sessions)

Use this when implementation spans multiple sessions. Eliminates the "re-establish context" problem by encoding session state explicitly.

---

```markdown
# Issue #NNN: Session Handoff — [Date]

| Field | Value |
|---|---|
| Branch | `feature/issue-NNN` |
| Last Commit | `[hash]` `[message]` |
| Spec Location | `docs/issues/ISSUE_NNN_*.md` |

## Current State

**Steps completed:** [N] of [total] (from §5 Execution Order)
**Steps remaining:** [list remaining step numbers]
**All verification checks passing:** Yes/No

## What Was Done This Session

1. [Completed Step N] — Verified: [result]
2. [Completed Step N+1] — Verified: [result]

## What's Next (Priority Order)

<!-- Copy directly from §5 Execution Order, starting at the next incomplete step -->

1. [Next step — exact description from spec]
2. [Step after — exact description from spec]

## Uncommitted or In-Progress State

<!-- Any files modified but not committed, any partial work, any
     temporary debugging changes that need to be reverted -->

- [file.py — partial change to function_name(), needs completion]
- [None — all work committed]

## Verification Commands for Next Session

<!-- Run these first in the next session to confirm current state is valid -->

```bash
# Confirm branch and last commit
git log --oneline -1

# Confirm tests still pass
[YOUR TEST COMMAND]

# Confirm current baseline
[YOUR MEASUREMENT COMMAND]
```

## Notes for Next Session

[Any context that would take time to rediscover — edge cases encountered,
 decisions made, things that almost worked but didn't]
```

---

## TYPE 3: Completion Report (Post-Implementation)

Record what changed, verify acceptance criteria, capture lessons for future issues.

---

```markdown
# Issue #NNN: Completion Report

| Field | Value |
|---|---|
| Date Completed | YYYY-MM-DD |
| Branch | `feature/issue-NNN` |
| Commits | `[hash1]`, `[hash2]` |
| Time Taken | [actual hours/days] |
| Spec Accuracy | [How well did the spec predict the actual work? 1-5] |

---

## What Changed

### Files Modified

| File | Change Summary |
|---|---|
| `path/to/file.py` | [what changed] |

### Documentation Updated

| Document | Section Updated |
|---|---|
| `docs/[ARCHITECTURE_DOC]` | § [section] |

---

## Measurement Results

| Metric | Before | After | Status |
|---|---|---|---|
| [KPI] | [value] | [value] | Improved / Stable / Regressed |

---

## Acceptance Criteria Verification

| Criterion (from §8) | Status | Evidence |
|---|---|---|
| Tests pass | PASS/FAIL | [output summary] |
| Validation gates | PASS/FAIL | [gate results] |
| Measurement target met | PASS/FAIL | [metric values] |
| No regressions | PASS/FAIL | [comparison data] |

---

## Lessons Learned

### What Worked
- [things the spec got right]

### What the Spec Missed
- [files that needed changing but weren't listed in §5]
- [handoffs that broke but weren't listed in §4]
- [edge cases not anticipated]

### For Future Issues
- [recommendations for similar changes]

---

## Supersession Updates

<!-- Update any related issues affected by this change -->

- Issue #NNN: [updated status/scope because of this fix]
- `docs/[file]`: [section updated to reflect new behavior]
```

---

## Quick Reference: Which Type When?

```
Starting new work?
├── Write TYPE 1 (Issue Spec) BEFORE implementation
│
├── Implementation spans multiple sessions?
│   └── Write TYPE 2 (Session Handoff) at end of each session
│
└── Implementation complete?
    └── Write TYPE 3 (Completion Report)
```

## Filing Location

- Active issue specs: `docs/issues/ISSUE_NNN_[TITLE].md`
- Session handoffs: `docs/issues/ISSUE_NNN_SESSION_HANDOFF_[DATE].md`
- Completion reports: `docs/issues/ISSUE_NNN_COMPLETION_REPORT.md`
- After completion: move to `docs/archive/issues/`

---

## Anti-Patterns

These patterns cause the most friction in issue-driven development. The template sections that prevent them are noted.

| Anti-Pattern | What Happens | Prevented By |
|---|---|---|
| **Diagnostic-only spec** (strong root cause, no execution plan) | Multiple follow-up issues needed | §5 Execution Order (mandatory) |
| **Oversized scope** (too much for one implementation session) | Forced split mid-implementation | §6 Scope Boundaries + NOT in scope |
| **Missing handoff trace** (change breaks unmentioned downstream) | Regression in untested component | §4 Affected Handoffs + downstream consumer list |
| **No validation commands** (implementer doesn't know how to verify) | Change ships without verification | §8 Validation Sequence (copy-pasteable) |
| **No measurement baseline** (can't tell if fix helped or hurt) | No evidence of improvement | §7 Measurement Story + §9 pin baseline |
| **Implicit audience** (spec assumes coder knowledge) | Manager can't verify success | §1 Manager Summary (non-coder readable) |
| **No rollback plan** (fix goes wrong, no recovery path) | Stuck with broken state | §9 Rollback Plan |
| **Orphaned supersession** (old issue not updated when superseded) | Conflicting specs coexist | Header field: Supersedes + §10 Related issues |
