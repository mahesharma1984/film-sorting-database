# Issue #18: Filename Normalization Pre-Stage — Separate PRECISION Cleaning from REASONING Classification

**Status:** Open
**Branch:** feature/v03-filename-normalization
**Priority:** High

---

## Background

The current pipeline has a PRECISION/REASONING violation at the boundary of `classify.py`. Before any tier judgment can happen, `classify.py` must first perform janitorial work: stripping edition markers, handling leading junk tokens, detecting non-film content, and resolving ambiguous year positions. When this janitorial work fails, films fall to Unsorted before the REASONING stage (Core/Reference/Satellite/Popcorn checks) ever sees them.

Current state: **568 / 694 films (81.9%) route to Unsorted.**

Per the R/P Split (REFACTOR_PLAN.md):

> *"Every operation in this system is either REASONING or PRECISION. The current codebase misassigns both."*

Filename cleaning is pure PRECISION — pattern matching, string manipulation, no cultural judgment. Tier assignment is pure REASONING — whitelist checks, decade bounds, satellite routing. These should not be the same stage.

Per the stage boundary law (REFACTOR_PLAN.md:234):

> *"The manifest is the contract. Classification never touches files. Moving never classifies."*

By extension: classification should not clean. Cleaning should not classify.

---

## Root Cause Analysis

### Cause 1: classify.py does two PRECISION jobs before reasoning begins

The current internal pipeline in `classify.py`:

```
[PRECISION] Clean dirty filename          ← janitorial
[PRECISION] Parse cleaned filename        ← parse work
[PRECISION] API enrichment                ← data gathering
[REASONING] Core check
[REASONING] Reference check
[REASONING] Satellite check
[REASONING] Popcorn check
```

The janitorial step is embedded inside the parser (`lib/parser.py`). When it fails, the error propagates upward as a bad `title`, missing `year`, or missing `director` — and the film falls to Unsorted with no REASONING stage reached.

### Cause 2: Six dirty filename pattern classes failing the parser

A full audit of the 568 Unsorted films identifies six distinct patterns that a dedicated normalization stage could handle:

| Pattern | Example | Count | classify.py failure |
|---|---|---|---|
| Leading junk tokens | `[DB]Tokyo Godfathers_(Dual Audio...)` | ~15 | `unsorted_no_director` |
| Edition markers in title position | `Braindead - Uncut (1992) - LaserDisc.mp4` | ~14 | `unsorted_no_match` |
| Year trapped in quality parenthetical | `A Força dos Sentidos (1978 - 480p - Áudio Original em Português).mp4` | ~9 | `unsorted_no_year` |
| Multiple years, wrong one chosen | `1992 Andrew Dice Clay For Ladies (1992 Hbo Broadcast).m4v` | ~18 | `unsorted_no_year` |
| TV episode format | `S01E05.mp4`, `The South Bank Show (1978) - S12E11...` | ~25 | `unsorted_no_year` |
| Interview / documentary prefix | `Interview - Stanley Kubrick (1966).mkv` | ~27 | `unsorted_no_match` |

These six patterns account for approximately **108 films** that a normalization pre-stage would rescue without any changes to `classify.py` or the REASONING logic.

### Cause 3: Non-film content pollutes the Unsorted analysis

~52 files (TV episodes + interviews + documentaries) are not films and should never enter the classification pipeline. They currently inflate the Unsorted count and obscure the true classification rate for actual films.

---

## Proposed Architecture

The refactor adds a single new stage — `normalize.py` — between raw input and `classify.py`:

```
scaffold.py     → folder structure         (PRECISION, existing)
     ↓
normalize.py    → filename cleaning        (PRECISION, NEW)
     ↓           [human review checkpoint — rename_manifest.csv]
classify.py     → tier assignment          (PRECISION + REASONING, existing, unchanged)
     ↓           [human review checkpoint — sorting_manifest.csv]
move.py         → file moves               (PRECISION, existing)
```

`normalize.py` is **pure PRECISION, zero reasoning**. It does not assign tiers, check directors, or make cultural judgments. Its sole output is `output/rename_manifest.csv`.

### normalize.py contract

**Input:** Source directory of video files
**Output:** `output/rename_manifest.csv` — one row per file with:

```
original_filename, cleaned_filename, change_type, notes
```

Where `change_type` is one of:
- `strip_junk` — removed leading `[TAG]` or `NN -` prefix
- `normalize_edition` — standardized edition marker to `{edition-...}` Plex format
- `fix_year` — extracted correct year from ambiguous position
- `flag_nonfim` — detected as TV episode, interview, or documentary
- `unchanged` — no cleaning needed

**Default:** dry-run (prints rename_manifest.csv, touches nothing)
**Execute:** `--execute` flag applies renames, same pattern as `move.py`

Human review of `rename_manifest.csv` before `--execute` preserves the audit trail that the manifest-as-contract pattern requires.

---

## Stages

### Stage 1: Catalogue all dirty filename patterns with regex test suite

Before writing `normalize.py`, document every failing pattern as a test case. No code without tests.

**Deliverables:**
- `tests/test_normalize.py` — one test per pattern class, using real filenames from the Unsorted audit
- Pattern inventory in this issue (update table above with final counts after test run)

**Success criteria:** All six pattern classes have passing tests before normalize.py is written.

---

### Stage 2: Implement normalize.py — pure PRECISION

Build `normalize.py` and `lib/normalizer.py` (the library module, following the same pattern as `lib/parser.py`).

**Normalizer rules (in application order — order matters):**

1. **Strip `[TAG]` prefixes** — `^\[.*?\]\s*` → remove
2. **Strip leading `NN -` numbering** — `^\d+\s*[-:]\s*` → remove
3. **Detect TV episodes** — match `S\d+E\d+` → flag as `nonfim/tv`
4. **Detect interview/documentary prefixes** — match `^(Interview|Documentary|Essay|Essay Film)\s*[-–]` → flag as `nonfim/supplementary`
5. **Fix year-in-quality-parenthetical** — `(YYYY - quality tags)` → extract year, rewrite as `(YYYY)`
6. **Fix multiple-year filenames** — when two valid years present, prefer the parenthetical year over a leading year prefix
7. **Normalize edition markers** — `- Uncut`, `- R-Rated Cut`, `- Hong Kong Cut`, `{edition-...}` → standardize to `{edition-NAME}` Plex convention

**What normalize.py does NOT do:**
- Does not assign tiers
- Does not check any whitelist or canon
- Does not call TMDb or OMDb
- Does not modify `SORTING_DATABASE.md`
- Does not move files (only renames in place, and only with `--execute`)

**Success criteria:**
- All Stage 1 tests pass
- `python normalize.py <source_dir>` produces a `rename_manifest.csv` without touching any file
- `python normalize.py <source_dir> --execute` applies renames and writes an audit log
- `python normalize.py <source_dir> --nonfim-only` flags non-film content without renaming

---

### Stage 3: Measure classification improvement

Run classify.py on the normalized filenames and compare manifests.

```bash
# Baseline (before normalize)
python classify.py <source_dir> --output output/manifest_before_normalize.csv

# Normalize
python normalize.py <source_dir>
# review rename_manifest.csv
python normalize.py <source_dir> --execute

# After normalize
python classify.py <source_dir> --output output/manifest_after_normalize.csv

# Compare
python compare_manifests.py output/manifest_before_normalize.csv output/manifest_after_normalize.csv
```

**Target:** Unsorted rate drops from 81.9% to ≤75% from normalization alone (before any classify.py changes).

**Success criteria:**
- No previously-classified film regresses to Unsorted (zero regressions)
- At least 80 of the ~108 targeted films now classify correctly
- `nonfim` films are excluded from the classification rate denominator

---

### Stage 4: Update pipeline documentation

`normalize.py` is a new mandatory stage in the pipeline. Docs that reference the 3-script architecture need updating.

**Files to update:**
- `REFACTOR_PLAN.md` — add Stage 0 (normalize) to the pipeline diagram
- `docs/DEVELOPER_GUIDE.md` — update execution order, add normalize to key commands
- `CLAUDE.md §5` — add `normalize.py` to Key Commands
- `docs/WORKFLOW_REGISTRY.md` — register new normalize workflow

**Success criteria:** A developer reading only `REFACTOR_PLAN.md` understands the pipeline correctly includes normalize.py.

---

## Files Implicated

| File | Role |
|------|------|
| `normalize.py` | New script — pure PRECISION filename cleaning |
| `lib/normalizer.py` | New library module — pattern matching rules |
| `tests/test_normalize.py` | New test suite — one test per dirty pattern class |
| `output/rename_manifest.csv` | New output — human review checkpoint before renames applied |
| `lib/parser.py` | Existing — may be simplified once normalize.py handles janitorial work |
| `classify.py` | Existing — unchanged in this issue; receives clean input |
| `REFACTOR_PLAN.md` | Update pipeline diagram |
| `docs/DEVELOPER_GUIDE.md` | Update execution order |

---

## Non-Goals (Explicitly Out of Scope)

The following are **not** part of this issue and should not be addressed here:

- Improving API enrichment for `unsorted_no_director` films (107 films) — separate issue
- Adding films to `SORTING_DATABASE.md` — human-curated, not programmatic
- Modifying `classify.py` classification logic
- Handling the ~243 files with no year anywhere in the filename (these require API enrichment, not normalization)

---

## Known Constraints

- `normalize.py --execute` renames files on the **source drive** (`/Volumes/One Touch/Movies/Organized/Unsorted/`). The drive must be mounted. Same hard gate as `move.py`.
- Renamed filenames must still be valid input to `lib/parser.py`. Normalize output is not a parallel path — it feeds the existing parser.
- The `{edition-...}` Plex convention must match whatever Plex expects; verify against existing edition-tagged files before standardizing.
- Do not rename files that are already correctly formatted (`change_type: unchanged`). The `rename_manifest.csv` should make this explicit so humans can audit zero-change rows easily.
