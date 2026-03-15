# Governance Chain Theory

**Status:** Canonical (Issue #54 implemented 2026-03-15)
**Implementation reference:** `docs/DEVELOPER_GUIDE.md` §Governance Chain Architecture
**Core question:** In a multi-stage pipeline where theory, architecture, components, development rules, and code all need to stay aligned — how do you prevent each level from drifting independently?

---

## Project Context

The film classification pipeline has excellent documentation at L1 (theory essays) and L2 (architecture docs). Issue #54 diagnosed that without L3 enforcement, the system had:

- **Three independent implementations** of director name matching (`satellite.py`, `signals.py`, `classify.py`) — same algorithm, separately maintained
- **Five inline `ClassificationResult()` constructions** — same fields, different subsets, no enforced schema
- **Two methods doing the same satellite evaluation** with subtle semantic differences nobody could verify

The governance chain fix: introduce typed `EnrichedFilm` and `Resolution` dataclasses at L3, making stage boundaries importable and enforceable rather than descriptive.

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
Level 3 — COMPONENTS       How it's mechanically enforced (function signatures, types)
    ↓ constrains
Level 4 — DEV PRINCIPLES   Rules governing how code is written
    ↓ constrains
Level 5 — CODE             Implementation operating within all four layers
```

### In This Project

```
L1 Theory       docs/theory/GOVERNANCE_CHAIN_THEORY.md (this file)
                docs/theory/TIER_ARCHITECTURE.md — why the 4 tiers exist
L2 Architecture docs/architecture/TWO_SIGNAL_ARCHITECTURE.md — two signals + priority chain
L3 Components   lib/pipeline_types.py — typed stage boundary dataclasses (enforcement layer)
                lib/director_matching.py — single shared director matching function
L4 Dev Rules    docs/DEVELOPER_GUIDE.md §Governance Chain Architecture — GC-1 through GC-6
L5 Code         classify.py, lib/signals.py, lib/satellite.py
```

---

## The Principle: Constrain Down, Fix Up

### Principle 1: Each Level Constrains the Next

Theory documents justify architecture. Architecture documents define component interfaces. Components enforce those interfaces through function signatures and validation. Dev rules govern how developers interact with components. Code imports components and follows rules.

**If Level 5 code contradicts Level 3 (component contract), the code is wrong.** Fix the code, not the component. If Level 3 contradicts Level 2 (architecture), the component is wrong. Fix the component, not the architecture. Always fix at the highest divergent level.

### Principle 2: Components Are the Enforcement Layer

The most important level is Level 3. This is where text-based constraints become mechanical constraints.

A theory doc that says "enrichment and routing are separate stages" is advisory. A typed `EnrichedFilm` return type from `_merge_api_results()` is enforceable — the caller must consume the typed fields; it cannot accidentally treat enrichment output as a routing decision.

```python
# L3: Component contract (lib/pipeline_types.py)
@dataclass
class EnrichedFilm:
    director: Optional[str]
    countries: List[str]
    genres: List[str]
    keywords: List[str]
    tmdb_id: Optional[int]
    tmdb_title: Optional[str]
    readiness: str         # 'R0', 'R1', 'R2', 'R3'
    sources: Dict[str, str] = field(default_factory=dict)
    raw: Optional[Dict] = None  # backward compat during transition
```

If a developer wants to use enrichment output for routing, they must use the typed fields. The architecture's requirement is now mechanical.

### Principle 3: Dev Rules Make Components Discoverable

Components alone aren't enough. A developer who doesn't know a component exists will rebuild it inline. Dev rules bridge this gap:

```
Rule GC-4: Director matching through lib/director_matching.match_director()
  All director name matching uses this single function.
  Never reimplement the whole-word vs. substring logic in a new location.
```

The rule makes the component *discoverable* — it tells developers to look for existing components before building.

### Principle 4: Resolvers Own Logic, Builder Owns Construction

The priority chain design separates concerns:
- `_resolve_*()` methods own classification logic (return `Optional[Resolution]`)
- `_build_result()` owns result construction (reads from `Resolution`)
- `classify()` owns priority ordering (first non-None resolution wins)

No resolver constructs a `ClassificationResult`. No builder contains classification logic. This is enforced by Rule GC-1 and GC-2 in the developer guide.

---

## Why Five Levels

You might ask: why not just docs and code? Because the gap between theory and code is too wide for a single jump:

| Gap | What Goes Wrong |
|---|---|
| Theory → Code (skip architecture) | Code implements the spirit but with incompatible interfaces between components |
| Theory → Architecture → Code (skip components) | Architecture describes what should exist but nothing enforces it — each developer reimplements from scratch |
| Theory → Architecture → Components → Code (skip dev rules) | Components exist but developers don't know when to use them — still build from scratch when component doesn't exactly fit |

**Each level fills a gap the levels above can't reach:**
- Theory says *why* something should work a certain way
- Architecture says *what* the interface should look like
- Components make the interface *importable and enforceable*
- Dev rules tell developers *when and how* to use the components
- Code operates *within* all four constraints

---

## Signs You Need a Governance Chain

| Symptom | What's Missing |
|---|---|
| Multiple implementations of the same concept with subtle differences | Level 3 (Components) — no shared importable implementation |
| New code doesn't follow documented principles despite good docs | Level 4 (Dev Rules) — no rules connecting docs to code practice |
| Documented theory is internally consistent but code diverges | Level 3 (Components) — no enforcement layer between theory and code |
| Each new feature reinvents patterns that already exist | Level 4, Rule GC-4 (Import-Don't-Rebuild) — no discovery mechanism |
| System has too many ways to do the same thing | Level 2 (Architecture) — no canonical interface definition |

---

## Connection to Other Theory Docs

| Concept | Connection |
|---|---|
| **TIER_ARCHITECTURE.md** | L1 source for why the 4-tier hierarchy takes this form — constrains `TWO_SIGNAL_ARCHITECTURE.md` (L2) priority chain |
| **TWO_SIGNAL_ARCHITECTURE.md** | L2 architecture for the two-signal pipeline — constrains `lib/pipeline_types.py` (L3) stage boundary types |
| **VALIDATION_ARCHITECTURE.md** | The evidence trail system is itself an L3 component: `_gather_evidence()` enforces that routing logic is auditable |
| **RECURSIVE_CURATION_MODEL.md** | The curation feedback loop (accept/override/enrich/defer) is governed by the same chain — L3 being the review queue and manifest types |
| **Pattern-First (Rule 2)** | The governance chain is Pattern-First applied to methodology: define the pattern (theory + architecture + component) before populating instances (code) |
| **Constraint Gates (Rule 5)** | L3 components are gates: `EnrichedFilm.readiness` gates which resolvers run; `Resolution.confidence` gates what enters the review queue |
