# Issue #41: Measurement Correctness — Closing the Three-Layer Validation Loop

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P2-High |
| Date Opened | 2026-03-04 |
| Component | Audit / Corpus / Satellite |
| Change Type | Feature + Data |
| Estimated Effort | Phase 1: ~1 hour. Phase 2: ~2 hours. Phase 3: 1-2 days per category. |
| Blocked By | None — all phases independently executable |
| Blocks | Accurate per-stage accuracy trend tracking |
| Supersedes | None. Subsumes the specific implementation gap described in GitHub #37. Depends on corpus infrastructure from GitHub #38/#39. |

---

## 1. Manager Summary

**Problem:** The classification pipeline cannot correctly measure its own accuracy. Three root causes compound each other: (1) the reaudit script conflates human-curated films and algorithmic classifications into a single score, hiding the true pipeline accuracy; (2) the corpus layer — which provides the only external standard for correctness — covers just 2 of 796 organised films (0.25%); and (3) the cohort analysis that diagnoses routing failures was generated pre-Phase 2 and contains systematically wrong failure attributions for tradition categories.

**Impact if unfixed:** The system can tell you 745/796 films are "confirmed" but cannot tell you which pipeline stage is responsible for the 51 discrepancies, whether per-stage accuracy is improving or regressing over time, or whether the organised library agrees with published scholarship for any category other than Giallo. Phase 2 (Issue #40) improved director routing correctness but this is unmeasured — there's no mechanism to quantify the improvement.

**Risk if fixed wrong:** Phase 2 (none — cohort regeneration is read-only). Phase 3 (low — adding `classified_reason` to reaudit is additive, no schema breaking). Phase 4 (low — corpus entries don't affect routing unless the film is actually misclassified).

**Estimated effort:** Phase 2 is ~30 lines of code in one script. Phases 1 and 3 are data work (run commands, review output, add scholarship citations). Phase 4 is the highest effort but independently valuable per category.

---

## 2. Evidence

### Observation

The investigation (2026-03-04) traced the full measurement chain using the work router and RAG query against `docs/architecture/VALIDATION_ARCHITECTURE.md`, `docs/CURATOR_WORKFLOW.md`, and live tool outputs.

Three distinct measurement gaps were identified:

**Gap 1 — Conflated accuracy score.** `reaudit_review.md` reports a single combined score:
```
Confirmed: 745 / 796 = 93.6%
```
But 93.6% includes SORTING_DATABASE films (Population A, trivially 100% consistent) and heuristically-routed films (Population C, ~91% accurate) pooled together. The combined score overstates pipeline accuracy. The 51 discrepancies have no `classified_reason` column — it's unknown whether they failed at Satellite routing, Core check, or something else.

**Gap 2 — Circular corpus measurement.** `reaudit --corpus` output:
```
In corpus + correct folder:    2 / 796
In corpus + WRONG folder:      0
Not in corpus (no verdict):    794
```
The system measures self-consistency (does the classifier agree with its past decisions?), not correctness. Two films have an external scholarly verdict. All others are circular. A Spanish film in Giallo, and re-running the classifier producing the same result, registers as "confirmed" — not as "wrong."

**Gap 3 — Stale cohort analysis.** `output/cohorts_report.md` was generated 2026-02-25 — before Phase 2 (Issue #40, committed 2026-03-04). Before Phase 2, the decade gate fired before the director check for tradition categories. This caused tradition films where the director *would have* matched (Abel Ferrara, Sammo Hung) to show `director=not_applicable` in their evidence trails instead of `director=pass`. `analyze_cohorts.py` reads evidence trails — it was attributing these films to `data_gap` cohorts when they belonged in `director_gap` cohorts or had no gap at all.

### Data — Concrete evidence trail comparison

**New Rose Hotel (1998, Abel Ferrara) — evidence trail post-Phase 2:**
```
american_exploitation: decade=not_applicable  director=PASS  → routed correctly
```
`decade=not_applicable` is the Phase 2 signature: director passed first, decade gate never evaluated. Pre-Phase 2 this would have been `decade=fail, director=not_applicable` — cohort analysis would have logged this film as `gate_design_gap` for American Exploitation (stuck on decade gate) rather than recognising the director as the routing mechanism.

**Matinee (1993, Joe Dante) — evidence trail:**
```
blaxploitation: decade=pass  country=pass  genre=pass  director=fail  → nearest miss
```
Cohort analysis correctly identifies this as `director_gap` for Blaxploitation. But without an external standard (corpus), there's no way to know whether Joe Dante films *should* route to Blaxploitation or are correctly Unsorted.

**Reaudit discrepancy types (post-Phase 2):**

| Type | Count | Issue |
|---|---|---|
| unroutable | 24 | Films placed via SORTING_DATABASE where classifier can't verify — structural |
| wrong_category | 11 | 5 are Popcorn subfolder mismatches (pre-existing), 3 are pre-existing, 3 are Phase 2 impacts |
| wrong_tier | 9 | Satellite↔Core conflicts (pre-existing) |
| no_data | 7 | API cache empty for some films (pre-existing) |

Phase 2 net impact on discrepancies: Pasolini (2014) and Welcome to New York (2014) were fixed with SORTING_DATABASE pins (2 discrepancies resolved). The Blackout (1997) [Ferrara] remains as Phase 2 correctly re-classifies it to AmExploit but the file is physically in Indie Cinema — curator action needed.

---

## 3. Root Cause Analysis

### RC-1: `reaudit_report.csv` lacks `classified_reason` for discrepancy films

**Location:** `scripts/reaudit.py` → `_classify_film()` result handling (~line 85)
**Mechanism:** When `_classify_film()` returns a `ClassificationResult`, the script writes `result.tier`, `result.destination`, and `result.confidence` but discards `result.reason`. For confirmed films, the reason appears in the `notes` field (`"Confirmed: explicit_lookup"`). For discrepancy films, `notes` only contains the discrepancy type — no reason code. This makes it impossible to attribute failures to pipeline stages or compute per-stage accuracy.

### RC-2: Corpus layer covers only 2/796 organised films

**Location:** `data/corpora/` — only `giallo.csv` exists (41 entries); only 2 match films currently in the organised library by IMDb ID or normalised title+year
**Mechanism:** The corpus infrastructure (Issue #38) is fully implemented but the data hasn't been populated for any category other than Giallo. Without corpus entries, `reaudit --corpus` cannot distinguish "correctly classified" from "classified consistently but wrongly." The circular measurement problem (VALIDATION_ARCHITECTURE.md §3) is only broken for Giallo.

### RC-3: Cohort analysis was generated pre-Phase 2 with systematically wrong evidence

**Location:** `output/cohorts_report.md` — generated 2026-02-25, pre-Phase 2
**Mechanism:** Before Phase 2, `lib/satellite.py classify()` fired the decade gate before the director check for tradition categories. Films blocked by the decade gate showed `director=not_applicable` in evidence trails. `analyze_cohorts.py` reads evidence trails to compute gate pass rates per category — tradition-category films that would have matched a director (Ferrara → AmExploit, Sammo Hung → HK Action) were logged as either `gate_design_gap` (blocked 1 gate from routing) or absorbed into `data_gap` counts. The 2026-02-25 cohort report has incorrect director gap attribution for all tradition categories.

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| `reaudit.py` → CSV | `scripts/reaudit.py` `_classify_film()` | `output/reaudit_report.csv` | Yes — add `classified_reason` column |
| `reaudit_report.csv` → review | `scripts/reaudit.py` | `output/reaudit_review.md` | Yes — add two-population summary section |
| `reaudit.py` → baseline | `scripts/reaudit.py` | `output/accuracy_baseline.json` (new file) | Yes — new output |
| `evidence_trails.csv` → cohorts | `classify.py` `_gather_evidence()` | `scripts/analyze_cohorts.py` | No code change; data is now accurate post-Phase 2 |
| `data/corpora/` → Stage 2.5 | `lib/corpus.py` | `classify.py` corpus lookup | No code change; adding corpus files expands coverage |

**Gate impact:** Adding `classified_reason` to the reaudit CSV is additive — no existing downstream consumer reads that column (it doesn't exist yet). Adding corpus entries changes `reason=corpus_lookup` for matched films, which will appear in the per-stage breakdown once classified_reason is implemented.

**Downstream consumers of changed outputs:**
- `output/reaudit_review.md` — human-readable; adding a two-population summary section at the top is purely additive
- `output/accuracy_baseline.json` — new file, no existing consumers
- `output/corpus_check_report.csv` — generated by `reaudit --corpus`; no code consumers, curator-facing only

---

## 5. Proposed Fix

Three independent phases. Each is independently valuable. Recommended execution order: Phase 1 first (free, validates Phase 2 impact), then Phase 2 (enables trend tracking), then Phase 3 (breaks circular measurement).

### Phase 1 — Regenerate Cohorts Post-Phase 2 (~1 hour)

Regenerate `output/cohorts_report.md` and `output/failure_cohorts.json` from current evidence trails. This is a read-only operation — no code changes.

#### Execution Order

1. **Re-run classify.py on the Unsorted queue** to regenerate `evidence_trails.csv` with Phase 2 evidence (director gate now correctly evaluated for tradition categories before decade gate):
   - **What to do:** `python classify.py <source_directory>`
   - **Verify:** `evidence_trails.csv` updated timestamp; check a Ferrara or Sammo Hung film shows `american_exploitation_director=pass` or `hong_kong_action_director=pass`

2. **Run cohort analysis** on new evidence trails:
   - **What to do:** `python scripts/analyze_cohorts.py`
   - **Verify:** `output/cohorts_report.md` updated timestamp; `director_gap` cohorts should now accurately reflect tradition-category director gaps; compare count of `director_gap` cohorts before/after

3. **Compare to pre-Phase 2 cohorts** — document which cohorts changed type or disappeared:
   - **What to look for:** Films previously in `gate_design_gap` (blocked by decade gate) should now appear as `director_gap` or have been routed out entirely; `data_gap` cohorts near tradition categories should be smaller

#### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `output/cohorts_report.md` | Regenerated | New cohort analysis with accurate Phase 2 evidence |
| `output/failure_cohorts.json` | Regenerated | Machine-readable version of above |

---

### Phase 2 — Add `classified_reason` to Reaudit (~2 hours)

This is the spec from GitHub issue #37, formalized here.

#### Execution Order

1. **Modify `scripts/reaudit.py`** — capture `result.reason` and add to CSV output:
   - **What to change:** In `_classify_film()` result handling, extract `result.reason` and write to a new `classified_reason` column for ALL films (not just confirmed). Add it between `classified_decade` and `match`.
   - **Verify:** `python scripts/reaudit.py && head -2 output/reaudit_report.csv` — `classified_reason` column present with `explicit_lookup`, `tmdb_satellite`, `unsorted_no_match`, etc.

2. **Add two-population summary to `reaudit_review.md`** — add a header section before the discrepancy detail:
   - **What to add:**
     ```
     ## Accuracy Summary
     Population A — explicit_lookup:   NNN/NNN = 100.0%
     Population C — pipeline heuristics: NNN/NNN = XX.X%
       by stage:
         tmdb_satellite:    NNN/NNN = XX.X%
         country_satellite: NNN/NNN = XX.X%
         core_director:     NNN/NNN = XX.X%
         reference_canon:   NNN/NNN = XX.X%
         popcorn_*:         NNN/NNN = XX.X%
     Combined:              NNN/NNN = XX.X%
     ```
   - Population A = all films where `classified_reason == 'explicit_lookup'`
   - Population C = all other reason codes
   - **Verify:** `reaudit_review.md` has Accuracy Summary section; Population A score = 100.0%; combined score matches old single-number summary

3. **Write `output/accuracy_baseline.json`** — machine-readable baseline for trend tracking:
   - **What to add:** Write JSON with date, commit hash, total films, per-population accuracy, per-stage accuracy. See GitHub issue #37 for schema.
   - **Verify:** `python -c "import json; d=json.load(open('output/accuracy_baseline.json')); print(d['pipeline_accuracy'])"` — should print score ~0.91

#### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `scripts/reaudit.py` | Modify | Add `classified_reason` column; two-population summary; write `accuracy_baseline.json` |
| `output/accuracy_baseline.json` | New | Created on each reaudit run |

---

### Phase 3 — Corpus Expansion for Four High-Priority Categories (1-2 days per category)

Build scholarship-sourced ground truth corpora for the four Tier-1 Satellite categories where published sources were already cited in Phase 1 (Issue #40) director list expansion:

| Category | Priority | Source already cited in #40 | Films in library |
|---|---|---|---|
| Blaxploitation | 1 | Guerrero (1993) *Framing Blackness*; Bogle (2001) *Toms, Coons, Mulattoes* | 9 |
| American Exploitation | 2 | Schaefer (1999) *Bold! Daring! Shocking! True!*; McCarthy & Flynn (1975) *Kings of the Bs* | 36 |
| HK Action | 3 | Teo (1997) *Hong Kong Cinema*; Hunt (2003) *Kung Fu Cult Masters* | ~20 |
| Brazilian Exploitation | 4 | Johnson (1987) *The Film Industry in Brazil*; Ramos (1987) *Cinema Brasileiro* | 40 |

Giallo already has 41 entries. These four categories extend external validation to the five highest-certainty Satellite categories.

#### Execution Order (per category)

1. **Audit the category folder** — detect anomalies before building corpus:
   - **What to do:** `python scripts/build_corpus.py --audit "Blaxploitation"`
   - **Verify:** Review HARD anomalies (country/decade gate violations — definite misclassifications); review SOFT flags (director not in list — may be legitimate)

2. **Add confirmed corpus entries** from scholarship:
   - **What to do:** `python scripts/build_corpus.py --add "Shaft" 1971 --category "Blaxploitation"` (interactive — prompts for canonical_tier, source, notes)
   - **Source requirement:** Every entry must cite published scholarship (monograph + page number preferred). No blog posts, IMDb tags, or system-own classifications.
   - **Verify:** `data/corpora/blaxploitation.csv` — entry present with citation

3. **Validate against organised library:**
   - **What to do:** `python scripts/reaudit.py --corpus`
   - **Verify:** `corpus_confirmed` count increases; `corpus_mismatch` count = 0 (if > 0, investigate before adding more)

#### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `data/corpora/blaxploitation.csv` | New | Scholarship-sourced entries |
| `data/corpora/american-exploitation.csv` | New | Scholarship-sourced entries |
| `data/corpora/hong-kong-action.csv` | New | Scholarship-sourced entries |
| `data/corpora/brazilian-exploitation.csv` | New | Scholarship-sourced entries |
| `docs/architecture/VALIDATION_ARCHITECTURE.md` | Update | §3 Current corpora table — add new entries |

---

## 6. Scope Boundaries

**In scope:**
- Regenerating cohort analysis with post-Phase 2 evidence trails (Phase 1)
- Adding `classified_reason` column and two-population summary to reaudit (Phase 2)
- Writing `accuracy_baseline.json` for trend tracking (Phase 2)
- Corpus entries for Blaxploitation, AmExploit, HK Action, BrExploit (Phase 3)

**NOT in scope:**
- Building an integrated dashboard that merges all three measurement layers — useful but separate issue
- Corpus entries for Indie Cinema, Classic Hollywood, Music Films — negative-space categories (no single authoritative source defines "Indie Cinema")
- Corpus entries for movement categories (FNW, AmNH, JNW) — these are already well-served by director-only routing and the Core whitelist
- Rewriting `analyze_cohorts.py` — the script is correct; only the evidence data feeding it was wrong (fixed by Phase 2)
- Implementing Issue #36 (reorganize.py — moving files based on reaudit discrepancies) — different scope

**Deferred to:** Future issue — integrated measurement view combining reaudit_report.csv + corpus_check_report.csv + evidence_trails.csv into a single per-film record.

---

## 7. Measurement Story

### Phase 1 — Cohort regeneration

| Metric | Before | Target | How to Measure |
|---|---|---|---|
| Cohort report freshness | 2026-02-25 (stale) | 2026-03-04+ (post-Phase 2) | file timestamp |
| `director_gap` cohort count | Unknown (pre-Phase 2 wrong) | Accurate count for tradition categories | `cohorts_report.md` |
| Films in `gate_design_gap` near AmExploit | Unknown | Reduced (Phase 2 routes tradition directors) | `cohorts_report.md` |

### Phase 2 — classified_reason

| Metric | Before | Target | How to Measure |
|---|---|---|---|
| Combined accuracy score | 745/796 = 93.6% | Same (no logic changes) | `reaudit_review.md` |
| Population A accuracy (lookup) | Unknown (conflated) | 100.0% | `reaudit_review.md` Accuracy Summary |
| Population C accuracy (pipeline) | Unknown (conflated) | ~91% baseline visible | `reaudit_review.md` Accuracy Summary |
| tmdb_satellite accuracy | Unknown | First measurement establishes baseline | `reaudit_review.md` by-stage table |
| Discrepancies with reason code | 0% (no column) | 100% (all discrepancies attributed) | `reaudit_report.csv` classified_reason |

### Phase 3 — Corpus expansion

| Metric | Before | Target | How to Measure |
|---|---|---|---|
| corpus_confirmed | 2 / 796 (0.25%) | ~50 / 796 (6%+) | `reaudit --corpus` |
| corpus_mismatch | 0 | 0 (no new misclassifications introduced) | `reaudit --corpus` |
| Categories with external standard | 1 (Giallo) | 5 (+ Blaxploitation, AmExploit, HK Action, BrExploit) | `data/corpora/` files |

**Pin baseline before implementing Phase 2:**
```bash
git tag pre-issue-041-phase2
python scripts/reaudit.py > output/pre-041-reaudit.txt
```

---

## 8. Validation Sequence

### Phase 1
```bash
# 1. Re-run classify to regenerate evidence trails with Phase 2 logic
python classify.py <source_directory>

# 2. Verify Phase 2 evidence is correct for a tradition director film
grep "new rose\|sammo hung" output/evidence_trails.csv \
  | cut -d',' -f83-88   # american_exploitation columns (decade, director, country, genre, keyword, title_kw)
# Expected: director=pass (not not_applicable)

# 3. Regenerate cohorts
python scripts/analyze_cohorts.py

# 4. Inspect output — compare to pre-Phase 2
cat output/cohorts_report.md | grep -A3 "director_gap\|gate_design_gap"
```

### Phase 2
```bash
# 1. Run tests — no regressions
pytest tests/ -v
# Expected: 343 passed, 1 skipped

# 2. Run reaudit — verify new column
python audit.py && python scripts/reaudit.py
head -1 output/reaudit_report.csv | tr ',' '\n' | grep -n "classified_reason"
# Expected: column present

# 3. Verify two-population summary in review
head -30 output/reaudit_review.md | grep -A 10 "Accuracy Summary"
# Expected: Population A = 100.0%, Population C = ~91%

# 4. Verify baseline JSON
python -c "import json; d=json.load(open('output/accuracy_baseline.json')); \
  print('lookup:', d['lookup_accuracy']['score'], \
        'pipeline:', d['pipeline_accuracy']['score'])"
# Expected: lookup: 1.0, pipeline: ~0.91
```

### Phase 3 (per category)
```bash
# 1. Audit category folder
python scripts/build_corpus.py --audit "Blaxploitation"
# Expected: HARD anomaly list, SOFT flag list

# 2. Add entries (repeat for each confirmed film)
python scripts/build_corpus.py --add "Shaft" 1971 --category "Blaxploitation"

# 3. Validate
python scripts/reaudit.py --corpus
# Expected: corpus_confirmed increases; corpus_mismatch = 0

# 4. No regressions
pytest tests/ -v
```

**If any step fails:** Stop. Do not proceed. Report the failure output.

---

## 9. Rollback Plan

**Phase 1** — No rollback needed. Read-only regeneration. Old cohorts report can be restored from git if needed: `git checkout output/cohorts_report.md output/failure_cohorts.json`

**Phase 2** — Detection: reaudit combined score drops unexpectedly, or `classified_reason` column is missing for some rows.
```bash
git revert <phase2-commit-hash>
# Reaudit reverts to old single-score format
```

**Phase 3** — Detection: `corpus_mismatch` count > 0 after adding corpus entries (indicates a film is physically in the wrong category per scholarship).
```bash
# Do NOT rollback — corpus_mismatch is a finding, not an error.
# Investigate each mismatch: is the film wrong, or is the corpus entry wrong?
# See: docs/architecture/VALIDATION_ARCHITECTURE.md §3 anomaly detection
```

**Pre-implementation checkpoint (Phase 2 only):**
```bash
git tag pre-issue-041-phase2
```

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `CLAUDE.md` Rule 7 (Measurement-Driven Development) — "After any pipeline change, follow this cycle: IDENTIFY → DIAGNOSE → FIX → VALIDATE HANDOFFS → MEASURE DEPTH → REBALANCE → MEASURE BREADTH → STABILIZE." Phase 2 (Issue #40) completed FIX and VALIDATE HANDOFFS. This issue completes MEASURE DEPTH (Phase 1 cohorts) and MEASURE BREADTH (Phase 2 reaudit + Phase 3 corpus).
- `CLAUDE.md` Rule 6 (Boundary-Aware Measurement) — Phase 2 (Issue #40) changed routing rules only (Stages 5-8). Measurement should target routing metrics (classification rate, per-stage accuracy), not re-run API enrichment (Stages 1-4).
- `CLAUDE.md` Rule 5 (Constraint Gates) — "Find the binding constraint before optimising. Don't run expensive stages on defective data." The circular measurement problem means expensive manual review is being applied to a corrupted signal — fixing the measurement gives the curator trustworthy data to act on.

**Architecture reference:**
- `docs/architecture/VALIDATION_ARCHITECTURE.md` §3 — The circular measurement problem and corpus solution; §4 — Three-population accuracy model and the classified_reason implementation gap (explicitly named as Issue #36, now GitHub #37); §2 — Failure cohort analysis and the evidence trail → cohort → hypothesis chain.
- `docs/architecture/RECURSIVE_CURATION_MODEL.md` §7 — Curation loop: Accept/Override/Enrich/Defer. Accurate measurement is the precondition for these four actions producing correct outcomes. Wrong measurement → wrong curator decisions → wrong classifications on the next pass.

**Related issues:**
- GitHub #37 — Two-population accuracy reporting: add classified_reason. This spec supersedes and formalises that GitHub issue. Phase 2 here is the implementation.
- GitHub #38 — Layer 1 ground truth corpora (COMPLETE). This issue uses its infrastructure.
- GitHub #39 — Corpus rollout for Giallo + multi-category expansion. Phase 3 here is the multi-category expansion work described in #39.
- Issue #40 (COMPLETE) — Two-Signal Satellite Routing. Phase 1 here validates #40's measurement impact.

---

## Section Checklist

- [x] §1 Manager Summary is readable without code knowledge
- [x] §3 Root causes reference specific files and functions
- [x] §4 ALL downstream consumers are listed
- [x] §5 Execution Order has verify commands for each step
- [x] §5 Files to Modify is complete per phase
- [x] §6 NOT in scope is populated
- [x] §7 Measurement Story has concrete before/after numbers per phase
- [x] §8 Validation Sequence commands are copy-pasteable
- [x] §9 Baseline pinning instruction present (Phase 2)
- [x] §10 Theory grounding exists for each rule invoked
