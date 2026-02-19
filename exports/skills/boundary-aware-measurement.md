# Skill: Boundary-Aware Measurement (Scoped Quality Across System Boundaries)

**Purpose:** Measure subsystems independently with cost-ordered validation gates, so you spend resources measuring the right thing.
**Addresses:** Monolithic measurement that wastes resources, mixing analysis and output metrics, inability to isolate where quality problems originate.

---

## Core Principle

**Identify the boundary. Measure each side independently. Validate handoffs before running expensive measurement.**

Without boundary-aware measurement:
- Every change requires a full pipeline run to test, even when only one subsystem changed
- Expensive API calls run on corrupt analysis models (wasted money)
- When output quality drops, you can't tell whether analysis or delivery is the cause
- Measurement history mixes metrics from different subsystems, making trends meaningless

---

## The Boundary Measurement Protocol

### Step 1: Identify Your System Boundary

Find where the pipeline switches from "understanding" to "producing":

```
Stage 1 ──► Stage 2 ──► Stage 3 ──► Stage 4 ──► Stage 5 ──► Stage 6
         analysis (cheap, code-only)      │      delivery (expensive, API)
                                          │
                                    BOUNDARY
                                  (purpose changes)
```

**Signals that a boundary exists:**
- Cost cliff (stages after are 10x+ more expensive)
- Purpose shift (analysis → delivery)
- Reuse potential (analysis output serves multiple applications)
- Change independence (changes on one side rarely affect the other)

If no clear boundary exists, this skill doesn't apply — use standard Measurement-Driven Development instead.

### Step 2: Define Metrics for Each Side

**Analysis metrics** (measured on the internal model):

| Metric Type | What It Measures | Example |
|---|---|---|
| Completeness | Does the model capture what's in the data? | "Did analysis identify all relevant patterns?" |
| Accuracy | Are classifications correct? | "Are entities assigned to correct categories?" |
| Consistency | Do similar inputs produce similar models? | "Does the same input produce the same model?" |
| Survival | Did upstream data survive stage boundaries? | "Did ≥70% of high-confidence observations survive?" |

**Delivery metrics** (measured on the output):

| Metric Type | What It Measures | Example |
|---|---|---|
| Fidelity | Does the output represent the model correctly? | "Are model patterns reflected in output?" |
| Extraction quality | Are located evidence items correctly extracted? | "Are quotes accurate and properly attributed?" |
| Coverage | Does the output include what the model provides? | "Did extraction attempt all model patterns?" |
| Format quality | Is the output well-structured? | "Is the output valid, well-formatted?" |

**Key rule:** Analysis metrics should NOT depend on delivery format. Delivery metrics SHOULD depend on analysis completeness.

### Step 3: Validate Handoff (Cheapest Check First)

Before measuring either subsystem, validate the handoff at the boundary:

```python
def validate_boundary(analysis_output, delivery_input):
    """$0 check — runs before any expensive measurement."""
    checks = {
        'schema': analysis_output conforms to boundary contract,
        'survival': observation survival rate >= threshold,
        'completeness': required fields present,
    }
    return all(checks.values()), checks
```

**If handoff validation fails:** Don't measure anything else. Fix the handoff first. All downstream metrics are measuring corruption.

### Step 4: Measure the Side That Changed

After a change, only measure the affected subsystem:

| What Changed | What to Measure | What to Skip |
|---|---|---|
| Analysis stage modified | Analysis metrics + handoff validation | Delivery metrics (reuse previous) |
| Delivery stage modified | Delivery metrics | Analysis metrics (reuse previous) |
| Boundary contract changed | Both sides + handoff validation | Nothing — full measurement needed |
| Infrastructure change | Both sides + handoff validation | Nothing — full measurement needed |

**The savings:** If only analysis changed, skip expensive delivery measurement entirely. Validate the handoff ($0), measure analysis ($), done. Only run delivery measurement ($$) when delivery actually changed.

### Step 5: Full Pipeline Measurement

Run full end-to-end measurement only when:
- Both sides pass independently
- You're declaring a version stable
- You're establishing a new baseline
- A boundary contract changed

---

## Cost-Ordering Rule

The most practical part of this skill — always run cheapest checks first:

```
TIER 0: $0 (seconds)
  ├── Handoff validation (checkpoint file inspection)
  ├── Schema contract checks (field presence, types)
  └── Basic sanity checks (output count, structure)
        │
        ↓ must pass before proceeding
        │
TIER 1: $ (seconds-minutes)
  ├── Analysis metrics (code-based model inspection)
  └── Unit tests (deterministic verification)
        │
        ↓ should pass
        │
TIER 2: $$ (minutes)
  ├── Delivery metrics (may require API calls)
  └── Integration tests (cross-stage verification)
        │
        ↓ should pass
        │
TIER 3: $$$ (minutes-hours)
  ├── Full end-to-end measurement
  └── Manual qualitative review
```

**Rule:** Never advance to a higher tier when a lower tier has failures. A $0 check that reveals corrupt data prevents $$ in wasted API calls.

---

## Integration with the MDD Cycle

Boundary-aware measurement extends the Measurement-Driven Development cycle by adding Step 3.5:

```
1. IDENTIFY (metric failure, quality gap)
2. DIAGNOSE (trace to component)
3. FIX (apply change)
   ↓
3.5 VALIDATE HANDOFFS ($0)
   Run handoff validation on modified stages
   Verify upstream data survives to downstream
   If handoff fails → return to step 3
   ↓
4. MEASURE DEPTH (scope to affected subsystem)
5. REBALANCE (if needed)
6. MEASURE BREADTH (scope to affected subsystem first, then full)
7. STABILIZE
```

**Step 3.5 is the highest-leverage addition:** It's the cheapest step ($0) that prevents the most expensive waste (running delivery measurement on corrupt analysis).

---

## Measurement History Scoping

When recording measurement history, tag each record with its scope:

```json
{
  "case_name": "Project X",
  "version": "3.1",
  "measured_at": "2026-02-19T10:30:00Z",
  "scope": "analysis",
  "metrics": {
    "completeness": 0.92,
    "accuracy": 0.88,
    "survival_rate": 0.85
  }
}
```

**Why scope matters in history:**
- Trend analysis per subsystem: "Analysis accuracy improved from 0.82 to 0.88 over 3 versions"
- Regression scoping: "Delivery quality dropped, but analysis is stable — problem is in delivery"
- Cost tracking: "We ran full measurement 3 times this sprint; boundary-scoped measurement 12 times — saved ~$40"

---

## When to Apply

| Situation | Apply Boundary-Aware Measurement? |
|---|---|
| Pipeline has ≥4 stages with a clear midpoint | Yes |
| Some stages cost $$ (API calls, human review) | Yes — cost-ordering saves money |
| You need to debug output quality drops | Yes — scope narrows the search |
| Pipeline has 2-3 stages, all cheap | No — just run everything |
| All stages have similar cost | Probably no — cost-ordering provides little benefit |
| You can't articulate where the boundary is | No — use standard MDD until a boundary emerges |

---

## Diagnostic: Is This a Boundary Problem?

| Symptom | Likely Boundary Problem? | What to Check |
|---|---|---|
| Output quality dropped but analysis looks fine | Delivery problem | Measure delivery independently |
| Analysis metrics pass but output is wrong | Handoff problem | Validate boundary contract |
| Everything passes but output feels off | Metric scoping problem | Are analysis metrics measuring the right thing? |
| Expensive stages keep running on bad data | Missing cost-ordering | Add $0 handoff validation before $$ stages |
| Can't tell where quality degraded | Missing boundary | Define the boundary and scope metrics |

---

## Integration with Other Skills

| Skill | How Boundary-Aware Measurement Connects |
|---|---|
| **Measurement-Driven** | Extends MDD with step 3.5 (handoff validation) and subsystem scoping |
| **Constraint Gates** | Handoff validation IS a constraint gate at the boundary |
| **Failure Gates** | Handoff failures at the boundary = hard gates (stop before wasting money downstream) |
| **Domain Grounding** | Analysis metrics can check taxonomy consistency across stages |
| **R/P Split** | The boundary often aligns with the R/P split: analysis = REASONING, delivery = PRECISION |

---

## Checklist

When setting up boundary-aware measurement:
- [ ] Identified system boundary (where does purpose shift from analysis to delivery?)
- [ ] Defined boundary contract (what crosses, what doesn't)
- [ ] Defined analysis metrics (completeness, accuracy, consistency, survival)
- [ ] Defined delivery metrics (fidelity, extraction quality, coverage, format)
- [ ] Added handoff validation ($0 checkpoint inspection)
- [ ] Established cost-ordering (cheapest checks gate expensive measurement)
- [ ] Tagged measurement history records with scope

When debugging a quality problem:
- [ ] Validated handoff at boundary ($0)
- [ ] Determined which subsystem is affected (analysis or delivery)
- [ ] Measured only the affected subsystem
- [ ] Fixed the root cause in the correct subsystem
- [ ] Ran full measurement only after both sides pass independently
