# Debug Runbook

**Purpose:** Triage → Diagnosis → Action mapping for classification pipeline failures.

---

## Triage Order

1. **Identify the symptom** — What's actually wrong? (Use symptom table below)
2. **Trace to component** — Which module produces the bad output?
3. **Diagnose root cause** — Why is it producing bad output?
4. **Fix upstream** — Fix the root cause, not symptoms downstream

**Key principle:** Fix upstream, not downstream. If classification is wrong because the parser extracted the wrong year, fix the parser — don't add a special case in the classifier.

---

## Symptom Table

| # | Symptom | Quick Check | Likely Cause | Fix |
|---|---|---|---|---|
| 1 | Film classified to wrong tier | Check manifest `reason` column | Decision tree priority order or wrong data in lookup/whitelist | Verify the reason chain: lookup → core → reference → satellite → unsorted |
| 2 | Film went to Unsorted unexpectedly | Check manifest reason code (`no_year`, `no_match`, `no_director`) | Parser failure or missing database entry | Fix parser or add film to SORTING_DATABASE.md |
| 3 | Parser extracted wrong year | Test filename through parser individually | Parenthetical-before-year-prefix priority wrong, or subtitle mistaken for director | Check parser priority chain, verify against SUBTITLE_KEYWORDS |
| 4 | Normalization lookup miss | Normalize both sides, compare character-by-character | Asymmetric format signal stripping or unicode mismatch | Fix in `lib/normalization.py` — ensure identical normalization on both paths |
| 5 | Classification rate dropped | `python compare_manifests.py before.csv after.csv` | Recent code change broke a check or constant | `git log --oneline -10`, bisect to find breaking commit |
| 6 | Move script too slow | Check if source/dest on same filesystem (`os.stat().st_dev`) | Using byte copy instead of rename on same filesystem | Verify same-FS detection in move.py |
| 7 | Satellite cap exceeded | Count per-category in manifest | Too many films routing to one satellite category | Review decade bounds, tighten routing rules, or add films to SORTING_DATABASE.md |
| 8 | Manifest CSV has broken columns | Open in text editor, check quoting | Commas or quotes in filenames breaking CSV | Verify `csv.DictWriter` with proper `quoting=csv.QUOTE_ALL` |

---

## Diagnostic Procedures

### Procedure 1: Wrong Classification Investigation

```
1. What tier did the film land in?
   → Check manifest: filename, tier, reason columns

2. What tier SHOULD it be in?
   → Check docs: SORTING_DATABASE, whitelist, canon, satellite categories

3. Which check produced the wrong result?
   → Trace the reason column:
     - explicit_lookup → wrong entry in SORTING_DATABASE.md (human fix)
     - core_director → director on whitelist when shouldn't be, or wrong decade
     - reference_canon → film in REFERENCE_CANON when shouldn't be
     - satellite_country → country/decade routing mismatch
     - user_tag → previous human tag was wrong
     - no_match → should have matched but didn't (likely normalization)

4. Is it a data issue or a logic issue?
   → Data: fix the source (database, whitelist, canon)
   → Logic: fix the code (parser, normalization, routing rules)
```

### Procedure 2: Parser Failure Investigation

```
1. What filename failed?
   → Record the exact filename string

2. Which parser priority matched (or didn't)?
   Priority order:
   a. (Director, Year) explicit format
   b. Title (Year) parenthetical
   c. Year - Title Brazilian prefix
   d. Director - Title inferred
   e. Title [Year] bracket
   f. Fallback (no year = hard gate failure)

3. Did a lower priority incorrectly match first?
   → The parser tries priorities top-down, first match wins

4. Is a subtitle being mistaken for a director?
   → Check SUBTITLE_KEYWORDS in lib/constants.py
   → "Title - Director's Cut (Year)" should NOT extract "Director's Cut" as director

5. Are format signals interfering?
   → Check FORMAT_SIGNALS in lib/constants.py
   → "Title 4K (2020)" should strip "4K" before parsing
```

### Procedure 3: Normalization Symmetry Check

```
1. Get the title from the SORTING_DATABASE.md entry
2. Get the title from the parsed filename
3. Run both through normalize_for_lookup()
4. Compare character-by-character

If they differ:
   → The normalization is asymmetric
   → Fix in lib/normalization.py (ONE place)
   → Never patch by adding special cases to the lookup or classifier

Common asymmetry causes:
   - Format signals stripped on one side but not the other
   - Diacritics handled differently (NFD decomposition)
   - Punctuation rules differ (apostrophes, hyphens)
```

### Procedure 4: Regression Investigation

```
1. What was the last known good state?
   → Check git log for recent commits
   → Check saved manifests in output/

2. What changed between good and bad?
   → git diff HEAD~N..HEAD -- lib/ classify.py
   → Check if constants changed
   → Check if normalization changed

3. Is the regression universal or case-specific?
   → Run classifier on full test set
   → Compare: how many films changed classification?

4. Can we roll back?
   → Recent: git revert <commit>
   → Older: fix forward using diagnosis
```

---

## Escalation Rules

1. **Hard gate failure** (no year, drive unmounted) → Stop, fix the prerequisite
2. **Data integrity failure** (asymmetric normalization, broken CSV) → Stop everything, fix normalization
3. **Wrong classification** (single film) → Fix data source (database, whitelist, canon)
4. **Classification regression** (multiple films) → Revert change, investigate root cause
5. **Accumulated soft failures** (many films to Unsorted) → Investigate systemic cause (parser or normalization issue)

---

## Recovery

### Re-run Classification (Manifest is Regenerable)
```bash
# The manifest is always regenerable from source files
python classify.py <source_directory>
```

### Restore Previous Manifest
```bash
# If you saved a backup
cp output/sorting_manifest_backup.csv output/sorting_manifest.csv
```

### Rollback Code Change
```bash
# Find the breaking commit
git log --oneline -10

# Revert it
git revert <commit_hash>

# Re-run classifier to verify
python classify.py <source_directory>
```

### Full Clean Re-run
```bash
# Start fresh: scaffold → classify → dry-run → execute
python scaffold.py
python classify.py <source_directory>
python move.py --dry-run
# Review output, then:
python move.py --execute
```
