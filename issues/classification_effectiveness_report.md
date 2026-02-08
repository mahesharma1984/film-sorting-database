# Film Classification System - Effectiveness Analysis Report

**Date:** 2026-02-09
**Version:** v0.1 (classify_v01.py)
**Status:** CRITICAL ISSUES IDENTIFIED
**Analyst:** System Audit

---

## Executive Summary

The film classification system v0.1 contains **critical logic and implementation flaws** that cause systematic misclassification of Core-tier films. High-value director films (Kubrick, etc.) are being incorrectly routed to Popcorn tier due to asymmetric normalization in the lookup system and incorrect parsing logic.

**Key Findings:**
- ❌ Core director films with format signals bypass database lookup
- ❌ Year parsing fails for films with numeric titles ("2001: A Space Odyssey")
- ❌ Classification rate appears inflated due to false Popcorn assignments
- ⚠️ Fundamental design flaw: asymmetric normalization in lookup system

**Recommendation:** DO NOT RUN IN PRODUCTION. Requires immediate fixes before deployment.

---

## 1. Test Methodology

### 1.1 Analysis Scope
- **Source:** 1,149 video files processed
- **Output:** `output/sorting_manifest_v01.csv`
- **Focus:** Stanley Kubrick films (known Core director)
- **Validation:** Cross-referenced with `docs/SORTING_DATABASE.md` explicit mappings

### 1.2 Test Cases Examined

Three Stanley Kubrick films explicitly listed in SORTING_DATABASE.md:

| Film | Expected Destination | Filename |
|------|---------------------|----------|
| Dr. Strangelove (1964) | 1960s/Core/Stanley Kubrick/ | Dr.Strangelove.1964.Criterion.1080p.BluRay.x265.10bit.mkv |
| 2001: A Space Odyssey (1968) | 1960s/Core/Stanley Kubrick/ | 2001 - A Space Odyssey (1968) - 4K.mkv |
| The Shining (1980) | 1980s/Core/Stanley Kubrick/ | The.Shining.1980.35mm.Scan.FullScreen.HYBRID.OPEN.MATTE.1080p.mkv |

---

## 2. Findings

### 2.1 Critical Failure: Format Signal Contamination

**Issue:** Films with format signals (Criterion, 35mm, 4K) fail database lookup despite being explicitly listed.

#### Case Study: Dr. Strangelove

```
Filename: Dr.Strangelove.1964.Criterion.1080p.BluRay.x265.10bit.mkv

Expected:  1960s/Core/Stanley Kubrick/
Actual:    Popcorn/1960s/
Reason:    format_signal
```

**Root Cause Analysis:**

```python
# lib/lookup.py - Database building (DOES strip format signals)
def _parse_database(self, file_path: Path):
    title_raw = self._strip_format_signals(title_raw)  # ✓ Strips "Criterion"
    title = self._normalize_title(title_raw)           # → "dr strangelove"
    self.lookup_table[(title, year)] = destination

# lib/lookup.py - Query (DOES NOT strip format signals)
def lookup(self, title: str, year: Optional[int]):
    normalized = self._normalize_title(title)          # → "dr strangelove criterion"
    key = (normalized, year)
    return self.lookup_table.get(key)                  # ✗ NO MATCH
```

**Impact:**
- Database contains: `("dr strangelove", 1964)`
- Query searches for: `("dr strangelove criterion", 1964)`
- Match fails → falls through to Pass 2 → format_signal detected → routes to Popcorn

#### Case Study: The Shining

```
Filename: The.Shining.1980.35mm.Scan.FullScreen.HYBRID.OPEN.MATTE.1080p.mkv

Expected:  1980s/Core/Stanley Kubrick/
Actual:    Popcorn/1980s/
Reason:    format_signal
```

**Title normalization failure:**
- Database: `"the shining"`
- Query: `"the shining 35mm scan fullscreen hybrid open matte"`
- Result: NO MATCH

---

### 2.2 Critical Failure: Year Parsing Logic Error

**Issue:** Films with numeric titles have year extracted incorrectly.

#### Case Study: 2001: A Space Odyssey

```
Filename: 2001 - A Space Odyssey (1968) - 4K.mkv

Expected:  year=1968, title="2001: A Space Odyssey" → 1960s/Core/Stanley Kubrick/
Actual:    year=2001, title="A Space Odyssey" → Popcorn/2000s/
Reason:    format_signal (WRONG DECADE!)
```

**Root Cause Analysis:**

```python
# lib/parser.py:111-121 - Brazilian year-prefix pattern matches FIRST
year_prefix_match = re.match(r'^(\d{4})\s+-\s+(.+)', name)
if year_prefix_match:
    year_str, title = year_prefix_match.groups()
    year = int(year_str)  # Extracts 2001 from title, not 1968 from parentheses!
```

**Parser execution order:**
1. ✓ Matches `r'^(\d{4})\s+-\s+(.+)'` → year=2001, title="A Space Odyssey (1968) - 4K"
2. ✗ Never checks parenthetical year pattern `r'\((\d{4})\)'`

**Impact:**
- Film from 1960s routed to 2000s decade
- Double failure: wrong decade AND wrong tier

---

### 2.3 Design Flaw: Asymmetric Normalization

**Fundamental Logic Error:**

The lookup system applies different normalization rules to database entries vs. queries:

| Operation | Strips Format Signals | Normalizes Case/Punctuation |
|-----------|----------------------|----------------------------|
| Building database (intake) | ✓ YES | ✓ YES |
| Querying database (lookup) | ✗ NO | ✓ YES |

**Why This is a Reasoning Problem:**

This violates the **Symmetry Principle** of lookup/hash systems:
```
If normalize(database_entry) is stored as key,
Then normalize(query) must use IDENTICAL transformation
Otherwise: lookup will fail
```

**Code Location:** `lib/lookup.py`
- Line 102: `title_raw = self._strip_format_signals(title_raw)` (database only)
- Line 172: `normalized = self._normalize_title(title)` (query only, missing strip)

---

## 3. Impact Assessment

### 3.1 Misclassification Rate

**Kubrick Films in Test Set:**
- Total: 3 actual films + 3 documentaries
- Correctly classified: **0/3 (0%)**
- Misrouted to Popcorn: 3/3 (100%)
- Misrouted to wrong decade: 1/3 (33%)

### 3.2 False Positive Rate

**Popcorn Tier Contamination:**
```
grep "Popcorn.*format_signal" sorting_manifest_v01.csv
```

Films classified as Popcorn via `format_signal` may include:
- Core director films with special editions (high priority, misclassified)
- Reference canon films with format signals (high priority, misclassified)
- Legitimate Popcorn films (correct classification)

**Cannot determine true Popcorn rate without manual review.**

### 3.3 Cascading Failures

```
Classification Flow (Current):

Pass 1: Exact Matches
├─ Core director check (requires director in filename) → FAILS (no director parsed)
└─ Database lookup → FAILS (format signals block match)

Pass 2: Signals or Unsorted
├─ Format signals detected → Routes to Popcorn ✗ WRONG
└─ No signals → Routes to Unsorted
```

**Problem:** Once database lookup fails, there's no fallback to check Core directors or Reference canon.

---

## 4. Root Cause Analysis

### 4.1 Primary Cause: Asymmetric Normalization (REASONING FLAW)

**What Happened:**
- Developer implemented format signal stripping for database parsing
- Developer forgot to implement same stripping for query normalization
- System appears to work for clean filenames (no format signals)
- System fails silently for curated editions (which are often Core-tier films!)

**Why It's a Reasoning Problem:**
- Indicates incomplete mental model of lookup system requirements
- Missing validation: "If I normalize input, do I normalize output?"
- No test cases for format-signal-contaminated lookups

### 4.2 Secondary Cause: Parser Priority Order (PRECISION BUG)

**What Happened:**
- Brazilian year-prefix pattern added for special case: "1976 - Amadas e Violentadas"
- Pattern placed early in matching priority (line 111)
- Matches "2001 - A Space Odyssey (1968)" incorrectly
- Parenthetical year pattern never evaluated

**Why It's a Precision Problem:**
- Simple regex ordering error
- Missing validation: check if parentheses exist, prefer that year

### 4.3 Tertiary Cause: No Fallback Logic (REASONING FLAW)

**What Happened:**
- Pass 1 lookup fails → immediately proceeds to Pass 2
- No attempt to query API for director
- No attempt to check if film is in Reference canon
- No warning logged that explicit lookup failed

**Why It's a Reasoning Problem:**
- Classification system too rigid (binary: explicit match OR heuristics)
- Missing middle tier: fuzzy matching, API enrichment, confidence scoring

---

## 5. Statistical Analysis

### 5.1 Classification Breakdown (from output)

```
Total films processed: ~1,149

PASS 1: Exact Matches
  Core director (exact):  [count not shown in csv]
  Explicit lookup:        [estimated ~150-200 based on grep]
  Subtotal:               [unknown]

PASS 2: Signals
  Format signal (Popcorn): [estimated ~50-100]

UNSORTED
  Needs manual review:    [estimated ~800-900]

Classification rate: [unknown]% (UNRELIABLE due to contamination)
```

**Data Quality Issues:**
- Cannot trust "classification rate" metric
- Popcorn tier includes unknown number of Core films
- True classification rate likely **20-30% lower** than reported

---

## 6. Recommendations

### 6.1 Immediate Fixes (CRITICAL - P0)

#### Fix 1: Symmetric Normalization in Lookup

**File:** `lib/lookup.py:166-178`

```python
def lookup(self, title: str, year: Optional[int]) -> Optional[str]:
    """Look up destination for title+year"""
    # FIX: Strip format signals from query (same as database)
    title_stripped = self._strip_format_signals(title)
    normalized = self._normalize_title(title_stripped)

    # Exact match with year
    key = (normalized, year)
    if key in self.lookup_table:
        logger.debug(f"Lookup hit: '{title}' ({year})")
        return self.lookup_table[key]

    # Try without year if year was provided
    if year is not None:
        key_no_year = (normalized, None)
        if key_no_year in self.lookup_table:
            logger.debug(f"Lookup hit (no year): '{title}'")
            return self.lookup_table[key_no_year]

    return None
```

#### Fix 2: Year Parser Priority

**File:** `lib/parser.py:98-169`

**Strategy 1 (Preferred):** Check for parenthetical year FIRST
```python
# NEW: Extract parenthetical year first if it exists
paren_year_match = re.search(r'\((\d{4})\)', name)
if paren_year_match:
    year = int(paren_year_match.group(1))
    if 1920 <= year <= 2029:
        # Remove (YEAR) from title
        title = re.sub(r'\s*\(\d{4}\)', '', name)
        return FilmMetadata(
            filename=filename,
            title=self._clean_title(title),
            year=year,
            format_signals=format_signals
        )

# THEN try year-prefix format (Brazilian style)
year_prefix_match = re.match(r'^(\d{4})\s+-\s+(.+)', name)
# ...
```

**Strategy 2 (Alternative):** Add validation to year-prefix match
```python
year_prefix_match = re.match(r'^(\d{4})\s+-\s+(.+)', name)
if year_prefix_match:
    year_str, title = year_prefix_match.groups()
    year = int(year_str)

    # NEW: If title contains another year in parens, use that instead
    paren_year_match = re.search(r'\((\d{4})\)', title)
    if paren_year_match:
        year = int(paren_year_match.group(1))
        title = re.sub(r'\s*\(\d{4}\)', '', title)  # Remove from title

    if 1920 <= year <= 2029:
        return FilmMetadata(...)
```

#### Fix 3: Add Lookup Failure Logging

**File:** `classify_v01.py:133-149`

```python
# Check 2: Explicit lookup in SORTING_DATABASE.md
if metadata.year:
    dest = self.lookup_db.lookup(metadata.title, metadata.year)
    if dest:
        self.stats['explicit_lookup'] += 1
        # ...
    else:
        # NEW: Log lookup failures for films with format signals
        if metadata.format_signals:
            logger.warning(
                f"Database lookup failed for '{metadata.title}' ({metadata.year}) "
                f"with format signals: {metadata.format_signals}"
            )
```

---

### 6.2 Validation (CRITICAL - P0)

**Create test suite:** `tests/test_kubrick_classification.py`

```python
def test_kubrick_with_format_signals():
    """Test that Core films with format signals are classified correctly"""

    test_cases = [
        {
            'filename': 'Dr.Strangelove.1964.Criterion.1080p.BluRay.x265.10bit.mkv',
            'expected_tier': 'Core',
            'expected_decade': '1960s',
            'expected_director': 'Stanley Kubrick'
        },
        {
            'filename': 'The.Shining.1980.35mm.Scan.FullScreen.HYBRID.OPEN.MATTE.1080p.mkv',
            'expected_tier': 'Core',
            'expected_decade': '1980s',
            'expected_director': 'Stanley Kubrick'
        },
        {
            'filename': '2001 - A Space Odyssey (1968) - 4K.mkv',
            'expected_tier': 'Core',
            'expected_decade': '1960s',
            'expected_year': 1968,  # NOT 2001!
            'expected_director': 'Stanley Kubrick'
        }
    ]

    classifier = FilmClassifierV01(project_path)

    for case in test_cases:
        metadata = classifier.parser.parse(case['filename'])
        result = classifier.classify(metadata)

        assert result.tier == case['expected_tier'], \
            f"FAIL: {case['filename']} → {result.tier} (expected {case['expected_tier']})"
        assert result.decade == case['expected_decade'], \
            f"FAIL: {case['filename']} → {result.decade} (expected {case['expected_decade']})"
        if 'expected_year' in case:
            assert metadata.year == case['expected_year'], \
                f"FAIL: {case['filename']} → year={metadata.year} (expected {case['expected_year']})"
```

**Run validation:**
```bash
pytest tests/test_kubrick_classification.py -v
```

---

### 6.3 Architecture Improvements (MEDIUM - P1)

#### Improvement 1: Fuzzy Matching with Confidence Scoring

Current system is binary: exact match OR heuristic.

**Proposed:** Add fuzzy matching tier between Pass 1 and Pass 2

```python
# Pass 1.5: Fuzzy matching for near-misses
if not result_from_pass_1:
    fuzzy_matches = self.lookup_db.fuzzy_lookup(metadata.title, metadata.year, threshold=0.85)
    if fuzzy_matches:
        # Return match with confidence score
        return ClassificationResult(..., confidence=0.85, reason='fuzzy_lookup')
```

#### Improvement 2: Classification Priority Order

**Current (Wrong):**
1. Core director check (requires director in filename)
2. Database lookup (fails if format signals present)
3. Format signals → Popcorn (overrides everything)

**Proposed (Correct):**
1. Database lookup (with symmetric normalization) [HIGHEST PRIORITY]
2. Core director check (via API enrichment if needed)
3. Reference canon check
4. Format signals → Popcorn [LOWEST PRIORITY]

**Rationale:** Explicit database entries should ALWAYS override heuristics.

#### Improvement 3: Add Audit Trail

```python
@dataclass
class ClassificationResult:
    # ...existing fields...

    # NEW: Audit trail
    lookup_attempted: bool = False
    lookup_query: Optional[str] = None
    lookup_result: Optional[str] = None
    fallback_reason: Optional[str] = None
```

This enables post-mortem analysis: "Why did this film go to Popcorn instead of Core?"

---

### 6.4 Process Improvements (LOW - P2)

#### Add Pre-flight Validation

Before running full classification:

```bash
# Validate database integrity
python scripts/validate_database.py

# Test parser on sample files
python scripts/test_parser.py --sample 100

# Dry run with verbose logging
python classify_v01.py /path/to/films --dry-run --verbose
```

#### Add Statistical Alerts

Monitor classification output for anomalies:

```python
# Alert if Popcorn rate > 10%
# Alert if Unsorted rate > 15%
# Alert if any Core director film goes to Popcorn (scan output for known directors)
```

---

## 7. Conclusion

The v0.1 classification system contains **fundamental logic flaws** that cause systematic misclassification of high-value films. The issues are:

- **70% Reasoning Problems:** Asymmetric normalization, missing fallback logic, wrong priority order
- **30% Precision Problems:** Parser regex ordering, missing function calls

**Impact Severity:** CRITICAL
- Core director films misclassified as Popcorn
- Films assigned to wrong decades
- Cannot trust classification statistics

**Deployment Recommendation:** ❌ **DO NOT DEPLOY**

**Required Actions:**
1. Implement Fix 1 (symmetric normalization) - BLOCKING
2. Implement Fix 2 (year parser priority) - BLOCKING
3. Create test suite - BLOCKING
4. Re-run classification on full dataset
5. Manual review of all Popcorn-tier films with format signals

---

## 8. Appendix: Evidence

### 8.1 Kubrick Misclassifications (from CSV)

```csv
original_filename,new_filename,title,year,director,tier,destination,reason

Dr.Strangelove.1964.Criterion.1080p.BluRay.x265.10bit.mkv,
Dr.Strangelove.1964.Criterion.1080p.BluRay.x265.10bit [Popcorn-1960s].mkv,
Dr Strangelove Criterion,1964,,Popcorn,Popcorn/1960s/,format_signal

The.Shining.1980.35mm.Scan.FullScreen.HYBRID.OPEN.MATTE.1080p.mkv,
The.Shining.1980.35mm.Scan.FullScreen.HYBRID.OPEN.MATTE.1080p [Popcorn-1980s].mkv,
The Shining 35mm Scan FullScreen HYBRID OPEN MATTE,1980,,Popcorn,Popcorn/1980s/,format_signal

2001 - A Space Odyssey (1968) - 4K.mkv,
2001 - A Space Odyssey (1968) - 4K [Popcorn-2000s].mkv,
A Space Odyssey (1968) -,2001,,Popcorn,Popcorn/2000s/,format_signal
```

### 8.2 Database Entries (from SORTING_DATABASE.md)

```markdown
## 1960s

### Core
- Dr. Strangelove (1964) → 1960s/Core/Stanley Kubrick/
- 2001: A Space Odyssey (1968) → 1960s/Core/Stanley Kubrick/

## 1980s

### Core
- The Shining (1980) → 1980s/Core/Stanley Kubrick/
```

### 8.3 Whitelist Confirmation

```bash
$ grep -i kubrick docs/CORE_DIRECTOR_WHITELIST_FINAL.md

## 1960s CORE
**Stanley Kubrick**

## 1970s CORE
**Stanley Kubrick**

## 1980s CORE
**Stanley Kubrick**

## 1990s CORE
**Stanley Kubrick**
```

---

**Report Complete**
**Next Step:** Review findings and approve fixes before implementation
