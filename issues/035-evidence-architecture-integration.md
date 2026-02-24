# Issue #35: Evidence Architecture Integration — Closing the Feedback Loop

**Type:** Architectural — pipeline observability + feedback infrastructure
**Severity:** High (structural — every Issue #14–#34 is a symptom of the same root cause)
**Discovered via:** Exploration session 2026-02-24 (triggered by Issue #34 pattern recognition)
**Depends on:** Issue #32 (pipeline gate architecture), Issue #34 (R2b genre gate diagnosis)
**Blocks:** Systematic Unsorted reduction without manual patch cycles
**Architecture doc:** `docs/architecture/EVIDENCE_ARCHITECTURE.md`
**Theory grounding:** `docs/theory/THEORETICAL_GROUNDING.md` §8-§12

---

## How This Was Found

Issue #34 identified 44 R2b films blocked by the genre gate despite having director + country data. The proposed fix — add directors to lists, pin films to SORTING_DATABASE — works for those 44 films. But the same pattern has repeated across Issues #14 through #34:

1. A population of stuck films is discovered (by running classify and reading the output)
2. A human diagnoses which gate blocks them (by reading the source code)
3. The human manually adds directors to a list, or pins films, or relaxes a gate
4. The pipeline runs again, classifying the specific films that were fixed
5. A new population of stuck films is discovered → cycle repeats

This is single-loop learning (THEORETICAL_GROUNDING §8): fixing instances without questioning governing variables. The pipeline was designed as a classifier. It needs to become an evidence accumulator — a system that records its reasoning so that the Refine stage of the recursive curation model (RECURSIVE_CURATION_MODEL.md) has material to work with, instead of requiring the curator to re-derive everything from scratch.

---

## The Root Problem: Information Destruction

The classification pipeline (`classify.py` lines 472–777) is a one-pass funnel with early exits. Each stage either returns a `ClassificationResult` immediately or falls through to the next stage. When a film exits at any stage, all intermediate evidence from prior stages is discarded.

### Stage-by-stage destruction map

```
FILENAME
  │
  ├─[Stage 0: Parser]
  │   Produces: title, year, director, language, country, user_tag, format_signals
  │   Destroys: format_signals (stripped during cleaning)
  │             parser confidence (no record of which regex matched)
  │             alternative parses (only the first successful match survives)
  │
  ├─[Stage 1: API Enrichment + Merge]
  │   Produces: merged tmdb_data dict
  │   Destroys: source attribution (which API provided which field)
  │             merge conflicts (when TMDb and OMDb disagree, the losing value is discarded)
  │             API confidence (TMDb search match score not preserved)
  │
  ├─[Stage 2: Explicit Lookup]
  │   Produces: destination path string OR None
  │   Destroys: lookup metadata (which entry matched, were there close misses?)
  │
  ├─[Stage 3: Reference Canon]
  │   Produces: decade OR None
  │   Destroys: canon proximity (was the title close to a canon entry?)
  │
  ├─[Stage 4-5: Satellite Routing]
  │   Produces: category name OR None
  │   Destroys: ALL intermediate evidence:
  │     - which categories were tested
  │     - which gates passed for each category
  │     - which gates failed for each category
  │     - which gates were untestable (data absent vs data contradictory)
  │     - the nearest-match category and its evidence profile
  │     - director match details, keyword signal hits
  │
  ├─[Stage 6-7: User Tag Recovery + Core Director Check]
  │   Produces: tier + decade OR None
  │   Destroys: tag parsing failures, director matching confidence
  │
  ├─[Stage 8: Popcorn Check]
  │   Produces: reason code OR None
  │   Destroys: individual signal states (popularity value, vote count)
  │             threshold distances (popularity=6.8 vs threshold=7.0)
  │
  └─[Stage 9: Unsorted]
      Produces: reason code (unsorted_no_match, unsorted_no_director, etc.)
      Destroys: everything above — conflates data problems, taxonomy gaps,
                and genuine non-matches into a single label
```

The largest information loss is at Stages 4-5 (Satellite routing), where the entire evidence profile for every category tested is discarded. The second largest is at Stage 1 (API merge), where source attribution and merge conflicts are lost.

---

## Three Missing Capabilities

The theoretical frameworks (THEORETICAL_GROUNDING §8-§12) converge on three capabilities the system lacks. Together they transform the pipeline from a one-shot classifier into an evidence accumulator that feeds the recursive curation model.

### A. Evidence Trails (Per-Film)

**Problem:** When a film fails to classify, the system records a reason code and nothing else. The curator cannot determine why the film failed without reading the source code.

**What it should produce:** Every routing stage produces an evidence record, not just a verdict. The record preserves what was tested, what matched, what failed, and what couldn't be evaluated (THEORETICAL_GROUNDING §9: Dempster-Shafer distinction between absent and negative evidence).

**Per-film evidence trail includes:**
- Data readiness level (R0/R1/R2/R3) and which fields are present/absent
- For each category considered: which gates passed, which failed, which were untestable
- The nearest-match category and what evidence would complete the match
- Confidence vector across all categories (not just the winning one)
- Source attribution: which API provided which field

**What this enables:** The curator sees: "This film almost matched Indie Cinema (country=FR pass, decade=1970s pass, genre gate untestable due to absent data; suggest enriching genres)." Actionable without reading source code.

### B. Failure Cohort Analysis (Per-Run)

**Problem:** The pipeline classifies films individually and reports individually. When 44 films fail for the same structural reason, this is invisible — the staging report lists 44 separate entries with the same reason code.

**What it should produce:** After all films are classified, analyse accumulated evidence trails to detect population-level patterns (THEORETICAL_GROUNDING §10: stigmergy — individual failures are noise, cohort failures are signal).

**Cohort analysis includes:**
- Group Unsorted films by failure pattern (which gate failed, what data was present)
- Name the pattern: "genre-data-absent cohort (44 films): country+decade present, genres=[]"
- Identify the binding constraint: "These films would classify if genres were available"
- Distinguish data cohorts from taxonomy cohorts: "These 8 HU films have full data but no rule matches Hungary"

**What this enables:** The curator sees three named problems instead of 44 anonymous failures.

### C. Hypothesis Generation (Per-Cycle)

**Problem:** Even when the curator diagnoses a failure pattern, the remedy must be invented by the human. The system never proposes its own improvements.

**What it should produce:** When a cohort failure is detected, generate a hypothesis about what rule change would resolve it. Present to curator for validation (THEORETICAL_GROUNDING §8: double-loop learning — question governing variables, not just instances).

**Hypothesis generation includes:**
- "HYPOTHESIS: Add 'dennis hopper' to American New Hollywood directors. EVIDENCE: 3 Hopper films unsorted, all US/1970s. CONFIDENCE: high."
- "HYPOTHESIS: Genre gate too strict for R2b population. EVIDENCE: 44 films fail genre gate with country+decade present but genres=[]. CONFIDENCE: medium."
- "HYPOTHESIS: Missing category for Hungarian arthouse. EVIDENCE: 5 HU films with R3 data, no category covers HU in 1970s-1980s. CONFIDENCE: low (may not meet density threshold)."

**What this enables:** The manual patch cycle (Issues #14-#34) becomes system-assisted. The system generates the diagnosis and proposes the fix. The curator validates or rejects.

---

## The New Information Contract

The five-stage recursive lifecycle (RECURSIVE_CURATION_MODEL.md) remains correct. What changes is the information contract between stages.

### Current contract

```
Cluster produces:   sorting_manifest.csv    (final verdicts)
                    staging_report.txt      (human-readable Unsorted list)
                    review_queue.csv        (low-confidence + unsorted-with-data)

Refine consumes:    sorting_manifest.csv    (to detect regressions via reaudit.py)
                    staging_report.txt      (human reads and manually diagnoses)
```

The problem: Cluster outputs *verdicts*, not *evidence*. Refine has nothing to work with except the verdict. The curator re-derives evidence by reading code.

### Required contract

```
Cluster produces:   sorting_manifest.csv    (verdicts — unchanged)
                    evidence_trails.csv     (per-film evidence profiles — NEW)
                    failure_cohorts.json    (population-level failure patterns — NEW)
                    hypotheses.md           (proposed rule changes with evidence — NEW)

Refine consumes:    evidence_trails.csv     (what matched, what didn't, what's missing)
                    failure_cohorts.json    (named failure populations with remediations)
                    hypotheses.md           (proposed improvements for curator review)
```

### Impact on the curation loop

The four curator actions (Accept, Override, Enrich, Defer) remain the same. What changes is the quality of information:

| Curator action | Currently sees | Would see |
|---|---|---|
| **Accept** | "This film is Giallo (confidence 0.7)" | "Giallo: country=IT pass, decade=1970s pass, genre=Horror pass, director=Argento pass. All gates passed." |
| **Override** | "This film is Unsorted (no match)" | "Nearest: Indie Cinema (FR + 1970s pass, genre untestable). Override to Indie Cinema? Or enrich genres first?" |
| **Enrich** | "This film needs data" | "Genre is the binding constraint. With genres, this film would likely route to Indie Cinema (2/3 gates pass)." |
| **Defer** | "This film is uncertain" | "Conflicting evidence: near-miss Giallo (IT + 1970s) AND near-miss European Sexploitation (IT + erotica keyword). Needs human judgment." |

---

## Integration Exploration: How It Attaches to Existing Code

### The pipeline shape and the critical design choice

`classify()` (lines 472–777) is a linear waterfall with early exits. Each stage either returns a `ClassificationResult` or falls through. The film never visits all stages — it exits at the first match.

Evidence accumulation needs to visit every stage regardless of match. Two approaches:

**Option 1: Minimal intrusion (keep early returns)**
Record evidence only at the winning stage and stages before it. Stages after the match are never visited, so their evidence is unknown. Cheaper but incomplete — you know the film matched Giallo at Stage 5, but you don't know whether it would also have matched Core at Stage 7.

**Option 2: Full pass (remove early returns) — RECOMMENDED**
Remove early returns. Run every stage, accumulate all evidence, pick the winner by priority order. This is the "blackboard" approach (THEORETICAL_GROUNDING §11). Every stage writes its observation regardless of other stages' results. The priority logic picks the final verdict from the accumulated evidence.

Option 2 is architecturally correct because:
- It produces complete evidence profiles (every category's gate results for every film)
- It enables proper near-miss detection (you can't find the nearest category if you stopped at the first match)
- It enables multi-match detection (films that genuinely belong in multiple categories — the genre overlap described in Issue #32 Part 3)
- The priority ordering (Rule 2, CLAUDE.md) is preserved — it just happens at the end instead of inline

Option 2 requires restructuring `classify()` from:
```python
# Current: waterfall with early returns
if lookup_match:
    return ClassificationResult(...)
if reference_match:
    return ClassificationResult(...)
if satellite_match:
    return ClassificationResult(...)
...
```

To:
```python
# Proposed: full pass with accumulated evidence
evidence = EvidenceTrail()
evidence.record_lookup(lookup_result)
evidence.record_reference(reference_result)
evidence.record_satellite(satellite_result)
evidence.record_core(core_result)
evidence.record_popcorn(popcorn_result)
# Pick winner by priority
verdict = evidence.resolve_by_priority()
return ClassificationResult(..., evidence_trail=evidence)
```

### The satellite bottleneck

`satellite.classify()` in `lib/satellite.py` returns `Optional[str]` — just a category name. This is the single biggest information bottleneck. The satellite classifier tests ~17 categories with ~5 gates each — approximately 85 gate evaluations, all discarded.

The return type needs to become a rich evidence object:

```python
@dataclass
class SatelliteEvidence:
    matched_category: Optional[str]
    per_category: Dict[str, CategoryEvidence]  # All 17 categories tested

@dataclass
class CategoryEvidence:
    decade_gate: GateResult      # pass/fail/untestable
    director_gate: GateResult    # pass (which director) / fail / untestable (no director data)
    country_gate: GateResult     # pass / fail / untestable (no country data)
    genre_gate: GateResult       # pass / fail / untestable (no genre data)
    keyword_gate: GateResult     # pass (which keyword, tier) / fail / not_applicable
```

This is where the Dempster-Shafer three-valued logic (THEORETICAL_GROUNDING §9) becomes concrete: each gate returns `pass` / `fail` / `untestable`, not just `True` / `False`.

**Specific code points where evidence exists but is currently discarded:**
- `satellite.py` ~line 155: `hit, _ = self._keyword_hit(...)` — the `_` throws away which keyword matched and from which source (tmdb_tag vs text_term)
- `satellite.py` ~lines 119-123: `any(self._director_matches(...))` — the `any()` consumes which director matched
- `satellite.py` ~lines 129-134: `country_match` and `genre_match` are computed separately but both discarded when the loop continues
- `classify.py` lines 350-470: `_merge_api_results()` silently picks winners without recording merge conflicts (TMDb says director is X, OMDb says Y)

### Where cohort analysis and hypothesis generation attach

Both operate **post-classification**, reading accumulated evidence trails:

```
classify() → results list (with evidence trails)
    │
    ├─ [NEW] analyze_failure_cohorts(results)
    │       Groups unsorted films by evidence pattern
    │       Output: failure_cohorts.json
    │
    └─ [NEW] generate_hypotheses(cohorts, current_rules)
            Reads cohorts + SATELLITE_ROUTING_RULES
            Proposes: director additions, gate relaxations, new categories
            Output: hypotheses.md
```

**Attachment point:** Between lines ~800 (results list complete) and ~807 (sorting_manifest.csv written) in `classify.py`. Or as separate scripts that read `evidence_trails.csv`.

**Cohort types and their hypothesis patterns:**

| Cohort type | Example | Hypothesis type |
|---|---|---|
| Data gap | 44 films: country+decade pass, genres=[] | "Enrich these films" (Curation Loop: Enrich) |
| Director gap | 3 Hopper films: US/1970s, no director match | "Add director to category" (most common #14-#34 fix) |
| Taxonomy gap | 8 HU films: R3 data, no rule covers HU | "Add new category or extend existing" (Domain Grounding check needed) |
| Gate design gap | 12 films: near-miss on 1 gate per category | "Relax gate for this category" (e.g., Issue #34 genre gate) |

### What already exists that helps

| Existing feature | What it provides | How it relates |
|---|---|---|
| `ClassificationResult.data_readiness` (R0–R3) | Data population distinction | Seed of evidence trail — already distinguishes data populations |
| `ClassificationResult.reason` (12 codes) | Which stage matched | Coarse evidence trail — captures the winning stage |
| `self.stats` (defaultdict(int)) | Aggregate counts per reason | Primitive cohort analysis — counts but not populations |
| `review_queue.csv` | Low-confidence + enriched-unsorted | Primitive hypothesis output ("these films need review") |
| `CATEGORY_CERTAINTY_TIERS` | Gate count per category | Primitive confidence model — how many independent gates each category has |

### What doesn't exist

1. No per-film gate-by-gate evidence record
2. No distinction between "gate failed" and "gate untestable" anywhere in the code
3. No cohort grouping beyond reason codes
4. No hypothesis generation of any kind
5. `satellite.classify()` returns only a string — the single biggest bottleneck

---

## Implementation Stages

### Stage 1: Evidence-producing satellite classifier

Refactor `satellite.classify()` to return `SatelliteEvidence` instead of `Optional[str]`. Each gate evaluation records pass/fail/untestable with the specific values tested. The matched category is still extracted for backward compatibility — callers that only need the category name can use `evidence.matched_category`.

**Files:** `lib/satellite.py` (primary), `lib/constants.py` (add `GateResult` enum or dataclass)
**Tests:** All existing satellite tests must pass with the new return type. Add tests for three-valued gate logic (especially `genres=[]` → untestable, not fail).
**Risk:** Medium — changes a core return type used by classify.py.

### Stage 2: Full-pass classify pipeline

Restructure `classify()` to run all stages and accumulate evidence, then pick the winner by priority. The `ClassificationResult` dataclass gains an `evidence_trail` field.

**Files:** `classify.py` (primary), `ClassificationResult` dataclass
**Tests:** All existing classification tests must produce identical results (same tier, destination, confidence for every film). The verdict must not change — only the amount of recorded evidence.
**Risk:** High — restructures the core pipeline method. Requires careful regression testing.
**Invariant:** For every film, `new_pipeline.tier == old_pipeline.tier` and `new_pipeline.destination == old_pipeline.destination`. Evidence is additive, not verdict-altering.

### Stage 3: Evidence trail output

Export `evidence_trails.csv` alongside `sorting_manifest.csv`. One row per film, with columns for each stage's evidence (data readiness, lookup result, reference result, per-category satellite gates, core match, popcorn signals).

**Files:** `classify.py` output section (~lines 807+)
**Format:** CSV with structured columns. For satellite evidence, either flatten to columns (`giallo_decade_gate`, `giallo_director_gate`, ...) or use a JSON column for the full per-category evidence dict.
**Tests:** Output format validation. Evidence trail for known films matches expected gate results.

### Stage 4: Failure cohort analysis

Post-classification pass that groups unsorted films by evidence pattern. Identifies named cohorts with remediation type.

**Files:** New module `lib/cohorts.py` or inline in classify.py
**Input:** List of `ClassificationResult` with evidence trails
**Output:** `failure_cohorts.json` — array of cohort objects, each with pattern description, film list, binding constraint, remediation type
**Tests:** Given a known set of evidence trails, produces expected cohort groupings.

### Stage 5: Hypothesis generation

Reads failure cohorts and current routing rules. Proposes rule changes with evidence and confidence.

**Files:** New module `lib/hypotheses.py` or new script `scripts/generate_hypotheses.py`
**Input:** `failure_cohorts.json` + `SATELLITE_ROUTING_RULES` + `CORE_DIRECTORS` + `SORTING_DATABASE`
**Output:** `hypotheses.md` — human-readable proposals with evidence
**Tests:** Given a known cohort (e.g., 3 Hopper films unsorted, US/1970s), generates expected hypothesis (add Hopper to AmNH directors).

---

## Regression Safety

**Critical invariant:** The evidence architecture is purely additive. No existing classification result should change. The pipeline makes the same decisions — it just records why.

**Test strategy:**
1. Before Stage 2, snapshot current `sorting_manifest.csv` for the full Unsorted corpus
2. After Stage 2, run the same corpus through the full-pass pipeline
3. Diff: every `tier`, `destination`, `confidence`, and `reason` must be identical
4. The only new data is in `evidence_trail` (which didn't exist before)

**If any verdict changes:** The full-pass restructuring has a priority ordering bug. Fix before proceeding to Stages 3-5.

---

## Cross-References

| Reference | Relevance |
|---|---|
| `docs/architecture/EVIDENCE_ARCHITECTURE.md` | Architecture document — diagnosis + three capabilities + new information contract |
| `docs/theory/THEORETICAL_GROUNDING.md` §8 | Double-loop learning (Argyris) — single-loop vs double-loop |
| `docs/theory/THEORETICAL_GROUNDING.md` §9 | Dempster-Shafer evidence theory — absent vs negative evidence |
| `docs/theory/THEORETICAL_GROUNDING.md` §10 | Stigmergy — individual failures are noise, cohort failures are signal |
| `docs/theory/THEORETICAL_GROUNDING.md` §11 | Blackboard architecture — shared workspace vs pipeline |
| `docs/theory/THEORETICAL_GROUNDING.md` §12 | Requisite variety (Ashby) — controller variety must match system variety |
| `docs/architecture/RECURSIVE_CURATION_MODEL.md` | The lifecycle this issue completes (Define → Cluster → Refine → Retain → Reinforce) |
| `docs/theory/REFINEMENT_AND_EMERGENCE.md` §4a | Lifecycle stages 3-5 — the stages that currently lack information inputs |
| `docs/theory/MARGINS_AND_TEXTURE.md` §8 | Positive-space vs negative-space categories — evidence architecture applies differently |
| `issues/032-pipeline-gate-architecture-diagnosis.md` | Pipeline gate inventory + R/P split violations + binding constraints |
| `issues/034-r2b-genre-gate-blocks-director-routable-films.md` | The specific instance that triggered this diagnosis |
| `classify.py` lines 472-777 | The pipeline to restructure (Stage 2) |
| `lib/satellite.py` | The satellite classifier to make evidence-producing (Stage 1) |
| `lib/constants.py` | Data structures (GateResult, SatelliteEvidence) to add |
