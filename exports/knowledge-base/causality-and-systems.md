# Causality & Systems Thinking: Why Order Matters

**Read this before:** Pattern-First skill
**Core question:** How do you know if your system's dependencies point the right direction?

---

## The Common Assumption

When building a multi-step system, most people think about **what** each step does and assume the order is obvious. Step 1 feeds step 2, step 2 feeds step 3. The flow feels natural because you designed it that way.

The hidden assumption: **the order you thought of the steps is the order they should execute.** This is almost never examined, and it's frequently wrong.

---

## The Failure That Reveals the Truth

A data processing pipeline has two stages:

- **Stage A:** Select the best items from a dataset
- **Stage B:** Derive a pattern that explains why these items belong together

This feels logical. Find the data, then explain it. But measurement reveals a problem: the "pattern" in Stage B is just a post-hoc story invented to justify whatever Stage A selected. Change the selection criteria, and a completely different "pattern" emerges — equally convincing, equally unfounded.

**The pattern doesn't constrain the selection. The selection constrains the pattern.** The causality is backwards.

The fix: Reverse the order. Derive the pattern first (from analysis of the full dataset), then select items that match the pattern. Now the pattern is a genuine constraint, not a rationalization.

**Metric impact:** When this was fixed in the reference project, the rate of items matching their declared pattern jumped from ~63% to ~85%. The remaining 15% were genuine edge cases, not arbitrary selections.

---

## The Mental Model: Dependency Direction

Every multi-step system has dependency arrows between its components. These arrows have a **direction**, and the direction matters:

```
CORRECT (constraint-driven):
  Pattern → Selection
  "The pattern constrains what gets selected"
  Test: Change the pattern → selection changes
  Test: Remove an item → pattern still makes sense

BACKWARDS (rationalization):
  Selection → Pattern
  "The pattern explains what was selected"
  Test: Change the selection → pattern changes
  Test: Remove an item → pattern might collapse
```

### The Rationalization Test

For any two connected stages, ask:

> **If I remove the output of Stage B, does Stage A's output still make sense on its own?**

- If yes → A is independent, B depends on A. Order A → B is correct.
- If no → A was designed to serve B. The real dependency is B → A, and your order is backwards.

> **If I change Stage A's output, does Stage B produce a fundamentally different result?**

- If yes → B genuinely depends on A. Order A → B is correct.
- If barely → B isn't actually using A's output. The dependency is cosmetic.

---

## Three Failure Patterns

### 1. Post-Hoc Rationalization

**What it looks like:** Generate output first, then explain it.

```
WRONG:
  Step 1: AI generates a recommendation
  Step 2: AI explains why this recommendation is good
  (The explanation is crafted to justify the recommendation,
   not derived from independent analysis)

RIGHT:
  Step 1: Analyze criteria and constraints
  Step 2: Generate recommendation constrained by criteria
  Step 3: Verify recommendation meets criteria
  (The criteria exist before the recommendation)
```

**Detection:** Ask whether the explanation could have predicted the output. If the explanation only makes sense *after* seeing the output, it's rationalization.

**Real-world examples:**
- Code review: Write code → generate rationale (rationalization) vs. Design approach → implement to design (constraint-driven)
- Data analysis: Find correlations → explain them (fishing) vs. Hypothesize → test (scientific method)
- Feature planning: Build feature → write justification (political) vs. Define user need → design feature (product-driven)

### 2. Missing Upstream Dependencies

**What it looks like:** A stage works with whatever it's given, but it would work *better* if a prior stage optimized its input.

```
BEFORE:
  Stage 1: Select data (using default criteria)
  Stage 2: Analyze data
  Problem: Analysis is shallow because data wasn't selected for analyzability

AFTER:
  Stage 0.5: Optimize data selection FOR analysis quality
  Stage 1: Select data (using optimized criteria)
  Stage 2: Analyze optimized data
  Improvement: Analysis is deeper because input was curated
```

**Detection:** When a stage consistently produces mediocre results, ask: "Is the input the best possible input, or just the first available input?"

**In the reference project:** Pattern derivation was running on chapters selected for narrative importance — but patterns need chapters rich in textual devices. Adding an optimization stage that selected for device density (before pattern derivation) produced significantly better patterns.

### 3. Circular Dependencies

**What it looks like:** Stage A needs Stage B's output, but Stage B needs Stage A's output.

```
Stage A: "To classify this, I need to know the category system"
Stage B: "To build the category system, I need classified examples"
```

**Resolution:** Break the circle by establishing one side independently:
- Define the category system from principles (not from examples)
- Then classify examples using the category system
- Then refine the category system based on classification results (iterative, but with a clear starting point)

**The key:** One side must be grounded in something outside the circle — theory, requirements, prior knowledge, or explicit decision.

---

## The Principle: Structure Before Content

The generalization across all three failure patterns:

> **Define the structure/schema/pattern/constraints BEFORE populating instances.**

| Wrong Order | Right Order |
|---|---|
| Select items → invent pattern | Define pattern → select matching items |
| Write code → document it | Write spec → implement to spec |
| Build features → define roadmap | Define roadmap → build features |
| Create outputs → extract structure | Define structure → create outputs |
| Find data → form hypothesis | Form hypothesis → gather evidence |

**The deeper principle:** When structure follows content, the structure is a rationalization. When content follows structure, the structure is a genuine constraint that improves quality.

---

## Causality Auditing: A Practical Tool

When you're unsure about dependency direction, use this template:

```
DEPENDENCY ANALYSIS:

Thing A: [e.g., schema definition]
Thing B: [e.g., data population]
Thing C: [e.g., environment optimization]

Current order: A → B
Proposed: C → A → B

Questions:
1. Does A need information from B to work properly?
   → If yes: B should come first (backwards causality detected)

2. Does A need information from C to work properly?
   → If yes: C should come first (missing dependency detected)

3. Is B a rationalization of A, or constrained by A?
   → If rationalization: order is backwards

4. If we change A, must we change B?
   → If yes and you didn't expect this: dependency is real

5. If we remove A entirely, does B still make sense?
   → If yes: A isn't really constraining B (cosmetic dependency)

6. Can you run Stage N without running Stage N+1?
   → If no: backwards causality
```

---

## Systems Thinking: Alignment Across Components

Correct dependency ordering is necessary but not sufficient. Components must also be **aligned** — their outputs must compose coherently.

### Three Levels of Alignment

**1. Intra-component alignment:** Each component produces correct output for its own contract.
- Stage A's output satisfies Stage A's postconditions
- Verification: Unit tests, contract validation

**2. Inter-component alignment:** Components compose correctly.
- Stage A's output is consumed correctly by Stage B
- Stage B's output genuinely reflects Stage A's constraints
- Verification: Integration tests, interface validation

**3. Cross-case alignment:** The system produces consistent quality across different inputs.
- What works for Input 1 also works for Input 2
- A fix for one case doesn't regress another
- Verification: Breadth measurement (see Measurement Theory)

### The Alignment Disruption Cycle

When you add a new component or change an existing one, alignment is disrupted:

```
STABLE STATE
    │
    ▼  add new component
DISRUPTED
  - New component changes downstream inputs
  - Existing components may not handle new input shape
  - Metrics shift (some improve, some regress)
    │
    ▼  rebalance
RE-ALIGNED
  - Downstream components updated
  - Metrics rebalanced
  - Cross-case validation confirms stability
```

**This cycle is expected.** Every significant change disrupts alignment. The question isn't "how do I avoid disruption?" but "how do I detect and resolve it quickly?" (See Measurement Theory.)

---

## The Environment-First Corollary

A subtlety that took multiple iterations to discover:

> **Optimize the environment before deriving the schema.**

Even with correct ordering (schema before instances), the schema quality depends on what data it's derived from. If the input data is suboptimal, the schema will be suboptimal — and downstream instances will be constrained by a weak schema.

```
Level 1: Schema → Instances          (basic pattern-first)
Level 2: Optimized Input → Schema → Instances  (environment-first)
Level 3: Meta-optimization → Optimized Input → Schema → Instances
```

**Practical example:** If you're building a recommendation system:
- Level 1: Define recommendation criteria → select recommendations (good)
- Level 2: Curate the best training data → define criteria from curated data → select recommendations (better)

Each level adds a "preparation" stage that improves downstream quality by giving the schema derivation better raw material.

---

## Test Yourself

Before proceeding to the Pattern-First skill, you should be able to answer:

1. How do you tell the difference between a genuine constraint and a post-hoc rationalization?
2. What's the "rationalization test" for checking dependency direction?
3. Why does fixing dependency order improve measurable quality metrics?
4. What's the difference between "A feeds B" and "A constrains B"?
5. When a system is "aligned," what three levels of alignment exist?

If these feel clear, proceed to [Pattern-First](../skills/pattern-first.md).

---

## References

- Fowler, M. (2003). "Patterns of Enterprise Application Architecture" — dependency management in complex systems
- Meyer, B. (1988). "Object-Oriented Software Construction" — contracts between components
- Kahneman, D. (2011). "Thinking, Fast and Slow" — post-hoc rationalization as System 1 behavior
- This repository's measurement data: PPR tracking from v4.0 to v9.3 (63% → 85%+ after causality fix)
