# Validation Architecture: How the System Knows It's Right

> A classifier that only measures itself against its own rules is testing consistency, not correctness. External standards are the difference between "it does what I told it" and "it does the right thing."

**Type:** Architecture document (HOW the system validates classifications)
**Status:** AUTHORITATIVE
**Consolidates:** `EVIDENCE_ARCHITECTURE.md` + `CLASSIFICATION_ACCURACY.md` + corpus layer (Issue #38)
**Theoretical grounding:** `docs/theory/THEORETICAL_GROUNDING.md` §8-§12
**Depends on:** `RECURSIVE_CURATION_MODEL.md` (the lifecycle this document validates)

---

## 1. The Validation Problem

The classification pipeline routes films through a sequence of stages: explicit lookup → corpus → reference canon → satellite routing → core director → popcorn → unsorted. Each stage tests conditions, returns a name or `None`, and passes the film onward.

Three questions arise:

1. **Per-film:** Why did this film land here? What was tested, what matched, what was missing?
2. **Per-category:** Does the routing agree with published film scholarship?
3. **Per-run:** How accurate is the pipeline overall? Is it getting better or worse?

These questions correspond to three validation layers, operating at different scales:

| Layer | Scale | Mechanism | Introduced |
|-------|-------|-----------|------------|
| **Evidence trails** | Per-film | Gate-by-gate evidence preservation | Issue #35 |
| **Ground truth corpora** | Per-category | Scholarship-sourced external validation | Issue #38 |
| **Accuracy measurement** | Per-run | Population-segmented reaudit | Issue #36 |

Each layer feeds the next: evidence trails are the raw material, corpora provide the external standard, accuracy measurement aggregates the result.

---

## 2. Layer 1: Evidence Trails (Per-Film)

### The information destruction problem

Before Issue #35, the pipeline was a one-pass funnel. Each stage received a film, tested a condition, returned a name or `None`, and **discarded all intermediate evidence**. When 44 films failed the Satellite genre gate with identical symptoms, the system produced 44 individual `unsorted_no_match` results with no record of what they shared or why they failed.

The largest information loss was at Satellite routing (Stages 4-5), where the evidence profile for every category tested was discarded. The second largest was at API merge (Stage 1), where source attribution and merge conflicts were lost.

### The evidence trail solution

Every film now accumulates an evidence record as it passes through the pipeline. The record preserves what was tested, what matched, what failed, and what could not be evaluated.

**Key distinction (Dempster-Shafer, THEORETICAL_GROUNDING §9):** A gate that fails because the data contradicts the rule (`country=US, expected IT`) is different from a gate that fails because no data exists (`genres=[]`). The evidence system uses three-valued gate logic:

| Gate status | Meaning | Example |
|-------------|---------|---------|
| `pass` | Data present, matches rule | `country=IT` for Giallo |
| `fail` | Data present, contradicts rule | `country=US` for Giallo |
| `untestable` | Data absent, cannot evaluate | `genres=[]` for any category |

**Implementation:**
- `GateResult`, `CategoryEvidence`, `SatelliteEvidence` dataclasses in `lib/constants.py`
- `evidence_classify()` in `lib/satellite.py` — read-only twin of `classify()`, three-valued gate logic
- `_gather_evidence()` shadow pass in `classify.py` — runs all stage logic read-only after the winner is determined
- `evidence_trail` dict on `ClassificationResult` — keys: `data_readiness`, `satellite`, `nearest_miss`, etc.

**Output:** `output/evidence_trails.csv` — flat CSV with ~17 categories × 6 gate columns per film. Feeds `analyze_cohorts.py` for population-level pattern detection.

### Failure cohort analysis

Individual evidence trails are noise. Cohort-level patterns are signal (THEORETICAL_GROUNDING §10: stigmergy).

`scripts/analyze_cohorts.py` groups Unsorted films by shared failure pattern and names the populations:

| Cohort type | What it means | Curator action |
|-------------|--------------|----------------|
| `cap_exceeded` | All gates pass but category is full | Raise cap in `lib/satellite.py` |
| `director_gap` | R3 data, director not in category list | Add director to `SATELLITE_ROUTING_RULES` |
| `data_gap` | Missing genres/country blocks routing | Enrich via `manual_enrichment.csv` |
| `gate_design_gap` | Film is 1 gate away from routing | Review gate strictness |
| `taxonomy_gap` | Full data, no category fits | Consider new Satellite category |

**Hypothesis generation:** Each cohort produces a hypothesis with confidence (HIGH/MEDIUM/LOW). HIGH = 3+ films sharing the same blocking pattern. This converts the manual patch cycle (Issues #14-#34) into system-assisted diagnosis: the system names the problem, the curator validates the fix.

**Outputs:**
- `output/cohorts_report.md` — human-readable, one section per cohort
- `output/failure_cohorts.json` — machine-readable for downstream tooling

*Deep-dive: [THEORETICAL_GROUNDING.md](../theory/THEORETICAL_GROUNDING.md) §8-§12 (Argyris double-loop learning, Dempster-Shafer evidence, stigmergy, blackboard architecture, Ashby's requisite variety).*

---

## 3. Layer 2: Ground Truth Corpora (Per-Category)

### The circular measurement problem

Before Issue #38, the system measured accuracy by re-running the classifier on organised films and comparing the result to the current folder location. This measures **self-consistency** — does the system agree with its own past decisions? — not **correctness** — are those decisions right?

When the classifier places a Spanish film in Giallo (Italian genre cinema), and re-running the classifier produces the same result, self-consistency says "correct." External scholarship says "wrong."

### The corpus solution

Ground truth corpora are per-category CSV files sourced from published film scholarship. Each entry cites a specific scholar's work, not the system's own classifications. This breaks the circularity: the standard exists independently of the classifier.

**Pipeline position:** Stage 2.5 — fires after explicit lookup (SORTING_DATABASE), before all heuristic routing.

```
Stage 2:   Explicit lookup (SORTING_DATABASE.md) — human-curated pins
Stage 2.5: Corpus lookup (data/corpora/*.csv) — scholarship-sourced  ← NEW
Stage 3:   Reference canon — 50-film hardcoded list
Stage 4+:  Heuristic routing — country/decade/genre/director rules
```

**Why this position:** Corpus entries have the same trust level as SORTING_DATABASE entries — they represent authoritative external classification, not algorithmic inference. They fire early and with confidence 1.0.

### Schema

Each corpus file lives at `data/corpora/{category-slug}.csv`:

```csv
title,year,imdb_id,director,country,canonical_tier,source,notes
```

| Field | Purpose |
|-------|---------|
| `title` | Film title (normalized for lookup) |
| `year` | Release year |
| `imdb_id` | IMDb ID (format-proof identifier) |
| `director` | Director name |
| `country` | Primary country code |
| `canonical_tier` | 1 = core canon, 2 = reference, 3 = texture |
| `source` | Citation (e.g., "Koven 2006 p.45") |
| `notes` | Anomalies, co-productions, editorial notes |

### Dual index lookup

`lib/corpus.py` (`CorpusLookup`) uses two indexes:

1. **IMDb ID match** — format-proof, highest confidence. A film's IMDb ID survives title variations, alternative names, and filename formatting differences.
2. **Normalized title + year match** — fallback when IMDb ID is unavailable. Uses `normalize_for_lookup()` for consistency with SORTING_DATABASE.

IMDb ID takes priority. If a film matches by IMDb ID but has a different title in the corpus, the IMDb match wins. This prevents format-related lookup failures.

### Canonical tier

Each corpus entry carries a `canonical_tier` (1-3) that maps to the within-category depth hierarchy:

| Canonical tier | Category depth | Meaning |
|----------------|---------------|---------|
| 1 | Category Core | Defined or transformed the tradition. Must-have exemplars. |
| 2 | Category Reference | Important works that establish what the tradition contains. |
| 3 | Category Texture | Skilled practitioners, interesting experiments, historical completeness. |

This directly feeds tentpole ranking (`scripts/rank_category_tentpoles.py`) as the 7th scoring dimension (0-3 points). Scholarship-confirmed exemplars rank higher than films known only from collection heuristics.

### Anomaly detection

`scripts/build_corpus.py --audit CATEGORY` cross-references films physically in a Satellite category folder against the category's routing rules:

| Anomaly type | Meaning | Action |
|-------------|---------|--------|
| **HARD** | Country or decade violates structural gates | Strong misrouting signal — investigate |
| **SOFT** | Director not in routing list | Weak signal — routing lists are intentionally incomplete |

Example: She Killed in Ecstasy (1971) — physically in Giallo, but country=ES (Spain), not IT (Italy). HARD anomaly. The film may be correctly placed (Jess Franco giallo-adjacent work) but the structural evidence says it's not Italian genre cinema.

### Current corpora

| Category | File | Entries | Sources |
|----------|------|---------|---------|
| Giallo | `data/corpora/giallo.csv` | 41 | Koven (2006), Lucas (2007) |
| Blaxploitation | `data/corpora/blaxploitation.csv` | 9 | Guerrero (1993), Bogle (2001) |
| American Exploitation | `data/corpora/american-exploitation.csv` | 24 | Schaefer (1999), McCarthy & Flynn (1975) |
| Hong Kong Action | `data/corpora/hong-kong-action.csv` | 18 | Teo (1997), Hunt (2003) |
| Brazilian Exploitation | `data/corpora/brazilian-exploitation.csv` | 25 | Johnson (1987), Ramos (1987) |

Additional corpora are built by running `build_corpus.py --audit CATEGORY` to generate a draft, then curating entries with scholarly citations via `build_corpus.py --add TITLE YEAR --category CATEGORY`.

### Graceful degradation

The corpus layer is **optional**. If `data/corpora/` does not exist or is empty, Stage 2.5 is silently skipped. No existing behaviour changes. This allows incremental rollout — one category at a time.

### Corpus validation via reaudit

`scripts/reaudit.py --corpus` adds external standard validation to the reaudit workflow:

| Verdict | Meaning |
|---------|---------|
| `corpus_confirmed` | Film in corpus AND in correct Satellite category folder |
| `corpus_mismatch` | Film in corpus BUT in different category — real misclassification |
| `corpus_unconfirmed` | Film not in corpus — no external verdict available |

Output: `output/corpus_check_report.csv` — enables measuring how well the organised library agrees with published scholarship, not just with itself.

---

## 4. Layer 3: Accuracy Measurement (Per-Run)

### Three populations

Classification accuracy is segmented by source. Aggregating all films into a single score inflates the number and hides signal.

| Population | Source | Reason codes | Trust | Confidence |
|-----------|--------|-------------|-------|------------|
| **A: Lookup** | SORTING_DATABASE.md | `explicit_lookup` | Human-curated | 1.0 |
| **B: Corpus** | data/corpora/*.csv | `corpus_lookup` | Scholarship-sourced | 1.0 |
| **C: Pipeline** | Heuristic routing (Stages 3-8) | `reference_canon`, `core_director`, `tmdb_satellite`, `country_satellite`, etc. | Rule-based | 0.3-0.8 |

**What to measure per population:**

- **Population A (Lookup):** Lookup integrity — does the system correctly retrieve and apply the human decision? Should be ~100%. Failures indicate normalization bugs or DB parse errors, not classification errors.
- **Population B (Corpus):** Corpus integrity — does the system correctly match against the scholarship standard? Should be ~100%. Failures indicate normalization bugs in corpus loading, not classification errors.
- **Population C (Pipeline):** Pipeline accuracy — does re-running the classifier on an organised film still route it to the same location? Failures indicate rule conflicts, data quality gaps, or taxonomy errors. This is where real accuracy work happens.

### Measurement workflow

For each organised film (via `scripts/reaudit.py`):

1. **Parse** filename → title, year, director
2. **Re-classify** → destination, confidence, reason (full pipeline)
3. **Compare** re-classified destination to current physical location
4. **Record** match/discrepancy, reason code, population tag

### Derived metrics

```
Lookup integrity     = confirmed[explicit_lookup] / total[explicit_lookup]
Corpus integrity     = confirmed[corpus_lookup]   / total[corpus_lookup]
Pipeline accuracy    = confirmed[heuristic]       / total[heuristic]

Per-stage accuracy:
  reference_canon    = confirmed[reference_canon]      / total[reference_canon]
  core_director      = confirmed[core_director]        / total[core_director]
  tmdb_satellite     = confirmed[tmdb_satellite]       / total[tmdb_satellite]
  country_satellite  = confirmed[country_satellite]    / total[country_satellite]
  user_tag_recovery  = confirmed[user_tag_recovery]    / total[user_tag_recovery]
  popcorn_*          = confirmed[popcorn_*]            / total[popcorn_*]
```

### Baseline (2026-02-26)

Run after commit `e6efb6c`, 738 organised films:

| Population | Confirmed | Discrepancies | Total | Score |
|---|---|---|---|---|
| **A: Lookup** | 353 | 0 | 353 | **100.0%** |
| **B: Corpus** | — | — | — | *Not yet measured* |
| **C: Pipeline** | 351 | 34 | 385 | **~91.2%** |
| Combined | 704 | 34 | 738 | 95.4% |

Pipeline discrepancy breakdown:
- 15 unroutable — films deliberately placed via SORTING_DATABASE where classifier cannot verify
- 7 wrong_tier — Satellite ↔ Core conflicts
- 7 wrong_category — inter-Satellite routing disagreements
- 5 no_data — API cache empty, cannot re-classify

### Routing contract and baseline clarity (Issue #48)

Under the `legacy` routing contract, Population A (`explicit_lookup`) pre-empts Population C before
signals fire, and Core/Reference routing is active within `integrate_signals()`. This means
combined accuracy metrics mix curated interventions with autonomous routing — the combined score
appears higher than the scholarship pipeline actually performs.

The `scholarship_only` contract isolates Population C:
- Stage 2 (`explicit_lookup`) bypassed — no Population A rows in output
- Core whitelist emission suppressed in `score_director()` — no `director_signal` (Core) rows
- Reference canon emission suppressed in `score_structure()` — no `reference_canon` rows

**Scholarship-only baseline workflow:**
```bash
python classify.py <src> --routing-contract scholarship_only --output output/scholarship_manifest.csv
python scripts/reaudit.py --routing-contract scholarship_only --review
```

The scholarship baseline reflects autonomous pipeline performance on Population C only — the
truthful measure for improving the two-signal system.

### Measurement cycle

**When to run:** After any change to routing rules, SORTING_DATABASE, corpus files, or pipeline logic.

**Triggers for investigation:**
- Pipeline accuracy drops > 2% from baseline → check which stage regressed
- Any confirmed film becomes a discrepancy → examine whether rule change was intended
- Corpus mismatch appears → investigate whether film or corpus entry is wrong
- New discrepancy type appears → may indicate systematic failure pattern

**R/P Split applied to measurement:**
- Running reaudit and producing the CSV = PRECISION (automated, deterministic)
- Interpreting whether a discrepancy is a bug vs expected behaviour = REASONING (curator judgment)
- The measurement produces inputs; the curator decides actions

### Implementation gap

`reaudit_report.csv` does not yet have a `classified_reason` column for discrepancy films. This means:
- We can measure combined accuracy and per-reason accuracy for CONFIRMED films
- We cannot segment discrepancies by which pipeline stage failed
- We cannot track per-stage accuracy trends over time

See Issue #36 for the implementation spec: add `classified_reason` column, two-population summary in `reaudit_review.md`, and `output/accuracy_baseline.json` for trend tracking.

---

## 5. The Information Contract

The five-stage lifecycle (RECURSIVE_CURATION_MODEL §10) depends on each stage producing information the next stage can consume.

### What Cluster produces

```
sorting_manifest.csv      — verdicts (tier, destination, confidence, reason)
evidence_trails.csv       — per-film gate-by-gate evidence profiles
failure_cohorts.json      — population-level failure patterns with hypotheses
corpus_check_report.csv   — per-film corpus confirmed/mismatch/unconfirmed (with --corpus flag)
```

### What Refine consumes

```
evidence_trails.csv       — what matched, what didn't, what's missing per film
failure_cohorts.json      — named failure populations with proposed remediations
corpus_check_report.csv   — external standard agreement/disagreement
reaudit_report.csv        — current-location vs current-rules comparison
```

### Impact on the curation loop

The four curator actions (Accept, Override, Enrich, Defer) remain the same. What changes is the quality of information at each decision point:

| Action | Without validation layers | With validation layers |
|--------|--------------------------|----------------------|
| **Accept** | "This film is Giallo (confidence 0.7)" | "Giallo: country=IT pass, decade=1970s pass, genre=Horror pass, director=Argento pass. Corpus: confirmed (Koven 2006, canonical tier 1)." |
| **Override** | "This film is Unsorted (no match)" | "Nearest: Indie Cinema (FR + 1970s pass, genre untestable). Corpus: not in any corpus. Override or enrich genres first?" |
| **Enrich** | "This film needs data" | "Genre is the binding constraint. With genres, this film would likely route to Indie Cinema (2/3 gates pass)." |
| **Defer** | "This film is uncertain" | "Conflicting evidence: near-miss Giallo (IT + 1970s) AND near-miss European Sexploitation (IT + erotica keyword). Corpus: confirmed Giallo (Lucas 2007, tier 3). Accept corpus classification?" |

Better evidence → better curator decisions → better feedback → better classification on the next pass. This is where the recursion actually closes.

---

## 6. Building New Corpora

### Prerequisites

A category is ready for a corpus when:
1. It exists in `SATELLITE_ROUTING_RULES` with defined routing gates
2. Published film scholarship exists for the movement (Domain Grounding, CLAUDE.md Rule 4)
3. The category has 10+ films in the organised library (enough to validate against)

### Workflow

```bash
# 1. Audit: see what's in the category folder and detect anomalies
python scripts/build_corpus.py --audit "Category Name"

# 2. Review the output: HARD anomalies, SOFT flags, unresolvable films
#    Output: stdout + output/corpus_draft_{category}.csv

# 3. Add confirmed entries one at a time with scholarly citations
python scripts/build_corpus.py --add "Film Title" 1975 --category "Category Name"
#    Interactive: prompts for canonical_tier, source citation, notes

# 4. Validate: re-run reaudit with corpus flag
python scripts/reaudit.py --corpus

# 5. Verify: corpus_confirmed count should match expectations
```

### Citation standards

Every corpus entry must cite published scholarship:
- **Preferred:** Monograph with page number (e.g., "Koven 2006 p.45")
- **Acceptable:** Academic article or edited collection chapter
- **Acceptable:** Film encyclopedia or authoritative filmography
- **Not acceptable:** Blog posts, user-generated lists, IMDb tags, or the system's own classifications

The citation in the `source` field is the entry's claim to authority. Without it, the entry is no different from a SORTING_DATABASE pin — human judgment, not external validation.

---

## Cross-References

- [RECURSIVE_CURATION_MODEL.md](RECURSIVE_CURATION_MODEL.md) — The lifecycle this document validates; §3 (decision tree), §5 (certainty tiers), §7 (curation loop), §10 (five-stage lifecycle)
- [THEORETICAL_GROUNDING.md](../theory/THEORETICAL_GROUNDING.md) — §8-§12 ground the frameworks cited here (Argyris, Dempster-Shafer, stigmergy, blackboard, Ashby)
- [REFINEMENT_AND_EMERGENCE.md](../theory/REFINEMENT_AND_EMERGENCE.md) — §4a (lifecycle stages 3-5); this document specifies the information contract those stages need
- [MARGINS_AND_TEXTURE.md](../theory/MARGINS_AND_TEXTURE.md) — §8 (positive-space vs negative-space); evidence architecture applies differently to each type
- [SATELLITE_DEPTH.md](../theory/SATELLITE_DEPTH.md) — §3-4 (Category Core/Reference/Texture); canonical_tier maps directly to within-category depth
- `lib/corpus.py` — CorpusLookup implementation
- `lib/constants.py` — GateResult, CategoryEvidence, SatelliteEvidence dataclasses
- `scripts/build_corpus.py` — Corpus auditing and entry creation
- `scripts/analyze_cohorts.py` — Failure cohort analysis
- `scripts/reaudit.py` — Accuracy measurement (--corpus flag for corpus validation)
