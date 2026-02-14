# Skill: R/P Split (Reasoning-Precision Task Allocation)

**Purpose:** Correctly allocate tasks between AI/LLMs and code based on task type.
**Addresses:** The #1 failure mode in AI-assisted systems — giving precision tasks to LLMs.

---

## Core Principle

**LLMs reason well but handle precision poorly.**

| Task Type | LLM Reliability | Give To |
|---|---|---|
| REASONING | High | LLM (Claude, GPT, etc.) |
| PRECISION | Low | Code |

When something fails in an AI-assisted system, the cause is almost always: **a precision task assigned to the LLM instead of code.**

---

## Task Classification

### Reasoning Tasks (Give to LLM)

| Category | Examples | Why Reasoning |
|---|---|---|
| Classification | "Is this category A or B?" | Requires interpretation |
| Interpretation | "What does this mean?" | Multiple valid answers |
| Synthesis | "How do these pieces combine?" | Integrative judgment |
| Explanation | "Why does this work this way?" | Conceptual understanding |
| Judgment | "Which option is better?" | Comparative assessment |
| Ranking | "Order these by importance" | Relative evaluation |

**Characteristics:**
- Answers "what" and "why" questions
- Output is semantic, conceptual
- Multiple valid answers possible
- Evaluation is qualitative

### Precision Tasks (Give to Code)

| Category | Examples | Why Precision |
|---|---|---|
| Exact extraction | "Copy these exact words from the source" | Must match source exactly |
| Counting | "How many items are there?" | Only one correct answer |
| Calculation | "What percentage is X out of Y?" | Mathematical operation |
| Format compliance | "Output valid JSON/XML/CSV" | Structural correctness |
| Position tracking | "What's at position N?" | Deterministic lookup |
| String search | "Find where this phrase appears" | Pattern matching |
| Verification | "Does this string exist in the source?" | Boolean check |

**Characteristics:**
- Answers "where exactly" and "how many" questions
- Output must match ground truth exactly
- Only one correct answer exists
- Evaluation is binary (right/wrong)

### The Danger Zone: Mixed Tasks

Mixed tasks look like one thing but contain both types:

| Appears To Be | Actually Contains | Problem |
|---|---|---|
| "Find items and describe them" | Identify (R) + Extract exact text (P) + Format output (P) | LLM hallucinate details |
| "Analyze and output structured data" | Analysis (R) + JSON formatting (P) | Malformed output |
| "Count and explain" | Counting (P) + Explanation (R) | Wrong counts with good explanations |

**Rule: If a task contains ANY precision component, split it.**

---

## Decision Framework

```
                    START
                      │
                      ▼
        ┌─────────────────────────────┐
        │ Does the task require       │
        │ interpretation, judgment,   │
        │ or explanation?             │
        └─────────────────────────────┘
                      │
              ┌───────┴───────┐
              │ YES           │ NO
              ▼               ▼
        ┌───────────┐   ┌───────────────────────┐
        │ REASONING │   │ Does the task have    │
        │ → LLM     │   │ exactly one correct   │
        └───────────┘   │ answer?               │
                        └───────────────────────┘
                              │
                      ┌───────┴───────┐
                      │ YES           │ NO
                      ▼               ▼
                ┌───────────┐   ┌───────────────┐
                │ PRECISION │   │ Probably      │
                │ → Code    │   │ REASONING     │
                └───────────┘   │ → LLM         │
                                └───────────────┘
```

### Splitting Mixed Tasks

When a task contains both reasoning and precision:

1. **Identify the reasoning core** — What judgment is needed?
2. **Identify the precision wrapper** — What exact output is required?
3. **Split at the boundary:**
   - LLM provides reasoning output (plain text, flexible format)
   - Code transforms to precision output (exact format, verified content)

**Example:**
```
Mixed: "Extract a matching quote and explain its significance"
  ↓
Split:
  LLM:  "Describe where the relevant passage is and why it matters"
  Code: Search source for described passage, extract exact text
  LLM:  "Given this verified quote, explain its significance"
  Code: Assemble structured output from verified parts
```

---

## The Trap

LLMs are confident. They don't say "I can't extract exact data reliably." They attempt any task and produce plausible-looking output.

**You can't tell from the output that it's wrong.** A hallucinated quote looks exactly like a real one. A miscounted total looks like any other number.

The only defense:
1. Understand capability limits beforehand
2. Design systems that don't rely on LLM precision
3. Verify precision outputs with code

---

## Diagnostic Procedure

When something fails in your AI-assisted system:

```
MEASURE → Which output is wrong?
    │
    ▼
TRACE → Which stage/component produces this output?
    │
    ▼
DECOMPOSE → What tasks does that component perform?
    │
    ▼
CLASSIFY → Is each task Reasoning or Precision?
    │
    ▼
AUDIT → Who's doing each task? (LLM or Code?)
    │
    ▼
FIX → Move misallocated tasks to correct actor
    │
    ▼
VERIFY → Re-run, check improvement
```

### Recursive Application

When a failure is found, ask "Is this reasoning or precision?" at each level until you find the root misallocation:

```
Component X produces wrong output
  → Sub-component Y fails
    → Is Y's task R or P? → Precision (code) ✓
    → Why does it fail? → Bad input from Z
      → Is Z's task R or P? → Precision (asking LLM for exact data)
      → ROOT CAUSE: Precision task given to LLM in Z
```

The failure is often one or two levels deeper than it appears.

---

## Checklist

Before any LLM API call:
- [ ] Listed all tasks in this call
- [ ] Categorized each as reasoning or precision
- [ ] Moved precision tasks to code
- [ ] LLM outputs flexible text (not rigid format)
- [ ] Code handles parsing/formatting
- [ ] Verification step for any extracted content

---

## Key Insight

**REASONING tasks benefit from PRECISION context.** When code can cheaply generate helpful context (templates, search results, pre-computed data), feed it to the LLM. The LLM reasons better with good context — and the context generation costs $0 (it's just code).

```
PRECISION stage (code, $0):    Generate focused guidance/context
    ↓
REASONING stage (LLM, $$$):   Use context to reason better
    ↓
PRECISION stage (code, $0):    Verify and format output
```

This three-step pattern — Context → Reasoning → Verification — is the most reliable architecture for AI-assisted tasks.

---

## Quick Reference

| If the task involves... | It's probably... | Give to... |
|---|---|---|
| Identifying, classifying | REASONING | LLM |
| Interpreting, explaining | REASONING | LLM |
| Judging, ranking, comparing | REASONING | LLM |
| Synthesizing, deriving | REASONING | LLM |
| Copying exact text | PRECISION | Code |
| Counting anything | PRECISION | Code |
| Calculating percentages | PRECISION | Code |
| Formatting output (JSON, etc.) | PRECISION | Code |
| Verifying existence | PRECISION | Code |
| String searching | PRECISION | Code |
