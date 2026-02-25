# Classification Accuracy — Architecture and Measurement Workflow

**Status:** AUTHORITATIVE
**Last updated:** 2026-02-26
**Related:** `exports/skills/measurement-driven.md`, `exports/skills/certainty-first.md`,
`docs/architecture/EVIDENCE_ARCHITECTURE.md`, `scripts/reaudit.py`

---

## §1 What "Accuracy" Means Here

This system does not have a single accuracy score. That would be misleading for two reasons:

1. **The classification population is not uniform.** Films classified by explicit human curation
   (SORTING_DATABASE.md) are a different population from films routed by heuristic rules. Averaging
   them together inflates the score and hides signal.

2. **Certainty is explicit, not inferred.** The system already assigns confidence levels per
   classification (see `exports/skills/certainty-first.md`). An aggregate accuracy score that ignores
   these levels loses the information that makes the score useful.

The correct measurement design: **two populations, segmented by classification source.**

---

## §2 The Two Populations

### Population A — Lookup-classified (SORTING_DATABASE)

Films routed at Stage 2 via `lookup.lookup(title, year)`.
**Reason code:** `explicit_lookup`
**Trust level:** Human-curated. Confidence = 1.0.
**What to measure:** Lookup integrity — does the system correctly retrieve and apply the human
decision? This should be ~100%. Failures here indicate normalization bugs or DB parse errors,
not classification errors.

### Population B — Pipeline-classified (heuristic routing)

Films that missed Stage 2 and were routed by Stages 3–8.
**Reason codes:** `reference_canon`, `core_director`, `tmdb_satellite`, `country_satellite`,
`keyword_satellite`, `user_tag_recovery`, `popcorn_auto`, `popcorn_cast_popularity`
**Trust level:** Rule-based. Confidence varies by certainty tier (0.3–0.8).
**What to measure:** Pipeline self-consistency — does re-running the classifier on an already-organized
film still route it to the same location? Failures here indicate rule conflicts, data quality gaps,
or taxonomy errors.

**Why self-consistency, not ground truth accuracy?**
We do not have a human-labeled ground truth for the full organized library. Self-consistency is
the measurable proxy: a film the classifier placed correctly AND would still place correctly is
evidence the rule is stable. A film it placed but would now route differently is a signal that
something changed (rule update, better API data, or original misclassification).

---

## §3 Measurement Workflow

### Inputs

| Input | Source | Notes |
|-------|--------|-------|
| Organized library filesystem | `/Volumes/.../Movies/Organized/` | All tier folders, excludes Unsorted |
| Classifier (fresh run) | `classify.py` | Run against each organized film |
| SORTING_DATABASE | `docs/SORTING_DATABASE.md` | Used to determine Population A membership |
| Previous reaudit results | `output/reaudit_report.csv` | For trend comparison |

### Processing (reaudit.py)

For each organized film:

1. **Parse** filename → title, year, director (lib/parser.py)
2. **Re-classify** → destination, confidence, reason (classify.py full pipeline)
3. **Compare** re-classified destination to current physical location
4. **Record** match/discrepancy AND reason code (population tag)

Step 4 currently records reason code only for confirmed films (via the notes field). The gap:
discrepancy films do not record their re-classification reason code, so we cannot attribute
discrepancies to specific pipeline stages.

### Outputs

**`output/reaudit_report.csv`** — per-film results, columns:

| Column | Type | Description |
|--------|------|-------------|
| `filename` | string | Film filename |
| `current_tier` | string | Where the file currently lives |
| `current_category` | string | Current subdirectory/director |
| `current_decade` | string | Current decade folder |
| `classified_tier` | string | Where classifier routes it now |
| `classified_category` | string | Classifier's category |
| `classified_decade` | string | Classifier's decade |
| `classified_reason` | string | **[MISSING — see §5]** Pipeline stage that classified |
| `match` | bool | True if current == classified destination |
| `discrepancy_type` | string | wrong_tier / wrong_category / unroutable / no_data |
| `confidence` | string | high / medium / low |
| `notes` | string | Human-readable summary including reason for confirmed films |

**`output/reaudit_review.md`** — human-readable summary grouped by category, with film-level
tables for discrepancies and recommended actions.

### Derived Accuracy Metrics

Computed from `reaudit_report.csv` after adding `classified_reason`:

```
Lookup integrity     = confirmed[explicit_lookup] / total[explicit_lookup]
Pipeline accuracy    = confirmed[non-lookup]      / total[non-lookup]

Per-stage accuracy:
  reference_canon    = confirmed[reference_canon]          / total[reference_canon]
  core_director      = confirmed[core_director]            / total[core_director]
  tmdb_satellite     = confirmed[tmdb_satellite]           / total[tmdb_satellite]
  country_satellite  = confirmed[country_satellite]        / total[country_satellite]
  user_tag_recovery  = confirmed[user_tag_recovery]        / total[user_tag_recovery]
  popcorn_*          = confirmed[popcorn_*]                / total[popcorn_*]
```

---

## §4 Baseline (Current State, 2026-02-26)

Run after commit `e6efb6c`, 738 organized films:

| Population | Confirmed | Discrepancies | Total | Score |
|---|---|---|---|---|
| **Lookup (Population A)** | 353 | 0 | 353 | **100.0%** |
| **Pipeline (Population B)** | 351 | 34 | 385 | **~91.2%** |
| Combined (current reaudit metric) | 704 | 34 | 738 | 95.4% |

Pipeline population breakdown by reason code (confirmed films):

| Reason | Confirmed | Films% |
|--------|-----------|--------|
| tmdb_satellite | 210 | 59.8% |
| country_satellite | 48 | 13.7% |
| user_tag_recovery | 38 | 10.8% |
| core_director | 24 | 6.8% |
| popcorn_cast_popularity | 21 | 6.0% |
| reference_canon | 10 | 2.8% |

The 34 pipeline discrepancies are unattributed (reason codes not captured for discrepancy films).
Until `classified_reason` is added to the report, discrepancies cannot be segmented by pipeline stage.

**Known discrepancy breakdown by type:**
- 15 unroutable — films in Music Films/2020s, Brazilian Exploitation, etc. where no routing rule covers their decade/country/genre combination. Deliberately placed via SORTING_DATABASE but classifier cannot verify.
- 7 wrong_tier — pipeline placed a film in Satellite that classifier now routes to Core (or vice versa). Usually indicates a SORTING_DATABASE pin is needed.
- 7 wrong_category — film is in one Satellite category but classifier routes to another.
- 5 no_data — API cache has no data for these films; cannot re-classify.

---

## §5 The Implementation Gap

`reaudit_report.csv` does not have a `classified_reason` column. This means:
- We can measure combined accuracy (95.4%) and per-reason accuracy for CONFIRMED films
- We cannot segment discrepancies by which pipeline stage failed
- We cannot track whether tmdb_satellite accuracy vs country_satellite accuracy is changing over time

**What needs to change in `scripts/reaudit.py`:**

1. Add `classified_reason` column to `reaudit_report.csv` — populated from the re-classification
   result regardless of whether the film is confirmed or discrepancy.

2. Add summary section to `reaudit_review.md` that shows the two-population accuracy split:
   ```
   Population A (SORTING_DATABASE): NNN/NNN = 100.0%
   Population B (pipeline):         NNN/NNN = XX.X%
     by stage: tmdb_satellite NNN/NNN | country_satellite NNN/NNN | ...
   ```

3. Store `classified_reason` in the accuracy baseline so trend comparisons are possible:
   ```
   output/accuracy_baseline.json  — {date, commit, lookup_accuracy, pipeline_accuracy, by_stage: {...}}
   ```

See GitHub Issue #36 for implementation spec.

---

## §6 Measurement Cycle

**When to run:** After any change to routing rules, SORTING_DATABASE, or pipeline logic.

**Triggers for investigation:**
- Pipeline accuracy drops > 2% from baseline → check which stage regressed
- Any confirmed film becomes a discrepancy → examine whether rule change was intended
- New discrepancy type appears → may indicate a new systematic failure pattern

**Regression threshold:** For this project at current maturity (59.6% overall classification rate,
large Unsorted backlog), a regression is defined as any drop in pipeline accuracy that is not
explained by intentional rule relaxation or new data. The absolute threshold is less important
than the direction and attribution.

**R/P Split applied to measurement:**
- Running reaudit and producing the CSV = PRECISION (automated, deterministic)
- Interpreting whether a discrepancy is a bug vs expected behavior = REASONING (curator judgment)
- The measurement produces inputs; the curator decides actions (see curation-loop.md §Four Actions)

---

## §7 Relationship to Other Architecture Docs

| Doc | Relationship |
|-----|-------------|
| `EVIDENCE_ARCHITECTURE.md` | Defines per-film evidence trails (Stage 1–3 complete). Accuracy measurement is the per-*run* aggregate of those trails. |
| `RECURSIVE_CURATION_MODEL.md §5` | Defines certainty tiers. Per-stage accuracy maps to certainty tier performance. |
| `exports/skills/measurement-driven.md` | Defines the MDD cycle. Reaudit is the MEASURE BREADTH step in that cycle. |
| `exports/skills/certainty-first.md` | Defines confidence levels. Pipeline accuracy by reason code validates whether tier confidence predictions are calibrated. |
| `docs/DEVELOPER_GUIDE.md` | Before/after manifest comparison is the MEASURE DEPTH step. Reaudit is MEASURE BREADTH. |
