# Investigation: Director-First Routing for Satellite Categories

**Type:** Category 0 — Theory Problem (§0.1 Work Router)
**Date:** 2026-03-03
**Status:** Pre-spec (findings → spec pending)

---

## §1 Problem Statement

Satellite classification is producing plausible-looking but wrong outputs. Indie Cinema accumulates 56% of all `tmdb_satellite` classifications. Tight tradition categories (Giallo, Pinku Eiga, Brazilian Exploitation) receive zero `tmdb_satellite` auto-classifications — they rely entirely on explicit `country_satellite` or `explicit_lookup` to populate. Director lists in the routing rules are present but functionally decorative: the decade gate fires first and prevents director checks from running for out-of-era tradition films.

**Signal that this is a theory problem, not an implementation bug:** The output is internally consistent — films are routing to plausible destinations given the rules — but the rules invert the priority that the theory specifies.

---

## §2 Work Router §0.1 Classification

**Category: THEORY PROBLEM**

> "The output looks plausible but is wrong" — the system is faithfully executing rules that contradict the curatorial thesis.

Distinguishing characteristics:
- Results pass basic sanity checks (films land in real Satellite categories)
- Results fail curatorial inspection (Indie Cinema is a catch-all, not a category)
- The code was written coherently — this is not a bug in the implementation of the design; it is a wrong design

---

## §3 Theory Check (§0.3)

What the theory documents say vs. what the code does:

| Theory Document | What it says | What the code does |
|---|---|---|
| COLLECTION_THESIS §7 | "Directors are the primary units of cinema evolution" | Routes by country+genre first; director as tiebreaker |
| SATELLITE_DEPTH §3 | "Category Core = directors who defined/transformed the tradition" | No within-category tier distinction in routing |
| TIER_ARCHITECTURE §13 | "The whitelist is the thesis" (Core director list = curatorial position) | Satellite has no equivalent director-first thesis |
| REFINEMENT_AND_EMERGENCE §7 | "Every Satellite category is the shadow of something in Core" | Shadow relationship not encoded in routing logic |
| MARGINS_AND_TEXTURE §8 | "Positive-space categories have distinctive vocabulary" | Keywords are secondary; director identity not primary |

**Finding:** The theory supports director-first routing. The implementation uses country+genre-first with director as a tiebreaker. This is implementation drift from the founding thesis, not a deliberate design decision.

---

## §4 Data Flow Trace (§0.5)

### What the current system does

```
Tradition category (Giallo, AmExploitation, Blaxploitation, etc.):
  film
    → decade gate (line 117: if decade not in rules['decades']: continue)
    → if decade passes: director check
    → if director passes: route to category
    → if director fails: country + genre check
    → if all fail: Indie Cinema catch-all

Result: A 1998 Abel Ferrara film (New Rose Hotel) never reaches the
American Exploitation director list — the decade gate (1960s-1980s) fires
first and skips the entire category.
```

```
What works (Core):
  film → director whitelist → decade metadata → destination

What works (FNW, AmNH):
  film → director list (country_codes=[], no decade gate) → destination

What works (explicit_lookup):
  film → SORTING_DATABASE → destination (highest trust, always fires first)
```

**Pattern that works is consistently: director identity first.**

### Current classification distribution (sorting_manifest.csv, n=53 Satellite films)

| Reason code | Films | % |
|---|---|---|
| tmdb_satellite | 41 | 77.4% |
| explicit_lookup | 8 | 15.1% |
| country_satellite | 4 | 7.5% |

Of the 41 `tmdb_satellite` films, **23 (56%) route to Indie Cinema** — the functional catch-all for anything that passes a loose country+genre check without matching a tighter tradition category.

### Tight tradition categories — auto-classification rate

| Category | Films in library | tmdb_satellite | explicit_lookup | country_satellite |
|---|---|---|---|---|
| Giallo | 13 | 0 | 8 | 5 |
| Brazilian Exploitation | 35+ | 0 | 35+ | 0 |
| Pinku Eiga | 8 | 0 | 6 | 2 |
| American Exploitation | 36 | 3 | 21 | 12 |
| Blaxploitation | 12 | 1 | 9 | 2 |

**Tight categories depend almost entirely on human curation (explicit_lookup) or country+genre matches (country_satellite). Director-list routing contributes essentially nothing to these categories currently.**

---

## §5 Root Causes

### RC-1: Director lists are too sparse

Current tradition category director coverage vs. scholarship standard:

| Category | Current directors | Target (Wikipedia/scholarship) | Gap |
|---|---|---|---|
| Giallo | 6 | 15–20 | ~60% missing |
| Blaxploitation | 4 | 12–15 | ~70% missing |
| American Exploitation | 5 | 12–15 | ~60% missing |
| Brazilian Exploitation | 0 | 8–10 | 100% missing |
| Classic Hollywood | 0 | 12–15 | 100% missing |
| Pinku Eiga | 4 | 10–12 | ~65% missing |
| Hong Kong Action | 4 | 12–15 | ~70% missing |
| European Sexploitation | 6 | 12–15 | ~55% missing |

Total across tradition categories: **~87 directors listed, ~120+ missing**.

Even if the routing logic were correct, the sparse lists mean most canonical directors' films would fall through to country+genre or Indie Cinema.

### RC-2: Decade gate fires before director check

In `lib/satellite.py` lines 117-118 (current code):

```python
for category_name, rules in SATELLITE_ROUTING_RULES.items():
    # Decade gate fires first — skips entire category
    if rules['decades'] is not None and decade not in rules['decades']:
        continue  # director check at line 121 is never reached

    # Director check (currently a tiebreaker, not primary)
    if rules['directors'] and director:
        ...
```

A 1998 Abel Ferrara film (New Rose Hotel) never reaches the American Exploitation director list. The decade gate (1960s–1980s) rejects it first. The film routes to Indie Cinema instead.

**The gate ordering means director lists function as tiebreakers within the decade window, not as primary routing signals.**

---

## §6 What the Current System Does Right

These mechanisms work and should be preserved:

| Mechanism | Films | Why it works |
|---|---|---|
| Core director whitelist (Stage 6) | ~400 organised | Director-first, scholarship-grounded, comprehensive list |
| French New Wave (country_codes=[]) | 10 films | Director-only routing, no country gate |
| American New Hollywood (country_codes=[]) | 12 films | Director-only routing, no country gate |
| explicit_lookup (SORTING_DATABASE) | 8 Satellite films | Human curation, highest trust, fires first |
| country_satellite | 4 films | Works when genre+country signal is unambiguous |

**The pattern that works is always director identity first.** FNW and AmNH work precisely because their `country_codes=[]` design forces director-only routing — a country gate would incorrectly route any French film from the 1960s to FNW regardless of movement membership.

---

## §7 The Director Matrix: Cross-Reference Before Routing

The key insight: **routing rules should be built by priority — corrective first, then queue, then prospective.** To know which rules have immediate value vs. future-only value, you must cross-reference canonical director lists against what is actually in the library.

### Cross-reference axes

- **Axis A:** Canonical directors per genre (from Wikipedia/scholarship), ordered by within-category tier (Core → Reference → Texture)
- **Axis B:** What is in the library (library_audit.csv + tmdb_cache.json + sorting_manifest.csv)
- **Output:** Per-director status: correctly placed / wrongly placed / in queue / unknown location / not in system

### Live findings from prototype cross-reference

| Director | Category | Films in system | Status |
|---|---|---|---|
| mario bava | Giallo Core | 2 films | In library — location UNKNOWN (filename parse miss) |
| dario argento | Giallo Core | 0 | NOT IN CACHE — no films processed |
| sergio martino | Giallo Reference | 1 | CORRECT → Satellite/Giallo/1970s/ ✓ |
| gordon parks | Blaxploitation Core | 1 (Shaft) | CORRECT → Satellite/Blaxploitation/ ✓ |
| jack hill | Blaxploitation/AmExploit | 4 films | SPLIT → 2 Blaxploitation ✓, 2 AmExploitation ✓ (correct dual-category) |
| abel ferrara | AmExploitation Reference | 5 films | MIXED → 2 in Indie Cinema (The Blackout 1997, Pasolini 2014); 3 in AmExploitation ✓ |
| larry cohen | AmExploitation Reference | 4 films | SPLIT → Hell Up In Harlem in Blaxploitation ✓, Perfect Strangers in AmExploit ✓ |
| john ford | Classic Hollywood Core | 1 (The Quiet Man) | IN QUEUE → correctly routing to Classic Hollywood |
| russ meyer | AmExploitation Core | 4 films | Partially correct; some UNKNOWN location |

### Key observations

1. **Jack Hill and Larry Cohen correctly span two categories** — their films route by genre, not director identity alone. This is correct behaviour and should be preserved.

2. **Abel Ferrara has 2 films in Indie Cinema** (The Blackout, 1997; Pasolini, 2014) that may belong in American Exploitation. The director matrix surfaces these as the highest-priority corrective opportunities.

3. **Bava, Fulci, Meyer have films at UNKNOWN location** — they are in the organised library (went through the pipeline) but filename-to-title matching fails. The films ARE placed somewhere — we just cannot confirm where from the current tooling.

4. **Many canonical directors have NO films in the system** (Argento, Lenzi, Van Peebles, Corman, Hawks) — routing rules for these directors are prospective only. Adding them has future value but zero immediate corrective value.

### Priority order for routing rule development

1. **Directors with wrongly placed films** — immediate corrective value (Ferrara → 2 films in Indie Cinema → should be AmExploitation)
2. **Directors with films in queue** — immediate routing value (Ford → The Quiet Man queuing correctly, but no rule confirms it)
3. **Directors with films in library at unknown location** — diagnostic value (Bava, Fulci, Meyer — need filename parsing improvement)
4. **Directors with no films in system** — prospective value only (Argento, Corman, Van Peebles)

---

## §8 Proposed Direction: Director-First Routing

Make tradition category Satellite routing match how Core works:

```
Proposed:
  film → tradition director list → [decade as confidence modifier] → destination
  film (no director match) → country+genre fallback → destination (unchanged)

Current:
  film → decade gate → [director tiebreaker] → country+genre → Indie Cinema catch-all
```

Director match fires regardless of decade gate. Decade becomes a confidence modifier:
- Director in list + decade within expected range → confidence 0.8
- Director in list + decade outside expected range → confidence 0.6 (flag for review)
- No director match → current country+genre logic unchanged

### Movement categories (FNW, AmNH, JNW) — no change

Movement categories already use `country_codes=[]` which forces director-only routing. Their decade gate is intentional — a 1990s Godard falls through to Core check, which is correct. These should not be modified.

### Within-category tiers (from SATELLITE_DEPTH.md)

The proposed routing supports adding a within-category tier structure in a follow-up pass:

| Tier | Definition | Routing behaviour |
|---|---|---|
| Category Core | Defined or transformed the tradition; sustained body of work | Auto-classify, confidence 0.8 |
| Category Reference | Solid practitioners; consistently recognised in scholarship | Auto-classify, confidence 0.7 |
| Texture | Genre workers; contributed individual films | Confidence 0.5, review-flagged |

Flat director lists are sufficient for the initial routing pass. Tier structure can be a follow-up.

---

## §9 Wikipedia-Sourced Director Lists (Initial Scope)

Directors to add per category, sourced from Wikipedia and published filmographies:

### Giallo (IT, 1960s–1980s) — 6 → ~15

Currently listed: bava, argento, fulci, lenzi, martino, bido
To add: `massimo dallamano`, `ruggero deodato`, `paolo cavara`, `armando crispino`, `fernando di leo`, `lamberto bava`, `enzo castellari`

Sources: Wikipedia "List of giallo films", "Giallo film directors"

### Blaxploitation (US, 1970s) — 4 → ~12

Currently listed: gordon parks, jack hill, ernest dickerson, ossie davis
To add: `melvin van peebles`, `gordon parks jr.`, `michael schultz`, `bill gunn`, `barry shear`, `arthur marks`

Source: Wikipedia "Blaxploitation", "Category:Blaxploitation film directors"

### American Exploitation (US, 1960s–1980s) — 5 → ~12

Currently listed: russ meyer, herschell gordon lewis, abel ferrara, larry cohen, larry clark
To add: `roger corman`, `andy milligan`, `david friedman`, `michael findlay`, `doris wishman`
Note: Consider removing `larry clark` — his 1970s–1980s films route via country+genre correctly; his 1990s films should route to Indie Cinema. Dual-listing creates a regression under director-first routing.

Source: Wikipedia "Grindhouse", "Exploitation film"

### Classic Hollywood (US, 1930s–1950s) — 0 → ~12

Currently listed: (none)
To add: `john ford`, `howard hawks`, `orson welles`, `frank capra`, `michael curtiz`, `george cukor`, `fred zinnemann`, `elia kazan`, `john huston`
Note: Billy Wilder is in Core whitelist — do not duplicate.

Source: Wikipedia "Classical Hollywood cinema", "30 Greatest Directors of Hollywood's Golden Age"

### Brazilian Exploitation (BR, 1960s–1990s) — 0 → ~8

Currently listed: (none)
To add: `carlos reichenbach`, `victor di mello`, `ody fraga`, `roberto mauro`, `fauzi mansur`, `claudio cunha`, `jose miziara`, `jean garret`

Source: Wikipedia "Pornochanchada", "Boca do Lixo"

### Pinku Eiga (JP, 1960s–1980s) — 4 → ~10

Currently listed: wakamatsu, adachi, hisayasu, tanaka
Note: `masao adachi` is in the Japanese New Wave list — verify no conflict before adding to Pinku.
To add: `noboru tanaka` (if not already matched by 'tanaka'), `hisayasu sato`

Source: Wikipedia "Pink film", Sharp "Behind The Pink Curtain" (2008)

### Hong Kong Action (HK/CN, 1970s–1990s) — 4 → ~12

Currently listed: johnwoo, tsui hark, ringo lam, johnnie to
To add: `king hu`, `chang cheh`, `sammo hung`, `yuen woo-ping`, `jackie chan`, `ching siu-tung`, `corey yuen`
Note: King Hu worked in TW as well as HK — verify country_codes includes TW.

Source: Wikipedia "Hong Kong action cinema", BFI "10 great Hong Kong action films"

### European Sexploitation (FR/IT/DE/BE, 1960s–1980s) — 6 → ~12

Currently listed: (check constants.py)
To add: `joe d'amato`, `jess franco`
Note: Jess Franco is Spanish (ES). Either add ES to country_codes or use director-only match (no country gate) for Franco.

Source: Wikipedia "Sexploitation film"

---

## §10 Implementation Order

### Step 0 (this document)
Write investigation report — `docs/issues/INVESTIGATION_DIRECTOR_FIRST_ROUTING.md`

### Step 1: Director matrix script
Build `scripts/build_director_matrix.py`.

Reads: canonical director lists (from constants.py or a new data file) + tmdb_cache.json + library_audit.csv + sorting_manifest.csv
Outputs: `output/director_matrix.csv`

Columns: `category`, `canonical_tier`, `director_entry`, `films_found`, `correctly_placed`, `wrongly_placed`, `in_queue`, `unknown_location`, `not_in_system`

**Verify:** Run script → confirm Ferrara's Indie Cinema films surface as corrective rows.

### Step 2: Expand director lists in constants.py
Data-only, no code change. Testable immediately: `python classify.py <source>` and verify new directors route.
Risk: low (adds routing paths, does not remove any existing paths).

### Step 3: Reorder gate in satellite.py
Move director check before decade gate for tradition categories only (~10 lines).
Discriminant: `rules['country_codes'] != []` (tradition) vs `rules['country_codes'] == []` (movement — leave unchanged).

**Verify:** `pytest tests/test_satellite.py -v` → all pass. Dry run shows New Rose Hotel routes to AmExploitation.

### Step 4: Remove larry clark dual-listing regression
His 1970s–1980s films route via country+genre (US + genre + decade). His 1990s films should route to Indie Cinema. Remove from AmExploitation directors list; add SORTING_DATABASE pin for any edge cases.

### Step 5: Regression check
`python audit.py && python scripts/reaudit.py`
Target: confirmed count ≥ 704 (current baseline). No new wrong_tier entries.

---

## §11 Verification

```bash
# After each change:
pytest tests/ -v

# Check specific directors route correctly:
grep "Abel Ferrara\|Roger Corman\|Melvin Van Peebles\|John Ford" output/sorting_manifest.csv

# Regression check:
python audit.py && python scripts/reaudit.py

# Indie Cinema count should decrease as films move to specific categories:
grep "Indie Cinema" output/sorting_manifest.csv | wc -l
```

Expected results after full implementation:
- Tests: all passing (especially test_satellite.py)
- New Rose Hotel (Ferrara, 1998) → American Exploitation
- Classic Hollywood director films → Classic Hollywood (not Indie Cinema or Unsorted)
- Reaudit: confirmed ≥ 704, no new wrong_tier

---

## §12 Files to Modify

| File | Change | Scope |
|---|---|---|
| `scripts/build_director_matrix.py` | New: director × library cross-reference | New file, ~100 lines |
| `lib/constants.py` | Expand `directors` lists in SATELLITE_ROUTING_RULES | ~100 lines of data additions |
| `lib/satellite.py` lines 113–125 | Reorder decade gate + director check for tradition categories | ~10 lines |
| `docs/SORTING_DATABASE.md` | Add pins for Ferrara films confirmed as misclassified | 0–5 lines |

## §13 Scope Boundaries

**In scope:**
- Expanding tradition category director lists with Wikipedia-sourced names
- Moving director check before decade gate for tradition categories
- Removing larry clark dual-listing regression

**Not in scope:**
- Within-category confidence tiering (follow-up pass)
- Wikipedia API integration (manual research → constants.py data)
- Movement categories (FNW, AmNH, JNW) — gate ordering is intentional for these
- Changing country_codes or decade bounds for any category
- Adding new categories
