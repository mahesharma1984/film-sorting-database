# System Boundary Theory: Why Multi-Stage Systems Need Explicit Boundaries

**Read this before:** Boundary-Aware Measurement skill
**Core question:** In a multi-stage pipeline, where should you draw the line between "analysis" and "output" — and what happens if you don't?

---

## The Common Assumption

Most developers think about pipelines as linear sequences. Data enters Stage 1, flows through Stages 2-5, and exits as output. The mental model is:

1. **"A pipeline is a chain"** — each stage feeds the next; there are no meaningful groupings
2. **"Test the whole thing"** — quality is measured on the final output
3. **"Change anything, rerun everything"** — any modification requires a full pipeline run

In small pipelines (2-3 stages, fast execution), these work fine. In multi-stage systems — especially those where some stages are expensive (API calls, human review) and others are cheap (code-only validation) — treating the pipeline as a single undifferentiated chain leads to wasted resources, coupled evolution, and diagnostic confusion.

---

## The Failure That Reveals the Truth

A pipeline has 8 stages. Stages 1-4 analyze data and build an internal model. Stages 5-8 use that model to produce deliverable output. Stage 5 involves expensive API calls ($2-5 per run). Stage 8 formats output for human consumption.

The team makes a change to Stage 3 (an analysis improvement). To test it, they run the full 8-stage pipeline. Stage 5's API calls cost $4. The output looks good. They repeat this cycle 15 times during development — $60 spent on API calls.

Later, someone realizes that their Stage 3 change **only affected the internal model**. Stages 5-8 would have produced the same output regardless, because the change was within the analysis half. They could have tested by running Stages 1-4 only and inspecting the model output — $0 cost, 10x faster feedback.

**Three failures:**
1. **No explicit boundary** — nobody recognized that Stages 1-4 and Stages 5-8 had different purposes
2. **Monolithic testing** — every change required running the entire pipeline
3. **Wasted resources** — $60 in API calls that provided no information

---

## The Mental Model: Natural Boundaries

### Where Boundaries Exist

Multi-stage pipelines have natural boundaries wherever the **purpose** of the output changes. The most common boundary is:

```
ANALYSIS (understanding)          DELIVERY (producing)
Stages that build an              Stages that produce
internal model of the data        consumable output from the model
                │
                ├── Reusable across applications
                ├── Testable without downstream stages
                └── Changes stay contained

                     ◄── BOUNDARY ──►

                                      │
                                      ├── Application-specific
                                      ├── Depends on analysis output
                                      └── Can change independently
```

**The boundary is where the pipeline switches from "understanding the data" to "producing something from that understanding."**

### Signs a Boundary Exists

| Signal | What It Means |
|---|---|
| Cost cliff | Stages before the boundary are cheap ($0 code); stages after are expensive ($$ API/human) |
| Reuse potential | Analysis output could serve multiple downstream applications |
| Change independence | Changes to analysis rarely require changes to delivery, and vice versa |
| Testing asymmetry | Analysis can be tested without running delivery; delivery can't run without analysis |
| Purpose shift | Stages before answer "what is this?"; stages after answer "what do I produce from it?" |

### The Boundary Contract

At the boundary, define an explicit contract — what crosses from analysis to delivery:

```
ANALYSIS OUTPUT (the model):
  ├── Verified patterns with supporting evidence
  ├── Classifications with confidence levels
  ├── Relationships between entities
  └── Structural properties of the dataset

DELIVERY INPUT (what it needs):
  ├── Which patterns to include in output
  ├── How to prioritize/sequence patterns
  ├── Where to find evidence (pointers, not full extraction)
  └── Quality thresholds for inclusion

CONTRACT:
  "Analysis provides a verified model.
   Delivery produces output from that model.
   Analysis does not know about delivery format.
   Delivery does not modify the model."
```

**The key property:** Analysis output is format-agnostic. It's a model of the data, not a pre-formatted deliverable. This means the same analysis can feed multiple delivery pipelines (different output formats, different audiences, different scoping decisions).

---

## The Principle: Explicit Boundaries Enable Independent Evolution

### Principle 1: Identify the Boundary

Every multi-stage pipeline with 4+ stages has at least one natural boundary. Find it by asking: "Where does the pipeline switch from understanding to producing?"

If no clear answer exists, look for the cost cliff — the point where stage execution cost jumps significantly. The boundary is usually immediately before the first expensive stage.

### Principle 2: Define the Contract

The boundary needs an explicit contract that specifies:

1. **What analysis provides** — the model shape, required fields, quality guarantees
2. **What delivery expects** — the inputs it needs, what it does and doesn't modify
3. **What doesn't cross** — format-specific decisions stay in delivery; model decisions stay in analysis

### Principle 3: Measure Each Side Independently

This is the highest-leverage consequence of explicit boundaries:

```
ANALYSIS METRICS (measured on the model):
  ├── Completeness: Does the model capture what's in the data?
  ├── Accuracy: Are classifications correct?
  ├── Consistency: Do similar inputs produce similar models?
  └── Survival: Does upstream data survive to the model?

DELIVERY METRICS (measured on the output):
  ├── Fidelity: Does the output faithfully represent the model?
  ├── Coverage: Does the output include what the model provides?
  ├── Format quality: Is the output well-structured for its audience?
  └── Extraction accuracy: Are located evidence items correctly extracted?
```

**Why this matters:** If a delivery metric fails, you need to know whether the failure is in delivery (output production) or analysis (the model was wrong). Without boundary-scoped measurement, you can't distinguish these cases.

### Principle 4: Gate Expensive Stages Behind Cheap Validation

The most practical benefit of boundaries: **don't run expensive stages until cheap stages have been validated.**

```
Cost ordering:
  $0    Analysis stages (code-only)
  $0    Boundary validation (model inspection)
  $$    Delivery stages (API calls, extraction)
  $$$   Full measurement (end-to-end quality)

Rule: Never spend $$ on delivery when $0 boundary
      validation would have caught the problem.
```

This is the cost-ordering principle from Constraint Theory applied specifically to boundaries.

---

## Two-Pass Semantics

Many boundaries involve a natural two-pass pattern:

### Pass 1: Abstract Recognition (REASONING)

The analysis half identifies patterns, categories, and relationships. This is a REASONING task — synthesizing patterns from data, making judgment calls about relevance, classifying entities.

```
Input: Raw data
Output: Abstract model (patterns, classifications, priorities)
Task type: REASONING (LLM excels)
Cost: $-$$ (LLM call)
```

### Pass 2: Concrete Extraction (PRECISION)

The delivery half extracts specific evidence, formats output, and produces deliverables. This is a PRECISION task — finding exact passages, copying verbatim, enforcing format constraints.

```
Input: Abstract model + raw data
Output: Formatted deliverable with extracted evidence
Task type: PRECISION (code excels) + REASONING (LLM for interpretation)
Cost: $$-$$$ (LLM calls + code)
```

**Why this matters:** The R/P Split is especially important at boundaries. Analysis is primarily REASONING (pattern recognition, classification). Delivery is primarily PRECISION (exact extraction, formatting). Treating them the same leads to either:
- Asking the LLM to do precision extraction during analysis (hallucination risk)
- Asking code to do pattern recognition during delivery (capability mismatch)

The boundary naturally separates the REASONING pass from the PRECISION pass.

---

## When Boundaries Don't Exist

Not every pipeline has a natural boundary:

| Situation | Boundary Status |
|---|---|
| 2-3 stages, all cheap | No boundary needed — run everything |
| Linear transformation pipeline (convert → validate → format) | No analysis/delivery distinction |
| Single-purpose pipeline (one input, one output, one format) | Boundary may exist but separation adds no value |
| Streaming pipeline (real-time, event-driven) | Boundaries are event-based, not stage-based |

**Signs you shouldn't add a boundary:**
- All stages have similar cost
- Analysis and delivery are tightly coupled (analysis output IS the delivery format)
- The pipeline has only 2-3 stages
- You can't articulate what the "model" would be

---

## Deeper: Why Coupled Pipelines Drift

Without explicit boundaries, a pipeline tends to develop implicit coupling between its analysis and delivery halves:

1. **Delivery assumptions leak into analysis:** Analysis starts producing output formatted for one specific delivery format, making it unusable for other formats.

2. **Analysis models get modified by delivery:** Delivery stages start "adjusting" the model to fit output requirements, corrupting the analysis for other uses.

3. **Testing becomes monolithic:** Every change requires a full pipeline run because there's no intermediate checkpoint to validate.

4. **Debugging becomes archeological:** When output quality drops, you have to trace through every stage because there's no clear point where "the model is correct but the output is wrong" or "the model is wrong so the output must be wrong."

**Explicit boundaries prevent all four** by establishing a stable contract at the midpoint. Analysis evolves independently. Delivery evolves independently. The contract is the only shared surface.

---

## Deeper: The Reuse Test

The strongest signal that a boundary should be explicit: **could the analysis half serve a different application?**

If your pipeline analyzes data and then produces a specific output format, ask: "Could someone else use the analysis output to produce a *different* output format?" If yes, the analysis half is a reusable model, and you should treat the boundary explicitly.

Examples:
- **Yes boundary:** A data analysis pipeline that builds a classified model, then generates reports. The model could also feed a dashboard, an API, or a different report format.
- **Yes boundary:** An NLP pipeline that identifies patterns in text, then produces teaching materials. The pattern model could also feed a search index, a summary generator, or a comparison tool.
- **No boundary:** A file converter that reads CSV, validates, and writes JSON. There's no "model" — it's a linear transformation.

---

## Connection to Other Knowledge Base Concepts

| Concept | Connection to System Boundary Theory |
|---|---|
| **Measurement Theory** | Boundary-scoped measurement prevents metric confusion. Analysis metrics and delivery metrics are tracked independently. |
| **Constraint Theory** | The boundary is often where the binding constraint hides. Cheap validation at the boundary catches upstream defects before expensive downstream stages run. |
| **Failure Theory** | Hard gates at the boundary catch the most costly failures — corrupt analysis models that would waste expensive delivery stage runs. |
| **LLM Capability Model** | Boundaries naturally align with R/P Split: analysis = REASONING (LLM), delivery = PRECISION (code) + REASONING (LLM). |
| **Causality & Systems** | The boundary enforces information direction: analysis → model → delivery. Delivery cannot modify the model (reverse causality). |

---

## Test Yourself

Before proceeding to the Boundary-Aware Measurement skill, you should be able to answer:

1. How do you identify a natural boundary in a multi-stage pipeline?
2. Why is measuring analysis and delivery independently more useful than measuring the whole pipeline?
3. What does the boundary contract specify, and why does analysis not know about delivery format?
4. How does the cost-ordering principle apply to boundaries?
5. What's the two-pass pattern, and how does it relate to R/P Split?
6. When should you NOT add a boundary?

If these feel clear, proceed to [Boundary-Aware Measurement](../skills/boundary-aware-measurement.md).

---

## References

- Parnas, D.L. (1972). "On the Criteria To Be Used in Decomposing Systems into Modules" — Information hiding; modules with stable interfaces
- Bass, L., Clements, P., & Kazman, R. (2012). *Software Architecture in Practice.* — Architectural boundaries, quality attribute scenarios
- Fowler, M. (2002). "Patterns of Enterprise Application Architecture" — Layered architecture, service boundaries
- Halliday, M.A.K. (1985). *An Introduction to Functional Grammar.* — Metafunctions as independent analytical dimensions
- This repository's measurement data: Kernel-pedagogical boundary (v11.0+), boundary-aware measurement (Issue #421)
