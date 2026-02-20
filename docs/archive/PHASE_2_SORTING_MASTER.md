# PHASE 2: MECHANICAL SORTING - MASTER DOCUMENT

## Overview

Now we apply the Phase 1 rules to actually sort the collection.

**Sorting Order:**
1. Core (clearest rules - director whitelist)
2. Reference (canonical list)
3. Satellite (category identification)
4. Popcorn (tonight test + format signals)
5. Staging (everything unclear)

---

## FOLDER STRUCTURE TEMPLATE

```
/Library
   /1950s
      /Core
         /Satyajit Ray/
         /Robert Bresson/
      /Reference
      /Satellite
         /[categories as needed]
      /Popcorn
   
   /1960s
      /Core
         /Godard/
         /Rivette/
         /Melville/
         /Pasolini/
         /Antonioni/
         /Resnais/
         /Varda/
         /Suzuki/
         /Demy/
         /Bertolucci/
         /Kubrick/
         /Fellini/
      /Reference
      /Satellite
         /Giallo/
         /Pinku/
         /European Sexploitation/
         /American Exploitation/
      /Popcorn
   
   /1970s
      /Core
         /Godard/
         /Rivette/
         /Melville/
         /Pasolini/
         /Ray/
         /Cassavetes/
         /Fassbinder/
         /Akerman/
         /Tarkovsky/
         /Ōshima/
         /Duras/
         /Malick/
         /Scorsese/
         /Bertolucci/
         /Herzog/
         /Fellini/
         /Coppola/
         /Kubrick/
      /Reference
      /Satellite
         /Giallo/
         /Pinku/
         /Brazilian/
         /Hong Kong Action/
         /American Exploitation/
         /Russ Meyer/
         /Blaxploitation/
         /European Sexploitation/
      /Popcorn
   
   /1980s
      /Core
         /Godard/
         /Yang/
         /Scorsese/
         /Lynch/
         /Coen Brothers/
         /Jarmusch/
         /Ruiz/
         /Kubrick/
         /Fassbinder/
         /Ray/
      /Reference
      /Satellite
         /Giallo/
         /Pinku/
         /Brazilian/
         /Hong Kong Action/
         /American Exploitation/
         /European Sexploitation/
      /Popcorn
         /Spider-Man/
         /Back to the Future/
         /Batman/
   
   /1990s
      /Core
         /Godard/
         /Yang/
         /Wong Kar-wai/
         /Hou Hsiao-hsien/
         /Hartley/
         /Coen Brothers/
         /Jarmusch/
         /Lynch/
         /Rohmer/
         /Malick/
         /Ray/
         /Oliveira/
         /Ruiz/
         /Kubrick/
      /Reference
      /Satellite
         /Hong Kong Action/
         /Brazilian/
         /American Exploitation/
      /Popcorn
   
   /2000s
      /Core
         /Wong Kar-wai/
         /Yang/
         /Hou Hsiao-hsien/
         /Lynch/
         /Godard/
      /Reference
      /Satellite
         /Hong Kong Action/
      /Popcorn
   
   /2010s
      /Core
         /Malick/
      /Reference
      /Satellite
      /Popcorn

/Staging
   /Unsorted
   /Unwatched
   /Undecided

/Out
   /Cut
```

---

## SORTING METHODOLOGY

### Step 1: Extract Film Metadata
For each film in the list, identify:
1. **Title**
2. **Year** → Decade
3. **Director** (if identifiable)
4. **Format/edition** (signals Popcorn curation)

### Step 2: Apply Decision Tree

```
START
  ↓
Is director on Core whitelist?
  YES → Core/[Decade]/[Director]/
  NO → Continue
  ↓
Is film on Reference canon list?
  YES → Reference/[Decade]/
  NO → Continue
  ↓
Is film exploitation/cult/margin?
  YES → Identify category → Satellite/[Decade]/[Category]/
  NO → Continue
  ↓
Is film rewatchable American entertainment?
  Does it pass "tonight test"?
  Does it have format curation signal (35mm, etc.)?
  YES → Popcorn/[Decade]/
  NO → Continue
  ↓
Unclear?
  → Staging/Undecided/
```

---

## PHASE 2 EXECUTION PLAN

### Task 1: Core Sorting (Mechanical)
- Parse movie list for Core director films
- Sort by decade + director
- **This is 80% automatic** (director whitelist = clear rule)

### Task 2: Reference Sorting (Manual Check)
- Cross-reference against Reference canon list
- Verify canonical status
- **This is manual verification**

### Task 3: Satellite Sorting (Category Identification)
- Identify exploitation/cult markers
- Apply category (giallo, pinku, Brazilian, etc.)
- Check caps
- **This requires some judgment**

### Task 4: Popcorn Sorting (Tonight Test)
- Apply rewatchability test
- Check format signals (35mm, open matte, etc.)
- **This requires judgment**

### Task 5: Staging Overflow
- Everything unclear goes here
- Monthly triage rule applies

---

## NEXT STEP

I will now begin parsing the movie list and creating the sorted breakdown.

**Starting with Core films (clearest rules)...**
