# Curator Workflow Guide

How to use the film sorting system end-to-end: from raw files to an organised library, and from an organised library back through refinement.

This is the **practical** guide. For **how** the system works, see `docs/architecture/RECURSIVE_CURATION_MODEL.md`. For **why**, see `docs/theory/`.

---

## The Cycle

Every pass through the library follows the same six phases:

```
NORMALISE → CLASSIFY → AUDIT → REVIEW → CURATE → MOVE
    ↑                                                │
    └────────────────────────────────────────────────┘
```

Each phase produces outputs that feed the next. The cycle repeats — each pass improves data quality and classification accuracy.

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

## Phase 6: Iterate

The cycle repeats. Each pass improves the system:

```bash
# 1. Reclassify (picks up new manual enrichment + SORTING_DATABASE entries)
python classify.py /path/to/unsorted/films

# 2. Re-audit the organised library against updated rules
python audit.py && python scripts/reaudit.py --review

# 3. Check unsorted — should be smaller now
python scripts/unsorted_readiness.py

# 4. Review, curate, move again
```

**Convergence:** When two consecutive cycles produce zero changes (no new classifications, no new discrepancies), the remaining Unsorted population is stable. It needs new data (manual enrichment, better parsers) or new categories (split protocol) to make progress.

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
| `output/reaudit_review.md` | reaudit.py | Curator | Regenerated on demand |
| `output/unsorted_readiness.md` | unsorted_readiness.py | Curator | Regenerated on demand |
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
