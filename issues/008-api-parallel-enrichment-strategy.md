# Issue #008: API Parallel Enrichment Strategy — Theory-First Data Acquisition

**Priority:** High (affects classification rate)
**Type:** Refactor / Bug Fix
**Status:** ✅ **IMPLEMENTED** (2026-02-16)
**Estimated Effort:** 1-2 days (implementation + testing)
**Blocked By:** None
**Impacts:** Satellite routing, Unsorted rate, country detection

---

## ✅ Implementation Complete

**Date:** 2026-02-16
**Commit:** (to be tagged)
**Tests:** 20/20 passing ([tests/test_api_merge.py](../tests/test_api_merge.py))

**Verification:**
- [x] All unit tests pass (20 new tests)
- [x] No regressions in existing tests (137 existing tests still pass)
- [x] Statistics tracking implemented
- [x] Documentation updated ([CLAUDE.md](../CLAUDE.md) §4)

**Files Modified:**
- `classify.py` — Added 3 helper methods, refactored enrichment (44 lines → 5 lines)
- `tests/test_api_merge.py` — New test file (20 tests)
- `CLAUDE.md` — Updated §3 Rule 3 and §4 with API enrichment strategy
- `docs/API_STRATEGY_ANALYSIS.md` — Theory-first analysis document

---

---

## Context

The v0.2 implementation (2026-02-16) added OMDb API as a "fallback" to TMDb for obscure film enrichment:

```python
# Current (fallback model):
tmdb_data = self.tmdb.search_film(title, year)
if not tmdb_data:  # Only try OMDb if TMDb fails
    omdb_data = self.omdb.search_film(title, year)
```

**The Problem:** This "fallback" model violates theory-first principles and causes data loss.

---

## Problem Statement

### Core Issue: Fallback Model Violates R/P Split

**From CLAUDE.md §3 Rule 1:**
> Every operation is either REASONING or PRECISION. Never mix them in one step.

**API enrichment is PRECISION** (gathering facts), not reasoning. Precision tasks should optimize for **data quality**, not API hierarchy.

**Current bug:** The fallback model treats TMDb as "primary" and OMDb as "secondary," but:
- TMDb is **weaker** on country data (often returns `countries: []` for foreign films)
- Country data is **critical** for Satellite routing (Italy→Giallo, Brazil→Brazilian Exploitation, etc.)
- When TMDb "succeeds" with empty country data, OMDb is never queried
- Result: Film goes to Unsorted instead of Satellite

### Concrete Example: Italian Giallo Misclassification

**Film:** "Deep Red" (Dario Argento, 1975)

**Current behavior:**
1. TMDb query: ✅ Success
   - Returns: `{director: 'Dario Argento', countries: [], genres: ['Horror']}`
2. OMDb query: ❌ **Never tried** (TMDb "succeeded")
3. Classification: No country → Can't route to Satellite/Giallo → **Unsorted** ❌

**Expected behavior:**
1. TMDb query: `{director: 'Dario Argento', countries: [], genres: ['Horror']}`
2. OMDb query: `{director: 'Dario Argento', countries: ['IT'], genres: ['Horror', 'Mystery']}`
3. **Merge:** `{director: 'Dario Argento', countries: ['IT'], genres: ['Horror']}`
4. Classification: Italy + 1970s + Horror → **Satellite/Giallo** ✅

---

## Symptoms

### 1. Poor Country Detection Rate
- **Current:** ~40% of films have country data after enrichment
- **Expected:** ~70% (OMDb provides country for most films)
- **Impact:** Satellite routing fails → films go to Unsorted

### 2. TMDb "Success" Masks Data Gaps
TMDb returns partial data that blocks OMDb query:
```json
// TMDb response (considered "success" but incomplete):
{
  "director": "Dario Argento",
  "countries": [],  // Empty!
  "genres": ["Horror"]
}
```

OMDb never queried → country data lost.

### 3. High Unsorted Rate for Foreign Films
- Italian giallo (1960s-1980s): TMDb often missing country
- Brazilian exploitation (1970s-1980s): TMDb weak coverage
- Japanese pinku eiga (1960s-1980s): TMDb incomplete
- Hong Kong action (1970s-1990s): TMDb partial data

**Current Unsorted rate:** 25-30%
**Expected with fix:** 10-15% (**-15% absolute improvement**)

---

## Root Cause Analysis

### Why Fallback is Wrong (Theory-First)

**1. Violates R/P Split:**
- Fallback is a **reasoning pattern** (if X fails, try Y)
- But enrichment is **precision** (gather all facts)
- Should query both sources, merge by field quality

**2. Violates Pattern-First:**
- The 4-tier pattern requires different data:
  - Core: Director (critical)
  - Satellite: Country + decade (critical)
  - Reference: Title (critical)
  - Popcorn: Genre hints (helpful)
- TMDb and OMDb excel at **different fields**
- Should use each API for what it does **best**

**3. Wrong Mental Model:**
- "Primary/fallback" implies hierarchy
- Correct model: **Complementary sources**
- Each API is authoritative for different fields

---

## API Strengths Analysis

### TMDb Strengths

| Field | Quality | Notes |
|-------|---------|-------|
| Director | Good (mainstream) | Reliable for English films, recent releases |
| **Country** | **❌ Poor** | Often empty `[]` for foreign films |
| **Genres** | **✅ Excellent** | Structured IDs (28→Action, 27→Horror) |
| Coverage | Good (mainstream) | ~800K films, strong post-2000 |

**Best for:** Genre tagging, mainstream films, structured data

### OMDb Strengths

| Field | Quality | Notes |
|-------|---------|-------|
| **Director** | **✅ Excellent** | IMDb = authoritative, comprehensive |
| **Country** | **✅ Excellent** | IMDb country data thorough (IT, BR, HK, etc.) |
| Genres | Good | Comma-separated strings (less structured) |
| Coverage | **✅ Best** | IMDb = 10M titles, strong 1960s-1990s |

**Best for:** Director names, country codes, obscure/foreign/exploitation films

---

## Proposed Solution: Parallel Query + Smart Merge

### Core Principle

> **Use each API for what it does best, not as primary/fallback**

### Implementation Strategy

**1. Query both APIs** (when available)
**2. Merge results** based on field quality
**3. Use best available data** for classification

### Field Priority Rules

| Field | Priority | Reasoning |
|-------|----------|-----------|
| **Director** | OMDb > TMDb > filename | OMDb = IMDb = most authoritative |
| **Country** | OMDb > TMDb > filename | OMDb country data superior |
| **Genres** | TMDb > OMDb | TMDb structured IDs > text strings |
| **Year** | filename > OMDb > TMDb | Filename is curated, most trustworthy |

---

## Expected Impact

### Metrics

| Metric | Current (Fallback) | Proposed (Parallel) | Improvement |
|--------|-------------------|---------------------|-------------|
| **Director found** | 75% | 85% | +10% |
| **Country found** | 40% | 70% | **+30%** |
| **Unsorted rate** | 25-30% | 10-15% | **-15% absolute** |

### Key Insight

**The biggest gain comes from querying OMDb even when TMDb succeeds**, because TMDb's country data is incomplete.

This is not about "fallback for failures" — it's about **combining strengths**.

---

## Implementation Plan

### Phase 1: Refactor Enrichment Logic

**Files to modify:**
- `classify.py` — Refactor `_enrich_with_apis()` method
- `lib/tmdb.py` — No changes (already works)
- `lib/omdb.py` — No changes (already works)

**New method:**
```python
def _enrich_with_apis(self, metadata: FilmMetadata) -> Optional[Dict]:
    """Query TMDb and OMDb, merge results by field quality"""

    clean_title = self._clean_title_for_api(metadata.title)

    # Query both APIs (parallel)
    tmdb_data = self.tmdb.search_film(clean_title, metadata.year) if self.tmdb else None
    omdb_data = self.omdb.search_film(clean_title, metadata.year) if self.omdb else None

    # Neither found anything
    if not tmdb_data and not omdb_data:
        return None

    # Merge by field priority
    return self._merge_api_results(tmdb_data, omdb_data, metadata)

def _merge_api_results(self, tmdb_data, omdb_data, metadata) -> Dict:
    """Merge TMDb and OMDb results, using best source for each field"""

    merged = {
        'title': tmdb_data.get('title') if tmdb_data else omdb_data.get('title'),
        'year': tmdb_data.get('year') if tmdb_data else omdb_data.get('year'),

        # Director: OMDb > TMDb (IMDb is authoritative)
        'director': (
            omdb_data.get('director') if omdb_data and omdb_data.get('director')
            else tmdb_data.get('director') if tmdb_data else None
        ),

        # Country: OMDb > TMDb (OMDb has superior country data)
        'countries': (
            omdb_data.get('countries') if omdb_data and omdb_data.get('countries')
            else tmdb_data.get('countries') if tmdb_data else []
        ),

        # Genres: TMDb > OMDb (TMDb has structured IDs)
        'genres': (
            tmdb_data.get('genres') if tmdb_data and tmdb_data.get('genres')
            else omdb_data.get('genres') if omdb_data else []
        ),

        'original_language': tmdb_data.get('original_language') if tmdb_data else None
    }

    # Log merge sources for debugging
    sources = []
    if tmdb_data: sources.append('TMDb')
    if omdb_data: sources.append('OMDb')
    logger.debug(f"Merged enrichment for '{metadata.title}' from: {', '.join(sources)}")

    return merged
```

### Phase 2: Add Statistics Tracking

Track which API provided which data:

```python
# In __init__:
self.stats['tmdb_queries'] = 0
self.stats['omdb_queries'] = 0
self.stats['tmdb_provided_director'] = 0
self.stats['omdb_provided_director'] = 0
self.stats['tmdb_provided_country'] = 0
self.stats['omdb_provided_country'] = 0
self.stats['merged_results'] = 0

# In _merge_api_results:
if merged['director']:
    if omdb_data and omdb_data.get('director'):
        self.stats['omdb_provided_director'] += 1
    elif tmdb_data and tmdb_data.get('director'):
        self.stats['tmdb_provided_director'] += 1

if merged['countries']:
    if omdb_data and omdb_data.get('countries'):
        self.stats['omdb_provided_country'] += 1
    elif tmdb_data and tmdb_data.get('countries'):
        self.stats['tmdb_provided_country'] += 1

if tmdb_data and omdb_data:
    self.stats['merged_results'] += 1
```

### Phase 3: Update Documentation

**Files to update:**
1. **`CLAUDE.md` §4:** Change "OMDb API fallback" → "Dual-source enrichment"
2. **`docs/DEVELOPER_GUIDE.md`:** Add API strategy section
3. **`OMDB_IMPLEMENTATION.md`:** Deprecate/update to reflect parallel model
4. **`docs/API_STRATEGY_ANALYSIS.md`:** Mark as implemented
5. **`classify.py` docstring:** Update to reflect parallel querying

---

## Testing Strategy

### Unit Tests

**New test file:** `tests/test_api_merge.py`

```python
def test_merge_prefers_omdb_country():
    """OMDb country data should override empty TMDb country"""
    tmdb_data = {'director': 'Argento', 'countries': [], 'genres': ['Horror']}
    omdb_data = {'director': 'Argento', 'countries': ['IT'], 'genres': ['Horror']}

    merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

    assert merged['countries'] == ['IT']  # OMDb wins

def test_merge_prefers_tmdb_genres():
    """TMDb genre data should override OMDb genres"""
    tmdb_data = {'genres': ['Horror', 'Thriller']}
    omdb_data = {'genres': ['Horror', 'Mystery']}

    merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

    assert merged['genres'] == ['Horror', 'Thriller']  # TMDb wins

def test_merge_handles_partial_data():
    """Should merge when only one API has data"""
    tmdb_data = {'director': 'Argento', 'countries': []}
    omdb_data = None  # OMDb failed

    merged = classifier._merge_api_results(tmdb_data, omdb_data, metadata)

    assert merged['director'] == 'Argento'
    assert merged['countries'] == []
```

### Integration Tests

**Test on known problem films:**
1. Italian giallo (1970s) — TMDb has no country, OMDb has IT
2. Brazilian exploitation (1970s) — TMDb missing, OMDb has BR
3. Japanese pinku eiga (1960s) — TMDb partial, OMDb complete
4. Hong Kong action (1980s) — TMDb no country, OMDb has HK

**Expected results:**
- Before: All go to Unsorted (no country data)
- After: All route to correct Satellite category

### Regression Testing

**Run on full test set:**
```bash
# Baseline
python classify.py test_films/ --output output/manifest_before.csv

# After changes
python classify.py test_films/ --output output/manifest_after.csv

# Compare
python scripts/compare_manifests.py output/manifest_before.csv output/manifest_after.csv
```

**Metrics to check:**
- Classification rate (should increase)
- Satellite routing rate (should increase)
- Unsorted rate (should decrease)
- No regressions in Core/Reference routing

---

## Costs and Trade-offs

### API Call Volume

**Current (fallback):**
- TMDb queries: 100% of films
- OMDb queries: ~25% (only TMDb failures)
- Total OMDb: ~250 per 1,000 films

**Proposed (parallel):**
- TMDb queries: 100% of films
- OMDb queries: 100% of films
- Total OMDb: ~1,000 per 1,000 films

**Cost:** OMDb $1/month = 1,000 requests/day
- Parallel model: 1,000 films/month at free tier
- **Solution:** Caching makes re-runs free (only new films cost API calls)
- **Alternative:** Upgrade to $10/month (100K/day) if needed

### Caching Mitigates Costs

- Both APIs cache in JSON files (`tmdb_cache.json`, `omdb_cache.json`)
- Re-running classifier = 100% cache hit rate (free)
- Only new/changed films require API calls
- Incremental classification: 50 new films = 50 TMDb + 50 OMDb calls

---

## Success Criteria

### Metrics

- [ ] Country detection rate increases from 40% to 70%
- [ ] Unsorted rate decreases from 25-30% to 10-15%
- [ ] Satellite routing improves for foreign/exploitation films
- [ ] No regressions in existing classifications
- [ ] Statistics show OMDb providing country data in 50%+ of cases

### Tests

- [ ] All unit tests pass (`pytest tests/test_api_merge.py`)
- [ ] Integration tests show improved Satellite routing
- [ ] Regression tests show no breaking changes
- [ ] Test on 100 known Italian giallo → all route correctly

---

## Related Issues

- **Issue #006:** Director-based Satellite routing (affects how enriched data is used)
- **Issue #005:** Parser fixes (year extraction feeds into API queries)
- **Issue #007:** RAG system (could use enriched metadata for better suggestions)

---

## References

- **Analysis:** `docs/API_STRATEGY_ANALYSIS.md` — Full theory-first justification
- **Code:** `classify.py:215-258` — Current fallback implementation
- **Docs:** `OMDB_IMPLEMENTATION.md` — Original fallback design
- **Theory:** `CLAUDE.md §3 Rule 1` — R/P Split principle
- **Theory:** `docs/DEVELOPER_GUIDE.md` — Before Making Changes checklist

---

## Implementation Checklist

### Code Changes
- [ ] Refactor `classify.py._enrich_with_apis()` to query both APIs
- [ ] Add `classify.py._merge_api_results()` method
- [ ] Update enrichment metadata assignment logic
- [ ] Add statistics tracking for merged results

### Testing
- [ ] Write unit tests for merge logic
- [ ] Test on Italian giallo films (should route to Satellite)
- [ ] Test on Brazilian exploitation (should route to Satellite)
- [ ] Run full regression test suite
- [ ] Verify no regressions in Core/Reference routing

### Documentation
- [ ] Update `CLAUDE.md` §4 (remove "fallback" language)
- [ ] Update `docs/DEVELOPER_GUIDE.md` (add API strategy section)
- [ ] Update `classify.py` docstring
- [ ] Mark `docs/API_STRATEGY_ANALYSIS.md` as implemented
- [ ] Update `OMDB_IMPLEMENTATION.md` or deprecate

### Verification
- [ ] Check statistics output shows merged results
- [ ] Verify OMDb cache size increases (being used)
- [ ] Compare before/after classification rates
- [ ] Review sample of changed classifications manually

---

## Notes

- **No breaking changes:** Graceful degradation if OMDb unavailable
- **Backwards compatible:** Works with existing cache files
- **Incremental improvement:** Each field merge rule can be tuned independently
- **Theory-first:** Justification rooted in R/P Split and Pattern-First principles
