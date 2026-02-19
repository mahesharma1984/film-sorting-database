# Issue #26: Knowledge-base gaps and missing cross-references in exports/

**Severity:** Low-Medium (no runtime impact; affects future development quality)
**Component:** `exports/knowledge-base/`, `exports/skills/`
**Type:** Documentation / knowledge architecture
**Discovered via:** Architecture analysis of exports/

---

## Summary

The `exports/knowledge-base/` and `exports/skills/` directories form a coherent system for reasoning about pipeline design. Eight gaps weaken it: six missing skills or theory sections, and two sets of cross-references that are absent from the skills layer but present in the corresponding theory documents. None of these gaps affect the running classifier. They affect the quality of reasoning when extending the system — which is exactly when this knowledge base is consulted.

The gaps fall into two categories:
- **Coverage gaps:** Task types, optimization levels, and failure modes that are fully theorized but have no operational skill
- **Cross-reference gaps:** Connections between skills that are stated in the theory docs but not surfaced in the skill docs themselves

---

## Coverage Gap 1: Creative and Discovery task types have no skills

**Theory location:** `exports/knowledge-base/task-design-theory.md` (sections on Creative Tasks and Discovery Tasks)

**What the theory says:**

Task design theory defines four task types:
- **Reasoning** — interpretation, judgment, synthesis → give to LLM
- **Precision** — exactly one correct answer → give to code
- **Creative** — novel output, subjective quality → human with AI assistance
- **Discovery** — don't know what you're looking for → human exploration

The R/P Split skill operationalizes Reasoning and Precision completely. Creative and Discovery are fully theorized but drop out at the skill layer.

**Why this matters in practice:**

Creative and Discovery tasks appear regularly in this project:
- Adding a new Satellite category (Discovery: you're exploring what films exist before you can define routing rules)
- Deciding whether a director belongs in Core or Reference (Creative/Judgment: there is no algorithm for this)
- Choosing what 50 films constitute the Reference canon (Creative: curatorial judgment, not classification)
- Deciding when to widen a decade boundary (Discovery: requires surveying the collection before the rule can be specified)

Without an operational skill, the only guidance is "this is a Discovery task" — but there's no protocol for how to run one.

**What's needed:**

A skill covering:
- How to scope a Discovery task (define the question before exploring, otherwise exploration is infinite)
- When to stop Discovery and move to Execution (the Rabbit Hole Detection section in prototype-building.md is partially applicable here)
- How Creative tasks are evaluated (if there's no single correct answer, what does "done" look like?)
- The handoff from Creative/Discovery output into Precision or Reasoning tasks

---

## Coverage Gap 2: Environment-First Corollary has no skill

**Theory location:** `exports/knowledge-base/causality-and-systems.md` (Environment-First Corollary section)

**What the theory says:**

Causality theory defines three levels of optimization:
- **Level 1:** Schema → Instances (covered by Pattern-First skill)
- **Level 2:** Optimized Input → Schema → Instances
- **Level 3:** Meta-optimization → Optimized Input → Schema → Instances

Levels 2 and 3 state that before you derive a pattern/schema, you should optimize the *input environment* so that the pattern you derive is the best possible one, not just the best one given mediocre input. Patterns derived from suboptimal input produce suboptimal downstream instances, even if the derivation logic is correct.

**Why this matters in practice:**

This project has a direct application: the quality of Satellite routing rules depends on how well the API data is normalized before routing logic sees it. If TMDb country data is sparse (empty `countries: []`) and OMDb data hasn't been enriched yet, routing rules derived or tuned against that input will be systematically suboptimal. The Input Optimization stage (API enrichment, cache warming, country code normalization) is the Level 2 preparation that enables better Level 1 pattern derivation.

No skill tells you *when* to add an input optimization stage, what it should contain, or how to validate that it improved the downstream schema quality.

**What's needed:**

An addition to the Pattern-First skill (or a standalone skill if substantial enough) covering:
- How to recognize when input quality is limiting schema quality
- The three-level hierarchy with worked examples
- When Level 2 optimization is worth adding vs. when Level 1 is sufficient
- How to measure whether input optimization actually improved schema quality (connects to Measurement-Driven Dev)

---

## Coverage Gap 3: Absence-based failure handling exists only in theory

**Theory location:** `exports/knowledge-base/failure-theory.md:234-279` (Absence-Based Failures section)

**What the theory says:**

Some system properties are defined by *absence* rather than presence. They require scope statements ("X does not occur across the dataset") rather than located instances ("X occurs at position Z"). The theory provides a complete treatment:
- Why presence-based gate logic produces syntactically valid but semantically wrong evidence for absence-based properties
- The correct gate design (scope statement + range + property, not located quote)
- The failure signal (a fabricated "located" instance where a scope statement was needed)
- The connection to abstraction levels (absence-based entities cluster at Levels 5-6)

**What the skill says:**

`exports/skills/failure-gates.md` has no section on absence-based failures. The gate design template in the skill is entirely presence-based (`did we find evidence?`, `is this field populated?`). A developer reading only the skill will implement presence-based gates for all failure modes, which will silently fail for absence-based properties.

**Why this matters in practice:**

The film classification system has absence-based properties:
- "No Core director films are misrouted to Satellite" — verified by the absence of Core directors in the Satellite manifest, not by finding them
- "No films exceed the Satellite cap" — a cap violation is detected by absence of overflow, not by presence of an instance
- "No duplicate films exist across tiers" — verified by absence of duplicates in the manifest

Each of these needs a scope gate ("across all N classified films, no Core director appears in the Satellite manifest"), not a presence gate.

**What's needed:**

A section in `failure-gates.md` mirroring the theory's treatment:
- The two gate types: presence-based and absence-based
- The gate design template for absence-based properties (scope, range, property name)
- Examples relevant to the film classification domain
- The connection to abstraction levels from domain-grounding theory

---

## Coverage Gap 4: Taxonomy evolution has no theory or skill

**Theory location:** `exports/knowledge-base/domain-grounding-theory.md` (Three-Taxonomy Problem section)

**What the theory covers:**

Domain grounding theory defines the three-taxonomy problem (detection, processing, output taxonomies diverging over time) and prescribes a canonical taxonomy as the fix. The treatment is entirely framed as prevention: establish the canonical taxonomy once, anchor it to a published framework, and all stages extend it rather than replacing it.

**What's missing:**

Real systems discover that their taxonomy is wrong or incomplete *after* it's been deployed. A new film nation emerges as significant (e.g., Romanian New Wave in the 2000s). A category turns out to be two distinct things (Pinku Eiga vs. Japanese Exploitation, which this project already split). A published framework is updated.

Neither the theory nor the skills address managed taxonomy evolution:
- How to add a new category without introducing the drift the grounding was designed to prevent
- How to split an existing category without corrupting the existing classification of films that were in the old category
- How to handle the transition period when films classified under the old category need to be reclassified
- How to know when a taxonomy update is complete (what does the post-update validation look like?)

**Why this matters in practice:**

Every Issue in this project that touches Satellite categories (`#6`, `#14`, `#20`) is implicitly a taxonomy evolution event. `#20` widened Indie Cinema and Brazilian Exploitation. `#14` narrowed American Exploitation and added French New Wave. These were done ad hoc. There is no protocol for ensuring that existing classifications remain correct after a rule change, no validation that the pre-change manifest is consistent with post-change rules, and no checklist for when a category change is complete.

**What's needed:**

A section in domain-grounding-theory.md and a corresponding addition to the domain-grounding skill covering:
- The three taxonomy change types: Add category, Split category, Retire category
- For each: what existing classifications are at risk, what validation is needed, what the rollback path is
- The consistency check: after any rule change, re-run `classify.py` on already-classified films and verify the change produced the expected deltas (connect to Measurement-Driven Dev: after-change breadth measurement)

---

## Coverage Gap 5: Survival rate thresholds are asserted without derivation or calibration guidance

**Theory location:** `exports/knowledge-base/constraint-theory.md`
**Skill location:** `exports/skills/constraint-gates.md`

**What both documents say:**

Both the theory and the skill introduce the same thresholds:
- Below 50% observation survival → ERROR
- 50–70% survival → WARNING
- Above 70% → HEALTHY

These propagate without any derivation, empirical basis, or calibration guidance.

**The problem:**

A reader building a different pipeline (or this pipeline under different conditions) has no basis for knowing whether 50% is appropriate. A pipeline with high-cost downstream stages might need 80% as the error threshold. A pipeline with cheap, reversible downstream stages might tolerate 40%. The current framing presents the thresholds as universal when they are illustrative defaults.

Additionally, both documents reference "this repository's Issue #415" as the measurement basis — a reference that no reader can access, which undermines the empirical grounding the theory claims.

**What's needed:**

In both constraint-theory.md and constraint-gates.md, add a calibration section:
- Explicitly label 50%/70% as defaults, not universal thresholds
- Provide the derivation logic: "set the error threshold at the survival rate where downstream output quality falls below acceptable" — i.e., it is derived from your specific cost function
- Give the calibration procedure: run the pipeline at different survival rates, measure output quality, find the knee of the curve
- Note that the thresholds should be named constants (already in the skill) specifically to make them easy to change during calibration

---

## Cross-Reference Gap 1: `failure-gates.md` skill missing three connections

**Failure theory's connection table** lists six concepts:
LLM Capability Model, Causality & Systems, Measurement Theory, Task Design, Domain Grounding Theory, System Boundary Theory

**`failure-gates.md` integration table** lists only three:
R/P Split, Pattern-First, Measurement-Driven

**Three missing connections and why they matter:**

**Missing: Constraint Gates**

The theory document explicitly states: *"Constraint Theory tells you WHERE to put gates; Failure Theory tells you HOW to design each gate."*

This is the most important operational relationship in the entire knowledge base. Someone implementing failure gates without knowing about constraint gates will place gates in the wrong locations — optimizing gate design at stages that aren't the binding constraint. The two skills are designed to be used together, but someone reading only failure-gates.md will not know this.

**Missing: Domain Grounding**

The theory says: *"Entities at different abstraction levels need different failure gates."* Absence-based entities (Levels 5-6) need scope-statement gates; presence-based entities (Levels 1-4) need instance gates. Without this connection, a developer designing gates for a high-abstraction property will use the wrong gate type.

**Missing: System Boundary Theory / Boundary-Aware Measurement**

The theory says: *"Hard gates at the system boundary catch the most costly failures."* The system boundary is the highest-leverage location for a hard gate. Without this connection, developers will distribute gates evenly across stages rather than concentrating the hard gates at the boundary.

**Fix:** Add three entries to the `failure-gates.md` integration table:

```
| Constraint Gates | Use constraint protocol first to find WHERE to put gates; then use failure gates to design HOW each gate works |
| Domain Grounding | Abstraction level determines gate type: Levels 1-4 use presence-based gates; Levels 5-6 use scope/absence-based gates |
| Boundary-Aware Measurement | Hard gates at the system boundary catch the most costly failures; place strongest gates at the cost cliff |
```

---

## Cross-Reference Gap 2: `pattern-first.md` skill missing circular dependency resolution

**Causality theory** covers three distinct failure modes:
- Backwards causality (A explains B instead of constraining it) — covered in pattern-first.md
- Post-hoc rationalization (generate then justify) — covered in pattern-first.md
- **Circular dependencies** (A needs B's output, B needs A's output) — NOT in pattern-first.md

Circular dependencies are a qualitatively different problem. They cannot be resolved by swapping order (unlike backwards causality). The theory's resolution principle is: "establish one side from principles external to the circle." But it does not provide:
- A procedure for identifying which side to establish first
- What "external to the circle" means operationally
- How to recognize a circular dependency before it creates downstream problems

**Why this matters in practice:**

The film classification system has a potential circular dependency in its API enrichment design: the classifier needs the director to determine the tier, but the API lookup uses the title to find the director, and the title is cleaned using rules that assume some knowledge of what tier the film is likely in (e.g., `_clean_title_for_api()` removes format signals that are more common in certain collection contexts). This is a weak circularity, but the pattern is present.

**Fix:** Add a section to `pattern-first.md`:
- Name circular dependencies as a distinct third failure mode (after backwards causality and post-hoc rationalization)
- Describe the detection pattern: if A's correctness improves with B's output and B's correctness improves with A's output, you have a circular dependency
- Give the resolution principle: identify which side can be established from first principles (not from the other side), establish it first, then let the other side depend on it
- Note the connection to the R/P split: circular dependencies often arise when a REASONING step and a PRECISION step are too tightly coupled — separating them usually reveals which side is foundational

---

## Proposed Fix: Staged approach

Given that all items are documentation-only, no prioritisation by runtime impact applies. Order by return on investment:

### Stage 1: High-leverage cross-reference additions (one afternoon)

These require adding ~3-5 sentences per connection to existing skill documents:

1. Add Constraint Gates, Domain Grounding, and Boundary-Aware Measurement to `failure-gates.md` integration table
2. Add Circular Dependencies section to `pattern-first.md` diagnostic section
3. Add calibration note to `constraint-gates.md` threshold section

### Stage 2: Absence-based failure gates section (half day)

Add a full section to `failure-gates.md` covering absence-based failure modes. Reuse the theory's treatment directly — this is an expansion of existing content into the skill layer, not new content.

### Stage 3: Environment-First Corollary in pattern-first skill (half day)

Add a Level 2 section to `pattern-first.md` (or a new `environment-first.md` skill if the content is substantial). Include the three-level hierarchy and a worked example using the film classification pipeline's API enrichment stage.

### Stage 4: Taxonomy evolution section (one day)

Add a section to `domain-grounding-theory.md` and a corresponding addition to `domain-grounding.md` skill covering the three change types (Add, Split, Retire) with validation checklists. This requires working through at least one real example from this project's history (e.g., the Issue #14 French New Wave addition or Issue #6 Pinku/Japanese Exploitation split).

### Stage 5: Creative and Discovery task skill (one day)

Write a new skill document `creative-discovery.md` covering the two unoperationalized task types. This is new content and the most effort-intensive item, but also the one most likely to be needed when extending the Satellite categories or updating the Reference canon.

---

## Acceptance Criteria

- [ ] `failure-gates.md` integration table includes Constraint Gates, Domain Grounding, Boundary-Aware Measurement
- [ ] `pattern-first.md` diagnostic section includes Circular Dependencies as a named failure mode with detection pattern and resolution procedure
- [ ] `constraint-gates.md` threshold section notes that 50%/70% are calibratable defaults, not universal constants, and gives the calibration procedure
- [ ] `failure-gates.md` has an Absence-Based Failures section mirroring the theory treatment
- [ ] `pattern-first.md` (or new skill) covers Environment-First Corollary Levels 2-3
- [ ] `domain-grounding.md` skill has a Taxonomy Evolution section covering Add, Split, and Retire change types
- [ ] New `creative-discovery.md` skill (or equivalent section) operationalizes Creative and Discovery task types
- [ ] `exports/skills/README.md` updated to reflect any new skill documents
