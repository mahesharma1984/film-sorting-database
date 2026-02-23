# Skill: Data Readiness (Input Quality Gates for Classification Pipelines)

**Purpose:** Assess whether enough data exists to produce a meaningful classification before entering routing stages.
**Addresses:** Wasted computation on empty data, misleading reason codes, silent pipeline failures when API enrichment returns nothing.

---

## Core Principle

**Do not run routing on films that lack the data routing needs. A routing stage that consumes an empty field is not "checking" — it is producing a guaranteed failure that looks like a legitimate result.**

Without data readiness:
- Films with no API data enter all 9 routing stages, fail at each one silently, and exit as `unsorted_no_director` — which conflates "we had no data to route with" and "we had data but no rule matched"
- Expensive routing stages (Satellite keyword matching, Popcorn popularity checks) run on empty input and return false negatives indistinguishable from legitimate mismatches
- Statistics become noisy: "126 films with no director match" hides the fact that 126 films had no director data at all — the routing stages never had a chance to match
- Downstream analysis (re-audit, tentpole ranking) inherits the noise

---

## Readiness Levels

Every film entering the classification pipeline has a measurable data readiness level based on what fields survived parsing and API enrichment.

| Level | Criteria | What Routing Can Work | Confidence Cap |
|-------|---------|----------------------|---------------|
| **R0** | No year extracted from filename | Explicit lookup only (SORTING_DATABASE title match) | 0.0 |
| **R1** | Title + year, but no director AND no country (API returned nothing or wasn't called) | Lookup + Reference canon + user tag recovery | 0.3 |
| **R2** | Partial enrichment: director OR country present, but not both; OR genres missing | Lookup + Reference + partial Satellite (director-only or country-only rules) + Core director check | 0.6 |
| **R3** | Full enrichment: director AND country AND genres all present | Full pipeline — all routing stages | 1.0 (no cap) |

**Assessment point:** Readiness is measured once, after API enrichment (Stage 1) and before routing (Stages 2+). It is a property of the data, not of the classification result. A film's readiness level does not change during a single classification run.

**Confidence cap:** The readiness level places an upper bound on the confidence of any classification produced. An R2 film cannot have confidence higher than 0.6, regardless of which routing stage matches it. This prevents high-confidence results from partial data.

---

## Gate Behavior by Level

### R0: Hard Stop (Already Implemented)

No year means no decade. Decade is required for all tier-based routing (Core/decade/director, Satellite/category/decade, Popcorn/decade). The only stage that can fire without a year is explicit lookup (SORTING_DATABASE title-only match).

**Current implementation:** `classify.py` line ~494, hard gate returns `unsorted_no_year`.

**No change needed.** R0 is already correct.

### R1: Skip Routing, Queue for Enrichment

Title + year exist, but API enrichment returned nothing useful. The film has no director, no country, no genres, no keywords. Running Satellite routing (country + genre + decade), Core director check (requires director), or Popcorn (requires popularity/cast) is guaranteed to fail.

**Gate behavior:**
1. Run Stage 2 (explicit lookup) — may match on title+year alone
2. Run Stage 3 (Reference canon) — may match on normalized title+year
3. Run Stage 6 (user tag recovery) — may match on filename bracket tag
4. **Skip Stages 4-5 (Satellite), 7 (Core director), 8 (Popcorn)** — these stages consume data that R1 films don't have
5. If no match: return `unsorted_insufficient_data` (not `unsorted_no_director`)

**Why a distinct reason code:** `unsorted_no_director` currently conflates two populations:
- Films where API returned nothing (R1) — a data problem, fixable by manual enrichment
- Films where API returned data but no routing rule matched (R2+) — a taxonomy gap, fixable by adding rules

Separating these populations enables targeted action: R1 films need data, R2+ films need rules.

### R2: Route with Capped Confidence

Partial data exists. The film has a director but no country, or country but no director, or both but no genres. Some routing stages can fire, but the classification is lower-certainty because not all corroborating signals are present.

**Gate behavior:**
1. Run all stages normally
2. Cap confidence at 0.6 for any result (overrides stage-specific confidence if higher)
3. If result confidence is below review threshold → route to review queue

**Example:** A film with director "Dario Argento" but no country code. Core director check can match (confidence 1.0 → capped to 0.6). Satellite routing cannot match on country+genre but may match on director-only rules (confidence 0.7 → capped to 0.6). The cap reflects: "we have a match, but we're missing corroborating data."

### R3: Full Pipeline

All critical fields present. No restrictions on routing stages or confidence values. This is the current behavior for films with complete API enrichment.

---

## The Data Readiness Assessment

The readiness check is a $0 function that reads fields already in memory. It runs after `_merge_api_results()` and before Stage 2.

```
assess_readiness(metadata, tmdb_data):

  IF metadata.year is None:
    return R0

  has_director = metadata.director is not None
                 OR (tmdb_data is not None AND tmdb_data['director'] is not None)

  has_country  = metadata.country is not None
                 OR (tmdb_data is not None AND len(tmdb_data['countries']) > 0)

  has_genres   = tmdb_data is not None AND len(tmdb_data['genres']) > 0

  IF NOT has_director AND NOT has_country:
    return R1

  IF has_director AND has_country AND has_genres:
    return R3

  return R2  (partial: has some but not all)
```

**Output:** A single string (`R0`, `R1`, `R2`, `R3`) stored in the classification result and written to the manifest CSV. This enables downstream tools (dashboard, re-audit, tentpole ranking) to filter by data quality.

---

## Design Rules

### Rule 1: Readiness Is a Property of Data, Not of Classification

A film's readiness level describes what data is available, not what classification it received. An R1 film that matches via explicit lookup (confidence 1.0) is still R1 — the data is still insufficient for heuristic routing, even though the lookup succeeded. The readiness level tells you: "if this film weren't in SORTING_DATABASE, how well could the pipeline classify it?"

This matters for re-audit: when routing rules change, R1 films that were only saved by explicit lookup are fragile — they depend on a single data source.

### Rule 2: Readiness Gates Are Cheap, Routing Is Expensive

The readiness assessment is a $0 field check. The stages it gates (Satellite routing with keyword matching, Popcorn with popularity thresholds) involve dict lookups, list intersections, and string comparisons across multiple categories. For 126 R1 films, skipping 5 routing stages each saves 630 stage evaluations that would all return None.

More importantly, the diagnostic value is high: the reason code `unsorted_insufficient_data` immediately tells the curator "this film needs manual enrichment or cache invalidation" rather than "something didn't match and we don't know why."

### Rule 3: Readiness Feeds the Curation Loop

R1 films are the primary candidates for manual enrichment. When a curator provides missing metadata (director, country) via the manual enrichment pathway, the film's readiness level rises from R1 to R2 or R3, and previously-skipped routing stages can now fire.

The readiness level creates a natural work queue:
- R1 → "needs data" (curator action: enrich or add to SORTING_DATABASE)
- R2 → "has partial data, low-confidence result" (curator action: verify or enrich further)
- R3 → "fully enriched, pipeline had every chance to classify" (curator action: accept result or investigate taxonomy gap)

### Rule 4: Confidence Cap Is Not Confidence Override

The readiness cap sets a ceiling, not a floor. An R2 film matched by Satellite director-only routing (base confidence 0.7) gets capped to 0.6. But an R2 film that fails all routing stages still gets confidence 0.0 (Unsorted). The cap prevents overconfident results from partial data — it does not inflate confidence for poor matches.

---

## Diagnostic: How to Use Readiness in Debugging

| Symptom | Check Readiness | Action |
|---------|----------------|--------|
| High `unsorted_no_director` count | How many are R1? | If most are R1: data problem (API not returning results). Run `invalidate_null_cache.py`, check API keys. |
| High `unsorted_no_match` count | How many are R2 vs R3? | R2: partial data, may classify with more enrichment. R3: genuine taxonomy gap — need new routing rules. |
| Classification rate dropped after change | Check readiness distribution shift | If R3 count dropped: enrichment regression. If R3 stable but classifications changed: routing regression. |
| Re-audit finds wrong-tier films | What readiness level? | R2 wrong-tier films are high risk — classification was made on partial data. R3 wrong-tier films are routing bugs. |

---

## Integration with Other Skills

| Skill | How Data Readiness Connects |
|---|---|
| **Failure Gates** | Data Readiness is the input-side complement to Failure Gates. Failure Gates declare what happens when a check fails. Data Readiness declares which checks are worth running given the available data. |
| **Constraint Gates** | Data Readiness is a Level 0 gate: validate that routing has the data it needs before running routing. It addresses the project's binding constraint (Gate 2: API enrichment quality). |
| **Boundary-Aware Measurement** | The enrichment/routing boundary is where readiness is assessed. Data Readiness formalizes that boundary as a gate, not just a measurement scope. |
| **Certainty-First Classification** | Data Readiness determines which certainty tier a classification can achieve. An R1 film cannot reach Tier 1 certainty regardless of category definition. |
| **Curation Loop** | Data Readiness creates the "needs enrichment" signal that feeds the manual enrichment pathway. |

---

## Checklist

When adding or modifying a routing stage:
- [ ] Documented which data fields the stage consumes
- [ ] For each field: what readiness level is required? (R1 stages need no API data; R2+ stages need at least one field; R3 stages need multiple fields)
- [ ] Stage does not execute at readiness levels below its requirement
- [ ] Reason codes distinguish "insufficient data" from "no rule match"
- [ ] Confidence cap applied based on readiness level

When debugging classification failures:
- [ ] Checked readiness level of failed film first
- [ ] If R1: investigated why API returned nothing (cache poisoning? title parsing error? API down?)
- [ ] If R2: identified which field is missing and whether it's recoverable
- [ ] If R3: investigated routing rules (genuine taxonomy gap)
