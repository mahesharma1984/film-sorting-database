# Theory Knowledge Base

This directory contains nine essays that articulate the theoretical foundation of the film sorting archive. The operational documentation (sorting rules, decision trees, implementation guides) lives in `docs/`. These essays address the **why** — why decades, why these tiers, why exploitation cinema belongs in a serious archive.

---

## Reading Order

For a newcomer, read in this sequence:

1. **[COLLECTION_IDENTITY.md](COLLECTION_IDENTITY.md)** — Start here. What this archive is and what thesis it embodies.
2. **[DECADE_WAVE_THEORY.md](DECADE_WAVE_THEORY.md)** — Why decades are the organizing unit (not movements, nations, or directors).
3. **[TIER_ARCHITECTURE.md](TIER_ARCHITECTURE.md)** — Why exactly four tiers, how they interact, and what the ratios mean.
4. **[AUTEUR_CRITERIA.md](AUTEUR_CRITERIA.md)** — What makes a director Core. The whitelist as thesis statement.
5. **[MARGINS_AND_TEXTURE.md](MARGINS_AND_TEXTURE.md)** — Why the archive contains exploitation cinema. Satellite as context for Core.
6. **[POPCORN_WAVES.md](POPCORN_WAVES.md)** — Studio cinema as a parallel history to the auteur tradition.
7. **[FORMAT_AS_INTENTION.md](FORMAT_AS_INTENTION.md)** — Why seeking out a 35mm scan is a curatorial act, not a technical preference.
8. **[REFINEMENT_AND_EMERGENCE.md](REFINEMENT_AND_EMERGENCE.md)** — How categories are built: the recursive refinement process, when a sub-category earns its name, and how new categories are applied retroactively.
9. **[SATELLITE_DEPTH.md](SATELLITE_DEPTH.md)** — Applying Core/Reference logic within Satellite categories: vetting strategy, within-category masters, and the seeking programme that emerges from recognising them.

---

## How the Essays Relate

```
COLLECTION_IDENTITY (master thesis)
  ├── DECADE_WAVE_THEORY (why decades)
  │     ├── AUTEUR_CRITERIA (Core directors defined within waves)
  │     ├── MARGINS_AND_TEXTURE (Satellite categories are wave-bounded)
  │     └── POPCORN_WAVES (studio cinema has its own wave structure)
  ├── TIER_ARCHITECTURE (why 4 tiers)
  │     └── FORMAT_AS_INTENTION (format is metadata, not tier)
  ├── AUTEUR_CRITERIA ←→ MARGINS_AND_TEXTURE (auteur/genre-master boundary)
  ├── REFINEMENT_AND_EMERGENCE (how all of the above is built and rebuilt over time)
  └── SATELLITE_DEPTH (Core/Reference logic applied within Satellite categories → seeking strategy)
```

---

## About `[YOUR INPUT]` Markers

These essays are hybrid frameworks: scaffolding drafted from existing documentation, with gaps marked by `[YOUR INPUT]` where the collector's curatorial judgment is needed. These are not bugs — they are the places where the theory depends on personal conviction that only the collector can provide.

The most important gaps:

| Essay | Gap | Why It Matters |
|-------|-----|---------------|
| AUTEUR_CRITERIA | Formal criteria for Core status | The whitelist exists but its logic is unstated |
| AUTEUR_CRITERIA | Warhol vs. Russ Meyer distinction | Defines where Core ends and Satellite begins |
| MARGINS_AND_TEXTURE | Why these 12 categories | Are they principled, personal, or pragmatic? |
| DECADE_WAVE_THEORY | Wave labels for 1950s and 2000s-2010s | These decades need stronger identities |
| COLLECTION_IDENTITY | Personal taste vs. historical rigor | The most interesting tension in the project |
| TIER_ARCHITECTURE | Ratios designed or emergent | Changes whether the architecture is prescriptive or descriptive |
| POPCORN_WAVES | Philosophy of the "tonight test" | What IS pleasure as a curatorial criterion? |
| FORMAT_AS_INTENTION | Anti-streaming thesis | Is format curation resistance or just preference? |

Fill these in at your own pace. Each `[YOUR INPUT]` marker includes context and possible directions to consider.

---

## Relationship to Operational Docs

These theory essays do not replace the operational documentation in `docs/`. They complement it:

- **Operational docs** answer: How do I sort this film?
- **Theory essays** answer: Why does this sorting system exist in this form?

A developer working on the classifier needs `docs/SATELLITE_CATEGORIES.md`. A curator asking whether to add a new Satellite category needs `docs/theory/MARGINS_AND_TEXTURE.md`.
