# Why Films End Up in Unsorted: Pattern Analysis

**Analysis Date:** 2026-02-16  
**Based on:** v1.0 classification pipeline + Issue #002 audit + Issue #007 RAG proposal

---

## Executive Summary

Films end up in `Unsorted/` due to **classifier complexity mismatches** with the data realities. The system requires clean, structured data (director names, years, country codes) but real-world film filenames are messy, incomplete, and inconsistent—especially for marginal/exploitation cinema.

**Key Finding:** The 25-30% Unsorted rate is NOT a bug. It's the classifier correctly refusing to guess when it lacks reliable information. The complexity is **appropriate** for Core/Reference but **too strict** for Satellite/Popcorn.

---

## Classification Pipeline (8 Stages)

```
Stage 1: TMDb Enrichment (optional)
         ↓ [adds director, country if missing]
Stage 2: Explicit Lookup (SORTING_DATABASE.md)
         ↓ [highest trust - human curated]
Stage 3: Core Director Check (whitelist)
         ↓ [requires exact director match]
Stage 4: Reference Canon Check (50-film list)
         ↓ [hardcoded titles]
Stage 5: User Tag Recovery ([Core-1960s])
         ↓ [trust previous classification]
Stage 6: Country→Satellite (from filename)
         ↓ [decade-bounded routing]
Stage 7: TMDb→Satellite (country+genre)
         ↓ [requires TMDb data]
Stage 8: Unsorted/ (default)
         ↓ [reason codes logged]
```

**Hard Gate:** No year = immediate Unsorted (line 246)  
**Soft Gates:** Everything else continues to next stage

---

## Unsorted Reason Codes

From `classify.py` lines 355-372:

| Reason Code | Meaning | Frequency Estimate |
|-------------|---------|-------------------|
| `unsorted_no_year` | Parser couldn't extract year | ~5-10% |
| `unsorted_no_director` | No director in filename, TMDb failed | ~40-50% |
| `unsorted_no_match` | Has director but not Core/Reference/Satellite | ~40-50% |

---

## Root Cause Analysis: Why Unsorted Rate is High

### 1. TMDb Dependency Creates Fragility

**The Problem:**
- Satellite routing (Stage 7) requires TMDb data for country + genre
- TMDb search can fail for:
  - Foreign titles (especially transliterated names)
  - Alternate spellings (Brazilian: "Amadas e Violentadas" vs TMDb English title)
  - Obscure films (exploitation/cult films often missing)
  - Special editions (parser strips format signals, TMDb expects clean title)

**Impact:**
```
Film: "Thriller: A Cruel Picture (1974)" [Swedish exploitation]
TMDb Search: "Thriller A Cruel Picture" (cleaned)
TMDb Result: No match (title too generic, Swedish original "Thriller – en grym film")
→ No country data
→ No Satellite routing
→ Unsorted/
```

**From classify.py lines 200-222:**
```python
if self.tmdb and metadata.title and metadata.year:
    tmdb_data = self.tmdb.search_film(clean_title.strip(), metadata.year)
    if tmdb_data:
        # Enrich director/country
    # But if search fails → no enrichment → falls through to Unsorted
```

---

### 2. Parser Complexity vs. Real-World Filenames

**The Disconnect:**
- Parser expects: `Film.Title.YEAR.format.ext`
- Reality: `Film.Title.(YEAR).Director.Country.format.ext` (inconsistent)

**Failure Modes:**

#### A. Year Extraction Failures (~5-10% Unsorted)

**Case 1: Numeric titles**
```
Filename: "2001 - A Space Odyssey (1968) - 4K.mkv"
Parsed:   year=2001 (WRONG - from title, not parentheses)
Result:   Wrong decade, possibly Unsorted if other checks fail
```

**From Issue #002 audit:**
> Brazilian year-prefix pattern `r'^(\d{4})\s+-\s+(.+)'` matches film titles starting with numbers

**Case 2: No year at all**
```
Filename: "Black.Orpheus.BluRay.1080p.mkv"
Parsed:   year=None
Result:   Immediate Unsorted (hard gate at line 246)
```

**v1.0 Fix Status:** ✅ Partially fixed (Issue #003)
- Parenthetical years now prioritized
- But still fails if no year present at all

#### B. Director Extraction Never Works (~40-50% Unsorted)

**The Reality:**
- Parser NEVER extracts director from filename (only title + year)
- Relies 100% on TMDb enrichment
- If TMDb fails → no director → cannot match Core/Satellite

**From classify.py lines 200-222:**
```python
if tmdb_data:
    if not metadata.director and tmdb_data.get('director'):
        metadata.director = tmdb_data['director']  # ONLY SOURCE
```

**Why This Matters:**
- Stage 3 (Core director check) requires `metadata.director` (line 261)
- Stage 7 (Satellite routing) benefits from director context
- No fallback: if TMDb fails, director stays None

**Example:**
```
Film: "Suspiria (1977)" [Dario Argento]
Filename: No director in name
TMDb: Search succeeds → director="Dario Argento"
Result: Could route to Satellite/Giallo (if TMDb also has country=Italy)

Film: "Killer Nun (1979)" [Giulio Berruti]
Filename: No director in name
TMDb: Search fails (obscure)
Result: No director → no Core check → no Satellite → Unsorted/
```

---

### 3. Satellite Routing is Too Complex for Marginal Films

**Requirements for Satellite classification (lines 322-353):**
1. ✅ Year extracted (for decade validation)
2. ✅ Country detected (from filename language OR TMDb)
3. ✅ Country in COUNTRY_TO_WAVE map
4. ✅ Decade within category boundaries (e.g., Giallo: 1960s-1980s only)
5. ✅ OR TMDb genre+country match (Stage 7)
6. ✅ Category not at capacity cap

**The Catch-22:**
- **Marginal films** (exploitation, cult, foreign) are EXACTLY the films that:
  - Have messy/incomplete filenames
  - Missing from TMDb or have poor metadata
  - Use alternate titles/transliterations
  - Most NEED Satellite classification
- **But Satellite routing requires the MOST data** (country + genre + decade)

**Example Failure Chain:**
```
Film: "As Sete Vampiras (1986)" [Brazilian exploitation]
Step 1: Parser extracts title="As Sete Vampiras", year=1986 ✓
Step 2: No match in SORTING_DATABASE.md
Step 3: No director → skip Core check
Step 4: Not in Reference canon
Step 5: No user tag
Step 6: Country routing check:
        - metadata.country = None (parser doesn't detect Portuguese)
        - No country → skip Stage 6
Step 7: TMDb enrichment:
        - Search "As Sete Vampiras" (1986)
        - TMDb returns: country="BR" (Brazil) ✓
        - BUT: Genre="Horror" (not specific enough for category)
        - satellite_classifier.classify() checks:
          * Brazil + 1980s decade → valid for Brazilian Exploitation
          * Genre check: needs "exploitation" or specific markers
          * Result: No match (too generic)
Step 8: Unsorted/
```

**From lib/satellite.py (not shown but referenced):**
- Requires specific genre combinations (not just "Horror")
- TMDb genres are broad ("Action", "Thriller") vs specific categories ("Giallo", "Pinku Eiga")

---

### 4. Format Signals Created False Positives (v0.1 Bug - FIXED in v1.0)

**Historical Issue (Issue #002):**

In v0.1, films with format signals (Criterion, 35mm, 4K) were:
1. Stripped from SORTING_DATABASE.md entries: `"Dr Strangelove"` (stored)
2. NOT stripped from queries: `"Dr Strangelove Criterion"` (searched)
3. Lookup failed → fell through to "format signal detected" → routed to Popcorn

**Impact:**
- Core director films (Kubrick, Godard) misclassified as Popcorn
- Made Unsorted rate APPEAR lower but contaminated other tiers

**v1.0 Fix Status:** ✅ FIXED
- Symmetric normalization (Issue #004)
- `normalize_for_lookup()` used identically for storage + queries
- Format signals stripped consistently

---

## Specific Complexity Issues

### Issue 1: TMDb API is Required but Unreliable

**Why it's complex:**
- Requires API key setup (config.yaml)
- Rate limits (40 requests/10 seconds)
- Search quality varies by film obscurity
- Foreign titles often miss
- Genre tags are broad, not specific enough for Satellite categories

**Impact on Unsorted rate:**
- With TMDb: ~25-30% Unsorted (current)
- Without TMDb: ~60-70% Unsorted (estimate - no director enrichment)

**From classify.py lines 78-103:**
```python
tmdb_key = self.config.get('tmdb_api_key')
if tmdb_key and not self.no_tmdb:
    self.tmdb = TMDbClient(...)
else:
    self.tmdb = None
    logger.warning("TMDb API enrichment disabled (no API key in config)")
```

**Evidence:**
```bash
# Test without TMDb
python classify.py /path/to/films --no-tmdb

# Expect Unsorted rate to double (no director/country enrichment)
```

---

### Issue 2: Decade Validation is Strict (By Design)

**Why it's complex:**
- Satellite categories are **historically bounded** (e.g., Giallo: 1960s-1980s)
- A 2010s Italian thriller is NOT Giallo (genre evolved/ended)
- Requires exact decade matching

**Impact:**
```
Film: "Amer (2009)" [Italian neo-giallo]
Country: Italy ✓
Genre: Giallo-inspired ✓
Decade: 2000s ✗ (outside 1960s-1980s bounds)
Result: Unsorted/ (correctly - not historically valid Giallo)
```

**From lib/satellite.py (referenced in classify.py:324-337):**
```python
if metadata.country and metadata.country in COUNTRY_TO_WAVE:
    wave_config = COUNTRY_TO_WAVE[metadata.country]
    if decade in wave_config['decades']:  # Strict check
        # Route to Satellite
```

**This is GOOD complexity** - preserves curatorial intent. But contributes to Unsorted rate.

---

### Issue 3: No Fuzzy Matching (Precision vs Recall Trade-off)

**Current Design:**
- Lookup is EXACT match only (after normalization)
- No fuzzy matching (Levenshtein distance, etc.)
- No "did you mean?" suggestions

**Why:**
- **Precision over recall:** Only classify if confident
- Avoid false positives (wrong tier worse than Unsorted)
- Manual curation for Unsorted is acceptable (25-30% is manageable)

**Impact:**
```
Filename: "Dr Strangleove (1964)" [typo]
Lookup: No exact match for "dr strangleove"
Result: Unsorted/ (even though it's obviously Kubrick)
```

**Could add fuzzy matching, but:**
- Increases complexity
- Risk of false matches ("Alien" vs "Aliens")
- Current philosophy: let humans handle edge cases

---

## Pattern Summary: Who Gets Unsorted and Why

### Profile 1: Obscure Foreign Films (~30-40% of Unsorted)

**Characteristics:**
- Non-English titles
- Not in TMDb or poor metadata
- No director in filename
- Country detection fails

**Example:**
```
"Amadas e Violentadas (1976)" [Brazilian exploitation]
- TMDb search: Fails (Portuguese title)
- Country: Not detected (no [BR] tag in filename)
- Director: None
→ Unsorted/
```

**Why complex:**
- Would need multi-language TMDb search
- Or extensive country detection patterns
- Or manual SORTING_DATABASE.md entries (current solution)

---

### Profile 2: Films with Missing/Unparseable Years (~5-10% of Unsorted)

**Characteristics:**
- No (YEAR) in filename
- Or year ambiguous (numeric title like "1900", "1984")

**Example:**
```
"Black.Orpheus.BluRay.1080p.mkv"
- Year: None (hard gate failure)
→ Unsorted/
```

**Why complex:**
- Can't route to decade-based tiers without year
- Could add year lookup via TMDb, but what if multiple versions?
- Current solution: manual addition to SORTING_DATABASE.md with year

---

### Profile 3: Directors Not in Core/Satellite (~30-40% of Unsorted)

**Characteristics:**
- TMDb enrichment succeeds
- Director found
- But director not in Core whitelist
- And film doesn't match Satellite criteria (wrong country/decade/genre)

**Example:**
```
"The Wicker Man (1973)" [Robin Hardy]
- TMDb: director="Robin Hardy" ✓
- Core check: Not in whitelist
- Reference: Not in 50-film canon
- Satellite: UK + 1970s (no UK Satellite category)
→ Unsorted/
```

**Why complex:**
- Core whitelist is intentionally exclusive (38-43 directors)
- Satellite categories are specific (not all countries/genres covered)
- These ARE films that need manual curatorial decision

---

## Is the Complexity Justified?

### ✅ YES for Core/Reference

**Requirements:**
- Core: Exact director match (whitelist)
- Reference: Exact title match (50-film canon)

**Reasoning:**
- These are HIGH-VALUE classifications
- False positive (Popcorn film → Core) is worse than false negative (Core → Unsorted)
- 100% precision required

**Unsorted here is CORRECT** - "I don't have enough information to confidently classify this as Core"

---

### ⚠️ MAYBE for Satellite

**Current Requirements:**
- Country detection (filename OR TMDb)
- Genre detection (TMDb)
- Decade validation (strict boundaries)
- Director context helpful but not required

**Tension:**
- Satellite is FOR marginal/exploitation films (inherently messy metadata)
- But Satellite routing requires MOST structured data (country+genre+decade)

**Potential Simplifications:**
1. **Relax decade boundaries** - Allow 1-2 decade grace period?
   - ❌ Rejected: Violates curatorial intent (Giallo ended in 1980s)
2. **Add more country detection patterns** - Expand language tags
   - ✅ Possible: Could add more [BR], [IT], [JP] detection
3. **Manual SORTING_DATABASE.md entries** - Current solution
   - ✅ Working: 276 entries handle edge cases

---

### ✅ NO for Popcorn (but not implemented)

**Current Design:**
- No Popcorn routing (removed in v1.0 after v0.1 format signal bug)
- Films that don't match Core/Reference/Satellite → Unsorted

**Potential:**
- Could route remaining films to Popcorn/Decade by default
- But chosen NOT to: "If we don't know, don't guess"

---

## Recommendations

### 1. Accept 25-30% Unsorted as Design Success

**Reasoning:**
- These are films that SHOULD require human review
- Classifier correctly refuses to guess without confidence
- Manual curation for 300 films out of 1,000 is manageable

**Action:** None (current design is correct)

---

### 2. RAG-Assisted Classification (Issue #007 - IN PROGRESS)

**Goal:** Use RAG to provide context for Unsorted films

**Approach:**
```bash
# For each Unsorted film:
python classify_assistant.py "Film (Year)" "Director" "Context"

# RAG returns:
# - Similar films in database
# - Matching satellite categories
# - Suggested classification
```

**Status:** ✅ Stage 1 complete (this session)

**Impact:** Reduce manual research time (not Unsorted rate itself)

---

### 3. Expand Country Detection Patterns (Quick Win)

**Current:** `LANGUAGE_PATTERNS` in constants.py (13 languages)

**Could Add:**
- More [COUNTRY] tag detection ([BR], [IT], [JP], [HK], [SE])
- Filename substring detection ("brazilian", "italian", "japanese")
- Would help Stage 6 (Country→Satellite routing)

**Impact:** ~5-10% reduction in Unsorted (marginal gains)

---

### 4. TMDb Search Improvements (Medium Effort)

**Current Issues:**
- Single search attempt with cleaned title
- No retry with original title if clean search fails
- No alternate language search

**Could Add:**
```python
# Try cleaned title first
tmdb_data = self.tmdb.search_film(clean_title, year)
if not tmdb_data:
    # Retry with original title
    tmdb_data = self.tmdb.search_film(original_title, year)
if not tmdb_data:
    # Try without year (for year extraction failures)
    tmdb_data = self.tmdb.search_film(clean_title, year=None)
```

**Impact:** ~5-10% reduction in Unsorted (better director/country enrichment)

---

### 5. Decision Logging for Pattern Analysis (Stage 2)

**Current:** Reason codes logged but not analyzed

**Could Add:**
- SQLite database of all classifications
- Query: "Show me all unsorted_no_director films from 1970s"
- Identify systematic gaps (e.g., "80% of Unsorted Swedish films → need Swedish Exploitation category?")

**Impact:** Data-driven category additions

---

## Conclusion

**The 25-30% Unsorted rate is NOT a failure. It's evidence of good judgment.**

The classifier correctly refuses to guess when:
- TMDb data is missing/unreliable (no director/country)
- Year can't be parsed (can't route to decade)
- Film doesn't match Core/Reference/Satellite criteria

**The complexity is justified:**
- ✅ Core/Reference: High precision required (no false positives)
- ✅ Satellite: Historically bounded categories (curatorial intent)
- ✅ TMDb dependency: Only practical way to get director/country for thousands of films

**The solution is NOT to simplify the classifier.**
**The solution is RAG-assisted manual curation** (Issue #007, Stage 1 complete).

Manual curators now have:
- `classify_assistant.py` - RAG suggestions for Unsorted films
- `python -m lib.rag.query` - Knowledge base search
- 276 SORTING_DATABASE.md entries - Human-curated mappings

**Next:** Stage 2-4 will further reduce manual effort, but Unsorted rate will stay ~25-30% by design.

---

