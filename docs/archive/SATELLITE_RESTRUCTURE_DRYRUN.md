# Satellite Restructure v0.3 - Dry Run Impact Report

**Date:** 2026-02-17
**Source:** output/sorting_manifest.csv
**Scope:** Sample analysis of reclassifications with new French New Wave category

---

## Executive Summary

**Confirmed Reclassifications:** 4 films
**Potential Additional:** ~9 French films (need manual review)

### Key Findings

1. **Chris Marker's work is being misclassified** - *La jetée* (1962), one of the most iconic French New Wave experimental films, is currently in "European Sexploitation"
2. **Jacques Demy is already on the Core whitelist** but has 1 film misrouted to Satellite
3. **Eric Rohmer has no destination** - his films go to Unsorted
4. **9 French films from 1960s-1970s are in Unsorted** - several lack director extraction, need manual review

---

## Detailed Reclassifications

### 1. Chris Marker (French New Wave experimental filmmaker)

#### Film 1: *La jetée* (1962)
```
Title:     La jetée (1962)
Director:  Chris Marker
Current:   Satellite/European Sexploitation/1960s
Reason:    tmdb_satellite (country + decade routing)
Problem:   This is NOT sexploitation - it's one of the most famous
           experimental shorts in cinema history

SHOULD BE: Satellite/French New Wave/1960s
```

#### Film 2: *Le joli mai* (1963)
```
Title:     Le joli mai (1963)
Director:  Chris Marker
Current:   Unsorted
Reason:    unsorted_no_match
Problem:   Documentary by major FNW director has no destination

SHOULD BE: Satellite/French New Wave/1960s
```

**Impact:** Both Marker films would move to new French New Wave category

---

### 2. Jacques Demy (Already Core Director - Bug Fix)

#### Film: *Donkey Skin* (1970)
```
Title:     Donkey Skin (1970)
Director:  Jacques Demy
Current:   Satellite/European Sexploitation/1970s
Reason:    tmdb_satellite (country + decade routing)
Problem:   Demy is already on Core whitelist (1960s section)
           This film should be Core, not Satellite

SHOULD BE: Core/1970s/Jacques Demy
```

**Note:** *The Umbrellas of Cherbourg* (1964) is correctly routed to Core via explicit lookup

**Impact:** This is a classifier bug - Core director check should happen BEFORE satellite routing

---

### 3. Eric Rohmer (Six Moral Tales - French New Wave)

#### Film: *A Summer's Tale* (1996)
```
Title:     A Summer's Tale (1996)
Director:  Éric Rohmer
Current:   Unsorted
Reason:    unsorted_no_match
Problem:   Rohmer is major FNW director (Six Moral Tales)
           No routing destination for his work

WOULD BE:  Satellite/French New Wave/1990s
```

**Note:** 1996 is technically post-FNW (movement ended ~1973), but Rohmer's late work is still stylistically FNW

**Options:**
1. Create French New Wave category with extended decades (1950s-1990s for Rohmer)
2. Promote Rohmer to Core (if his complete filmography is essential)
3. Keep 1990s Rohmer as Reference if it reaches canonical status

---

### 4. French Films in Unsorted (Manual Review Needed)

These 1960s-1970s French films are currently Unsorted and could potentially route to French New Wave:

```
1. Le cercle vicieux (1960) - Max Pécas
   → Likely B-movie director, not FNW. Possibly Euro Sexploitation?

2. Les Sept Peches Capitaux (1962) - [NO DIRECTOR]
   → Anthology film - "The Seven Deadly Sins"
   → Directors include Godard, Chabrol (both Core)
   → Manual review needed

3. Plein soleil (1960) - [NO DIRECTOR]
   → Likely "Purple Noon" (René Clément, Alain Delon)
   → NOT FNW - this is a thriller, could be Reference or Popcorn

4. Cours du soir (1967) - Nicolas Ribowski
   → Unknown director, likely not FNW

5. Successive Slidings of Pleasure (1974) - [NO DIRECTOR]
   → This is Alain Robbe-Grillet
   → Arthouse erotica - Euro Sexploitation or FNW?

6. Le Jardin qui bascule (1975) - [NO DIRECTOR]
   → Unknown film, needs manual lookup

7. Le Plein De Super (1976) - Alain Cavalier
   → Cavalier is a French auteur, but NOT core FNW
   → Could be FNW or stay Unsorted

8. Passing Through (1977) - Larry Clark
   → Wait - this is AMERICAN Larry Clark (Kids, Bully)
   → The "-french" in filename is likely a language tag
   → Should route to American Exploitation, NOT FNW

9. Interview - Jacques Demy and Michel Legrand (1964)
   → This is a documentary/interview, not a narrative film
   → Possibly cut to /Out or create "Documentary" category
```

**Impact:** Of the 9 Unsorted French films:
- **2-3 might actually be French New Wave** (need director extraction)
- **3-4 are misidentified** (wrong director, language tag confusion)
- **2-3 should stay Unsorted** or route to other categories

---

## Category Impact Analysis

### European Sexploitation: Before vs After

**BEFORE restructure:**
- Contains: Chris Marker's *La jetée*, Jacques Demy's *Donkey Skin*, + actual sexploitation films

**AFTER restructure:**
- Marker → French New Wave
- Demy → Core (bug fix)
- European Sexploitation remains for actual erotica (Emmanuelle, Borowczyk, etc.)

**Result:** European Sexploitation becomes more focused and accurate

---

### French New Wave: New Category Population

**Confirmed films (from this analysis):**
1. *La jetée* (1962) - Chris Marker
2. *Le joli mai* (1963) - Chris Marker
3. *A Summer's Tale* (1996) - Eric Rohmer (if category extends to 1990s)

**Potential additions (need manual review):**
- *Les Sept Peches Capitaux* (1962) - anthology film
- *Successive Slidings of Pleasure* (1974) - Robbe-Grillet
- *Le Plein De Super* (1976) - Alain Cavalier

**Estimated total:** 3-6 films initially, growing as more FNW directors' work is added

---

## Classification Priority Bug Found

### Issue: Core Directors Being Misrouted

**Current behavior:**
```
1. Explicit lookup (SORTING_DATABASE.md)
2. Core director check
3. Reference canon check
4. Satellite routing (country + decade) ← HAPPENS TOO EARLY
5. Popcorn heuristics
```

**Problem:** Jacques Demy is a Core director (on whitelist), but his film *Donkey Skin* routes to Satellite because the country+decade check (France + 1970s → European Sexploitation) happens before verifying the director is Core.

**Fix needed:**
The Core director check needs to be **more robust**, or the explicit lookup needs to include all Demy films.

**Code location to investigate:**
- `classify.py` - check stage ordering
- `lib/core_directors.py` - verify Demy is in 1960s AND 1970s sections

---

## Open Questions

### 1. How to handle Rohmer's late work (1990s)?

**Options:**
- Extend French New Wave category to 1990s (just for Rohmer)
- Promote Rohmer to Core (if his complete filmography is essential)
- Create "Late New Wave" subcategory?

**Decision needed:** Is Rohmer's late work (Six Moral Tales continuation) essential enough for Core, or is it Satellite texture?

### 2. Should Alain Robbe-Grillet be French New Wave or European Sexploitation?

His films are experimental arthouse erotica - they bridge both categories.

**Current:** *Successive Slidings of Pleasure* (1974) is in Unsorted (no director extracted)

**Options:**
- French New Wave (he was part of Left Bank group with Resnais)
- European Sexploitation (his films are explicitly erotic)
- Stay Unsorted and manually route to appropriate category

### 3. How to fix the Demy Core routing bug?

**Immediate fix:** Add *Donkey Skin* to SORTING_DATABASE.md as explicit lookup

**Proper fix:** Investigate why Core director check didn't catch this

---

## Implementation Recommendations

### Phase 1: Fix Critical Bugs (High Priority)
1. Add Jacques Demy's *Donkey Skin* to explicit lookup → Core
2. Verify Core director whitelist includes Demy in both 1960s AND 1970s
3. Test that Core check happens before Satellite country routing

### Phase 2: Add French New Wave Category (Medium Priority)
1. Add to `SATELLITE_ROUTING_RULES` in `lib/constants.py`
2. Define directors: Marker, Rohmer (decide on late work), Robbe-Grillet?
3. Define decades: 1950s-1970s (or extend to 1990s for Rohmer)
4. Test routing priority: FNW before European Sexploitation

### Phase 3: Manual Review of Unsorted French Films (Low Priority)
1. Extract directors for films currently showing [NO DIRECTOR]
2. Research unknown directors (Max Pécas, Nicolas Ribowski, etc.)
3. Decide on Robbe-Grillet's category placement
4. Fix Larry Clark filename (remove "-french" language tag)

---

## Estimated Workload

**Immediate reclassifications:** 4 films
**Manual review needed:** 9 films
**Code changes:** 2-3 hours (add category, fix routing priority, test)
**Documentation updates:** 1 hour (SATELLITE_CATEGORIES.md, theory docs)

**Total estimated impact:** 10-15 films reclassified, clearer category structure

---

## Conclusion

The dry run validates the need for a French New Wave category:

✅ **Fixes concrete misclassifications** (Marker's *La jetée* is NOT sexploitation)
✅ **Provides destination for Rohmer** (currently has nowhere to go)
✅ **Reveals Core routing bug** (Demy should never hit Satellite)
✅ **Makes European Sexploitation more accurate** (removes art films from exploitation category)

**Recommendation:** Proceed with implementation, starting with critical bug fixes (Demy routing) and then adding French New Wave category.
