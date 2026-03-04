# Investigation: Two-Signal Classification Architecture

**Type:** Category 0 — Theory Problem (§0.1 Work Router)
**Date:** 2026-03-03
**Status:** Complete → Issue Spec #40 filed (GitHub #40)
**Depends on:** `INVESTIGATION_DIRECTOR_FIRST_ROUTING.md` (same session, precursor findings)

---

## §1 Problem Statement

Satellite routing currently entangles two fundamentally different kinds of knowledge — director identity and structural coordinates (country+decade+genre) — in a sequential gate chain where decade blocks director and structure is a fallback. The investigation below demonstrates that these two signals are independently computable, complementary in their strengths, and that their pattern of agreement or disagreement is itself informative for classification confidence.

**Origin:** The director-first routing investigation (precursor document) identified that director lists are functionally decorative because the decade gate fires first. This exploration asked: what if you treat director matching and structural matching as two independent scorers and integrate them?

---

## §2 The Two Signals

### Signal 1: Director Matrix — relational knowledge ("who made this?")

Maps a director to one or more tradition associations based on body of work, technique lineage, and documented historical membership. This is an **identity** signal. It persists across the director's career — a 1998 Ferrara is still "from" the American exploitation tradition even though the film's structural coordinates don't match the movement's era.

Properties:
- **Not binary.** Directors have varying strengths of association (Category Core → Category Reference → Texture), per SATELLITE_DEPTH.md §3.
- **Can span categories.** Jack Hill is both Blaxploitation and AmExploitation. Larry Cohen spans AmExploitation and Blaxploitation.
- **Period-dependent.** Godard's 1960s work is FNW; his 2014 work is still by a FNW director but outside the movement's era.
- **High precision, low recall** with current lists: ~87 directors listed, ~120+ missing. Near-zero false positives when lists are correct, but most canonical directors' films fall through.

### Signal 2: Structural Triangulation — coordinate knowledge ("where/when/what?")

Country + decade + genre locate a film in a 3D space. Some regions are owned by a single tradition (IT+1970s+Horror = Giallo territory). Some overlap (US+1970s+Crime = Blaxploitation OR AmExploitation OR AmNH). This is a **coordinates** signal about the landscape, not the film's identity.

Properties:
- **High precision in distinctive regions** (IT+1970s → Giallo at 88%, US+1940s → Classic Hollywood at 90%, BR+1970s → Brazilian Exploitation at 100%).
- **Ambiguous in overlapping regions** (US+1970s has 3-way overlap, FR+1960s has 2-way, HK+1990s has 3-way).
- **Blind to out-of-era films.** Structure says nothing about a 2014 Godard film or a 1998 Ferrara.

---

## §3 Evidence: The Two Signals Are Already Independent

The evidence trail system (`evidence_classify()` in `lib/satellite.py`) already computes both signals independently for every film × every category. Analysis of `output/evidence_trails.csv` (n=403 films in queue) reveals:

### 3.1 Agreement rate: zero

Across all categories, `both_pass = 0`. No film currently has both director pass AND structural pass for the same category. This is because:
- Director lists are so sparse that the director signal barely fires (only 10 passes across 403 films).
- When it does fire, it's in movement categories (FNW, AmNH) where `country_codes=[]` means there's no structural signal to compare.

### 3.2 Structural match distribution

| Match type | Films |
|---|---|
| Unique match (1 category) | 56 |
| Ambiguous (2+ categories) | 12 |
| No structural match | 334 |

Of the 56 unique matches: Indie Cinema 33, Blaxploitation 12, AmExploitation 10, HK Action 1.

### 3.3 Structural overlap pairs

| Pair | Films |
|---|---|
| European Sexploitation + Indie Cinema | 6 |
| American Exploitation + Blaxploitation | 5 |
| European Sexploitation + Giallo | 1 |
| Giallo + Indie Cinema | 1 |
| Hong Kong Action + Indie Cinema | 1 |

### 3.4 Films where structure matches multiple categories

| Film | Director | Structural matches | Actually routed |
|---|---|---|---|
| Le Samourai | Melville | Giallo, EuroSex, Indie | Giallo (incorrect) |
| The French Connection | Friedkin | Blaxploitation, AmExploit | Unsorted |
| The Omega Man | Sagal | Blaxploitation, AmExploit | Unsorted |
| A Touch of Zen | King Hu | HK Action, Indie | HK Action (correct) |
| The Long Goodbye | Altman | Blaxploitation, AmExploit | AmNH (via director) |

### 3.5 Films where director identity disagrees with structural placement

| Film | Director signal | Structure signal | Current routing |
|---|---|---|---|
| Adieu au langage (Godard, 2014) | FNW (if expanded) | Indie Cinema | Indie Cinema |
| A Summer's Tale (Rohmer, 1996) | FNW (if expanded) | Indie Cinema | Indie Cinema |
| New Rose Hotel (Ferrara, 1998) | AmExploit (if expanded) | Blaxploitation | Unsorted |
| Happiness of Katakuris (Miike, 2001) | JExploit (if expanded) | Indie Cinema | Indie Cinema |
| Color of Money (Scorsese, 1986) | AmNH | (nothing) | AmNH (correct — director rescues) |

---

## §4 Structural Precision Map

### High-precision regions (structure alone is sufficient)

Empirical validation against organized library placement (n=125 matched Satellite films):

| Region | → Category | Cache films | Library size | Empirical precision |
|---|---|---|---|---|
| IT+1970s | Giallo | 9 | 24 | 88% (7/8) |
| IT+1980s | Giallo | 6 | 24 | 100% |
| US+1940s | Classic Hollywood | 18 | 49 | 90% (9/10) |
| US+1930s | Classic Hollywood | 5 | 49 | 100% |
| BR+1970s | Brazilian Exploitation | 7 | 40 | 100% |
| BR+1980s | Brazilian Exploitation | 2 | 40 | 100% |
| HK+1980s | Hong Kong Action | 11 | 29 | 100% |
| FR+1970s | European Sexploitation | 10 | 32 | 100% |

These regions cover ~66 films in cache, ~248 in the organized library. No director signal needed.

### Ambiguous regions (director signal required for disambiguation)

| Region | Competing categories | Cache films | Ambiguity type |
|---|---|---|---|
| **US+1970s** | AmExploit / Blaxploitation / AmNH | **37** | 3-way tradition overlap |
| US+1980s | AmExploit / AmNH | 30 | Era boundary |
| US+1960s | AmExploit / Classic Hollywood | 27 | Era boundary |
| **HK+1990s** | HK Action / Cat III / New Wave | **21** | 3-way tradition overlap |
| **FR+1960s** | FNW / EuroSex | **20** | Movement overlap |
| IT+1960s | Giallo / EuroSex | 15 | Movement overlap |
| JP+1970s | JNW / Pinku / JExploit | 13 | 3-way tradition overlap |

These regions cover ~163 films. Genre helps marginally, but within these zones, director identity is the only reliable discriminator.

---

## §5 Signal Reachability Analysis

For the organized Satellite library (506 films), how many are reachable by each signal with CURRENT routing rules?

| Category | Library size | Dir only | Struct only | Both | Neither (explicit_lookup) |
|---|---|---|---|---|---|
| Indie Cinema | 155 | 0 | 38 | 1 | **116** |
| Music Films | 57 | 0 | 0 | 0 | **57** |
| Classic Hollywood | 49 | 0 | 26 | 0 | 23 |
| Brazilian Exploitation | 40 | 0 | 4 | 0 | **36** |
| American Exploitation | 36 | 4 | 8 | 0 | **24** |
| European Sexploitation | 32 | 1 | 5 | 1 | **25** |
| Hong Kong Action | 29 | 2 | 5 | 1 | **21** |
| Giallo | 24 | 0 | 5 | 2 | **17** |
| Pinku Eiga | 18 | 0 | 1 | 1 | **16** |
| American New Hollywood | 15 | 8 | 0 | 0 | 7 |
| French New Wave | 13 | 4 | 0 | 0 | **9** |
| Japanese New Wave | 13 | 1 | 0 | 0 | **12** |
| Blaxploitation | 9 | 0 | 0 | 0 | **9** |

**Total: ~120 films reachable by either signal. ~386 films (76%) depend entirely on explicit_lookup.**

The current system is running on human curation, not automated classification. Both signals are severely underpowered.

---

## §6 Director Grouping by Routing Value

Directors should be prioritized by what adding them to routing rules actually accomplishes:

### Group A: Disambiguators (highest value)

Directors whose identity resolves a structurally ambiguous zone. Adding them multiplies the structural signal's effectiveness.

- **US+1970s** (37 films, 3-way ambiguity): Jack Hill (→Blaxploitation), Larry Cohen (→AmExploit/Blaxploitation), Gordon Parks (→Blaxploitation), Russ Meyer (→AmExploit), Robert Aldrich (→mainstream, exclude)
- **HK+1990s** (21 films, 3-way): Johnnie To (→HK Action), Wong Kar-wai (→HK New Wave), Herman Yau (→Cat III), Lam Nai-Choi (→HK Action)
- **FR+1960s** (20 films, 2-way): Godard/Truffaut (→FNW), Roger Vadim (→EuroSex), Jesús Franco (→EuroSex)
- **JP+1970s** (13 films, 3-way): Terayama (→JNW), Hasebe (→Pinku), Fujita (→JExploit)

### Group B: Confirmers (medium value)

Directors in high-precision structural zones. Adding them raises confidence but doesn't change routing outcomes. Value is in the integration model (both-agree = highest confidence).

- IT+1970s Giallo directors (Bava, Argento, Fulci)
- BR+1970s Brazilian Exploitation directors
- HK+1980s HK Action directors (Tsui Hark)

### Group C: Rescuers (targeted value)

Directors whose identity routes films that have NO structural signal (out of era). Small populations but curatorially important.

- Late Godard (2014), late Rohmer (1996), late Resnais → FNW directors in 1990s-2010s
- Late Ferrara (1998, 2014) → AmExploit director in 1990s-2010s
- Late Miike → JExploit director in 2000s-2010s

---

## §7 The Integration Model

### Current architecture (sequential gate chain)

```
film → decade gate → [director tiebreaker] → country+genre fallback → Indie Cinema catch-all
```

Decade blocks director. Structure is fallback. First match wins.

### Proposed architecture (two independent signals → integration)

```
Film → [Director Matrix]          → evidence vector per category
Film → [Structural Triangulation] → evidence vector per category
                                    ↓
                           Integration function
                                    ↓
                      Category + confidence + explanation
```

### Integration semantics

| Director says | Structure says | Meaning | Confidence | Action |
|---|---|---|---|---|
| A | A | Core member, in era | 0.85 | Route |
| A | B (different) | Structural ambiguity, director disambiguates | 0.75 | Route to A |
| A | nothing | Out-of-era tradition work | 0.6 | Route to A, flag |
| nothing | B (unique region) | Unknown director, clear territory | 0.65 | Route to B |
| nothing | B (ambiguous region) | Unknown director, overlapping zone | 0.4 | Review queue |
| A | C (different tradition) | Late-period / evolved past movement | — | Flag both, review |
| nothing | nothing | No evidence | — | Unsorted |

### Key differences from current system

1. **Both signals run for every film, always.** No short-circuiting. The decade gate doesn't prevent the director check.
2. **Disagreement is information.** Currently discarded; in integration model, the pattern of agree/disagree tells you about classification confidence.
3. **Confidence is evidence-dependent, not category-dependent.** Currently Giallo = 0.8 fixed. Under integration: a Giallo match with both signals = 0.85; with structure only = 0.65.

---

## §8 Bang for Buck Priority

### Tier 1 — Structure alone, high precision, large population

No director signal needed. Structural region is distinctive enough.

| Region | Category | Library size | Action |
|---|---|---|---|
| US+1940s/1930s | Classic Hollywood | 49 | Structure works. Add Classic Hollywood directors (Group B) for confirmation. |
| IT+1970s/1980s | Giallo | 24 | Structure works. Add Giallo directors (Group B) for confirmation. |
| BR+1970s/1980s | Brazilian Exploitation | 40 | Structure works but country_codes needs BR films in cache. |
| HK+1980s | HK Action | 29 | Structure works. |

### Tier 2 — Director resolves ambiguous structure, biggest populations

This is where director signal MULTIPLIES structural signal. Highest leverage.

| Zone | Films | What director resolves |
|---|---|---|
| US+1970s | 37 | AmExploit vs Blaxploitation vs AmNH (3-way) |
| HK+1990s | 21 | HK Action vs Cat III vs New Wave (3-way) |
| FR+1960s | 20 | FNW vs EuroSex (2-way) |
| US+1980s | 30 | AmExploit vs AmNH (2-way) |
| JP+1970s | 13 | JNW vs Pinku vs JExploit (3-way) |

### Tier 3 — Director rescues out-of-era films

Small populations but curatorially significant — these are tradition directors whose later work currently routes to Indie Cinema.

- Late FNW directors (Godard 2014, Rohmer 1996, Resnais)
- Late AmExploit directors (Ferrara 1998, 2014)
- Late JExploit directors (Miike 2000s)

---

## §9 Relationship to `evidence_classify()`

The infrastructure for two-signal classification is substantially built. `evidence_classify()` in `lib/satellite.py` (Issue #35) already:

- Runs all gates for all categories independently (no short-circuiting)
- Uses three-valued gate logic (pass / fail / untestable)
- Returns `SatelliteEvidence` with `CategoryEvidence` per category
- Records 6 gate results per category (decade, director, country, genre, keyword, title_kw)
- Writes flat CSV to `output/evidence_trails.csv`

What's missing:
1. **Expanded director lists** (RC-1 from precursor investigation) — Signal 1 barely fires with current data
2. **Integration function** — something that reads both evidence vectors and produces a ranked result with confidence
3. **Gate reordering in `classify()`** — or replacing `classify()` with an integration-based router that uses `evidence_classify()` as its engine

---

## §10 Files Referenced

| File | Role in this investigation |
|---|---|
| `output/evidence_trails.csv` | Primary data source — all gate results per film × per category |
| `output/sorting_manifest.csv` | Queue classification outcomes (reason codes, destinations) |
| `output/library_audit.csv` | Organized library — ground truth placement (1064 films) |
| `output/tmdb_cache.json` | Enrichment data — director, country, genres, keywords (578 entries) |
| `lib/satellite.py` | Current sequential gate chain (lines 113-186) + evidence_classify() (lines 188-300+) |
| `lib/constants.py` | SATELLITE_ROUTING_RULES — director lists, country_codes, decades, genres |
| `docs/issues/INVESTIGATION_DIRECTOR_FIRST_ROUTING.md` | Precursor investigation — RC-1 (sparse lists) and RC-2 (gate ordering) |
