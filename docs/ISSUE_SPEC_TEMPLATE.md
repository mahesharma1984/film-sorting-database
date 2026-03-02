# Issue Specification Standard

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
| Component | Parser / API Enrichment / Lookup / Corpus / Satellite / Core / Popcorn / Move / Audit |
| Change Type | Bug Fix / Feature / Refactor / Infrastructure |
| Estimated Effort | [hours or days] |
| Blocked By | #NNN (or "None") |
| Blocks | #NNN (or "None") |
| Supersedes | #NNN (or "None") |

---

## 1. Manager Summary

**Problem:** [1-2 sentences describing what's broken or missing]

**Impact if unfixed:** [what degrades, breaks, or is blocked — e.g. "Films from X route to wrong tier" or "Classification rate stays at N%"]

**Risk if fixed wrong:** [what could regress — e.g. "Satellite routing for HK Action films", "SORTING_DATABASE lookup misses"]

**Estimated effort:** [hours/days, with confidence: "~4 hours" or "1-2 days, depends on X"]

---

## 2. Evidence

### Observation
[What you see in the outputs — describe in plain English using manifest reason codes, reaudit verdicts, etc.]

### Data
[Tables, JSON excerpts, measurement values, error messages]
[Include: which films triggered the issue, which reason code, which reaudit verdict]

---

## 3. Root Cause Analysis

### RC-1: [Description]
**Location:** `path/to/file.py` → `function_name()`
**Mechanism:** [How this code produces the observed symptom]

### RC-2: [Description] (if applicable)
**Location:** `path/to/file.py` → `function_name()`
**Mechanism:** [How this contributes to the problem]

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| [e.g. Parser → Lookup] | `lib/parser.py:_extract_year()` | `lib/lookup.py:find()` | Yes/No |
| [e.g. Satellite → classify.py] | `lib/satellite.py:classify()` | `classify.py:_route_film()` | Yes/No |

**Gate impact:** [Does this affect any hard gates, validation rules, or thresholds? e.g. "Changes Satellite decade bounds — reaudit baseline will shift"]

**Downstream consumers of changed output:**
- [consumer 1 — what it reads and why, e.g. "move.py reads source_path from manifest — relative path required"]
- [consumer 2]

---

## 5. Proposed Fix

### Fix Description
[What to change and why — 2-3 sentences]

### Execution Order

1. **Step 1:** Modify `path/to/file.py` — [describe the change]
   - **What to change:** [specific function/section]
   - **Verify:** `pytest tests/test_relevant.py -v`

2. **Step 2:** Modify `path/to/other_file.py` — [describe the change]
   - **Depends on:** Step 1
   - **What to change:** [specific function/section]
   - **Verify:** `python classify.py /path/to/test_films`

3. **Step 3:** Update SORTING_DATABASE.md or constants.py — [if applicable]
   - **Verify:** `python classify.py /path/to/test_films` — check reason code for affected film

4. **Step 4:** Update documentation — [which doc, which section]
   - **Verify:** grep for outdated references

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `lib/parser.py` | Modify | `function_name()` — [description] |
| `lib/constants.py` | Modify | `CONSTANT_NAME` — [description] |
| `docs/[RELEVANT_DOC]` | Update | § [relevant section] |

---

## 6. Scope Boundaries

**In scope:**
- [item 1]
- [item 2]

**NOT in scope:**
- [item 1 — why excluded]
- [item 2 — why excluded]

**Deferred to:** #NNN (if follow-up work is anticipated)

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Reaudit confirmed | [N / M] | [N+k / M] | `python scripts/reaudit.py` |
| Classification rate | [N%] | [N+k%] | `python classify.py <source>` |
| [Specific reason code count] | [N] | [N-k] | check manifest |

**Pin baseline before implementing:**
```bash
git tag pre-issue-NNN
python scripts/reaudit.py > output/pre-NNN-reaudit.txt
```

---

## 8. Validation Sequence

```bash
# Step 1: Run full test suite
pytest tests/ -v

# Step 2: Validate handoffs
python scripts/validate_handoffs.py

# Step 3: Classify test films (with known expected destinations)
python classify.py /path/to/test_films

# Step 4: Regression check — reaudit organised library
python audit.py && python scripts/reaudit.py
```

**Expected results:**
- Step 1: All tests pass (0 failures, 1 skipped allowed)
- Step 2: All gates pass (no errors)
- Step 3: Target film routes to correct tier with correct reason code
- Step 4: Confirmed count ≥ pre-fix baseline; no new wrong_tier/wrong_category

**If any step fails:** Stop. Do not proceed. Report the failure output.

---

## 9. Rollback Plan

**Detection:** [How you'd notice the fix is wrong — e.g. "Reaudit confirmed count drops below N", "HK Action films misroute"]

**Recovery:**
```bash
git revert [commit-hash]
# If cache was modified:
python scripts/invalidate_null_cache.py conservative
```

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-NNN
```

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `CLAUDE.md` § Rule [N] — [how it applies]

**Architecture reference:**
- `docs/architecture/VALIDATION_ARCHITECTURE.md` § [section] — [what contract is relevant]
- `docs/architecture/RECURSIVE_CURATION_MODEL.md` § [section] — [if applicable]

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

1. [Next step — exact description from spec]
2. [Step after — exact description from spec]

## Uncommitted or In-Progress State

- [file.py — partial change to function_name(), needs completion]
- [None — all work committed]

## Verification Commands for Next Session

```bash
# Confirm branch and last commit
git log --oneline -1

# Confirm tests still pass
pytest tests/ -v

# Confirm current baseline
python scripts/reaudit.py
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
| `lib/parser.py` | [what changed] |

### Documentation Updated

| Document | Section Updated |
|---|---|
| `docs/[DOC]` | § [section] |

---

## Measurement Results

| Metric | Before | After | Status |
|---|---|---|---|
| Reaudit confirmed | [N / M] | [N+k / M] | Improved / Stable / Regressed |
| Classification rate | [N%] | [N+k%] | Improved / Stable / Regressed |

---

## Acceptance Criteria Verification

| Criterion (from §8) | Status | Evidence |
|---|---|---|
| Tests pass | PASS/FAIL | [output summary] |
| Validation gates | PASS/FAIL | [gate results] |
| Measurement target met | PASS/FAIL | [metric values] |
| No regressions | PASS/FAIL | [reaudit comparison] |

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

- Issue #NNN: [updated status/scope because of this fix]
- `docs/[file]`: [section updated to reflect new behavior]
- `MEMORY.md`: [updated session memory if applicable]
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
