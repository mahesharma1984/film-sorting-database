# Issue #32: Pipeline Gate Architecture — Diagnosis and Decisions

**Type:** Architectural diagnosis → decisions required before further build work
**Severity:** High (structural — affects correctness of all downstream curation work)
**Discovered via:** Exploration session 2026-02-23 (triggered by Issue #30 ranking scores stuck at max 7/10)
**Depends on:** Issue #31 (reaudit tool — built), Issue #30 (tentpole ranking — built)
**Blocks:** Wikipedia fetch implementation, any further enrichment work, tentpole curation pass

---

## How This Was Found

This diagnosis emerged from asking a simple question: why do no films score above 7/10 in the tentpole ranking? The answer led upward through the scoring model, through the classification pipeline, and into the fundamental architecture of both workflows. The exploration covered three sessions of analysis using RAG queries, direct doc reads, and reaudit data.

The exploration confirmed that the 7/10 ceiling is not a tuning problem. It is a structural symptom of deeper architectural issues that manifest at four levels simultaneously.

---

## Part 1: The Scoring Type Error

### Diagnosis

The tentpole ranking score (0–10) is intended to answer: "within a Satellite category, which films are Category Core vs. Reference vs. Texture?" This is a **reasoning** judgment requiring four qualitative criteria (`docs/theory/SATELLITE_DEPTH.md §3`):

1. Sustained body of work in the category
2. Formal distinctiveness
3. Influence on how the category is understood (Bloom criterion)
4. Personal engagement depth (Bourdieu criterion)

The score as implemented measures:

| Dimension | What it actually measures |
|---|---|
| `director_tier` (0–3) | Is the director's name in a list? |
| `decade_match` (0–2) | Is the year in the valid range? |
| `keyword_alignment` (0–2) | Do TMDb tags overlap with category genre tags? |
| `canonical_recognition` (0–1) | Does TMDb/OMDb have ≥1000 votes? |
| `text_signal` (0–1) | Do 2+ text terms appear in overview/plot? |
| `external_canonical` (0–3) | S&S 2022 membership / Criterion / Wikipedia |

**The type error:** The score is a sum of data richness signals, not a measure of canonical authority. These are different properties that are **inversely correlated** within the Satellite tier: the more culturally important a Satellite film is, the more obscure it tends to be, and the less API data it has.

Bay of Blood (1971, Bava) scores 7/10 — Category Reference bracket. It is Category Core Giallo by any scholarly account. The score doesn't fail because the algorithm is miscalibrated. It fails because **canonical authority and data richness are orthogonal**, and the score conflates them.

### What the score is actually good for

Despite the type error, the score correctly orders films within a category for triage purposes. Bay of Blood at 7 surfaces above Strip Nude for Your Killer at 3. The score is a valid **discovery instrument** — it gets the curator to the right 5 films per category quickly. It should not be treated as a verdict.

The correct framing: scores are inputs to curator review, not outputs of curation. The curator confirms or overrides. Confirmed Category Core films go into `SATELLITE_TENTPOLES` (constants.py) and `SORTING_DATABASE.md`. The score is then no longer needed for those films.

**Reference:** `docs/theory/SATELLITE_DEPTH.md §7` — within-category hierarchy is encoded in SORTING_DATABASE.md and constants.py, not computed by a scoring algorithm.

---

## Part 2: R/P Split Violations in the Classification Pipeline

### Four operations conflated in one pipeline

The classification pipeline (`classify.py`) performs four distinct operations that should be kept separate:

**Operation 1 — Data extraction (correctly precision)**
Filename → title, year, director. Cache lookup → genres, country, keywords. This is pure precision and is correctly implemented.

**Operation 2 — Tradition membership detection (reasoning disguised as precision)**
The question "does this film belong to Giallo?" is a reasoning judgment about tradition membership. The pipeline answers it with precision tools:
- Is IT in `country_codes`? ← structural fact
- Is year in `[1960, 1989]`? ← structural fact
- Is genre in `['Horror', 'Thriller']`? ← API-returned label
- Does keyword match? ← tag overlap

This works when the film is an unambiguous member of the tradition with clean API data. It fails for:
- Marginal films: a Brazilian sexploitation film tagged only as "Horror" in TMDb fails the genre gate even though it belongs in Brazilian Exploitation by tradition
- API failures: foreign films that TMDb can't match have no keywords, no genres, no vote count — the Satellite gate requires three separate signals
- Tradition ambiguity: a Japanese film from 1975 that is both horror and softcore could legitimately be Pinku Eiga, Japanese Exploitation, or Giallo-adjacent

**Operation 3 — Tradition disambiguation (heuristic masquerading as reasoning)**
When a film matches multiple Satellite categories, the pipeline picks the **first match** in `SATELLITE_ROUTING_RULES` dictionary order. This is documented and intentional, but it is a convention — not a reasoned decision. It can't be justified; only the dictionary order can be justified, and that requires reading the dev guide.

**Operation 4 — Within-tradition ranking (pure reasoning replaced by sum-of-signals)**
Which films are Category Core vs. Reference vs. Texture? This requires the four qualitative criteria from `SATELLITE_DEPTH.md §3`. The 0–10 score approximates this with additive signals. See Part 1.

### The correct resolution

SORTING_DATABASE.md is the structurally correct resolution mechanism for Operations 2 and 3. When tradition membership is ambiguous, a human makes the judgment and records it as a lookup entry. The pipeline then retrieves it (Operation 1, pure precision). This is already how the architecture is designed — the problem is that SORTING_DATABASE.md entries only exist for a fraction of the collection.

**References:**
- `docs/DEVELOPER_GUIDE.md §2` — R/P split definition
- `docs/UNSORTED_ANALYSIS.md §152-197` — "Satellite routing too complex for marginal films"
- `exports/skills/rp-split.md §103-125` — splitting mixed tasks
- `issues/028-classification-model-revision-character-not-prestige.md` — fork model vs. linear chain

---

## Part 3: Genre Overlap Is Historical Fact, Not a Bug

The Satellite categories were built to reflect real film-historical movements. Real movements overlap. Italian films from 1972 were simultaneously Giallo, European Sexploitation, and sometimes Pinku-adjacent. The routing rules can't resolve this — not because the rules are poorly written, but because the ambiguity is genuine.

The dictionary priority order in `SATELLITE_ROUTING_RULES` resolves the ambiguity for the pipeline, but it does so by convention (Giallo before European Sexploitation for Italian films), not by reasoning about the film's actual tradition. This is correct behaviour for a precision system — but it should not be mistaken for a classification judgment.

The reaudit data confirms this: 56 films are flagged `wrong_category` within Satellite. Most of these are not definitively wrong — they're genuinely ambiguous, and the current routing rules chose one answer where the film could belong to either. These are the cases that need SORTING_DATABASE.md entries, not routing rule adjustments.

**References:**
- `docs/theory/MARGINS_AND_TEXTURE.md §8` — keyword signals apply to positive-space categories only
- `docs/theory/REFINEMENT_AND_EMERGENCE.md §5` — two kinds of category (historical vs. functional)

---

## Part 4: Workflow Map — Two Workflows, Their Data Inputs and Gates

The system has two distinct workflows that operate in sequence. Understanding them separately is the prerequisite for adding gates correctly.

### Workflow 1: New Film Pipeline (Unsorted → Library)

```
RAW FILENAME
  ↓ normalize.py
  [GATE 0 — HARD — IMPLEMENTED] Year extracted?
    → STOP: reason=unsorted_no_year

CLEANED FILENAME
  ↓ classify.py Stage 1: API Enrichment
  DATA IN: Cleaned title + year
  [GATE 1 — HARD — DESIGNED NOT INTEGRATED]
    Release tags survived title cleaning?
    → Skip API call (don't waste $$ on dirty title)
    → Script: scripts/validate_handoffs.py gate_title_cleaning()
  → Query: output/tmdb_cache.json (or TMDb API — $$)
  → Query: output/omdb_cache.json (or OMDb API — $$)
  [GATE 2 — SOFT — DESIGNED NOT INTEGRATED]
    Director OR country found?
    → WARN and continue (no director = degrades Satellite routing)
    → Script: scripts/validate_handoffs.py gate_api_enrichment()

ENRICHED METADATA {title, year, director, country, genres, keywords, overview, tagline, plot}
  ↓ classify.py Stages 2–9: Routing
  DATA IN: Enriched metadata
    Stage 2: SORTING_DATABASE.md lookup (highest trust — human curated)
    Stage 3: REFERENCE_CANON check (50-film hardcoded list)
    Stages 4–5: Satellite routing
      - Stage 4: Country/decade from filename metadata
      - Stage 5: TMDb structured data (country + genre + decade + director + keyword)
    Stage 6: User tag recovery ([Core-YYYY] in filename)
    Stage 7: Core director check (whitelist match)
    Stage 8: Popcorn check (popularity + vote_count + format signals)
    Stage 9: Default → Unsorted + reason code
  [GATE 3 — SOFT — DESIGNED NOT INTEGRATED]
    Enriched film went Unsorted?
    → WARN: enrichment succeeded but routing failed
    → Script: scripts/validate_handoffs.py gate_routing_success()

CLASSIFICATION RESULT {tier, destination, reason, confidence}
  → Written to: output/sorting_manifest.csv
  ↓ move.py
  DATA IN: sorting_manifest.csv + filesystem
  [GATE — HARD — IMPLEMENTED] Destination drive mounted?
    → STOP: can't move
  [GATE — SOFT — NOT DESIGNED] --dry-run reviewed before --execute?
    → No enforcement; process responsibility only

MOVED FILES → Library filesystem (Core/, Reference/, Satellite/, Popcorn/)
```

**Binding constraint in Workflow 1:**
Gate 2 (API enrichment). 83% of Satellite-candidate films have no TMDb data. When Gate 2 fires (no director AND no country), Stages 4–8 run and produce no value — they all fail on empty input and fall through to Unsorted. The constraint is not downstream routing complexity; it is upstream data absence. Optimizing Satellite routing rules, adding keyword signals, tuning text analysis — none of this moves the constraint because the data those rules require is absent.

**What correct Gate 2 behaviour looks like:**
If no director AND no country, skip Stages 4–5 (Satellite routing) entirely. Proceed to Stage 7 (Core director check using filename director only) then Stage 9 (Unsorted). The routing stages contribute nothing and should not run.

---

### Workflow 2: Curatorial Lifecycle (Library → Refined Library)

```
LIBRARY FILESYSTEM
  ↓ audit.py
  DATA IN: Filesystem walk of all tier folders
  [GATE — HARD — IMPLEMENTED] Drive mounted?
  → Output: output/library_audit.csv

output/library_audit.csv
  ↓ reaudit.py
  DATA IN: library_audit.csv + tmdb_cache.json + omdb_cache.json
  [GATE — MISSING] Is library_audit.csv fresh?
    → If files have moved since last audit, reaudit operates on stale data
    → Proposed: check mtime of library_audit.csv vs. sorting_manifest.csv
  [GATE — MISSING] What % of films have no_data?
    → High no_data rate = large unverifiable population
    → Proposed: WARN if >40% of category is no_data
  → Output: output/reaudit_report.csv

output/reaudit_report.csv ← HUMAN READS THIS
  Human decides per discrepancy: reclassify / pin (→ SORTING_DATABASE.md) / investigate
  [GATE — MISSING — LIFECYCLE SEQUENCING]
    High-confidence wrong_tier discrepancies resolved before ranking?
    → Theory says Stage 4 (ranking) depends on Stage 3 (refine) being complete
      docs/theory/REFINEMENT_AND_EMERGENCE.md §4a
    → No code enforces this. Ranking can run on polluted categories.
    → Proposed: reaudit_report.csv as required input to ranking script,
      or a --acknowledge-pollution flag that makes the trade-off explicit

HUMAN DECISIONS → SORTING_DATABASE.md additions + SATELLITE_TENTPOLES additions
  ↓ rank_category_tentpoles.py
  DATA IN: library_audit.csv + tmdb_cache.json + omdb_cache.json
  [GATE — MISSING] Category pollution ratio acceptable?
    → Proposed: check unroutable/wrong_tier % from reaudit_report.csv before scoring
    → WARN if category has >20% discrepancies
  [GATE — MISSING — Wikipedia fetch]
    Article fetched successfully? N film titles extracted > threshold?
    → WARN if fetch returns <5 film titles (article may be wrong/empty)
  [GATE — MISSING — Wikipedia matching]
    Title normalization symmetric? (same normalize_for_lookup() both sides)
    → Proposed: validate sample matches before using Wikipedia data in scoring

output/tentpole_rankings.md ← HUMAN READS THIS
  Human confirms Category Core per category
  ↓ Writes to: SATELLITE_TENTPOLES (lib/constants.py) + SORTING_DATABASE.md
  ↓ Re-run Workflow 1 → routing rules improve → cycle repeats
```

**Binding constraint in Workflow 2:**
Category pollution. You cannot produce reliable tentpole rankings until categories contain only films that belong there. Rankings on a polluted category are plausible-looking but built on corrupt input — scoring films that don't belong in the category as if they're candidates for Category Core.

The reaudit data (Feb 22) shows 306/779 organized films are mismatches (39%). American Exploitation has 65 discrepancies — the category currently contains Dead Poets Society, Leaving Las Vegas, Three Days of the Condor, and others. Any Giallo/European Sexploitation/Blaxploitation cross-contamination similarly affects those rankings.

**REFINEMENT_AND_EMERGENCE.md §4a** makes the lifecycle sequencing explicit: "Stage 4 (retain and discard) depends on Stage 3 (refine) being complete." No code enforces this sequencing.

---

## Part 5: Gate Inventory — What Exists, What's Missing

### Existing gates (working)

| Gate | Location | Type | Status |
|---|---|---|---|
| No year extracted | classify.py | HARD | Working |
| Destination drive mounted | move.py | HARD | Working |
| Satellite cap enforcement | lib/satellite.py | SOFT | Working (warns, allows human override via SORTING_DATABASE) |
| TMDb result validation | lib/tmdb.py `_validate_result()` | HARD | Working (prevents cache poisoning) |
| Country code mapping | lib/omdb.py | SOFT | Working |

### Designed but not integrated

These gates exist in `scripts/validate_handoffs.py` as a `HandoffGates` class with full implementation. They are commented out in the file with "Example integration for classify.py:" and have never been wired into the actual pipeline.

| Gate | validate_handoffs.py method | Proposed severity | Downstream impact if missing |
|---|---|---|---|
| Title cleaning | `gate_title_cleaning()` | HARD | API query receives dirty title → cache miss → API call wasted |
| API enrichment | `gate_api_enrichment()` | SOFT (warn) | Stages 4–8 run on empty input |
| Routing success | `gate_routing_success()` | SOFT (track) | Enriched films lost to Unsorted without systematic tracking |

### Not designed (missing entirely)

| Gate | Workflow | What it checks | Proposed type |
|---|---|---|---|
| library_audit.csv freshness | Curatorial | mtime vs. last move execution | WARN |
| no_data population rate | Curatorial (reaudit) | % of category with no cache data | WARN |
| Category pollution before ranking | Curatorial (ranking) | % wrong_tier / unroutable from reaudit | WARN or HARD |
| Lifecycle sequencing | Curatorial | Is reaudit acted on before ranking runs? | Process + optional HARD |
| Wikipedia fetch validation | Curatorial (ranking) | Did fetch return >N film titles? | SOFT |
| Wikipedia title normalization | Curatorial (ranking) | Symmetric normalize_for_lookup() both sides | HARD (for matching) |

---

## Part 6: The Three-Taxonomy Problem — Wikipedia

### What was planned

Issue #30 specified Wikipedia per-category fetch as the highest-value data input for `external_canonical`. The genre article (e.g., the "Giallo" Wikipedia article) represents accumulated editorial consensus from film scholars. Films listed there have cleared an implicit canonical bar. Fetch once per category (~20 HTTP requests for all categories).

### The architectural problem

`exports/skills/domain-grounding.md §150-169` names the "three-taxonomy problem": detection taxonomy, processing taxonomy, and output taxonomy drifting apart when stages use parallel systems instead of referencing a canonical one.

In this project:
- **Canonical taxonomy**: `SATELLITE_ROUTING_RULES` + `SATELLITE_TENTPOLES` + `SORTING_DATABASE.md` — single source of truth for what each category means
- **Wikipedia's taxonomy**: the "Giallo" Wikipedia article's definition of which films are notable Giallo — different scope, different editorial bar, different update cadence
- **Ranking taxonomy**: the 0–10 score's `external_canonical` dimension — introduces Wikipedia's editorial judgments as a direct scoring input

Wikipedia used as a direct `score += 1` input creates a parallel taxonomy that bypasses the project's canonical taxonomy. A film appearing in Wikipedia's "Giallo" article has cleared Wikipedia's editorial bar — not this collection's curatorial bar. The bars are different:
- Wikipedia's Giallo article is a broad genre survey covering hundreds of films
- This collection's Giallo category has a cap of 30 films with explicit tentpoles

If the Wikipedia signal directly affects scores, the ranking output reflects Wikipedia's judgment, not the curator's. The canonical taxonomy is bypassed, not referenced.

### The correct data flow

```
WRONG (parallel taxonomy):
  Wikipedia article → score_external_canonical() += 1 → ranking score

CORRECT (canonical taxonomy as reference):
  Wikipedia article
    → curator sees: "Bay of Blood in Wikipedia's Giallo article"
    → curator confirms: validates Category Core status
    → curator writes: SATELLITE_TENTPOLES entry in lib/constants.py
    → canonical taxonomy updated
    → future rankings: director_tier = 3 (tentpole) from canonical source
```

Wikipedia is REASONING input for the human curator. The curator's confirmed decision then feeds into the canonical taxonomy (SORTING_DATABASE.md, SATELLITE_TENTPOLES). The decision propagates through the pipeline as a precision lookup — which is how the architecture was designed.

**The practical change this implies:**
Rather than `score_external_canonical()` using Wikipedia for a +1 score increment, the ranking script should display Wikipedia film list coverage as **curator-visible annotation** — "this film appears in the Wikipedia Giallo article" — alongside but separate from the numerical score. The curator uses this as evidence when confirming or overriding the ranking. The score remains data-driven; the canonical judgment remains human-made.

---

## Part 7: Current State Summary

### What works

- Classification pipeline correctly routes films with clean data and API coverage
- Reaudit tool (Issue #31) correctly identifies discrepancies using existing caches
- Tentpole ranking (Issue #30) correctly orders films within categories using available data (max score 7 reflects data coverage, not algorithm failure)
- Handoff gates designed in validate_handoffs.py are correct in design

### What doesn't work

- Gates 1-3 are not integrated — classify.py runs without handoff validation
- Ranking can run on polluted categories with no warning
- The 83% API data gap means keyword/text/canonical signals are absent for most Satellite films
- Wikipedia, if added as a direct score signal, would create a parallel taxonomy

### The pipeline's actual capability ceiling

Given current data coverage: the ranking score collapses to `director_tier + decade_match` for 83% of films (range 0–5). That range separates tentpoles from texture with enough signal for curator triage but not for automated category determination.

The ceiling is not a software problem — it is a data coverage problem compounded by a structural property: Satellite-tier films are niche by definition, and niche films have the lowest API coverage. This inverse relationship is inherent, not fixable by improving routing rules.

---

## Part 8: Decisions Required Before Further Build Work

Six decisions. Each has option A (more code enforcement) and option B (process enforcement).

### Decision 1: Gate 2 hardening (API enrichment)

Currently: SOFT, not integrated — warns and continues even with no director AND no country.

**Option A (harder gate):** If no director AND no country from API, skip Stages 4–5 (Satellite routing) entirely. Proceed to Stage 7 (Core check) then Unsorted. Saves cycles, makes the failure mode explicit.
**Option B (status quo + integration):** Integrate as SOFT (warning only), keep all stages running. Add reason code enrichment: `unsorted_no_enrichment` distinct from `unsorted_no_match`.

Impact: Option A changes some routing outcomes for films with director in filename but no API data — they still reach Stage 7 (Core check). Only films with no director anywhere are affected.

### Decision 2: Gates 1 and 3 integration

Gate 1 (title cleaning) and Gate 3 (routing success tracking) are straightforward integrations.

**Option A:** Integrate both into classify.py as designed in validate_handoffs.py. Gate 1 = HARD (no API call on dirty title). Gate 3 = SOFT (track enriched-but-Unsorted as a metric).
**Option B:** Keep validate_handoffs.py as a standalone audit tool run separately. Don't integrate into classify.py's hot path.

### Decision 3: Freshness gate on library_audit.csv

**Option A:** reaudit.py checks mtime of library_audit.csv vs. sorting_manifest.csv. Warns if library_audit.csv is older.
**Option B:** Curator responsibility. Document in procedure that audit.py must be run before reaudit.py.

### Decision 4: Pollution gate before ranking

**Option A (HARD):** rank_category_tentpoles.py requires reaudit_report.csv as an argument, reads the pollution rate for the requested category, refuses to rank if >20% wrong_tier or unroutable.
**Option B (SOFT):** WARN on pollution rate, proceed with ranking but annotate report header: "Warning: 30% of this category's films are flagged as discrepancies in the last reaudit."
**Option C (process only):** Document the sequencing requirement, no code enforcement.

### Decision 5: Lifecycle sequencing enforcement

Currently: nothing prevents running ranking before reaudit is acted upon.

**Option A:** Ranking script checks timestamp of reaudit_report.csv. If reaudit is newer than last SORTING_DATABASE.md edit, warns that the reaudit output has not been acted on.
**Option B:** Process documentation only. Update CLAUDE.md §5 Key Commands with explicit sequencing.

### Decision 6: Wikipedia data flow

The highest-stakes architectural decision.

**Option A (annotate, don't score):** Wikipedia fetch returns a set of film titles. The ranking report annotates: "★ Wikipedia [Category]" for matching films. Score unchanged. Curator uses annotation as evidence. No parallel taxonomy created.
**Option B (score with gate):** Wikipedia data goes into `external_canonical += 1` as currently designed, BUT only after: (a) pollution gate passes, (b) fetch validation gate passes (>5 titles returned), (c) title matching uses year-constrained normalized comparison. Parallel taxonomy risk remains but is bounded.
**Option C (remove from score, keep for display):** `external_canonical` removes Wikipedia dimension entirely. Score becomes a 0–9 maximum (S&S: +2, Criterion: +1). Wikipedia-listed films shown in report as annotation. Highest structural integrity.

---

## Recommended Resolution Order

Based on the binding constraint analysis:

1. **Act on reaudit output** (human task, no code) — clean the polluted categories. This is the binding constraint for the curatorial lifecycle. Everything downstream is unreliable until this is done.

2. **Integrate Gates 1 and 3** (small code change, high value) — title cleaning and routing success tracking are $0 checks that make the pipeline's failure modes visible.

3. **Decide Decision 6 (Wikipedia data flow)** — the architectural question that determines how the Wikipedia fetch is implemented. Option A or C is recommended; Option B carries the three-taxonomy risk.

4. **Implement Wikipedia fetch correctly** (after Decision 6) — with disk caching, fetch validation gate, year-constrained title matching, and the data flow pattern chosen in Decision 6.

5. **Decision 4 (pollution gate)** — after the reaudit cleanup, calibrate the threshold against the cleaned state. The right threshold is the post-cleanup pollution rate + a tolerance margin.

---

## Cross-References

| Reference | Relevance |
|---|---|
| `docs/theory/SATELLITE_DEPTH.md §3` | Four criteria for within-category Core status (the reasoning the score approximates) |
| `docs/theory/SATELLITE_DEPTH.md §7` | Where tentpole designations are stored (canonical taxonomy) |
| `docs/theory/REFINEMENT_AND_EMERGENCE.md §4a` | Curatorial lifecycle stages and their sequencing dependency |
| `docs/theory/MARGINS_AND_TEXTURE.md §4` | Caps as curatorial discipline (forcing function for within-category ranking) |
| `docs/DEVELOPER_GUIDE.md Rule 0` | Declare failure gates — foundational principle |
| `docs/DEVELOPER_GUIDE.md §2` | R/P split definition and examples |
| `docs/UNSORTED_ANALYSIS.md §16-53` | Classification pipeline 8 stages + reason codes |
| `scripts/validate_handoffs.py` | Gate 1, 2, 3 implementations (designed, not integrated) |
| `exports/skills/constraint-gates.md` | Gate design patterns, cost-ordering, standalone audit mode |
| `exports/knowledge-base/constraint-theory.md §41-68` | Theory of Constraints formal definition |
| `exports/skills/domain-grounding.md §150-169` | Three-taxonomy problem |
| `exports/knowledge-base/system-boundary-theory.md §134-152` | Gate expensive stages behind cheap validation |
| `issues/028-classification-model-revision-character-not-prestige.md` | Fork model vs. linear chain; film character determines tier |
| `issues/030-elite-curation-tentpole-model.md` | Wikipedia fetch specification (Issue #30 Stage 3) |
| `issues/031-library-re-audit-tool.md` | Reaudit tool specification; lifecycle sequencing dependency |
| `output/reaudit_report.csv` | 306/779 discrepancies (Feb 22, 2026) — current pollution baseline |
