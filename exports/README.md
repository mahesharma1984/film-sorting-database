# Development Methodology Kit

A portable, drop-in collection of development methodologies, documentation templates, and AI-assisted development skills extracted from a production codebase.

## What This Is

This kit distills battle-tested development practices from a project that evolved through 10+ major versions of a staged AI pipeline. The methodologies are **domain-agnostic** — they apply to any project that uses AI/LLMs, staged pipelines, or measurement-driven quality.

## Quick Start

1. **Read** [`BOOTSTRAP.md`](BOOTSTRAP.md) to set up a new repo
2. **Pick skills** from [`skills/`](skills/) based on your project type
3. **Copy templates** from [`templates/`](templates/) into your `docs/` directory
4. **Customize** the CLAUDE.md template with your project specifics

## Directory Structure

```
exports/
├── README.md                  # This file
├── BOOTSTRAP.md               # Step-by-step guide for new repos
├── skills/                    # Composable methodology modules
│   ├── README.md              # Skills overview and composition guide
│   ├── rp-split.md            # Reasoning/Precision task allocation
│   ├── pattern-first.md       # Schema-before-instances methodology
│   ├── measurement-driven.md  # Depth/breadth quality cycles
│   ├── failure-gates.md       # Hard vs soft failure semantics
│   └── prototype-building.md  # Exploration → execution stages
├── templates/                 # Documentation structure templates
│   ├── CLAUDE.md.template     # AI assistant project instructions
│   ├── CORE_DOCS_INDEX.md     # Documentation index template
│   ├── WORK_ROUTER.md         # Symptom-based navigation template
│   ├── DEBUG_RUNBOOK.md       # Diagnosis → action mapping template
│   ├── WORKFLOW_REGISTRY.md   # Atomic + composed workflows template
│   ├── DEVELOPER_GUIDE.md     # Change management guide template
│   └── CI_RULES.md            # Safety guardrails template
└── examples/                  # Real examples from the reference repo
    └── methodology-in-action.md
```

## Skills System

Each **skill** is a self-contained methodology module that includes:
- **Principles** — The core ideas
- **Decision rules** — When and how to apply
- **Diagnostic procedures** — How to identify and fix violations
- **Examples** — Real cases (generalized from the reference repo)

Skills are composable. See [`skills/README.md`](skills/README.md) for recommended combinations.

## Project Types and Recommended Skills

| Project Type | Recommended Skills |
|---|---|
| AI/LLM pipeline | R/P Split + Pattern-First + Measurement-Driven |
| Data processing pipeline | Pattern-First + Failure Gates + Measurement-Driven |
| Any project with Claude Code | R/P Split + Prototype Building |
| Complex multi-stage system | All five skills |

## Origin

These practices were developed through 10+ versions of a literary analysis automation system. Each methodology emerged from real failures, measured regressions, and architectural fixes. The domain-specific content has been removed; what remains are the universal principles.

See [`examples/methodology-in-action.md`](examples/methodology-in-action.md) for how these practices evolved in the reference project.
