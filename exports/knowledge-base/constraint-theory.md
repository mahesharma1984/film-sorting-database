# Constraint Theory: Why Fixing the Bottleneck Beats Fixing the Symptoms

**Read this before:** Constraint Gates skill
**Core question:** When a multi-stage system underperforms, how do you find *what* to fix — and how do you stop fixing the wrong thing?

---

## The Common Assumption

Most developers optimize wherever they see a problem. If Stage 5 produces poor output, they improve Stage 5. If a metric drops, they tweak the component the metric measures. The default mental model is:

1. **Local optimization:** "Fix the stage that produces bad output"
2. **Push-forward thinking:** "Each stage does its job and hands off to the next"
3. **Additive improvement:** "More validation downstream means better quality"

In multi-stage pipelines — especially those involving AI — all three assumptions lead to wasted effort. The fix is often several stages away from where the symptom appears.

---

## The Failure That Reveals the Truth

A pipeline detects patterns in Stage 3 with high confidence. Stage 4 maps those patterns to downstream work items using a category-based lookup table. Stage 5 does expensive API-driven extraction based on whatever Stage 4 provides.

The team notices Stage 5 extracts the wrong items. They spend weeks improving Stage 5's prompts, adding heuristics, tuning parameters. Results improve slightly but remain fundamentally wrong.

Eventually someone traces the data flow and discovers: **Stage 4's lookup table silently discards the high-confidence detections from Stage 3.** Stage 5 was never given the right inputs. No amount of Stage 5 optimization could fix this — the constraint was upstream.

**Three failures compounded:**
1. **Wrong optimization target** — improving Stage 5 when the defect was in Stage 4
2. **Silent data loss** — Stage 4 discarded observations without reporting it
3. **Push-forward flow** — each stage pushed output forward unconditionally, with no inspection at boundaries

The team spent $50+ on Stage 5 API calls extracting the wrong things, because nobody validated the handoff between stages 3 and 4.

---

## The Mental Model: Theory of Constraints + Kanban

Two manufacturing theories, developed independently, combine to address this problem.

### Theory of Constraints (TOC)

From Eliyahu Goldratt's *The Goal* (1984): **every system has exactly one binding constraint that limits throughput.** Optimizing anything other than the constraint is waste — it just creates inventory piling up in front of the bottleneck.

The TOC protocol:

```
1. IDENTIFY the constraint
   "Where is value being destroyed?"

2. EXPLOIT the constraint
   "Maximize throughput at this point — squeeze every bit of
    value from the current setup."

3. SUBORDINATE everything else
   "Don't let upstream produce more than the constraint can
    process. Don't optimize downstream until the constraint
    is resolved."

4. ELEVATE the constraint
   "Invest to remove the constraint entirely."

5. REPEAT
   "The constraint has moved. Find the new one."
```

**The key insight:** Before optimizing *anything*, identify which single point in the system is destroying the most value. Fix that first. Everything else waits.

### Kanban (Pull-Based Quality Gates)

From Taiichi Ohno's *Toyota Production System* (1988): **downstream stations signal readiness before upstream stations push work.** Three rules:

1. **Visualize flow** — make every stage's input/output visible
2. **Limit Work In Progress (WIP)** — don't start new work until the previous item has been pulled downstream
3. **Stop-the-line on defect** (the *andon cord*) — when a quality problem is detected, halt production rather than pass defective work forward

**The key insight:** Push systems hide defects because each station just passes output forward regardless of quality. Pull systems expose defects because the downstream station refuses to accept defective input.

### How They Combine

**TOC tells you WHERE the constraint is.** Kanban tells you HOW to protect it.

```
TOC: "The constraint is the Stage 3→4 handoff"
     (value is destroyed here)
         │
         ▼
Kanban: "Add a quality gate at this boundary"
        (inspect output before the next stage pulls it)
         │
         ▼
Combined: "Stage 4 does not run until Stage 3's output
           passes the handoff gate"
```

---

## The Principle: Fix the Constraint, Not the Symptoms

### Principle 1: Identify Before You Optimize

Before improving any stage, trace the data flow and find where value is being destroyed:

```
Stage 1 → [handoff] → Stage 2 → [handoff] → Stage 3
                          ↑
                     Does value survive
                     this handoff?
```

If the answer is "no" at any handoff, fixing downstream stages is waste. **The constraint is the first handoff where value is destroyed.**

### Principle 2: Subordinate Downstream to Upstream

Don't run expensive downstream stages until upstream handoffs pass. In pipeline terms:

```
WRONG:
  Stage 3 runs → pushes output → Stage 4 runs → pushes output → Stage 5 runs ($$)
  (even if Stage 3→4 handoff lost critical data)

RIGHT:
  Stage 3 runs → GATE validates handoff → passes? → Stage 4 runs → ...
                                        → fails?  → STOP. Fix Stage 3 or the handoff.
```

**The cost ordering:** Handoff validation is $0 (code only, reads checkpoint files). Stage 5 API calls cost $2-5 per run. Running validation before extraction is always cheaper than discovering bad data after extraction.

### Principle 3: Quality Gates at Every Boundary

Every stage boundary should have an explicit quality gate:

```
Stage N → [checkpoint] → GATE → [pass/fail] → Stage N+1
              │                      │
              │                      └─ fail: stop, report what was lost
              └─ inspects checkpoint on disk (external, non-invasive)
```

Gates are **external observers** — they read checkpoint files, they don't modify pipeline internals. This keeps the pipeline clean and the validation auditable.

### Principle 4: Stop the Line, Don't Patch Around

When a gate fails, the correct response is to stop and fix the constraint — not to add workarounds downstream:

```
WRONG:
  Gate fails at Stage 3→4 handoff
  → "Add heuristics to Stage 5 to compensate"
  (patches the symptom, hides the root cause)

RIGHT:
  Gate fails at Stage 3→4 handoff
  → "Fix Stage 4's mapping so it preserves Stage 3's observations"
  (fixes the constraint, removes the root cause)
```

**This is the andon cord principle:** stop the line, fix the defect at the station that introduced it, then resume.

---

## Pull vs Push: Recognizing the Pattern

### Signs Your Pipeline Is Push-Based (Fragile)

- Stages run unconditionally — each stage pushes output regardless of quality
- No inspection at boundaries — you discover problems only at the final output
- Expensive stages run even when upstream data is corrupt
- Fixing late stages doesn't improve results (because the defect is upstream)
- Quality metrics at the end mask process failures in the middle

### Signs Your Pipeline Is Pull-Based (Resilient)

- Each stage's output is inspected before the next stage consumes it
- Expensive stages only run when upstream data passes quality gates
- When a metric fails, you can trace it to the specific handoff that introduced the defect
- Stop-the-line mechanism exists and is wired to quality gates
- Process health is visible at every boundary, not just at the final output

---

## The Five-Step Application

For any multi-stage system:

### Step 1: Map the Value Flow

Trace what data each stage produces and what the next stage actually needs:

```
Stage A produces: {items detected, confidence, frequency, justification}
Stage B consumes: {item names only}
                   ↑
                   VALUE LOST: confidence, frequency, justification stripped
```

### Step 2: Find the Binding Constraint

The constraint is where the most valuable information is destroyed. Look for:
- Data that gets silently discarded between stages
- Stages that use lookup tables instead of upstream observations
- Handoffs where rich data is flattened to simple lists

### Step 3: Add a Gate at the Constraint

Validate that critical data survives the handoff:

```python
def validate_handoff(upstream_output, downstream_input):
    """Check that high-value observations survive the boundary."""
    upstream_items = {item.name for item in upstream_output if item.confidence == 'HIGH'}
    downstream_items = set(downstream_input.item_names)

    survival_rate = len(upstream_items & downstream_items) / len(upstream_items)

    if survival_rate < 0.50:
        return GateResult(
            passed=False,
            message=f"Only {survival_rate:.0%} of high-confidence items survived handoff"
        )
    return GateResult(passed=True)
```

### Step 4: Wire the Stop Mechanism

Connect the gate to a stop-the-line mechanism:

```python
# Pipeline execution with gate
for stage in pipeline:
    result = stage.run()

    if not handoff_gate(stage.name, result):
        print(f"⛔ Handoff failed after {stage.name}. Stopping.")
        break  # Don't run expensive downstream stages
```

### Step 5: Fix the Root Cause

Once the gate is catching the defect, fix the upstream stage so the gate passes. Then move to the next constraint.

---

## The Observation-Data Axiom

In systems with observation-based inputs — human annotations, sensor readings, high-confidence detections from specialized classifiers — a critical principle applies:

**Observation data is authoritative. Downstream stages may filter, prioritize, or reorder observations — but they must not silently discard them.**

### Why Observations Are Special

Observations differ from computed values. A computed value (e.g., a score, a category assignment) can be recomputed if needed. An observation (e.g., "a human annotator detected X with HIGH confidence") represents captured ground truth. If the observation is silently discarded by a downstream lookup table or category mapping, that ground truth is lost — and no downstream stage can recover it.

### The 50% Survival Rule

When an upstream stage produces HIGH-confidence observations and a downstream stage silently discards more than half of them, the problem is at the handoff, not downstream:

```
Stage 3 detects 20 items with HIGH confidence
Stage 4 maps items through category lookup table
Stage 4 output contains 4 of the 20 items

Survival rate: 20% (below 50% threshold)

WRONG: "Improve Stage 5's extraction"
RIGHT: "Stage 4's lookup table is silently discarding
        80% of high-confidence observations.
        Either fix the lookup table or document why
        these observations should be excluded."
```

**Threshold semantics:**
- **< 50% survival** = ERROR: Stop the pipeline. The handoff is destroying value.
- **50-70% survival** = WARNING: Investigate. Some loss may be justified, but document it.
- **> 70% survival** = HEALTHY: Normal filtering is occurring.

### Pull-Based Validation

Before running expensive downstream stages, validate that observations survived the handoff:

```
$0   Read checkpoint files, check survival rate
      ↓ (must pass ≥50%)
$$   Run expensive downstream stages
      ↓
$$$  Full measurement suite
```

The cheapest check ($0 file inspection) should gate the most expensive stage ($$ API calls). This is cost-ordering applied to observation data: **never spend money processing data that was already corrupted at a handoff.**

### When to Apply the Observation-Data Axiom

| Situation | Apply? |
|---|---|
| Upstream produces human annotations or curated observations | Yes — these can't be recomputed |
| Upstream produces computed scores or derived values | Maybe — if the computation is expensive or the derivation is lossy |
| Downstream uses a lookup table to map/filter upstream output | Yes — lookup tables are the #1 cause of silent observation loss |
| Downstream uses pattern matching to select from upstream output | Maybe — depends on selectivity |
| Loss is intentional and documented | No — documented filtering is not silent discarding |

---

## When to Apply This vs Failure Gates

| Situation | Use This (Constraint Theory) | Use Failure Gates |
|---|---|---|
| Pipeline produces bad output, don't know why | ✅ Trace value flow to find constraint | |
| Know the stage that fails, need to handle it | | ✅ Define hard/soft gates for that stage |
| Expensive stages run on corrupt data | ✅ Add gates at handoffs to stop early | |
| Need failure semantics for a single stage | | ✅ Classify failures as hard/soft |
| Fixing one stage doesn't improve results | ✅ Constraint is elsewhere — trace upstream | |
| Building a new stage | | ✅ Define gates from the start |

**They compose:** Constraint Theory tells you *where* to put gates. Failure Gates tells you *how* to design each gate.

---

## Connection to Other Knowledge Base Concepts

| Concept | Connection to Constraint Theory |
|---|---|
| **Failure Theory** | Constraint Theory is *where* to look; Failure Theory is *what* to do when you find it. Gates at constraints are the highest-leverage application of failure gates. |
| **Causality & Systems** | The constraint is a causality chain: upstream data determines downstream quality. Fix the cause, not the effect. |
| **Measurement Theory** | Measurement tells you something is wrong. Constraint Theory tells you *where* to trace. Always validate handoffs ($0) before running expensive measurements ($$). |
| **Task Design Theory** | Poor task decomposition often creates constraints: when a precision task is given to reasoning (R/P violation), the handoff becomes unreliable. |
| **LLM Capability Model** | LLMs can detect patterns (reasoning task) but shouldn't map them to categories (precision task). R/P violations at stage boundaries create constraints. |
| **Domain Grounding Theory** | Lookup tables that silently discard observations often stem from ungrounded taxonomies — the mapping categories don't match the observation categories because neither is anchored in published theory. |
| **System Boundary Theory** | The binding constraint often hides at the system boundary. Cheap validation at the boundary catches upstream defects before expensive downstream stages run. |

---

## Test Yourself

Before proceeding to the Constraint Gates skill, you should be able to answer:

1. Why is optimizing a downstream stage often wasted effort?
2. What's the difference between a push system and a pull system?
3. What does "subordinate everything to the constraint" mean in practice?
4. Why should handoff validation run before expensive API calls?
5. How do you identify the binding constraint in a multi-stage pipeline?
6. What's the andon cord and why does stopping the line beat patching downstream?

If these feel clear, proceed to [Constraint Gates](../skills/constraint-gates.md).

---

## References

- Goldratt, E. (1984). *The Goal.* — Theory of Constraints: identify, exploit, subordinate, elevate
- Ohno, T. (1988). *Toyota Production System: Beyond Large-Scale Production.* — Kanban, pull-based flow, andon cord
- Womack, J. & Jones, D. (1996). *Lean Thinking.* — Value stream mapping, waste identification
- This repository's Issue #415: Pipeline handoff validation — the case study that motivated this document
