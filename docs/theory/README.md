# Theory Knowledge Base

This directory contains five essays that articulate the theoretical foundation of the film sorting archive. The operational documentation (sorting rules, decision trees, implementation guides) lives in `docs/`. These essays address the **why** — why decades, why these tiers, why exploitation cinema belongs in a serious archive.

---

## Reading Order

For a newcomer, read in this sequence:

1. **[COLLECTION_THESIS.md](COLLECTION_THESIS.md)** — Start here. What this archive is, why decades are the organizing unit, and why format curation matters.
2. **[TIER_ARCHITECTURE.md](TIER_ARCHITECTURE.md)** — Why exactly four tiers, what makes a director Core, and how Popcorn constitutes a parallel cinema history.
3. **[MARGINS_AND_TEXTURE.md](MARGINS_AND_TEXTURE.md)** — Why the archive contains exploitation cinema. Satellite as context for Core.
4. **[REFINEMENT_AND_EMERGENCE.md](REFINEMENT_AND_EMERGENCE.md)** — How categories are built: the recursive refinement process, when a sub-category earns its name, and how new categories are applied retroactively.
5. **[SATELLITE_DEPTH.md](SATELLITE_DEPTH.md)** — Applying Core/Reference logic within Satellite categories: vetting strategy, within-category masters, and the seeking programme that emerges from recognising them.

---

## How the Essays Relate

```
COLLECTION_THESIS (what & why: identity + decades + format)
  └── TIER_ARCHITECTURE (how: 4 tiers + auteur criteria + Popcorn waves)
        ├── MARGINS_AND_TEXTURE (Satellite categories, caps, boundaries)
        │     └── SATELLITE_DEPTH (within-category depth hierarchies)
        └── REFINEMENT_AND_EMERGENCE (how the tier system evolves over time)
              └── SATELLITE_DEPTH (outward splitting ↔ inward deepening)
```

---

## About `[YOUR INPUT]` Markers

These essays are hybrid frameworks: scaffolding drafted from existing documentation, with gaps marked by `[YOUR INPUT]` where the collector's curatorial judgment is needed. These are not bugs — they are the places where the theory depends on personal conviction that only the collector can provide.

The most important gaps (18 total across 3 essays):

| Essay | Gap | Why It Matters |
|-------|-----|---------------|
| TIER_ARCHITECTURE (Part II) | Formal criteria for Core status | The whitelist exists but its logic is unstated |
| TIER_ARCHITECTURE (Part II) | Warhol vs. Russ Meyer distinction | Defines where Core ends and Satellite begins |
| TIER_ARCHITECTURE (Part III) | Philosophy of the "tonight test" | What IS pleasure as a curatorial criterion? |
| TIER_ARCHITECTURE (Part I) | Ratios designed or emergent | Changes whether the architecture is prescriptive or descriptive |
| COLLECTION_THESIS (Part I) | Personal taste vs. historical rigor | The most interesting tension in the project |
| COLLECTION_THESIS (Part II) | Wave labels for 1950s and 2000s-2010s | These decades need stronger identities |
| COLLECTION_THESIS (Part III) | Anti-streaming thesis | Is format curation resistance or just preference? |
| MARGINS_AND_TEXTURE | Why these 17 categories | Are they principled, personal, or pragmatic? |

REFINEMENT_AND_EMERGENCE and SATELLITE_DEPTH have no gaps — they are fully authored.

Fill these in at your own pace. Each `[YOUR INPUT]` marker includes context and possible directions to consider.

---

## Relationship to Operational Docs

These theory essays do not replace the operational documentation in `docs/`. They complement it:

- **Operational docs** answer: How do I sort this film?
- **Theory essays** answer: Why does this sorting system exist in this form?

A developer working on the classifier needs `docs/SATELLITE_CATEGORIES.md`. A curator asking whether to add a new Satellite category needs `docs/theory/MARGINS_AND_TEXTURE.md`.
