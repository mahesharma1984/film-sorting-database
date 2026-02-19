# LLM Capability Model: What AI Can and Cannot Do

**Read this before:** R/P Split skill
**Core question:** What are the actual capabilities and limitations of large language models?

---

## The Common Assumption

Most people approach LLMs with one of two mental models:

1. **"It's smart, it can do anything"** — Treats the LLM as a general-purpose intelligence. Asks it to reason, extract, format, calculate, and verify all in one step.
2. **"It's unreliable, don't trust anything"** — Treats every output as suspect. Adds excessive validation, redundant checks, and manual review to everything.

Both are wrong. LLMs have a **specific capability profile** — reliably strong in some areas, reliably weak in others. Understanding this profile is the foundation for designing systems that work.

---

## The Failure That Reveals the Truth

A content processing pipeline asks an LLM: "Find relevant items in this text, quote them exactly, explain their significance, and format as JSON."

The output looks perfect. Well-structured JSON. Plausible quotes. Insightful explanations. You ship it.

Weeks later, someone checks the quotes against the source text. **Half of them don't exist.** The LLM generated text that *sounds like* it could be in the source — syntactically plausible, thematically relevant — but it's fabricated. The explanations are excellent analyses of fabricated evidence.

**Why wasn't this caught?** Because fabricated output is indistinguishable from real output by inspection. A hallucinated quote looks exactly like a real quote. A miscounted total looks like any other number. The only way to know is to verify against ground truth — which the LLM can't do either.

---

## The Mental Model: Asymmetric Capabilities

LLMs are **statistical pattern completion engines** trained on text. This architecture produces a specific, predictable capability profile:

### What LLMs Do Well: REASONING

| Capability | Why It Works | Examples |
|---|---|---|
| Classification | Pattern matching against training distribution | "Is this category A or B?" |
| Interpretation | Synthesizing patterns across context | "What does this passage suggest?" |
| Explanation | Generating coherent causal narratives | "Why does this approach work?" |
| Synthesis | Combining multiple inputs into coherent output | "How do these ideas connect?" |
| Judgment | Applying learned heuristics to novel cases | "Which option is more appropriate?" |
| Analogy | Mapping structure between domains | "This is like X because..." |

**Why these work:** They require integrating patterns across large contexts, weighing multiple interpretations, and producing outputs where multiple answers are valid. This is exactly what statistical pattern completion excels at.

**Characteristics of reasoning tasks:**
- Multiple valid answers exist
- Evaluation is qualitative ("good interpretation" vs "bad interpretation")
- Output is semantic and conceptual
- Answers "what," "why," and "how" questions

### What LLMs Do Poorly: PRECISION

| Capability | Why It Fails | Examples |
|---|---|---|
| Exact extraction | No mechanism to copy from input verbatim | "Quote these exact 10 words" |
| Counting | Token-by-token generation can't reliably count | "How many items in this list?" |
| Calculation | No arithmetic unit; simulates math via patterns | "What's 17.3% of 4,291?" |
| Format compliance | Can approximate but not guarantee structure | "Output valid JSON with no errors" |
| Position tracking | No index into input; processes sequentially | "What's at character 5,470?" |
| String matching | Pattern completion ≠ exact comparison | "Does this string appear in the text?" |
| Verification | Can't reliably check its own output against source | "Is this quote real or fabricated?" |

**Why these fail:** They require exact, deterministic operations — copying specific bytes, performing arithmetic, enforcing structural constraints. The LLM's generation mechanism (probabilistic next-token prediction) cannot guarantee exactness. It can get *close*, which is worse than getting it obviously wrong, because close looks correct.

**Characteristics of precision tasks:**
- Exactly one correct answer exists
- Evaluation is binary (right or wrong)
- Output must match ground truth exactly
- Answers "where exactly," "how many," and "what precisely" questions

---

## The Dangerous Middle: Confident Wrongness

The most important property of LLMs is not what they get wrong — it's that **they don't know they're wrong, and neither do you.**

```
You: "Extract the exact quote where the character first appears."
LLM: "Here is the quote: 'She walked into the room with a quiet
      determination that suggested she had been there before.'"
```

This quote:
- Sounds like it belongs in the text
- Uses the right character name
- Matches the narrative tone
- Is grammatically perfect
- **Does not exist in the source text**

The LLM generated a plausible completion, not an extraction. It has no mechanism for copying verbatim from its input context (beyond short, salient phrases). The statistical process that generates "walked into the room" is the same process that generates hallucinated content — there's no internal flag distinguishing "remembered from input" vs "generated from training."

### The Confidence Trap

LLMs do not express uncertainty proportional to their actual reliability:
- They'll attempt any task without caveats
- They'll produce precision outputs with the same fluency as reasoning outputs
- They'll format fabricated data identically to real data
- When asked "are you sure?", they'll typically confirm

**Implication:** You cannot use the LLM's self-assessment to determine output quality. External verification is required for any precision claim.

---

## The Principle

**Design systems around the capability profile, not against it.**

| Instead of... | Do this... |
|---|---|
| Asking the LLM to extract exact text | LLM describes location; code extracts |
| Asking the LLM to count items | LLM identifies items; code counts |
| Asking the LLM to format JSON | LLM outputs plain text; code formats |
| Asking the LLM to verify its output | Code verifies against source |
| Asking the LLM to do everything in one call | Split into reasoning calls + code steps |
| Trusting the LLM's self-assessment | Use external checks (tests, verification, measurement) |

The three-step pattern that emerges from this model:

```
1. CODE (precision, $0):     Prepare context for the LLM
2. LLM  (reasoning, $$$):    Reason about the context
3. CODE (precision, $0):     Verify and format the output
```

This is the **Context → Reasoning → Verification** architecture. It works because each actor does what it's good at.

---

## Deeper: Why Hallucination Is Structural

Hallucination is not a bug that will be fixed in the next model version. It's a structural property of how LLMs work:

1. **Training objective:** LLMs are trained to predict the next token given context. They learn what text *typically looks like*, not what's *true*.

2. **No grounding mechanism:** LLMs have no direct connection to source documents during generation. They process input into hidden states and generate from those states. There's no "copy from input" operation — only "generate what's likely given the hidden state."

3. **Distributional matching:** A hallucinated quote is often *more* typical of the source text's style than an actual quote. The LLM generates the platonic ideal of what a quote from this text would sound like, which can be more stylistically consistent than the actual text.

4. **No internal uncertainty signal:** The model's confidence (token probability) doesn't distinguish "I'm generating from training data" from "I'm generating from input context." Both use the same mechanism.

**What this means for system design:** Don't wait for LLMs to stop hallucinating. Design systems that don't depend on precision from LLMs. This isn't a temporary workaround — it's the correct architecture.

---

## Deeper: The Mixed Task Trap

The most common failure mode isn't asking an LLM to do something it can't do. It's asking it to do something it *can* do alongside something it *can't*:

```
"Analyze this data AND format it as a CSV"
        ↑ reasoning (good)    ↑ precision (bad)
```

The LLM will do both. The analysis will be insightful. The CSV will have formatting errors — missing commas, inconsistent quoting, wrong column count. But because the analysis is good, you're tempted to accept the whole output.

**Mixed tasks are the trap because the good part masks the bad part.**

Detection rule: If a task produces output where *part* is evaluated qualitatively ("is this a good analysis?") and *part* is evaluated exactly ("is this valid CSV?"), it's a mixed task. Split it.

---

## Implications for System Architecture

### 1. Separation of Concerns Is Not Optional

In traditional software, separating reasoning from data handling is a best practice. In AI-assisted systems, it's a **requirement**. The LLM physically cannot do both reliably. This isn't a design preference — it's a capability constraint.

### 2. Verification Cannot Be Omitted

In traditional software, you can sometimes skip validation for trusted internal components. In AI-assisted systems, **every precision output from an LLM must be verified by code.** The LLM is not a trusted internal component for precision tasks. It's an external, probabilistic source.

### 3. Architecture Determines Quality Ceiling

No amount of prompt engineering fixes a precision task assigned to an LLM. The ceiling is the model's statistical precision, which is typically 50-90% for extraction tasks and degrades with complexity. Moving the task to code raises the ceiling to 100%.

The architecture question — "who does this task?" — determines the quality ceiling before any code is written.

### 4. Context Improves Reasoning

While precision can't be prompt-engineered, reasoning quality responds strongly to context. LLMs reason *better* when given:
- Structured context (not raw dumps)
- Explicit criteria (not vague instructions)
- Relevant excerpts (not entire documents)
- Prior stage outputs (not starting from scratch)

This is why the Context → Reasoning → Verification pattern works: the code-prepared context makes the LLM's reasoning task easier and more focused.

---

## Test Yourself

Before proceeding to the R/P Split skill, you should be able to answer:

1. Why does a hallucinated quote look indistinguishable from a real one?
2. If an LLM produces valid JSON 90% of the time, why shouldn't you rely on it for JSON formatting?
3. What's the difference between "the LLM got it wrong" and "the LLM can't reliably do this"?
4. Why can't you fix precision failures with better prompts?
5. Why is a mixed task (reasoning + precision) more dangerous than a pure precision task?

If these answers feel obvious, good — you have the mental model. Proceed to [R/P Split](../skills/rp-split.md).

---

## References

- Bender, Gebru et al. (2021). "On the Dangers of Stochastic Parrots" — foundational critique of statistical language models
- Ji et al. (2023). "Survey of Hallucination in Natural Language Generation" — taxonomy of hallucination types
- Anthropic (2024-2026). Claude model documentation — capability profiles and known limitations
- This repository's measurement data: QVR tracking from v5.0 to v9.3 (50% → 95%+ after R/P Split)
