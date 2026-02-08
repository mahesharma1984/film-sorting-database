# Refactoring Plan: Film Sorting Database

## R/P Task Analysis

Every operation in this system is either REASONING or PRECISION. The current codebase misassigns both.

| Task | Type | Current Actor | Correct Actor | Status |
|------|------|---------------|---------------|--------|
| Parse filename → title, year | PRECISION | Code (regex) | Code (regex, improved) | Mostly works |
| Get canonical director/genre/country | PRECISION | Nobody (or broken filename parse) | Code (TMDb API + cache) | **Missing** |
| Look up known film → destination | PRECISION | Nobody | Code (SORTING_DATABASE.md parser) | **Missing** |
| "Is this a Core director?" | REASONING (structured rules) | Code (whitelist + fuzzy match) | Code (same, expanded list) | Works |
| "Is this in Reference canon?" | REASONING (structured rules) | Code (canon list + fuzzy match) | Code (same) | Works |
| "What satellite category?" | REASONING | Code (keyword grep on title) | Code (TMDb country + genre + director rules) | **Broken** |
| "Is this Popcorn?" | REASONING (structured rules) | Code (format signals only) | Code (format signals + lookup table) | Partial |
| Create folder tree on disk | PRECISION | Code | Code | Works |
| Move file from A to B | PRECISION | Code (copy2 bug) | Code (os.rename / shutil.move) | Fixed in film_sorter, not in sort_from_manifest |
| Format manifest CSV | PRECISION | Code (pandas) | Code (csv module, proper quoting) | Quoting bugs |

**Core problem:** The satellite classifier does a PRECISION operation (substring match on title) where a REASONING operation is needed (determine cultural/genre classification from structured metadata). TMDb provides the precision data; structured rules do the reasoning.

---

## Three Operations, Three Scripts

### 1. `scaffold.py` — Establish Folder Structure

**Type:** Pure PRECISION. Zero reasoning.

**Input:** Config with library root path + docs defining the structure.
**Output:** Empty folder tree on disk.

Reads the decade/tier/subdirectory structure from SORTING_DATABASE.md and CORE_DIRECTOR_WHITELIST_FINAL.md. Creates:

```
/Volumes/One Touch/movies/Organized/
├── 1940s/
│   ├── Core/
│   ├── Reference/
│   ├── Satellite/
│   └── Popcorn/
├── 1950s/
│   ├── Core/
│   │   ├── Satyajit Ray/
│   │   └── Billy Wilder/
│   ├── Reference/
│   ├── Satellite/
│   │   ├── European Sexploitation/
│   │   └── ...
│   └── Popcorn/
├── 1960s/ ...
├── 1970s/ ...
├── ... (through 2020s)
├── Staging/
│   ├── Borderline/
│   ├── Unknown/
│   ├── Unwatched/
│   └── Evaluate/
└── Out/
    └── Cut/
```

Director subfolders under Core come from the whitelist. Satellite category subfolders come from the category definitions. Deterministic — same input always produces same output.

---

### 2. `classify.py` — Classify Files

**Type:** Mixed. PRECISION for data gathering, REASONING via structured rules for tier assignment.

**Input:** Directory of video files + config (TMDb API key, paths to docs).
**Output:** `sorting_manifest.csv` — the contract between classification and moving.

**Never touches a file. Never moves anything. Only reads filenames and writes a CSV.**

#### Pipeline (priority order):

```
FILENAME
  │
  ▼
[PRECISION] Parse filename → raw title, year
  │
  ▼
[PRECISION] TMDb lookup → canonical title, year, director, genres, country
  │         (cached locally in tmdb_cache.json)
  ▼
[PRECISION] Explicit lookup → check SORTING_DATABASE.md table
  │         If found: done. Use the mapped destination.
  │         (This catches hundreds of films already classified by hand.)
  │
  ▼ (only if not in lookup table)
  │
[REASONING via rules] Core director check
  │         Director on whitelist? → Core/{decade}/Core/{Director}/
  │         Uses TMDb director, not filename director.
  │         Film goes to ITS OWN decade, not director's "primary" decade.
  │
  ▼ (only if not Core)
  │
[REASONING via rules] Reference canon check
  │         Title+year in 50-film canon? → {decade}/Reference/
  │
  ▼ (only if not Reference)
  │
[REASONING via rules] Satellite classification
  │         NO keyword matching against titles.
  │         Uses TMDb structured data:
  │           - country=BR + exploitation-adjacent → Brazilian Exploitation
  │           - country=JP + adult/erotic → Pinku Eiga
  │           - country=IT + horror/thriller + 1960s-80s → Giallo
  │           - country=HK + action → Hong Kong Action
  │           - Known satellite directors (Bava→Giallo, Wakamatsu→Pinku, etc.)
  │         Cap enforcement per category.
  │
  ▼ (only if not Satellite)
  │
[REASONING via rules] Popcorn check
  │         Format signals in filename (35mm, open matte, criterion, etc.)
  │         Plus: known Popcorn films from lookup table.
  │
  ▼ (only if nothing matched)
  │
[PRECISION] Staging assignment
            Has director but no tier match → Staging/Borderline
            Missing metadata even after TMDb → Staging/Unknown
```

#### What the explicit lookup table changes:

SORTING_DATABASE.md contains hundreds of lines like:
```
- Can't Buy Me Love (1987) → 1980s/Popcorn/
- Peking Opera Blues (1986) → 1980s/Satellite/Hong Kong Action/
- Shanghai Blues (1984) → 1980s/Satellite/Hong Kong Action/
```

These are films YOU already classified. The current code ignores all of this. The refactored classifier parses these into a title+year → destination lookup and checks it BEFORE any heuristic. This is the Stage 4.5 equivalent — pure PRECISION, zero API cost, eliminates the entire class of keyword misclassification bugs.

#### TMDb cache:

First run: query TMDb for all ~1201 films. Store results in `tmdb_cache.json`. Subsequent runs read cache. Cache is manually editable if TMDb returns wrong data. This means the API key is only burned once.

#### Manifest output:

```csv
filename,title,year,director,tier,decade,subdirectory,confidence,reason,destination
"Can't Buy Me Love (1987) 1080p WEB-DL DD2.0-fixed.mp4","Can't Buy Me Love",1987,Steve Rash,Popcorn,1980s,,1.0,Explicit lookup: SORTING_DATABASE.md,/Volumes/One Touch/movies/Organized/1980s/Popcorn
```

Properly quoted CSV. No more column misalignment from commas in filenames.

---

### 3. `move.py` — Move Files

**Type:** Pure PRECISION. Zero reasoning.

**Input:** `sorting_manifest.csv` + source directory.
**Output:** Files in their correct locations.

**Never classifies anything. Just reads the manifest and moves.**

- Validate: source files exist, destination drive mounted
- Same-filesystem detection: `os.stat().st_dev` comparison
- Same filesystem → `os.rename()` (instant, no byte copying)
- Different filesystem → `shutil.copy2()` + verify size + delete source
- Dry-run mode (default)
- Resumable: skips files already at destination
- Progress logging

---

## File Structure After Refactor

```
film-sorting-database/
├── scaffold.py              # Op 1: Create folder structure
├── classify.py              # Op 2: Classify → manifest CSV
├── move.py                  # Op 3: Read manifest → move files
├── lib/
│   ├── parser.py            # FilenameParser (cleaned up)
│   ├── tmdb.py              # TMDb client + local JSON cache
│   ├── lookup.py            # SORTING_DATABASE.md → lookup table
│   ├── core_directors.py    # Whitelist loader + fuzzy matcher
│   ├── reference_canon.py   # Canon loader + fuzzy matcher
│   ├── satellite.py         # TMDb-based satellite rules (no keywords)
│   └── popcorn.py           # Format signals + lookup
├── config_external.yaml     # Paths + TMDb API key (exists, has key)
├── docs/                    # UNCHANGED — source of truth
├── output/
│   ├── sorting_manifest.csv # Generated by classify.py
│   ├── staging_report.txt   # Generated by classify.py
│   └── tmdb_cache.json      # TMDb response cache
└── run.sh                   # Updated: scaffold → classify → move
```

---

## What Gets Deleted

- `film_sorter.py` — replaced by `classify.py` + `lib/` modules
- `sort_from_manifest.py` — replaced by `move.py`
- `test_sorter.py` — replaced with tests that actually test real filenames
- `setup_external_drive.sh` — drive detection lives in `move.py`

## What Stays Untouched

- Everything in `docs/` — the source of truth
- `config_external.yaml` — already has API key and correct paths
- `output/` directory

---

## Execution Order

```bash
# 1. Create the folder tree
python scaffold.py --config config_external.yaml

# 2. Classify all files (never moves anything)
python classify.py /Volumes/One\ Touch/movies/unsorted --config config_external.yaml

# 3. Review the manifest
# (edit sorting_manifest.csv by hand if needed)

# 4. Dry run the moves
python move.py output/sorting_manifest.csv /Volumes/One\ Touch/movies/unsorted --dry-run

# 5. Execute
python move.py output/sorting_manifest.csv /Volumes/One\ Touch/movies/unsorted
```

Step 3 is key — you can inspect and hand-edit the manifest between classification and moving. The manifest is the contract. Classification never touches files. Moving never classifies.

---

## Expected Outcomes

| Metric | Current | After Refactor |
|--------|---------|----------------|
| Staging rate | 72% (868/1201) | ~25-30% (only genuinely unknown films) |
| False satellite classifications | 22+ (keyword matching) | 0 (TMDb data + lookup table) |
| Correct decade assignment | Wrong for multi-decade directors | Correct (uses film's year) |
| Move speed (same filesystem) | 60-80 hours (byte copy) | 2-5 minutes (os.rename) |
| Manifest CSV integrity | Broken by commas in filenames | Properly quoted |
