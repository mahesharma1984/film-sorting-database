# Changelog

All notable changes to the Film Sorting Database project.

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
