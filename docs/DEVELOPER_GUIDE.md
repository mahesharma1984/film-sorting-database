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
parser.py → classify.py (FilmMetadata)
constants.py → parser.py, normalization.py, classify.py (FORMAT_SIGNALS, RELEASE_TAGS, etc.)
normalization.py → lookup.py, classify.py (normalize_for_lookup)
lookup.py → classify.py (SORTING_DATABASE lookups)
core_directors.py → classify.py (whitelist checks)
classify.py → move.py (sorting_manifest.csv)
```

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
- Are stage boundaries still clean? (classify never moves; move never classifies)

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
6. **Workflow change** → Update `docs/WORKFLOW_REGISTRY.md`

**Critical rule:** Update docs in the same commit as code changes. Stale docs are worse than no docs.

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
