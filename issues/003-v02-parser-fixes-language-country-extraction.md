# Issue #003: v0.2 — Parser Fixes, Language/Country Extraction, and User Tag Recovery

**Priority:** Critical
**Type:** Feature / Bug Fix
**Status:** Open
**Blocking:** v0.3 (TMDb enrichment) depends on clean titles from this work

---

## Problem

v0.1 classifies **112 of 1,202 films (9.3%)**. The remaining 1,090 are Unsorted. Analysis shows the bottleneck is NOT the Reference tier (+15 films) — it's a combination of:

1. **Parser bugs** producing garbled/empty titles → films that ARE in the database can't match (~90 films)
2. **No language/country extraction** → hundreds of films with clear origin signals sit in Unsorted when they could route to Satellite waves by decade + country
3. **127 user-tagged films ignored** → filenames already contain `[Popcorn-1970s]` or `[Core-Scorsese]` tags that the system strips but never reads
4. **Hardcoded Reference tier missing** (original v0.2 scope — ~35 films)

Combined estimated impact: **~270-350 films classified**, taking coverage from 9.3% to ~30-35%.

---

## Root Cause Analysis

### A. Parser Bugs (3 distinct bugs, ~160 films affected)

#### Bug 1: "Title (Year) - Resolution" → Empty Title (~46 films)

```
Input:  "Casablanca (1942) - 4K [Popcorn-1940s].mkv"
Parsed: director="Casablanca (1942)", title="", year=1942
```

The `Director - Title (Year)` regex (`^(.+?)\s+-\s+(.+)`) matches the dash before "4K" and puts the real title into the director field. Affects: Casablanca, Chinatown, Pulp Fiction, Serpico, Blood Simple, Battle Royale, Miller's Crossing, Blow Out, Coffy, Clue, Weird Science, Spider-Man, Tombstone, The Apartment, Deliverance, Juice, Miracle Mile, and ~30 more.

**Many of these ARE in SORTING_DATABASE.md** but can't match because the title is empty.

#### Bug 2: "Series - Subtitle (Year)" → Swapped Fields (~44 films)

```
Input:  "Cinema Paradiso - Theatrical Cut (1988) - 4K.mkv"
Parsed: director="Cinema Paradiso", title="Theatrical Cut -", year=1988
```

Series names, franchise titles, and films with subtitles get their name treated as the director. Affects: Stray Cat Rock series (5 films), Cinema Paradiso, Leon the Professional, Dances with Wolves, Braindead, From Beyond, The Godfather HBO cut, and ~30 more.

#### Bug 3: "(Director, Year)" Pattern Not Handled (~30-40 films)

```
Input:  "A Bay of Blood (Mario Bava, 1971).mkv"
Parsed: director="", title="A Bay of Blood", year="" (no year extracted)
```

Filenames in the `(Director Name, Year)` format — common in curated collections — yield no year and no director. Affects: A Bay of Blood, Attack of the 50ft Woman, Comizi d'amore, Noite Em Chamas, Louie Bluie, and ~25 more.

### B. No Language/Country Extraction (hundreds of films)

The parser extracts title, year, director, and format_signals. It does **not** extract language or country, despite many filenames containing clear signals:

**Language signals found in filenames:**
- `"In French"`, `"(French)"`, `"-french"`
- `"Dual IT and EN audio"`, `"Dual IT and EN"`
- `"em Português"`, `"Portuguese"`
- `"Malayalam"`, `"CHINESE"`, `"KOREAN"`
- `"Spanish audio with English subtitles"`
- `"Japanese"`, `"Dual Audio"`

**Country/region signals found in filenames:**
- `CHINESE` (appears in 10+ HK/Chinese films — Peking Opera Blues, A Touch of Zen, Curry and Pepper, The Heroic Trio, etc.)
- `KOREAN` (The Good the Bad the Weird, etc.)
- `Portuguese` / `em Português` (Brazilian films — Mango Yellow, A Força dos Sentidos, etc.)
- `Italian` / `IT` (Giallo and Italian exploitation)
- `French` (French New Wave and European art cinema)

**These signals map directly to Satellite wave categories:**

| Language/Country Signal | → Satellite Category | Decade Filter |
|---|---|---|
| CHINESE, Cantonese, Mandarin | Hong Kong Action | 1970s-1990s |
| Japanese, JP | Pinku Eiga | 1960s-1980s |
| Italian, IT (+ horror/thriller signals) | Giallo | 1960s-1980s |
| Portuguese, PT, Brazilian | Brazilian Exploitation | 1970s-1980s |
| French, FR (+ sexploitation signals) | European Sexploitation | 1960s-1980s |
| Korean, KR | (new category or Cult Oddities) | — |
| Malayalam, Hindi, Tamil | (new category or Cult Oddities) | — |

### C. User-Applied Tier Tags Ignored (127 films)

127 unsorted films already have user-applied classification tags in their original filenames:

| Tag Pattern | Count |
|---|---|
| `[Popcorn-{decade}]` | 87 |
| `[{decade}-Satellite-{category}]` | 20 |
| `[{decade}-Core-{director}]` | 12 |
| `[{decade}-Reference]` or `[Reference]` | 7 |
| `[Staging]` | 1 |

Examples:
- `Detour.1945.Criterion....[Popcorn-1940s].mkv` → should be Popcorn/1940s/
- `Dog Day Afternoon (1975)...[1970s-Reference].mkv` → should be Reference/1970s/
- `Who's that Knocking at My Door_ (1967)...[Popcorn-1960s].mkv` → should be Popcorn/1960s/

These are the user's own curatorial decisions already encoded in the filenames. The system currently strips bracket content during parsing but never reads it as a classification hint.

### D. Hardcoded Reference Tier (original v0.2 scope, ~15 net new films)

50 Reference canon films documented in `docs/REFERENCE_CANON_LIST.md`. Only 8 currently matched via explicit_lookup. The existing `lib/reference_canon.py` uses fuzzy matching (violates v0.1 principles). Needs a simple exact-match check added to the classify pipeline.

---

## Proposed Solution

### Phase 1: Parser Fixes (rescue ~160 films already in database)

#### Fix 1: "Title (Year) - Resolution" bug
In `lib/parser.py`, when the dash-split pattern matches `Director - Title`:
- If the "director" segment contains a parenthetical year like `(1942)`, treat the whole segment as the **title**, not director
- The dash was separating title from resolution info, not director from title

```
Before: "Casablanca (1942) - 4K" → director="Casablanca (1942)", title=""
After:  "Casablanca (1942) - 4K" → director="", title="Casablanca", year=1942
```

#### Fix 2: "Series - Subtitle (Year)" bug
When dash-split produces a "director" that:
- Is multi-word AND
- Contains no known director name (not in Core whitelist) AND
- The "title" part looks like a subtitle (short, generic words like "Theatrical Cut", "Director's Cut")

Then treat the first segment as part of the title, not as director.

#### Fix 3: "(Director, Year)" pattern
Add a new regex pattern to handle `(Name, Year)` parentheticals:
```python
# Pattern: "Title (Director Name, Year)"
match = re.search(r'\(([^,]+),\s*(\d{4})\)', filename)
```
Extract both director and year from the parenthetical.

### Phase 2: Language/Country Extraction

#### Add to `lib/constants.py`:

```python
# Language signal → ISO country code mapping
LANGUAGE_TO_COUNTRY = {
    # East Asian
    'chinese': 'CN', 'cantonese': 'HK', 'mandarin': 'CN',
    'japanese': 'JP', 'korean': 'KR',
    # European
    'french': 'FR', 'italian': 'IT', 'german': 'DE',
    'spanish': 'ES', 'portuguese': 'BR',  # Default to BR for Portuguese in this collection
    # South Asian
    'malayalam': 'IN', 'hindi': 'IN', 'tamil': 'IN',
    'bengali': 'IN',
    # Other
    'swedish': 'SE', 'danish': 'DK', 'norwegian': 'NO',
    'russian': 'RU', 'polish': 'PL', 'czech': 'CZ',
    'turkish': 'TR', 'thai': 'TH',
}

# Patterns to detect language/country in filenames
LANGUAGE_PATTERNS = [
    r'\b(?:in\s+)?(french|italian|japanese|chinese|korean|portuguese|spanish|german|swedish|russian|malayalam|hindi|tamil|bengali|cantonese|mandarin|turkish|thai)\b',
    r'\b(CHINESE|KOREAN|JAPANESE|FRENCH|ITALIAN|GERMAN|SPANISH|PORTUGUESE|RUSSIAN|SWEDISH)\b',
    r'\bDual\s+(IT|FR|DE|ES|PT|JP|CN|KR)\s+and\s+EN\b',
    r'\bem\s+(Português|Francês|Italiano)\b',
    r'\b(Português|Francês)\b',
]

# Country code → Satellite wave mapping (with decade constraints)
COUNTRY_TO_WAVE = {
    'HK': {'category': 'Hong Kong Action', 'decades': ['1970s', '1980s', '1990s']},
    'CN': {'category': 'Hong Kong Action', 'decades': ['1970s', '1980s', '1990s']},
    'JP': {'category': 'Pinku Eiga', 'decades': ['1960s', '1970s', '1980s']},
    'IT': {'category': 'Giallo', 'decades': ['1960s', '1970s', '1980s']},
    'BR': {'category': 'Brazilian Exploitation', 'decades': ['1970s', '1980s']},
    'FR': {'category': 'European Sexploitation', 'decades': ['1960s', '1970s', '1980s']},
    'DE': {'category': 'European Sexploitation', 'decades': ['1960s', '1970s', '1980s']},
}
```

#### Add to `lib/parser.py`:
- New `_extract_language()` method that scans filename against `LANGUAGE_PATTERNS`
- Returns detected language string and mapped country code
- Add `language` and `country` fields to `FilmMetadata` dataclass

#### Add to `classify_v01.py`:
- New Pass 2 (before Unsorted fallback): Country/language + decade → Satellite wave routing
- Only routes when country+decade matches a known wave (high confidence)
- Films with country signals outside known wave decades → still Unsorted (no guessing)

### Phase 3: User Tag Recovery (127 films, instant wins)

#### Add to `lib/parser.py`:
- New `_extract_user_tags()` method
- Parse bracket patterns: `[Popcorn-1970s]`, `[1980s-Satellite-Brazilian]`, `[Core-Scorsese]`, `[Reference]`
- Add `user_tag` field to `FilmMetadata`

#### Add to `classify_v01.py`:
- New check (after explicit_lookup, before country routing): if `metadata.user_tag` exists, use it as classification
- Reason: `user_tag_recovery`
- This respects the user's own curatorial decisions

### Phase 4: Hardcoded Reference Tier (~15 net new films)

- Add a `REFERENCE_CANON` dict to `lib/constants.py` (title → year mapping for ~50 films)
- Add exact title+year check in `classify_v01.py` after explicit_lookup
- NO fuzzy matching — consistent with v0.1/v0.2 principles
- Route matches to `Reference/{Decade}/`

---

## Implementation Order

| Step | What | Impact | Effort | Dependencies |
|---|---|---|---|---|
| 1 | Parser Bug 1: "Title (Year) - Resolution" | ~46 films rescued | Low | None |
| 2 | Parser Bug 2: "Series - Subtitle (Year)" | ~44 films rescued | Low | None |
| 3 | User tag recovery | 127 films classified | Low | None |
| 4 | Language/country constants + parser extraction | Foundation for Step 5 | Medium | None |
| 5 | Country+decade → Satellite wave routing | ~50-100+ films classified | Medium | Step 4 |
| 6 | Parser Bug 3: "(Director, Year)" pattern | ~30-40 films rescued | Low | None |
| 7 | Hardcoded Reference tier | ~15 films classified | Low | None |

Steps 1-3 are independent and can be done in parallel.
Steps 4-5 are sequential.
Steps 6-7 are independent of everything else.

---

## Acceptance Criteria

- [ ] Parser Bug 1 fixed: "Casablanca (1942) - 4K" → title="Casablanca", year=1942, director=""
- [ ] Parser Bug 2 fixed: "Cinema Paradiso - Theatrical Cut (1988)" → title="Cinema Paradiso", year=1988
- [ ] Parser Bug 3 fixed: "A Bay of Blood (Mario Bava, 1971)" → title="A Bay of Blood", director="Mario Bava", year=1971
- [ ] Language/country extraction: "Peking.Opera.Blues.1986.CHINESE.1080p" → country="CN"
- [ ] Language/country extraction: "Mississippi Mermaid (1969) In French" → country="FR"
- [ ] Language/country extraction: "Pistol for Ringo (1965) Dual IT and EN audio" → country="IT"
- [ ] Country+decade routing: CN + 1986 → Satellite/Hong Kong Action/1980s/
- [ ] Country+decade routing: FR + 1969 → only routes if fits a known wave, otherwise Unsorted
- [ ] User tags recovered: `[Popcorn-1970s]` → Popcorn/1970s/
- [ ] User tags recovered: `[1980s-Core-Martin Scorsese]` → Core/1980s/Martin Scorsese/
- [ ] Reference canon: Citizen Kane (1941) → Reference/1940s/ (exact match only)
- [ ] All changes validated against full 1,202-film collection
- [ ] 0 regressions on existing 112 classified films
- [ ] Classification rate rises from 9.3% to ≥25%
- [ ] Output CSV includes new columns: `language`, `country`, `user_tag`
- [ ] No external API calls (TMDb deferred to v0.3)
- [ ] Runs in under 10 seconds for full collection

---

## Test Cases

### Parser Bug 1
```
"Casablanca (1942) - 4K [Popcorn-1940s].mkv"         → title="Casablanca", year=1942
"Chinatown (1974) - 4K.mkv"                           → title="Chinatown", year=1974
"Pulp Fiction (1994) - 1080p.mkv"                      → title="Pulp Fiction", year=1994
"Battle Royale (2000) - Extended - 4K.mkv"             → title="Battle Royale", year=2000
```

### Parser Bug 2
```
"Cinema Paradiso - Theatrical Cut (1988) - 4K.mkv"    → title="Cinema Paradiso", year=1988
"Stray Cat Rock - Sex Hunter (1970) - 1080p Remux.mkv"→ title="Stray Cat Rock - Sex Hunter", year=1970
"Leon the Professional - Extended (1994).mkv"          → title="Leon the Professional", year=1994
```

### Parser Bug 3
```
"A Bay of Blood (Mario Bava, 1971).mkv"               → title="A Bay of Blood", director="Mario Bava", year=1971
"Comizi d'amore (Pier Paolo Pasolini, 1964).mkv"      → title="Comizi d'amore", director="Pier Paolo Pasolini", year=1964
```

### Language/Country Extraction
```
"Peking.Opera.Blues.1986.CHINESE.1080p.mkv"            → country="CN", language="chinese"
"Mississippi Mermaid (1969) In French.mkv"              → country="FR", language="french"
"Pistol for Ringo (1965) Dual IT and EN audio.mkv"     → country="IT", language="italian"
"A Força dos Sentidos (1978 - Áudio Original em Português).mp4" → country="BR", language="portuguese"
"Thampu AKA The Circus Tent (1978) Malayalam.mkv"      → country="IN", language="malayalam"
```

### User Tag Recovery
```
"Detour.1945.Criterion...[Popcorn-1940s].mkv"         → tier="Popcorn", decade="1940s"
"Dog Day Afternoon (1975)...[1970s-Reference].mkv"     → tier="Reference", decade="1970s"
```

### Country+Decade → Satellite Wave
```
country="CN" + year=1986 → Satellite/1980s/Hong Kong Action/
country="IT" + year=1975 → Satellite/1970s/Giallo/       (if horror/thriller signals present)
country="BR" + year=1981 → Satellite/1980s/Brazilian Exploitation/
country="FR" + year=1969 → Unsorted/                      (no wave match without genre signals)
```

---

## Relationship to Roadmap

This issue consolidates and reorders the original incremental path from Issue #001:

| Original | Revised (this issue) | Reason |
|---|---|---|
| v0.2: Reference tier only (+15 films) | v0.2: Parser fixes + language/country + user tags + Reference (~270-350 films) | Reference alone doesn't move the needle |
| v0.3: TMDb enrichment | v0.3: TMDb enrichment (unchanged) | Still needed for the remaining ~700 films |
| v0.4: Fuzzy matching | v0.4: Fuzzy matching (unchanged) | Deferred until v0.3 data available |

After v0.2 (this issue): ~380-460 films classified (~30-35%)
After v0.3 (TMDb): target ~800-900 films classified (~65-75%)
After v0.4 (fuzzy): target ~1,000+ films classified (~85%+)

---

## Notes

- The country+decade → wave routing is intentionally conservative. Not every French film is European Sexploitation. The routing should only fire when the country+decade combo falls within the defined wave parameters. Ambiguous cases stay Unsorted for v0.3 (TMDb) to resolve with genre data.
- User tag recovery trusts the user's curatorial judgment. These tags were manually applied and represent deliberate classification decisions.
- The "(Director, Year)" parser fix is especially valuable because it extracts BOTH director and year — enabling Core director matching for those films.
- Italian films need a secondary signal (horror/thriller/giallo keywords in filename) to route to Giallo vs generic Italian cinema. Without that signal, they should stay Unsorted.
