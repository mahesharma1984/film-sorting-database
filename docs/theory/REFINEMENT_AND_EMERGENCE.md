# Refinement and Emergence: How Categories Are Built

> A category is not invented. It is recognised. The films arrive first. The name comes when enough of them have arrived to make the pattern undeniable.

---

## 1. The Curatorial Process Is Recursive

This archive is not a fixed taxonomy applied to a stable collection. It is a living system that refines itself as the collection grows. New films arrive, patterns emerge, categories split, and the rules are applied retroactively to everything that came before. This is the normal mode of operation, not an exception to it.

The process works at two scales simultaneously:

**Macro:** The four-tier framework (Core → Reference → Satellite → Popcorn) establishes the broadest possible set of curatorial relationships. Every film in the archive belongs to one of these four relationships with the collector.

**Micro:** Within each macro tier, patterns emerge. Satellite contains thirty-plus countries and seven decades. It is not a single relationship — it is a space inside which dozens of more specific relationships can be named. Each named satellite category (Giallo, Brazilian Exploitation, French New Wave, Indie Cinema) is a micro-level refinement of the macro Satellite relationship.

The recursion does not stop there. Satellite categories themselves get refined:
- American Exploitation (macro) → Classic Hollywood splits off (1930s–1950s US), Popcorn absorbs the rewatchable mainstream, and American New Hollywood claims the prestige studio work. American Exploitation is left with what it always was: grindhouse, VHS cult, direct-to-video.
- Satellite (undifferentiated) → French New Wave splits off from European cinema, recognised first as a director cluster, then as a historically bounded movement.
- Indie Cinema (functional catch-all) → will eventually produce sub-patterns worth naming as the collection deepens.

At each step, the refinement is:
1. Applied retroactively to existing files
2. Encoded in the routing rules (constants.py)
3. Documented in SORTING_DATABASE.md for one-off cases
4. Captured in theory (this document and the other essays)

---

## 2. Three Conditions for a New Category

A macro category earns a micro split when three conditions align:

### Condition 1: Density

Enough films accumulate that managing them as a single group loses information. The archive's caps encode this threshold: Giallo is capped at 30 (focused engagement), Brazilian Exploitation at 45 (moderate engagement), Hong Kong Action at 65 (strong engagement), American Exploitation at 80 (deepest Satellite engagement). A sub-category is not worth naming unless it can plausibly fill its cap. A collection of three Italian crime films does not need "Giallo" — it needs a shelf. Thirty does.

### Condition 2: Coherence

The sub-group shares something that the parent category does not have: a historical movement, a national industry moment, a director cluster, a thematic tradition, or a functional role the parent cannot play. This is the hardest condition to satisfy. Not every cluster of similar films is coherent. Coherence requires that the shared property is *historically or formally real* — that the films belong together for a reason that precedes the act of categorising them.

- **Giallo** is coherent because there is a real Italian genre tradition with documented conventions (slasher mechanics, Ennio Morricone, Bava → Argento progression).
- **French New Wave** is coherent because there is a documented historical movement with identifiable participants and a shared theoretical programme (Les Cahiers du Cinéma).
- **American New Hollywood** is coherent because there is a documented industrial shift: the collapse of the Production Code, the brief window between the old studio system and the blockbuster era (roughly 1965–1985), and a recognisable set of directors who exploited it.
- **Indie Cinema** is a different kind of coherence: *functional*, not historical. It does not name a movement. It names a curatorial role — arthouse films from any country and era that are not Core, not exploitation, not mainstream Popcorn. Its coherence is defined negatively.

### Condition 3: Archival Necessity

The sub-group must serve a purpose that nothing else in the taxonomy can serve. If an existing category can absorb the films without losing meaning, no new category is needed. The test: if you removed the proposed category and scattered its films into neighbouring categories, would you lose something real?

- Remove Giallo: Italian Horror films go to Satellite/Italian or Unsorted. You lose the visual language, the tradition, the connection between Bava and Argento. You lose something real.
- Remove Indie Cinema: non-exploitation arthouse films go to Unsorted. You lose the ability to represent the global independent tradition at all. You lose something real.
- Remove American Exploitation prematurely (before American New Hollywood exists): Fosse and Russ Meyer end up in the same folder. You lose the distinction between an industrial outsider and a prestige studio filmmaker. You lose something real.

When all three conditions hold — density, coherence, archival necessity — the category exists. The act of naming it makes it visible to the routing system and to the people who use the archive.

---

## 3. The Refinement Events (History)

The following splits have occurred in this archive's history. Each one followed the three-condition pattern:

| Event | From | To | Trigger |
|-------|------|----|---------|
| **Satellite added** | Unsorted (everything non-Core/Reference) | Satellite macro tier | Exploitation films numerous enough to need their own curatorial relationship |
| **Decade bounding** | Satellite (no time bounds) | Satellite with historical start/end dates | Anachronistic routing (2010s Argento film routing to Giallo) forced the question of when each tradition ended |
| **Popcorn priority raised** | Popcorn checked last | Popcorn checked before Satellite | Mainstream studio films (Rush Hour, Speed) routing to exploitation categories because of country/decade match |
| **Classic Hollywood split** | American Exploitation (all US, all decades) | Classic Hollywood (1930s–1950s), AmEx (1960s–1980s) | Pre-1960s US studio cinema and post-1960s grindhouse are two entirely different traditions that happen to share a country code |
| **French New Wave split** | European Sexploitation / generic European routing | French New Wave (director-gated, 1950s–1970s) | Enough Nouvelle Vague directors to name the movement; country-based routing (FR) was too blunt — it would catch all French cinema, not just the movement |
| **Indie Cinema created** | Unsorted (no home for non-exploitation arthouse) | Indie Cinema (functional catch-all, 1960s–2020s, 30+ countries) | Accumulated films from diverse national cinemas with no exploitation category to match; needed a functional home rather than a historical name |
| **AmEx genre gate + title keywords** | American Exploitation (US + decade = match) | American Exploitation (US + decade + genre + title keyword = match) | Too many mainstream studio films routing to AmEx — tightened to genuine exploitation signals |
| **American New Hollywood** (proposed) | American Exploitation (catch-all for prestige US) | American New Hollywood (1965–1985, director-gated) | Fosse, Ashby, Pakula, Pollack represent a specific, bounded movement distinct from grindhouse; density (15–25 films), coherence (documented New Hollywood movement), archival necessity (no other category places them correctly) |

---

## 4. How Retroactive Application Works

Every refinement is applied retroactively. When a new category is named, the question is not only "which new films go here?" but "which films already in the archive belong here and are currently misclassified?"

The retroactive process has three components:

### Component 1: Human curation (SORTING_DATABASE.md)

The lookup table is the highest-trust classification signal. When a new category is created, the films that clearly belong in it are added to SORTING_DATABASE.md with their correct destination. The classifier then routes them correctly on the next run. This is the appropriate tool for cases that require curatorial judgment: films where the category is right but the automated routing cannot reach it alone.

**Never modify SORTING_DATABASE.md programmatically.** It is a record of human decisions. Code reads it; people write it.

### Component 2: Rule changes (constants.py + routing logic)

When the refinement generalises — when a rule can be stated that will correctly route an entire class of films — it goes into `SATELLITE_ROUTING_RULES` in constants.py. This is what happened when Classic Hollywood split from American Exploitation: the rule "US + 1930s–1950s → Classic Hollywood" was encoded and the classifier applied it to all new films automatically.

Rule changes require:
- Positioning in the routing dictionary (more specific categories before catch-alls — French New Wave before European Sexploitation; American New Hollywood before American Exploitation)
- Decade bounds reflecting the historical moment
- Director gates for movements that are person-driven rather than country-driven
- Tests in `tests/test_satellite.py`

### Component 3: Cache invalidation and re-classification of new files

After rule changes, the API cache may contain stale data. Run:
```bash
python scripts/invalidate_null_cache.py conservative
python classify.py <source_directory>
```

This handles new files entering through the Unsorted queue. For existing library films, see §4a below.

---

## 4a. The Curatorial Lifecycle

The classification pipeline handles one direction: new films enter through Unsorted, get classified, and get moved to the library. But curation is a cycle, not a one-way pipeline. Categories get redefined. Routing rules tighten. Connoisseurship deepens. Films that were placed correctly under old rules may be wrong under current ones — and films that were placed manually before the pipeline existed may never have been evaluated against any rules at all.

The full curatorial lifecycle has five stages:

### Stage 1: Define

Establish category identity. A category must satisfy the three conditions (§2: density, coherence, archival necessity) and have clear boundaries encoded in `SATELLITE_ROUTING_RULES`: country codes, decade bounds, genre gates, director lists, keyword signals. Historical categories are director-gated and movement-anchored. Functional categories are negatively defined.

This is the work documented in `docs/SATELLITE_CATEGORIES.md` and `lib/constants.py`.

### Stage 2: Cluster

Route films into categories using the available data. The classification pipeline (`classify.py`) applies the routing rules to produce an initial assignment. This is approximate — it depends on API data quality, filename parsing accuracy, and the completeness of director lists and keyword signals. The initial clustering is a hypothesis, not a verdict.

For new films, `classify.py` handles this. For films already in the library, there is currently no automated mechanism to re-evaluate their placement (see Issue #31). The library audit (`audit.py`) reports what is in each folder but does not check whether it belongs there.

**The gap:** The pipeline was designed assuming manual organisation was correct and only new files needed classification. That assumption was wrong. Films placed by hand before the pipeline existed — and films placed by earlier, looser routing rules — are never re-evaluated. This is the single largest source of category pollution.

### Stage 3: Refine

Compare each film's current placement against the current routing rules and flag discrepancies. This is the re-audit step: run the classifier on existing library contents and surface films where "folder says X, classifier says Y."

The output is a discrepancy report, not an automatic move. The curator reviews each flagged film and decides:
- **Reclassify:** the film genuinely belongs elsewhere; move it
- **Pin:** the film is correctly placed despite the routing rules (edge case); add it to SORTING_DATABASE.md to override future routing
- **Investigate:** the routing rules themselves may be wrong; the discrepancy reveals a definition problem

This stage does not yet have tooling. It requires a re-classification audit script (Issue #31).

### Stage 4: Retain and discard

Once categories contain only films that belong there, apply within-category hierarchy (SATELLITE_DEPTH.md §3–4). Identify Category Core films (define the tradition), Category Reference (essential range), and texture (skilled practitioners). Films below the cap are kept. Films above the cap are ranked: tentpoles stay, texture is the first to be cut.

This is the tentpole ranking described in Issue #30. It depends on Stage 3 being complete — you cannot rank films within a category if the category contains films that don't belong there.

### Stage 5: Reinforce

Confirmed curatorial decisions feed back into the classification model:
- Films pinned during Stage 3 are added to SORTING_DATABASE.md (explicit lookup, highest trust)
- Directors identified as Category Core during Stage 4 are added to `core_directors` in routing rules
- Keyword patterns discovered during refinement are added to `keyword_signals`
- Caps are adjusted based on actual curatorial engagement, not collection size

Each pass through the cycle makes the routing rules more precise, which makes the next clustering more accurate, which reduces the refinement burden. The system gets smarter — but only if every stage completes.

### The cycle is continuous

```
Define → Cluster → Refine → Retain/Discard → Reinforce
  ↑                                              │
  └──────────────────────────────────────────────┘
```

The lifecycle is not a one-time migration. It is the ongoing operating model. Monthly reviews (TIER_ARCHITECTURE.md §8) are micro-iterations of this cycle. Category splits (§3 of this document) are macro-iterations. The tentpole ranking process (Issue #30) is a systematic pass through Stages 4–5 across all categories.

**Current status (2026-02):** The system has been operating at Stage 2 (clustering new films) since the pipeline was built. Stages 3–5 have not been executed systematically against the existing library. The ~500 films placed before the pipeline existed have never been re-evaluated. This is the architectural gap that Issue #31 addresses.

---

## 5. Two Kinds of Category

A key distinction that emerged from examining the history:

### Historical categories

Correspond to a real, documented cultural event with a beginning and an end. The category name refers to something that existed independently of this archive.

- Giallo (Italian genre cinema, c.1963–1986)
- French New Wave (Nouvelle Vague, c.1958–1973)
- Blaxploitation (US Black cinema boom, c.1971–1979)
- Hong Kong Action (pre-handover martial arts and Category III, c.1971–1997)
- American New Hollywood (post-Production Code prestige studio cinema, c.1965–1985)

Historical categories are **director-gated** or **movement-anchored**. They cannot be entered by country+decade alone because the historical movement was not synonymous with the national cinema of that era. Not every French film from 1960–1973 is French New Wave. Not every Italian film from 1965–1980 is Giallo. Not every American drama from 1965–1985 is New Hollywood.

### Functional categories

Defined by what they serve in the archive rather than by a historical moment they name. They are catch-alls of a principled kind.

- Indie Cinema (1960s–2020s, 30+ countries): films that are not Core, not exploitation, not mainstream Popcorn; arthouse, festival cinema, international independent work
- Classic Hollywood (1930s–1950s): pre-New Hollywood American studio cinema (a functional container, not a movement — Hollywood in this era was too uniform to call it a "movement")
- Music Films (all decades): concert films and music documentaries from non-Core directors
- Cult Oddities (all decades): films that resist every other category

Functional categories are defined **negatively**: a film belongs here because it does not belong in any more specific category. This is valid. It is not a failure of precision — it is a precise recognition that some films resist historical categorisation and need a functional home.

The critical rule: **functional categories must come last in the routing order**, after all historical categories have been checked. Classic Hollywood and Indie Cinema are checked after Giallo, Blaxploitation, Brazilian Exploitation, and the other historical categories — because a film that matches a historical category is more precisely located there than in a functional catch-all.

---

## 6. When to Split vs. When to Merge

Not every pattern justifies a new category. The three-condition threshold (density, coherence, archival necessity) guards against over-splitting. But over-merging is also a failure mode — the original mistake with American Exploitation, which absorbed both grindhouse and prestige cinema into the same folder.

**Split when:**
- Films in the parent category have clearly different curatorial relationships with the collector
- The sub-group is large enough to hold a meaningful collection (roughly 10+ films)
- The sub-group has historical or functional coherence the parent lacks
- The sub-group would be lost or misrepresented if it stayed in the parent

**Merge when:**
- A category is under-populated (fewer than 5–8 films) and unlikely to grow
- The distinction between two categories is too fine to be meaningful at collection scale
- The category was created for a single film or director and no others qualify

**Do not create a category for:**
- A single director (use the Core whitelist or the SORTING_DATABASE.md lookup, not a new Satellite category)
- A film you cannot yet describe with a rule (use Unsorted; let the pattern emerge)
- A genre that is not historically bounded and not functionally distinct (avoid "Drama" or "Thriller" as standalone Satellite categories — these are genre tags, not curatorial relationships)

---

## 7. The Shadow Cinema Principle

The most productive use of the micro/macro recursion is understanding what each satellite category is *the shadow of*.

Brazilian pornochanchada is the shadow of Cinema Novo — the commercial cinema that Cinema Novo sought to transcend. You cannot fully understand what Cinema Novo was reacting against without knowing what pornochanchada looked like.

Giallo is the shadow of Italian modernism (Antonioni, Fellini). The genre tradition that Italian art cinema implicitly repudiated.

American Exploitation (grindhouse) is the shadow of American New Hollywood. New Hollywood directors were borrowing energy and audience from the exploitation circuit even as they elevated it. Cassavetes and Russ Meyer are not opposites — they are two responses to the same industrial moment.

This is why satellite categories are organised alongside their corresponding Core directors in the tier-first folder structure. `Core/1970s/` and `Satellite/American Exploitation/1970s/` sit next to each other deliberately. The archive is not just a filing system — it is an argument about the relationships between mainstream, margins, and centre.

When creating a new satellite category, ask: **what is this the shadow of?** The answer tells you whether the category has earned its place.

---

## 8. Applying This Framework to Future Refinements

The following patterns in the current archive suggest future refinement candidates:

**Near-term (density threshold approaching):**
- *American New Hollywood* (1965–1985) — currently partially in AmEx, partially in Reference, partially Unsorted. Three conditions met; category warranted. See Issue #23.
- *Music Films sub-categories* — concert films, music documentaries, and music-biography films may eventually be dense enough to split. Not yet.

**Medium-term (coherence emerging):**
- *Soviet Cinema* — if Russian/Soviet films accumulate, the Tarkovsky Core + Elem Klimov Satellite + experimental film tradition forms a coherent cluster
- *Korean Cinema* — Park Chan-wook (Core candidate), Bong Joon-ho (Core candidate), and genre cinema (Quiet Family, I Saw the Devil) suggest a national cinema with enough range to warrant sub-categorisation

**Long-term (functional question):**
- *Documentary* — currently scattered (Paris Is Burning in AmEx, Straight No Chaser in AmEx, Lonely Boy in Music Films). If documentary practice becomes a sustained collection interest, a functional Documentary category would consolidate them.

The test in every case: wait for density, look for coherence, confirm archival necessity. Then name it.

---

## Summary

| Principle | Statement |
|-----------|-----------|
| **The process is recursive** | Macro categories split into micro; micro can split further. This is not a failure — it is the system working. |
| **Three conditions for a new category** | Density (enough films), coherence (historical or functional), archival necessity (the films would be lost without it) |
| **Two kinds of category** | Historical (movement-bounded, director-gated) and Functional (negatively defined, catch-all with principles) |
| **Retroactive application is mandatory** | A new category that is not applied to existing films is incomplete. Update SORTING_DATABASE.md, update constants.py, re-classify. |
| **Curation is a cycle, not a pipeline** | Define → Cluster → Refine → Retain/Discard → Reinforce. Each pass makes the routing rules more precise. The system only gets smarter if every stage completes (§4a). |
| **Routing order encodes the hierarchy** | Historical categories before functional; specific before general; first match wins |
| **Shadow cinema** | Every satellite category is the shadow of something in Core or Reference. Identify it. |
| **Split to clarify; merge to simplify** | Over-splitting creates noise; over-merging loses information. The three-condition test is the guard against both. |

---

## Cross-References

- [TIER_ARCHITECTURE.md](TIER_ARCHITECTURE.md) — §8 Permeable Boundaries; the living tier system that this document explains over time; Part II (Auteur Criteria) explains Core whitelist inclusion criteria
- [MARGINS_AND_TEXTURE.md](MARGINS_AND_TEXTURE.md) — The satellite categories whose creation history is documented in §3 of this essay
- [SATELLITE_DEPTH.md](SATELLITE_DEPTH.md) — The complementary inward movement: as macro categories mature, internal depth hierarchies develop within each named category
- [COLLECTION_THESIS.md](COLLECTION_THESIS.md) — The master thesis within which all refinement events occur; the stable framework the process refines
