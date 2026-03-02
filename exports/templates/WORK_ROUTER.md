# Work Router: Symptom-Based Navigation

<!--
  TEMPLATE: Route developers to the right documentation based on what they're trying to do.
  Replace [PLACEHOLDER] values. Add/remove scenarios as needed.
  Goal: Reduce time-to-relevant-docs from ~15 min to ~5 min.
-->

**Purpose:** Fast routing from "what are you trying to do?" to the right docs and actions.

---

## Quick Triage (30 seconds)

```
What are you doing?
│
├── Don't know what's wrong yet / investigating
│   └── Category 0: Investigation & Problem Classification
│
├── Something is broken
│   └── Category 1: Debugging & Fixing Issues
│
├── Building something new or changing existing behavior
│   └── Category 2: Building & Feature Work
│
├── Learning the system or understanding why
│   └── Category 3: Understanding Architecture
│
└── Running, deploying, or operating
    └── Category 4: Operational Tasks
```

---

## Category 0: Investigation & Problem Classification

<!--
  Use this when you don't know what's wrong yet, or when you need to
  classify a problem before deciding how to fix it.

  The key question: "Is this a theory, architecture, or implementation problem?"
  The answer determines which docs to read and which approach to take.
-->

### §0.1 Problem Classification Decision Tree

```
Start here: What kind of problem is this?
│
├── "The system does something, but the LOGIC is wrong"
│   │  (wrong priorities, wrong categories, wrong ordering)
│   └── THEORY PROBLEM
│       → Check: Do methodology/theory docs define the correct behavior?
│       → Read: docs/knowledge-base/* or docs/methodology/*
│       → Fix: Update the theory/methodology doc first, then align code
│
├── "The system does something, but the HANDOFF between components is wrong"
│   │  (data lost between stages, wrong format, contract violation)
│   └── ARCHITECTURE PROBLEM
│       → Check: Do component contracts match actual data flow?
│       → Read: docs/architecture/* → component contract section
│       → Fix: Update the contract, then fix the code
│
├── "A REASONING task is assigned to code, or a PRECISION task to the LLM"
│   │  (LLM extracting exact text, code doing classification)
│   └── R/P SPLIT PROBLEM
│       → Check: Is the task allocation correct per R/P Split?
│       → Read: R/P Split skill doc
│       → Fix: Reassign the task to the correct executor
│
└── "The logic and architecture are right, but the CODE doesn't match"
    │  (bug, missing implementation, wrong algorithm)
    └── IMPLEMENTATION PROBLEM
        → Check: Does the code implement what the architecture doc specifies?
        → Read: The specific file + its architecture contract
        → Fix: Fix the code to match the contract
```

**Diagnostic signals:**

| Signal | Likely Classification |
|---|---|
| "The output looks plausible but is wrong" | Theory or R/P Split |
| "Data disappears between components" | Architecture (handoff) |
| "It worked before, now it doesn't" | Implementation (regression) |
| "The LLM hallucinates/fabricates" | R/P Split |
| "Metrics pass but output is bad" | Theory (wrong metrics) |
| "Works for one case, fails for others" | Architecture (contract too narrow) |

### §0.2 Component Lookup Table

<!--
  TEMPLATE: Fill this in for your project. Map each major component to its
  theory doc, architecture doc, code location, validation command, and
  active issues. This table is the fastest way to navigate from
  "something is wrong with X" to the right documentation.

  Example row:
  | Data Ingestion | task-design-theory.md | SYSTEM_ARCHITECTURE.md § Ingestion | src/ingest/ | pytest tests/test_ingest.py | #42, #67 |
-->

| Component | Theory Doc | Architecture Doc | Code Location | Validation Command | Active Issues |
|---|---|---|---|---|---|
| [Component 1] | [theory doc] | [arch doc § section] | [code path] | [test/validation command] | [issue #s] |
| [Component 2] | [theory doc] | [arch doc § section] | [code path] | [test/validation command] | [issue #s] |
| [Component 3] | [theory doc] | [arch doc § section] | [code path] | [test/validation command] | [issue #s] |

<!--
  Add one row per major component in your system. The table should cover
  every component that has its own theory, architecture contract, and code.
  This is the bridge between "I have a problem" and "here's where to look."
-->

### §0.3 Theory Check

When classification points to a theory problem:

1. Identify which methodology/theory doc governs this behavior
2. Read the relevant section — does it define the correct behavior?
3. If yes → the code drifted from the theory. Fix code to match.
4. If no → the theory needs updating. Update theory first, then code.
5. Check: is the theory grounded in published frameworks? (Domain Grounding)

### §0.4 Architecture Check

When classification points to an architecture problem:

1. Find the component contract in `docs/architecture/*`
2. Verify: does the upstream producer output what the contract says?
3. Verify: does the downstream consumer read what the contract says?
4. If mismatch → fix the component that violates the contract
5. If contract is wrong → update contract first, then fix components

### §0.5 Data Flow Trace

When you need to understand how data moves through the system:

1. Start at the component where the problem is visible
2. Trace backward: what does this component consume? From where?
3. Trace forward: what does this component produce? Who consumes it?
4. Document: reads / produces / sends / ignores (the "ignores" dimension reveals drift)
5. This is a PRECISION task — observe deterministically, don't interpret yet

### §0.6 Drift Audit

When a component hasn't been updated in a while:

1. Identify the component + the version it was designed at
2. Map what it reads, produces, sends, and ignores (§0.5)
3. Check: has the system added new upstream data since this was designed?
4. Check: does the component consume that new data, or ignore it?
5. If ignoring → the component has drifted. This is often the highest-leverage fix.

### §0.7 Investigation → Spec Workflow

Once investigation is complete, convert findings to an actionable spec:

```
Investigation complete
    ↓
1. Classify the problem (§0.1)
    ↓
2. Trace to root cause using appropriate check (§0.3-§0.6)
    ↓
3. Write Issue Spec using ISSUE_SPEC_TEMPLATE.md
   - §1 Manager Summary from your investigation findings
   - §3 Root Cause from your trace
   - §4 Affected Handoffs from your data flow trace
   - §7 Measurement Story from your baseline data
    ↓
4. Validate spec completeness using Section Checklist
    ↓
5. Hand to implementer (or begin implementation)
```

---

## Category 1: Debugging & Fixing Issues

### Scenario: Output quality dropped
**Symptoms:** Scores decreased, output looks wrong, regression detected
**Read:** `docs/DEBUG_RUNBOOK.md` → triage section
**Then:** Identify which component failed, trace to root cause
**Time:** ~10 min to identify, varies to fix

### Scenario: Pipeline/component fails
**Symptoms:** Error during execution, stage crashes, invalid output
**Read:** `docs/DEBUG_RUNBOOK.md` → error section
**Then:** Check input contracts, verify dependencies, check logs
**Time:** ~5 min to diagnose

### Scenario: Tests failing
**Symptoms:** CI red, test errors after changes
**Read:** `docs/DEVELOPER_GUIDE.md` → testing section
**Then:** Run failing tests locally, check if change broke contract
**Time:** ~5 min

### Scenario: Writing an Issue Spec

After diagnosing a problem, write a spec before fixing:

1. Use `ISSUE_SPEC_TEMPLATE.md` (in `docs/` or `templates/`)
2. Fill all 10 mandatory sections
3. Pay special attention to §4 (Affected Handoffs) and §5 (Execution Order)
4. Run Section Checklist before handing to implementer
5. Pin measurement baseline before implementation starts

<!-- ADD YOUR PROJECT-SPECIFIC DEBUGGING SCENARIOS -->

---

## Category 2: Building & Feature Work

### Scenario: Adding a new component/stage
**Read in order:**
1. `docs/architecture/SYSTEM_ARCHITECTURE.md` — understand existing components
2. `docs/DEVELOPER_GUIDE.md` — change management rules
**Key rules:** Define inputs/outputs, add checkpoint, declare failure gates

### Scenario: Modifying existing behavior
**Read in order:**
1. `docs/architecture/SYSTEM_ARCHITECTURE.md` — find the relevant contract
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
│
├── Don't know what's wrong yet
│   ├── Need to classify the problem → Category 0: §0.1 Decision Tree
│   ├── Need to trace data flow → Category 0: §0.5 Data Flow Trace
│   └── Component seems outdated → Category 0: §0.6 Drift Audit
│
├── Something is broken
│   ├── Output quality dropped → Category 1: quality scenario
│   ├── Component crashed → Category 1: failure scenario
│   ├── Tests failing → Category 1: test scenario
│   └── Need to write a fix spec → Category 1: issue spec scenario
│
├── Building something new
│   ├── New component → Category 2: new component
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
