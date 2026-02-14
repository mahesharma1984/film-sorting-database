# Work Router

**Purpose:** Route symptoms to the right documentation and action.

Start here when you have a problem, question, or task. Find your symptom, follow the pointer.

---

## Debugging: Something Is Wrong

### "A film was classified to the wrong tier"

1. Check the manifest `reason` column — what logic produced this classification?
2. If reason = `explicit_lookup` → The film is in `docs/SORTING_DATABASE.md` with that destination. Edit the database entry (human decision).
3. If reason = `core_director` → Check `docs/CORE_DIRECTOR_WHITELIST_FINAL.md`. Is the director actually on the whitelist for that decade?
4. If reason = `reference_canon` → Check `REFERENCE_CANON` in `lib/constants.py`. Is it in the 50-film list?
5. If reason = `satellite_country` → Check `COUNTRY_TO_WAVE` in `lib/constants.py`. Is the decade within the valid range for that country?
6. If reason = `user_tag` → A previous human classification was recovered from the filename path. Override by adding to SORTING_DATABASE.md.

→ See: `docs/DEBUG_RUNBOOK.md` Symptom #1

### "A film went to Unsorted unexpectedly"

1. Check the manifest `reason` column for the reason code:
   - `no_year` → Parser couldn't extract a year. Check filename format. → See `docs/DEBUG_RUNBOOK.md` Symptom #3
   - `no_match` → Film didn't match any tier check. Add it to `docs/SORTING_DATABASE.md`.
   - `no_director` → No director extracted AND no lookup match. Consider adding to SORTING_DATABASE.md.
2. Try parsing the filename manually: check `lib/parser.py` priority chain
3. Try normalizing the title: check `lib/normalization.py` output matches SORTING_DATABASE entry

→ See: `docs/DEBUG_RUNBOOK.md` Symptom #2

### "Parser extracted wrong year or director"

1. Test the specific filename against the parser
2. Check the parser priority order: `(Director, Year)` → parenthetical year → Brazilian year-prefix → Director-Title → bracket year → fallback
3. Is a subtitle being mistaken for a director? Check against `SUBTITLE_KEYWORDS` in `lib/constants.py`

→ See: `docs/DEBUG_RUNBOOK.md` Symptom #3, `issues/003-v02-parser-fixes-language-country-extraction.md`

### "Normalization lookup miss — film should match but doesn't"

1. Normalize both sides manually with `normalize_for_lookup()`
2. Compare: are format signals being stripped on both sides?
3. Check for unicode issues: diacritics, ligatures, special characters
4. The fix is ALWAYS in `lib/normalization.py` — make both sides match, never patch one side

→ See: `docs/DEBUG_RUNBOOK.md` Symptom #4, `issues/002-v01-fails-reasoning-and-precision-audit.md`

### "Classification rate dropped after a change"

1. Compare manifests: `python compare_manifests.py before.csv after.csv`
2. Which films changed? Are the changes correct or regressions?
3. `git log --oneline -10` — what changed recently?
4. If regression: revert the change, investigate root cause

→ See: `docs/DEBUG_RUNBOOK.md` Symptom #5

### "Move script is slow or stuck"

1. Check if source and destination are on the same filesystem
2. Same FS → should use `os.rename()` (instant). If not, the same-FS detection is broken.
3. Different FS → `shutil.copy2()` is expected to be slow for large files
4. Check `PERFORMANCE_ISSUE_REPORT.md` for historical context

→ See: `docs/DEBUG_RUNBOOK.md` Symptom #6

---

## Building: Adding or Changing Things

### "Add a new satellite category"

1. Define the category in `docs/SATELLITE_CATEGORIES.md` (name, cap, decade bounds, criteria)
2. Add the country→category mapping to `COUNTRY_TO_WAVE` in `lib/constants.py`
3. Add tests for the new routing logic
4. Run classifier, verify only expected films route to the new category
5. Update `docs/CORE_DOCUMENTATION_INDEX.md` if needed

→ See: `docs/SATELLITE_CATEGORIES.md`, `docs/theory/MARGINS_AND_TEXTURE.md`

### "Add a Core director"

1. Determine which decade(s) — see `docs/theory/AUTEUR_CRITERIA.md` for criteria
2. Add to `docs/CORE_DIRECTOR_WHITELIST_FINAL.md`
3. Update whitelist parser if format changed
4. Run classifier, verify the director's films now route to Core
5. Check: did any films move OUT of other tiers unexpectedly?

→ See: `docs/CORE_DIRECTOR_WHITELIST_FINAL.md`, `docs/theory/AUTEUR_CRITERIA.md`

### "Add a known film to the database"

1. Edit `docs/SORTING_DATABASE.md` — add `- Title (Year) → Decade/Tier/Subdirectory/`
2. Follow the existing format in the file
3. Run classifier to verify it picks up the new entry
4. No code changes needed — the lookup parser reads the file dynamically

→ See: `docs/SORTING_DATABASE.md`

### "Add a film to the Reference canon"

1. Check if the 50-film cap would be exceeded
2. Add to `REFERENCE_CANON` in `lib/constants.py` as `(normalized_title, year): 'Reference'`
3. Also add to `docs/REFERENCE_CANON_LIST.md` for documentation
4. Run tests, verify classification

→ See: `docs/REFERENCE_CANON_LIST.md`, `lib/constants.py`

### "Change the classification pipeline"

1. Read `REFACTOR_PLAN.md` — understand the current architecture
2. Read `CLAUDE.md § 3` — understand the decision rules (R/P Split, Pattern-First, Failure Gates)
3. Follow the Large Changes procedure in `docs/DEVELOPER_GUIDE.md`
4. Pin baseline before making changes
5. Test depth (target case) then breadth (all cases)

→ See: `REFACTOR_PLAN.md`, `docs/DEVELOPER_GUIDE.md`

---

## Operations: Running the System

### "Classify new films"

```
1. python classify.py <source_directory>
2. Review output/sorting_manifest.csv
3. python move.py --dry-run
4. Review dry-run output
5. python move.py --execute
```

### "Re-classify the entire collection"

```
1. Backup current manifest: cp output/sorting_manifest.csv output/sorting_manifest_backup.csv
2. python classify.py <source_directory>
3. python compare_manifests.py output/sorting_manifest_backup.csv output/sorting_manifest.csv
4. Review all changes
```

### "Set up a new external drive"

→ See: `EXTERNAL_DRIVE_GUIDE.md`

---

## Understanding: New to This Project

**Reading order:**

1. `CLAUDE.md` — Project rules and work modes (5 min)
2. `docs/CORE_DOCUMENTATION_INDEX.md` — Where to find everything (2 min)
3. `REFACTOR_PLAN.md` — How the system works (10 min)
4. `docs/theory/README.md` → Theory essays — Why the system works this way (30 min)
5. `docs/PROJECT_COMPLETE_SUMMARY.md` — Collection stats and outcomes (5 min)
