# Exploration Theory: Why You Must Map and Audit Before You Change

**Read this before:** Exploration-First skill
**Core question:** When improving an existing system, why does building before investigating make things worse — and how do you structure investigation so it produces actionable evidence?

---

## The Common Assumption

When developers want to improve an existing system, the default approach is:

1. **"I see the problem, let me fix it"** — Jump from symptom to solution without tracing causality
2. **"I've read the code, I know what it does"** — Assume understanding without mapping data flow
3. **"This worked last time"** — Apply a familiar fix without checking whether the system has evolved since it was designed

All three skip the same step: **structured investigation of the current system state before deciding what to change.** The result is interventions that miss root causes, break downstream contracts, or solve problems the system no longer has.

---

## The Failure That Reveals the Truth

A team notices that a late-stage process produces mediocre output. A developer reads the code, sees what looks like an obvious improvement, and implements it. The target case improves. But three other cases regress. The developer patches those regressions, which introduces a new edge case. Two weeks of fixes later, the system is more complex and no better overall.

Post-mortem reveals: the process was designed two versions ago. Since then, an upstream stage was added that produces data the process never consumes. The "obvious improvement" was patching a symptom. The actual leverage point was wiring the process to consume the upstream data it was ignoring.

**Three failures compounded:**
1. **No mapping** — The developer didn't document what the process reads, produces, and ignores before changing it
2. **No audit** — Nobody checked whether the process still aligned with the system's own design principles
3. **No theory** — The intervention was chosen by intuition, not by evidence from discriminating probes

The team spent two weeks optimizing the wrong thing because nobody mapped the system first.

---

## The Mental Model: Structured Investigation

Improving an existing system is fundamentally different from building a new one. New systems need exploration to understand the *problem*. Existing systems need exploration to understand the *current state* — which is often different from what anyone thinks it is.

### The Investigation Backbone

Every system improvement follows the same causal chain:

```
MAP the current state
    → what does the process actually read, produce, send, ignore?
         │
AUDIT against principles
    → does the process align with the system's own design rules?
         │
THEORIZE with falsifiable claims
    → what specific change would produce what specific improvement?
         │
PROBE with discriminating tests
    → does the evidence support the theory or refute it?
         │
DECIDE based on evidence
    → what is the minimal intervention with the highest leverage?
         │
BUILD the change
         │
VALIDATE depth then breadth
    → did the target improve? did anything else regress?
         │
CODIFY the learning
    → what reusable logic did this produce?
```

**The key insight:** Build is step 6 of 8. Five steps of investigation precede it. This isn't bureaucracy — each step produces artifacts that prevent wasted work in later steps.

### Three Investigation Modes

Not all investigations start from the same place:

| Mode | Entry | Stop Rule |
|---|---|---|
| **Contract breach** | Something is failing | First broken upstream contract |
| **Optimization** | Nothing failing, but could be better | First high-leverage upstream point |
| **Drift audit** | Nothing failing, no known target | Principles audit scorecard complete |

Drift audit is the proactive mode. It doesn't require a known problem. It asks: "This process was designed at version N. The system is now at version M. Does the process still align?" The answer often reveals leverage points nobody knew existed.

---

## The Principles

### Principle 1: Map Before You Reason

You cannot audit what you have not documented. Before any analysis:

1. **What does the process read?** (inputs, context objects, upstream data)
2. **What does it produce?** (outputs, artifacts, downstream consumers)
3. **What does it send to the LLM?** (prompt construction, context provided)
4. **What does it truncate, ignore, or discard?** (available-but-unused data)

This mapping is a PRECISION task — deterministic observation of code and data flow. The output is a workflow document, not a narrative assessment.

**Why this matters:** Without a map, audit findings are speculative ("I think it ignores X"). With a map, they are grounded ("Line 247 constructs the prompt from fields A, B, C. Field D is available on the context object but never referenced").

### Principle 2: Audit Against Declared Principles

After mapping, check the process against the system's own design rules using a structured checklist. For each principle:

1. What does the principle require?
2. What does the current process do?
3. Pass / Soft violation / Hard violation?
4. If violation: what specific data or behavior causes it?

The output is a scorecard — per-principle verdicts with evidence. This is what converts vague "it could be better" into specific, falsifiable claims.

### Principle 3: Theory Before Architecture, Architecture Before Build

No build work should start until:

1. Theory claims and expected evidence are explicit
2. Architecture deltas and contract impacts are explicit
3. Probe evidence supports a specific implementation decision

This prevents the most common failure: implementing an intuitive fix that misses the actual leverage point.

### Principle 4: Separate Observation from Inference

For every investigation step, record:

- **Observation:** what the artifact or metric directly shows
- **Inference:** what you conclude from that observation

Do not promote inference to fact without a confirming probe. This prevents the second most common failure: acting on assumptions disguised as findings.

### Principle 5: Stop at Earliest Leverage Point

When multiple opportunities are visible, choose the earliest upstream intervention that can explain or improve downstream behavior. Do not continue investigating once decision-quality evidence exists. Do not patch downstream when upstream contracts remain broken.

### Principle 6: Persist Learning as Reusable Logic

Every completed investigation should produce reusable assets: workflow docs, probe specifications, gate criteria, decision rules. This turns one investigation into future operational capability. The process catalog grows with each exploration — each mapping makes the next audit cheaper.

---

## Three Modes in Practice

### Contract Breach: Something Is Failing

```
1. Define one failing invariant (not a vague problem)
2. Map the current workflow
3. Build causal map backward from symptom using stage contracts
4. Run discriminating probes at each upstream boundary
5. Stop at first broken contract
6. Apply minimal fix
7. Validate depth then breadth
8. Codify the learning
```

### Optimization: Could Be Better

Same backbone, different entry and stop rule:

```
1. Define bounded improvement target with expected delta
2. Map the current workflow
3. Build causal map forward from inputs to leverage points
4. Run probes to identify highest-leverage upstream change
5. Stop at first change with measurable expected gain
6. Apply minimal intervention
7. Validate depth then breadth
8. Codify the learning
```

### Drift Audit: Has the System Evolved Past This Process?

The proactive mode — no known failure, no specific target:

```
1. Identify process + version it was designed at
2. Map the current workflow (REQUIRED first step)
3. Run principles audit using structured checklist
4. If all principles pass → done (workflow doc + scorecard are the artifacts)
5. If violations found → violations become the bounded targets
6. Proceed to theory → probes → build → validate
7. Codify the learning
```

**When to trigger drift audits:**
- A new upstream stage was added — do downstream processes consume its output?
- A major schema change shipped — do processes that should use it actually reference it?
- A process hasn't been modified in >6 months — does it still align with current architecture?

---

## The Process Catalog: Compounding Returns

Each investigation produces a workflow document. Over time, these accumulate into a process catalog — a collection of maps showing what every process reads, produces, sends, and ignores.

**Without the catalog:** Every audit requires expensive code archaeology. Understanding one process takes hours.

**With the catalog:** Auditing becomes: pull the workflow doc, run the principles checklist, record the scorecard. Understanding one process takes minutes.

The catalog has compounding returns: each new workflow doc makes the next investigation cheaper. A system with 20 documented processes is radically easier to maintain than one with 20 undocumented processes, even if the code is identical.

---

## Connection to Other Knowledge Base Concepts

| Concept | Connection to Exploration Theory |
|---|---|
| **Task Design Theory** | Task decomposition tells you what to build. Exploration theory tells you what to investigate before deciding what to build. Exploration is where you discover the task decomposition. |
| **Causality & Systems** | Exploration theory applies causal tracing to existing systems. Map the dependency chain, find the earliest upstream leverage point. |
| **Constraint Theory** | Constraint theory asks "where is value destroyed?" Exploration theory asks "what does the current system actually do?" Mapping (exploration) precedes constraint identification. |
| **Measurement Theory** | Measurement tells you something is wrong. Exploration tells you how to investigate why. Validate depth then breadth after every intervention. |
| **Failure Theory** | Exploration theory prevents a specific failure mode: changing code you don't fully understand. Mapping prevents unintended side effects. |
| **LLM Capability Model** | Mapping what a process sends to the LLM reveals R/P violations — precision tasks given to reasoning, or reasoning tasks given to code. |
| **System Boundary Theory** | Drift audits often reveal that processes designed before a boundary change don't consume data from the new boundary. |

---

## Test Yourself

Before proceeding to the Exploration-First skill, you should be able to answer:

1. Why does mapping the current process precede any other investigation step?
2. What's the difference between an observation and an inference, and why does it matter?
3. When would you trigger a drift audit vs a contract-breach investigation?
4. Why does the process catalog have compounding returns?
5. What does "stop at the earliest leverage point" prevent?
6. Why is build step 6 of 8 rather than step 1?

If these feel clear, proceed to [Exploration-First](../skills/exploration-first.md).

---

## References

- Deming, W. E. (1986). *Out of the Crisis.* — PDCA cycle: iterative investigation before action
- Boehm, B. W. (1988). A Spiral Model of Software Development and Enhancement. — Risk-driven: resolve highest uncertainty before implementation
- Basili, V., Caldiera, G., and Rombach, H. D. (1994). Goal Question Metric paradigm. — Define goals and diagnostic questions before selecting metrics
- Argyris, C., and Schon, D. A. (1978). *Organizational Learning.* — Double-loop learning: revise assumptions, not only actions
- Murphy, G. C., Notkin, D., and Sullivan, K. J. (2001). Software Reflexion Models. — Detect drift between intended and implemented architecture
- Kruchten, P., Nord, R. L., and Ozkaya, I. (2012). Technical Debt: From Metaphor to Theory and Practice. — Proactive identification of architectural debt
