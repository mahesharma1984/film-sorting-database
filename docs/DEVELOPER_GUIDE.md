# Developer Guide

**Purpose:** How to make changes safely in the film classification pipeline.

---

## Rule 0: Declare Failure Gates

Every script and check must declare:
- **Hard gates:** Failures that STOP execution (no year = can't route to decade, dest drive unmounted = can't move)
- **Soft gates:** Failures that WARN and continue (no director = fall through to lookup, no TMDb match = filename-only)

If you add a new check, explicitly document what happens when it fails.

---

## Before Making Changes

### 1. Understand What You're Changing

Before editing any module, trace:
- **What does it consume?** (inputs, imports, config)
- **What does it produce?** (outputs, side effects)
- **What depends on it?** (downstream modules, scripts)

Key dependency chains:
```
normalizer.py → normalize.py (FilenameNormalizer — pure PRECISION, Issue #18)
normalize.py → classify.py (cleaned filenames via rename_manifest.csv)
parser.py → classify.py (FilmMetadata)
constants.py → parser.py, normalization.py, classify.py (FORMAT_SIGNALS, RELEASE_TAGS, etc.)
normalization.py → lookup.py, classify.py (normalize_for_lookup — for LOOKUP symmetry)
lookup.py → classify.py (SORTING_DATABASE lookups)
core_directors.py → classify.py (whitelist checks)
classify.py → move.py (sorting_manifest.csv)
```

Note: `lib/normalizer.py` (filename cleaning) is separate from `lib/normalization.py`
(lookup normalization). They have different purposes — do not merge.

### 2. Apply the R/P Split

Before writing new classification logic:
- Is this a **REASONING** task (tier assignment, cultural judgment)? → Use structured rules on metadata
- Is this a **PRECISION** task (parsing, normalization, lookup, file I/O)? → Use deterministic code
- Is it **mixed**? → Split it into two steps

**Example:** "Determine if an Italian film is Giallo" is MIXED.
- PRECISION: Extract country code from TMDb data or filename language detection
- REASONING: Apply decade-bounded rule (Italy + 1960s-1980s → Giallo)

### 3. Check for Backwards Causality

Use the Pattern-First audit:
- Does this change make a downstream stage depend on an upstream stage's output that isn't guaranteed yet?
- Should this be a new pipeline step or a modification to an existing one?
- Are stage boundaries still clean? (normalize never classifies; classify never moves; move never classifies)

---

## Making Changes

### Small Changes (Single File, Clear Scope)

1. Make the change
2. Run `pytest tests/`
3. Verify output: run classifier on a test case, check manifest
4. Commit with clear message

### Medium Changes (Multiple Files, Single Feature)

1. Backup: `git stash` or commit current state
2. Measure baseline: run classifier, note classification rate and tier distribution
3. Make changes
4. Run `pytest tests/`
5. Re-run classifier, compare manifest to baseline
6. Commit with clear message

### Large Changes (Architecture, New Stage, Breaking)

1. Document the change plan (what, why, risks)
2. Pin baseline: tag current commit, save manifest copy
3. Make changes incrementally (commit each step)
4. Run `pytest tests/` after each step
5. Measure depth: check target case improved
6. Measure breadth: check no other cases regressed
7. Update docs in same commit as code changes
8. Update `docs/CHANGELOG.md`

---

## Satellite Routing Architecture (Issue #6 Update)

### Unified Decade-Validated Routing

As of Issue #6, ALL Satellite routing uses the `SATELLITE_ROUTING_RULES` structure in `lib/constants.py`. This applies decade validation to BOTH country-based AND director-based routing.

**Critical bug fixed:** Before Issue #6, directors like Argento could route a 2010s film to Giallo (historically ended in 1980s). Now, decade bounds prevent anachronistic classifications.

### Adding a New Satellite Director

1. **Determine the category:** Which exploitation/cult category does this director belong to?
   - Giallo (Italian horror-thriller 1960s-1980s)
   - Pinku Eiga (Japanese pink films 1960s-1980s)
   - Japanese Exploitation (yakuza/action 1970s-1980s)
   - Brazilian Exploitation (pornochanchada 1970s-1980s)
   - Hong Kong Action (martial arts/Category III 1970s-1990s)
   - American Exploitation (grindhouse 1960s-2000s)
   - European Sexploitation (1960s-1980s)
   - Blaxploitation (1970s, 1990s)

2. **Add to `SATELLITE_ROUTING_RULES` in `lib/constants.py`:**
   ```python
   'Category Name': {
       'country_codes': ['XX'],
       'decades': ['1970s', '1980s'],  # Decade bounds
       'genres': ['Genre1', 'Genre2'],
       'directors': [
           'existing director',
           'new director',  # Add here (lowercase, substring match)
       ],
   }
   ```

3. **Update `docs/SATELLITE_CATEGORIES.md`:**
   - Add director to category definition
   - Document decade bounds
   - Explain curatorial rationale

4. **Add tests to `tests/test_satellite_director_routing.py`:**
   ```python
   def test_new_director_routes_correctly(mock_metadata):
       """New Director 1970s → Category Name"""
       tmdb_data = {
           'director': 'New Director',
           'year': 1975,
           'countries': ['XX'],
           'genres': ['Genre1']
       }
       classifier = SatelliteClassifier()
       result = classifier.classify(mock_metadata, tmdb_data)
       assert result == 'Category Name'

   def test_new_director_outside_decade_not_routed(mock_metadata):
       """New Director 2000s → None (outside decade bounds)"""
       tmdb_data = {
           'director': 'New Director',
           'year': 2005,
           'countries': ['XX'],
           'genres': ['Genre1']
       }
       classifier = SatelliteClassifier()
       result = classifier.classify(mock_metadata, tmdb_data)
       assert result is None  # Outside valid decades
   ```

5. **Run tests:** `pytest tests/test_satellite_director_routing.py -v`

6. **Verify classification:** Run classifier on films by this director and check manifest

### Folder Structure: Category-First

Since Issue #6, Satellite uses **category-first** organization:
- ✅ New: `Satellite/{category}/{decade}/` (e.g., `Satellite/Giallo/1970s/`)
- ❌ Old: `{decade}/Satellite/{category}/` (deprecated)

**Rationale:** Category-first enables browsing all Giallo together, all Pinku Eiga together, etc.

**Updating `scaffold.py`:**
```python
satellite_path = library_path / 'Satellite' / category / decade
```

**Updating `classify.py`:**
```python
dest = f'Satellite/{category}/{decade}/'
```

### Priority Order in SATELLITE_ROUTING_RULES

Categories are checked in dictionary order (Python 3.7+ preserves insertion order). **Order matters** when directors might match multiple categories.

**Current order (as of Issue #27):**

1. French New Wave (director-only, no country/genre fallback)
2. Brazilian Exploitation
3. Giallo
4. Pinku Eiga
5. Japanese Exploitation
6. Hong Kong Action
7. Blaxploitation
8. **American New Hollywood** (director-only, 1960s–1980s)
9. American Exploitation
10. European Sexploitation
11. Music Films
12. **Classic Hollywood** ← catch-all for pre-1960 US (MUST be near end)
13. **Indie Cinema** ← catch-all for post-1980 international (MUST be last)

**Critical rule (Issue #16):** Indie Cinema and Classic Hollywood are broad catch-alls. They MUST come AFTER all exploitation categories. If they appear earlier, they intercept films that should reach exploitation director checks.

**Pipeline change (Issue #25):** The overall classify.py pipeline now fires Satellite routing BEFORE the Core director check. Core is a fallback for prestige non-movement work; Satellite catches movement-period films by any director (including Core directors). See `docs/theory/TIER_ARCHITECTURE.md` §3 and §11 for the full rationale.

**Example:** Ernest Dickerson could match both Blaxploitation (1970s, 1990s) and Indie Cinema (US, Drama, 1990s). Blaxploitation is listed BEFORE Indie Cinema, so a 1992 Dickerson film routes to Blaxploitation (correct). If Indie Cinema were listed first, it would intercept the film before Blaxploitation was checked.

If you add a new category, consider where it should appear. Specific/director-driven categories belong near the top. Broad country+decade catch-alls belong at the bottom.

---

## Testing Guidelines

### What to Test

- [ ] Unit tests for changed code (`pytest tests/`)
- [ ] Parser changes: test against known filenames with expected outputs
- [ ] Normalization changes: verify symmetry (build-side and query-side produce same result)
- [ ] Classification changes: run on test directory, compare manifest before/after
- [ ] Move changes: always test with `--dry-run` first

### When to Test

| Change Type | Unit Tests | Classification Run | Manifest Compare |
|---|---|---|---|
| Parser fix | Yes | Yes | Yes |
| New constant | Yes | If classification affected | If output affected |
| Normalization change | Yes | Yes (critical) | Yes |
| Lookup table edit | No (human-curated) | Yes | Yes |
| Move logic change | Yes | No | No |
| New satellite category | Yes | Yes | Yes |

### Measurement: Before/After Comparison

After any classification change, compare manifests:
```bash
# Run classifier before and after
python classify.py <test_dir> --output output/manifest_before.csv
# ... make changes ...
python classify.py <test_dir> --output output/manifest_after.csv

# Compare
python compare_manifests.py output/manifest_before.csv output/manifest_after.csv
```

Key metrics:
- **Classification rate:** % of films NOT going to Unsorted (higher = better)
- **Tier distribution:** Core/Reference/Satellite/Popcorn/Unsorted counts
- **Changed classifications:** which films moved between tiers (review each one)

---

## Documentation Rules

When code changes require doc updates:

1. **Architecture change** → Update `docs/CORE_DOCUMENTATION_INDEX.md`
2. **New satellite category** → Update `docs/SATELLITE_CATEGORIES.md` + `lib/constants.py`
3. **New Core director** → Update `docs/CORE_DIRECTOR_WHITELIST_FINAL.md`
4. **New known film** → Edit `docs/SORTING_DATABASE.md` (human only)
5. **Bug fix** → Update relevant `issues/` file or create new one
6. **Workflow change** → Update `docs/DEVELOPER_GUIDE.md` or `CLAUDE.md`

**Critical rule:** Update docs in the same commit as code changes. Stale docs are worse than no docs.

---

## Theory and Implementation Status

The theory knowledge base is in `docs/theory/` — five essays organized by the reading order in `docs/theory/README.md`. The full development methodology is in `exports/skills/` — nine composable skills summarized as Rules 1–9 in `CLAUDE.md` §3.

**Theory is currently ahead of implementation.** The two most recent essays describe work not yet implemented:

- `REFINEMENT_AND_EMERGENCE.md` → **Phase 1: American New Hollywood** as a new Satellite category. Specified in Issue #27 (Gap 1); implementation tracked in Issue #23.
- `SATELLITE_DEPTH.md` → **Phase 2–3: Within-category Core/Reference depth hierarchy.** Architecture decision: Option A (destination-changing, `core_directors` field in `SATELLITE_ROUTING_RULES`). Specified in Issue #27 (Gap 3).

Phase 2–3 is intentionally deferred until Phase 1 is complete — American New Hollywood is the test case for within-category depth.

The pre-implementation documentation gaps are tracked in `issues/027-pre-implementation-documentation-gaps.md`.

### RAG Semantic Search

For cross-concept questions across all documentation (including skills and knowledge-base):

```bash
python3 -m lib.rag.query "your question"                              # Top-5 results
python3 -m lib.rag.query "query" --filter AUTHORITATIVE               # Authority-filtered
python3 -m lib.rag.indexer --force                                     # Rebuild after doc changes
```

The index covers `docs/`, `exports/skills/`, and `exports/knowledge-base/`. See `docs/RAG_QUERY_GUIDE.md` for query patterns.

---

## Commit Messages

Format:
```
[type]: [what changed] ([why])

[details if needed]
```

Types: `fix`, `feat`, `refactor`, `docs`, `test`, `chore`

Examples:
```
fix: parser extracts year from parenthetical before year-prefix (issue #003)
feat: add TMDb cache layer for offline classification
refactor: extract satellite routing into lib/satellite.py
docs: update DEBUG_RUNBOOK with normalization lookup miss symptom
test: add parser edge cases for Brazilian year-prefix format
```

---

## Parser Priority Order (lib/parser.py)

The parser checks year extraction patterns in strict priority order. Higher priorities are checked first and win on match.

**CRITICAL:** Order matters for defensive parsing. Adding new patterns requires careful placement to avoid breaking existing logic.

### Year Extraction Priority (as of v1.0)

| Priority | Pattern | Example | Line | Added |
|----------|---------|---------|------|-------|
| **0** | `(Director, YYYY)` | `A Bay of Blood (Mario Bava, 1971).mkv` | 149 | v0.1 |
| **0.5** | `(Director YYYY)` no comma | `Ed Wood (Tim Burton 1994).mkv` | 169 | v1.0 (Issue #5) |
| **1** | `(YYYY)` parenthetical | `Film Title (1985).mkv` | 172 | v0.1 |
| **2** | `YYYY - Title` Brazilian prefix | `1976 - Amadas e Violentadas.avi` | 242 | v0.1 |
| **3** | `[YYYY]` brackets | `Film Title [1969].mkv` | 277 | v0.1 |
| **4** | Fallback patterns (in `_extract_year()`) | Various | 72 | v0.1 |

### Fallback Year Patterns (_extract_year method)

Tried in order when main patterns fail:

| Order | Pattern | Example | Added |
|-------|---------|---------|-------|
| **1** | `\s+(\d{4})$` bare year at end | `sermon to the fish 2022.mp4` | v1.0 (Issue #5) |
| **2** | `\((\d{4})\)` parenthetical | `Film (1999).mkv` | v0.1 |
| **3** | `\[(\d{4})\]` brackets | `Film [1969].mkv` | v0.1 |
| **4** | `[\.\s](\d{4})[\.\s]` delimited | `Film.1984.720p.mkv` | v0.1 |

### Adding New Patterns: Checklist

Before adding a new year extraction pattern:

- [ ] **Understand priority:** Where does this fit? Will it break existing patterns?
- [ ] **Test specificity:** Can it match filenames the wrong way?
- [ ] **Add regression tests:** Verify existing patterns still work
- [ ] **Document the change:** Update this table with line number and version
- [ ] **Consider year range validation:** All patterns must validate `1920 <= year <= 2029`

### Example: Issue #5 Parser Fixes

**Problem:** 284 films had years in filenames but parser failed to extract them.

**Failed patterns:**
1. `Ed Wood (Tim Burton 1994).mkv` — director + year without comma
2. `sermon to the fish 2022.mp4` — bare year at end

**Solution:**
- Added Priority 0.5 pattern `(Director YYYY)` at line 169
- Added fallback pattern `\s+(\d{4})$` to `_extract_year()` at line 72
- Order: Insert **after** comma-based director pattern (Priority 0) to avoid breaking it
- Verified: All 36 parser tests pass (29 existing + 7 new)
