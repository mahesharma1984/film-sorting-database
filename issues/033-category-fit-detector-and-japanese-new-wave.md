# Issue #33: Category fit detector + Japanese New Wave — misroute detection and missing category discovery

**Type:** Two-part — Tooling (Stage 1) + Curatorial discovery (Stage 2) + New category implementation (Stage 3)
**Severity:** Medium (category pollution in Pinku Eiga and American Exploitation; blocked curation work)
**Component:** new script `scripts/category_fit.py`, `lib/constants.py`, `docs/SATELLITE_CATEGORIES.md`, `docs/SORTING_DATABASE.md`
**Discovered via:** Tentpole ranking session (2026-02-23) — low scores surfaced films clearly outside their assigned categories
**Depends on:** Issue #30 (tentpole scoring infrastructure — built), Issue #33 prefetch (cache now populated)
**Blocks:** Accurate tentpole rankings for Pinku Eiga, Japanese Exploitation; Stage 3 curation passes for those categories

---

## How This Was Found

After running `scripts/prefetch_satellite_cache.py --retry-nulls` to populate the TMDb cache for organised Satellite films, the tentpole rankings (`output/tentpole_rankings.md`) revealed that Pinku Eiga contains films scoring 1–2/10 that are clearly not pink films:

- **Akira (1988)** — Katsuhiro Ôtomo — anime sci-fi
- **Tampopo (1985)** — Jûzô Itami — food comedy
- **The Ballad of Narayama (1983)** — Shôhei Imamura — art cinema
- **Demon Pond (1979)** — Masahiro Shinoda — fantasy
- **Twilight of the Cockroaches (1987)** — Hiroaki Yoshida — animation
- **Throw Away Your Books, Rally in the Streets (1971)** — Shûji Terayama — underground
- **Grass Labyrinth (1979)** — Shûji Terayama — underground
- **AKA Serial Killer (1975)** — Masao Adachi — documentary/underground
- **Doberman Cop (1977)** — Kinji Fukasaku — yakuza action

Cross-scoring these films against all other Satellite categories (prototype run 2026-02-23) showed:

| Film | Current score | Best alt | Alt score | Signal |
|---|---|---|---|---|
| i (1967) — Godard | Pinku 3 | French New Wave | 5 | Core director flag |
| Doberman Cop (1977) | Pinku 2 | Japanese Exploitation | 5 | Clear winner |
| Akira (1988) | Pinku 2 | all categories ≤ 3 | — | No Satellite fit |
| Tampopo (1985) | Pinku 1 | all categories ≤ 2 | — | No Satellite fit |
| Ballad of Narayama | Pinku 2 | all categories ≤ 2 | — | No Satellite fit |

The "no Satellite fit" cluster — Akira, Tampopo, Imamura, Terayama, Yoshida — is not random noise. These are major Japanese art cinema and underground films from the 1960s–1980s that landed in Pinku Eiga because the routing rule fires on `JP + 1960s–1980s + no other match`. The cluster indicates a **missing category**, not just individual misroutes.

The same pattern exists in American Exploitation (Australian and non-US films incorrectly routed via decade match: Turkey Shoot, Girl Slaves of Morgana Le Fay) and has been partially addressed by prior reaudit work (Issue #31).

---

## The Two-Part Problem

### Problem 1: Misrouted films with a clear alternative

Films that score significantly higher (≥ 2 points) in another existing category. These are routing errors fixable by SORTING_DATABASE pin or routing rule adjustment.

Examples:
- **Doberman Cop (1977)** — Pinku Eiga → Japanese Exploitation (5 vs 2)
- **i (1967)** — Pinku Eiga → Core/1960s/Jean-Luc Godard (Core director)
- **Forbidden Game of Love (1975)** — Spanish director (Eloy de la Iglesia) in Pinku Eiga — country mismatch, no good Satellite fit → Unsorted or European Sexploitation

### Problem 2: Films with no good Satellite fit — missing category candidate

Films scoring ≤ 2 in their current category AND ≤ 3 in all alternatives. When these cluster by country/decade/tradition, they are **category gap evidence**.

The Japanese no-fit cluster (8–12 films, 1960s–1980s, Japanese art/underground cinema) is the strongest current candidate for a new category.

---

## Stage 1: Build `scripts/category_fit.py`

A read-only diagnostic script. NEVER moves files.

### What it does

For every Satellite film scoring ≤ threshold (default: 2) in its current category:

1. **Cross-score against all Satellite categories** using the existing `score_film()` infrastructure from `rank_category_tentpoles.py`
2. **Check Core director whitelist** — if match, flag as Core candidate regardless of cross-scores
3. **Classify the outcome** into one of three types:
   - `REROUTE` — best alternative scores ≥ current + 2 (clear winner exists)
   - `NO_FIT` — all alternatives score ≤ current + 1 (no better home in existing categories)
   - `CORE_CANDIDATE` — director in Core whitelist (should exit Satellite entirely)
4. **Group NO_FIT films** by country + decade to surface missing-category clusters

### Output format

```
## Pinku Eiga — 9 low-fit films (score ≤ 2)

### CORE_CANDIDATE (1)
  i (1967) — Jean-Luc Godard
  → Core director. Move to Core/1960s/Jean-Luc Godard/

### REROUTE (2)
  Doberman Cop (1977) — Kinji Fukasaku
  → Japanese Exploitation scores 5 vs current 2. Delta: +3
  Forbidden Game of Love (1975) — Eloy de la Iglesia
  → No fit (Spanish director). Delta flat. Flag for manual review.

### NO_FIT — potential missing category (6)
  Akira (1988) — Katsuhiro Ôtomo — JP 1980s — anime/sci-fi
  Tampopo (1985) — Jûzô Itami — JP 1980s — comedy
  The Ballad of Narayama (1983) — Shôhei Imamura — JP 1980s — art cinema
  Demon Pond (1979) — Masahiro Shinoda — JP 1970s — fantasy
  Throw Away Your Books (1971) — Shûji Terayama — JP 1970s — underground
  Grass Labyrinth (1979) — Shûji Terayama — JP 1970s — underground

  Cluster: JP / 1960s–1980s / 6 films
  Possible missing category: Japanese New Wave / Japanese Art Cinema
```

### CLI

```bash
python scripts/category_fit.py                          # all Satellite categories
python scripts/category_fit.py --category "Pinku Eiga" # one category
python scripts/category_fit.py --threshold 3            # widen to score ≤ 3
python scripts/category_fit.py --output output/category_fit_report.md
```

### Implementation notes

- Import `score_film`, `make_cache_key`, `RANKING_TAGS` from `rank_category_tentpoles.py` — no duplication
- `CORE_CANDIDATE` check: `core_db.is_core_director(director)` — already in the ranker
- Cluster grouping: group NO_FIT films by `(country_code, decade)` — country from OMDb cache, decade from audit CSV
- Threshold default 2 catches films with only `decade_match` signal and nothing genre-specific

---

## Stage 2: Discovery — Japanese New Wave as a Satellite category

Before implementing, verify Rule 4 (Domain Grounding): does the category have published scholarly basis, documented director membership, and clear decade bounds?

### Evidence for viability

**The movement exists in scholarship:**
- *Japanese New Wave Cinema* (Isolde Standish, 2011, BFI) — primary academic reference
- *Eros Plus Massacre: An Introduction to the Japanese New Wave Cinema* (David Desser, 1988)
- Senses of Cinema "Great Directors" entries for Oshima, Terayama, Wakamatsu, Imamura
- Criterion "Japanese New Wave" collection (explicit institutional recognition)

**Core directors (documented movement members):**
- Nagisa Oshima (In the Realm of the Senses, Death by Hanging, Boy, The Man Who Left His Will on Film)
- Shôhei Imamura (The Insect Woman, Intentions of Murder, Pigs and Battleships) — *early work*; later Imamura (Narayama, Black Rain) is less movement-specific
- Kôji Wakamatsu (Go Go Second Time Virgin, Violated Angels) — also Pinku Eiga overlap
- Shûji Terayama (Throw Away Your Books, Pastoral: To Die in the Country, Grass Labyrinth)
- Masao Adachi (AKA Serial Killer, Red Army/PFLP)
- Hiroshi Teshigahara (Woman in the Dunes, Face of Another) — likely Core
- Seijun Suzuki (Tokyo Drifter, Branded to Kill) — genre/underground overlap
- Yoshishige Yoshida / Kiju Yoshida (Eros + Massacre, Heroic Purgatory)

**Decade bounds:**
- Peak: 1960s–1970s (movement active 1959–1975 by most accounts)
- Valid extended: 1950s (Oshima's early films) through 1980s (late movement work)
- 1990s onward: not movement-appropriate

**Collection density check (needed before proceeding):**
Currently in Pinku Eiga at low scores: Terayama (2 films), Adachi (1), Yoshida (2), Imamura (1).
Also check Japanese Exploitation for misrouted NW films.
→ **Need to count: are there ≥ 6 films that would route to Japanese New Wave?** (Rule 4 minimum density threshold)

### Overlap questions to resolve

1. **Wakamatsu overlap with Pinku Eiga**: Wakamatsu made both pink films (Violated Angels) and political underground films (Soldier's Wife). Pink films → stay Pinku Eiga. Non-pink work → Japanese New Wave. Per-film SORTING_DATABASE entries.
2. **Imamura split**: Early Imamura (1960s Shochiku period) → Japanese New Wave. Late Imamura (Narayama 1983, Black Rain 1989) → arguably Core or Indie Cinema. Director-level routing insufficient; film-level pins needed.
3. **Fukasaku**: Yakuza genre films (Doberman Cop, Battle Without Honor) → Japanese Exploitation, not NW.
4. **Teshigahara**: Core candidate (Woman in the Dunes is canonical enough for Core whitelist).

### Routing rule design

```python
'Japanese New Wave': {
    'country_codes': ['JP'],
    'decades': ['1950s', '1960s', '1970s', '1980s'],
    'genres': ['Drama'],          # Broad — most NW films are Drama
    'directors': [
        'Nagisa Oshima', 'Shoji Terayama', 'Shuji Terayama',
        'Masao Adachi', 'Yoshishige Yoshida', 'Kiju Yoshida',
        'Seijun Suzuki', 'Hiroshi Teshigahara',
    ],
    # Director-only routing: no country+genre+decade auto-match
    # (too many Japanese films would catch)
    'keyword_signals': {
        'tmdb_tags': ['japanese new wave', 'nuberu bagu', 'political cinema',
                      'underground film', 'avant-garde'],
        'text_terms': ['new wave', 'underground', 'political', 'rebellion']
    }
}
```

**Key design constraint:** Unlike Giallo or Brazilian Exploitation, Japanese New Wave should route **director-first**, not country+genre+decade. The movement is defined by specific directors, not by all Japanese drama from the 1960s. Without a director match, a Japanese 1960s drama should fall to Indie Cinema, not auto-route to NW.

### Peak decade for tentpole scoring

```python
PEAK_DECADES['Japanese New Wave'] = ['1960s', '1970s']
```

### Category cap

15–20 films (tighter than Giallo at 30 — this is a more specialised movement).

---

## Stage 3: Implementation

Once Stage 2 confirms ≥ 6 films and resolves the overlap questions:

1. Add `'Japanese New Wave'` entry to `SATELLITE_ROUTING_RULES` in `lib/constants.py`
2. Add `PEAK_DECADES` entry
3. Add `CATEGORY_CAPS` entry in `rank_category_tentpoles.py`
4. Add `SATELLITE_TENTPOLES` entries for 3–5 anchor films
5. Add SORTING_DATABASE pins for the overlap cases (Wakamatsu, Imamura split)
6. Run `classify.py` on Unsorted to pick up any new NW films there
7. Move misrouted films from Pinku Eiga → Japanese New Wave (via `move.py`)
8. Re-run `rank_category_tentpoles.py --all` to validate new rankings

---

## Open Questions

1. **Is the collection dense enough?** 6 confirmed films minimum before adding category. Run `category_fit.py` output + manual check of Japanese Exploitation to get real count.
2. **Teshigahara → Core or NW?** Woman in the Dunes (1964) has strong claim to Core. If Core, it exits Satellite. Check Core whitelist criteria.
3. **Anime as separate category?** Akira and Twilight of the Cockroaches have no good home. A "Japanese Animation" micro-category (3–5 films) might be warranted if more anime is in the collection. Or they go to Indie Cinema (JP country code is included).
4. **Itami (Tampopo, A Taxing Woman)?** Not NW — too late, too mainstream in tone. Indie Cinema (JP, 1980s) is the better fit. Verify Indie Cinema will catch him via country_codes.

---

## Definition of Done

- [ ] `scripts/category_fit.py` built and producing correct output for all Satellite categories
- [ ] Japanese New Wave density confirmed (≥ 6 films in collection)
- [ ] Overlap questions resolved (Wakamatsu, Imamura, Fukasaku, Teshigahara)
- [ ] `SATELLITE_ROUTING_RULES` entry added for Japanese New Wave
- [ ] SORTING_DATABASE pins added for overlap/split cases
- [ ] Misrouted films moved out of Pinku Eiga to correct destinations
- [ ] `rank_category_tentpoles.py --all` re-run — Pinku Eiga rankings no longer contain non-pink films
