# Work Router

**Purpose:** Route symptoms to the right documentation and action.

Start here when you have a problem, question, or task. Find your symptom, follow the pointer.

---

## Quick Triage (30 seconds)

```
What are you doing?
│
├── Don't know what's wrong yet / investigating
│   └── Category 0: Investigation & Problem Classification (below)
│
├── Something is broken (known symptom)
│   └── Debugging: Something Is Wrong
│
├── Building or changing something
│   └── Building: Adding or Changing Things
│
├── Running the system
│   └── Operations: Running the System
│
└── New to the project
    └── Understanding: New to This Project
```

---

## Category 0: Investigation & Problem Classification

Use this when you don't know what's wrong yet — or need to classify a problem before deciding how to fix it.

### §0.1 Problem Classification Decision Tree

```
Start here: What kind of problem is this?
│
├── "The system does something, but the LOGIC is wrong"
│   │  (wrong tier priority, wrong category, wrong decade bounds)
│   └── THEORY PROBLEM
│       → Check: Do CLAUDE.md Decision Rules or theory docs define the correct behavior?
│       → Read: CLAUDE.md §3 Rules, docs/theory/*, exports/knowledge-base/
│       → Fix: Update the rule/theory doc first, then align code
│
├── "The system does something, but the HANDOFF between stages is wrong"
│   │  (data lost between stages, wrong format, contract violation)
│   └── ARCHITECTURE PROBLEM
│       → Check: Do stage contracts match actual data flow?
│       → Read: docs/architecture/VALIDATION_ARCHITECTURE.md, docs/architecture/RECURSIVE_CURATION_MODEL.md
│       → Fix: Update the contract, then fix the code
│
├── "A REASONING task is in code, or a PRECISION task went to the wrong place"
│   │  (film title parsed by regex that requires judgment, or vice versa)
│   └── R/P SPLIT PROBLEM
│       → Check: Is the task allocation correct per CLAUDE.md Rule 1?
│       → Read: CLAUDE.md §3 Rule 1, exports/skills/rp-split.md
│       → Fix: Reassign the task to the correct executor
│
└── "The logic and architecture are right, but the CODE doesn't match"
    │  (bug, missing implementation, wrong regex, bad constant)
    └── IMPLEMENTATION PROBLEM
        → Check: Does the code implement what CLAUDE.md / architecture docs specify?
        → Read: The specific lib/ file + its CLAUDE.md rule
        → Fix: Fix the code to match the declared contract
```

**Diagnostic signals:**

| Signal | Likely Classification |
|---|---|
| "The output looks plausible but is wrong" | Theory or R/P Split |
| "Film disappears between stages" | Architecture (handoff) |
| "It worked before, now it doesn't" | Implementation (regression) |
| "Metrics pass but classification is bad" | Theory (wrong metrics) |
| "Works for one film, fails for others" | Architecture (contract too narrow) |
| "Reason code says X but I expected Y" | Check §0.2 component for that reason code |

### §0.2 Component Lookup Table

| Component | Theory/Rule | Architecture Doc | Code Location | Validation Command | Reason Codes |
|---|---|---|---|---|---|
| Parser | CLAUDE.md Rule 1 (PRECISION) | RECURSIVE_CURATION_MODEL.md §1 | `lib/parser.py` | `pytest tests/test_parser.py -v` | `no_year` |
| Explicit lookup | CLAUDE.md Rule 2 (priority 1) | VALIDATION_ARCHITECTURE.md §1 | `lib/lookup.py` | `pytest tests/test_lookup.py -v` | `explicit_lookup` |
| Corpus lookup | CLAUDE.md Rule 2 (priority 2) | VALIDATION_ARCHITECTURE.md §3 | `lib/corpus.py` | `pytest tests/test_corpus_lookup.py -v` | `corpus_lookup` |
| Reference canon | CLAUDE.md Rule 2 (priority 3) | RECURSIVE_CURATION_MODEL.md §3 | `lib/constants.py REFERENCE_CANON` | `pytest tests/ -k reference` | `reference_canon` |
| Satellite routing | CLAUDE.md Rule 2 (priority 4) | RECURSIVE_CURATION_MODEL.md §4 | `lib/satellite.py` | `pytest tests/test_satellite.py -v` | `satellite_*` |
| Core director | CLAUDE.md Rule 2 (priority 6) | RECURSIVE_CURATION_MODEL.md §3 | `lib/constants.py CORE_DIRECTORS` | `pytest tests/ -k core` | `core_director` |
| Popcorn check | CLAUDE.md Rule 2 (priority 7) | RECURSIVE_CURATION_MODEL.md §6 | `classify.py _popcorn_check()` | `pytest tests/ -k popcorn` | `popcorn_*` |
| API enrichment | CLAUDE.md §4 Dual-Source | VALIDATION_ARCHITECTURE.md §2 | `lib/tmdb.py`, `lib/omdb.py` | `python scripts/validate_handoffs.py` | (enrichment, not routing) |
| Evidence trails | CLAUDE.md Rule 7 | VALIDATION_ARCHITECTURE.md §2 | `lib/constants.py GateResult` | `pytest tests/test_evidence_trails.py -v` | (diagnostic only) |

### §0.3 Theory Check

When classification points to a theory problem:

1. Identify which CLAUDE.md Rule or theory doc governs this behavior
2. Read the relevant section — does it define the correct behavior?
3. If yes → the code drifted from the theory. Fix code to match.
4. If no → the theory needs updating. Update theory first, then code.
5. Check: is the theory grounded in scholarship? (Domain Grounding — CLAUDE.md Rule 4)

### §0.4 Architecture Check

When classification points to an architecture problem:

1. Find the relevant stage in `docs/architecture/RECURSIVE_CURATION_MODEL.md`
2. Verify: does the upstream stage output what the contract says?
3. Verify: does the downstream stage read what the contract says?
4. Run `python scripts/validate_handoffs.py` — checks all stage boundaries
5. If mismatch → fix the stage that violates the contract

### §0.5 Data Flow Trace

When you need to understand how a film moves through the pipeline:

1. Start at the stage where the problem is visible (check `reason` code)
2. Trace backward: what does this stage consume? From where?
3. Trace forward: what does this stage produce? Who consumes it?
4. Document: reads / produces / ignores (the "ignores" dimension reveals drift)
5. This is a PRECISION task — observe the code deterministically, don't interpret yet

Key pipeline flow:
```
filename → Parser → [explicit_lookup → corpus_lookup → reference → satellite → user_tag → core → popcorn] → Unsorted
                                                                ↑
                                              API enrichment feeds satellite/popcorn
```

### §0.6 Drift Audit

When a component hasn't been updated in a while, or a new upstream stage was added:

1. Identify the component + the issue/commit it was designed for
2. Map what it reads, produces, and ignores (§0.5)
3. Check: did any upstream stages add data since this component was designed?
4. Check: does the component consume that new data, or ignore it?
5. If ignoring new upstream data → likely highest-leverage fix

Common drift patterns in this project:
- New API field added (e.g. keywords) but satellite routing doesn't check it
- New corpus added but reaudit script doesn't check that category
- SORTING_DATABASE entry format changed but lookup parser still uses old format

### §0.7 Investigation → Spec Workflow

Once investigation is complete, convert findings to an actionable spec:

```
Investigation complete
    ↓
1. Classify the problem (§0.1)
    ↓
2. Trace to root cause using appropriate check (§0.3–§0.6)
    ↓
3. Write Issue Spec using docs/ISSUE_SPEC_TEMPLATE.md
   - §1 Manager Summary from your investigation findings
   - §3 Root Cause from your trace (specific file + function)
   - §4 Affected Handoffs from your data flow trace
   - §7 Measurement Story from your reaudit baseline
    ↓
4. Validate spec completeness using Section Checklist
    ↓
5. Pin baseline: git tag pre-issue-NNN && python scripts/reaudit.py
    ↓
6. Begin implementation
```

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

### "Writing a fix spec before implementing"

After diagnosing a problem, write an issue spec before touching code:

1. Use `docs/ISSUE_SPEC_TEMPLATE.md` — all 10 sections are mandatory
2. Pay special attention to §4 (Affected Handoffs) — list every downstream consumer
3. §5 Execution Order — numbered steps with verify commands for each
4. §7 Measurement Story — pin `python scripts/reaudit.py` baseline before starting
5. Run Section Checklist at the bottom before handing to implementer

→ See: `docs/ISSUE_SPEC_TEMPLATE.md`, `docs/WORK_ROUTER.md` §0.7

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

1. Determine which decade(s) — see `docs/theory/TIER_ARCHITECTURE.md` Part II for criteria
2. Add to `docs/CORE_DIRECTOR_WHITELIST_FINAL.md`
3. Update whitelist parser if format changed
4. Run classifier, verify the director's films now route to Core
5. Check: did any films move OUT of other tiers unexpectedly?

→ See: `docs/CORE_DIRECTOR_WHITELIST_FINAL.md`, `docs/theory/TIER_ARCHITECTURE.md` Part II

### "Add a known film to the database"

1. Edit `docs/SORTING_DATABASE.md` — add `- Title (Year) → Decade/Tier/Subdirectory/`
2. Follow the existing format in the file
3. Run classifier to verify it picks up the new entry
4. No code changes needed — the lookup parser reads the file dynamically

→ See: `docs/SORTING_DATABASE.md`

### "Add a film to a ground truth corpus"

1. Identify the Satellite category and find published scholarship that includes this film
2. Run `python scripts/build_corpus.py --add "Title" YEAR --category "Category Name"`
3. Provide canonical_tier (1=core canon, 2=reference, 3=texture), source citation, notes
4. Validate: `python scripts/reaudit.py --corpus`

→ See: `docs/architecture/VALIDATION_ARCHITECTURE.md` §3 and §6

### "Audit a category against scholarship"

1. Run `python scripts/build_corpus.py --audit "Category Name"`
2. Review HARD anomalies (structural gate violations — likely misrouted)
3. Review SOFT flags (director not in list — may be fine)
4. For confirmed films, add to corpus with citations

→ See: `docs/architecture/VALIDATION_ARCHITECTURE.md` §3

### "Corpus says a film is in the wrong category"

1. Run `python scripts/reaudit.py --corpus`
2. Check `output/corpus_check_report.csv` for `corpus_mismatch` entries
3. If the film is wrong: move it to the correct category (or add SORTING_DATABASE pin)
4. If the corpus entry is wrong: update `data/corpora/{category}.csv` with corrected data

→ See: `docs/architecture/VALIDATION_ARCHITECTURE.md` §3, `docs/DEBUG_RUNBOOK.md` Symptom #9

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

### "See the full library classification state / dashboard shows wrong percentage"

The dashboard's "Classified" percentage depends on which manifest you load:
- `sorting_manifest.csv` = Unsorted work queue only (shows ~0% when queue is all dirty filenames)
- `library_audit.csv` = full library including all tier folders (shows true collection-wide rate)

To generate / refresh the full library inventory:
```bash
python audit.py
# → output/library_audit.csv
```
Then load `library_audit.csv` in the dashboard manifest picker.

Run `audit.py` after each batch of `move.py --execute` to keep the picture current.

→ See: `audit.py`, `docs/CHANGELOG.md` v1.2

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
5. `docs/theory/COLLECTION_THESIS.md` — Collection identity, decade theory, format curation (10 min)
