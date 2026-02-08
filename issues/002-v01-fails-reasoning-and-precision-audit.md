# Issue #002: v0.1 Fails Reasoning & Precision Principles — Full Audit

**Priority:** Blocking
**Type:** Bug / Architecture
**Status:** Open

---

## Context

v0.1 (`classify_v01.py`) was built to be the stripped-down, near-100% accuracy foundation. The whole point was: if we classify a film, we're right. Everything else goes to Unsorted.

It's not doing that. The effectiveness report flagged Kubrick misclassifications, but the problems are structural. This isn't a bug-fix situation — the code violates its own stated principles at multiple levels.

---

## Audit: Every module against Reasoning & Precision

### What "Reasoning" and "Precision" mean here

- **Reasoning:** Does the code's logic actually follow from its stated intent? Does each step's output feed correctly into the next step's input? Are assumptions validated?
- **Precision:** Does the code handle the exact data it will encounter? Are transformations symmetric? Do edge cases get caught or silently corrupt?

---

## 1. `lib/parser.py` — FAILS PRECISION

### Problem: Year-prefix regex matches film titles that start with numbers

**Line 111:**
```python
year_prefix_match = re.match(r'^(\d{4})\s+-\s+(.+)', name)
```

This is meant for Brazilian format: `1976 - Amadas e Violentadas`

But it matches: `2001 - A Space Odyssey (1968) - 4K.mkv`
- Extracts year = **2001** (the title, not the year)
- Extracts title = `A Space Odyssey (1968) - 4K`
- The actual year (1968) is buried in the title string and never used

This isn't an edge case. "2001" is one of the most famous films ever made. The regex has no guard for "does this string also contain a parenthetical year that should take priority?"

### Problem: `_clean_title()` truncates at first release tag match

**Lines 60-65:**
```python
for tag in self.RELEASE_TAGS:
    idx = title_lower.find(tag)
    if idx != -1:
        title = title[:idx]
```

This finds the tag position in a lowered copy but truncates the original. Fine. But the issue is the tag list includes `'hd'` which matches inside words like `Shahid`, `Richard`, or anything with "hd" in it. And `'remastered'` appears in both `FORMAT_SIGNALS` and `RELEASE_TAGS` — so it gets detected as a format signal (Popcorn routing) AND stripped from the title (lookup mismatch).

### Problem: Format signals detected BEFORE title cleaning

**Lines 105-108** (format signal extraction) run before **lines 110-161** (pattern matching and title cleaning). So format signals are detected on the raw filename, which is correct. But the title that gets returned still contains format signal words, because `_clean_title()` only strips `RELEASE_TAGS`, not `FORMAT_SIGNALS`.

The title "Dr Strangelove Criterion" gets passed to lookup. The database has "Dr Strangelove". No match.

**This is the root cause of the Kubrick failures.** The parser produces titles contaminated with format signal words, and the lookup system doesn't strip them from queries.

---

## 2. `lib/lookup.py` — FAILS REASONING

### Problem: Asymmetric normalization (the core bug)

**Database building (line 102):**
```python
title_raw = self._strip_format_signals(title_raw)
title = self._normalize_title(title_raw)
```

**Query (line 172):**
```python
normalized = self._normalize_title(title)
```

The database strips format signals, then normalizes. The query normalizes but never strips format signals. The operations are not symmetric. This violates the most basic property of a lookup system: the key you store under and the key you search with must go through identical transformations.

This isn't a missing function call. It's a reasoning failure. The developer who wrote `_strip_format_signals` understood the problem well enough to write the function — then didn't apply it on the query side.

### Problem: `_strip_format_signals` is incomplete

**Lines 49-64:** The function handles `criterion`, `35mm`, `open matte`, etc. But the parser's `FORMAT_SIGNALS` list (parser.py line 37-42) also includes `4k`, `uhd`, `remux`, `commentary`, `special edition`, `remastered`, `restored`, `anniversary`. These aren't in `_strip_format_signals`. So even if you fix the asymmetry, some format signals will still contaminate lookups.

Two different modules maintain two different lists of format signals. They will always drift.

---

## 3. `classify_v01.py` — FAILS REASONING

### Problem: Priority order defeats the stated design

The docstring says:
```
Pass 1: Known films (exact matches only)
  - Core director exact match
  - Explicit lookup in SORTING_DATABASE.md
Pass 2: Simple signals or Unsorted
  - Format signals → Popcorn
  - Everything else → Unsorted
```

But look at what actually happens for a Core director film with format signals (e.g., The Shining 35mm):

1. **Core director check (line 113):** Requires `metadata.director`. Parser almost never extracts director from filenames (only works for `Director - Title (Year)` format). Most filenames are `Title.Year.Tags.mkv`. So `metadata.director` is None. **Check skipped.**

2. **Explicit lookup (line 134):** Title contains format signal words ("The Shining 35mm Scan FullScreen HYBRID OPEN MATTE"). Lookup database has "the shining". **No match.** Check fails.

3. **Format signal check (line 154):** Format signals were detected. Film has a year. **Routes to Popcorn.**

The Core director check is almost useless because filenames rarely contain director names. The explicit lookup is broken by format signal contamination. So the only check that fires is the lowest-priority one — format signals — which catches everything that has a special edition tag.

**The irony:** The films most likely to have format signals (35mm, Criterion, 4K) are the films you care most about (Core auteur films, Reference canon). The system systematically misclassifies your most curated films.

### Problem: Popcorn as catch-all for format signals

**Lines 153-168:** Any film with any format signal goes to Popcorn. No check for "is this film already in the database?" No check for "is this director on any list?" The format signal check is a blind catch-all that doesn't know about any other classification layer.

v0.1 was supposed to say: "If I can't match it exactly, it goes to Unsorted." Instead it says: "If it has 35mm in the filename, it's Popcorn." That's not a binary sort — it's a heuristic, and a wrong one.

---

## 4. `lib/core_directors_v01.py` — PASSES (mostly)

This module actually follows the v0.1 principles correctly:
- Exact case-insensitive match via dict lookup (line 85)
- O(1) performance
- No fuzzy matching

**One issue:** `get_director_decade()` (line 99-122) returns None if the director exists but isn't listed in the film's decade. E.g., if Kubrick is listed under 1960s/1970s/1980s/1990s but not 2000s, a Kubrick film from 2005 gets None back, and the Core classification fails silently. This is arguably correct (Kubrick died in 1999) but the failure is silent — no log, no warning.

---

## 5. `lib/popcorn.py` — FAILS REASONING

### Problem: Double-dips on lookup

**Lines 38-43:**
```python
if self.lookup_db and hasattr(metadata, 'title'):
    dest = self.lookup_db.lookup(metadata.title, film_year)
    if dest and 'Popcorn' in dest:
        return True
```

The Popcorn classifier runs its own lookup against SORTING_DATABASE.md. But `classify_v01.py` already ran a lookup at line 134-135. If the first lookup failed (because of format signal contamination), this one will fail too — same bug, same input, same result.

And if the first lookup succeeded, the film was already classified and Popcorn never runs. So this lookup call is either redundant or broken. It never adds value.

### Problem: Any format signal = Popcorn

**Lines 46-49:** If the film has ANY format signal from a list of 15+ signals, it's Popcorn. `criterion` is a format signal. `remastered` is a format signal. `4k` is a format signal. These are present in art films, core auteur films, reference films — they're not Popcorn signals, they're curation signals. The assumption "format signal = Popcorn" is wrong.

---

## 6. Cross-Module: Single Source of Truth Violations

| Concept | Defined in | Also defined in | Conflict? |
|---|---|---|---|
| Format signals | `parser.py` lines 37-42 (15 items) | `lookup.py` lines 49-64 (10 items) | YES — different lists |
| Format signals | `parser.py` lines 37-42 | `popcorn.py` lines 16-21 (16 items) | YES — different lists |
| Release tags to strip | `parser.py` lines 45-51 | nowhere else | One module cleans, others don't |
| Title normalization | `lookup.py` `_normalize_title()` | `parser.py` `_clean_title()` | YES — different algorithms |

Three modules clean titles three different ways. Parser strips dots and release tags. Lookup strips accents, punctuation, and format signals (on intake only). Popcorn doesn't clean at all.

When Parser hands a title to Lookup, the title has been cleaned by Parser's rules but not Lookup's rules. The two cleaning algorithms are not composable or even compatible.

---

## Summary: What's Actually Wrong

This isn't a list of bugs. It's a pattern:

1. **No contract between modules.** Parser produces titles in one format. Lookup expects them in another. Neither module documents what format it expects or produces. There's no shared `normalize()` function.

2. **No single source of truth for format signals.** Three modules maintain three lists. They're already different and will only drift further.

3. **The priority order is correct on paper but broken in practice.** Core director check can't fire because filenames don't have directors. Lookup can't match because titles are contaminated. Popcorn catches everything by default.

4. **Format signals are treated as classification when they're metadata.** Whether a film is 35mm or Criterion tells you about the *edition*, not the *tier*. A 35mm scan of Breathless is Core. A 35mm scan of Die Hard is Popcorn. The format signal is orthogonal to classification.

---

## What Needs to Happen

### Principle 1: One normalization function, used everywhere

A single `normalize_for_lookup(raw_title) -> clean_title` function that:
- Strips format signals (one canonical list)
- Strips release tags
- Lowercases
- Removes punctuation and accents
- Collapses whitespace

Used by: parser output, lookup intake, lookup query. Same function, same list, same result.

### Principle 2: Format signals are metadata, not classification

Format signals get extracted and stored on the metadata object (already happening). They do NOT trigger tier classification. They're available for display, for manual review, for future Popcorn logic — but they don't route films.

### Principle 3: If lookup fails, the answer is Unsorted, not Popcorn

v0.1's entire premise: "If I can't match it exactly, I don't classify it." The format signal catch-all violates this. Remove it. If a film doesn't match Core director (exact) or explicit lookup, it's Unsorted. Period.

### Principle 4: Fix the parser's year extraction

Parenthetical year `(1968)` always takes priority over leading digits `2001 - ...`. Check for parens first. Only fall through to year-prefix if no parenthetical year exists.

### Principle 5: Director-less classification needs lookup, not director matching

Most filenames don't contain directors. The Core director check will almost never fire. The explicit lookup table IS the primary classification mechanism for v0.1. If you fix the lookup (symmetric normalization), the system works because SORTING_DATABASE.md already maps Kubrick films to Core. You don't need the director check to be the hero — you need the lookup to not be broken.

---

## Acceptance Criteria

- [ ] Single `normalize()` function shared across all modules
- [ ] Single `FORMAT_SIGNALS` list imported from one location
- [ ] Lookup query uses identical normalization as lookup intake
- [ ] Parser prefers parenthetical year over leading-digit year
- [ ] Format signals do NOT trigger Popcorn classification
- [ ] Any film not matched by Core exact or explicit lookup → Unsorted
- [ ] Test: all 3 Kubrick films from the report classify correctly
- [ ] Test: "2001 - A Space Odyssey (1968)" extracts year=1968
- [ ] Test: "Dr.Strangelove.1964.Criterion.1080p.BluRay.x265.10bit.mkv" matches lookup
