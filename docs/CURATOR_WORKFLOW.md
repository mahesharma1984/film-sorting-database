# Curator Workflow Guide

How to use the film sorting system end-to-end: from raw files to an organised library, and from an organised library back through refinement.

This is the **practical** guide. For **how** the system works, see `docs/architecture/RECURSIVE_CURATION_MODEL.md`. For **why**, see `docs/theory/`.

---

## Two Workflows

The system has two distinct operational workflows. They share tools and data, but serve different purposes:

```
Workflow A — Unsorted → Organised          Workflow B — Organised → Reorganised
─────────────────────────────────          ─────────────────────────────────────
NORMALISE                                  AUDIT (library inventory)
    │                                           │
CLASSIFY (Unsorted queue)                  REAUDIT (discrepancy check)
    │                                           │
AUDIT & DIAGNOSE                           ANALYSE COHORTS
    │                                           │
REVIEW & DECIDE                            FIX RULES (act on hypotheses)
    │                                           │
EXECUTE DECISIONS                          RE-RUN CLASSIFY
    │                                           │
MOVE                                       MOVE (within organised library)
    │                                           │
    └──── both feed back into each other ───────┘
```

**Workflow A** processes the Unsorted queue — it takes raw files and places them in the organised library. Run after adding new films or when the Unsorted queue needs attention.

**Workflow B** improves the organised library — it finds films placed by outdated rules, surfaces cohort patterns, and feeds hypothesis-driven rule improvements back into Workflow A's next run. Run periodically (after every batch of moves, or when routing rules change).

**Where learning happens:** In the gap between Workflow B and the next Workflow A run. Acting on Workflow B's cohort hypotheses (adding directors, raising caps, fixing SORTING_DATABASE entries) changes what the next classify run produces. Films that were Unsorted are now routed. Discrepancies that reaudit flagged are now clean. That is the learning event — the system accumulates new routing knowledge with each cycle. See [§ Where Learning Happens](#where-learning-happens) for the full mechanism.

---

## Workflow A: Unsorted → Organised

Run these phases to process the Unsorted queue and move films into the organised library.

---

## Phase 0: Normalise Filenames

Clean filenames before classification. Dirty filenames cause API lookup failures.

```bash
# Preview what would change (dry-run, safe)
python normalize.py /path/to/unsorted/films

# Review output/rename_manifest.csv — check for false positives

# Apply renames
python normalize.py /path/to/unsorted/films --execute

# See which files are non-film content (supplements, trailers, TV)
python normalize.py /path/to/unsorted/films --nonfim-only
```

**Output:** `output/rename_manifest.csv` — one row per file with `original_filename`, `cleaned_filename`, `change_type`, `notes`.

**When to run:** Before every classification pass, especially after adding new films.

---

## Phase 1: Classify

Run the classification pipeline. This never moves files — it only produces a manifest.

```bash
# Classify all films in the source directory
python classify.py /path/to/unsorted/films

# Offline mode (no API queries — uses cached data only)
python classify.py /path/to/unsorted/films --no-api
```

**Outputs (three files):**

| File | Contents | Use |
|------|----------|-----|
| `output/sorting_manifest.csv` | All films — classified and unsorted | Full pipeline result |
| `output/review_queue.csv` | Films needing curator review | Triage queue |
| `output/staging_report.txt` | Human-readable unsorted summary | Quick scan |

**Key columns in sorting_manifest.csv:**
- `tier` — Core, Reference, Satellite, Popcorn, or Unsorted
- `confidence` — 0.0 to 1.0 (higher = more certain)
- `reason` — why this classification was made
- `data_readiness` — R0, R1, R2, or R3

**Reason codes you'll see:**
- `explicit_lookup` — matched SORTING_DATABASE.md (highest trust)
- `reference_canon` — in the 50-film Reference canon
- `country_satellite` — routed by country+decade+genre
- `core_director` — matched Core director whitelist
- `popcorn` — popularity signals
- `unsorted_no_year` — no year extracted (R0)
- `unsorted_insufficient_data` — year only, no API data (R1)
- `unsorted_no_match` — has data but no rule fits (R2/R3)

---

## Phase 2: Audit & Diagnose

Run diagnostics to understand the current state of both the Unsorted queue and the organised library.

### What's in Unsorted?

```bash
# Group unsorted films by data readiness (most actionable first)
python scripts/unsorted_readiness.py

# Include the no-year films too
python scripts/unsorted_readiness.py --no-year-too

# Also get CSV for spreadsheet analysis
python scripts/unsorted_readiness.py --csv
```

**Output:** `output/unsorted_readiness.md` — films grouped by readiness level:
- **R3** (8 films): Full data, no rule matched → add SORTING_DATABASE entries
- **R2b** (14 films): Director + partial API data → need routing rules
- **R2a** (10 films): Director from filename only → may respond to cache retry
- **R1** (126 films): Year only → need manual enrichment
- **R0** (246 films): No year → mostly non-films, filter out

### Is the organised library correct?

```bash
# Build current library inventory
python audit.py

# Re-classify organised films against current rules
python scripts/reaudit.py

# Write human-readable discrepancy report
python scripts/reaudit.py --review

# Also try live API for films with no cached data
python scripts/reaudit.py --enrich
```

**Outputs:**
- `output/library_audit.csv` — inventory of all organised films
- `output/reaudit_review.md` — discrepancies between current location and current rules

### Are films in the right categories?

```bash
# Score all Satellite categories for tentpoles vs texture
python scripts/rank_category_tentpoles.py --all

# Score a single category
python scripts/rank_category_tentpoles.py "Giallo"

# Detect misrouted films (low category fit)
python scripts/category_fit.py

# Check a specific category with wider threshold
python scripts/category_fit.py --category "Pinku Eiga" --threshold 3
```

**Outputs:**
- `output/tentpole_rankings.md` — per-category scored rankings (Category Core / Reference / Texture)
- Category fit report on stdout — CORE_CANDIDATE, REROUTE, NO_FIT labels

---

## Phase 3: Review & Decide

This is the human part. Read the diagnostic outputs and make decisions.

### Triage the review queue

Open `output/review_queue.csv`. For each film, decide one of four actions:

| Action | When to use | What it does |
|--------|-------------|--------------|
| **accept** | Classification is correct | Confirms placement, available for move |
| **override** | Classification is wrong, you know the correct one | Stages a SORTING_DATABASE entry |
| **enrich** | Missing data, you can supply director/country | Adds to manual enrichment for next run |
| **defer** | Uncertain, needs research | Parks for next cycle |

### Create the decisions file

Create `output/curation_decisions.csv` with your decisions:

```csv
filename,action,destination,director,country,notes
"Princess Yang Kwei Fei (1955).mkv",override,"Core/1950s/Kenji Mizoguchi/","","","Mizoguchi is Core"
"A Fêmea do Mar (1980).mp4",enrich,"","Fernando Lopes","PT","Found director on IMDb"
"Unknown Film (1973).mkv",defer,"","","","Need to research"
"Braindead (1992).mkv",override,"Satellite/Indie Cinema/1990s/","","","Peter Jackson early horror"
```

**Rules:**
- `accept`: leave destination, director, country empty (uses existing classification)
- `override`: fill in the correct destination path
- `enrich`: fill in director and/or country (2-letter ISO code)
- `defer`: leave everything empty

### Prefer enrich over override

If providing a missing director name would let the routing rules classify correctly, use **enrich** (systemic fix — helps all films by that director) rather than **override** (point fix — helps only this film).

---

## Phase 4: Execute Decisions

```bash
# Preview what curate.py would do (dry-run, safe)
python scripts/curate.py

# Apply the decisions
python scripts/curate.py --execute
```

**What happens for each action:**
- **accept** → appends to `output/confirmed_films.csv`
- **override** → appends to `output/sorting_database_additions.txt` (staging file — you review and manually add to `docs/SORTING_DATABASE.md`)
- **enrich** → appends to `output/manual_enrichment.csv` (automatically picked up by next `classify.py` run)
- **defer** → updates `output/review_queue.csv` with `deferred=true`

### After curate.py: update SORTING_DATABASE

Review `output/sorting_database_additions.txt`. For entries you approve, manually add them to `docs/SORTING_DATABASE.md`:

```
Princess Yang Kwei Fei (1955) → Core/1950s/Kenji Mizoguchi
Braindead (1992) → Satellite/Indie Cinema/1990s
```

**SORTING_DATABASE.md is never written programmatically.** Code reads it; humans edit it.

---

## Phase 5: Move Files

```bash
# Preview moves (dry-run, safe — this is the default)
python move.py --dry-run

# Actually move files
python move.py --execute
```

`move.py` reads `sorting_manifest.csv` (or `confirmed_films.csv` if it exists). It moves classified films to their destination folders. Unsorted films stay where they are.

**After moving:** Run `python audit.py` to update the library inventory.

---

## Phase 6: Iterate (Workflow A)

Workflow A repeats. Each pass picks up new rules and enrichment from the previous cycle:

```bash
# Picks up new manual enrichment + SORTING_DATABASE entries from previous cycle
python classify.py /path/to/unsorted/films

# Then: audit → review → curate → move again
```

**Convergence:** When two consecutive Workflow A cycles produce zero new classifications, the remaining Unsorted population is stable. It needs new data (manual enrichment, better parsers) or new categories (split protocol) to shrink further.

---

## Workflow B: Organised Library Reaudit

Run these phases to check and improve the already-organised library. Workflow B is how the system learns — see [§ Where Learning Happens](#where-learning-happens).

---

## Phase B1: Audit — Build Library Inventory

```bash
# Walk all tier folders and build a complete inventory
python audit.py
```

**Output:** `output/library_audit.csv` — one row per organised film with tier, category, decade, director, filename.

**When to run:** After every batch of moves. Required before B2 and B3.

---

## Phase B2: Reaudit — Detect Discrepancies

Re-classify every organised film against the current rules and compare against its current folder location.

```bash
# Run reaudit (requires fresh library_audit.csv from Phase B1)
python scripts/reaudit.py

# Write human-readable discrepancy report
python scripts/reaudit.py --review

# Also try live API for films with no cached data
python scripts/reaudit.py --enrich
```

**Output:** `output/reaudit_review.md` — discrepancies grouped by type:
- `wrong_tier` — film is in Satellite but current rules say Core, or vice versa
- `wrong_category` — film is in Giallo but current rules say Indie Cinema
- `wrong_decade` — correct tier and category but wrong decade folder
- `unroutable` — rules return no destination for this film

**What causes discrepancies:** Rules have changed since the film was last classified (new directors added, caps raised, SORTING_DATABASE entries added). This is expected and healthy — it means the system learned since the last move.

---

## Phase B3: Analyse Cohorts — Surface Patterns

Convert anonymous discrepancies and Unsorted films into named, actionable cohorts.

```bash
# Analyse unsorted films and generate hypotheses
python scripts/analyze_cohorts.py

# Use a higher minimum cohort size to reduce noise
python scripts/analyze_cohorts.py --min-cohort-size 3
```

**Outputs:**
- `output/cohorts_report.md` — human-readable: one section per cohort with hypothesis and film list
- `output/failure_cohorts.json` — machine-readable: same data for downstream tooling

**Cohort types:**

| Type | What it means | Action |
|------|--------------|--------|
| `cap_exceeded` | All gates pass but category is full | Raise cap in `lib/satellite.py` |
| `director_gap` | R3 data, director not in category list | Add director to `SATELLITE_ROUTING_RULES` in `lib/constants.py` |
| `data_gap` | Missing genres/country blocks routing | Enrich via `manual_enrichment.csv` or relax gate |
| `gate_design_gap` | Film is 1 gate away from routing | Review gate strictness |
| `taxonomy_gap` | Full data, no category fits this country/era | Consider new Satellite category (split protocol) |

**Confidence levels:**
- `HIGH` — 3+ films sharing the same blocking pattern → fix immediately
- `MEDIUM` — 2 films → likely real, worth acting on
- `LOW` — 1 film → may be an outlier, investigate first

---

## Phase B4: Fix Rules — Act on Hypotheses

Read `output/cohorts_report.md`. For each HIGH or MEDIUM confidence cohort, decide whether to act:

### Cap exceeded
```python
# In lib/satellite.py — raise the cap for the blocked category
SATELLITE_CAPS = {
    'Music Films': 35,   # was 20 — raised after 8 cap_exceeded films found
}
```

### Director gap
```python
# In lib/constants.py — add the missing director to the category's directors list
'American New Hollywood': {
    'directors': ['..existing..', 'dennis hopper'],  # add after finding 3-film cohort
}
```

### Data gap (enrich path)
```csv
# In output/manual_enrichment.csv — curator provides missing field
filename,director,country,year
"Fantastic Planet (1973).mkv","René Laloux","FR","1973"
```

### Data gap (gate relaxation path)
If a genre gate blocks routing for R2 films that have country+decade but no genres, consider making the gate advisory for that readiness level. This is a code change in `lib/satellite.py` — gate it carefully (raises false-positive risk).

### Taxonomy gap
A sustained taxonomy gap cohort (5+ films, same country, same decade, HIGH confidence) triggers the split protocol:
1. Research the country's film tradition for that era
2. Verify density + coherence + archival necessity (`docs/architecture/RECURSIVE_CURATION_MODEL.md` §4)
3. Add to `SATELLITE_ROUTING_RULES` in `lib/constants.py`
4. Add SORTING_DATABASE pins for boundary cases

---

## Phase B5: Re-run Classify + Verify

After rule changes, re-run Workflow A and check that the cohort population shrinks:

```bash
# 1. Reclassify Unsorted (picks up new rules)
python classify.py /path/to/unsorted/films

# 2. Check new evidence_trails.csv
python scripts/analyze_cohorts.py

# 3. Did the target cohort shrink?
# Before: "Cap exceeded — Music Films: 8 films (HIGH)"
# After:  cohort should not appear (cap raised, films now route)

# 4. Re-audit organised library
python audit.py && python scripts/reaudit.py --review
```

**Verification criteria:** A rule change is confirmed when:
- The cohort it targeted no longer appears at the same confidence level
- No new unexpected discrepancies appear in reaudit
- Existing tests pass: `pytest tests/ -q`

---

## Phase B6: Move (Organised Library)

When reaudit identifies wrong-tier or wrong-category films, those films need physical moves within the organised library. Currently this is manual — there is no `reorganize.py` equivalent to `move.py`.

**Manual move procedure:**
1. Open `output/reaudit_review.md`
2. For each discrepancy, verify the new destination is correct
3. Move the file at the shell: `mv "current/path/film.mkv" "new/path/film.mkv"`
4. Run `python audit.py` to update the inventory
5. Run `python scripts/reaudit.py` to confirm the discrepancy is resolved

**Future:** A `reorganize.py` script that reads `reaudit_report.csv` and executes moves within the organised library would close this gap.

---

## Where Learning Happens

The recursive curation model (§1 of `RECURSIVE_CURATION_MODEL.md`) describes the system as getting smarter with each pass. Here is precisely where that happens:

### The Feedback Loop

```
Workflow A (classify Unsorted)
    │
    ├── Films route correctly → MOVE
    │
    └── Films stay Unsorted → evidence_trails.csv
                                     │
Workflow B                           ▼
    ├── reaudit.py detects discrepancies
    │
    └── analyze_cohorts.py names the failure pattern
              │
              │   ← THIS IS WHERE LEARNING HAPPENS
              ▼
    Curator acts on HIGH-confidence hypotheses:
    ├── Adds director to routing rules (director_gap cohort)
    ├── Raises cap (cap_exceeded cohort)
    ├── Adds SORTING_DATABASE pin (taxonomy_gap, no rule fits)
    └── Enriches data (data_gap cohort)
              │
              ▼
    Next Workflow A run incorporates the change
    ├── Director-gap films now route correctly
    ├── Cap-blocked films now route correctly
    └── evidence_trails.csv has fewer films in that cohort
              │
              ▼
    Verify: cohort is smaller or gone → learning confirmed
```

### What "Learning" Means Technically

The system does not use machine learning in the statistical sense. Learning is **rule accumulation**:

1. `SORTING_DATABASE.md` grows with each override — explicit lookup fires before all heuristics, so every added entry is permanent, precise knowledge
2. `SATELLITE_ROUTING_RULES` directors lists grow with each director_gap cohort action — each new director makes a whole cohort routable on the next run
3. Category caps are calibrated to actual collection depth — each cap adjustment brings the category's size in line with curatorial intent
4. `manual_enrichment.csv` grows with enrich decisions — each enrichment promotes a film from R1/R2 to R2/R3, making it routable by heuristics

These four accumulators are the system's memory. The cohort analysis makes the gaps visible so the curator can fill them efficiently — highest-leverage changes first (add one director → route 8 films) rather than ad hoc individual fixes.

### Rate of Learning Per Cycle

A single classify → reaudit → analyze → act cycle typically:
- Produces 1–3 HIGH-confidence hypotheses
- Each hypothesis, if acted on, routes 2–10 previously Unsorted films
- Requires ~30 minutes of curator time (reading reports, making decisions)
- Requires ~5 minutes of code/data changes

After 3–5 cycles, the easy gains are captured. The remaining Unsorted population represents genuine taxonomy gaps (countries with no category, films no source can identify) or non-film content. These require either new data sources or new category definitions — both of which are strategic, not tactical, decisions.

---

## Quick Reference: Cache Management

```bash
# Clear null cache entries (forces API re-query on next classify run)
python scripts/invalidate_null_cache.py conservative   # missing both director AND country
python scripts/invalidate_null_cache.py aggressive      # missing director OR country

# When to use:
# - After fixing parser/normalization bugs (titles may now query better)
# - After adding manual enrichment (want fresh API data too)
# - When API was temporarily down during a previous run
```

---

## Quick Reference: All Output Files

| File | Producer | Consumer | Lifecycle |
|------|----------|----------|-----------|
| `output/rename_manifest.csv` | normalize.py | Curator review | Regenerated each run |
| `output/sorting_manifest.csv` | classify.py | move.py, readiness, review | Regenerated each run |
| `output/review_queue.csv` | classify.py | Curator → curate.py | Regenerated each run, updated by curate.py |
| `output/staging_report.txt` | classify.py | Curator | Regenerated each run |
| `output/library_audit.csv` | audit.py | reaudit.py, tentpoles, category_fit | Regenerated on demand |
| `output/reaudit_review.md` | reaudit.py | Curator (Workflow B) | Regenerated on demand |
| `output/unsorted_readiness.md` | unsorted_readiness.py | Curator | Regenerated on demand |
| `output/evidence_trails.csv` | classify.py (shadow pass) | analyze_cohorts.py | Regenerated each classify run |
| `output/cohorts_report.md` | analyze_cohorts.py | Curator (Workflow B) | Regenerated on demand |
| `output/failure_cohorts.json` | analyze_cohorts.py | Curator / tooling | Regenerated on demand |
| `output/tentpole_rankings.md` | rank_category_tentpoles.py | Curator | Regenerated on demand |
| `output/curation_decisions.csv` | **Curator** (manual) | curate.py | Created by curator per cycle |
| `output/confirmed_films.csv` | curate.py | move.py | Appended each curate run |
| `output/sorting_database_additions.txt` | curate.py | Curator → SORTING_DATABASE.md | Appended each curate run |
| `output/manual_enrichment.csv` | curate.py | classify.py (next run) | Appended each curate run |
| `output/tmdb_cache.json` | classify.py | classify.py (persistent) | Grows over time |
| `output/omdb_cache.json` | classify.py | classify.py (persistent) | Grows over time |
| `docs/SORTING_DATABASE.md` | **Curator** (manual) | classify.py (lookup) | Human-curated, never programmatic |

---

## Troubleshooting

### "Classification rate is 0%"
You're looking at `sorting_manifest.csv` which only contains the Unsorted queue. Run `python audit.py` and check `library_audit.csv` for the full library state.

### "Film X should be in Category Y but it's Unsorted"
Check `output/unsorted_readiness.md` for that film's data readiness:
- **R3**: Add a SORTING_DATABASE.md entry (immediate fix)
- **R2**: Check if director/country is missing — enrich via `manual_enrichment.csv`
- **R1**: API returned nothing — try `invalidate_null_cache.py conservative` then re-run classify
- **R0**: No year in filename — fix filename or add to manual enrichment

### "Film X is in the wrong category"
Two options:
1. **Override**: Add a SORTING_DATABASE.md entry pinning it to the correct destination (point fix)
2. **Enrich**: If the routing rules WOULD classify it correctly with better data, add director/country to `manual_enrichment.csv` (systemic fix — preferred)

### "A whole cluster of films are going to Indie Cinema but shouldn't be"
Run `python scripts/category_fit.py --category "Indie Cinema"`. If you see a cluster from the same country/decade, it may signal a missing Satellite category. See the split protocol in `docs/architecture/RECURSIVE_CURATION_MODEL.md` §4.

### "I see unsorted films but don't know what to fix first"
Run `python scripts/analyze_cohorts.py`. Read `output/cohorts_report.md`. Start with the HIGH-confidence cohorts — these are the highest-leverage changes: one director addition may route 3–8 films at once. Ignore LOW-confidence single-film cohorts until HIGH and MEDIUM are resolved.

### "Reaudit shows discrepancies but cohorts report looks clean"
The cohort analysis runs on the Unsorted queue (from `evidence_trails.csv`), not on discrepancies in the organised library. Reaudit discrepancies are wrong-location films already in the library — these require physical moves (Phase B6), not rule changes. Check `output/reaudit_review.md` directly for the discrepancy details.
