# Skill: Measurement-Driven Development

**Purpose:** Use measurement to drive development decisions across two axes — depth (single-case quality) and breadth (cross-case consistency).
**Addresses:** "Did this change help?" and "Did it break anything else?"

---

## Core Principle

**Development operates on two axes simultaneously.**

```
                     BREADTH (cross-case consistency)
                     ─────────────────────────────────►
                     │
                     │  "Does this change work for
                     │   ALL cases, not just this one?"
                     │
    DEPTH            │  ┌─────┐  ┌─────┐  ┌─────┐
    (single case     │  │Case │  │Case │  │Case │ ...
     quality)        │  │  A  │  │  B  │  │  C  │
                     │  │     │  │     │  │     │
                     ▼  │Score│  │Score│  │Score│
                        │0.84 │  │0.75 │  │0.91 │
                        └─────┘  └─────┘  └─────┘
    "Does this change
     improve THIS case's
     quality?"
```

**The fundamental tension:** A change that fixes Case A might degrade Case B. A change to the scoring formula shifts every score.

---

## The Development Cycle

```
1. IDENTIFY
   │  Metric failure, quality gap, or feature need
   │
   ▼
2. DIAGNOSE
   │  Trace to component (use R/P Split, Pattern-First)
   │
   ▼
3. FIX
   │  Apply appropriate methodology:
   │  - R/P Split for task misallocation
   │  - Pattern-First for causality violations
   │  - Architecture change for structural issues
   │
   ▼
3.5 VALIDATE HANDOFFS (Constraint Gates)
   │  Run handoff validation on modified stages ($0, code-only)
   │  Verify upstream data survives to downstream consumers
   │  If handoff fails → return to step 3 (fix the constraint, not downstream)
   │
   ▼
4. MEASURE DEPTH
   │  Re-measure the target case(s)
   │  Compare: did the targeted metric improve?
   │  Compare: did any other metric regress?
   │
   ▼
5. REBALANCE (if needed)
   │  If new metric added → reweight formula
   │  If new stage added → update downstream contracts
   │  If gate behavior changed → verify gate model
   │
   ▼
6. MEASURE BREADTH
   │  Re-measure across all cases (or representative sample)
   │  Compare: did any case regress?
   │  Identify: case-specific vs universal effect
   │
   ▼
7. STABILIZE
   │  When both axes aligned → declare version stable
   │  Document: what changed, why, metric evidence
   │
   ▼
   (back to 1 for next issue)
```

---

## Boundary-Aware Extension

When your pipeline has an explicit boundary (see System Boundary Theory, Boundary-Aware Measurement skill), scope your measurement to the affected subsystem:

| What Changed | Measure Depth On | Measure Breadth On |
|---|---|---|
| Analysis stage | Analysis metrics only | Analysis cases only |
| Delivery stage | Delivery metrics only | Delivery cases only |
| Boundary contract | Both sides | Full corpus |
| Infrastructure | Both sides | Full corpus |

**Why scope matters:** If only analysis changed, running expensive delivery measurement ($$ API calls) provides no information — the delivery code hasn't changed. Validate the handoff ($0), measure analysis ($), and skip delivery entirely.

For the full boundary-aware measurement protocol, see [Boundary-Aware Measurement](boundary-aware-measurement.md).

---

## Two Development Modes

### Frontier Work (Depth-First)

Pushing what the system can do at its best. Produces **capability leaps** — qualitative jumps where the system captures something it previously couldn't.

**Characteristics:**
- High-risk, high-reward
- Targets a single case or small set
- Often requires architectural change
- Success is a capability that didn't exist before

**When to use:**
- A case is missing something obviously important
- A metric has clear headroom (most cases score low — high leverage)
- Exploring whether a new approach is viable

### Consistency Work (Breadth-First)

Making sure what already works keeps working across all cases. This is **regression prevention** and **baseline establishment**.

**Characteristics:**
- Lower-risk, systematic
- Targets the whole corpus or representative sample
- Typically follows a frontier change
- Success is stability: no case regressed

**When to use:**
- After a frontier change, to verify no regressions
- Before declaring a version stable
- When expanding the corpus (new cases need baselines)

**The ratio shifts over time.** Early development is mostly frontier (build capability). Mature development is mostly consistency (prevent regressions).

---

## What to Measure

### "Did this change help?" (Depth)

For the specific case(s) targeted:
- Before/after composite score
- Before/after for the specific metric the change targeted
- Sanity checks (e.g., output count — did extraction break?)

### "Did this change break anything?" (Breadth)

For all other cases:
- Score delta — did any case's score drop?
- Gate status change — did any passing case now fail?
- Tier change — did any case move from STRONG to WEAK?

### "Is the system stable?" (Alignment)

Across everything:
- Score distribution — clustered (good) or bimodal (bad)?
- Universal patterns — any metrics universally passing or failing?
- Metric correlations — do related metrics move together?

### "What should I work on next?" (Prioritization)

- Weakest case — which has the lowest score?
- Most common failure — which metric fails most often?
- Biggest leverage — which metric improvement would move the most cases up a tier?

---

## Measurement History

### Minimum Viable History

Each measurement run should record:

| Field | Why |
|---|---|
| `case_name` | What was measured |
| `version` | What produced it — key for before/after |
| `measured_at` | Chronological ordering |
| `composite_score` | Overall quality signal |
| `key_metrics` | Individual metrics for diagnosis |
| `output_count` | Sanity check for extraction regressions |

**Append-only:** Each run adds a row. No overwrites. Detailed reports remain the detail layer.

### Queries This Enables

```
# Depth history (single case over time)
SELECT * WHERE case='X' ORDER BY measured_at

# Breadth snapshot (all cases at one version)
SELECT * WHERE version='2.0' ORDER BY score DESC

# Regression detection (after a change)
SELECT case, score WHERE latest.score < previous.score
```

---

## Connection to Software Engineering Theory

| Theory | How It Applies |
|---|---|
| **Build-Measure-Learn** (Lean) | The MDD cycle is structurally identical |
| **Shift-Left Quality** (DevOps) | Catch defects earlier where fixes are cheaper |
| **Design by Contract** (Meyer) | Each stage declares preconditions, postconditions, invariants |
| **Property-Based Testing** (QuickCheck) | Define invariants that must hold across all valid inputs |
| **Strangler-Fig Refactoring** (Fowler) | Insert validation layers incrementally |
| **Observability First** (distributed systems) | Instrument the process, not just the output |
| **TOC / Kanban Gates** (manufacturing) | Find the binding constraint; validate handoffs before expensive stages |

### Cost-Ordering Principle

Not all feedback is equally expensive. Seek cheap feedback before costly feedback:

| Feedback Type | Cost | Speed | What It Catches |
|---|---|---|---|
| Contract validation | $0 (code only) | Seconds | Process violations |
| Basic quality checks | $0 (code only) | Seconds | Data corruption |
| Full measurement | $$ (may need API) | Minutes | Quality gaps |
| Manual qualitative review | Time-intensive | Hours | Insight gaps |

**Principle:** Run cheap checks first. Only proceed to expensive measurement when contracts pass.

---

## When MDD Cycles Fail

Not all interventions improve metrics. A cycle can fail because:

1. **Infrastructure was correct but the data doesn't support the measurement** — the fix works mechanically but the input case lacks the patterns being measured
2. **The fix is text/case-specific** — works for one case, not others
3. **The metric is wrong** — measuring the wrong thing

### Stopping Criteria

When a depth cycle fails, check:
1. Infrastructure validated? (mechanism works)
2. Intervention works partially? (at least one metric improved)
3. Input instability? (same inputs produce different outputs)
4. Input characteristics mismatch? (the case doesn't suit this approach)
5. Corpus outlier? (this case is unusual)

**When 3+ criteria met → accept limitation, pivot to breadth work.**

### Pivot Options

| Option | When |
|---|---|
| Pivot to breadth-first | Target metrics with universal weakness across all cases |
| Target different metric | Current metric may not be improvable for this case |
| Target different case | Validate the approach works where conditions are right |

---

## Quick Reference

### Starting a Change
1. Identify what's failing and why
2. Diagnose root cause (R/P Split, Pattern-First)
3. Measure baseline before touching anything

### After Making a Change
1. Validate handoffs ($0 — did data survive stage boundaries?)
2. Measure depth (did target improve? Scope to affected subsystem if boundary exists)
3. Rebalance if needed
4. Measure breadth (did anything else regress?)
5. Stabilize when both axes aligned

### Declaring Stability
- Composite score stable or improving for 80%+ of cases
- No case moved from passing to failing
- Changes documented with metric evidence
