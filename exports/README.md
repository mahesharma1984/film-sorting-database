# Development Methodology Kit

A portable, drop-in collection of theoretical foundations, development methodologies, documentation templates, and AI-assisted development skills extracted from a production codebase.

## What This Is

This kit distills battle-tested development practices from a project that evolved through 10+ major versions of a staged AI pipeline. The methodologies are **domain-agnostic** — they apply to any project that uses AI/LLMs, staged pipelines, or measurement-driven quality.

**Key insight:** The kit has four layers, and they build on each other.

## The Four Layers

```
Layer 0: KNOWLEDGE BASE (understand why)
         Theory, mental models, failure patterns
         "Why do AI systems hallucinate? Why does dependency
          order matter? Why do metrics lie?"
              │
              ▼
Layer 1: SKILLS (know how)
         Composable methodology modules
         "Split reasoning from precision tasks. Define
          schema before instances. Measure depth and breadth."
              │
              ▼
Layer 2: TEMPLATES (implement)
         Documentation structure for your project
         "CLAUDE.md, debug runbook, workflow registry,
          work router — ready to customize."
              │
              ▼
Layer 3: RAG VERIFICATION (verify)
         Queryable documentation search
         "Does my error handling follow the gate pattern?
          Which principle applies to this decision?"
```

**Theory enables correct application. Skills without theory become cargo cult.** If you skip the knowledge base, you'll follow the skills as rules without understanding when to adapt them to new situations.

**RAG closes the last mile.** Layers 0-2 get you to ~80% methodology alignment. Layer 3 — querying your docs to verify compliance — helps close the gap to 90%+. Add it when your docs grow beyond ~15 files.

## Quick Start

1. **Read** the [`knowledge-base/`](knowledge-base/) — understand the theory (1-2 hours)
2. **Read** [`BOOTSTRAP.md`](BOOTSTRAP.md) — step-by-step setup guide
3. **Pick skills** from [`skills/`](skills/) based on your project type
4. **Copy templates** from [`templates/`](templates/) into your `docs/` directory
5. **Customize** the CLAUDE.md template with your project specifics
6. **Add RAG** from [`rag/`](rag/) when your docs grow beyond ~15 files (optional)

## Directory Structure

```
exports/
├── README.md                  # This file
├── BOOTSTRAP.md               # Step-by-step guide for new repos
├── knowledge-base/            # Layer 0: Theoretical foundations
│   ├── README.md              # Reading order and theory-skill mapping
│   ├── llm-capability-model.md    # What AI can and cannot do
│   ├── task-design-theory.md      # How decomposition determines quality
│   ├── causality-and-systems.md   # Why dependency direction matters
│   ├── domain-grounding-theory.md # Why published frameworks beat invented categories
│   ├── system-boundary-theory.md  # Why multi-stage systems need explicit boundaries
│   ├── measurement-theory.md      # How to know if something works
│   ├── failure-theory.md          # How systems break silently
│   └── constraint-theory.md       # How to find the real bottleneck
├── skills/                    # Layer 1: Composable methodology modules
│   ├── README.md              # Skills overview and composition guide
│   ├── rp-split.md                # Reasoning/Precision task allocation
│   ├── pattern-first.md           # Schema-before-instances methodology
│   ├── domain-grounding.md        # Anchoring decisions in published theory
│   ├── boundary-aware-measurement.md  # Scoped quality across system boundaries
│   ├── measurement-driven.md      # Depth/breadth quality cycles
│   ├── failure-gates.md           # Hard vs soft failure semantics
│   ├── constraint-gates.md        # TOC/Kanban bottleneck identification
│   └── prototype-building.md      # Exploration → execution stages
├── templates/                 # Layer 2: Documentation structure templates
│   ├── CLAUDE.md.template     # AI assistant project instructions
│   ├── CORE_DOCS_INDEX.md     # Documentation index template
│   ├── WORK_ROUTER.md         # Symptom-based navigation template
│   ├── DEBUG_RUNBOOK.md       # Diagnosis → action mapping template
│   ├── WORKFLOW_REGISTRY.md   # Atomic + composed workflows template
│   ├── DEVELOPER_GUIDE.md     # Change management guide template
│   └── CI_RULES.md            # Safety guardrails template
├── rag/                       # Layer 3: RAG verification tool (optional)
│   ├── README.md              # Why RAG matters (80% → 90%)
│   ├── INTEGRATION_GUIDE.md   # Step-by-step setup
│   ├── requirements.txt       # Python dependencies
│   └── rag/                   # Generalized Python package
│       ├── config.py          # Tunable parameters (CUSTOMIZE sections)
│       ├── chunker.py         # Heading-based document splitting
│       ├── metadata.py        # Authority metadata extraction
│       ├── precision_filter.py # Keyword matching + query classification
│       ├── indexer.py         # Index builder (embeddings + BM25)
│       ├── retriever.py       # Hybrid scoring engine
│       ├── structured_lookup.py # Deterministic matching
│       └── query.py           # CLI + programmatic interface
└── examples/                  # Real examples from the reference repo
    └── methodology-in-action.md
```

## Knowledge Base → Skill Mapping

Each knowledge base document provides the theory that underlies a specific skill:

| Theory (understand first) | Skill (apply after) |
|---|---|
| [LLM Capability Model](knowledge-base/llm-capability-model.md) | [R/P Split](skills/rp-split.md) |
| [Task Design Theory](knowledge-base/task-design-theory.md) | [Prototype Building](skills/prototype-building.md) |
| [Causality & Systems](knowledge-base/causality-and-systems.md) | [Pattern-First](skills/pattern-first.md) |
| [Domain Grounding Theory](knowledge-base/domain-grounding-theory.md) | [Domain Grounding](skills/domain-grounding.md) |
| [System Boundary Theory](knowledge-base/system-boundary-theory.md) | [Boundary-Aware Measurement](skills/boundary-aware-measurement.md) |
| [Measurement Theory](knowledge-base/measurement-theory.md) | [Measurement-Driven Dev](skills/measurement-driven.md) |
| [Failure Theory](knowledge-base/failure-theory.md) | [Failure Gates](skills/failure-gates.md) |
| [Constraint Theory](knowledge-base/constraint-theory.md) | [Constraint Gates](skills/constraint-gates.md) |

## Project Types and Recommended Skills

| Project Type | Knowledge Base Focus | Recommended Skills |
|---|---|---|
| AI/LLM pipeline | LLM Capability + Task Design + Measurement | R/P Split + Pattern-First + Measurement-Driven |
| Data processing pipeline | Causality + Measurement + Failure + Constraint | Pattern-First + Failure Gates + Constraint Gates + Measurement-Driven |
| Domain-specific classification system | Domain Grounding + Causality + Measurement | Domain Grounding + Pattern-First + Measurement-Driven |
| Multi-stage system with expensive stages | System Boundary + Constraint + Measurement | Boundary-Aware Measurement + Constraint Gates + Measurement-Driven |
| Any project with Claude Code | LLM Capability + Task Design | R/P Split + Prototype Building |
| Complex multi-stage system | All eight theory docs | All eight skills |

## Positioning

This kit operates at **Layer 1** of the AI development stack — the thinking layer:

```
Layer 4: EXECUTION LOOP     ← Ralph, CI/CD (keep running until done)
Layer 3: ORCHESTRATION       ← GSD, BMAD (who does what, when)
Layer 2: SPECIFICATION       ← SpecKit (what to build)
Layer 1: METHODOLOGY         ← THIS KIT (how to think)
Layer 0: THEORY              ← THIS KIT (why it works)
```

It's complementary to execution frameworks (Ralph), orchestration frameworks (GSD/BMAD), and specification frameworks (SpecKit). Those tell you how to run, organize, and specify AI work. This kit tells you **how to think about the problems** those frameworks solve — and when the default approach won't work.

## Origin

These practices were developed through 10+ versions of a literary analysis automation system. Each methodology emerged from real failures, measured regressions, and architectural fixes. Every principle in the knowledge base was discovered by getting something wrong first. The documentation exists so you can learn from those failures without repeating them.

See [`examples/methodology-in-action.md`](examples/methodology-in-action.md) for how these practices evolved in the reference project.
