# Skill: Failure Gates (Hard vs Soft Failure Semantics)

**Purpose:** Define explicit failure handling at every stage of a pipeline.
**Addresses:** Cascading failures, silent corruption, and unclear failure semantics.

---

## Core Principle

**Every pipeline stage must declare which failures stop execution (hard gates) and which warn and continue (soft gates).**

Without explicit failure gates:
- Failures cascade silently downstream
- Debugging requires tracing through multiple stages
- Partial failures produce corrupt output that looks valid
- Teams disagree about what should stop the pipeline

---

## Gate Types

### Hard Gates (Stop Execution)

Failures that invalidate everything downstream. The pipeline cannot produce valid output if these fail.

**Characteristics:**
- Downstream stages would consume corrupt data
- Output would be misleading if published
- No reasonable default or fallback exists
- Data integrity is compromised

**Examples:**
- Data validation failure (required fields missing)
- Evidence integrity failure (source data corrupted)
- Critical invariant violation (contract broken)
- Required output missing (can't proceed without it)

### Soft Gates (Warn and Continue)

Failures that reduce quality but don't invalidate the output. The pipeline can still produce useful results.

**Characteristics:**
- Output is degraded but still valid
- Downstream stages can handle missing/partial data
- Reasonable defaults exist
- Quality is reduced, not corrupted

**Examples:**
- Coverage below target (some areas not covered)
- Quality score below target (not great but not broken)
- Optional enrichment failed (skip and continue)
- Expected variance (not every input produces ideal output)

---

## Absence-Based Failures: When Evidence Is What's Missing

The Gate Types section above describes presence-based gates: "Is this field populated? Does this record exist? Is this value within range?" But some system properties are defined by **absence**, not presence. These require a different gate design.

### The Problem

For absence-based properties, the evidence is a **scope statement** ("X does not occur across Y"), not a **located instance** ("X occurs at position Z"). When a presence-based gate is applied to an absence-based property, it fails in a specific way: it produces syntactically valid but semantically wrong evidence.

```
WRONG (presence gate applied to absence property):
  Gate asked: "Verify no Core directors appear in Satellite manifest"
  Gate checks: "Find an instance of a Core director in Satellite"
  Gate finds nothing → reports PASS
  Problem: "found nothing" is not a verified scope statement.
           The gate didn't check the whole manifest; it just failed
           to find a counterexample. These are different things.

RIGHT (scope gate):
  Gate checks: "Across all N classified films in Satellite manifest,
               count films where director ∈ CORE_DIRECTORS"
  Gate finds count = 0 → reports PASS with scope
  "Zero Core director films in Satellite (N=847 films checked)"
  This is a verified scope statement, not an absence of evidence.
```

### Two Gate Types

| | Presence-Based | Absence-Based |
|---|---|---|
| **Success criterion** | Did we find evidence? | Did we correctly verify the property holds across the declared scope? |
| **Evidence format** | Located instance (position + value) | Scope statement (range + property + count) |
| **Validation** | Compare found instance against source | Verify property holds across all N items in declared range |
| **Failure signal** | No instance found | Count > 0 (property violated); or scope not declared (gate was incomplete) |

### Film Classification Examples

All three of these properties are absence-based. Each requires a scope gate, not an instance gate.

**"No Core director films are misrouted to Satellite"**
```
Scope: all films in sorting_manifest.csv where destination contains "Satellite/"
Property: director ∉ CORE_DIRECTORS whitelist
Verification: count films where director ∈ CORE_DIRECTORS
Gate: HARD if count > 0; PASS if count = 0 (report N films checked)
```

**"No Satellite category exceeds its film cap"**
```
Scope: all Satellite categories in sorting_manifest.csv
Property: count(films per category) ≤ self.caps[category]
Verification: group by category, compare each group size to cap constant
Gate: HARD if any category count > cap; PASS if all within bounds
```

**"No film appears in more than one tier"**
```
Scope: all films in sorting_manifest.csv
Property: each film_id appears exactly once
Verification: count duplicates (group by normalized title+year, find count > 1)
Gate: HARD if duplicates > 0; PASS if all unique (report N films checked)
```

### Scope Gate Design Template

```
Scope gate for [property name]:

Scope:    [what dataset, manifest, or range is being checked]
Property: [what must not occur / what must hold]
Method:   [how to verify — count, group by, set intersection, etc.]
Report:   "Zero violations of [property] across [N] items in [scope]"
          OR
          "[K] violations found: [list]"
Gate:     HARD if violations > 0
          PASS if violations = 0 (always report N items checked)
```

Always report N items checked. A PASS on 0 items is not a PASS — it means the gate didn't run. If N = 0, raise a soft warning: "scope was empty, gate did not execute."

### Connection to Abstraction Levels

Absence-based properties tend to appear at higher abstraction levels (see Domain Grounding):

- **Levels 1-2 (Concrete/Descriptive):** Usually presence-based — specific things at specific positions
- **Levels 5-6 (Structural/Abstract):** Often absence-based — properties of the whole system, not individual parts

If your pipeline classifies entities across abstraction levels, you need both gate types. Match gate design to abstraction level: instance gates for concrete properties, scope gates for structural properties.

---

## Gate Design Template

For each pipeline stage:

```
Stage N: [Name]
├── Hard Gates (stop on failure):
│   ├── [Gate 1]: [What it checks] → [Why it stops]
│   ├── [Gate 2]: [What it checks] → [Why it stops]
│   └── ...
│
├── Soft Gates (warn on failure):
│   ├── [Gate 3]: [What it checks] → [What happens if it fails]
│   ├── [Gate 4]: [What it checks] → [What happens if it fails]
│   └── ...
│
└── Validation:
    ├── Run order: Hard gates first, then soft gates
    ├── On hard gate failure: Stop, log, report
    └── On soft gate failure: Warn, continue, report
```

### Example

```
Stage: Data Processing
├── Hard Gates:
│   ├── Input file exists and is readable → Can't process without input
│   ├── Schema validation passes → Downstream expects specific shape
│   └── No duplicate primary keys → Would corrupt joins
│
├── Soft Gates:
│   ├── Coverage ≥ 80% → Below target but still useful
│   ├── No null values in optional fields → Quality reduced
│   └── Processing time < 5min → Performance warning
│
└── Validation:
    ├── Hard gates run first (fail fast)
    ├── If any hard gate fails → abort stage, return error
    └── If soft gate fails → log warning, continue processing
```

---

## Design Rules

### Rule 1: Level 0 Gates Everything

Define a "Level 0" — the most fundamental validity check. If Level 0 fails, nothing downstream is worth measuring.

```
Level 0: Can we verify the data is real?
         ↓ (must pass)
Level 1+: Everything else
```

**Example:** If your pipeline produces outputs with cited sources, verify the sources exist before measuring output quality. If sources are fabricated, quality metrics describe the fabrication.

### Rule 2: Hard Gates Have No Repair Logic

Hard gates are binary: pass or fail. Don't add repair mechanisms to hard gates — that makes them soft gates with auto-fix.

If you want auto-repair, make it a separate stage with its own gates:

```
Stage N: Processing
  → Stage N.1: Validation Gate (hard gates)
  → Stage N.2: Repair (if N.1 fails, attempt repair, max 2 tries)
  → Stage N.3: Re-validation (hard gates again after repair)
```

### Rule 3: Soft Gates Accumulate

Track soft gate failures across the pipeline. Individual soft failures are acceptable; accumulation signals systemic issues.

```python
soft_warnings = []

for stage in pipeline:
    result = stage.run()
    soft_warnings.extend(result.warnings)

if len(soft_warnings) > WARNING_THRESHOLD:
    log.error(f"Accumulated {len(soft_warnings)} warnings — investigate")
```

### Rule 4: Gate Thresholds Are Explicit

Don't hide thresholds in code comments or documentation. Make them constants:

```python
# Hard gate thresholds
MIN_DATA_INTEGRITY = 0.90      # Below this, data is unreliable
REQUIRED_FIELDS = ['id', 'source', 'content']

# Soft gate thresholds
TARGET_COVERAGE = 0.80         # Below this, warn but continue
TARGET_QUALITY = 0.70          # Below this, warn but continue
MAX_PROCESSING_TIME = 300      # Seconds; above this, performance warning
```

---

## Failure Escalation

When diagnosing failures, follow this escalation pattern:

```
1. Which gate failed?
   → Hard gate: Pipeline stopped. Fix the input or the stage.
   → Soft gate: Pipeline continued. Check if output quality is acceptable.

2. Where did it fail?
   → Early stage: Fix upstream. Don't patch downstream.
   → Late stage: Likely consuming bad upstream output. Trace backwards.

3. Is it a new failure?
   → Yes: Something changed. Diff recent changes.
   → No (recurring): Systemic issue. Needs architecture fix, not patch.
```

**Key principle: Fix upstream, not downstream.** If Stage 3 produces bad output because Stage 1's input was wrong, fix Stage 1 — don't add special handling in Stage 3.

---

## Integration with Other Skills

| Skill | How It Connects |
|---|---|
| **R/P Split** | Many hard gate failures trace to precision tasks given to LLMs |
| **Pattern-First** | Gate ordering follows dependency ordering |
| **Measurement-Driven** | Gates are contract tests; measurement validates contracts |
| **Constraint Gates** | Use constraint protocol first to find WHERE to put gates (at the binding constraint); then use failure gates to design HOW each gate works (hard vs soft semantics). The two skills are designed to be used together. |
| **Domain Grounding** | Abstraction level determines gate type: Levels 1-4 entities use presence-based gates (find an instance); Levels 5-6 entities use scope/absence-based gates (characterize the whole). See Absence-Based Failures section below. |
| **Boundary-Aware Measurement** | Hard gates at the system boundary catch the most costly failures. Concentrate the strongest gates at the cost cliff — the handoff where corrupt data becomes expensive to recover from. |

---

## Checklist

When adding a new pipeline stage:
- [ ] Listed all possible failure modes
- [ ] Classified each as hard gate or soft gate
- [ ] For each property: is it presence-based or absence-based?
  - Presence-based → instance gate (find an example of X)
  - Absence-based → scope gate (verify X does not occur across N items; always report N)
- [ ] Hard gates have no auto-repair (separate repair stage if needed)
- [ ] Soft gates log warnings with context
- [ ] Gate thresholds are explicit constants
- [ ] Level 0 gates run first
- [ ] Failure reporting includes which gate failed and why
- [ ] Scope gates report items-checked count (a PASS on 0 items is not a PASS)
