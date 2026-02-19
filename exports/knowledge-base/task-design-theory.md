# Task Design Theory: How You Decompose Work Determines Outcome Quality

**Read this before:** Prototype Building skill, R/P Split skill
**Core question:** Why does the way you break down a problem determine whether the solution works?

---

## The Common Assumption

When faced with a complex task, most people jump to solutions:

1. **"Let me just build it"** — Start coding immediately, figure out the structure as you go.
2. **"Let me plan the architecture"** — Design the technical structure, then populate it with logic.
3. **"Let me ask the AI to do it"** — Describe the desired outcome, let the AI figure out the steps.

All three skip the same step: **understanding the nature of the tasks involved before choosing who does them and in what order.**

---

## The Failure That Reveals the Truth

You ask an AI to "analyze this dataset, find the key patterns, extract supporting evidence, calculate statistics, and produce a formatted report."

The AI produces something. It looks comprehensive. But:
- The "patterns" are plausible narratives, not data-driven findings
- The "evidence" includes fabricated data points that don't exist in the source
- The statistics are approximately right but contain arithmetic errors
- The report format has structural inconsistencies

You spent hours reviewing and correcting. Next time, you add more instructions to the prompt. The output improves slightly but the same categories of errors persist.

**The problem isn't the prompt. It's the task design.** You gave a single actor (the AI) a task that contains fundamentally different types of work. Some of those types are things the AI is good at. Others are things it structurally cannot do reliably. No prompt improvement fixes a structural mismatch.

---

## The Mental Model: Tasks Have Types

Every unit of work has inherent properties that constrain who can do it well:

### Reasoning Tasks

**Properties:**
- Require interpretation, judgment, or synthesis
- Multiple valid outputs exist
- Quality is evaluated qualitatively
- Benefit from broad context and pattern recognition
- Answers "what," "why," and "how" questions

**Best actor:** Human judgment or LLM reasoning

**Examples:** Classifying items, explaining relationships, comparing options, generating insights, judging quality, synthesizing information

### Precision Tasks

**Properties:**
- Have exactly one correct output
- Quality is evaluated binary (right/wrong)
- Require deterministic operations (arithmetic, string matching, formatting)
- Don't benefit from "creativity" — correctness is the only criterion
- Answers "where exactly," "how many," and "what precisely" questions

**Best actor:** Code

**Examples:** Counting items, calculating percentages, extracting exact text, formatting output, verifying data against source, enforcing structural constraints

### Creative Tasks

**Properties:**
- Require generating novel output
- No single "correct" answer — quality is subjective
- Benefit from exploration and iteration
- Constrained by requirements but not determined by them

**Best actor:** Human with AI assistance

**Examples:** Designing interfaces, writing prose, choosing names, defining strategy

### Discovery Tasks

**Properties:**
- Don't know what you're looking for until you find it
- Require exploring a space before defining the problem
- Output is understanding, not a deliverable
- Often change the problem definition

**Best actor:** Human exploration (possibly AI-assisted)

**Examples:** Understanding a new codebase, investigating a bug, researching a domain, figuring out what users actually need

---

## The Key Insight: Mixed Tasks Fail

Most real-world tasks are **mixtures** of these types. The mixture is invisible until something breaks.

```
"Analyze this data and produce a report"

Actually contains:
├── Identify patterns in data         (REASONING)
├── Extract exact supporting data     (PRECISION)
├── Calculate summary statistics      (PRECISION)
├── Explain what the patterns mean    (REASONING)
├── Format as structured document     (PRECISION)
└── Write executive summary           (CREATIVE)
```

When you give this entire task to one actor:
- A human does everything but makes arithmetic errors and formatting inconsistencies
- An AI does everything but fabricates data points and makes structural errors
- Code can't do the reasoning or creative parts at all

**No single actor can handle all task types well.** The solution is decomposition along type boundaries.

---

## The Principle: Decompose Before Assigning

Before deciding HOW to do something or WHO does it, classify WHAT each sub-task actually is:

### Step 1: List every discrete sub-task

Be granular. "Analyze the data" is too coarse. Break it into:
- Read and parse input data (PRECISION)
- Identify potential patterns (REASONING)
- Verify patterns against data (PRECISION)
- Explain pattern significance (REASONING)
- etc.

### Step 2: Classify each sub-task

For each sub-task, ask:
- Does it have exactly one correct answer? → PRECISION
- Does it require interpretation or judgment? → REASONING
- Does it require generating something novel? → CREATIVE
- Do we not know what we're looking for? → DISCOVERY

### Step 3: Assign each sub-task to the right actor

| Task Type | Best Actor | Why |
|---|---|---|
| REASONING | LLM or human | Requires pattern matching and judgment |
| PRECISION | Code | Must be deterministic and verifiable |
| CREATIVE | Human (AI-assisted) | Requires taste, intent, and stakeholder alignment |
| DISCOVERY | Human (AI-assisted) | Requires changing the problem definition |

### Step 4: Design the handoff points

Where reasoning output feeds into precision processing (or vice versa), define the interface clearly:

```
REASONING (LLM): "The key pattern involves items X, Y, Z
                  located approximately in sections 2 and 4"
    ↓
HANDOFF: LLM outputs plain text description of findings
    ↓
PRECISION (code): Search for X, Y, Z in sections 2 and 4
                  Extract exact data, calculate statistics
    ↓
HANDOFF: Code outputs structured data with verified values
    ↓
REASONING (LLM): "Given this verified data, here's what
                  it means and why it matters"
```

---

## Exploration Before Execution

A meta-principle for task design:

> **You must understand the problem before you can decompose it correctly.**

This seems obvious, but it's routinely violated. Teams jump to architecture before understanding what they're building. Developers start coding before confirming the approach works. AI users write elaborate prompts before testing on a real case.

### The Exploration Stages

```
1. PROBLEM DEFINITION
   "Can I state what we're solving in one sentence?"
   If no → keep exploring

2. DECOMPOSITION
   "What are the sub-problems? What do I need to know?"
   If unclear → keep exploring

3. PATTERN RECOGNITION
   "What approach will work? Have I tested it on a real case?"
   If untested → keep exploring

4. TASK CLASSIFICATION
   "What type is each sub-task? Who should do it?"
   If mixed tasks remain → decompose further

5. EXECUTION
   "Build it following the confirmed pattern."
   Only now.
```

**The trap:** Exploration feels unproductive. "We're not building anything yet." But execution without exploration builds the wrong thing — and rebuilding costs more than exploring.

### Real Case First

Never decompose in the abstract. Always start with one concrete, real example:

| Abstract (dangerous) | Concrete (safe) |
|---|---|
| "Design a validation system" | "Validate this specific input, then generalize" |
| "Build a data pipeline" | "Process this one file end-to-end, then extract the pattern" |
| "Create a reporting framework" | "Produce this one report manually, then automate" |

The real case forces you to confront specifics that abstract planning misses. It reveals hidden assumptions, exposes task type mixtures, and provides test data for verification.

---

## LLM Output Is Hypothesis

A critical mental model for AI-assisted task design:

> **Every LLM output is a hypothesis until verified by execution.**

"This should work" from an AI means:
- The logic seems sound
- The approach looks reasonable
- **It has not been tested on real data**

Treat every AI suggestion, design, and code generation as hypothesis. The verification step is not optional — it's where you discover whether the task decomposition was correct.

```
AI: "Here's the solution"
You: "This is a hypothesis"
     → Test on real case
     → Measure result
     → If it works: hypothesis confirmed
     → If it doesn't: re-examine task decomposition
```

---

## Task Design Anti-Patterns

### The Monolith Prompt

Giving everything to the AI in one shot:
```
"Read this data, analyze it, extract key points, calculate stats,
 format as JSON, and explain your reasoning."
```

Fix: Decompose into separate calls, with code handling precision between them.

### The Infinite Loop

Asking the AI to iterate until "it's good enough":
```
"Keep improving this until it's perfect"
```

Fix: Define concrete success criteria. Measure against them. Stop when criteria are met.

### The Abstraction Trap

Designing systems for hypothetical future requirements:
```
"Build a flexible framework that can handle any type of analysis"
```

Fix: Build for the concrete case you have. Generalize only when a second case arrives and you can see the real pattern.

### The Rabbit Hole

Spending increasing effort on diminishing returns:

| Signal | What's Happening |
|---|---|
| "This changes everything" | Probably doesn't |
| Same problem reframed 3+ times | Lost the thread |
| 20+ iterations with no measurable improvement | Wrong approach |
| Building infrastructure for hypothetical use | Premature abstraction |

Fix: State the original problem. Ask "what's the simplest thing that could work?" Test it.

---

## Test Yourself

Before proceeding to the Prototype Building and R/P Split skills, you should be able to answer:

1. Why does giving a mixed task to a single actor produce unreliable results?
2. What's the difference between a reasoning task and a precision task?
3. Why should you test on a real case before decomposing into sub-tasks?
4. What does "LLM output is hypothesis" mean for your workflow?
5. How do you design handoff points between reasoning and precision steps?

If these feel clear, proceed to [Prototype Building](../skills/prototype-building.md) and [R/P Split](../skills/rp-split.md).

---

## References

- Simon, H. (1969). "The Sciences of the Artificial" — decomposition as a design strategy
- Brooks, F. (1975). "The Mythical Man-Month" — conceptual integrity and task allocation
- Polya, G. (1945). "How to Solve It" — problem-solving stages (understand → plan → execute → reflect)
- Kahneman, D. (2011). "Thinking, Fast and Slow" — System 1 (fast, heuristic) vs System 2 (slow, deliberate) mapping to task types
