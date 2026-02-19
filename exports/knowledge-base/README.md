# Knowledge Base: Theoretical Foundations

**Read these BEFORE the skills.** The skills are procedures; the knowledge base is understanding. Without the theory, the skills become cargo cult — rules followed without comprehension, misapplied in novel situations, and abandoned when they don't obviously fit.

---

## Why Theory First

This repository's methodologies weren't designed in the abstract. They emerged from failures:

1. A pipeline hallucinated 50% of its output → discovery that LLMs can't do precision tasks → R/P Split
2. Output looked good but was built on backwards causality → discovery that dependency direction determines quality → Pattern-First
3. Fixing one case broke three others → discovery that quality has two axes → Measurement-Driven Development
4. A "STRONG" quality score masked a broken process → discovery that metrics measure output, not process → Failure Gates
5. Teams kept building the wrong thing → discovery that exploration must precede execution → Prototype Building

**Each skill encodes the fix. The knowledge base explains the failure that made the fix necessary.** If you only learn the fix, you'll apply it mechanically. If you understand the failure, you'll recognize when the same category of failure appears in a new form.

---

## Reading Order

The knowledge base documents build on each other:

```
1. LLM Capability Model
   "What can AI actually do?"
   ↓ establishes the fundamental constraint

2. Task Design Theory
   "How do you decompose work given these constraints?"
   ↓ establishes the decomposition method

3. Causality & Systems Thinking
   "How do you order the decomposed tasks?"
   ↓ establishes the ordering principle

4. Domain Grounding Theory
   "How do you classify entities consistently?"
   ↓ establishes the classification method

5. System Boundary Theory
   "Where do you draw the line in a multi-stage system?"
   ↓ establishes the boundary principle

6. Measurement Theory
   "How do you know if the ordered tasks are working?"
   ↓ establishes the verification method

7. Failure Theory
   "What happens when they don't work?"
   ↓ establishes the failure handling principle

8. Constraint Theory
   "When something's wrong, how do you find WHERE to fix?"
   ↓ establishes the constraint identification method
```

Each document follows the same structure:
1. **The common assumption** — what most people believe
2. **The failure** — what goes wrong when you act on that assumption
3. **The mental model** — the correct way to think about it
4. **The principle** — the rule that follows from the model
5. **Test yourself** — questions to verify understanding before moving to the skill

---

## Documents

| # | Document | Core Question | Leads To Skill |
|---|---|---|---|
| 1 | [LLM Capability Model](llm-capability-model.md) | What can AI actually do vs what does it fake? | R/P Split |
| 2 | [Task Design Theory](task-design-theory.md) | How does decomposition determine outcome quality? | Prototype Building, R/P Split |
| 3 | [Causality & Systems](causality-and-systems.md) | Why does dependency direction matter? | Pattern-First |
| 4 | [Domain Grounding Theory](domain-grounding-theory.md) | How do you design classification systems that stay consistent? | Domain Grounding |
| 5 | [System Boundary Theory](system-boundary-theory.md) | Where should you draw the line in a multi-stage system? | Boundary-Aware Measurement |
| 6 | [Measurement Theory](measurement-theory.md) | How do you know something is actually working? | Measurement-Driven Dev |
| 7 | [Failure Theory](failure-theory.md) | How do systems break silently? | Failure Gates |
| 8 | [Constraint Theory](constraint-theory.md) | When a pipeline underperforms, how do you find *what* to fix? | Constraint Gates |

---

## The Theory-Skill Relationship

```
LAYER 0: KNOWLEDGE BASE (understand)
├── LLM Capability Model     → understand the capability constraint
├── Task Design Theory        → understand decomposition
├── Causality & Systems       → understand ordering
├── Domain Grounding Theory   → understand classification design
├── System Boundary Theory    → understand pipeline boundaries
├── Measurement Theory        → understand verification
├── Failure Theory            → understand failure modes
└── Constraint Theory         → understand bottleneck identification
         │
         ▼
LAYER 1: SKILLS (apply)
├── R/P Split                 → apply capability constraint to task allocation
├── Prototype Building        → apply decomposition to exploration
├── Pattern-First             → apply ordering to dependencies
├── Domain Grounding          → apply classification design to taxonomies
├── Boundary-Aware Measurement → apply boundary principle to measurement scoping
├── Measurement-Driven Dev    → apply verification to development cycle
├── Failure Gates             → apply failure handling to pipeline design
└── Constraint Gates          → apply bottleneck identification to pipeline boundaries
         │
         ▼
LAYER 2: TEMPLATES (implement)
├── CLAUDE.md                 → encode skills as project instructions
├── WORK_ROUTER.md            → encode navigation patterns
├── DEBUG_RUNBOOK.md          → encode diagnostic procedures
├── WORKFLOW_REGISTRY.md      → encode named workflows
└── ...                       → encode other operational patterns
```

**Theory enables correct application.** Skills without theory produce people who follow rules but can't adapt to new situations. Theory without skills produces people who understand problems but can't act on them. You need both, starting with theory.

---

## When to Read What

| If you want to... | Start with... |
|---|---|
| Understand why AI systems fail | LLM Capability Model |
| Design a multi-step pipeline | Causality & Systems → Task Design Theory |
| Design a classification taxonomy | Domain Grounding Theory |
| Scope measurement to pipeline subsystems | System Boundary Theory |
| Set up quality tracking | Measurement Theory |
| Build a robust system | Failure Theory |
| Diagnose why fixing a stage doesn't help | Constraint Theory |
| Apply everything together | Read all eight in order, then the skills |

---

## How the Theory Was Discovered

Every principle in the knowledge base was discovered through the same cycle:

```
1. Build something that seems reasonable
2. Measure the output
3. Discover the measurement reveals a problem
4. Diagnose the root cause
5. Realize the root cause is a category of error, not a specific bug
6. Formalize the category into a principle
7. Apply the principle to prevent the entire category
```

This cycle repeated across 10+ versions of the reference project. The knowledge base captures step 6 — the formalized understanding. The skills capture step 7 — the applied prevention.

The honest version: every principle in this knowledge base was discovered by getting something wrong first. The documentation exists so you can learn from those failures without having to repeat them.
