# Skills: Composable Development Methodologies

## What Are Skills?

Skills are self-contained methodology modules that you can adopt independently or compose together. Each skill addresses a specific category of development challenge.

## Available Skills

| Skill | Addresses | Core Question |
|---|---|---|
| [R/P Split](rp-split.md) | Task allocation between AI and code | "Who should do this — the LLM or code?" |
| [Pattern-First](pattern-first.md) | Dependency ordering and causality | "What must exist before I populate instances?" |
| [Measurement-Driven](measurement-driven.md) | Quality cycles across depth and breadth | "Did this change help, and did it break anything?" |
| [Failure Gates](failure-gates.md) | Pipeline reliability and failure semantics | "Should this failure stop everything or just warn?" |
| [Prototype Building](prototype-building.md) | Exploration → execution methodology | "Am I building the right thing before building it right?" |

## Composition Guide

### Minimal Setup (Any Project)
- **Prototype Building** — Establishes exploration-before-execution discipline

### AI/LLM Projects
- **R/P Split** — Prevents the #1 failure mode in AI systems (precision tasks given to LLMs)
- **Pattern-First** — Prevents post-hoc rationalization in generated outputs
- **Measurement-Driven** — Catches regressions across versions

### Staged Pipeline Projects
- **Pattern-First** — Enforces correct dependency ordering between stages
- **Failure Gates** — Defines what stops the pipeline vs what warns
- **Measurement-Driven** — Tracks quality across depth (single case) and breadth (all cases)

### Full Stack (Complex Systems)
All five skills compose into a complete methodology:

```
Prototype Building (exploration discipline)
    ↓ confirms approach
Pattern-First (dependency ordering)
    ↓ structures pipeline
R/P Split (task allocation)
    ↓ assigns work correctly
Failure Gates (reliability semantics)
    ↓ prevents cascading failures
Measurement-Driven (quality cycles)
    ↓ validates changes
STABLE SYSTEM
```

## How Skills Relate

```
                    MEASUREMENT-DRIVEN
                    (the development cycle)
                            │
            ┌───────────────┼───────────────┐
            │               │               │
            ▼               ▼               ▼
       R/P SPLIT      PATTERN-FIRST    FAILURE GATES
      (adjustment     (adjustment      (reliability
       strategy:       strategy:        strategy:
       task            causality        failure
       allocation)     ordering)        semantics)
            │               │               │
            └───────────────┼───────────────┘
                            │
                            ▼
                    PROTOTYPE BUILDING
                    (exploration before
                     execution)
```

- **Measurement-Driven** is the orchestration layer — it tells you *when* to look at quality
- **R/P Split, Pattern-First, Failure Gates** are adjustment strategies — they tell you *how* to fix problems
- **Prototype Building** is the foundation — it ensures you understand before you build

## Adopting Skills

1. Read the skill document
2. Copy the decision rules into your CLAUDE.md (use the template)
3. Add the diagnostic procedures to your debug runbook
4. Apply the principles when reviewing code and making architecture decisions

Skills don't require tooling — they're thinking frameworks that improve decision-making.
