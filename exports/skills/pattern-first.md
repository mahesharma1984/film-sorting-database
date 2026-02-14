# Skill: Pattern-First Development

**Purpose:** Ensure correct dependency ordering — define structure before populating instances.
**Addresses:** Post-hoc rationalization, backwards causality, and scope creep in staged systems.

---

## Core Principle

**Define the schema/pattern/structure BEFORE populating instances.**

| Wrong Order (Rationalization) | Right Order (Structure-First) |
|---|---|
| Select items → invent pattern to explain them | Derive pattern → select items matching it |
| Create outputs → extract structure | Define structure → fill outputs |
| Write code → document what it does | Write spec → implement to spec |
| Find data → validate hypothesis | Define hypothesis → find supporting data |
| Build features → map progression | Define progression → build features |

**The test:** If you remove the instances, does the pattern still make sense? If yes, pattern-first is working. If the pattern only exists because of specific instances, you have post-hoc rationalization.

---

## Principles

### Principle 1: Derive Constraints Before Filling Them

Always define what you're looking for before you start looking.

**Anti-patterns:**
- **Post-hoc naming:** Generate output → name it based on output
- **Selection without criteria:** Pick items → invent reason they fit
- **Iterative rationalization:** Make change → discover it breaks something → fix that → repeat

**Correct patterns:**
- Define criteria → select items matching criteria
- Define schema → populate conforming instances
- Define contract → implement to contract

### Principle 2: Stage Boundaries Are Invariants

In any multi-stage system, each stage should have:
1. **Clear inputs** — reads from prior stages
2. **Clear outputs** — saves for next stage
3. **No skipping** — cannot bypass dependencies
4. **Validation** — verifies dependencies exist before running

```
Stage 1 (Foundation)
  → Stage 2 (Optimization)
    → Stage 3 (Derivation)
      → Stage 4 (Application)
        → Stage 5 (Output)
```

Each stage cannot run without its predecessor completing. This prevents:
- Running application without derivation
- Running derivation without optimization
- Running any stage without its dependencies

### Principle 3: Causality Auditing

Before changing dependency order, verify causality direction:

```
DEPENDENCY ANALYSIS:

Thing A: [e.g., schema definition]
Thing B: [e.g., instance creation]
Thing C: [e.g., environment setup]

Current order: A → B
Proposed: C → A → B

Questions:
1. Does A need information from B to work properly?
2. Does A need information from C to work properly?
3. Is B a rationalization of A, or a constraint on A?
4. Is A a rationalization of C, or an optimization using C?
5. If we change A, must we change B?
6. If we change C, must we change A?

If 1=Yes or 3=constraint → B should come FIRST (A→B wrong)
If 2=Yes or 4=optimization → C should come FIRST (C→A correct)
If 5=Yes → Current A→B order is wrong
If 6=Yes → C→A order is correct
```

**Simple test:** Can you run Stage N without running Stage N+1? If no, you have backwards causality.

### Principle 4: Checkpoint-Driven Development

Every stage saves a checkpoint for resumption:

```python
def stage_n(self):
    # Try to load checkpoint
    cached = self._load_checkpoint('stage_n')
    if cached:
        return cached

    # Do work
    result = do_work()

    # Save for future runs
    self._save_checkpoint('stage_n', result)
    return result
```

Benefits:
- **Resume from failure** — restart from last good stage
- **Incremental testing** — validate each stage independently
- **Dependency tracking** — each checkpoint declares what it needs
- **Version compatibility** — old checkpoints work with new code

### Principle 5: Mechanism vs. Theme Separation

When generating structured output, separate HOW from WHAT:

| Aspect | Mechanism (HOW) | Theme (WHAT) |
|---|---|---|
| Describes | How the system works | What the system reveals |
| Source | Process/structure analysis | Output/evidence analysis |
| Function | Constrains downstream work | Emerges from downstream work |

**Correct causality:**
```
Analysis (codes) → Mechanism (HOW) → Application (instances) → Theme (WHAT emerges)
```

**Test:** Your mechanism should complete: "The system uses [mechanism] to achieve..."
- "The system uses progressive disclosure to build understanding" ✓
- "The system uses user engagement improvement to..." ✗ (tautological — describes outcome, not process)

---

## Diagnostic Procedure

### Detecting Backwards Causality

**Symptoms:**
- Output quality varies unpredictably
- Changes in one component cascade unexpectedly
- "It works but I'm not sure why"
- Adding data changes the schema/structure

**Diagnosis:**
1. List all stages/components
2. Draw dependency arrows
3. Check: does any arrow point backwards?
4. Check: is any dependency missing?

### Detecting Post-Hoc Rationalization

**Symptoms:**
- Categories change when data changes
- Structure only makes sense with specific instances
- Can't predict what new instances would look like
- Naming happens after generation

**Fix:** Insert an explicit derivation step before the population step.

---

## Refactoring Checklist

When modifying a staged system:
- [ ] Does this change introduce backwards causality?
- [ ] Should this be a new stage or modify existing?
- [ ] Does the checkpoint system need updating?
- [ ] Are stage boundaries still clean?
- [ ] Did we trace ALL dependencies?
- [ ] Can we resume from failure?
- [ ] Does this optimize the environment before deriving schema?

---

## Key Insight

Pattern-First is orthogonal to other methodologies:
- **Pattern-First** addresses DEPENDENCY ordering (what must exist before what)
- **R/P Split** addresses WHO does the work (LLM vs code)
- **Measurement-Driven** addresses WHEN to validate (depth then breadth)

They compose naturally: Pattern-First tells you the order, R/P Split tells you the actor, Measurement-Driven tells you when to check.
