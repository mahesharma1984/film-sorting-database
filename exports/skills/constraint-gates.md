# Skill: Constraint Gates (TOC/Kanban Quality Gates for Pipelines)

**Purpose:** Identify the binding constraint in a multi-stage pipeline and add quality gates that prevent defective output from flowing downstream.
**Addresses:** Silent data loss at stage boundaries, wasted API costs on corrupt data, fixing the wrong stage.

---

## Core Principle

**Find the constraint first. Fix the constraint first. Don't run expensive stages on defective data.**

Without constraint gates:
- Upstream defects propagate silently through every downstream stage
- Expensive stages (API calls, compute-heavy processing) run on corrupt input
- Debugging requires tracing through the entire pipeline end-to-end
- Teams optimize the wrong stage because the symptom is far from the cause

---

## The Constraint Protocol

### Step 1: Map Value Flow

For each stage boundary, document what data is produced upstream and what data is consumed downstream:

```
Stage A output:    {detected items, confidence, frequency, justification}
                              │
                        [handoff boundary]
                              │
Stage B input:     {item names}
                              ↑
                    LOST: confidence, frequency, justification
```

**What to look for:**
- Fields that exist upstream but vanish downstream
- Rich objects flattened to simple lists or strings
- Lookup tables that override observation data
- Data that gets silently filtered without logging

### Step 2: Identify the Binding Constraint

The constraint is the handoff where the most valuable information is destroyed. Rank handoffs by:

| Factor | Weight |
|---|---|
| Amount of data lost | How much information vanishes? |
| Cost of downstream stages | How expensive are the stages that run on corrupt data? |
| Detectability | How hard is it to notice the data loss? |
| Impact on final output | How much does this loss affect end quality? |

**The constraint is the handoff that scores highest across these factors.**

### Step 3: Add a Gate

Write a validation function that reads the checkpoint files on both sides of the boundary and checks that critical data survived:

```python
def validate_handoff(stage_name, upstream_checkpoint, downstream_checkpoint):
    """External observer: reads checkpoints, never modifies pipeline."""

    if stage_name == 'stage3a_to_stage4b':
        # Critical: high-confidence detections must survive
        upstream_high = {
            item['name']
            for item in upstream_checkpoint['detected_items']
            if item['confidence'] == 'HIGH'
        }
        downstream_items = set(downstream_checkpoint.get('item_priorities', []))

        survived = upstream_high & downstream_items
        survival_rate = len(survived) / len(upstream_high) if upstream_high else 1.0

        return GateResult(
            passed=survival_rate >= 0.50,
            survival_rate=survival_rate,
            lost_items=upstream_high - downstream_items,
            severity='HARD' if survival_rate < 0.50 else 'SOFT'
        )
```

### Step 4: Wire to Stop Mechanism

Connect the gate to a stop-the-line hook in the pipeline runner:

```python
class PipelineRunner:
    def run(self):
        for stage in self.stages:
            result = stage.execute()

            # Quality gate after each stage
            gate_result = validate_handoff(stage.name, ...)
            if not gate_result.passed:
                print(f"⛔ Handoff gate failed after {stage.name}")
                print(f"   Lost: {gate_result.lost_items}")
                print(f"   Survival rate: {gate_result.survival_rate:.0%}")
                return False  # Stop — don't waste money downstream

            print(f"✓ {stage.name} passed handoff gate")
```

### Step 5: Fix Root Cause, Then Move On

Once the gate is catching the defect:
1. Fix the upstream stage so the gate passes
2. Run the full pipeline and verify the gate passes
3. The constraint has moved — find the next weakest handoff

---

## Gate Design Patterns

### Pattern 1: Observation Survival Gate

Validates that observation data detected upstream survives to downstream consumption.

```
Rule: ≥X% of high-confidence upstream observations
      must appear in downstream output.

Example: ≥50% of Stage 3a HIGH-confidence detections
         must appear in Stage 4b item_priorities.

Severity: HARD (below threshold stops pipeline)
Cost: $0 (reads checkpoint files on disk)
```

### Pattern 2: Metadata Preservation Gate

Validates that critical metadata (confidence, frequency, justification) isn't stripped at the boundary.

```
Rule: Downstream checkpoint must contain metadata fields
      for items that have them upstream.

Example: If Stage 3a provides {name, confidence, layer},
         Stage 4b output must preserve at least {name, confidence}.

Severity: SOFT (warns but continues — quality degraded, not corrupted)
Cost: $0
```

### Pattern 3: Coverage Gate

Validates that enrichment stages actually produce output for their declared scope.

```
Rule: Enrichment output must cover ≥Y% of the items
      it received as input.

Example: Stage 4.5 cluster guidance must produce
         non-empty guidance for ≥1 cluster-type item
         if cluster items exist in the input.

Severity: SOFT when coverage is partial;
          HARD when coverage is zero and items exist.
Cost: $0
```

### Pattern 4: Schema Contract Gate

Validates that the output shape matches what the next stage's code expects.

```
Rule: Required fields present, correct types, within value ranges.

Example: Stage 4b output must have 'device_priorities' as List[str]
         with length ≥ 1 for each pattern.

Severity: HARD (wrong schema crashes downstream)
Cost: $0
```

---

## External Observer Architecture

Gates should be **external observers**, not embedded in pipeline stages:

```
Pipeline:     Stage N → [checkpoint on disk] → Stage N+1
                              │
Observer:                     └─→ Gate reads checkpoint
                                  Validates data survival
                                  Returns pass/fail
                                        │
Pipeline:                          [continue / stop]
```

**Why external:**
- Pipeline code stays clean — no validation logic mixed with processing
- Gates can be added, modified, or removed without touching pipeline code
- Gate results are independently auditable
- Same gate can validate checkpoints from different runs
- Can run gates retroactively on historical checkpoints

**Implementation:**

```python
# Gates read checkpoint files, never import pipeline code
import json

def load_checkpoint(title, stage_name):
    path = f"checkpoints/{title}/{stage_name}.json"
    with open(path) as f:
        return json.load(f)

def validate_stage3a_to_4b(title):
    stage3a = load_checkpoint(title, 'stage3a')
    stage4b = load_checkpoint(title, 'stage4')
    return check_observation_survival(stage3a, stage4b)
```

---

## Implementation Patterns

### The Validation Callback Factory

Integrate gates into pipeline runners as a callback, not as inline code:

```python
def create_validation_callback(gate_configs):
    """Factory: returns a callback that validates handoffs at stage boundaries."""

    def validate(stage_name, checkpoint_data):
        """Called by the pipeline runner after each stage."""
        relevant_gates = [g for g in gate_configs if g.applies_to(stage_name)]

        for gate in relevant_gates:
            result = gate.check(checkpoint_data)

            if result.severity == 'ERROR':
                return StopSignal(
                    message=f"Gate failed: {gate.name}",
                    details=result.details
                )
            elif result.severity == 'WARNING':
                log_warning(gate.name, result.details)

        return ContinueSignal()

    return validate

# Usage:
runner = PipelineRunner(stages=[...])
runner.review_callback = create_validation_callback(gate_configs)
runner.run()  # Stops automatically on gate failure
```

**Why a factory:**
- Gate configurations can be loaded from files (no code change to add gates)
- Same factory produces callbacks for different pipeline configurations
- Testing: inject mock callbacks to test pipeline without gates

### Two-Tier Thresholds

Use two thresholds per gate to distinguish "stop" from "investigate":

```
Gate: Observation Survival
  ERROR threshold:   < 50%  → STOP the pipeline. Data is critically corrupted.
  WARNING threshold: < 70%  → LOG and continue. Some loss occurred, investigate later.
  HEALTHY:           ≥ 70%  → Normal operation.

Gate: Schema Compliance
  ERROR threshold:   Missing required fields → STOP.
  WARNING threshold: Optional fields missing  → LOG.
  HEALTHY:           All fields present       → Normal.
```

**Why two tiers:**
- Single-threshold gates are either too strict (stop on minor issues) or too lenient (miss major issues)
- Two tiers let you alert on concerning signals without stopping the pipeline
- Over time, WARNING-level signals accumulate into patterns that reveal systemic issues

**These are illustrative defaults, not universal constants.**

The correct thresholds depend on your pipeline's cost function. A pipeline with cheap, reversible downstream stages might tolerate 40% survival; one with expensive, irreversible stages (API calls, file moves, external publishes) may require 80% as the ERROR threshold.

Calibration procedure:
1. Run the pipeline at several survival rates (vary upstream quality by injecting test defects or using historical checkpoints at known quality levels)
2. Measure downstream output quality at each rate
3. Find the knee of the curve — the survival rate where output quality drops sharply
4. Set ERROR at that knee; set WARNING 15-20 percentage points above it

The thresholds are named constants (see code example above) specifically to make this calibration easy: change one number in one place, no hunting through inline logic. If you're building a new pipeline, start with 50%/70% as a placeholder and calibrate once you have measurement data.

### Standalone Audit Mode

Gates should work in two modes — integrated and standalone:

```python
# Mode 1: Integrated (runs during pipeline execution)
runner.review_callback = create_validation_callback(gates)
runner.run()

# Mode 2: Standalone (audits existing checkpoints without re-running)
results = validate_existing_checkpoints("ProjectName", gates)
print(results.summary())
```

**Why standalone matters:**
- Audit historical runs without re-executing the pipeline
- Compare gate results across runs to track improvement
- Add new gates and retroactively check old checkpoints
- Debug without the cost of re-running expensive stages

---

## Cost-Ordering: Cheap Gates Before Expensive Stages

Always validate handoffs before running stages that cost money:

| Check | Cost | Speed | Run When |
|---|---|---|---|
| Handoff validation | $0 | Seconds | After every stage |
| Schema contract check | $0 | Seconds | After every stage |
| Basic quality check | $0 | Seconds | Before expensive stages |
| Full API-based measurement | $$ | Minutes | Only when all gates pass |
| Manual review | Time | Hours | Only when metrics are ambiguous |

**The rule:** Never spend $2-5 on an API call when a $0 checkpoint read would have caught the problem.

---

## Integration with Other Skills

| Skill | How Constraint Gates Connects |
|---|---|
| **Failure Gates** | Constraint Gates tells you *where* to put gates (at the binding constraint). Failure Gates tells you *how* to design each gate (hard vs soft semantics). |
| **Measurement-Driven** | Add step 3.5 (Validate Handoffs) to the MDD cycle between FIX and MEASURE DEPTH. $0 validation before $$ measurement. |
| **Pattern-First** | Constraints often arise from causality violations — upstream observations overridden by downstream lookup tables. Pattern-First prevents this by enforcing dependency direction. |
| **R/P Split** | Many constraints trace to R/P violations: a precision task (category lookup) overriding a reasoning task's output (pattern detection). |
| **Prototype Building** | When exploring a new stage, validate handoffs early — don't build downstream stages until the upstream handoff is reliable. |
| **Domain Grounding** | Lookup tables that silently discard observations often stem from ungrounded taxonomies. Grounding categories in published theory reduces handoff failures. |
| **Boundary-Aware Measurement** | The system boundary is often where the binding constraint hides. Cheap validation at the boundary catches upstream defects before expensive downstream stages. |

---

## Diagnostic: Is This a Constraint Problem?

| Symptom | Likely Constraint? | What to Check |
|---|---|---|
| Improving a stage doesn't improve output quality | ✅ Yes | Trace data flow — is the defect upstream? |
| Expensive stages produce poor results | ✅ Yes | Are they consuming corrupt input? |
| Adding downstream heuristics provides diminishing returns | ✅ Yes | The root cause is upstream of the heuristics |
| A metric masks a process failure | Possibly | Check if gates at boundaries would catch it |
| A single stage fails intermittently | Probably not | More likely a Failure Gates problem |
| Pipeline crashes on bad input | No | This is a Failure Gates / schema validation problem |

---

## Checklist

When diagnosing a pipeline quality problem:
- [ ] Mapped value flow across all stage boundaries
- [ ] Identified which handoff destroys the most value (the constraint)
- [ ] Added observation survival gate at the constraint boundary
- [ ] Wired gate to stop mechanism (pipeline stops on gate failure)
- [ ] Verified that fixing the constraint (not downstream) improves output
- [ ] After fixing, identified the next constraint (it moves)

When adding a new stage:
- [ ] Defined what data the new stage needs from upstream (pull signal)
- [ ] Defined what data the new stage provides to downstream (output contract)
- [ ] Added handoff gate at the upstream boundary
- [ ] Added handoff gate at the downstream boundary
- [ ] Verified that gate cost < downstream stage cost (always validate before spending)
