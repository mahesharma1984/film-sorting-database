# Methodology in Action: How These Skills Evolved

This document shows how the five skills were discovered and refined through real development experience. Each skill emerged from a concrete failure, was validated by measurement, and generalized into a reusable principle.

---

## R/P Split: The Quote Hallucination Discovery

### The Problem (v6.0)

A content processing pipeline asked an LLM to do everything in one call: "Find relevant items in this text, quote them exactly, explain their significance, and output as JSON."

**What happened:** ~50% of the "exact quotes" didn't exist in the source text. The LLM was generating plausible-looking text from its training data instead of extracting from the actual input.

**Why it wasn't caught:** The output looked correct. Fabricated quotes were indistinguishable from real ones without automated verification.

### The Fix (v6.1)

Split the single call into four phases:

```
BEFORE (single call - fails):
  LLM: "Find items, quote them, explain them, format as JSON"
  Result: ~50% fabricated quotes, some malformed JSON

AFTER (4-phase split - works):
  Phase A (REASONING): LLM identifies items, describes locations
  Phase B (PRECISION): Code searches source, extracts exact text
  Phase C (REASONING): LLM explains significance given verified text
  Phase D (PRECISION): Code assembles valid output format

  Result: 95%+ verified quotes, valid output format
```

### The Metric

Quote Verification Rate (QVR) tracked this:
- Before R/P Split: ~50-67%
- After R/P Split: 95%+
- The fix was **universal** — worked across all inputs

### The Generalization

The R/P Split skill emerged: **LLMs reason well but handle precision poorly.** Any task that mixes reasoning (interpretation) with precision (exact extraction) should be split. The LLM does the reasoning; code handles the precision.

---

## Pattern-First: The Backwards Causality Discovery

### The Problem (v4.0)

The pipeline selected output items first, then invented a pattern to explain why those items were selected. This is post-hoc rationalization — the pattern didn't actually constrain selection.

**Metric:** Priority Purity Rate (PPR) = ~63%. Only 63% of items came from the declared priority list. The rest were whatever the LLM found interesting.

### The Fix (v5.0)

Reversed the causality: derive the pattern FIRST (from analysis), THEN select items that match the pattern.

```
BEFORE (rationalization):
  Stage 5: Select items (whatever looks good)
  Stage 6: Invent pattern to explain selection
  PPR: ~63%

AFTER (pattern-first):
  Stage 4: Derive pattern from analysis (mechanism, priorities)
  Stage 5: Select items matching pattern priorities
  PPR: ~85%
```

### Further Refinement (v5.0)

A second causality issue was discovered: the pattern was derived from suboptimal data. Adding an optimization stage BEFORE pattern derivation improved results further:

```
Stage 2: Optimize data selection (find richest inputs)
  → Stage 4: Derive pattern from optimized data
    → Stage 5: Select items matching pattern
```

### The Generalization

The Pattern-First skill emerged: **Define the schema/pattern/structure BEFORE populating instances.** And the environment-optimization corollary: **Optimize the data landscape before deriving the schema.**

---

## Measurement-Driven Development: The Two-Axis Discovery

### The Problem (v8.0)

A new feature (semantic grouping) was added. It improved some inputs dramatically but didn't affect others. Worse, the scoring formula had to be reweighted, which shifted every score.

**The tension:** A fix that helped Input A might degrade Input B. How do you know?

### The Cycle That Emerged

Looking back at version history (v5.0-v9.0), a consistent pattern was visible:

1. A metric fails → identify which component
2. Fix the component → re-measure the target (depth)
3. Re-measure all inputs → check for regressions (breadth)
4. If regression found → investigate case-specific vs universal
5. Stabilize when both axes aligned

This cycle was followed implicitly for years before being documented.

### The Two Development Modes

**Frontier (depth-first):** Push capability for one case. A v9.0 bug fix let the system detect a key pattern for the first time. Score went from 0.78 to 0.84 — but the real gain was a capability that didn't exist before.

**Consistency (breadth-first):** After frontier changes, verify nothing regressed. Some fixes are universal (R/P Split improved all inputs). Others are case-specific (semantic grouping helps some inputs, not others).

### The Generalization

The Measurement-Driven Development skill emerged: **Development operates on two axes — depth (single case quality) and breadth (cross-case consistency).** Always measure both after changes.

---

## Failure Gates: The Silent Corruption Discovery

### The Problem (v8.5)

A component was producing invalid output that looked valid. Downstream stages consumed it without complaint. Quality scores looked acceptable because the scoring system measured the invalid output's surface properties.

**The discovery:** A scored 0.84 ("STRONG") while only checking 1 of 4 declared validation gates. The contract said "check 4 gates" but only 1 was enforced.

### The Fix

Added explicit validation gates between stages:

```
Stage 4: Produce output
  → Stage 4.2: VALIDATION GATE (hard gates)
    ├── Gate 1: Coherence check (≥3 of 5 items align) → HARD
    ├── Gate 2: Concrete anchor floor (2-3 anchors) → HARD
    └── Gate 3: Compatibility check → SOFT
  → Stage 4.5: Continue with validated output
```

The gate has a repair mechanism (max 2 attempts). If repair fails, it degrades gracefully rather than silently passing bad data.

### The Generalization

The Failure Gates skill emerged: **Every stage must declare hard gates (stop on failure) and soft gates (warn and continue).** Without explicit gates, failures cascade silently and produce output that looks valid but isn't.

---

## Prototype Building: The Rabbit Hole Discovery

### The Problem (Ongoing)

Development sessions would start with a clear goal but drift into:
- Redesigning everything instead of fixing one thing
- Building infrastructure for hypothetical future use
- Explaining theory instead of testing against real cases
- 20+ exchanges with no tangible output

### The Recognition

Productive sessions followed a pattern:
1. State problem clearly (one sentence)
2. Get a real test case
3. Test approach against real case
4. Build only after pattern confirmed

Unproductive sessions skipped step 2 or 3.

### The Rabbit Hole Signals

| Signal | What's Happening |
|---|---|
| "This changes everything" | Probably doesn't |
| 1000+ words explaining a simple fix | Over-engineering |
| Can't test against real case | Too abstract |
| Same problem reframed 3+ times | Lost the thread |

### The Generalization

The Prototype Building skill emerged: **Don't build until the pattern is confirmed.** Exploration (understanding) must precede execution (building). And: **LLM output is hypothesis until tested.**

---

## How the Skills Compose

In practice, these skills are used together:

```
1. New problem arrives
   → Prototype Building: State problem, get real case

2. Explore the problem
   → R/P Split: Classify tasks (reasoning vs precision)
   → Pattern-First: Check dependency ordering

3. Build the solution
   → Failure Gates: Define what stops vs warns
   → Pattern-First: Schema before instances

4. Validate the solution
   → Measurement-Driven: Measure depth (did target improve?)
   → Measurement-Driven: Measure breadth (did anything regress?)

5. Stabilize
   → Document what changed and why (with metric evidence)
```

The skills are orthogonal — each addresses a different dimension:
- **WHO** does the work → R/P Split
- **WHAT ORDER** → Pattern-First
- **WHAT HAPPENS ON FAILURE** → Failure Gates
- **HOW TO VALIDATE** → Measurement-Driven
- **HOW TO START** → Prototype Building
