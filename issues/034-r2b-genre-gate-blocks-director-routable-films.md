# Issue #34: R2b Films Blocked by Genre Gate Despite Having Director + Country

**Type:** Routing gap — systematic mis-classification of a recoverable data population
**Severity:** Medium (44 films currently stuck in Unsorted that should be classifiable)
**Discovered via:** First data-gathering run on Unsorted directory (2026-02-24), post-Issue #33 implementation
**Depends on:** Issue #33 (data readiness levels, R2b population defined)
**Blocks:** Reducing Unsorted count without manual curation for every film

---

## How This Was Found

After implementing the Issue #33 Unsorted Protocol (non-film filtering, data readiness levels,
manual enrichment seed), the first full API-backed classify run on the Unsorted directory
produced this breakdown:

- 91 Non-Film (supplements/trailers) — correctly filtered
- 167 R1 (year only, no API data)
- 44 R2b (year + director + country from API, but no genres)
- 28 R2a (year + director from filename, API returned nothing)
- 3 R3 (full data, no routing rule)

The 44 R2b films were all tagged `unsorted_no_match` — meaning they entered the full routing
pipeline but matched nothing. Investigation showed the root cause: the satellite genre gate
blocks them even when director + country + decade would suffice for routing.

---

## Root Cause

### The genre gate in `lib/satellite.py` (lines 132–134)

```python
genre_match = True  # Default to True if no genre restriction
if rules['genres'] is not None:
    genre_match = any(g in genres for g in rules['genres'])
```

When `genres = []` (API returned no genre data), `any(g in [] for g in rules['genres'])` is
always `False`. The genre gate fails. The film is not routed.

### Why genres are missing for R2b films

OMDb returns director and country reliably but its genre field is often empty for foreign
or older films. TMDb genres require a successful title match — many of these films have
non-standard filenames or titles that confuse the TMDb search. Result: director + country
present, genres absent.

### The data flow

```
Filename → Parser → TMDb (title match fails or returns no genres) + OMDb (returns director+country)
→ _merge_api_results() → tmdb_data with genres=[]
→ Satellite stage: director path (if in directors list) → routes OK
                   country+genre path → genre_match = False → blocked
```

Director-only routing (French New Wave, American New Hollywood, Japanese New Wave) bypasses
the genre gate entirely — those categories use `country_codes: []` and route on director match
alone. Films whose directors are NOT in any directors list fall through to the country+genre
path, where the empty genres list blocks them.

---

## Affected Films (44 total)

Representative films that should be routable:

| Film | Director | Country | Correct Destination | Blocker |
|---|---|---|---|---|
| The Last Movie (1971) | Dennis Hopper | US | American New Hollywood | Not in directors list |
| Play It As It Lays (1972) | Frank Perry | US | American New Hollywood | Not in directors list |
| Fantastic Planet (1973) | René Laloux | FR, CS | Indie Cinema | Genre gate (FR + 1970s but no genres) |
| Linda Linda Linda (2005) | Nobuhiro Yamashita | JP | Indie Cinema | Genre gate (JP + 2000s but no genres) |
| One-Eyed Jacks (1961) | Marlon Brando | US | Unsorted (correct) | US excluded from Indie Cinema — correctly unroutable |
| Narcissus And Psyche (1980) | Gábor Bódy | HU | Indie Cinema | Genre gate (HU + 1980s but no genres) |
| Death of a Salesman (1985) | Volker Schlöndorff | US | Unsorted (correct) | US TV production — correctly unroutable |
| Looking for Mister Perfect (2003) | Ringo Lam | HK | HK Action | Genre gate (HK + 2000s but no genres) |

Many R2b films are genuinely unroutable (adult film directors, TV directors, experimental
one-offs) — those should remain Unsorted. The issue is that films which DO belong to a
satellite category are blocked by missing genre data, not by a genuine routing mismatch.

---

## What the Architecture Says

### Rule 10 (Data Readiness) — CLAUDE.md

> R2: Partial data → Route but cap confidence at 0.6

The intent is to route R2 films, not block them. The 0.6 confidence cap signals lower
certainty without refusing classification.

### MARGINS_AND_TEXTURE.md §8

Genre gates are structural for **positive-space categories** (Giallo, Pinku Eiga, Brazilian
Exploitation) — they prevent false positives where country+decade match but the film is not
genre-aligned with the movement. An Italian drama from the 1970s should NOT auto-route to
Giallo without genre evidence.

For **negative-space categories** (Indie Cinema, Popcorn), genre gates are weaker —
these categories are defined by what films aren't, not what they are.

### Director matching already bypasses the genre gate

The Satellite routing code has two distinct paths:
1. Director match → routes immediately (genre irrelevant)
2. Country + decade + genre match → genre is a required gate

Films whose directors are in a category's `directors` list never hit the genre gate.
The R2b problem only affects films that should route via the country+decade path.

---

## Two-Part Fix

### Part 1: Add missing directors to `lib/constants.py` (systemic — preferred)

For directors who clearly belong to a satellite movement, adding them to the category's
`directors` list is the correct fix. The director match path bypasses the genre gate,
routing fires immediately, and all future films by that director are handled automatically.

Directors to add (verified against published film history):

| Director | Category | Rationale |
|---|---|---|
| `'hopper'` (Dennis Hopper) | American New Hollywood | The Last Movie (1971) is canonical AmNH |
| `'frank perry'` | American New Hollywood | Play It As It Lays (1972), David and Lisa (1962) |
| `'ringo lam'` | HK Action | Prolific HK action director (City on Fire, Full Contact) |

René Laloux is a one-off (Fantastic Planet is his only widely-known film) — SORTING_DATABASE
pin is more appropriate than adding him to a directors list.

### Part 2: SORTING_DATABASE pins for one-off films (point fix — lower priority)

For films by directors who don't belong permanently in a category's directors list:

```
- Fantastic Planet (1973) → Satellite/Indie Cinema/1970s/
- Linda Linda Linda (2005) → Satellite/Indie Cinema/2000s/
- Narcissus And Psyche (1980) → Satellite/Indie Cinema/1980s/
- Looking for Mister Perfect (2003) → Satellite/HK Action/2000s/
```

### What NOT to do

- Do not relax the genre gate globally (`if rules['genres'] is not None and genres:`) —
  this would incorrectly route Italian/Japanese/Brazilian films with missing genres to
  positive-space categories (Giallo, Pinku, Brazilian Exploitation) that require genre evidence.
  Tested: breaks `test_kubrick_1999` (Eyes Wide Shut routes to Satellite instead of Core via
  the weakened gate).
- Do not add SORTING_DATABASE entries for all 44 R2b films — most are correctly Unsorted
  (adult films, TV productions, experimental one-offs). Mass pinning would encode curatorial
  noise as permanent decisions.

---

## Remaining R2b Films (genuinely unroutable — correct behaviour)

These films are correctly Unsorted and should remain so:

| Film | Reason |
|---|---|
| Henri Pachard — Public Affairs (1983) | Adult film director, no satellite category |
| Andy Wolk — Kiss and Tell (1996) | TV director |
| Brett Thompson — Adventures in Dinosaur City (1991) | Children's direct-to-video |
| David Lowell Rich — Satan's School for Girls (1973) | TV movie |
| John Milius — Motorcycle Gang (1994) | TV movie |
| Robert Fenz — Meditations on Revolution (×5) | Experimental/structural cinema — no category |
| Margarida Cordeiro — Rosa de Areia (1989) | PT director — PT excluded from Indie Cinema |
| Víctor Gaviria — The Rose Seller (1998) | CO director — CO excluded from Indie Cinema |
| Sigrid Andrea Bernardo — Lorna (2014) | PH director — PH excluded from Indie Cinema |
| Abel Ferrara — New Rose Hotel (1998) | US — possibly Core candidate; needs separate decision |

---

## Implementation Order

1. Add Dennis Hopper + Frank Perry to American New Hollywood directors in `lib/constants.py`
2. Add Ringo Lam to HK Action directors in `lib/constants.py`
3. Run `pytest tests/` — verify no regressions
4. Add 3–4 SORTING_DATABASE pins for the Laloux/Yamashita/Bódy one-offs
5. Re-run classify on Unsorted — R2b count should drop from 44 to ~35 (9 films rerouted)

The remaining ~35 R2b films are a mix of correctly-Unsorted films and films needing
manual enrichment (genres added to `output/manual_enrichment.csv`) before routing
can succeed.
