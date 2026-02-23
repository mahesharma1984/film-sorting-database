# Skills: Composable Development Methodologies

## What Are Skills?

Skills are self-contained methodology modules that you can adopt independently or compose together. Each skill addresses a specific category of development challenge.

## Available Skills

| Skill | Addresses | Core Question |
|---|---|---|
| [R/P Split](rp-split.md) | Task allocation between AI and code | "Who should do this — the LLM or code?" |
| [Pattern-First](pattern-first.md) | Dependency ordering and causality | "What must exist before I populate instances?" |
| [Domain Grounding](domain-grounding.md) | Classification taxonomy design | "Are my categories grounded in published theory?" |
| [Boundary-Aware Measurement](boundary-aware-measurement.md) | Scoped quality across system boundaries | "Am I measuring the right subsystem at the right cost?" |
| [Measurement-Driven](measurement-driven.md) | Quality cycles across depth and breadth | "Did this change help, and did it break anything?" |
| [Failure Gates](failure-gates.md) | Pipeline reliability and failure semantics | "Should this failure stop everything or just warn?" |
| [Constraint Gates](constraint-gates.md) | Bottleneck identification and pull-based quality | "Am I fixing the right stage, or just patching symptoms?" |
| [Prototype Building](prototype-building.md) | Exploration → execution methodology | "Am I building the right thing before building it right?" |
| [Creative & Discovery](creative-discovery.md) | Unstructured problem types | "How do I scope a Discovery task without going down a rabbit hole?" |
| [Data Readiness](data-readiness.md) | Input quality gates for routing pipelines | "Does this film have enough data to be worth classifying?" |
| [Certainty-First](certainty-first.md) | Anchor-then-expand classification strategy | "Which categories can I prove, and which are aspirational?" |
| [Curation Loop](curation-loop.md) | Bidirectional feedback between system and curator | "How does a curatorial decision get back into the system?" |

## Composition Guide

### Minimal Setup (Any Project)
- **Prototype Building** — Establishes exploration-before-execution discipline

### AI/LLM Projects
- **R/P Split** — Prevents the #1 failure mode in AI systems (precision tasks given to LLMs)
- **Pattern-First** — Prevents post-hoc rationalization in generated outputs
- **Measurement-Driven** — Catches regressions across versions

### Domain-Specific Classification Systems
- **Creative & Discovery** — Defines new categories, scopes boundary decisions, runs director audits
- **Domain Grounding** — Anchors categories in published theory; prevents taxonomy drift
- **Pattern-First** — Ensures taxonomy (schema) is stable before classifying entities (instances)
- **Certainty-First** — Classifies from proven anchors outward; gates expand with decreasing certainty
- **Data Readiness** — Prevents routing on films that lack the data routing needs
- **Curation Loop** — Feeds curator decisions back into the system; completes the lifecycle
- **Measurement-Driven** — Measures classification consistency and coverage

### Staged Pipeline Projects
- **Pattern-First** — Enforces correct dependency ordering between stages
- **Failure Gates** — Defines what stops the pipeline vs what warns
- **Constraint Gates** — Identifies which handoff to fix first; prevents wasted work on wrong stage
- **Boundary-Aware Measurement** — Scopes measurement to subsystems; gates expensive stages behind cheap validation
- **Measurement-Driven** — Tracks quality across depth (single case) and breadth (all cases)

### Full Stack (Complex Systems)
All twelve skills compose into a complete methodology:

```
Creative & Discovery (define the schema when it isn't known yet)
    ↓ produces schemas, taxonomies, category decisions
Prototype Building (exploration discipline)
    ↓ confirms approach on a real case
Pattern-First (dependency ordering)
    ↓ structures pipeline
Domain Grounding (taxonomy design)
    ↓ anchors classifications in published theory
Certainty-First (anchor-then-expand)
    ↓ classifies from proven anchors outward
R/P Split (task allocation)
    ↓ assigns work correctly
Data Readiness (input quality gates)
    ↓ gates routing behind data availability
Failure Gates (reliability semantics)
    ↓ prevents cascading failures
Constraint Gates (bottleneck protection)
    ↓ validates data survives stage boundaries
Boundary-Aware Measurement (scoped quality)
    ↓ measures subsystems independently
Measurement-Driven (quality cycles)
    ↓ validates changes across depth and breadth
Curation Loop (bidirectional feedback)
    ↓ feeds curator decisions back into system
IMPROVING SYSTEM
```

## How Skills Relate

```
                    MEASUREMENT-DRIVEN
                    (the development cycle)
                            │
                            ▼
                 BOUNDARY-AWARE MEASUREMENT
                 (scope to subsystem,
                  cost-order checks)
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
            │         DOMAIN GROUNDING      │
            │        (taxonomy design:      │
            │         published frameworks) │
            │               │               │
            └───────────────┼───────────────┘
                            │
                            ▼
                    CONSTRAINT GATES
                    (where to fix:
                     bottleneck identification,
                     boundary validation)
                            │
                            ▼
                    PROTOTYPE BUILDING
                    (exploration before
                     execution)
```

- **Measurement-Driven** is the orchestration layer — it tells you *when* to look at quality
- **Boundary-Aware Measurement** scopes measurement to the right subsystem at the right cost
- **R/P Split, Pattern-First, Failure Gates** are adjustment strategies — they tell you *how* to fix problems
- **Domain Grounding** anchors classifications in published theory — it tells you *what categories* to use
- **Certainty-First** governs classification strategy — it tells you *what to classify first* and *how much to trust each result*
- **Data Readiness** gates the pipeline — it tells you *whether to classify at all* given available data
- **Constraint Gates** is the diagnostic layer — it tells you *where* to fix (which handoff is the bottleneck)
- **Curation Loop** closes the feedback cycle — it tells you *how decisions get back into the system*
- **Prototype Building** is the foundation — it ensures you understand before you build

## Adopting Skills

1. Read the skill document
2. Copy the decision rules into your CLAUDE.md (use the template)
3. Add the diagnostic procedures to your debug runbook
4. Apply the principles when reviewing code and making architecture decisions

Skills don't require tooling — they're thinking frameworks that improve decision-making.
