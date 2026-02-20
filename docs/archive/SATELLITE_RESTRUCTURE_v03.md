# Satellite Category Restructuring Proposal (v0.3)

**Date:** 2026-02-17
**Status:** DRAFT
**Rationale:** Fix misclassified French New Wave films + establish clearer decade boundaries for American/European categories

---

## Problem Statement

### 1. French New Wave Films Misrouted to Exploitation

**Current behavior:**
- French films from 1960s → "European Sexploitation" (via `COUNTRY_TO_WAVE`)
- This incorrectly classifies French New Wave art films as exploitation

**Affected films:**
- Eric Rohmer films (non-Core director)
- Early Claude Chabrol (before he was added to Core)
- Chris Marker documentaries
- Alain Resnais (not on Core whitelist)
- Jacques Demy musicals
- Agnès Varda films not already in Core

**Why this is wrong:**
- French New Wave is not exploitation - it's modernist art cinema
- These films are textural context for Core (Godard, Varda), not sexploitation margins
- They should be near Core in curatorial logic, not near Emmanuelle

### 2. American Categories Lack Clear Temporal Structure

**Current state:**
- "American Exploitation" spans 1960s-2000s (too broad)
- No distinction between Golden Age Hollywood (<1960) and later periods
- No category for American Indie Cinema (1980s+)

**Result:**
- Pre-1960 American genre films (Film Noir, Classic Western) have no clear home
- 1980s+ American indie/arthouse (Jarmusch, Hartley, early P.T. Anderson) routes to Unsorted or Popcorn incorrectly

### 3. European Sexploitation is Overloaded

**Current behavior:**
- Catches ALL French/German/Italian erotica 1960s-1980s
- But also incorrectly catches French New Wave, German New Cinema margins

---

## Proposed Solution: New Satellite Categories

### NEW CATEGORY 1: French New Wave

**Definition:**
- French art cinema from the Nouvelle Vague movement
- 1958-1973 (from Breathless to post-May '68 decline)
- Non-Core directors who participated in or orbited the movement

**Directors:**
- Eric Rohmer (Six Moral Tales)
- Claude Chabrol (pre-Core work, 1960s thrillers)
- Alain Resnais (Last Year at Marienbad, Hiroshima Mon Amour)
- Chris Marker (La Jetée, Sans Soleil)
- Jacques Demy (Umbrellas of Cherbourg, Young Girls of Rochefort)
- Jacques Rivette (non-Core if not already on whitelist)
- Louis Malle (Elevator to the Gallows, Zazie dans le Métro)

**Routing rules:**
```python
'French New Wave': {
    'country_codes': ['FR'],
    'decades': ['1950s', '1960s', '1970s'],  # 1958-1973 spans these
    'genres': ['Drama', 'Romance', 'Crime', 'Comedy'],
    'directors': [
        'rohmer', 'chabrol', 'resnais', 'marker',
        'demy', 'rivette', 'malle'
    ],
}
```

**Cap:** 30 films (similar to Giallo)

**Rationale:**
- These films provide textural context for Core Godard/Varda
- They're the "margins" of the New Wave - important but not auteur-obsession level
- Historically bounded movement with clear aesthetic identity
- Analogous to how Giallo provides context for Italian modernism

**Boundary rules:**
- Godard, Varda → Core (already on whitelist)
- Rohmer, Marker, Demy → Satellite (unless promoted to Core)
- Reference-level films (Hiroshima Mon Amour) → may override to Reference

---

### NEW CATEGORY 2: American Indie Cinema

**Definition:**
- American independent arthouse cinema
- 1980s-2010s (post-New Hollywood, pre-streaming)
- Non-Core directors working outside studio system

**Directors:**
- Jim Jarmusch (Stranger Than Paradise, Down by Law)
- Hal Hartley (Trust, Henry Fool)
- Richard Linklater (Slacker, Before trilogy) - non-Core work
- Kelly Reichardt (Certain Women, First Cow)
- Todd Haynes (Safe, Carol) - non-Core work
- Harmony Korine (Gummo) - non-Larry Clark work

**Routing rules:**
```python
'American Indie Cinema': {
    'country_codes': ['US'],
    'decades': ['1980s', '1990s', '2000s', '2010s'],
    'genres': ['Drama', 'Comedy', 'Romance'],
    'directors': [
        'jarmusch', 'hartley', 'linklater', 'reichardt',
        'haynes', 'korine'
    ],
}
```

**Cap:** 40 films

**Rationale:**
- Fills gap between Core (Coen Brothers, Lynch) and Popcorn (studio entertainment)
- Captures American arthouse that's neither auteur-obsession nor exploitation
- Cross-generational category (1980s Jarmusch → 2010s Reichardt)

**Boundary rules:**
- Coen Brothers, Lynch, P.T. Anderson → Core (on whitelist)
- Jarmusch, Hartley, Reichardt → Satellite (unless promoted)
- Mumblecore/ultra-low-budget → cut to /Out unless genuinely compelling

---

### RENAMED CATEGORY: Classic Hollywood (formerly implicit)

**Definition:**
- American studio cinema from classical era
- Pre-1960 (before New Hollywood rupture)
- Genre cinema: Film Noir, Westerns, Musicals, Melodrama
- Non-Core directors (Hawks, Preminger not on whitelist)

**Routing rules:**
```python
'Classic Hollywood': {
    'country_codes': ['US'],
    'decades': ['1930s', '1940s', '1950s'],
    'genres': ['Film-Noir', 'Western', 'Musical', 'Drama', 'Crime'],
    'directors': [],  # Country + decade driven
}
```

**Cap:** 25 films

**Rationale:**
- Reference canon only covers ~10 classic Hollywood films (Casablanca, Sunset Blvd)
- Genre classics that aren't Reference-tier but provide historical context
- The Searchers, Sweet Smell of Success, Touch of Evil (if not by Core directors)

**Boundary rules:**
- Orson Welles, Billy Wilder → Core (if on whitelist)
- Canonical classics → Reference (Casablanca, Citizen Kane)
- Genre classics → Satellite (The Big Sleep, Out of the Past)

---

### NARROWED CATEGORY: American Exploitation (restricted decades)

**Current:** 1960s-2000s (too broad)
**Proposed:** 1960s-1980s (grindhouse/VHS era only)

**Rationale:**
- Exploitation as a distinct industrial category ends with VHS collapse
- 1990s+ American transgressive cinema routes to either:
  - American Indie Cinema (Harmony Korine, Gregg Araki)
  - Popcorn (DTV action, horror)
  - /Out (low-quality exploitation)

**Updated routing:**
```python
'American Exploitation': {
    'country_codes': ['US'],
    'decades': ['1960s', '1970s', '1980s'],  # NARROWED from 1960s-2000s
    'genres': ['Horror', 'Thriller', 'Crime'],
    'directors': [
        'russ meyer', 'abel ferrara', 'larry cohen',
        'herschell gordon lewis', 'larry clark'
    ],
}
```

---

### NARROWED CATEGORY: European Sexploitation (restricted scope)

**Current:** Catches all French/German/Italian erotica
**Proposed:** ONLY arthouse-adjacent erotica, NOT French New Wave

**Updated routing:**
```python
'European Sexploitation': {
    'country_codes': ['FR', 'IT', 'DE', 'BE'],
    'decades': ['1960s', '1970s', '1980s'],
    'genres': ['Romance', 'Drama'],  # REMOVED Documentary to avoid Marker
    'directors': [
        'borowczyk', 'metzger', 'brass', 'vadim',
        'jaeckin'  # Explicitly Just Jaeckin (Emmanuelle)
    ],
    # CRITICAL: Check director BEFORE country routing to prevent FNW misroutes
}
```

**New priority rule:**
- Check French New Wave directors BEFORE European Sexploitation
- Only route to Sexploitation if NO director match in other categories

---

## Routing Priority Order (Updated)

**Current order:** Core → Reference → Satellite (country) → Popcorn → Unsorted
**Proposed order for Satellite:** Check categories in this sequence:

1. **French New Wave** (1950s-1970s French, specific directors)
2. **Giallo** (1960s-1980s Italian, specific directors)
3. **Pinku Eiga** (1960s-1980s Japanese, specific directors)
4. **Japanese Exploitation** (1970s-1980s Japanese, Fukasaku)
5. **Brazilian Exploitation** (1970s-1980s Brazilian, country-driven)
6. **Hong Kong Action** (1970s-1990s HK, specific directors)
7. **Blaxploitation** (1970s, 1990s US, specific directors)
8. **American Exploitation** (1960s-1980s US, specific directors)
9. **American Indie Cinema** (1980s-2010s US, specific directors)
10. **Classic Hollywood** (pre-1960 US, country-driven)
11. **European Sexploitation** (1960s-1980s EU, fallback for erotica)
12. **Music Films** (any decade, genre-driven)
13. **Cult Oddities** (catch-all)

**Rationale:** Director-specific categories BEFORE country-only categories to prevent misrouting.

---

## Updated Satellite Cap Summary

| Category | Current Cap | Proposed Cap | Change |
|----------|-------------|--------------|--------|
| Giallo | 30 | 30 | - |
| Pinku Eiga | 35 | 35 | - |
| Japanese Exploitation | 25 | 25 | - |
| Brazilian Exploitation | 45 | 45 | - |
| Hong Kong Action | 65 | 65 | - |
| **French New Wave** | **-** | **30** | **NEW** |
| **American Indie Cinema** | **-** | **40** | **NEW** |
| **Classic Hollywood** | **-** | **25** | **NEW** |
| American Exploitation | 80 | 60 | Narrowed to 1960s-1980s |
| European Sexploitation | 25 | 20 | Narrowed scope |
| Blaxploitation | 20 | 20 | - |
| Nunsploitation | 15 | 15 | - |
| WIP/Rape-Revenge | 15 | 15 | - |
| Music Films | 20 | 20 | - |
| Mondo | 10 | 10 | - |
| Cult Oddities | 50 | 50 | - |

**Total Satellite Cap:** ~435 films → ~475 films (+40 for new categories)

---

## Implementation Steps

### Phase 1: Update Constants (lib/constants.py)

1. Add `'French New Wave'` to `SATELLITE_ROUTING_RULES`
2. Add `'American Indie Cinema'` to `SATELLITE_ROUTING_RULES`
3. Add `'Classic Hollywood'` to `SATELLITE_ROUTING_RULES`
4. Update `'American Exploitation'` decades: `['1960s', '1970s', '1980s']`
5. Update `'European Sexploitation'` to check director FIRST

### Phase 2: Update Satellite Logic (lib/satellite.py)

1. Ensure `check_satellite_category()` respects new priority order
2. Add decade validation for all new categories
3. Test French films route to French New Wave BEFORE European Sexploitation

### Phase 3: Update Folder Structure (scaffold.py)

```python
'French New Wave': {
    'decades': ['1950s', '1960s', '1970s'],
    'category': 'French New Wave'
},
'American Indie Cinema': {
    'decades': ['1980s', '1990s', '2000s', '2010s'],
    'category': 'American Indie Cinema'
},
'Classic Hollywood': {
    'decades': ['1930s', '1940s', '1950s'],
    'category': 'Classic Hollywood'
}
```

### Phase 4: Update Documentation

- `docs/SATELLITE_CATEGORIES.md` - add new categories
- `docs/theory/MARGINS_AND_TEXTURE.md` - justify French New Wave as texture
- `CLAUDE.md` - update satellite routing examples

### Phase 5: Reclassify Existing Films

Run targeted reclassification:
```bash
python scripts/reclassify.py \
  --filter-country FR \
  --filter-decade 1960s \
  --dry-run
```

Expected reclassifications:
- French New Wave films: European Sexploitation → French New Wave
- American indie films: Unsorted → American Indie Cinema
- Classic Hollywood: Popcorn → Classic Hollywood

---

## Theoretical Justification

### Why French New Wave is Satellite, Not Reference

**Reference = canonical films across ALL of cinema** (50-film cap)
**French New Wave = textural context for Core Godard/Varda**

Analogy:
- Giallo is context for Italian modernism (Antonioni, Pasolini)
- French New Wave is context for French modernism (Godard, Varda)

Both are Satellite because they provide **margins/texture**, not universal canonicity.

Films like *Hiroshima Mon Amour* (Resnais) could still be in Reference if they meet the Reference canon threshold. But most Rohmer, Marker, Demy films are Satellite-appropriate.

### Why American Indie ≠ Core

**Core = auteur obsession** (Coen Brothers, Lynch, P.T. Anderson)
**American Indie = interest in the tradition** (Jarmusch, Hartley, Reichardt)

These are different curatorial relationships:
- Jarmusch: "I appreciate the aesthetic, but I don't need his complete filmography"
- Lynch: "I need every film he's made to understand his vision"

### Why Classic Hollywood is Satellite, Not Reference

**Reference** holds the 10-15 canonical classics (Casablanca, Sunset Boulevard)
**Classic Hollywood** holds genre classics that provide historical texture

Example:
- *Out of the Past* (1947, Robert Mitchum noir) → Classic Hollywood
- *Double Indemnity* (1944, Billy Wilder) → Reference (already in canon)

---

## Open Questions

1. **Should Chabrol be promoted to Core?** He's currently in Satellite, but he has a large filmography (1960s-2000s). If promoted, his French New Wave work moves to Core.

2. **Rohmer threshold:** Six Moral Tales are essential French New Wave. Should Rohmer be Core? Or is he Satellite because he's a "minor" New Wave director?

3. **Chris Marker documentary status:** Does he route to French New Wave or Documentary (if we ever add that category)?

4. **American Indie vs Popcorn boundary:** Where does Richard Linklater's *Dazed and Confused* go? It's indie in production but feels like Popcorn in rewatchability.

5. **Classic Hollywood vs Reference:** Should we REMOVE some Reference classics and route them to Classic Hollywood to free up Reference slots? Or keep Reference strictly for top-50 canonical works?

---

## Next Steps

1. **User approval** of category additions and rationale
2. **Update constants.py** with new routing rules
3. **Write tests** for French New Wave routing
4. **Run dry-run reclassification** on French 1960s films
5. **Update theory documentation** to justify French New Wave as texture

**Estimated reclassification impact:**
- ~20-30 French New Wave films: European Sexploitation → French New Wave
- ~15-20 American indie films: Unsorted → American Indie Cinema
- ~10-15 classic films: Popcorn → Classic Hollywood
