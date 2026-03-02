# Skill: Exploration-First (Map → Audit → Probe → Build)

**Purpose:** Ensure you understand the current system before modifying it.
**Addresses:** Intuition-driven fixes, architectural drift, regressions from unexamined assumptions, wasted effort on wrong leverage points.

**Relationship to Prototype Building:** Prototype Building covers exploring a *new problem* before building. Exploration-First covers investigating an *existing system* before changing it. Use Prototype Building when creating. Use Exploration-First when modifying.

---

## Core Principle

**Don't change what you haven't mapped.**

```
INVESTIGATION (must complete first):
1. Map              → What does the process read, produce, send, ignore?
2. Audit            → Does it align with the system's own design principles?
3. Theorize         → What specific change would produce what improvement?
4. Probe            → Does the evidence support the theory?
5. Decide           → What's the minimal intervention with highest leverage?
─────────────────────────────────────────────────────────────────────────────
EXECUTION (only after investigation):
6. Build            → Implement the minimal change
7. Validate         → Depth (target improved?) then breadth (no regressions?)
8. Codify           → Persist learning as reusable logic
```

If you're building and can't point to a workflow map, principles scorecard, and probe evidence, stop and go back.

---

## The Three Modes

### Mode A: Contract Breach — Something Is Failing

**Entry:** A hard invariant or threshold is violated.

```
1. Define one failing invariant (singular, not vague)
2. Map the current workflow
3. Trace causality backward from symptom using stage contracts
4. Run discriminating probes at each upstream boundary
5. Stop at first broken upstream contract
6. Apply minimal fix
7. Validate depth then breadth
8. Codify learning + update workflow doc
```

**Stop rule:** First broken upstream contract.

### Mode B: Optimization — Nothing Failing, Could Be Better

**Entry:** A bounded improvement target with expected delta.

```
1. Define target with expected delta (not "make it better")
2. Map the current workflow
3. Trace causality forward from inputs to leverage points
4. Run probes to identify highest-leverage upstream change
5. Stop at first change with measurable expected gain
6. Apply minimal intervention
7. Validate depth then breadth
8. Codify learning + update workflow doc
```

**Stop rule:** First high-leverage upstream point with measurable expected gain.

### Mode C: Drift Audit — Has the System Evolved Past This Process?

**Entry:** Process identifier + version it was designed at. No known failure. No specific target.

```
1. Identify process + version it was designed at
2. Map the current workflow (REQUIRED first step)
3. Run principles audit using structured checklist
4. If all principles pass → DONE (workflow doc + scorecard are the artifacts)
5. If violations found → violations become the bounded targets
6. Proceed through theory → probes → build → validate
7. Codify learning + update workflow doc
```

**Stop rule:** Principles audit scorecard is complete. If all pass, no further work needed.

**When to trigger Mode C:**
- New upstream stage added — do downstream processes consume its output?
- Major schema change shipped — do processes that should use it reference it?
- Process not modified in >6 months — does it still align with current architecture?

---

## The Mapping Step (Phase 0.5)

Mapping is a PRECISION task — deterministic observation, not interpretation.

For each process under investigation, document:

| Dimension | What to Record |
|---|---|
| **Reads** | Which inputs, context attributes, upstream data fields |
| **Produces** | Output schema, where stored, downstream consumers |
| **Sends to LLM** | Prompt construction, context provided, truncation applied |
| **Ignores** | Data available but not accessed (the most revealing dimension) |
| **Validates** | Gates, checks, error handling at boundaries |

**The "ignores" dimension is the most valuable.** It reveals data the system produces upstream that the process doesn't consume — often the root cause of drift and the source of the highest-leverage improvements.

### Mapping Checklist

- [ ] Read the process code (not just the docstring)
- [ ] Document every context field the process accesses
- [ ] Document every context field the process does NOT access
- [ ] Document the prompt construction (for LLM-calling processes)
- [ ] Document what gets truncated or filtered before the LLM call
- [ ] Identify downstream consumers of the process output
- [ ] Record this as a workflow document (not a chat summary)

---

## The Principles Audit (Phase 1)

After mapping, run a structured checklist against the system's declared design principles.

### Core Checklist (applies to all processes)

| Principle | What to Check | Pass/Fail Criterion |
|---|---|---|
| R/P Split | Are precision tasks in code and reasoning tasks in LLM? | No R/P violations in prompt |
| Observation authority | Does the process consume upstream HIGH-confidence observations? | Observations not silently discarded |
| Cost ordering | Are cheap checks run before expensive operations? | No $$$ operations before $0 validations |
| Gate coverage | Does the process have quality gates at input and output? | Gates exist and fire on violations |
| Evidence contract | Does output contain all fields downstream consumers need? | No silent field stripping |

### Output: Principles Scorecard

For each principle:

```
Principle: [name]
Requires: [what the principle demands]
Current:  [what the process actually does]
Verdict:  PASS | SOFT VIOLATION | HARD VIOLATION
Evidence: [specific code line, data field, or behavior]
```

The scorecard is the input to the theory phase. Violations become falsifiable claims. Passes confirm alignment.

---

## The Observation-Inference Ledger (Phase 4)

During probe execution, maintain strict separation:

| Step | Artifact Inspected | Observation | Inference | Confidence | Next Probe |
|---|---|---|---|---|---|
| 1 | Stage 4 checkpoint | Field `clusters` has 3 entries | Process generates cluster data | HIGH | Check if Stage 5 consumes `clusters` |
| 2 | Stage 5 source code | No reference to `clusters` field | Stage 5 ignores cluster data | HIGH | Check if this was intentional |
| 3 | Git blame on Stage 5 | Stage 5 last modified v7.3; clusters added v8.1 | Drift: Stage 5 predates clusters | HIGH | Theory confirmed |

**Rules:**
- Never promote inference to fact without a confirming probe
- If two inferences conflict, design a probe that discriminates
- Record "next probe" to maintain investigation chain

---

## The Process Catalog

### What It Is

A collection of workflow docs — one per process — showing what each process reads, produces, sends, and ignores.

### Why It Matters

| Without catalog | With catalog |
|---|---|
| Every audit requires code archaeology | Pull workflow doc, run checklist |
| Understanding one process: hours | Understanding one process: minutes |
| Each investigation starts from scratch | Each investigation builds on previous |
| Drift is invisible until something breaks | Drift is visible in "ignores" dimension |

### Compounding Returns

Each investigation that produces a workflow doc makes the next investigation cheaper. After 5 workflow docs, the team has a partial map of the system. After 15, they have a comprehensive map. The cost per audit drops with each addition.

### Promotion Path

```
UNDOCUMENTED → CONTRACT ONLY → FULL WORKFLOW
     │                │               │
     │                │               └─ reads/produces/sends/ignores + scorecard
     │                └─ inputs/outputs/gates in architecture doc
     └─ no documentation of data flow
```

---

## Integration with Other Skills

| Skill | How Exploration-First Connects |
|---|---|
| **Prototype Building** | Prototype Building explores *problems* before building new things. Exploration-First investigates *systems* before changing existing things. Use both: Prototype Building for creation, Exploration-First for modification. |
| **Constraint Gates** | Constraint Gates identifies *where* the bottleneck is. Exploration-First provides the mapping and audit that precedes constraint identification — you can't find what's lost if you don't know what's there. |
| **Pattern-First** | Pattern-First ensures correct dependency ordering. Exploration-First's mapping reveals when dependency ordering has drifted (upstream data exists but downstream doesn't consume it). |
| **R/P Split** | Mapping what a process sends to the LLM reveals R/P violations. The principles audit explicitly checks for them. |
| **Measurement-Driven** | Measurement-Driven validates changes (depth then breadth). Exploration-First structures the investigation that precedes the change. MDD is Phase 7; Exploration-First is Phases 0-5. |
| **Failure Gates** | Exploration-First's audit checks whether gates exist at boundaries. Missing gates become findings in the principles scorecard. |
| **Boundary-Aware Measurement** | Drift audits often reveal that processes straddle boundaries incorrectly — measuring the wrong subsystem or running expensive checks before cheap ones. |
| **Domain Grounding** | Mapping reveals whether classification categories match between stages. Ungrounded taxonomies often cause the silent discarding that mapping exposes. |

---

## Diagnostic: Is This an Exploration-First Problem?

| Symptom | Likely? | What to Do |
|---|---|---|
| Fixing one case regresses three others | Yes | Map the process — you're changing something you don't fully understand |
| New upstream data exists but output doesn't improve | Yes | Drift audit — process may not consume the new data |
| "I read the code, it should work" but doesn't | Yes | Map reads/produces/ignores — assumptions differ from reality |
| Process was designed 6+ months ago | Possibly | Mode C drift audit to check alignment |
| Building something entirely new | No | Use Prototype Building instead |
| Know exactly which handoff is broken | No | Use Constraint Gates instead |
| Need to validate a completed change | No | Use Measurement-Driven instead |

---

## Minimum Artifact Contract

A complete exploration produces:

1. **Workflow doc** — current-state process map (Phase 0.5)
2. **Principles scorecard** — per-principle verdicts with evidence (Phase 1)
3. **Theory brief** — claims, assumptions, expected evidence (Phase 1)
4. **Architecture delta** — affected contracts and handoffs (Phase 2)
5. **Probe plan + results** — discriminating checks + observation-inference ledger (Phases 3-4)
6. **Decision record** — chosen intervention, rejected alternatives, rationale (Phase 5)
7. **Validation report** — depth and breadth results (Phase 7)

For drift audits where all principles pass, artifacts 1-2 may be the only outputs. The investigation concludes early because no intervention is needed.

---

## Checklist

### Before modifying an existing process:
- [ ] Mapped what the process reads, produces, sends to LLM, and ignores
- [ ] Ran principles audit with structured checklist
- [ ] Generated falsifiable claims from audit findings
- [ ] Designed discriminating probes (not exhaustive inspection)
- [ ] Maintained observation-inference separation in all probe results
- [ ] Identified earliest upstream leverage point (not downstream symptom)

### After implementing the change:
- [ ] Validated depth (target case improved)
- [ ] Validated breadth (no unacceptable regressions)
- [ ] Updated workflow doc in process catalog
- [ ] Persisted reusable logic (probes, gates, decision rules)

### For drift audits:
- [ ] Identified process + version it was designed at
- [ ] Completed workflow mapping (Phase 0.5) before any audit
- [ ] Ran full principles checklist (core + domain-specific)
- [ ] Recorded scorecard with per-principle verdicts and evidence
- [ ] If all pass: documented alignment, no further phases needed
- [ ] If violations: violations became bounded targets for Phases 2+
