# Architectural Patterns: Conversation Notes

**Date:** 2026-02-21
**Context:** Discussion connecting this project's design decisions to named software architecture patterns and manufacturing theory.

---

## 1. Issues #25/#26: From Linear Gates to Hierarchical Classification

**The transition:** The classification pipeline moved from linear, sequential gate checks to a priority-ordered, hierarchical system where rules declare their match conditions and the engine resolves conflicts by priority.

**What this is called:**

| Layer | Pattern name |
|-------|-------------|
| Base GoF pattern | **Chain of Responsibility** — each handler either claims the input or passes it on |
| What it evolved into | **Rule Engine** (also: Business Rules Engine / Production Rule System) |
| The conceptual shift | **Imperative → Declarative** — rules declare what they match; the engine handles priority and dispatch |

**Key properties of the evolved system:**
- Rules are **declarative** (each rule states its match conditions, not how to check them)
- A **priority/precedence** order determines which rule fires first
- **First-match wins** semantics (called "conflict resolution strategy" in rule engine literature)

**In this codebase specifically:** The 7-tier priority order (lookup → Reference → Satellite → user tag → Core → Popcorn → Unsorted) is a textbook priority-ordered production rule system. Issue #25 tightened the precision of individual rule conditions (director matching, country codes) — the standard maintenance work a rule engine requires once its architecture is established.

---

## 2. Theory of Constraints + Kanban: Do They Conflict?

**Answer: No — they are complementary and operate at different levels.**

From `constraint-theory.md`:
> TOC tells you WHERE the constraint is. Kanban tells you HOW to protect it.

| Theory | Question it answers | Level |
|--------|--------------------|----|
| Theory of Constraints (TOC) | Where is value being destroyed? | Strategic (system-wide) |
| Kanban (pull/andon cord) | How do you stop defective work from propagating? | Tactical (boundary-level) |

**A surface tension exists** — TOC says "don't optimize non-bottlenecks," Kanban says "add quality gates at every boundary." These seem to conflict. Resolution: gates cost $0 (they read checkpoint files). TOC's "don't optimize non-bottlenecks" applies to expensive work (API calls, pipeline stages). A $0 gate at every handoff doesn't violate TOC — it's precisely how you *find* the binding constraint cheaply before spending money on expensive stages.

**Historically:** Both theories emerged from Toyota's production system in adjacent decades (Ohno's Kanban 1950s, Goldratt's TOC formalization 1984). Kanban's WIP limits *are* the implementation of TOC's "subordinate everything to the constraint" — you slow upstream to match the bottleneck's rate. They're different framings of the same insight: system throughput is set by the constraint, not by local station speed.

---

## 3. Do TOC + Kanban Conflict with the Rule Engine Pattern?

**Answer: No — they apply at different domains entirely.**

The full pipeline in this codebase is:

```
Parse → TMDb → OMDb → Merge → [Rule Engine] → Output
        ←── enrichment stages ──→   routing stage
```

- **Rule Engine** answers: *"Given this film's data, which category does it belong to?"*
  Architecture of a single stage (routing). Intra-stage logic.

- **TOC + Kanban** answer: *"Across many films flowing through the full pipeline, where is quality being destroyed?"*
  Inter-stage flow and bottleneck location. The enrichment→routing handoff.

They don't compete — they apply at different boundaries.

**A subtler point:** TOC can also be applied *within* the rule engine at finer granularity. If 80% of films fail at Satellite routing (rule tier 3), that's the binding constraint inside routing — don't spend effort improving the lookup stage (tier 1) that's already working. Not a conflict, just TOC applied at smaller scope.

**The only genuine tension** would be applying Kanban's stop-the-line principle *inside* the rule engine — halting evaluation mid-chain if an intermediate rule produces bad output. That would break first-match-wins semantics. Nobody in this knowledge base suggests doing that.

---

## Summary Table

| Pattern | Question it answers | Where it applies in this project |
|---------|--------------------|---------------------------------|
| **Rule Engine / Production Rule System** | How should routing logic be structured? | Stages 5–8 of `classify.py` (routing) |
| **Theory of Constraints** | Where in the pipeline is quality being destroyed? | Finding which enrichment→routing handoff is the bottleneck |
| **Kanban / pull-based gates** | How do we prevent bad data from compounding through stages? | `scripts/validate_handoffs.py`; cost-ordered gate checks ($0 before $$) |

Three different questions. Three compatible answers. No conflicts.
