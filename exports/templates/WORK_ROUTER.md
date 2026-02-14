# Work Router: Symptom-Based Navigation

<!--
  TEMPLATE: Route developers to the right documentation based on what they're trying to do.
  Replace [PLACEHOLDER] values. Add/remove scenarios as needed.
  Goal: Reduce time-to-relevant-docs from ~15 min to ~5 min.
-->

**Purpose:** Fast routing from "what are you trying to do?" to the right docs and actions.

---

## Category 1: Debugging & Fixing Issues

### Scenario: Output quality dropped
**Symptoms:** Scores decreased, output looks wrong, regression detected
**Read:** `docs/DEBUG_RUNBOOK.md` → triage section
**Then:** Identify which component/stage failed, trace to root cause
**Time:** ~10 min to identify, varies to fix

### Scenario: Pipeline stage fails
**Symptoms:** Error during execution, stage crashes, invalid output
**Read:** `docs/DEBUG_RUNBOOK.md` → error section
**Then:** Check input contracts, verify dependencies, check logs
**Time:** ~5 min to diagnose

### Scenario: Tests failing
**Symptoms:** CI red, test errors after changes
**Read:** `docs/DEVELOPER_GUIDE.md` → testing section
**Then:** Run failing tests locally, check if change broke contract
**Time:** ~5 min

<!-- ADD YOUR PROJECT-SPECIFIC DEBUGGING SCENARIOS -->

---

## Category 2: Building & Feature Work

### Scenario: Adding a new pipeline stage
**Read in order:**
1. `docs/architecture/SYSTEM_ARCHITECTURE.md` — understand existing stages
2. `docs/DEVELOPER_GUIDE.md` — change management rules
**Key rules:** Define inputs/outputs, add checkpoint, declare failure gates

### Scenario: Modifying existing behavior
**Read in order:**
1. `docs/architecture/SYSTEM_ARCHITECTURE.md` — find the relevant stage contract
2. `docs/DEVELOPER_GUIDE.md` — trace dependencies before editing
**Key rules:** Check what consumes this output, update downstream if needed

### Scenario: Adding a new output type
**Read in order:**
1. `docs/architecture/SYSTEM_ARCHITECTURE.md` — where does it fit?
2. Schema definitions if applicable
**Key rules:** Define schema first, populate instances second (Pattern-First)

<!-- ADD YOUR PROJECT-SPECIFIC BUILD SCENARIOS -->

---

## Category 3: Understanding Architecture

### Scenario: New to the project
**Read in order:**
1. `CLAUDE.md` — overview and work modes
2. `docs/CORE_DOCUMENTATION_INDEX.md` — find what you need
3. `docs/architecture/SYSTEM_ARCHITECTURE.md` — how it works
**Time:** ~30 min for overview

### Scenario: Understanding a specific component
**Read:** `docs/architecture/SYSTEM_ARCHITECTURE.md` → relevant section
**Then:** Look at the code for that component
**Time:** ~15 min

### Scenario: Understanding development methodology
**Read:** Methodology docs (if adopted from skills/)
**Time:** ~20 min per methodology

<!-- ADD YOUR PROJECT-SPECIFIC ARCHITECTURE SCENARIOS -->

---

## Category 4: Operational Tasks

### Scenario: Deploying changes
**Read:** `docs/DEVELOPER_GUIDE.md` → deployment section
**Time:** ~5 min

### Scenario: Running the full pipeline
**Read:** `docs/WORKFLOW_REGISTRY.md` → relevant workflow
**Time:** ~5 min

<!-- ADD YOUR PROJECT-SPECIFIC OPERATIONAL SCENARIOS -->

---

## Routing Decision Tree

```
What are you doing?
├── Something is broken
│   ├── Output quality dropped → Category 1: quality scenario
│   ├── Stage/component crashed → Category 1: failure scenario
│   └── Tests failing → Category 1: test scenario
│
├── Building something new
│   ├── New stage/component → Category 2: new stage
│   ├── Modifying existing → Category 2: modify behavior
│   └── New output type → Category 2: new output
│
├── Learning the system
│   ├── First time → Category 3: new to project
│   ├── Specific component → Category 3: component deep-dive
│   └── Why we do X → Category 3: methodology
│
└── Running/operating
    ├── Deploy → Category 4: deployment
    └── Run pipeline → Category 4: pipeline execution
```
