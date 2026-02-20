# Issue #029: Text Signal Enrichment — Keyword-Based Satellite Routing

**Status:** Specification (pre-implementation)
**Scope:** Enrichment stage (lib/tmdb.py, lib/omdb.py) + Satellite routing (lib/satellite.py, lib/constants.py)
**Boundary:** Enrichment changes → measure Stage 2 only. Routing changes → measure Stage 6 only. (Rule 6)

---

## Problem

The current satellite routing has two signal types:

- **Structural:** country + decade + genre — coarse, produces false negatives (Italian Drama 1970s misses Giallo's genre gate) and false positives (any Italian film in the right decade with the right genre auto-routes to Giallo)
- **Director list:** known names — high precision, zero recall for unknown or variant-named directors

What's missing is evidence from the film's actual content: movement vocabulary, critical language, thematic terms that sit between "is it Italian?" and "is it Bava?" This evidence is already available in the existing API responses — it's just not being extracted or used.

---

## What We Already Have (Unused)

| Field | API | Where it lives | Status |
|---|---|---|---|
| `overview` | TMDb | `details_data['overview']` | Discarded — not in result dict |
| `tagline` | TMDb | `details_data['tagline']` | Discarded — not in result dict |
| `keywords` | TMDb | Already in result dict | Extracted but **not used for routing** |
| `Plot` | OMDb | `data['Plot']` | Not extracted; needs `plot=full` param |

All four fields arrive in API responses that are already being made. No new API calls required.

---

## Workflow

```
STAGE 0: DEFINE CATEGORIES
  keyword_signals per category in SATELLITE_ROUTING_RULES (lib/constants.py)
  Edited by humans only. Grounded in film-historical scholarship (Rule 4).

STAGE 1: PARSE FILENAME
  filename → title, year, director (unchanged)
  Hard gate: no year → Unsorted

STAGE 2: PULL DATA — APIs (lib/tmdb.py, lib/omdb.py)
  TMDb: director, countries, genres, popularity, vote_count,
        overview ←NEW, tagline ←NEW, keywords (already extracted)
  OMDb: director, countries, genres, vote_count,
        plot ←NEW (add plot=full param)

STAGE 3: VERIFY (unchanged)
  Right film? title similarity + year delta
  Soft gates: director absent, country absent, keywords empty → continue

STAGE 4: MERGE (unchanged except new fields flow through)
  OMDb > TMDb > filename for director, country, year
  TMDb > OMDb for genres
  New: overview/tagline/plot merge by length (longer wins, encyclopedic preferred)

STAGE 5: CLASSIFY — routing (first match wins)
  1. Explicit lookup (SORTING_DATABASE.md)
  2. Core director whitelist
  3. Reference canon
  4. Popcorn (popularity + mainstream signals)
  5. Satellite — three sub-rules per category:
     5a. Director match + decade → ROUTE          (unchanged)
     5b. Country + genre + decade → ROUTE         (unchanged)
     5c. Country + decade + keyword hit → ROUTE   ←NEW (Tier A)
     5d. TMDb keyword hit, director-only          ←NEW (Tier B)
         categories only → ROUTE
  6. Indie Cinema (structural catch-all, no keyword routing)
  7. Unsorted + reason code
```

---

## Keyword Signal Design

### Signal types

Two distinct evidence qualities:

**TMDb keyword tags** — crowd-curated, structured, high precision. An actual TMDb tag of "giallo" or "nouvelle vague" is a strong signal. Used for both Tier A and Tier B routing.

**Text scan terms** — words/phrases to search in `overview` + `plot` free text. Broader recall, lower precision. Used for Tier A only (not strong enough to route without structural corroboration).

### Per-category keyword_signals

These are the authoritative definitions. Each list covers both TMDb tags and text scan terms — the routing code distinguishes them at match time.

**Giallo**
```
tmdb_tags:    ['giallo', 'italian horror', 'psychosexual thriller', 'black-gloved killer']
text_terms:   ['giallo', 'stylized violence', 'voyeurism', 'whodunit', 'fetishism',
               'mystery thriller', 'slasher', 'italian genre']
```
Historical grounding: Stefano Della Casa, *Storia e storie del cinema popolare italiano* (2001); Tim Lucas on Mario Bava; Mikel Koven, *La Dolce Morte* (2006)

**Pinku Eiga**
```
tmdb_tags:    ['pink film', 'roman porno', 'pinku eiga', 'nikkatsu', 'erotic drama']
text_terms:   ['pink film', 'roman porno', 'erotica', 'softcore', 'exploitation',
               'pinku', 'nikkatsu']
```
Historical grounding: Jasper Sharp, *Behind the Pink Curtain* (2008)

**Japanese Exploitation**
```
tmdb_tags:    ['yakuza', 'jidaigeki', 'toei', 'chambara', 'japanese crime film']
text_terms:   ['yakuza', 'gang war', 'crime syndicate', 'organized crime',
               'samurai', 'yakuza film', 'toei']
```
Historical grounding: Mark Schilling, *The Yakuza Movie Book* (2003)

**Brazilian Exploitation**
```
tmdb_tags:    ['pornochanchada', 'boca do lixo', 'brazilian exploitation']
text_terms:   ['pornochanchada', 'chanchada', 'boca do lixo', 'embrafilme',
               'erotic comedy']
```
Note: Low expected hit rate — TMDb/OMDb coverage of Brazilian exploitation is thin. Keyword signals are supplementary to the primary country+decade routing.
Historical grounding: Ruy Gardnier on Boca do Lixo; João Luiz Vieira in *Studies in Spanish & Latin American Cinemas* (2008)

**Hong Kong Action**
```
tmdb_tags:    ['martial arts', 'wuxia', 'kung fu', 'triad', 'heroic bloodshed',
               'shaw brothers', 'hong kong action']
text_terms:   ['martial arts', 'kung fu', 'wuxia', 'swordplay', 'triad',
               'heroic bloodshed', 'shaw brothers', 'golden harvest', 'category iii']
```
Historical grounding: David Bordwell, *Planet Hong Kong* (2000); Bey Logan, *Hong Kong Action Cinema* (1995)

**American New Hollywood**
```
tmdb_tags:    ['new hollywood', 'american new wave', 'counterculture', 'post-code']
text_terms:   ['new hollywood', 'new american cinema', 'post-production code',
               'counterculture', 'auteur', 'vietnam era', 'anti-establishment']
```
Note: Tier B eligible — a TMDb tag of "new hollywood" or "american new wave" can route without a director match (movement category, high specificity).
Historical grounding: Peter Biskind, *Easy Riders, Raging Bulls* (1998); David Cook, *Lost Illusions* (2000)

**American Exploitation**
```
tmdb_tags:    ['grindhouse', 'exploitation film', 'b-movie', 'troma', 'slasher',
               'drive-in movie']
text_terms:   ['grindhouse', 'drive-in', 'exploitation', 'splatter', 'gore',
               'b-movie', 'troma', 'low budget horror', 'cult classic']
```
Historical grounding: Eric Schaefer, *Bold! Daring! Shocking! True!* (1999); Jeffrey Sconce on paracinema

**European Sexploitation**
```
tmdb_tags:    ['erotic film', 'softcore', 'sexploitation', 'european erotica']
text_terms:   ['erotic film', 'softcore', 'erotica', 'sexploitation',
               'adult film', 'european erotica']
```
Historical grounding: Pam Cook, *Fashioning the Nation* (1996); Tanya Horeck & Tina Kendall on European exploitation

**Blaxploitation**
```
tmdb_tags:    ['blaxploitation', 'african american', 'inner city', 'black power']
text_terms:   ['blaxploitation', 'soul', 'ghetto', 'black power',
               'inner city', 'african american exploitation']
```
Historical grounding: Ed Guerrero, *Framing Blackness* (1993); Stephane Dunn, *Baad Bitches & Sassy Supermamas* (2008)

**Music Films**
```
tmdb_tags:    ['concert film', 'rockumentary', 'musical performance', 'rock documentary']
text_terms:   ['concert film', 'rockumentary', 'music documentary',
               'concert', 'live performance']
```

**French New Wave**
```
tmdb_tags:    ['nouvelle vague', 'french new wave', 'new wave', 'cinéma vérité',
               'cinema verite']
text_terms:   ['nouvelle vague', 'new wave', 'jump cut', 'cinéma vérité',
               'left bank', 'french new wave']
```
Note: Tier B eligible — a TMDb tag of "nouvelle vague" or "french new wave" can route without a director match.
Historical grounding: Richard Neupert, *A History of the French New Wave Cinema* (2007); Antoine de Baecque, *La Nouvelle Vague* (1998)

**Classic Hollywood**
```
tmdb_tags:    ['film noir', 'pre-code', 'golden age of hollywood', 'screwball comedy',
               'classical hollywood']
text_terms:   ['film noir', 'golden age', 'studio system', 'pre-code',
               'screwball comedy', 'hays code', 'classical hollywood']
```
Historical grounding: David Bordwell, Janet Staiger, Kristin Thompson, *The Classical Hollywood Cinema* (1985)

**Indie Cinema**
```
NO keyword routing.
```
Rationale: Indie Cinema is a negative-space category — defined by what it is NOT (not exploitation, not Popcorn mainstream, not Core auteur, not a named historical movement). No keyword set can define it positively without producing widespread false positives. "Art house", "independent film", "festival film" all appear in texts about Core auteurs, French New Wave, and Popcorn-adjacent prestige films alike. Indie Cinema remains a structural catch-all reached only when all other routes fail. See `docs/theory/MARGINS_AND_TEXTURE.md` §8.

---

## Routing Logic: Three Tiers of Keyword Evidence

### Tier A — Keyword substitutes for genre gate

**Fires when:**
- Country match ✓
- Decade match ✓
- Genre match ✗ (film doesn't carry expected genre tags)
- Any keyword_signal found in TMDb `keywords` list OR overview/plot text ✓

**Effect:** Routes to category despite genre mismatch.

**Primary use case:** Italian Drama 1970s that is clearly Giallo by vocabulary but TMDb filed under Drama rather than Horror/Thriller.

### Tier B — TMDb keyword routes movement categories without director

**Fires when:**
- Category is director-only (French New Wave, American New Hollywood)
- No director match found in directors list
- TMDb `keywords` field (not text scan) contains a movement-specific tag

**Effect:** Routes to movement category despite no director match.

**Scope:** Restricted to French New Wave and American New Hollywood only. TMDb keyword tags for these movements ("nouvelle vague", "new hollywood") are specific enough that a false positive is unlikely. Text scan terms are NOT eligible for Tier B — "new wave" in an overview could mean anything.

### What keywords do NOT do

- Keywords cannot override structural disqualifiers (wrong decade, wrong country in non-director-only categories)
- Keywords cannot route into Indie Cinema or Popcorn — those are structurally defined
- Text scan terms alone (without country+decade) cannot route anything
- Keywords do not affect the Popcorn check, which runs before all Satellite routing

---

## Failure Gates

| Check | Gate type | Behaviour on failure |
|---|---|---|
| TMDb `overview` absent | Soft | Continue with OMDb plot and TMDb keywords only |
| OMDb `Plot` = 'N/A' | Soft | Continue with TMDb overview and keywords only |
| TMDb `keywords` empty | Soft | Continue with structural routing only (existing behaviour) |
| All text sources empty | Soft | Fall through to structural routing — existing behaviour preserved |

No hard gates. The text signal layer is purely additive — every film that classified correctly before will still classify correctly. The layer only adds new routing paths; it cannot remove existing ones.

---

## Out of Scope (This Issue)

- Wikipedia plot summaries (CMU Movie Summary Corpus, Kaggle Wikipedia plots) — deferred. Requires a local index build step and title+year normalization across a 42K-film dataset. Impact unclear until API text fields are measured. Revisit after this issue ships.
- MovieLens tag genome — deferred for same reason.
- Embedding-based similarity routing — deferred. Rule-based keyword matching is the right starting point; evaluate gap before adding ML complexity.
- Letterboxd / Rotten Tomatoes scraped data — excluded permanently. Legal risk, stale data, unclean text.

---

## Implementation Checklist

- [ ] `lib/tmdb.py`: Add `overview` and `tagline` to result dict (extract from `details_data`)
- [ ] `lib/omdb.py`: Add `'plot': 'full'` to request params; extract `data.get('Plot')` as `plot`
- [ ] `lib/constants.py`: Add `keyword_signals` field to each entry in `SATELLITE_ROUTING_RULES`
- [ ] `lib/satellite.py`: Add Tier A routing sub-rule (country + decade + keyword → route)
- [ ] `lib/satellite.py`: Add Tier B routing sub-rule (TMDb keyword only, movement categories)
- [ ] `classify.py`: Ensure `overview`, `tagline`, `plot` flow through merge to satellite classifier
- [ ] Tests: Add test cases for Tier A (Italian Drama → Giallo via keyword) and Tier B (no director, TMDb keyword "nouvelle vague" → FNW)
- [ ] Invalidate TMDb cache entries missing `overview` after implementation (or let them repopulate naturally)

---

## Measurement

Per Rule 6 (Boundary-Aware Measurement) and Rule 7 (Measurement-Driven Development):

**Enrichment metrics (Stage 2 changes only):**
- % of films with non-empty `overview`
- % of films with non-empty `plot`
- % of films with ≥1 keyword_signal match

**Routing metrics (Stage 5 changes only, measure after enrichment is stable):**
- Classification rate before/after on Unsorted directory
- Tier A fires: count of films routed via keyword-replaces-genre
- Tier B fires: count of films routed via TMDb-keyword-only
- Regression check: any previously-classified films that changed tier

Run `python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted` before and after. Compare `output/staging_report.txt`.
