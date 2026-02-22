# Issue #30: Elite curation model — tentpole directors, landmark films, anti-doom-scrolling architecture

**Severity:** High (strategic architecture revision)
**Component:** `docs/theory/SATELLITE_DEPTH.md`, `docs/SATELLITE_CATEGORIES.md`, `docs/theory/MARGINS_AND_TEXTURE.md`, `classify.py`, `lib/constants.py`, new script `scripts/rank_category_tentpoles.py`
**Type:** Architecture revision — documentation first, then implementation
**Discovered via:** Strategic review session (2026-02-22)
**Depends on:** Issue #29 (text signal enrichment — provides TMDb overview/plot data needed for ranking)

---

## Summary

The current system was designed for **mass organisation**: route everything into a tier, maximise classification rate, handle 491+ unsorted films. The correct design goal is **elite curation**: a navigable, curated library where every genre has 10–20 essential films, anchored by tentpole directors, and everything else has been consciously deleted rather than accumulated.

This is not a contradiction of the existing tier architecture — it is the tier architecture taken to its intended conclusion. The theory already supports it (caps as curatorial discipline; within-category hierarchy in `SATELLITE_DEPTH.md`). What's missing is the designation of *which specific films* are the tentpoles within each category, and the AI-assisted process for generating those recommendations.

---

## The Problem

### 1. Classification rate is the wrong metric

The system currently reports "11.2% classified (55/491 films)". This optimises for coverage — how many films have a destination. But the correct question is: **which of these 491 films should I keep?**

A collection where every film has a classification is not better than one where only the right 200 films have been kept. The classification pipeline should be a *triage tool*, not an exhaustive sorter.

### 2. The Unsorted queue is noise, not unclassified films

Of the 405 files in the staging report, roughly 60–70% are not films at all:

- **Bluray supplements** (~150 files): "Interview - Stanley Kubrick (1966)", "Trailer - The Vampire Lovers", "A Nun's Story - Interview with actress Eleonora Giorgi", "Within a Cloister - Interview with camera operator Daniele Nannuzzi"
- **TV episodes** (~20 files): S01E01–S01E11, Fallet S01E01–S01E08
- **Radio plays**: "Radio Play - Dracula (1938)", "Radio Play - Heart of Darkness (1938)"
- **Junk**: "sample.avi", "cowry-bcrazy-rp.avi", "BENEAT~1.MKV"

Only ~100–120 of the 405 are actual unclassified feature films. Trying to route a Kubrick interview extra through the classification pipeline is a category error. The system needs a supplement detection stage that diverts these before any tier routing fires.

### 3. No tentpole designation within categories

Each Satellite category has a cap (Giallo: 30 films) but no internal hierarchy of "which 5 films you keep last". If you have 30 Giallo films and want to cut to 10, the system gives you no guidance. The within-category hierarchy concept exists in `SATELLITE_DEPTH.md §7` (Category Core / Category Reference / texture) but is not populated with actual film lists per category.

### 4. The anti-doom-scrolling argument

The streaming problem is not finding something to watch — it is deciding. When every film is one scroll away, paradox of choice causes paralysis. You spend 45 minutes scrolling and watch something you've already seen.

A curated library with 10–15 films per genre solves this at the category level:
- "I'm in a Giallo mood" → 12 films, 3 obvious tentpoles, choose one
- "I want something Korean and serious" → 10 films, clear anchors (Parasite, Poetry, Burning, Oasis)
- "I want 80s Popcorn" → 30 films by genre, clear anchors (Die Hard, Back to the Future)

The navigation *is* the curation. You don't need an algorithm if the collection is already curated to be navigable.

---

## The Correct Model

### Architecture stays the same, caps tighten

The 4-tier hierarchy (Core → Reference → Satellite → Popcorn) is correct. No structural change needed. What changes:

| Dimension | Current | Target |
|---|---|---|
| Satellite category caps | 15–80 films each | 10–20 films each for historical movement categories |
| Number of Satellite categories | 17 | 25–30 (wider genre range, each tighter) |
| Within-category hierarchy | Defined in theory, not populated | Explicit tentpole list per category in `SATELLITE_CATEGORIES.md` |
| Unsorted queue | Classification-pending | Supplement-detected + deletion candidates |
| Classification metric | Coverage rate (%) | Curation quality (tentpoles confirmed per category) |

### Wider genre range, smaller caps

Instead of broad catch-all categories, move toward named historical movements with hard 10–15 film caps. Illustrative expansions from the Indie Cinema catch-all:

| New category | Cap | Tentpole directors |
|---|---|---|
| Korean New Wave | 10 | Park Chan-wook, Bong Joon-ho (pre-Hollywood) |
| Romanian New Wave | 8 | Cristian Mungiu, Cristi Puiu |
| Argentine New Cinema | 10 | Lucrecia Martel, Pablo Trapero |
| Mexican New Cinema | 10 | Carlos Reygadas, Amat Escalante |
| Brazilian Cinema Novo | 10 | Glauber Rocha, Nelson Pereira dos Santos |
| Czech New Wave | 10 | Vera Chytilová, Jiří Menzel, early Forman |
| Hong Kong Handover Cinema | 12 | Stanley Kwan, Ann Hui (Wong Kar-wai stays Core) |

Indie Cinema shrinks to a residual (cap 15) for films from countries with no dedicated category. Not a catch-all for 30 countries.

---

## The Tentpole Designation

Every Satellite category needs an explicit tentpole list in `SATELLITE_CATEGORIES.md`. Standard format:

```
**Category Core (keep last — defines what [Category] means):**
*The films that define what this category is. Keep even if nothing else remains.*
- [Film (Year)] — [Director] — [1-line reason: what this film establishes or transforms]

**Category Reference (keep if cap allows — essential range):**
*Essential examples that establish the tradition's range; films by secondary directors.*
- [Film (Year)] — [Director] — [1-line reason]

**Cut first when trimming:**
*AI-ranked texture films. Review when over cap.*
- [Film (Year)]
- *(rerun ranking script when collection changes)*

**AI ranking status:** [ ] Run  [ ] Human-reviewed  [ ] Confirmed
```

Category Core is the anti-doom-scrolling layer: 3–6 films that can stand alone as the category's argument. If someone asks "where do I start with Giallo?", Category Core is the answer.

### Worked example — Giallo

**Category Core:**
- Bay of Blood (1971) — Mario Bava — invents the visual grammar; slasher prototype; everything after responds to this
- Deep Red (1975) — Dario Argento — formal peak; most distinctive Giallo mise-en-scène and sonic language
- Suspiria (1977) — Dario Argento — genre at maximum intensity; canonical crossover to supernatural horror
- Don't Torture a Duckling (1972) — Lucio Fulci — introduces the Catholic guilt register; distinct strand from Bava/Argento

**Category Reference:**
- Blood and Black Lace (1964) — Bava — prototype fashion-world Giallo; stylised kill template
- The Bird with the Crystal Plumage (1970) — Argento — debut; establishes the witness-protagonist formula
- Your Vice Is a Locked Room and Only I Have the Key (1972) — Martino — peak erotic thriller variant

**Cut first:**
- Strip Nude for Your Killer (1975)
- Femina Ridens (1969)
- The Bloodstained Lawn (1973)

---

## AI-Assisted Tentpole Ranking

The tentpole designation is a human curation task, but generating the initial ranked list is a precision task that benefits from automation. The goal: AI recommends the top films per category; human reviews, adjusts, and confirms.

### Scoring model (0–10)

```
SCORE = director_tier + decade_match + keyword_alignment + canonical_recognition + text_signal + external_canonical

  director_tier         0-3  (3 = Category Core director; 2 = Reference director; 1 = listed; 0 = unlisted)
  decade_match          0-2  (2 = peak decade; 1 = adjacent; 0 = outside)
  keyword_alignment     0-2  (film's TMDb keywords ∩ category keyword_signals: ≥3 = 2; 1-2 = 1; 0 = 0)
  canonical_recognition 0-1  (TMDb vote_count ≥ 1 000 = 1; else 0)
  text_signal           0-1  (≥2 category vocabulary terms in overview+plot = 1; else 0)
  external_canonical    0-3  (Sight & Sound 2022 = +2; Criterion = +2; Wikipedia genre list = +1; additive, capped 3)
```

Score interpretation:
- **8–10:** Category Core candidate — watch first for Core vetting
- **5–7:** Category Reference candidate
- **0–4:** Texture — cut first when trimming

### Data inputs

**Already in pipeline (Issue #29):**
- TMDb keywords (for keyword_alignment)
- TMDb overview + OMDb plot (for text_signal)
- TMDb vote_count (for canonical_recognition)
- SATELLITE_ROUTING_RULES `directors` + `core_directors` lists (for director_tier)

**New external inputs (augment ranking quality):**

| Source | Signal | Method |
|--------|--------|--------|
| **Wikipedia genre article** | Film appears in genre's "Notable films" list | Fetch once per category (one HTTP request); cross-reference with collection |
| **Wikipedia film article** | "Considered a classic of the genre" in lead paragraph | Fetch per film; score for canonical language patterns |
| **Sight & Sound 2022 poll** | Film on decennial critics' poll | Static list; hardcode in `lib/constants.py` as `SIGHT_AND_SOUND_2022` |
| **Criterion Collection** | Film has a Criterion spine number | Static list; signals highest institutional canonical status |
| **Letterboxd curated lists** | Appears in "Essential [Category]" lists | Pre-scraped JSON per category; not real-time |

**Wikipedia is the highest-value new input.** The genre article (e.g., the "Giallo" Wikipedia page) represents accumulated editorial consensus from film scholars. A film listed there has cleared an implicit canonical bar. Fetching the genre article once per category costs one HTTP request and returns a film list usable for the full ranking pass. No authentication required.

### New script

```
scripts/rank_category_tentpoles.py
```

```bash
# Rank all films in a category
python3 scripts/rank_category_tentpoles.py Giallo

# All categories
python3 scripts/rank_category_tentpoles.py --all

# With Wikipedia fetch (one-time; adds ~2s per category)
python3 scripts/rank_category_tentpoles.py Giallo --wikipedia

# Markdown report
python3 scripts/rank_category_tentpoles.py Giallo --output output/tentpole_ranking_giallo.md
```

Output:

```markdown
## Giallo — Tentpole Ranking (2026-02)

### Category Core candidates (score 8–10)
1. Deep Red (1975) — Argento — 9/10
   director:3 decade:2 keywords:2 canonical:1 text:1 external:0
   TMDb keywords matched: giallo, psychosexual thriller, black-gloved killer

2. Bay of Blood (1971) — Bava — 8/10
   director:3 decade:2 keywords:1 canonical:1 text:1 external:0

### Category Reference candidates (score 5–7)
3. Blood and Black Lace (1964) — Bava — 7/10
   ...

### Texture — cut first when over cap (score 0–4)
8. Strip Nude for Your Killer (1975) — Bianchi — 3/10
   ...
```

---

## Supplement Detection (separate but related)

Before any tentpole ranking or tier routing, the classifier needs a Stage 0.5 that detects supplement filenames and diverts them to `Supplements/` rather than `Unsorted/`. This resolves ~60% of the Unsorted queue immediately.

Detection patterns:
- Prefix patterns: `Interview -`, `Trailer -`, `Video Essay -`, `Radio Play -`, `Audio essay`, `Restoration notes`
- TV episode patterns: `S\d{2}E\d{2}`, `Fallet S\d{2}E\d{2}`
- Generic single-name files with no year: `Trailer.mkv`, `Gallery.mkv`, `Outtakes.mkv`, `Deleted Scenes.mkv`
- Actor/critic name files with no year: matches a name-only pattern with no title

This is documented separately but logically precedes tentpole ranking in any implementation sequence.

---

## Where This Fits in Existing Docs

RAG search results (2026-02-22):

| Query | Top hit | Relevance |
|---|---|---|
| "tentpole films satellite category curation" | `SATELLITE_DEPTH.md §7` (182–225) | Direct — §7 already defines within-category hierarchy encoding; new content extends this |
| "satellite depth within-category tiers keep delete" | `SATELLITE_CATEGORIES.md §Satellite ≠ Dump Tier` | Confirms deletion framing already exists; tentpole list adds the "what to keep" positive statement |
| "caps curatorial discipline deletion" | `MARGINS_AND_TEXTURE.md §4` | Caps as statements of engagement; tentpole model makes this more explicit |

### Documents to update

1. **`docs/theory/SATELLITE_DEPTH.md`** — New §8 "AI-Assisted Tentpole Ranking" (insert before current §8 Monthly Review). Covers scoring model, data inputs, review workflow, relationship to within-category vetting.

2. **`docs/SATELLITE_CATEGORIES.md`** — Add standard tentpole block to each category entry. Giallo as worked example (populated above). Other categories: `[ ] Run  [ ] Human-reviewed  [ ] Confirmed` pending ranking pass.

3. **`docs/theory/MARGINS_AND_TEXTURE.md`** — Add §9 on the deletion decision workflow: caps as forcing functions, how tentpole designation enables cut decisions, the /Out quarantine pathway.

4. **New: `docs/AI_TENTPOLE_RANKING.md`** — Full practical procedure: running the script, reviewing output, confirming tentpoles, updating SATELLITE_CATEGORIES.md. Cross-reference from SATELLITE_DEPTH.md.

5. **`docs/CORE_DOCUMENTATION_INDEX.md`** — Add row for `AI_TENTPOLE_RANKING.md` in Quick Reference and Canonical Sources tables.

---

## Implementation Stages

### Stage 1: Documentation (this issue)

In order:
1. Write `docs/AI_TENTPOLE_RANKING.md` — full procedure spec
2. Update `docs/theory/SATELLITE_DEPTH.md` — add §8 AI-Assisted Tentpole Ranking
3. Update `docs/SATELLITE_CATEGORIES.md` — add standard tentpole template + Giallo worked example
4. Update `docs/theory/MARGINS_AND_TEXTURE.md` — add deletion workflow section
5. Update `docs/CORE_DOCUMENTATION_INDEX.md` — register new doc

### Stage 2: Supplement detection (separate issue, depends on: nothing)

Add Stage 0.5 to `classify.py`:
- Pattern-match filenames against supplement patterns
- Route matches to `Supplements/` (not `Unsorted/`)
- Output `supplements_manifest.csv` separately
- Expected result: Unsorted queue drops from ~405 to ~100–120 actual films

### Stage 3: Ranking script (depends on: Stage 1 docs + Issue #29 text signals)

Build `scripts/rank_category_tentpoles.py`:
- Reads `output/tmdb_cache.json` + `output/sorting_manifest.csv`
- Implements 6-dimension scoring model
- Optional Wikipedia fetch per category
- Outputs ranked markdown report per category
- No pipeline changes — read-only tool

### Stage 4: Category expansion (depends on: Stage 1 docs + curatorial review)

- Define new named categories (Korean New Wave, Romanian New Wave, etc.) in `lib/constants.py`
- Tighten existing caps: Indie Cinema from 40 → 15 residual; historical movement categories from 15–80 → 10–20
- Write tentpole blocks for new categories in `SATELLITE_CATEGORIES.md`
- Update routing rules to route to new categories before Indie Cinema fallback

### Stage 5: Human curation pass (depends on: Stage 3 ranking script)

- Run ranking script across all categories
- Human reviews output and confirms/adjusts tentpoles
- Write confirmed lists into `SATELLITE_CATEGORIES.md`
- Mark `AI ranking status: [x] Confirmed` per category
- This is the ongoing curatorial work, not a one-time task

---

## Decision needed before Stage 1

1. **Category expansion scope** — which new named categories? The list above is illustrative. Need to decide which movements have enough films in the collection to warrant a dedicated category (Rule 4: demonstrate density + coherence + archival necessity).

2. **Cap targets** — specific numbers for each category under the new model. Current caps range 10–80. Target range: 10–20 for historical movements, 15–25 for functional categories (Indie Cinema residual, Cult Oddities), 30–50 for Popcorn sub-genres.

3. **Criterion / Sight & Sound static lists** — should these be hardcoded in `lib/constants.py` or maintained as external JSON files? Hardcoding is simpler; JSON is easier to update when new polls are released.

4. **Wikipedia fetch policy** — per-category (once, for the genre article) or per-film (for the film's own article)? Per-category is cheap (~20 HTTP requests for all categories). Per-film is expensive (hundreds of requests) but gives richer data. Recommendation: start per-category.

---

## Cross-references

- Issue #28 — Classification model revision (character not prestige): the tentpole model extends that principle — within a category, Core films are those that define the character of the movement, not just films by the most famous director
- Issue #29 — Text signal enrichment: provides TMDb overview and OMDb plot that the ranking script uses for text_signal dimension
- `docs/theory/SATELLITE_DEPTH.md §3` — Four criteria for within-category Core status: the human review step applies these criteria to the AI ranking output
- `docs/theory/SATELLITE_DEPTH.md §7` — Cross-Application: Encoding the Within-Category Hierarchy: shows how tentpole designations are stored in SORTING_DATABASE.md and constants.py
- `docs/theory/MARGINS_AND_TEXTURE.md §4` — Caps as Curatorial Discipline: the theoretical basis for the deletion forcing function
