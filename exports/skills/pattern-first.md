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

### Principle 5: Optimize the Environment Before Deriving the Schema

Basic Pattern-First (Principle 1) ensures schema before instances. This principle extends it: **the schema quality depends on what it was derived from.** If the input environment is suboptimal, the schema will be suboptimal — and downstream instances will be constrained by a weak schema, even if the derivation logic is correct.

```
Level 1: Schema → Instances
         (basic pattern-first: schema before instances)

Level 2: Optimized Input → Schema → Instances
         (environment-first: curate input before deriving schema)

Level 3: Meta-optimization → Optimized Input → Schema → Instances
         (optimize the optimization: track which input qualities
          actually improved schema quality, then target those)
```

Each level adds a preparation stage upstream that gives schema derivation better raw material.

**Film classification worked example:**

*Level 1 (pre-v0.2):* Derive routing rules → classify films. Country data came from TMDb, which frequently returns `countries: []` for foreign films. Routing rules tuned against this input were systematically unreliable for non-English cinema — the rules couldn't route what the data couldn't describe. Improving the rules didn't help: the binding constraint was the input quality, not the rule logic.

*Level 2 (current v0.2):* Add OMDb parallel query → merge and normalize country data → derive routing rules → classify films. The `_query_apis()` + `_merge_api_results()` methods are the Level 2 preparation stage. Country data quality improves before routing rules are derived or tuned. Non-English films now arrive with reliable country codes; the routing rules that were always logically correct can finally fire.

*Level 3 (not yet implemented):* Track which API fields actually drove classification decisions (which country codes triggered which Satellite routes, which director names triggered which Core matches). Optimize the enrichment strategy to maximize coverage of those specific fields. This is meta-optimization of the enrichment stage itself — changing not just what data you collect, but how you collect it based on what the downstream schema actually needs.

**Decision rule — when is Level 2 worth adding?**

```
If Stage N consistently underperforms for a specific class of inputs:

1. Is Stage N's logic correct in principle?
   → If no: fix Stage N. Level 2 won't help.

2. Does improving Stage N's logic produce measurable improvement
   for that class?
   → If yes: constraint is in Stage N. Level 1 is sufficient.
   → If no: constraint is upstream. Input quality is the problem.

3. What information is Stage N missing to do its job correctly?
   → That missing information is what the Level 2 stage must provide.
```

**Validating that Level 2 helped:** Run classify.py on a test set before and after adding the enrichment stage. Compare routing accuracy for the class of inputs that was underperforming. If accuracy improves and the inputs that changed are exactly the inputs that were data-deficient, the Level 2 stage is working. If accuracy doesn't improve, the constraint wasn't the input — revisit Stage N's logic.

### Principle 6: Mechanism vs. Theme Separation

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

### Detecting Circular Dependencies

Unlike backwards causality (which can be fixed by swapping order), circular dependencies cannot be resolved by reordering. They require breaking the circle from outside it.

**Detection pattern:** Stage A's correctness improves with Stage B's output, and Stage B's correctness improves with Stage A's output. Neither can fully validate without the other.

**Film classification example:** `_clean_title_for_api()` removes format signals before API lookup. The API lookup uses the cleaned title to find the director. The director determines the tier. The tier partially predicts which format signals are meaningful (a 35mm signal on a Godard title behaves differently than on a mainstream release). This is a weak circularity — title cleaning assumes some knowledge of what tier a film is likely in.

**Resolution:** Identify which side can be established from first principles — i.e., from something outside the circle. Establish that side first; let the other depend on it.

For the film example: format signal removal rules are defined from the `FORMAT_SIGNALS` constant in `lib/constants.py` (a static precision rule, not inferred from tier). The circle is broken by grounding title cleaning in an explicit list rather than in tier inference.

**General resolution procedure:**
```
1. Name the two sides: A needs B, B needs A
2. Ask: can A be defined without B using first principles,
        theory, or explicit requirements?
3. If yes → establish A from first principles, then derive B from A
4. If both sides need the other → one side is foundational
   (usually the schema/taxonomy side); ground it in published
   theory or explicit decision, then derive the other
```

**Connection to R/P Split:** Circular dependencies often arise when a REASONING step and a PRECISION step are too tightly coupled. Separating them reveals which side is foundational — the PRECISION side can almost always be established from explicit rules without needing the reasoning output first.

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
