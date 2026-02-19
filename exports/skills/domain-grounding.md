# Skill: Domain Grounding (Anchoring Decisions in Published Theory)

**Purpose:** Prevent taxonomy drift and classification inconsistency by grounding pipeline categories in published frameworks.
**Addresses:** Invented categories that drift over time, classification disagreements between team members, unfalsifiable design decisions, competing parallel taxonomies.

---

## Core Principle

**Every classification taxonomy in your pipeline should trace to a published framework. Entity processing priority should follow abstraction level, not frequency.**

Without domain grounding:
- Categories mean different things to different people on the same team
- Taxonomies fragment as different stages invent their own classification schemes
- Design decisions can't be validated against an external standard
- New team members can't learn the taxonomy without oral history

---

## The Domain Grounding Protocol

### Step 1: Identify Your Classification Dimensions

List every place in your pipeline where entities are classified, categorized, or sorted into types:

```
Example:
  Stage 2: Entities classified by "type" (structural, stylistic, semantic)
  Stage 4: Entities classified by "priority" (high, medium, low)
  Stage 5: Entities classified by "extraction mode" (exact, approximate, inferred)
```

For each classification, note:
- How many categories exist?
- Who defined them (one person? team consensus? published source?)
- Are they documented?

### Step 2: Find Published Theory

For each classification dimension, search for published frameworks that address it:

```
Classification need:    "Classify entities by function"
Published framework:    Halliday's SFL metafunctions (1985)
Mapping:               Our "structural" → SFL "ideational"
                       Our "stylistic" → SFL "interpersonal"
                       Our "connective" → SFL "textual"
```

**Where to look:**
- Academic textbooks in your domain
- Professional standards and taxonomies
- Published classification systems (ICD codes, NAICS codes, etc.)
- Widely-used open-source schemas in your field

**If no published framework exists:** Document your taxonomy formally with definitions, boundary conditions, and classification tests. Treat it as a local standard and require all stages to reference it.

### Step 3: Map Categories to Published Framework

Create an explicit mapping table:

```markdown
| Our Category | Published Category | Source |
|---|---|---|
| Structural | Ideational metafunction | Halliday (1985) |
| Stylistic | Interpersonal metafunction | Halliday (1985) |
| Connective | Textual metafunction | Halliday (1985) |
```

**What to check:**
- Does every category map to something published? (Coverage)
- Does any published category lack a mapping? (Gaps)
- Do multiple categories map to the same published category? (Ambiguity)
- Does any category map to multiple published categories? (Overloading)

### Step 4: Document the Mapping

Put the mapping in a canonical document that all stages reference:

```markdown
# Entity Taxonomy Reference

## Source Framework
Halliday, M.A.K. (1985). An Introduction to Functional Grammar.

## Category Definitions
| Category | Definition | Published Correspondence | Classification Test |
|---|---|---|---|
| Structural | Entities that organize... | Ideational (Halliday) | "Does this entity represent..." |
| Stylistic | Entities that position... | Interpersonal (Halliday) | "Does this entity affect..." |
| Connective | Entities that create... | Textual (Halliday) | "Does this entity connect..." |
```

**Key:** Include a **classification test** for each category — a question that resolves ambiguous cases. This is what prevents two people from classifying the same entity differently.

### Step 5: Use Abstraction Levels for Processing Priority

When entities need to be ranked for processing, use abstraction level as the primary dimension:

```
Priority 1: Level 5-6 (Structural/Abstract)
  → These are the highest-meaning entities but statistically rare
  → Processing: characterize the whole, scope statements

Priority 2: Level 3-4 (Figurative/Symbolic)
  → These carry second-order meaning through specific instances
  → Processing: track across dataset, locate key instances

Priority 3: Level 1-2 (Concrete/Descriptive)
  → These are frequent but carry meaning mainly through accumulation
  → Processing: sample representative instances
```

**Why not frequency?** Frequency-based ranking biases toward concrete entities. A data point that appears 100 times at Level 1 is less significant than a pattern that appears 5 times at Level 4, because the Level 4 entity carries more meaning per occurrence.

---

## Multi-Layer Taxonomy Design

### When to Use Multiple Layers

| Signal | What It Means |
|---|---|
| Same entity belongs to multiple categories | Your "categories" are actually multiple dimensions |
| Team members disagree on classification | They're thinking about different dimensions |
| Adding new entities requires new hybrid categories | Flat taxonomy can't encode multiple dimensions |
| Categories overlap in confusing ways | Dimensions are conflated |

### How to Design Layers

```
1. List all the dimensions along which entities vary
   "Function, scope, abstraction level, ..."

2. For each dimension, find a published framework
   "Function → Halliday's metafunctions"
   "Scope → localized vs pervasive"

3. Verify independence
   "Can I classify an entity's function without knowing its scope?"
   Yes → independent layers (good)
   No → coupled dimensions (redesign)

4. Create one layer per independent dimension
   Layer 1: Function (ideational / interpersonal / textual)
   Layer 2: Scope (localized / pervasive / structural)
   Layer 3: Abstraction (concrete / figurative / symbolic / abstract)
```

### The Canonical Taxonomy Pattern

Avoid the three-taxonomy problem (detection taxonomy, processing taxonomy, output taxonomy drifting apart):

```
CANONICAL TAXONOMY (published framework, single source of truth)
        │
        ├── Detection: uses canonical categories + detection attributes
        │   (adds: confidence, method, position)
        │
        ├── Processing: uses canonical categories + processing metadata
        │   (adds: priority, extraction mode, dependencies)
        │
        └── Output: uses canonical categories + output formatting
            (adds: display order, presentation format)

Rule: All stages REFERENCE the canonical taxonomy.
      No stage REPLACES it with a parallel system.
```

---

## Decision Rules

### The Grounding Check

Before adding a new category to any taxonomy:

```
1. Does this category exist in the published framework?
   Yes → use the published name and definition
   No  → is it a subset of an existing published category?
         Yes → define it as a subcategory with documented criteria
         No  → is the published framework incomplete for your needs?
               Yes → document the extension formally, noting the gap
               No  → reconsider whether you need this category
```

### The Priority Decision

When ranking entities for processing:

```
1. What abstraction level is this entity?
   Level 5-6: high priority (rare but meaningful)
   Level 3-4: medium priority (moderate frequency, moderate meaning)
   Level 1-2: lower priority (frequent but individually less meaningful)

2. Within the same level, rank by:
   - Downstream consumption need (what does the next stage need most?)
   - Domain significance (what would a domain expert prioritize?)
   - Frequency (as tiebreaker only)
```

---

## When to Apply

| Situation | Apply Domain Grounding? |
|---|---|
| Taxonomy propagates through 3+ pipeline stages | Yes — categories must be stable across stages |
| Multiple people classify entities | Yes — shared external standard prevents drift |
| Classification affects processing strategy | Yes — wrong category → wrong processing |
| Taxonomy has 15+ categories | Yes — too many to maintain by intuition |
| Throwaway prototype | No — categories won't survive long enough to drift |
| Single-stage classification | Maybe — depends on complexity |
| Categories are user-configurable | No — users define their own taxonomy |

---

## Integration with Other Skills

| Skill | How Domain Grounding Connects |
|---|---|
| **Pattern-First** | The taxonomy IS the pattern. Domain grounding establishes the schema; Pattern-First ensures instances are populated after the schema is stable. |
| **R/P Split** | Taxonomy design is a REASONING task (requires domain expertise). Entity classification against a grounded taxonomy is a PRECISION task (apply rules). Don't mix them. |
| **Measurement-Driven** | You can measure taxonomy quality: inter-rater agreement, coverage of published categories, propagation consistency across stages. |
| **Constraint Gates** | When extraction produces wrong results, check whether the taxonomy handoff is the constraint — are entities arriving with correct classifications? |
| **Failure Gates** | Taxonomy drift is a silent failure. Add gates that check classification consistency across stages. |

---

## Checklist

When designing a new taxonomy:
- [ ] Identified all classification dimensions in the pipeline
- [ ] Found published framework(s) for each dimension
- [ ] Created explicit mapping table (our categories → published categories)
- [ ] Documented classification tests for ambiguous cases
- [ ] Verified layers are independent (if multi-layer)
- [ ] Established canonical taxonomy as single source of truth
- [ ] All pipeline stages reference canonical taxonomy (no parallel systems)

When adding a new entity type:
- [ ] Classified on each layer using published framework definitions
- [ ] Assigned abstraction level (1-6)
- [ ] Determined processing strategy based on abstraction level
- [ ] Updated canonical taxonomy document
- [ ] Verified downstream stages can handle the new entity type
