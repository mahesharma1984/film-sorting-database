# Domain Grounding Theory: Why Published Frameworks Beat Invented Categories

**Read this before:** Domain Grounding skill
**Core question:** How do you design classification systems that stay consistent, scalable, and defensible — instead of drifting into arbitrary categories?

---

## The Common Assumption

Most developers invent their own classification systems. If a pipeline needs to categorize entities, they brainstorm categories that seem reasonable, assign labels, and start building:

1. **"We know our domain"** — Categories based on team intuition and experience
2. **"Labels are just labels"** — What matters is the code, not the taxonomy
3. **"We'll refine later"** — Start with rough categories, improve iteratively

In small systems these work fine. In multi-stage pipelines — especially those where categories propagate through multiple stages, inform downstream decisions, and interact with each other — all three assumptions lead to taxonomy drift, classification inconsistency, and eventually unmaintainable systems.

---

## The Failure That Reveals the Truth

A text analysis pipeline classifies entities into three categories: "structural," "stylistic," and "semantic." These categories were invented by the team based on what seemed natural. The pipeline works well for several months.

Then problems accumulate:

1. **Category drift:** Different team members classify the same entity differently. "Repetition" — is it structural (it creates rhythm), stylistic (it creates emphasis), or semantic (it carries meaning)? Nobody agrees, because the categories weren't defined against a formal framework.

2. **Taxonomy fragmentation:** A second developer creates a parallel classification for a downstream stage — "surface," "deep," and "analytical." These overlap with the original three categories but don't align. Now two competing taxonomies coexist, with no clear mapping between them.

3. **Unfalsifiable decisions:** When the team debates whether an entity is "structural" or "semantic," there's no objective arbiter. The categories are their own definitions. You can't look up the answer because the categories don't exist outside the team's heads.

**Root cause:** The categories were *invented* rather than *grounded*. They had no anchor in published theory, so they couldn't be validated against an external standard.

---

## The Mental Model: Grounded Classification

### Why Grounding Matters

A grounded classification traces every category to a published framework. This provides three things invented categories lack:

1. **Falsifiability** — If a published framework defines Layer X as "structures that organize narrative sequences," you can objectively test whether an entity belongs there. The definition exists outside your team.

2. **Stability** — Published frameworks have been refined through peer review, application, and critique. Their categories are typically more robust than anything a team invents in a brainstorming session.

3. **Communicability** — When you cite a published source, anyone who reads that source understands your categories. When you invent categories, every new team member needs a custom explanation.

### The Grounding Protocol

```
1. Identify your classification need
   "I need to classify entities along dimension X"

2. Search for published theory that covers dimension X
   "What published framework addresses this classification?"

3. Map your categories to the framework's categories
   "My 'structural' → their 'ideational metafunction'"

4. Document the mapping
   "Category: Structural → Source: Halliday (1985), ideational metafunction"

5. Use the framework's internal distinctions for subcategories
   "Within ideational: material, mental, relational, verbal, existential"
```

**The key insight:** You're not doing academic research. You're borrowing categorization schemes that have been stress-tested across multiple applications by domain experts. This is the same principle as using a well-tested library instead of writing your own.

---

## Entity Abstraction Levels

One of the most common classification dimensions is **abstraction level** — how concrete or abstract an entity is. Published theory provides a six-level hierarchy:

```
Level 1: CONCRETE (physical, observable)
  "A red barn in a field" — specific, material, directly observable
      ↓
Level 2: DESCRIPTIVE (properties, qualities)
  "The warmth of the afternoon" — sensory details, qualities, atmosphere
      ↓
Level 3: FIGURATIVE (metaphorical extension)
  "The city is a machine" — semantic innovation via comparison
      ↓
Level 4: SYMBOLIC (stable second-order meaning)
  "The white whale" — entity that reliably signifies beyond itself
      ↓
Level 5: STRUCTURAL (system-level patterns)
  "The three-act structure" — properties of the whole, not parts
      ↓
Level 6: ABSTRACT (theoretical constructs)
  "Justice" — concepts without direct material referent
```

### Why Abstraction Level Matters

In pipelines that process, extract, or analyze entities, **processing strategy should vary by abstraction level**:

| Level | Processing Strategy | Why |
|---|---|---|
| Concrete | Locate specific instances | These exist at identifiable positions |
| Descriptive | Locate clusters of instances | Properties manifest across nearby passages |
| Figurative | Locate the comparison point | The innovation occurs where vehicle meets tenor |
| Symbolic | Track across the full dataset | Symbolic meaning accumulates through recurrence |
| Structural | Characterize the whole | Properties belong to the whole, not individual parts |
| Abstract | Infer from evidence | Cannot be pointed to; must be argued for |

**The critical insight:** If your pipeline treats all entities the same way (e.g., "find a quote for each entity"), it will fail systematically for structural and abstract entities. You can't "quote" a structural property — you have to *characterize* it. The abstraction level determines the extraction strategy.

### Processing Priority

A common mistake is ranking entities by **frequency** (how often they appear). Published theory suggests ranking by **abstraction level** instead:

- A concrete entity that appears 50 times may be less significant than a symbolic entity that appears 5 times
- The symbolic entity carries more meaning per occurrence because it operates at a higher abstraction level
- Frequency-based ranking biases toward concrete entities and misses the most meaningful ones

**Principle:** When prioritizing entities for downstream processing, use abstraction level as the primary dimension and frequency as a tiebreaker within levels.

---

## Multi-Layer Taxonomy Design

When entities need to be classified across multiple independent dimensions, you need a multi-layer taxonomy. Published theory provides a pattern for this.

### The Published Pattern: Functional Layers

Michael Halliday's Systemic Functional Linguistics (1985) identifies three metafunctions of language — three independent dimensions along which any text simultaneously operates:

| Metafunction | What It Describes | Example |
|---|---|---|
| **Ideational** | What's happening — processes, participants, circumstances | "Who does what to whom" |
| **Interpersonal** | The relationship between producer and receiver | "How the producer positions the receiver" |
| **Textual** | How information is organized and connected | "What creates cohesion and emphasis" |

**Why this is useful beyond linguistics:** Any system that produces structured output for consumers operates on these three dimensions simultaneously:

- **What does the system produce?** (Ideational — the content)
- **How does the system position its audience?** (Interpersonal — the stance)
- **How is the production organized?** (Textual — the structure)

### Applying Published Layers to Your Taxonomy

The general principle:

```
1. Identify the independent dimensions in your domain
   "Our entities operate on multiple orthogonal axes"

2. Find a published framework with named functional layers
   "Published theory X identifies N independent functions"

3. Map each dimension to a published layer
   "Dimension A → Layer X (published name)"

4. Validate independence
   "Can an entity be classified on Layer X without knowing its Layer Y classification?"
   If yes → layers are independent (good)
   If no → layers are coupled (redesign)

5. Use published layer names in your taxonomy
   "Don't call it 'Type A' — call it by the published name"
```

### Signs You Need Multi-Layer Taxonomy

- Same entity legitimately belongs to multiple categories
- Different team members classify the same entity into different categories because they're thinking about different dimensions
- Categories overlap in confusing ways
- Adding new entities keeps requiring new hybrid categories

These are symptoms of a **flat taxonomy trying to encode multiple dimensions**. The fix is to separate the dimensions into independent layers, each grounded in published theory.

---

## When Grounding Applies (And When It Doesn't)

### Good Candidates for Domain Grounding

| Situation | Why Grounding Helps |
|---|---|
| Taxonomy will propagate through 3+ pipeline stages | Categories need to be stable across stages |
| Multiple people will classify entities | Shared external standard prevents drift |
| Classification affects downstream processing strategy | Wrong category → wrong processing → wrong output |
| Taxonomy has 15+ categories | Too many categories to maintain by intuition |
| System will be maintained for 1+ years | Categories need to survive team turnover |

### Poor Candidates for Domain Grounding

| Situation | Why Grounding Is Overkill |
|---|---|
| Throwaway prototype | Categories won't survive long enough to drift |
| Single-stage classification | No propagation risk |
| Purely internal labels | Only one person needs to understand them |
| Categories are configurable by users | Users define their own taxonomy |

---

## The Principle

**Every classification taxonomy in a pipeline should cite a published framework. Entity processing priority should follow abstraction level, not frequency. Multi-layer designs need formal correspondence to published theory.**

These three rules prevent:
1. **Taxonomy drift** — categories don't change meaning over time because the published definition is stable
2. **Classification inconsistency** — different people arrive at the same classification because the framework provides an external standard
3. **Processing mismatches** — entities at different abstraction levels get appropriate processing strategies
4. **Dimension conflation** — independent classification dimensions stay independent

---

## Deeper: Why Frequency Is a Trap

Systems that process entities (text analysis, data classification, medical coding, financial categorization) commonly rank by frequency: the most common entities get highest priority. This seems rational — focus resources where they'll have the most impact.

But frequency-based ranking has a structural bias: **it favors concrete, easily identifiable entities over abstract, meaningful ones.** Concrete entities (specific names, locations, quantities) are frequent because they're specific. Abstract entities (patterns, themes, structural properties) are infrequent because they're general.

Example: In a dataset of medical records, individual symptom mentions (concrete) vastly outnumber diagnostic patterns (structural). A frequency-based system focuses on the symptoms. But the diagnostic patterns — which involve relationships between symptoms — are what doctors actually need.

**The fix:** Rank by abstraction level first, then by frequency within each level. This ensures that high-level patterns get appropriate attention even when they're statistically rare.

---

## Deeper: The Three-Taxonomy Problem

Systems that evolve organically tend to develop multiple competing taxonomies:

1. **Detection taxonomy** — what the classification stage uses (optimized for recognition)
2. **Processing taxonomy** — what the middle stages use (optimized for pipeline flow)
3. **Output taxonomy** — what the final output uses (optimized for consumption)

When these three diverge, entities get classified differently at different stages. Data that enters as Category A may exit as Category B, and nobody can trace why.

**The fix:** Establish one canonical taxonomy grounded in published theory. All three stages reference this single source of truth. Detection, processing, and output may *filter* or *subset* the canonical taxonomy, but they don't create parallel classification systems.

```
CANONICAL TAXONOMY (published framework, single source of truth)
        │
        ├── Detection stage uses subset + detection-specific attributes
        │
        ├── Processing stage uses full taxonomy + processing metadata
        │
        └── Output stage uses subset + output-specific formatting
```

Each stage extends the canonical taxonomy; none replaces it.

---

## Connection to Other Knowledge Base Concepts

| Concept | Connection to Domain Grounding |
|---|---|
| **Causality & Systems** | Taxonomy design is upstream of everything — wrong categories propagate wrong classifications through every downstream stage |
| **Task Design Theory** | Taxonomy design is a REASONING task (domain expertise). Entity classification is a PRECISION task (applying the taxonomy). Don't mix them. |
| **Failure Theory** | Taxonomy drift is a silent failure — output looks reasonable but classifications gradually diverge from intent |
| **Constraint Theory** | When downstream extraction produces wrong results, check whether the taxonomy handoff is the constraint — are entities arriving with correct classifications? |
| **Measurement Theory** | You can measure taxonomy quality: inter-rater reliability, coverage of published categories, propagation consistency across stages |

---

## Test Yourself

Before proceeding to the Domain Grounding skill, you should be able to answer:

1. Why do invented categories drift but published categories don't?
2. Why should processing priority follow abstraction level rather than frequency?
3. What's the difference between a flat taxonomy with overlapping categories and a multi-layer taxonomy with independent dimensions?
4. How does the three-taxonomy problem arise, and what's the fix?
5. When is domain grounding overkill?

If these feel clear, proceed to [Domain Grounding](../skills/domain-grounding.md).

---

## References

- Halliday, M.A.K. (1985). *An Introduction to Functional Grammar.* — Three metafunctions: ideational, interpersonal, textual
- Jakobson, R. (1960). "Closing Statement: Linguistics and Poetics." — The equivalence principle; selection vs combination axes
- Barthes, R. (1957). *Mythologies.* — Second-order semiological systems; how objects accumulate meaning
- Ricoeur, P. (1975). *The Rule of Metaphor.* — Metaphor as semantic innovation, not substitution
- Bowker, G. & Star, S.L. (1999). *Sorting Things Out: Classification and Its Consequences.* — How classification systems shape what they classify
- This repository's measurement data: Taxonomy unification (Issue #429), semiotic grounding (Issue #434), device extraction strategy
