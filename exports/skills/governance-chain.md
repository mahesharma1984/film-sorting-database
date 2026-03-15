# Skill: Governance Chain (Multi-Level Constraint Architecture)

**Purpose:** Build and enforce a five-level constraint chain (Theory → Architecture → Components → Dev Rules → Code) so that proven practices are mechanically enforced, not just documented.
**Addresses:** Implementation drift from documented theory, duplicate inline reimplementations, overly complex first builds, lack of enforcement between docs and code.

---

## Core Principle

**Proven practices should be importable and enforceable, not just described. Each level constrains the next. Fix at the highest divergent level.**

Without a governance chain:
- Developers (and AI agents) reimplement shared patterns from scratch
- Each implementation diverges slightly from the documented spec
- Complexity accumulates in individual components instead of emerging from composition
- Documentation is correct but code ignores it because nothing enforces alignment

---

## The Governance Chain Protocol

### Step 1: Audit Existing Levels

Map what you have at each governance level. Use a traceability matrix:

```
| Proven Practice | L1 Theory | L2 Architecture | L3 Component | L4 Dev Rule | L5 Code | Status |
|---|---|---|---|---|---|---|
| [Practice A]    | doc.md §2 | arch.md §3      | ???           | ???         | file.py | Divergent |
| [Practice B]    | doc.md §4 | arch.md §5      | component.py  | rule 2      | file.py | Faithful  |
```

For each practice, classify:
- **Faithful** — code matches theory through all levels
- **Partial** — some levels present, others missing
- **Divergent** — code contradicts documented spec
- **Missing** — practice not implemented at all

**What to look for in the audit:**
- Constants redefined in multiple files (colours, labels, vocabulary)
- The same structure rendered differently across files
- Documented techniques that appear in theory docs but not in code
- Code that implements a technique but with different parameters than the spec

### Step 2: Fill Missing Levels (Top-Down)

Start at the highest missing level and work down. Never build Level 5 code without Level 3 components, because the code will drift.

#### If Level 1 (Theory) Is Missing

Consolidate proven practices into a **Technique Catalogue** — a single lookup table:

```markdown
## Practice: [Name]

**Theory source:** [document § section]
**Definition:** [canonical spec]
**Parameters:** [what it takes as input]
**Output:** [what it produces]
**Prerequisites:** [what must exist before this practice]
**Level range:** [what complexity levels it operates at]
```

#### If Level 2 (Architecture) Is Missing

Define the **progression map** — the directed graph of how practices compose:

```
Practice A (Level 1-2)
  → produces output X
    → Practice B consumes X (Level 2-3)
      → produces output Y
        → Practice C consumes Y (Level 3-4)
```

Document each transition: what data flows, what level shift occurs, what the student/user produces.

#### If Level 3 (Components) Is Missing

Define **component contracts** — function signatures with required parameters:

```python
def render_practice_a(
    *,
    required_param_1: str,     # Can't skip this
    required_param_2: List[str],  # Enforces the theory requirement
    ceiling: Level,            # Controls complexity
) -> str: ...
```

For each component, specify:
- **Preconditions:** What data must exist upstream
- **Postconditions:** What the output guarantees
- **Invariants:** What must remain true
- **Failure modes:** Hard (stop) vs soft (warn and continue)

#### If Level 4 (Dev Rules) Is Missing

Write **development principles** — explicit rules that reference the components:

```markdown
Rule 1: MVP-First
  Start with minimum functional version. Do not add complexity until
  the basic version is validated by end users.

Rule 2: Import-Don't-Rebuild
  If a proven practice has a component contract, import it.
  Hard failure: duplicate inline implementation in code review.

Rule 3: Ceiling Enforcement
  Every output declares a complexity ceiling. Components validate
  that content does not exceed the ceiling.

Rule 4: Handoff Composition
  Complexity from composing simple outputs, not from individual
  output complexity.

Rule 5: Naming Contract
  User-facing labels use canonical names, never internal identifiers.

Rule 6: End-User Validation Gate
  No output is complete until used by actual end users.
```

### Step 3: Wire Into Workflow

The chain must be discoverable by whoever writes code (human or AI agent):

#### Navigation Integration

Add governance chain routing to your work router:

```markdown
Building or modifying an output generator?
  → Read governance chain from Level 1 down to your working level:
    L1: TECHNIQUE_CATALOGUE.md (what the practice is)
    L2: ARCHITECTURE.md § progression map (where it fits)
    L3: COMPONENT_CONTRACTS.md (how to import it)
    L4: DEVELOPER_GUIDE.md (rules for building)
```

#### Startup Integration

Add to your CLAUDE.md (or equivalent AI instructions):

```markdown
Before any code change, read:
1. [existing startup reads]
2. GOVERNANCE_CHAIN_REFERENCE.md (identify your working level)
```

#### Decision Rule Integration

Add to your development decision rules:

```markdown
N. Enforce governance chain for generator work:
   - Before modifying any generator, read the chain from Level 1 down
   - Import proven practices from component contracts — never reimplement
   - Every output declares a complexity ceiling and enforces it
   - Complexity from handoff composition, not individual complexity
   - Start with MVP — add complexity only after end-user validation
```

#### Search Integration

If you have a documentation search tool (RAG), tag chunks with governance level:

```python
chunk_metadata = {
    "governance_level": 1,  # Theory
    "governance_level": 3,  # Component contract
}
```

This way, a search for "sentence frame" returns the theory spec (L1), the architecture contract (L2), the component interface (L3), and the dev rule (L4) — in constraint order.

---

## Component Contract Design Patterns

### Pattern 1: Required Parameters Enforce Theory

The theory says "verb selection controls complexity." The component enforces this:

```python
def render_sentence_frame(
    *,
    topic: str,
    allowed_verbs: List[str],  # Theory requirement → required parameter
    ceiling: Level,
) -> str: ...
```

If `allowed_verbs` is empty, the component raises an error. The theory requirement is now mechanical.

### Pattern 2: Shared Style Tokens Prevent Drift

Multiple components need the same visual identity. A single source:

```python
def get_style_tokens() -> dict:
    return {
        "category_a": {"primary": "#F9A825", "light": "#FFF9C4"},
        "category_b": {"primary": "#1976D2", "light": "#E3F2FD"},
        "role_1": "#4A90E2",
        "role_2": "#27AE60",
        # ... canonical palette
    }
```

**Invariant:** No generator defines colours inline. All import from `get_style_tokens()`.

### Pattern 3: Validation Gate for Ceiling Compliance

```python
def validate_ceiling(*, content_items: List[str], ceiling: Level) -> GateResult:
    violations = [item for item in content_items if exceeds_ceiling(item, ceiling)]
    if violations:
        return GateResult(passed=False, severity="HARD", detail=f"Ceiling exceeded: {violations}")
    return GateResult(passed=True)
```

Run this after generation, before output. Catches drift mechanically.

### Pattern 4: Handoff Block Makes Composition Visible

```python
def render_handoff_block(
    *,
    current_step: str,
    coming_from: str,       # What prior output is consumed
    going_to: str,          # What next step uses this output
    produced_output: str,   # What this step creates
) -> str: ...
```

Every output includes this block at the top. End users see the composition chain. Developers see the contract.

### Pattern 5: Naming Contract Resolver

```python
def resolve_heading(item_key: str, items: dict) -> str:
    """Returns canonical user-facing name, never internal identifier."""
    item = items.get(item_key, {})
    name = item.get("display_name") or item.get("name")
    if not name or looks_like_internal_id(name):
        raise ValueError(f"No user-facing name for '{item_key}'")
    return name
```

**Hard failure:** An internal identifier like "Group 1" appears as a primary heading.

---

## Migration: From Library Model to Governance Chain

When refactoring existing code to follow the governance chain:

### Priority Order

Rank generators by:
1. **Drift severity** — how far the code diverges from documented theory
2. **End-user impact** — how often this output is used by actual people
3. **Downstream dependency** — how many other components consume this output

Migrate highest-priority generators first.

### Migration Per Generator

1. Read the technique catalogue for each technique the generator uses
2. Check if a component contract exists for each technique
3. If yes: replace inline implementation with component import
4. If no: implement the component first, then import it
5. Add handoff block
6. Add ceiling declaration and validation
7. Replace inline colour/style definitions with shared tokens
8. Verify naming contract compliance

### What Not to Change During Migration

- Don't redesign the generator's purpose or scope
- Don't add new features
- Don't change the data flow between generators
- Only replace inline implementations with component imports and add governance metadata

---

## Integration with Other Skills

| Skill | How Governance Chain Connects |
|---|---|
| **Pattern-First** | The governance chain IS Pattern-First applied to methodology: define the pattern (theory + architecture + component) before populating instances (code). |
| **Constraint Gates** | Governance chain gates are constraint gates applied to knowledge compliance. The component contract is the gate; the function signature is the checkpoint schema. |
| **Failure Gates** | Component contracts use the same hard/soft semantics: hard failure (missing required parameter) stops generation; soft failure (missing optional field) warns and continues. |
| **R/P Split** | Theory and architecture are REASONING work (defining what should exist). Components and code are PRECISION work (implementing it exactly). Don't mix them. |
| **Prototype Building** | Rule 1 (MVP-First) IS prototype building applied to output generation: build the simplest usable version first, validate with end users, then add complexity. |
| **Measurement-Driven** | After migration, measure output quality. Track: did the governance chain improve end-user usability? If not, the components need revision, not the code. |
| **Exploration-First** | The audit step (Step 1) IS exploration-first: map what exists at each level before modifying anything. |
| **Domain Grounding** | Proven techniques in the catalogue are the equivalent of published frameworks: they anchor practice in validated knowledge, not ad hoc invention. |
| **Boundary-Aware Measurement** | Level 3 (Components) is the system boundary between knowledge (theory, architecture) and implementation (rules, code). Validate at this boundary before running expensive generators. |

---

## Diagnostic: Is This a Governance Chain Problem?

| Symptom | Likely Missing Level | What to Check |
|---|---|---|
| Output reimplements a documented technique differently | Level 3 (no importable component) | Does a component contract exist? |
| Output is technically correct but end users can't use it | Level 4, Rule 1 (no MVP-first rule) | Was simplicity validated before complexity? |
| Same visual element looks different across outputs | Level 3 (no shared style tokens) | How many files define this element independently? |
| New generator doesn't follow existing patterns | Level 4, Rule 2 (no import-don't-rebuild rule) | Does the developer know the component exists? |
| Output complexity jumps from Level 1 to Level 4 in one step | Level 4, Rule 4 (no handoff composition rule) | Is there a progression map? |
| Internal labels appear in end-user output | Level 3 + Level 4, Rule 5 (no naming contract) | Does a name resolver exist? |
| Documentation is excellent but code diverges | Level 3 (gap between docs and code) | Is there an enforcement layer? |

---

## Checklist

When building a governance chain:
- [ ] Audited existing levels (traceability matrix completed)
- [ ] Identified which levels are missing for each proven practice
- [ ] Filled missing levels top-down (theory → architecture → components → rules)
- [ ] Component contracts have function signatures with required parameters
- [ ] Dev rules reference specific components (not just principles)
- [ ] Chain wired into navigation (work router, startup reads, decision rules)
- [ ] Generators migrated in priority order (highest drift first)
- [ ] Shared style tokens centralized (no inline definitions)
- [ ] Naming contract enforced (internal identifiers blocked)
- [ ] MVP-first rule applied (simplest usable version validated before adding complexity)
- [ ] End-user validation gate in place (output tested with actual users)

When modifying a generator in a governed system:
- [ ] Read governance chain from Level 1 down to working level
- [ ] Identified which component contracts apply
- [ ] Imported components (not reimplemented inline)
- [ ] Declared complexity ceiling and wired validation
- [ ] Added handoff block (coming from / going to)
- [ ] Used shared style tokens
- [ ] Verified naming contract compliance
- [ ] Set end-user validation status (DRAFT or VALIDATED)
