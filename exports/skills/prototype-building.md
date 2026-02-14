# Skill: Prototype Building (Exploration → Execution)

**Purpose:** Ensure you understand the problem before building the solution.
**Addresses:** Over-engineering, rabbit holes, scope creep, and building the wrong thing.

---

## Core Principle

**Don't build until the pattern is confirmed.**

```
EXPLORATION (must complete first):
1. Problem Definition    → Can you state it in one sentence?
2. Decomposition         → What are the sub-problems?
3. Pattern Recognition   → What approach will work?
4. Abstraction           → Can you describe it generally?
─────────────────────────────────────────────────────────
EXECUTION (only after exploration):
5. Build                 → Follow the confirmed pattern
```

If you're building and can't clearly state 1-4, stop and go back.

---

## Principles

### Real Case First

Never build in the abstract. Start with one real case.

| Wrong | Right |
|---|---|
| "Design a validation system" | "Validate this one input, then figure out the system" |
| "Build a data pipeline" | "Process this one file, then extract the pattern" |
| "Create a testing framework" | "Write this one test, then generalize" |

The real case forces concrete decisions, reveals hidden assumptions, provides test data, and prevents over-engineering.

### One Problem Per Session

Each work session = one bounded piece of work.

- State the problem at the start
- Don't branch into side problems (log them for later)
- End with clear output or decision
- Use handoff docs for continuity

Long sessions drift. Bounded sessions stay focused.

### Structure Before Content

Define the pattern/schema/structure before populating it. (See Pattern-First skill for full treatment.)

### LLM Output Is Hypothesis

"This should work" from an LLM means:
- The logic seems sound
- The code looks correct
- **It has not been tested**

Treat every LLM output as hypothesis until verified by running actual code on actual data.

---

## The Exploration Stages

### Stage 1: Problem Definition

**Question:** What are we actually trying to solve?

**Do:**
- State the problem in one sentence
- Identify who the user is
- Define what success looks like
- Get a real case to test against

**Don't:**
- Jump to solutions
- Accept vague requirements ("make it better")
- Start with technical architecture

**Checkpoint:** Can you state the problem in one sentence?

### Stage 2: Decomposition

**Question:** What are the component parts?

**Do:**
- List sub-problems or questions
- Identify what you need to know before solving
- Name assumptions you're making
- Find the simplest version of the problem

**Don't:**
- Decompose into technical components before understanding needs
- Treat everything as equally important
- Skip to architecture

**Checkpoint:** Do you have a list of sub-problems?

### Stage 3: Pattern Recognition

**Question:** What approach will work?

**Do:**
- Check if you've solved something similar before
- Identify what approaches exist
- Test approach against real case
- Note what worked and what didn't

**Don't:**
- Invent new approach when existing one works
- Copy approach without understanding why it works
- Declare pattern found without testing

**Checkpoint:** Can you describe the pattern or approach?

### Stage 4: Abstraction

**Question:** Can we describe this generally?

**Do:**
- Explain approach to someone else
- Identify what's reusable vs case-specific
- Predict when approach will fail
- Classify tasks as reasoning or precision (R/P Split)

**Don't:**
- Abstract before pattern is confirmed
- Over-generalize from one case
- Skip R/P classification

**Checkpoint:** Can you state the solution approach in general terms?

### Stage 5: Execution

Only now: build the thing.

**Do:**
- Follow the confirmed pattern
- Test against the original real case
- Test against 2+ additional cases
- Save checkpoints for resumption

**Don't:**
- Improvise or expand scope
- Skip verification
- Build without testing

**Checkpoint:** Does the output solve the problem stated in Stage 1?

---

## The Iterative Fix Loop

When fixing something that's broken:

```
MEASURE → DIAGNOSE → FIX → VERIFY → (repeat)
```

### Rules

1. **Measure first** — Numbers, not vibes. Build measurement tools before fixing.
2. **Establish baseline** — Numbers before you touch anything.
3. **Define success** — What metrics need to change, by how much.
4. **Level 0 gates everything** — If the data is fabricated, all other metrics describe the fabrication.
5. **Scope fix to single issue** — Don't fix three things at once.
6. **Verify with measurement** — "I think it's working better" → "Score went from 33% to 92%"

---

## Rabbit Hole Detection

### Signs You're In a Rabbit Hole

| Signal | What's Happening |
|---|---|
| Elaborating something already documented | Rediscovering, not discovering |
| "This changes everything" | Probably doesn't |
| 1000+ words explaining a simple fix | Over-engineering |
| Can't test it against real case | Too abstract |
| Same problem reframed 3+ times | Lost the thread |
| Building infrastructure for hypothetical use | Premature optimization |
| 20+ exchanges with no output | Blocked on something |

### How to Reframe

| Trigger | Reframe To |
|---|---|
| "We need to restructure the whole system" | What's the ONE thing broken? |
| "This is more complex than I thought" | What's the simplest version? |
| "Let me explain the theory first" | What's the concrete test case? |
| "This should work now" | Did you actually run it? |
| "I need to build X before I can do Y" | Can I do Y manually first? |

### Recovery Steps

1. State the original problem in one sentence
2. State what you've tried and why it failed
3. Ask: "What's the simplest thing that could work?"
4. Get a real case and test against it
5. If still stuck, start fresh with new framing

---

## Quick Reference

### Starting Work
- [ ] State problem in one sentence
- [ ] Have a real case to test against
- [ ] Identify exploration stage (1-4) or execution (5)

### During Exploration
- [ ] Test ideas against real case
- [ ] Don't build until pattern confirmed
- [ ] Watch for rabbit hole signals
- [ ] Classify R/P before building

### Building
- [ ] Follow confirmed pattern
- [ ] Precision in code, reasoning in LLM
- [ ] Save checkpoints
- [ ] Test on original + 2 more cases

### Debugging
- [ ] Measure first (numbers, not vibes)
- [ ] Apply R/P recursive diagnostic
- [ ] Scope fix to single sub-issue
- [ ] Verify fix with measurement
