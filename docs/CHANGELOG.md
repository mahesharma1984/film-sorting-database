# Changelog

All notable changes to the Film Sorting Database project.

---

## [v1.3] - 2026-02-23

### Fixed

- **Release-tag truncation bug in API/cache title cleaning**

  Short release tags (`hd`, `nf`) were being matched as raw substrings during second-pass cleanup. This could truncate valid titles (for example, `Shadow` or `The Conformist`) before TMDb/OMDb lookup.

  Fix: added boundary-aware release-tag stripping in `lib/normalization.py` and updated all affected callers:
  - `classify.py` (`_clean_title_for_api`)
  - `scripts/rank_category_tentpoles.py` (`clean_title_for_cache`)

- **Deterministic test failure from stale explicit-lookup assumption**

  `tests/test_core_director_priority.py::test_demy_1970s_routes_to_fnw` assumed `Donkey Skin (1970)` had no explicit lookup pin. `docs/SORTING_DATABASE.md` now explicitly pins this film to Core, so the test failed whenever Stage 2 lookup fired.

  Fix: test now uses a synthetic Demy title with no lookup pin, preserving the intended movement-vs-Core routing assertion without coupling to mutable curator data.

### Added

- **Regression tests for release-tag boundary behavior**

  Added API title-cleaning tests to ensure:
  - in-word substrings are not treated as release tags (`Shadow`, `The Conformist`, `Shahid`)
  - tokenized tags are still removed (`Shadow 1080p NF` → `Shadow`)

### Testing

- `pytest tests/ -q` → **295 passed, 1 skipped**

---

## [v1.2] - 2026-02-17

### Fixed

- **Issue #17 Stage 1: Migrate legacy decade-first folders to tier-first**

  16 files moved from `1950s/`–`1990s/` legacy top-level folders to correct tier-first locations. All 5 legacy decade folders removed. Zero errors.

  Affected directors/categories: Júlio Bressane (2), Pier Paolo Pasolini (1), Orson Welles (1), John Cassavetes (2), Claude Chabrol (1), American Exploitation (1), Classic Hollywood (1), Giallo (1), Hong Kong Action (2), Reference/1950s Hitchcock (3), Popcorn/1990s Waters (2).

  Script used: `scripts/migrate_structure.py` (existing, dry-run safe).

- **Issue #17 Stage 2: Move Core director films out of Popcorn**

  5 Core director films that the v0.1 pipeline had placed in Popcorn were reclassified and moved to their correct Core locations:
  - `Who's that Knocking at My Door` (1967) → `Core/1960s/Martin Scorsese/`
  - `The Bonfire of the Vanities` (1990) → `Core/1990s/Brian De Palma/`
  - `Snake Eyes` (1998) → `Core/1990s/Brian De Palma/`
  - `Only Lovers Left Alive` (2013) → `Core/2010s/Jim Jarmusch/`
  - `One-Tenth of a Millimeter Apart` (2021) → `Core/2020s/Wong Kar-wai/`

  Regression check: 0 regressions. No previously-classified films dropped to Unsorted.

- **Issue #17 Stage 4: Regenerate `sorting_manifest.csv`**

  Fresh `classify.py` run against the Unsorted folder. 568 entries, zero decade-first destination paths. Replaces stale 693-entry manifest.

### Added

- **`audit.py`** — Full library inventory script (Issue #17 Stage 3, Option B)

  Pure PRECISION. Read-only. Walks the organized library (Core/, Reference/, Satellite/, Popcorn/, Unsorted/, Staging/) and generates `output/library_audit.csv` compatible with the dashboard manifest picker.

  Derives tier/decade/subdirectory from folder paths — no classification logic, no API calls. Fills the manifest coverage gap: `sorting_manifest.csv` covers only the Unsorted work queue; `library_audit.csv` covers the full library.

  **Usage:** `python audit.py` (uses config_external.yaml). Run after each batch of moves for a current library overview. Load `library_audit.csv` in the dashboard for the full collection picture.

  **Current library state (2026-02-17):** Core 135 / Reference 27 / Satellite 360 / Popcorn 110 / Unsorted 568 / Staging 3 → **Classified: 52.5% (632/1,203)**

### Changed

- **Two-manifest workflow clarified**

  The dashboard now has two distinct manifest modes:
  - `sorting_manifest.csv` — work queue (Unsorted films only, what `classify.py` produces)
  - `library_audit.csv` — full library inventory (all tier folders, what `audit.py` produces)

  Load `library_audit.csv` in the dashboard to see collection-wide classification rates. Load `sorting_manifest.csv` to triage the current Unsorted queue.

- **Issue #17 Stage 3: Option C accepted**

  The manifest is a classification work queue, not a full library inventory. The ~500 manually curated files that pre-date the pipeline remain outside `sorting_manifest.csv` scope by design. `audit.py` fills this gap as a separate, independent script.

### Commits
- `64c7b47` - fix: migrate legacy decade-first folders to tier-first structure (Issue #17)
- `6e08117` - fix: move Core director films out of Popcorn (Issue #17 Stage 2)
- `eaf3267` - chore: close Issue #17 — update resolution, document Stage 3 decision
- `e41e5b4` - feat: add audit.py — full library inventory for dashboard (Issue #17 Stage 3)

---

## [v1.1] - 2026-02-17

### Fixed

- **Issue #16**: Classification rate regression (15% → target 65-70%)

  **Root cause:** Three cascading failures blocked classification:
  1. Dirty titles (tokens like `Metro`, `576p`, `SPANISH`) survived parser cleaning and poisoned TMDb/OMDb queries
  2. OMDb 95% null rate (downstream symptom of Layer 1)
  3. Routing rules too narrow for post-1980 and pre-1960 films

  **Fixes applied:**
  - `classify.py` — `_clean_title_for_api()` now does second-pass RELEASE_TAGS truncation + residual token removal
  - `lib/constants.py` — `SATELLITE_ROUTING_RULES` reordered: Indie Cinema and Classic Hollywood moved to END (they're catch-alls; exploitation categories must have priority)
  - `lib/constants.py` — Indie Cinema genres expanded to include `Thriller`; Classic Hollywood genre gate removed
  - `lib/popcorn.py` — `min_popularity` lowered from `10.0` to `7.0`
  - `lib/satellite.py` — Added Core director defensive check to prevent Satellite misrouting of Core auteurs

### Added

- **`scripts/invalidate_null_cache.py`** — Cache invalidation utility
  - Removes null TMDb/OMDb entries so re-queries use the improved title cleaning
  - Conservative mode (recommended): removes entries missing both director AND country
  - Aggressive mode: removes all null entries
  - Always backs up caches before modification

- **`scripts/validate_handoffs.py`** — Quality gates for pipeline handoffs (Theory of Constraints compliance)
  - Gate 1 (HARD): Title cleaning validation — catches dirty titles before expensive API calls
  - Gate 2 (SOFT): API enrichment validation — tracks minimum data survival at handoff
  - Gate 3 (SOFT): Routing success tracking — flags enriched films that went Unsorted

- **`issues/016-classification-rate-regression.md`** — Issue documentation with root cause analysis, fix details, and pre-existing test failures noted

### Changed

- **Satellite routing priority order** — Indie Cinema and Classic Hollywood are now checked LAST (after all exploitation categories). This is a semantic correctness fix: catch-alls must not override director-specific routing.

### Testing

- Test suite: 5 failures remain (down from 40 pre-existing failures)
- The 40 pre-existing failures were caused by a `CoreDirectorDatabase` import error in `SatelliteClassifier`; this is now fixed
- 5 remaining failures are pre-existing design tensions from Issue #14 (Larry Clark 1995+ decade narrowing); see `issues/016` for details

---

## [v1.0] - 2026-02-15

### Added
- **Parser: `(Director YYYY)` pattern without comma** (Issue #5)
  - Handles filenames like `Ed Wood (Tim Burton 1994).mkv`
  - Inserted at Priority 0.5 (after comma-based director pattern)
  - Added to [lib/parser.py:169](../lib/parser.py#L169)

- **Parser: Bare year at end of filename** (Issue #5)
  - Handles filenames like `sermon to the fish 2022.mp4`
  - Added to `_extract_year()` fallback patterns at [lib/parser.py:72](../lib/parser.py#L72)

- **Core Directors: 62 new directors added** (Issue #4)
  - Orson Welles (1940s, 1950s, 1960s, 1970s)
  - Vincent Gallo (1990s, 2000s)
  - Júlio Bressane (1960s, 1970s, 1980s, 1990s, 2000s)
  - Claude Chabrol (1960s, 1970s, 1980s, 1990s)
  - Total: **105 Core directors** across 8 decades

- **Testing: 7 new parser test cases**
  - Added to [tests/test_parser.py](../tests/test_parser.py)
  - `TestDirectorYearNoComma` class (3 tests)
  - `TestBareYearAtEnd` class (3 tests)
  - 1 regression test for comma pattern priority

### Changed
- **Documentation: Parser priority order documented**
  - Added comprehensive parser section to [docs/DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
  - Documents all 6 year extraction priorities with examples
  - Includes checklist for adding new patterns

- **Documentation: Collection stats updated**
  - [docs/PROJECT_COMPLETE_SUMMARY.md](PROJECT_COMPLETE_SUMMARY.md): Updated from ~850 films to 1,769 films
  - Core director count: 38-43 → 105 directors
  - Current classification rate: 19.0% (337/1,769)

- **Documentation: README features updated**
  - Added Core director count (105 across 8 decades)
  - Updated parser description to include new patterns

### Fixed
- **Issue #5**: Parser year extraction for 284 films with years in filenames
  - Fixed: `(Director YYYY)` pattern without comma
  - Fixed: Bare years at end of filename
  - Expected impact: ~30-50 films reclassified from `unsorted_no_year`

- **Issue #4**: Missing Core directors causing ~15-20 films to be unsorted
  - Fixed: Added Welles, Gallo, Bressane, Chabrol to whitelist
  - Verified: All directors correctly routing films to Core tier
  - Citizen Kane correctly remains in Reference canon

### Testing
- All 36 parser tests passing (29 existing + 7 new)
- Classification verified on 1,769-film collection
- No regressions detected

### Commits
- `db614d2` - Fix parser year extraction and add missing Core directors (Issues #5 and #4)

---

## [v0.2] - 2026-02-08

### Changed
- Refactored to tier-first organization (from decade-first)
- Enhanced classification pipeline with TMDb enrichment
- Added language/country extraction for satellite routing

---

## [v0.1] - 2026-02-07

### Added
- Initial 3-script architecture (classify, move, scaffold)
- Parser with 5 year extraction patterns
- Core director whitelist system
- Reference canon (50 films)
- 12 satellite categories with caps
- TMDb API integration
