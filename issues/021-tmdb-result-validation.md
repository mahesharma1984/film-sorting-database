# Issue #21: TMDb search returns wrong film — `results[0]` accepted without title/year validation

**Severity:** High
**Component:** `lib/tmdb.py`, `classify.py`
**Type:** Classification correctness bug
**Discovered via:** Architecture analysis (exports/knowledge-base)

---

## Summary

`TMDbClient._query_api()` accepts the first search result (`results[0]`) without checking whether the returned film's title or year matches the query. When TMDb returns the wrong film first — a remake, a foreign retitle, or a similarly-named film — all downstream classification (director, country, genres) silently uses the wrong data. Because the result is then cached, every subsequent run will continue returning the wrong classification.

---

## Root Cause

`lib/tmdb.py:115`:
```python
# Get first result
film_data = data['results'][0]
film_id = film_data['id']
```

TMDb's `/search/movie` endpoint returns results ranked by relevance, not by exact title match. Passing `year` as a search parameter (`tmdb.py:98-100`) narrows the search but does not guarantee the first result is a match — TMDb may return a result from a close year, a partial title match, or an alternate cut under the same title.

There is no validation step between receiving `results[0]` and fetching full details for `film_id`. By the time `film_data['title']`, `director`, `countries`, and `genres` are extracted and merged into `metadata`, there is no record of which TMDb film was actually used.

---

## Failure Scenarios

### Scenario A: Remake displaces original
Query: `"Suspiria (1977)"` — TMDb may rank the 2018 remake higher in some regions. The classifier receives Luca Guadagnino's director and production countries (IT/US 2018) instead of Dario Argento's.

**Result:** A legitimate Giallo is classified as Indie Cinema or Unsorted because the director `luca guadagnino` is not in the Giallo directors list, the year resolves to 1980s decade even with 2018 API data, but country metadata would differ.

### Scenario B: Foreign retitle collision
Query: `"The Ring (2002)"` — may match either the US remake (Gore Verbinski, US) or Hideo Nakata's `Ringu` (1998). If TMDb returns the 2002 US version for a file that is actually the 1998 Japanese film, the JP country signal is lost and the film cannot route to Pinku Eiga or Japanese Exploitation.

### Scenario C: Partial title with popular franchise
Query: `"Alien (1979)"` is unambiguous. But `"Aliens (1986)"` could theoretically match a different film titled "Aliens" with a closer text distance. Less common, but not impossible.

### Scenario D: Result cached with wrong data
Because the result is cached immediately (`tmdb.py:83-84`), a wrong `results[0]` match is stored and returned on every future run until the cache is manually invalidated. `scripts/invalidate_null_cache.py` only removes null entries; it does not detect or remove wrong-match entries.

---

## Impact

The downstream classification chain (`classify.py:309-412`) uses `tmdb_data` at three points:
1. `_merge_api_results()` (`classify.py:309-412`) — merges TMDb director and countries into `metadata` (mutates the object)
2. Satellite classification (`classify.py:584`) — `SatelliteClassifier.classify()` receives `metadata` and `tmdb_data` directly
3. Popcorn classification (`classify.py:550`) — `PopcornClassifier.classify_reason()` uses `tmdb_data` for popularity and genres

A wrong TMDb match silently corrupts all three stages. The classifier has no way to detect this — there is no confidence penalty for mismatched results, no warning log, and no audit trail in the manifest CSV for which TMDb film ID was used.

---

## R/P Split relevance

Per `CLAUDE.md §3 Rule 1`, "Get canonical director/genre/country" is a PRECISION task. Precision tasks require exactly one correct answer and binary evaluation. The current code does not evaluate correctness — it evaluates only availability (`results[0]` exists). Validation is the missing half of the PRECISION operation.

---

## Proposed Fix

### Stage 1: Add title and year validation after `results[0]`

In `lib/tmdb.py`, after line 115, add a validation pass:

```python
# Validate: check title similarity and year delta before accepting result
result_title = film_data.get('title', '') or film_data.get('original_title', '')
result_year = None
release_date = film_data.get('release_date', '')
if release_date:
    result_year = int(release_date[:4])

# Accept result only if title is similar and year is within 2 years
title_ok = _title_similarity(title, result_title) >= 0.6
year_ok = (year is None) or (result_year is None) or (abs(result_year - year) <= 2)

if not title_ok or not year_ok:
    logger.warning(
        f"TMDb result mismatch: query='{title}' ({year}), "
        f"got='{result_title}' ({result_year}) — skipping"
    )
    return None
```

Where `_title_similarity()` is a normalised string comparison (e.g. sequence matcher ratio or normalised edit distance after applying `normalize_for_lookup()` from `lib/normalization.py`).

### Stage 2: Log the matched TMDb film ID in classification output

Add `tmdb_id` and `tmdb_title` as optional fields in `ClassificationResult`. Populate them when a TMDb match is used. Write them to the manifest CSV (`output/sorting_manifest.csv`) so every classified film has an auditable record of which TMDb entity contributed to its routing.

This enables retroactive auditing: run `classify.py` on a known-good set, export the manifest, and spot-check TMDb IDs against the expected films.

### Stage 3: Cache invalidation for mismatched entries

Extend `scripts/invalidate_null_cache.py` to also flag and optionally remove cache entries where the cached film's `title` field does not match the cache key's title component (after normalization). Add a `--validate-matches` mode that reports suspect entries without deleting.

### Stage 4: Tests

Add test cases to `tests/test_tmdb_client.py` (or create it):
- Mock TMDb returning a 2018 film for a 1977 query → assert `search_film()` returns `None`
- Mock TMDb returning an exact match → assert result is accepted
- Mock TMDb returning a year-adjacent result (within 2 years) → assert result is accepted
- Mock TMDb returning a zero-result response → assert `None` (existing behaviour)

---

## Acceptance Criteria

- [ ] `TMDbClient._query_api()` validates title similarity and year delta before accepting `results[0]`
- [ ] Mismatched results log a `WARNING` and return `None` (not a crash, not silent acceptance)
- [ ] `ClassificationResult` and the manifest CSV include `tmdb_id` and `tmdb_title` fields
- [ ] Cache invalidation script has a `--validate-matches` mode
- [ ] New tests cover mismatch scenarios
- [ ] No regression in existing tests
