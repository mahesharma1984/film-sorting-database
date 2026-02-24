# The Recursive Curation Model

> A classification system that cannot learn from its own output is a filing cabinet. One that can is a curatorial practice.

This document is the unified architecture reference for the film sorting database. It integrates the five theory essays, the twelve operational skills, the recursive deepening pattern observed across national cinemas, and the data gathering protocol for Unsorted films into a single description of how the system works as a recursive, self-refining whole.

The existing theory essays remain as deep-dives into specific topics. This document describes how they fit together.

---

## 1. The Core Loop

The system is a recursive cycle with five stages. Each pass through the cycle improves both data quality and category precision. The cycle never "finishes" — it asymptotically approaches the curator's ideal library.

```
    ┌──────────────────────────────────────────────────────────────┐
    │                                                              │
    ▼                                                              │
  GATHER          CLASSIFY          AUDIT          REFINE          │
  (data)    →    (route)     →    (diagnose)  →  (decide)    →  REINFORCE
  §2               §3-5              §7             §7            (feed back)
  R0→R1→R2→R3     Tiers +          Review          Accept/         │
  Data readiness   Satellite +      queue           Override/       │
                   Certainty        Re-audit        Enrich/         │
                   tiers            Tentpole        Defer           │
                                    ranking                        │
    │                                                              │
    └──────────────────────────────────────────────────────────────┘
```

**Pass 1 (broad strokes):** Classify films into four tiers — Core, Reference, Satellite, Popcorn, Unsorted. This is the pipeline as originally built.

**Pass 2 (satellite differentiation):** Within Satellite, find sub-populations by country, decade, and tradition. Split into named categories (Giallo, Pinku Eiga, French New Wave). This happened during initial development.

**Pass 3 (within-category depth):** Within each named category, identify tentpoles vs texture. Establish Category Core / Category Reference / Category Texture rankings. This is where the system is now.

**Pass 4 (cross-category refinement):** Compare categories against each other. Does a country need another sub-category? Is a catch-all absorbing films that belong elsewhere? Are there Core directors hiding in Satellite? This is the next frontier.

**Pass 5 (feed back):** Reclassify the whole library with refined rules. New sub-populations emerge. Back to Pass 2.

Each pass produces two kinds of output:
1. **Classifications** — films placed in the library
2. **Discoveries** — patterns that improve the next pass (new directors for whitelists, new categories to define, routing bugs to fix, data gaps to fill)

The system degrades when only classifications are produced and discoveries are ignored. It improves when discoveries feed back into rules, data, and category definitions.

*Deep-dive: [REFINEMENT_AND_EMERGENCE.md](REFINEMENT_AND_EMERGENCE.md) §1 (the curatorial process is recursive), §4a (the five-stage lifecycle).*

---

## 2. Data Readiness: The Foundation of Every Pass

Before any classification can happen, data must exist. The binding constraint of the entire system is not downstream complexity (routing rules, category definitions, tentpole rankings) — it is upstream data quality. Of 405 Unsorted films:
- 246 have no year (supplements, interviews, non-film content)
- 126 have a year but API returned no director or country
- 32 have full data but no routing rule matches

The 126 films with no API data enter all 9 routing stages, fail at every one, and exit as `unsorted_insufficient_data`. Every downstream routing stage runs on empty input and produces guaranteed failures that look like legitimate non-matches.

### Readiness Levels

Every film has a measurable data readiness level:

| Level | Data Present | What Routing Can Work | Confidence Cap |
|-------|-------------|----------------------|---------------|
| **R0** | No year | Explicit lookup only | 0.0 |
| **R1** | Title + year, no director AND no country | Lookup + Reference canon + user tag | 0.3 |
| **R2** | Partial (director OR country, not both) | Partial Satellite + Core director check | 0.6 |
| **R3** | Full (director AND country AND genres) | Full pipeline | 1.0 (no cap) |

Readiness is assessed once, after API enrichment and before routing. It gates which downstream stages execute. R1 films skip Stages 4-8 entirely — those stages consume data R1 films do not have.

### The Data Gathering Protocol

Data readiness is not a static property. It is a progression. The system should actively promote films up the readiness ladder:

**R0 → R1: Extract a year**
- `normalize.py` cleans filenames and extracts years
- Non-film content (TV episodes, supplements, interviews) should be filtered, not classified
- 246 R0 films are the largest population — but most are not feature films. Filtering non-films reduces the R0 count dramatically and removes noise from all downstream statistics.

**R1 → R2: Get API data**
- Cache invalidation: `python scripts/invalidate_null_cache.py conservative` clears entries where both director AND country are missing, allowing re-query on next run
- Title normalization: parser improvements that produce cleaner titles get better API matches
- Alternative title queries: films with non-English titles may need romanised or alternative-language queries
- Manual enrichment: `output/manual_enrichment.csv` — the curator provides director/country from personal knowledge. This is the fastest path for films the curator recognises.

**R2 → R3: Complete enrichment**
- Secondary API query for the missing field (director without country, or vice versa)
- Manual enrichment for the remaining gap
- OMDb often succeeds where TMDb fails for country data (and vice versa for genres)

**Why this matters:** Every R1 film promoted to R2 or R3 becomes classifiable by the routing pipeline. The 126 R1 films are not a permanent population — they are a work queue. The data gathering protocol is how the work gets done.

*Deep-dive: [data-readiness.md](../../exports/skills/data-readiness.md) (Skill 10 — full framework).*

---

## 3. The Four-Tier Hierarchy

The four tiers name four kinds of relationship between the collector and a film:

| Tier | Relationship | What it means |
|------|-------------|---------------|
| **Core** | Identity | "This filmmaker is part of who I am" — complete filmographies, auteur commitment |
| **Reference** | Acknowledgment | "Cinema history requires I keep this" — canonical films by non-Core directors |
| **Satellite** | Interest | "This is a margin I find compelling" — exploitation, movements, national waves |
| **Popcorn** | Pleasure | "I rewatch this for fun" — mainstream entertainment, rewatchable genre |

These are not degrees of the same thing. They are categorically different. A Godard film is not "more liked" than a Spider-Man film — it is liked in a fundamentally different way.

### Tier as Primary Axis

The library is organised tier-first, not decade-first or country-first:

```
Core/1960s/Jean-Luc Godard/
Reference/1960s/
Satellite/Giallo/1970s/
Popcorn/1980s/
```

This allows each tier to be a separate Plex library: Core = complete auteur filmographies, Reference = the canon, Satellite = margins and movements, Popcorn = pleasure viewing.

### The Decision Tree

The classification pipeline checks tiers in a specific priority order:

1. **Explicit lookup** (SORTING_DATABASE.md) — human-curated, highest trust
2. **Reference canon** — 50-film hardcoded list
3. **Satellite routing** — country + decade + genre + director + keyword rules
4. **User tag recovery** — trust previous human classification
5. **Core director check** — whitelist match
6. **Popcorn check** — popularity + format signals
7. **Default** → Unsorted with reason code

This order is a philosophical statement: **character determines tier, not director prestige alone**. A Godard film in his French New Wave period routes to Satellite/FNW. A Godard film from his post-movement period routes to Core. The decade gate does the heavy lifting.

*Deep-dive: [TIER_ARCHITECTURE.md](TIER_ARCHITECTURE.md) — Parts I-III (why four tiers, auteur criteria, Popcorn as parallel history).*

---

## 4. Satellite Differentiation: The Fractal Layer

Satellite is not a single category. It is a space inside which dozens of more specific traditions can be named. Each named satellite category (Giallo, Pinku Eiga, French New Wave, Indie Cinema) is a micro-level refinement of the macro Satellite relationship.

### Two Kinds of Category

**Historical categories** correspond to a real, documented cultural event with a beginning and an end. The name refers to something that existed independently of this archive.

- Giallo (Italian genre cinema, c.1963-1986)
- French New Wave (Nouvelle Vague, c.1958-1973)
- American New Hollywood (post-Production Code prestige, c.1965-1985)
- Blaxploitation (US Black action cinema, c.1971-1979)
- Pinku Eiga (Japanese erotic cinema, c.1962-1988)

Historical categories are **director-gated or movement-anchored**. They cannot be entered by country+decade alone. Not every French film from 1960-1973 is French New Wave.

**Functional categories** are defined by what they serve in the archive rather than by a historical moment they name.

- Indie Cinema (1960s-2020s, 30+ countries) — arthouse films that are not Core, not exploitation, not mainstream
- Classic Hollywood (1930s-1950s) — pre-New Hollywood American studio cinema
- Music Films (all decades) — concert films and music documentaries

Functional categories are defined **negatively**: a film belongs here because it does not belong anywhere more specific. They must come last in routing order, after all historical categories have been checked.

### The Split Protocol

A category earns a sub-split when three conditions converge:

**Condition 1: Density** — Enough films accumulate that managing them as a single group loses information. A cluster of three films does not need a category. Thirty does.

**Condition 2: Coherence** — The sub-group shares a historically or formally real property the parent category does not have. A documented movement, a director cluster, a thematic tradition. Not every cluster of similar films is coherent.

**Condition 3: Archival necessity** — Would films be lost or misrepresented without the split? If removing the proposed category and scattering its films into neighbours loses something real, the category is necessary.

When all three hold, the category exists. The act of naming it makes it visible to the routing system.

### Positive-Space vs Negative-Space

Categories defined by what they ARE (named movements with distinctive vocabulary) are positive-space. Categories defined by what they are NOT (catch-alls for films that failed other checks) are negative-space.

This distinction determines:
- **Keyword routing eligibility:** Positive-space categories can use keyword signals (Tier A and B). Negative-space categories cannot — their vocabulary is too diffuse.
- **Certainty tier:** Positive-space categories can reach Tier 1-2 certainty. Negative-space categories are structurally Tier 3 (see §5).
- **False-positive risk:** Positive-space categories have low false-positive rates (orthogonal gates). Negative-space categories absorb whatever falls through upstream checks.

### Category Caps as Pressure Valves

Each category has a cap (maximum film count). Caps are not arbitrary — they encode the curator's intended depth of engagement:

- Giallo: 30 (focused engagement)
- Brazilian Exploitation: 45 (moderate)
- Hong Kong Action: 65 (strong)
- American Exploitation: 80 (deepest Satellite engagement)

When a category approaches its cap, the within-category depth hierarchy (§6) determines what stays and what goes. Tentpoles stay. Texture is the first to be cut.

*Deep-dive: [MARGINS_AND_TEXTURE.md](MARGINS_AND_TEXTURE.md) (satellite categories and caps), [REFINEMENT_AND_EMERGENCE.md](REFINEMENT_AND_EMERGENCE.md) §2-3 (split conditions and history).*

---

## 5. Certainty Tiers and the Inverse Gate Rule

Not all categories are equally automatable. A category with 4 independent corroborating signals (country + genre + decade + director) produces far more reliable classifications than one with 2 signals and a negative-space definition.

### Category Certainty Tiers

| Tier | Categories | Independent Gates | Auto-classify? |
|------|-----------|-------------------|---------------|
| **1** | Giallo, Brazilian Exploitation, HK Action, Pinku Eiga, American Exploitation, European Sexploitation, Blaxploitation | country + genre + decade + directors (4) | Yes, confidence 0.7-0.8 |
| **2** | Classic Hollywood, French New Wave, American New Hollywood | director/country + decade + keywords (3) | Yes, confidence 0.6-0.7 |
| **3** | Music Films, Indie Cinema | genre/country + decade (2, negative-space) | Review-flagged, confidence 0.4-0.5 |
| **4** | Japanese Exploitation, Cult Oddities | Manual only | No auto-classification |

**Counting gates:** Country, genre, decade, and director are independent gates (each from independent data sources). Keywords are corroborating — they strengthen a match but do not count as a separate gate. Negative-space definitions receive a one-tier penalty because they catch whatever failed upstream checks.

### The Inverse Gate Rule

As certainty decreases, gates get stricter — not looser:

- **Tier 1 match** → auto-classify (4 orthogonal gates make false positives extremely unlikely)
- **Tier 2 match** → auto-classify at lower confidence
- **Tier 3 match** → flag for review (human must confirm)
- **Tier 4** → manual only via SORTING_DATABASE entry
- **Fuzzy expansion** → structural signal + anchor proximity → SUGGEST only

This is counterintuitive but prevents the most common failure mode: catch-all categories silently absorbing misclassified films.

### Categories Must Earn Automation

A new Satellite category starts at Tier 4 (manual only). It earns higher tiers by demonstrating data support:
- Tier 3: at least 2 independent gate signals implemented and tested
- Tier 2: at least 3 independent gates, with 10+ films successfully auto-classified
- Tier 1: all 4 gate signals, with 20+ films auto-classified and tentpoles established

This prevents the failure mode that created the current dysfunction: defining 17 categories before proving the data can populate them.

### The Anchor-Then-Expand Pattern

1. **Establish anchors** — explicit lookups (SORTING_DATABASE, ~334 entries) + Reference canon (50 films) + SATELLITE_TENTPOLES = the known-good population
2. **High-certainty routing** — Tier 1-2 categories auto-classify. These newly classified films expand the anchor population per category.
3. **Fuzzy expansion (gated)** — for R2 films that do not match any rule, compare against established anchors. A film with partial Italian metadata from the 1970s near known Giallo tentpoles → SUGGEST for review queue, never auto-classify.

*Deep-dive: [certainty-first.md](../../exports/skills/certainty-first.md) (Skill 11 — full framework).*

---

## 6. Within-Category Depth: The Recursive Application

The four-tier logic is not a one-time sorting operation. It is a recursive principle. The same distinction between depth of engagement applies at every scale of organisation.

At the whole-archive level: Core / Reference / Satellite / Popcorn.
At the satellite category level: **Category Core** / **Category Reference** / **Category Texture**.

| Level | Meaning | Example (Giallo) |
|-------|---------|------------------|
| **Category Core** | Directors who defined or transformed the tradition | Bava (established visual grammar), Argento (pushed toward psychological abstraction) |
| **Category Reference** | Essential films that establish what the tradition contains | Fulci's key works, Martino's best gialli |
| **Category Texture** | Skilled practitioners, interesting experiments, historical completeness | Lenzi, Lado, late-period entries |

### The Four Criteria for Within-Category Core

The same criteria that define global Core status apply within a category:

1. **Sustained body of work** — multiple films in the tradition across multiple years
2. **Formal distinctiveness** — a recognisable visual/narrative language specific to their work in this tradition
3. **Influence** — later directors respond to them; the category looks different without them
4. **Collector commitment** — not just historically important but personally valued within the category

### Tentpole Ranking

The `rank_category_tentpoles.py` script scores films across 6 dimensions (0-10):
- Director tier within category
- Keyword alignment with category vocabulary
- Canonical recognition (awards, critical lists)
- Text signal match (overview/plot proximity to category themes)
- External validation (Wikipedia, scholarly mentions)
- Collection depth (how many films by this director in this category)

Films scoring highest become Category Core tentpoles. These anchor the category's identity and serve as reference points for fuzzy expansion (§5).

**Critical dependency:** Tentpole ranking assumes clean categories. If American Exploitation contains Dead Poets Society, the ranking scores a film that does not belong. The curation loop (§7) must clean categories BEFORE ranking fires.

*Deep-dive: [SATELLITE_DEPTH.md](SATELLITE_DEPTH.md) (full theoretical grounding — Sarris, Bloom, Bourdieu, Baxandall, Foucault, Altman).*

---

## 7. The Curation Loop: How the System Learns

The system was built as a one-directional classifier: data → rules → tier. It needs to be a bidirectional curation assistant: data → rules → suggestion → curator confirms → system learns.

### The Review Queue

The review queue is the interface between the system and the curator. Three populations enter it:

1. **Low-confidence classifications** — films classified by the pipeline with confidence below 0.5 (all Tier 3-4 auto-classifications)
2. **Enriched-but-unsorted** — R2/R3 films that no rule matched (genuine taxonomy gaps)
3. **Re-audit discrepancies** — films where current folder location disagrees with current routing rules

### Four Curator Actions

| Action | When | System Effect |
|--------|------|--------------|
| **Accept** | Classification correct | Move file to destination; classification confirmed |
| **Override** | Classification wrong, curator knows correct | Stage entry for SORTING_DATABASE.md; reclassify |
| **Enrich** | Data missing, curator can supply | Write to manual_enrichment.csv; promote readiness; reclassify |
| **Defer** | Uncertain, needs research | Park in review queue for next cycle |

**Enrich before Override:** Prefer enrichment (systemic improvement — helps all films by that director) over override (point fix — helps only this specific film). If providing the missing director name would let the routing rules work correctly, enrich. If the routing rules fundamentally cannot handle this film, override.

### Lifecycle Completion

The curation loop closes the lifecycle gap:

| Lifecycle Stage | Theory (REFINEMENT_AND_EMERGENCE §4a) | Tool |
|----------------|----------------------------------------|------|
| Stage 1: Define | Establish category identity | SATELLITE_CATEGORIES.md + constants.py |
| Stage 2: Cluster | Route films into categories | classify.py + move.py |
| Stage 3: Refine | Flag discrepancies | reaudit.py → **review queue** → accept/override/enrich/defer |
| Stage 4: Retain/Discard | Within-category hierarchy | rank_category_tentpoles.py → curator confirms |
| Stage 5: Reinforce | Feed decisions back | Override → SORTING_DATABASE growth. Enrich → manual_enrichment.csv. Patterns → routing rule changes. |

Each pass through the loop makes routing rules more precise, which makes the next clustering more accurate, which reduces the refinement burden. The system gets smarter — but only if every stage completes and decisions feed back.

*Deep-dive: [curation-loop.md](../../exports/skills/curation-loop.md) (Skill 12 — full framework).*

---

## 8. The Country Deepening Model

The recursive pattern described in §1 has played out most visibly at the level of national cinemas. A country's cinema is "explored" through the system when its different traditions are identified, separated, and named as distinct satellite categories.

### The Pattern

Every national cinema has an apex (its greatest directors) and margins (its genre traditions, movement periods, exploitation output). The system explores a country by:

1. **Identifying the apex** → promote to Core (director whitelist)
2. **Naming the margins** → create Satellite categories for distinct traditions
3. **Splitting margins when they diverge** → when one category contains films with clearly different curatorial relationships, split

### Worked Examples

**United States — deepest exploration (4 categories, spanning overlapping decades):**

```
US Cinema
├── Core: Kubrick, Scorsese, Coppola, Lynch, Cassavetes, Malick...
├── Reference: canonical films by non-Core US directors
├── Satellite:
│   ├── Classic Hollywood (1930s-1950s) — studio system era
│   ├── American New Hollywood (1960s-1980s) — prestige post-Production Code
│   ├── American Exploitation (1960s-1980s) — grindhouse, VHS cult
│   └── Blaxploitation (1970s-1990s) — identity-based subgenre
├── Popcorn: mainstream entertainment
└── Gap: US 1960s-1970s mainstream (too old for Popcorn, not exploitation)
```

The same time period (1960s-1980s) splits into THREE categories based on curatorial relationship. Without this split, Bob Fosse and Russ Meyer share a folder. The split resolves a fundamental ambiguity.

**Japan — 3 categories, overlapping decades:**

```
Japanese Cinema
├── Core: Kurosawa, Ozu, Mizoguchi, Suzuki...
├── Satellite:
│   ├── Japanese New Wave (1960s-1970s) — director-only routing (art cinema)
│   ├── Pinku Eiga (1960s-1980s) — country+decade+genre (erotic tradition)
│   └── Japanese Exploitation (1970s-1980s) — country+decade+genre (yakuza/action)
└── Indie Cinema catches remaining JP art films
```

A 1970s Japanese Drama by Oshima → Japanese New Wave (director override). A 1970s Japanese Drama/Romance by unknown → Pinku Eiga (country+genre match). Routing order encodes the hierarchy: director-gated categories must be checked before country+genre catch-alls.

**Hong Kong — 3 categories:**

```
Hong Kong Cinema
├── Core: Wong Kar-wai, Johnnie To...
├── Satellite:
│   ├── Hong Kong New Wave (1970s-1990s) — director-only (art cinema)
│   ├── Hong Kong Action (1970s-1990s) — country+decade+genre (martial arts)
│   └── Hong Kong Category III (1980s-1990s) — manual curation only
└── Indie Cinema catches remaining HK art films
```

**Italy, France, Brazil — 1 country-specific category each:**

```
Italian Cinema                 French Cinema                 Brazilian Cinema
├── Core: Antonioni,          ├── Core: Godard, Varda,     ├── Core: Rocha (candidate)
│   Fellini, Pasolini...      │   Chabrol, Demy...          ├── Satellite:
├── Satellite:                ├── Satellite:                │   └── Brazilian Exploitation
│   ├── Giallo               │   ├── French New Wave       │       (1960s-1990s)
│   └── European Sexploitation│   └── European Sexploitation└── Indie Cinema catches rest
└── Indie Cinema catches rest └── Indie Cinema catches rest
```

### The Core-Apex Principle

A national cinema is **hierarchically complete** when its greatest work lives in Core, its named movements live in Satellite, and its remaining margins fit into functional catch-alls.

**Why US, Japan, and HK have multiple categories while Italy, France, and Brazil have fewer:** The depth of sub-categorisation reflects the diversity of the country's margins, not the quality of its cinema. US cinema produced exploitation, prestige, and identity-based subgenres as distinct industrial traditions. Italian cinema produced Giallo as its primary exploitation tradition — the rest of Italian margins (poliziotteschi, Italian horror beyond giallo) are either too sparse in this collection or already captured by European Sexploitation.

### When Deepening Is Complete vs Incomplete

**Complete:** A country where the Core apex is established, named margins cover the distinct traditions, and remaining films route correctly to functional catch-alls. Italy is complete at this collection's scale: Antonioni/Fellini/Pasolini are Core, Giallo names the exploitation margin, European Sexploitation catches the rest.

**Incomplete:** A country where films are landing in the wrong categories or in Unsorted because the margin structure is too coarse. The US was incomplete before American New Hollywood split from American Exploitation — Fosse and Russ Meyer shared a folder.

**Unexplored:** A country where enough films exist to justify investigation but no sub-categories have been defined. The system should surface these through the curation loop (§7): when the review queue shows a cluster of films from a single country all going to Indie Cinema, it is a signal that the country may deserve its own named category.

### Triggering a New Country Split

The split protocol (§4) applies: density + coherence + archival necessity. But the recursive model adds a precondition: **you must have enough data to populate the new category reliably.**

Before splitting, verify:
1. The films that would populate the new category have R2/R3 data readiness (director AND/OR country known)
2. The proposed category would be Tier 2 or higher (at least 3 independent gates)
3. At least 10 films would route to the new category under proposed rules
4. The category can be grounded in published film-historical scholarship (Domain Grounding, Skill 4)

If any of these fail, the split is premature. Add the films to SORTING_DATABASE.md instead and revisit when data quality improves or the collection grows.

---

## 9. The Unsorted Protocol

Unsorted is not a failure state. It is a work queue. Each Unsorted film has a specific reason it is there and a specific protocol for addressing it.

### Three Populations, Three Strategies

**Population 1: No Year (R0) — 246 films**

Most of these are not feature films. They are supplements, interviews, behind-the-scenes content, TV episodes, and trailers that lack year information in their filenames.

**Strategy:** Run `normalize.py --nonfim-only` to identify non-film content. Filter these out of the classification pipeline entirely. For genuine feature films without years, the curator must supply the year manually (manual enrichment).

**Expected impact:** Removing non-film content from the Unsorted count clarifies the real classification backlog. If 200 of 246 are non-films, the actual Unsorted population drops from 405 to ~205.

**Population 2: Insufficient Data (R1) — 126 films**

These films have a year but API enrichment returned nothing — no director, no country, no genres. They cannot be classified by heuristic routing. This is the binding constraint of the whole system.

**Strategy (systematic, not ad-hoc):**

| Approach | Cost | Expected Yield | When to Use |
|----------|------|---------------|-------------|
| Cache invalidation + re-query | $0 then $$ | Low-moderate (APIs may still return nothing) | After parser/normalization changes |
| Title normalization improvement | $0 | Moderate (better titles → better API matches) | When parser bugs are found |
| Manual enrichment (curator provides director/country) | Time | High (curator recognises film) | For films the curator knows |
| Alternative title query | $$ | Moderate (non-English titles with romanised alternatives) | For foreign-language films |
| Batch title search via secondary sources | $$ | Variable | When primary APIs consistently fail for a country/decade |

**Priority order:** Manual enrichment first (highest yield, $0 API cost, but requires curator time). Then cache invalidation + re-query (may recover films where API was temporarily down). Then title normalization improvements (systemic fix). Alternative queries last (highest cost per film).

**Population 3: No Match (R2/R3) — 32 films**

These films have data — director, country, sometimes full TMDb enrichment — but no routing rule matches. This population splits into two sub-populations:

**Routing bugs (films that SHOULD classify but don't):**
- Princess Yang Kwei Fei (Mizoguchi, 1955, HK) — Mizoguchi is not in the Core director whitelist
- Picnic On The Grass (Renoir, 1959, FR) — Renoir is not in the Core director whitelist
- Black Girl (Ossie Davis, 1972, US) — should route to Blaxploitation but Ossie Davis is not in the director list
- The Incredible Melting Man (1977, US) — should route to American Exploitation

These are actionable fixes: add missing directors to whitelists, add SORTING_DATABASE entries.

**Genuine taxonomy gaps (no existing category fits):**
- US films from 1950s-1960s mainstream (The Dark at the Top of the Stairs, Bachelor in Paradise) — too old for Popcorn, not exploitation, not Core
- Single-country outliers (Braindead/NZ, Lorna/PH, Rose Seller/CO) — countries without enough films for a category
- Trailers and compilations (United Artists, Warner Brothers, 20th Century Fox) — non-film content that should be filtered

**Strategy:** Fix routing bugs immediately (whitelist additions, SORTING_DATABASE entries). For taxonomy gaps, evaluate whether a new rule or category is warranted (split protocol, §4). For non-film content, filter via normalize.py.

### The Unsorted Reduction Cycle

```
UNSORTED (405)
    │
    ├── Filter non-films (normalize.py --nonfim-only)
    │   └── ~200 removed → UNSORTED drops to ~205
    │
    ├── Fix routing bugs (whitelist additions, SORTING_DATABASE)
    │   └── ~10 reclassified → UNSORTED drops to ~195
    │
    ├── Manual enrichment (curator provides director/country for known films)
    │   └── ~30-50 promoted to R2/R3, many now classifiable
    │
    ├── Cache invalidation + re-query
    │   └── ~10-20 more API results
    │
    └── Remaining: genuine taxonomy gaps + films no source can identify
        └── These stay Unsorted until new data arrives or new categories are defined
```

Each pass through this cycle reduces the Unsorted count. The first pass (non-film filtering + routing bug fixes) has the highest yield for the lowest cost.

---

## 10. The Five-Stage Lifecycle (Revised)

The curatorial lifecycle from REFINEMENT_AND_EMERGENCE.md §4a, now integrated with Skills 10-12 and mapped to tooling:

### Stage 1: Define

Establish category identity. A category must satisfy the three conditions (density, coherence, archival necessity) and have clear boundaries in SATELLITE_ROUTING_RULES.

| Requirement | Verified by |
|------------|------------|
| Historical grounding | Domain Grounding (Skill 4) — published scholarship, not collection contents |
| Gate signals defined | SATELLITE_ROUTING_RULES entry with country codes, decades, genres, directors |
| Certainty tier assigned | Gate count → Tier 1/2/3/4 (§5) |
| Cap set | SATELLITE_CATEGORIES.md entry with rationale |

**Tooling:** `docs/SATELLITE_CATEGORIES.md` (human), `lib/constants.py` (code).

### Stage 2: Cluster

Route films into categories using available data.

| Step | Tool | Gate |
|------|------|------|
| Parse filename | lib/parser.py | R0 hard gate: no year → stop |
| API enrichment | lib/tmdb.py, lib/omdb.py | R1 gate: no data → skip routing |
| Explicit lookup | lib/lookup.py | Highest trust |
| Heuristic routing | lib/satellite.py, lib/core_directors.py | Certainty-tier-aware confidence |
| Output | sorting_manifest.csv + review_queue.csv | Confidence threshold gates manifest vs review |

**Tooling:** `classify.py`, `move.py`.

### Stage 3: Refine

Compare each film's current placement against current routing rules. Flag discrepancies.

| Input | Tool | Output |
|-------|------|--------|
| library_audit.csv | scripts/reaudit.py | reaudit_report.csv (discrepancies) |
| review_queue.csv | Curator triage | curation_decisions.csv |

**Curator actions:** Accept (confirm placement), Override (stage SORTING_DATABASE entry), Enrich (provide missing data), Defer (park for next cycle).

**Gate:** reaudit.py requires fresh library_audit.csv (mtime check). Ranking (Stage 4) should not fire on stale audit data.

**Tooling:** `scripts/reaudit.py` (diagnostic), `scripts/curate.py` (execution, planned).

### Stage 4: Retain and Discard

Within clean categories, apply within-category hierarchy. Identify Category Core, Category Reference, Category Texture. Films above the cap are ranked; tentpoles stay, texture is cut first.

| Input | Tool | Output |
|-------|------|--------|
| library_audit.csv + caches | scripts/rank_category_tentpoles.py | tentpole_rankings.md |

**Gate:** Stage 4 depends on Stage 3 being complete. You cannot rank films within a category if the category is polluted with films that do not belong. No code currently enforces this — it is a process dependency.

**Tooling:** `scripts/rank_category_tentpoles.py` (diagnostic).

### Stage 5: Reinforce

Confirmed decisions feed back into the classification model:

| Decision | Feeds into | Effect |
|----------|-----------|--------|
| Pin (film correctly placed despite routing) | SORTING_DATABASE.md | Explicit lookup fires on future runs |
| Director identified as Category Core | core_directors in routing rules | Director-gated routing strengthened |
| Keyword pattern discovered | keyword_signals in routing rules | Satellite keyword matching improved |
| Cap adjusted | SATELLITE_CATEGORIES.md + constants.py | Category depth calibrated |
| New category warranted | Full split protocol (§4) | New SATELLITE_ROUTING_RULES entry |

Each pass through the cycle makes routing rules more precise. The system only gets smarter if every stage completes and decisions feed back.

### Tooling Status

| Stage | Tool | Status |
|-------|------|--------|
| 1. Define | SATELLITE_CATEGORIES.md, constants.py | Complete |
| 2. Cluster | classify.py, move.py | Complete (data readiness + certainty gating planned: Issue #30) |
| 3. Refine | reaudit.py (diagnostic) | Diagnostic complete; execution tool planned (Issue #30 Component 5) |
| 4. Retain/Discard | rank_category_tentpoles.py | Diagnostic complete; no execution tool yet |
| 5. Reinforce | Manual edits to SORTING_DATABASE.md, constants.py | Process-enforced, not code-enforced |

---

## Appendix A: Relationship to Theory Essays

This document is the unified architecture reference. The five theory essays are deep-dives:

| Essay | Deep-dive for | Sections of this doc |
|-------|--------------|---------------------|
| [TIER_ARCHITECTURE.md](TIER_ARCHITECTURE.md) | Why four tiers, auteur criteria, Popcorn as parallel history | §3 |
| [MARGINS_AND_TEXTURE.md](MARGINS_AND_TEXTURE.md) | Satellite categories, caps, positive/negative-space | §4 |
| [REFINEMENT_AND_EMERGENCE.md](REFINEMENT_AND_EMERGENCE.md) | How categories split, the five-stage lifecycle, shadow cinema | §1, §4, §7, §10 |
| [SATELLITE_DEPTH.md](SATELLITE_DEPTH.md) | Within-category hierarchy, theoretical grounding (Sarris through Altman) | §6 |
| COLLECTION_THESIS.md | The curator's voice and personal philosophy | Not referenced here (orthogonal) |

Reading order for new arrivals: **this document first** (the whole system), then the essay most relevant to current work.

---

## Appendix B: Relationship to Skills 1-12

| Skill | Primary section | Role in the recursive model |
|-------|----------------|----------------------------|
| 1. R/P Split | §2, §10 | Parser (precision) vs routing rules (structured reasoning) |
| 2. Pattern-First | §3, §4 | Tier hierarchy is THE pattern; categories are instances |
| 3. Failure Gates | §2, §10 | R0 hard gate, R1 skip gate, confidence thresholds |
| 4. Domain Grounding | §4, §8 | Categories grounded in published scholarship, not collection |
| 5. Constraint Gates | §2 | Data readiness is the binding constraint |
| 6. Boundary-Aware Measurement | §10 | Enrichment vs routing boundary |
| 7. Measurement-Driven | §10 | Measure after each cycle pass |
| 8. Prototype Building | §4, §8 | Confirm category on real cases before building |
| 9. Creative & Discovery | §4, §8 | Category discovery protocol |
| 10. Data Readiness | §2 | R0-R3 levels gate the entire pipeline |
| 11. Certainty-First | §5 | Category certainty tiers, anchor-then-expand |
| 12. Curation Loop | §7 | Accept/Override/Enrich/Defer feedback cycle |

---

## Appendix C: Known Routing Gaps

As of 2026-02-24:

### Missing Core Directors
- **Kenji Mizoguchi** — not in Core whitelist. Princess Yang Kwei Fei (1955) goes Unsorted.
- **Jean Renoir** — not in Core whitelist. Picnic On The Grass (1959) goes Unsorted.

### Missing Satellite Director Entries
- **Ossie Davis** — Black Girl (1972, US) should route to Blaxploitation.
- **William Sachs** — The Incredible Melting Man (1977, US) should route to American Exploitation.

### US 1950s-1960s Mainstream Gap
Films like The Dark at the Top of the Stairs (1960), Bachelor in Paradise (1961), The Exiles (1961) have full R3 data but no category fits. Too old for Popcorn (low TMDb votes), not exploitation, not Core. Options:
- Extend Classic Hollywood decade range to 1960s
- Add individual SORTING_DATABASE entries
- Accept as permanent Unsorted (some films genuinely resist categorisation)

### Non-Film Content in Unsorted
Studio trailers (United Artists, Warner Brothers, 20th Century Fox) and compilations should be filtered by normalize.py non-film detection, not classified.

---

## Cross-References

- `CLAUDE.md` §3 Rules 1-12 — operational summaries of all skills
- `exports/skills/` — full skill framework documents
- `docs/SATELLITE_CATEGORIES.md` — per-category specifications
- `docs/CORE_DIRECTOR_WHITELIST_FINAL.md` — Core director list
- `docs/SORTING_DATABASE.md` — human-curated overrides
- `lib/constants.py` — SATELLITE_ROUTING_RULES, SATELLITE_TENTPOLES, REFERENCE_CANON
- Issue #30 — Phase 2: Structural architecture (data readiness scoring, confidence gating, review queue, curation tool)
- Issue #31 — Phase 3: Tactical wiring (handoff gates, R1 exit, confidence thresholds, category scale-back)
