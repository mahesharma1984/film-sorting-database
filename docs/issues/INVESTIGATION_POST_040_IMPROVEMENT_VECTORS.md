# Investigation: Post-Issue #40 — What's Actually Left

**Type:** Category 0 — Theory Problem (§0.1 Work Router)
**Date:** 2026-03-04
**Status:** Complete → Curation loop action, not engineering action
**Depends on:** Issue #40 (Two-Signal Satellite Routing) — implemented
**Precursor:** `INVESTIGATION_TWO_SIGNAL_ARCHITECTURE.md`

---

## §1 Problem Statement

Issue #40 implemented the two-signal classification architecture. The system routes 12 of 361 queue films (3.3%). This investigation asked: what are the highest-leverage improvements?

**Key finding:** The problems are not new. Every improvement vector identified traces back to issues already documented in the project history. The remaining work is primarily **curatorial** (adding SORTING_DATABASE entries for 45 R3 films) and **data enrichment** (Issue #29 text signals), not new engineering.

---

## §2 Prior Work — What's Already Been Diagnosed

This section exists because the initial investigation re-discovered known problems. The Work Router (§0.6 Drift Audit) requires checking whether upstream stages have already addressed an issue.

| "New" Finding | Already Documented In | Existing Tooling |
|---|---|---|
| 106 films with null cache → `unsorted_insufficient_data` | Issue #16 Layer 1 (dirty titles poison API), `UNSORTED_ANALYSIS.md` §1 (TMDb dependency) | `scripts/invalidate_null_cache.py`, `scripts/unsorted_readiness.py` (shows R1=108) |
| Genre gates too broad (Drama in Blaxploitation, Crime in AmExploitation) | Issue #16 Layer 3 (routing rules too narrow), Issue #29 (keyword routing as alternative signal) | `scripts/analyze_cohorts.py`, title keyword gates already implemented |
| US mainstream films (The Hustler, Omega Man) have no routing path | `UNSORTED_ANALYSIS.md` §Profile 3, `MEMORY.md` "taxonomy gap" section | `scripts/unsorted_readiness.py` (shows R3=45 — all need SORTING_DATABASE entries) |
| Parser failures contaminate titles | Issues #002, #003, #005, bug fixes doc (commit e6efb6c, 5 parser fixes) | 295+ parser tests, extensive regression coverage |
| Indie Cinema missing country codes (PH, NZ, IE) | Issue #20 (Indie Cinema widening), `UNSORTED_ANALYSIS.md` §Recommendation 3 | `scripts/unsorted_readiness.py` shows affected films |

**Lesson:** Before declaring "5 improvement vectors," run `scripts/unsorted_readiness.py` and `scripts/analyze_cohorts.py` first. These tools were built specifically to answer the question "what should we fix next?" and they already segment the queue by actionability.

---

## §3 What's Genuinely New Post-#40

### 3.1 Director lists are no longer decorative

Before Issue #40: 69 directors, decade gate fired before director check → director lists were functionally unused.
After Issue #40: 118 directors, tradition categories check director BEFORE decade → director signal is now functional.

**This means Issue #29 (Text Signal Enrichment) becomes the real next engineering frontier.** It was designed as the third signal layer — keyword-based routing that resolves films where country+decade match but genre doesn't. The spec is already complete with per-category keyword lists, scholarship citations, and implementation checklist.

### 3.2 The R3 population (45 films) is the binding constraint

`unsorted_readiness.py` shows 45 films at R3 — they have full data (director + country + genres) and STILL can't route. This is not an engineering problem. It's a **curatorial backlog**: each film needs a human decision written into `SORTING_DATABASE.md`.

These 45 films represent the ceiling of what the current routing rules can achieve. No amount of parser fixes or cache recovery will classify them — they need curator action.

### 3.3 Cache invalidation cycle confirms plateau

Running the documented curation loop (`invalidate_null_cache.py conservative` → `classify.py` → `unsorted_readiness.py`):

| Metric | Before Cycle | After Cycle | Delta |
|---|---|---|---|
| Classified | 11 | 12 | +1 |
| R3 (full data, no match) | 45 | 45 | 0 |
| R1 (year only, no API data) | 108 | 108 | 0 |
| R0 (no year) | 173 | 173 | 0 |
| TMDb cache nulls | 125 | (re-queried) | 64 hits |
| OMDb cache nulls | 158 | (re-queried) | 57 hits |

The API re-queries recovered data for ~60 films but routing rules still couldn't place them — they moved from R1 to R3 or stayed R1. The `UNSORTED_ANALYSIS.md` conclusion holds: "The 25-30% Unsorted rate is NOT a bug. It's the classifier correctly refusing to guess."

---

## §4 Current State (Post-Cycle)

### Queue Distribution (361 films)

| Reason Code | Count | % |
|---|---|---|
| `unsorted_no_year` | 173 | 48% |
| `unsorted_insufficient_data` | 106 | 29% |
| `unsorted_no_match` | 68 | 19% |
| `tmdb_satellite` | 9 | 2.5% |
| `country_satellite` | 3 | 0.8% |
| `unsorted_no_director` | 2 | 0.6% |

### Data Readiness (349 Unsorted films)

| Level | Count | Action |
|---|---|---|
| R3 | 45 | **Add SORTING_DATABASE entries** (curatorial work) |
| R2b | 12 | Add SORTING_DATABASE entries or routing rules |
| R2a | 11 | API missed — may respond to title cleaning |
| R1 | 108 | Manual enrichment or accept as unidentifiable |
| R0 | 173 | Non-films / supplements — use `park_supplements.py` |

### Cohort Analysis (from `analyze_cohorts.py`)

| Cohort | Type | Films | Confidence | Actionable? |
|---|---|---|---|---|
| Missing country+genres → nearest FNW | data_gap | 6 | MEDIUM | R2a — parser bugs (director/title swapped) |
| Joe Dante → Blaxploitation | director_gap | 2 | MEDIUM | **False lead** — Dante is not Blaxploitation. Nearest-miss algorithm misleading. |
| Missing data → Classic Hollywood | data_gap | 3 | LOW | R2a — API missed |
| Missing data → Brazilian Exploitation | data_gap | 2 | LOW | R2a — parser bugs |

---

## §5 Recommended Next Actions (Priority Order)

### Action 1: Curate R3 Films (45 films → SORTING_DATABASE entries)

This is the highest-leverage action. These films have full data; they just need a human to decide where they go. Per `CURATOR_WORKFLOW.md` Phase B5, each film gets a `SORTING_DATABASE.md` entry.

See §6 below for draft entries.

### Action 2: Implement Issue #29 (Text Signal Enrichment)

Already fully spec'd (`issues/029-text-signal-enrichment.md`). Adds keyword-based routing as a third signal. Per-category keyword lists with scholarship citations already defined. Implementation checklist ready. This is the actual next engineering issue.

### Action 3: Implement Issue #41 (Measurement Correctness)

Already spec'd (`issues/041-measurement-correctness.md`). Closes the measurement loop: add `classified_reason` to reaudit, expand corpora to 5 categories. Without this, we can't tell if improvements are working.

### Action 4: Park R0 Supplements (173 films)

Run `scripts/park_supplements.py` to identify and separate non-film content (interviews, making-of, bonus features). This doesn't improve classification rate but cleans the queue denominator.

### Action 5 (Deferred): R1 Population (108 films)

These films have a year but no API data. The cache invalidation cycle confirmed most are genuinely obscure or have foreign-language titles that TMDb can't match. Options:
- **Manual enrichment** (`output/manual_enrichment.csv`) for known films
- **Accept as unidentifiable** for genuinely obscure content
- **Future**: Issue #29's text signal layer may help if Wikipedia/Letterboxd data is added later (currently out of scope per Issue #29 spec)

---

## §6 R3 Film Curation — Draft SORTING_DATABASE Entries

These 45 films need curatorial decisions. Draft routing based on director, country, decade, and genre analysis:

*(See companion document or SORTING_DATABASE.md additions)*

---

## §7 What NOT To Do

The initial version of this investigation proposed 5 engineering "vectors" (null cache recovery, genre gate tightening, parser fixes, country code gaps, US mainstream taxonomy gap). Review against the issue history revealed:

1. **Don't write new issue specs for already-documented problems.** Issue #16 already solved dirty title cleaning. Issue #29 already spec'd keyword routing. Issue #20 already widened Indie Cinema.

2. **Don't treat curatorial work as engineering work.** The 45 R3 films need SORTING_DATABASE entries — that's curator judgment, not code changes.

3. **Don't invalidate cache expecting different results.** The cache invalidation cycle is documented in `CURATOR_WORKFLOW.md`. It works for parser/normalization bug fixes. It doesn't help when the underlying titles are genuinely hard to match.

4. **Run existing diagnostic tools before investigating.** `unsorted_readiness.py` and `analyze_cohorts.py` were built to answer "what's blocking classification" — they should be the first step, not the conclusion.

---

## §8 Files Referenced

| File | Role |
|---|---|
| `scripts/unsorted_readiness.py` | Primary diagnostic — segments queue by data readiness |
| `scripts/analyze_cohorts.py` | Cohort analysis — finds systematic routing failures |
| `scripts/invalidate_null_cache.py` | Cache invalidation — forces API re-query |
| `docs/UNSORTED_ANALYSIS.md` | Prior art — February 2026, same findings |
| `issues/016-classification-rate-regression.md` | Prior art — dirty titles, routing rules |
| `issues/029-text-signal-enrichment.md` | Next engineering frontier — keyword routing |
| `issues/041-measurement-correctness.md` | Measurement infrastructure gap |
| `docs/CURATOR_WORKFLOW.md` | Curation loop procedure |
| `output/unsorted_readiness.md` | Current readiness report (regenerated this session) |
| `output/cohorts_report.md` | Current cohort report (regenerated this session) |
