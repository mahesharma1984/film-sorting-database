# Bug Fixes

**Date:** 2026-02-23
**Commit:** `5af1cb5`

## Summary

This document records the bug fixes that stabilized clean test runs and removed release-tag parsing regressions.

## Fix 1: Release Tag Truncation in Title Cleaning

### Problem

Second-pass release-tag cleanup used raw substring matching. Short tags like `hd` and `nf` could match inside valid words and truncate real titles.

Examples of bad behavior:
- `Shadow` could be truncated by `hd`
- `The Conformist` could be truncated by `nf`

### Fix

Added token-boundary-aware release-tag stripping in `lib/normalization.py` (`strip_release_tags`) and applied it to:
- `classify.py` (`_clean_title_for_api`)
- `scripts/rank_category_tentpoles.py` (`clean_title_for_cache`)

## Fix 2: Stale Test Assumption on Explicit Lookup

### Problem

`tests/test_core_director_priority.py::test_demy_1970s_routes_to_fnw` assumed `Donkey Skin (1970)` had no explicit lookup entry.  
`docs/SORTING_DATABASE.md` now pins this film to Core, so Stage 2 lookup correctly overrides downstream routing and the test failed.

### Fix

Updated the test to use a synthetic non-pinned title (`Demy Test Film (1970)`) so it validates routing order without coupling to mutable curator lookup data.

## Regression Coverage Added

Added title-cleaning regression tests in `tests/test_api_merge.py` to verify:
- in-word substrings are not treated as release tags (`Shadow`, `The Conformist`, `Shahid`)
- tokenized tags are still stripped (`Shadow 1080p NF` -> `Shadow`)

## Validation

Command run:

```bash
pytest tests/ -q
```

Result:
- `295 passed, 1 skipped`
