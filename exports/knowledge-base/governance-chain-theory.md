# Governance Chain Theory: Why Multi-Level Constraints Prevent Drift

**Read this before:** Governance Chain skill
**Core question:** In a system where theory, architecture, components, development rules, and code all need to stay aligned — how do you prevent each level from drifting independently?

---

## The Common Assumption

Most developers think about documentation as a reference library. Docs describe the system. Code implements the system. If you update one, you should update the other. The mental model is:

1. **"Docs and code are parallel"** — they describe the same thing from different angles
2. **"Good documentation prevents mistakes"** — if the docs are clear, the code will follow
3. **"More documentation means more alignment"** — write more docs, get better results

In small projects (1-3 files, one developer), this works. In multi-stage systems — especially those where AI agents write code guided by documentation — the parallel model breaks down. Documentation describes intent. Code does whatever it does. Nothing mechanically connects the two.

---

## The Failure That Reveals the Truth

A project has excellent theoretical foundations. The pedagogy theory docs describe proven techniques (sentence frames, paragraph structures, reasoning progressions). The architecture docs describe how worksheets should be structured. 15+ documents, all well-written, all internally consistent.

Then a developer (or AI agent) builds a new worksheet generator. They read the docs. They understand the theory. They produce a 500-line generator that:

- Reimplements a proven sentence frame with slightly wrong slot labels
- Defines its own colour palette (different from 6 other generators)
- Skips the scaffolding progression that the theory docs prescribe
- Produces output that's technically impressive but unusable in practice

**Why?** The docs described what should happen. Nothing *enforced* what should happen. The theory said "use a verb bank to control reasoning depth." But there was no importable component that *required* a verb bank parameter. The architecture said "worksheets should build on each other's output." But there was no handoff contract that *validated* the chain. The developer read the docs, interpreted them through their own lens, and built something that satisfied their interpretation — which diverged from the proven classroom practice.

**This happened 14 times** — once for each generator. Each one reimplemented shared techniques from scratch, producing 7 different colour palettes, 3 different arc role mappings, and 0 verb bank implementations.

**Three failures compounded:**
1. **No mechanical enforcement** — docs described constraints but nothing checked compliance
2. **No importable components** — proven techniques existed as text descriptions, not as code with required parameters
3. **No development rules** — no rule said "import the proven component instead of rebuilding it" or "start with the simplest version first"

---

## The Mental Model: Stacked Constraint Levels

### The Library Model (Wrong)

```
Theory docs  ←→  Architecture docs  ←→  Code

Each references the others. None constrains the others.
Alignment depends on the developer reading everything
and correctly interpreting all of it.
```

### The Governance Chain Model (Right)

```
Level 1 — THEORY           Why this principle exists
    ↓ constrains
Level 2 — ARCHITECTURE     What the interface looks like
    ↓ constrains
Level 3 — COMPONENTS       How it's mechanically enforced (function signatures, schemas)
    ↓ constrains
Level 4 — DEV PRINCIPLES   Rules governing how code is written
    ↓ constrains
Level 5 — CODE             Implementation operating within all four layers
```

Each level constrains the level below it. Not by description — by *structure*. Level 3 (components) has function signatures with required parameters. If a developer doesn't provide the required parameter, the code doesn't compile or run. Level 4 (dev principles) says "import the component, don't rebuild it." If a code review finds an inline reimplementation, the PR is rejected.

**The key difference:** In the library model, alignment is optional and depends on interpretation. In the governance chain model, alignment is structural and enforced by the layers above.

### Why Five Levels

You might ask: why not just docs and code? Why five levels? Because the gap between theory and code is too wide for a single jump:

| Gap | What Goes Wrong |
|---|---|
| Theory → Code (skip architecture) | Code implements the spirit of the theory but with incompatible interfaces between components |
| Theory → Architecture → Code (skip components) | Architecture describes what should exist but nothing enforces it in code — each generator reimplements from scratch |
| Theory → Architecture → Components → Code (skip dev rules) | Components exist but developers don't know when to use them — they still build from scratch when the component doesn't exactly fit |

**Each level fills a gap the levels above can't reach:**
- Theory says *why* something should work a certain way
- Architecture says *what* the interface should look like
- Components make the interface *importable and enforceable*
- Dev rules tell developers *when and how* to use the components
- Code operates *within* all four constraints

---

## The Principle: Constrain Down, Fix Up

### Principle 1: Each Level Constrains the Next

Theory documents justify architecture. Architecture documents define component interfaces. Components enforce those interfaces through function signatures and validation. Dev rules govern how developers interact with components. Code imports components and follows rules.

**If Level 5 code contradicts Level 3 (component contract), the code is wrong.** Fix the code, not the component. If Level 3 contradicts Level 2 (architecture), the component is wrong. Fix the component, not the architecture. Always fix at the highest divergent level.

### Principle 2: Components Are the Enforcement Layer

The most important level is Level 3 — Components. This is where text-based constraints become mechanical constraints. A theory doc that says "use a verb bank sorted by reasoning depth" is advisory. A function signature that requires `allowed_verbs: List[str]` and `ceiling: ReasoningLevel` is enforceable.

```python
# Level 3: Component contract
def render_sentence_frame(
    *,
    topic: str,
    allowed_verbs: List[str],
    ceiling: ReasoningLevel,  # Can't skip this parameter
    detail: str,
    effect: str,
) -> str: ...
```

If a developer wants to render a sentence frame, they must provide a verb bank and a ceiling. The theory's requirement is now mechanical. You can't accidentally skip it.

### Principle 3: Dev Rules Make Components Discoverable

Components alone aren't enough. A developer who doesn't know a component exists will rebuild it inline. Dev rules bridge this gap:

```
Rule 2: Import-Don't-Rebuild
  If a proven technique has a component contract, import and compose it.
  Do not reimplement it inline.
  Hard failure trigger: duplicate inline implementation found in code review.
```

The rule makes the component *discoverable* — it tells developers to look for existing components before building. Combined with a component catalogue, this prevents the "each generator rebuilds everything from scratch" pattern.

### Principle 4: MVP-First Prevents Complexity Drift

Even with components and rules, generators can become too complex on first build. A dev rule addresses this directly:

```
Rule 1: MVP-First
  Start with the smallest usable output.
  Minimum: one theme, one technique, 2-3 examples.
  Do not add complexity until this version is validated by end users.
```

This rule addresses a specific failure mode: the tendency to build the maximum-complexity version first, which produces technically impressive but practically unusable output. Starting simple forces the developer (or AI agent) to validate the basic case before adding layers.

### Principle 5: Handoff Composition Over Individual Complexity

The deepest principle: **complexity should emerge from composing simple components, not from making individual components complex.**

In a multi-worksheet system, each worksheet should do one thing well at one reasoning level. The student progresses through worksheets, building complexity through the handoff chain:

```
Worksheet A (simple, Level 1-2)
  → produces output X
    → Worksheet B consumes X (Level 2-3)
      → produces output Y
        → Worksheet C consumes Y (Level 3-4)
          → full complexity achieved through composition
```

If instead you try to put all the complexity into Worksheet A, you get:
- A 500-line generator that tries to scaffold from Level 1 to Level 4 in one worksheet
- An output that's overwhelming for end users
- A maintenance burden where one change affects everything

**The governance chain itself follows this principle.** Each level does one thing. Complexity emerges from their composition.

---

## Analogy: Software Dependency Management

The governance chain is the knowledge-management equivalent of software dependency management:

| Software | Governance Chain |
|---|---|
| Published library (npm, pip) | Proven technique (documented in theory) |
| Package interface (API) | Component contract (function signature) |
| `import` statement | Dev rule: "import, don't rebuild" |
| Compiler/type checker | Gate/validator: "does this satisfy the contract?" |
| Application code | Generator code |

In software, nobody reimplements `sort()` inline. You import it. The function signature tells you what parameters it needs. The type checker verifies you're using it correctly. If your code compiles and passes tests, you're aligned with the library's contract.

The governance chain applies the same pattern to knowledge. Nobody should reimplement a proven pedagogical technique inline. You import the component. The function signature tells you what parameters it needs. The validator checks that the output satisfies the contract.

---

## Signs You Need a Governance Chain

| Symptom | What's Missing |
|---|---|
| Multiple implementations of the same concept with subtle differences | Level 3 (Components) — no shared importable implementation |
| New code doesn't follow documented principles despite good docs | Level 4 (Dev Rules) — no rules connecting docs to code practice |
| Documented theory is internally consistent but code diverges | Level 3 (Components) — no enforcement layer between theory and code |
| End-user output is technically correct but practically unusable | Level 4, Rule 1 (MVP-First) — no simplicity constraint |
| Each new feature reinvents patterns that already exist | Level 4, Rule 2 (Import-Don't-Rebuild) — no discovery mechanism |
| System has too many ways to do the same thing | Level 2 (Architecture) — no canonical interface definition |

---

## How to Build a Governance Chain

### Step 1: Audit What Exists

Before building anything, map what you already have at each level:

```
Level 1 — Theory: Which principles are documented? Which are implicit?
Level 2 — Architecture: Which interfaces are specified? Which are ad hoc?
Level 3 — Components: Which patterns are shared? Which are duplicated?
Level 4 — Dev Rules: Which rules exist? Which are missing?
Level 5 — Code: How much of it follows levels 1-4? How much diverges?
```

The audit produces a traceability matrix: for each proven technique, which levels have it and which levels are missing.

### Step 2: Fill Gaps Top-Down

Start at the highest missing level and work down:
- If theory is missing, don't build components — you don't know what to enforce
- If architecture is missing, don't write dev rules — you don't know what the interfaces should be
- If components are missing, don't blame the code — there's nothing to import

### Step 3: Wire Into Workflow

The chain only works if it's discoverable. Wire it into whatever tools developers (or AI agents) use to navigate the codebase:
- Navigation tools should route to the governance chain before code changes
- Search tools should return results tagged by governance level
- Startup instructions should include the chain as a required read

---

## Connection to Other Knowledge Base Concepts

| Concept | Connection to Governance Chain Theory |
|---|---|
| **Causality & Systems** | The governance chain IS a causal chain: theory causes architecture, architecture causes components, components cause rules, rules cause code. Violating this ordering produces the same backward-causality failures as in pipeline design. |
| **Constraint Theory** | When a generator produces bad output, the governance chain tells you WHERE to trace: is the theory wrong? Is the component missing? Is the dev rule absent? It's the same "fix the constraint, not the symptom" principle applied to knowledge management. |
| **Failure Theory** | Missing governance levels are silent failures. The code runs. The output looks plausible. But it diverges from proven practice in ways that only become visible during end-user validation (classroom, production, etc.). |
| **Task Design Theory** | The governance chain decomposes "make good output" into five levels of increasingly concrete constraints. Each level is a task that constrains the next — the same decomposition principle applied to knowledge. |
| **Pattern-First** | The governance chain is Pattern-First applied to methodology: define the pattern (theory + architecture + component) before populating instances (generator code). |
| **Exploration Theory** | Before modifying a governance chain, audit what exists at each level. Map before modify — the same principle. |
| **Domain Grounding** | Proven techniques in the governance chain are the equivalent of published frameworks in domain grounding — they anchor practice in validated knowledge rather than ad hoc invention. |
| **LLM Capability Model** | LLM agents are especially prone to reimplementing from scratch because they don't carry state between sessions. The governance chain compensates by making constraints structural rather than memory-dependent. |
| **System Boundary Theory** | The Level 3 component layer IS a system boundary — it separates the knowledge domain (theory, architecture) from the implementation domain (dev rules, code). Cheap validation at this boundary catches drift before expensive output is produced. |

---

## Test Yourself

Before proceeding to the Governance Chain skill, you should be able to answer:

1. Why doesn't good documentation alone prevent code from diverging from theory?
2. What role does Level 3 (Components) play that documentation can't fill?
3. Why does "fix at the highest divergent level" matter?
4. How does MVP-First prevent complexity drift in AI-generated code?
5. Why should complexity emerge from composition rather than individual component complexity?
6. What's the analogy between `import` in software and "import-don't-rebuild" in a governance chain?

If these feel clear, proceed to [Governance Chain](../skills/governance-chain.md).

---

## References

- Parnas, D. (1972). *On the Criteria To Be Used in Decomposing Systems into Modules.* — Information hiding; interfaces constrain implementations
- Meyer, B. (1992). *Applying Design by Contract.* — Preconditions, postconditions, invariants as enforceable specifications
- Gamma et al. (1994). *Design Patterns.* — Reusable solutions as importable components
- This repository's Issues #557, #558: Pedagogical governance chain — the case study that motivated this document
