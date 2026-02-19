# Issue #25: Satellite classification integrity — eight defects in routing, matching, and enforcement

**Severity:** Medium (individually low-to-medium; collectively material)
**Components:** `lib/satellite.py`, `lib/omdb.py`, `lib/constants.py`, `lib/popcorn.py`, `classify.py`
**Type:** Implementation correctness — multiple independent defects in the Satellite layer
**Discovered via:** Architecture analysis (exports/knowledge-base)

---

## Summary

Eight defects in the satellite classification layer. None is individually catastrophic but together they represent a systematic quality problem: wrong films enter Satellite (false positives from substring matching and corrupt country codes), valid films never enter Satellite (missing decade, dead category), caps are enforced inconsistently, and dead code in the Popcorn module embeds a PRECISION operation inside a REASONING stage. All eight items have the same fix pattern: tighten the precision operation, document the constraint, add an assertion or test.

---

## Defect 1: Satellite director matching uses substring, not exact match

**Location:** `lib/satellite.py:103`

```python
if any(d in director_lower for d in rules['directors']):
```

The `in` operator performs a substring check. Any director whose normalised lowercase name *contains* a listed entry will match, regardless of whether they are actually that director.

**Examples of unsafe entries in `SATELLITE_ROUTING_RULES`:**

| Entry | Matches correctly | Also matches (false positive risk) |
|---|---|---|
| `'bava'` | "mario bava" | Any name containing "bava" (e.g. "Kurosabava" — unlikely but not impossible) |
| `'malle'` | "louis malle" | Any name containing "malle" |
| `'brass'` | "tinto brass" | "Christopher Brass", "Metal Brass" |
| `'lenzi'` | "umberto lenzi" | Any name ending in "lenzi" |
| `'duras'` | if added: "marguerite duras" | Any name containing "duras" |
| `'larry clark'` | "larry clark" | ✅ Multi-word strings are safe (substring match would require exact substring) |

Short single-word entries are the risk. `'bava'`, `'malle'`, `'brass'` are the three most likely to false-positive against real director names.

**Contrast with Core director matching** (`lib/core.py` / `CoreDirectorDatabase`), which uses exact NFC-normalised matching. Two different matching algorithms exist for the same conceptual operation (director identity check). This is an R/P split violation: director identity is a PRECISION task that should use the same algorithm everywhere.

**Fix:** Change `any(d in director_lower for d in rules['directors'])` to a word-boundary-aware match. The safest drop-in is to split `director_lower` into tokens and check whether any entry equals a token or a multi-token substring:

```python
director_tokens = set(director_lower.split())

def _director_matches(director_lower, director_tokens, entry):
    # Single-word entry: must match a whole word
    if ' ' not in entry:
        return entry in director_tokens
    # Multi-word entry: substring is fine (exact phrase)
    return entry in director_lower

if rules['directors'] and director:
    if any(_director_matches(director_lower, director_tokens, d) for d in rules['directors']):
        return self._check_cap(category_name)
```

This preserves the current behaviour for multi-word entries (`'larry clark'`, `'tsui hark'`, `'john woo'`, `'gordon parks'`, `'ringo lam'`) while requiring whole-word matching for single-word entries (`'bava'`, `'malle'`, `'lenzi'`, `'brass'`, etc.).

---

## Defect 2: OMDb country fallback produces silent corrupt country codes

**Location:** `lib/omdb.py:245-247`

```python
else:
    # Unknown country - just use first 2 letters uppercase as fallback
    codes.append(name[:2].upper() if len(name) >= 2 else name.upper())
```

When OMDb returns a country name not in the 40-entry `country_map` dict, `_map_countries_to_codes()` produces a 2-letter code by truncating the name. These corrupt codes flow silently into `merged['countries']` and are used by `SatelliteClassifier` and `COUNTRY_TO_WAVE` for routing decisions.

**Known problem inputs:**

| OMDb country string | Expected code | Fallback produces |
|---|---|---|
| `"West Germany"` | `DE` | `WE` |
| `"East Germany"` | `DE` (or separate) | `EA` |
| `"Soviet Union"` | `RU` (approx) | `SO` |
| `"Czechoslovakia"` | `CZ` (approx) | `CZ` ✅ (accident) |
| `"Yugoslavia"` | None clear | `YU` (in map) ✅ |
| `"Federal Republic of Germany"` | `DE` | `FE` |
| Any novel film nation | — | Unpredictable 2 letters |

The failure is silent: no log warning, no `None` return, no downstream signal. A film that OMDb reports as "West German" silently produces `WE` as its country code. `WE` does not appear in `COUNTRY_TO_WAVE` or any `SATELLITE_ROUTING_RULES['country_codes']`, so the film correctly falls through — but the absence of routing is indistinguishable from correct-absence and incorrect-absence. There is no way to know, from the manifest, that the country was corrupt.

**Fix — two parts:**

**Part A:** Expand `country_map` with historical nation names known to appear in OMDb data:
```python
'West Germany': 'DE',
'East Germany': 'DE',
'Federal Republic of Germany': 'DE',
'Soviet Union': 'RU',
'Czechoslovakia': 'CZ',
'Yugoslavia': 'YU',  # already in map — verify
```

**Part B:** Replace the silent fallback with a logged `None`:
```python
else:
    logger.warning(f"OMDb: unknown country name '{name}' — skipping (no country code mapped)")
    # Do not append anything; return only codes we know are correct
```

Returning `None`/skipping is better than a corrupt code because it converts a silent wrong answer into a transparent absence. A film with no country (rather than corrupt country) will correctly fall through to Unsorted with `reason='unsorted_no_match'`, which is auditable.

---

## Defect 3: Language-to-country mapping collapses national distinctions

**Location:** `lib/constants.py:132-145`

```python
LANGUAGE_TO_COUNTRY = {
    'pt': 'BR',   # Portuguese → Brazil
    'zh': 'HK',   # Chinese → Hong Kong
    'es': 'ES',   # Spanish → Spain
    ...
}
```

This mapping is used by `lib/parser.py` to derive a country code when no explicit country is available. The mapping embeds three hard assumptions about collection context:

| Language | Mapped to | Problem case |
|---|---|---|
| Portuguese | `BR` (Brazil) | Portuguese European films (1960s-1970s) route to `BR` → Brazilian Exploitation |
| Chinese (any) | `HK` (Hong Kong) | Mainland Chinese and Taiwanese films route to `HK` → Hong Kong Action |
| Spanish | `ES` (Spain) | Latin American films (Argentina, Mexico, Chile) route to `ES`, which has no Satellite routing |

**Concrete examples:**
- A 1968 Portuguese film by Manoel de Oliveira is parsed as language=`pt` → country=`BR` → decade=1960s → routes to `Satellite/Brazilian Exploitation/1960s/`. Oliveira is Portuguese, not Brazilian.
- A 2002 Zhang Yimou film is parsed as language=`zh` → country=`HK` → decade=2000s → HK Action decades are `1970s-1990s`, so it falls through. Correct result, wrong path (country was `HK` not `CN`).
- A 1968 Argentine film by Leopoldo Torre Nilsson routes to `ES`, which has no `COUNTRY_TO_WAVE` or `SATELLITE_ROUTING_RULES` entry — falls through to Unsorted. This may be correct but the country signal is wrong.

The comments in `LANGUAGE_TO_COUNTRY` acknowledge the limitation (`# for this collection's context`) but do not document the failure modes or explain where the collection-context assumption breaks down.

**Fix:** This mapping cannot be made universally correct without film-specific knowledge. The appropriate fix is:

1. Add warning comments documenting the three known failure modes
2. Add `LANGUAGE_TO_COUNTRY_NOTES` as a dict or comment block explaining when API data should override the language-derived country
3. Ensure that in `_merge_api_results()`, API-derived country **always** overwrites language-derived country (currently `if not metadata.country` — this already works correctly; the problem is when API data is absent)
4. Consider adding `'pt-pt': 'PT'` as a more specific Portuguese-Portugal pattern if the parser can distinguish it from Brazilian Portuguese in filenames (e.g. `"pt-pt audio"` vs `"br audio"`)

---

## Defect 4: `Cult Oddities` has a cap but no routing rules — unreachable category

**Location:** `lib/satellite.py:39`, `lib/constants.py:SATELLITE_ROUTING_RULES`

```python
# satellite.py:39
self.caps = {
    ...
    'Cult Oddities': 50,
}
```

`Cult Oddities` appears in `self.caps` with a cap of 50. It does not appear anywhere in `SATELLITE_ROUTING_RULES` in `lib/constants.py`. The `classify()` method iterates `SATELLITE_ROUTING_RULES` — categories not in that dict are never evaluated. No film can ever be classified as `Cult Oddities` through the normal pipeline.

This is dead configuration: the cap exists, counts would be tracked, but the category can never be reached.

**Two possible resolutions:**

**Option A: Design the routing rules for `Cult Oddities`** — Define what country codes, decades, genres, and directors constitute a Cult Oddity. This is a non-trivial curatorial decision (it requires a definition of what the category contains).

**Option B: Remove the cap entry** — If `Cult Oddities` is not yet designed, remove it from `self.caps` to eliminate confusion. Add a `# TODO: define routing rules before adding cap` comment.

If `Cult Oddities` is intended to be human-curated only (via `SORTING_DATABASE.md`), document that explicitly: `# Human-curated only — not auto-classified. Entries must be in SORTING_DATABASE.md.`

---

## Defect 5: Blaxploitation `decades` list skips the 1980s

**Location:** `lib/constants.py:282`

```python
'Blaxploitation': {
    'country_codes': ['US'],
    'decades': ['1970s', '1990s'],  # Extended to include 1990s for Ernest Dickerson
    ...
}
```

The comment notes the 1990s extension for Ernest Dickerson but does not explain the 1980s absence. The Blaxploitation movement peaked in the early-to-mid 1970s but the 1980s produced relevant films: *Beat Street* (1984), *Krush Groove* (1985), *Tougher Than Leather* (1988), and several others that sit in the cultural continuum of the movement.

This may be intentional — the 1980s was the transition to hip-hop era, which is distinct enough to justify the gap — but without a comment, it looks like an error. Any 1980s film with US country, matching genres, and a title keyword match (`BLAXPLOITATION_TITLE_KEYWORDS`) will fall through to American Exploitation rather than Blaxploitation.

**Fix:** Either add `'1980s'` to the decades list, or add a comment explaining the deliberate exclusion:

```python
'decades': ['1970s', '1990s'],
# 1980s excluded by design: the movement peaked 1970-1975 and dissolved by ~1978.
# 1980s US exploitation films route to American Exploitation.
# 1990s included specifically for Ernest Dickerson (Juice 1992, Surviving the Game 1994).
```

---

## Defect 6: Reference canon count is not enforced

**Location:** `lib/constants.py:498-559`

The `REFERENCE_CANON` dict currently has 57 entries (58 including the dual-normalisation entry for E.T.). `CLAUDE.md §3 Rule 2` and the inline comment both state "50-film hardcoded list". There is no assertion anywhere that enforces this.

The count has silently exceeded 50 at some point. There is no record of when or which films pushed it over, because no gate exists to catch it.

**Concrete count:**
```
1930s-1940s: 10 entries
1950s: 14 entries
1960s: 5 entries
1970s: 7 entries
1980s-1990s: 21 entries (including 1 duplicate normalisation)
Total: 57 unique films + 1 duplicate = 58 dict entries
```

**Fix:** Add a module-level assertion immediately after the `REFERENCE_CANON` dict definition:

```python
# Enforce the 50-film cap. If this assertion fails, you have added too many entries.
# The cap is a curatorial constraint: Reference is a curated canon, not a comprehensive list.
# Remove lower-priority entries before adding new ones.
_UNIQUE_REFERENCE_FILMS = len({title for title, _ in REFERENCE_CANON.keys()})
assert _UNIQUE_REFERENCE_FILMS <= 50, (
    f"REFERENCE_CANON has {_UNIQUE_REFERENCE_FILMS} unique films (cap is 50). "
    f"Remove entries before adding new ones."
)
```

This assertion fires at import time, making it impossible to silently exceed the cap.

Separately, decide whether the current 57-film list should be pruned back to 50, or whether the cap should be updated to 60 (if the original 50 was arbitrary). Document the decision.

---

## Defect 7: Satellite caps not enforced for explicit lookup path

**Location:** `classify.py:455-457`

```python
if parsed['tier'] == 'Satellite' and parsed.get('subdirectory'):
    self.satellite_classifier.increment_count(parsed['subdirectory'])
```

When `SORTING_DATABASE.md` returns a Satellite destination, `increment_count()` is called to track the category count. But `increment_count()` only increments — it does not check the cap:

`lib/satellite.py:150-151`:
```python
def increment_count(self, category: str):
    """Increment count for explicit lookup results"""
    if category in self.caps:
        self.counts[category] += 1
```

The cap check only runs in `_check_cap()` (`satellite.py:138-148`), which is only called from `classify()`. Explicit lookup entries can silently push a category over its cap.

**Example:** Giallo has a cap of 30. The `SORTING_DATABASE.md` has 35 Giallo entries. All 35 will be routed to `Satellite/Giallo/` and counted, but the cap check never fires for lookup entries. The category can reach 35 in the manifest while the `self.counts['Giallo']` counter would hit 35 and all *subsequent heuristic* classifications of new films would be blocked — but the 35 already in the manifest are not retroactively affected.

This creates an inconsistency between the cap's intent (limit total Giallo films in the collection) and its actual enforcement (limits only heuristic new classifications, not lookup-sourced ones).

**Fix:** Modify `increment_count()` to return a boolean indicating whether the cap was exceeded, and handle the over-cap case at the callsite:

```python
def increment_count(self, category: str) -> bool:
    """Increment count for explicit lookup results. Returns False if cap exceeded."""
    if category not in self.caps:
        return True
    if self.counts[category] >= self.caps[category]:
        logger.warning(f"Category '{category}' at cap ({self.caps[category]}) — explicit lookup entry exceeds cap")
        return False  # Over cap — caller can decide whether to warn or proceed
    self.counts[category] += 1
    return True
```

Note: explicit lookup entries should probably *not* be blocked by the cap (the human chose those entries deliberately). The fix should at minimum log a warning when the cap is exceeded via the lookup path, and the cap's docstring should clarify whether it applies to lookup entries or only heuristic entries.

---

## Defect 8: `popcorn.py` re-queries the lookup DB — dead code inside a REASONING stage

**Location:** `lib/popcorn.py:48-52`

```python
if self.lookup_db and getattr(metadata, 'title', None):
    dest = self.lookup_db.lookup(metadata.title, film_year)
    if dest and 'Popcorn' in dest:
        return 'popcorn_lookup'
```

`PopcornClassifier.classify_reason()` is called at Stage 6 (`classify.py:550`). By that point, Stage 2 of the pipeline has already checked `SORTING_DATABASE.md` (`classify.py:442-468`). If the lookup had found a match, the pipeline would have returned at Stage 2 and never reached Stage 6. Therefore, by the time `popcorn.py:49` is reached, either:
- The film is not in `SORTING_DATABASE.md` → `lookup_db.lookup()` returns `None` → the branch never fires
- OR `lookup_db` is `None` → the condition is False immediately

`return 'popcorn_lookup'` is unreachable code. The lookup is a PRECISION operation (`lib/normalization.py` + dict match) embedded inside a REASONING module. This violates the R/P split principle.

**Fix:** Remove lines 48-52 from `popcorn.py`. The `lookup_db` injection in `PopcornClassifier.__init__()` can also be removed. If a lookup-based Popcorn classification is needed, it should remain in Stage 2 of `classify.py`, not in the Popcorn REASONING module.

Before removing, add a test that verifies a Popcorn lookup entry is caught at Stage 2 (not Stage 6) to confirm the removal is safe.

---

## Acceptance Criteria

- [ ] **D1:** Satellite director matching uses whole-word matching for single-word entries; substring matching only for multi-word entries; existing tests pass
- [ ] **D2:** OMDb `_map_countries_to_codes()` logs a warning and returns no code for unknown country names; `country_map` extended with West Germany, East Germany, Soviet Union, Czechoslovakia
- [ ] **D3:** `LANGUAGE_TO_COUNTRY` has comments documenting the three known failure modes (PT→BR, ZH→HK, ES→ES)
- [ ] **D4:** `Cult Oddities` either has defined routing rules or its cap entry is removed with a comment explaining its intended use
- [ ] **D5:** Blaxploitation 1980s either added with justification or absence is commented as a deliberate decision
- [ ] **D6:** `assert len(REFERENCE_CANON) <= 50` (or adjusted cap) added at module level; current over-count resolved by pruning or cap update
- [ ] **D7:** `increment_count()` logs a warning when an explicit lookup entry exceeds the cap; docstring clarifies cap scope
- [ ] **D8:** Dead lookup code removed from `popcorn.py`; test confirms Popcorn lookup entries are caught at Stage 2
