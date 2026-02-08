# IMPLEMENTATION GUIDE - HOW TO PHYSICALLY ORGANIZE YOUR COLLECTION

## Overview

This guide walks you through the actual process of reorganizing your movie library using the decade-wave structure.

**Time estimate:** 2-4 weeks (depending on collection size and review depth)

---

## BEFORE YOU BEGIN

### Prerequisites
□ **Backup your collection** - Full backup before any file moving
□ **Free disk space** - Ensure you have space for reorganization
□ **File manager ready** - Use a robust file manager (not just Windows Explorer)
□ **Sorting database open** - Have SORTING_DATABASE.md open for reference
□ **Core whitelist open** - Have CORE_DIRECTOR_WHITELIST_FINAL.md open

### Tools You'll Need
- **Spreadsheet software** (Excel, Google Sheets) for tracking progress
- **File manager with two-pane view** (Total Commander, Directory Opus, etc.)
- **Text editor** for notes
- **IMDb/Letterboxd** for director verification

---

## PHASE 1: CREATE FOLDER STRUCTURE

### Step 1.1: Create Base Directories

In your movie library root, create these folders:

```
/Library
   /1950s
   /1960s
   /1970s
   /1980s
   /1990s
   /2000s
   /2010s
/Staging
/Out
```

### Step 1.2: Create Tier Subdirectories

Inside each decade folder, create:
```
/[Decade]/Core
/[Decade]/Reference
/[Decade]/Satellite
/[Decade]/Popcorn
```

### Step 1.3: Create Core Director Folders

**For 1960s, create:**
```
/1960s/Core/Jean-Luc Godard
/1960s/Core/Jacques Rivette
/1960s/Core/Jean-Pierre Melville
/1960s/Core/Pier Paolo Pasolini
/1960s/Core/Seijun Suzuki
/1960s/Core/Jacques Demy
/1960s/Core/Stanley Kubrick
/1960s/Core/Federico Fellini
```

**For 1970s, create:**
```
/1970s/Core/John Cassavetes
/1970s/Core/Rainer Werner Fassbinder
/1970s/Core/Martin Scorsese
/1970s/Core/Francis Ford Coppola
/1970s/Core/Stanley Kubrick
/1970s/Core/Terrence Malick
/1970s/Core/Andy Warhol
[etc. - see full list in folder structure template]
```

Repeat for all decades. **Use CORE_DIRECTOR_WHITELIST_FINAL.md for complete list.**

### Step 1.4: Create Satellite Category Folders

**For 1970s (largest Satellite decade), create:**
```
/1970s/Satellite/Giallo
/1970s/Satellite/Pinku Eiga
/1970s/Satellite/Brazilian Exploitation
/1970s/Satellite/Hong Kong Action
/1970s/Satellite/American Exploitation
/1970s/Satellite/Russ Meyer
/1970s/Satellite/Blaxploitation
/1970s/Satellite/European Sexploitation
/1970s/Satellite/Music Films
/1970s/Satellite/Cult Oddities
```

Repeat for other decades, adjusting categories as needed.

### Step 1.5: Create Staging Subdirectories
```
/Staging/Borderline
/Staging/Unwatched
/Staging/Unknown
/Staging/Evaluate
```

### Step 1.6: Create Out Directory
```
/Out/Cut
```

**CHECKPOINT:** Your folder structure is now ready. Don't move any files yet.

---

## PHASE 2: SORT CORE FILMS (CLEAREST RULES)

Core films have the most mechanical sorting rules (director whitelist).

### Step 2.1: Open Core Director Whitelist

Have **CORE_DIRECTOR_WHITELIST_FINAL.md** open.

### Step 2.2: Sort by Director (Alphabetically)

Start with directors whose films are easiest to identify:

**High-confidence directors to start with:**
1. **Jean-Luc Godard** (~15 films)
   - Look for: Breathless, Vivre Sa Vie, Alphaville, Contempt, etc.
   - Move to appropriate decade: /[1960s-1980s]/Core/Jean-Luc Godard/

2. **Stanley Kubrick** (7-8 films)
   - Look for: 2001, Dr. Strangelove, The Shining, Full Metal Jacket, etc.
   - Move to: /[1960s-1990s]/Core/Stanley Kubrick/

3. **Martin Scorsese** (6 films)
   - Look for: Mean Streets, Taxi Driver, King of Comedy, After Hours, etc.
   - Move to: /[1970s-1980s]/Core/Martin Scorsese/

4. **Francis Ford Coppola** (4 films)
   - Look for: The Godfather (HBO cut), The Conversation, Apocalypse Now
   - Move to: /1970s/Core/Francis Ford Coppola/

5. **Edward Yang** (6 films)
   - Look for: Yi Yi, A Brighter Summer Day, Taipei Story, The Terrorizers
   - Move to: /[1980s-2000s]/Core/Edward Yang/

6. **Wong Kar-wai** (5+ films)
   - Look for: In the Mood for Love, Chungking Express, Fallen Angels
   - Move to: /[1990s-2000s]/Core/Wong Kar-wai/

7. **Satyajit Ray** (8 films)
   - Look for: Apur Sansar, The Music Room, Days and Nights in the Forest
   - Move to: /[1950s-1990s]/Core/Satyajit Ray/

### Step 2.3: Continue With All Core Directors

Work through the entire Core Director Whitelist alphabetically:
- Antonioni
- Cassavetes
- Coen Brothers
- Demy
- Fassbinder
- Fellini
- Godard
- Hartley
- Hou Hsiao-hsien
- Jarmusch
- Kubrick
- Lynch
- Malick
- Melville
- Pasolini
- Rivette
- Rohmer
- Ruiz
- Scorsese
- Suzuki
- Tarkovsky
- Yang
- Wong Kar-wai

**Process:**
1. Search your collection for films by this director
2. Verify year to determine decade
3. Move to /[Decade]/Core/[Director Name]/

### Step 2.4: Add Newly-Identified Core Directors

Add these directors to Core (from Phase 2 analysis):
- **Andy Warhol** → Move Flesh, Trash, Heat to /[1960s-1970s]/Core/Andy Warhol/
- **John Waters** → Move Serial Mom, Pecker to /1990s/Core/John Waters/
- **Michel Gondry** → Move Be Kind Rewind to /2000s/Core/Michel Gondry/
- **Satoshi Kon** → Move Tokyo Godfathers to /2000s/Core/Satoshi Kon/

### Step 2.5: Track Progress

Use a spreadsheet to track:
- Director name
- Films found
- Films moved
- Missing films from collection

**CHECKPOINT:** All Core films should now be in their decade/director folders.

---

## PHASE 3: SORT REFERENCE FILMS

Reference has clearest canonical status.

### Step 3.1: Use SORTING_DATABASE.md

Go through Reference section of sorting database.

### Step 3.2: Sort by Decade

**1930s-1940s Reference:**
- Citizen Kane (1941) → /1940s/Reference/ (create 1940s folder if needed)
- Casablanca (1942) → /1940s/Reference/
- It Happened One Night (1934) → /1930s/Reference/ (create if needed)
- Double Indemnity (1944) → /1940s/Reference/

**1950s Reference (Heavy Hitchcock):**
- Rear Window (1954) → /1950s/Reference/
- Vertigo (1958) → /1950s/Reference/
- North by Northwest (1959) → /1950s/Reference/
- Psycho (1960) → /1960s/Reference/ [Actually 1960]
- The Searchers (1956) → /1950s/Reference/
- Seven Samurai (1954) → /1950s/Reference/
- Rashomon (1950) → /1950s/Reference/
- All other Hitchcock films → /1950s/Reference/

**1970s Reference:**
- Chinatown (1974) → /1970s/Reference/
- Network (1976) → /1970s/Reference/
- Dog Day Afternoon (1975) → /1970s/Reference/

**1990s Reference:**
- Pulp Fiction (1994) → /1990s/Reference/
- The Silence of the Lambs (1991) → /1990s/Reference/
- The Matrix (1999) → /1990s/Reference/

### Step 3.3: Note Missing Reference Films

Track films you don't have but should acquire:
- Some Like It Hot (1959)
- Lawrence of Arabia (1962)
- The Graduate (1967)
- E.T. (1982)
- Schindler's List (1993)

**CHECKPOINT:** Reference tier should have ~35 films sorted, ~15 gaps noted.

---

## PHASE 4: SORT SATELLITE FILMS

Satellite requires category identification.

### Step 4.1: Sort by Category (Easiest First)

Start with most identifiable categories:

**A. Brazilian Exploitation (Easiest to Identify)**

All films with Portuguese titles, Brazilian production:
- Look for: "Os...", Brazilian director names, pornochanchada markers
- Sort by decade:
  - 1960s: Os Cafajestes → /1960s/Satellite/Brazilian Exploitation/
  - 1970s: Escola Penal, Dona Flor, etc. → /1970s/Satellite/Brazilian Exploitation/
  - 1980s: Rio Babilônia, O Império do Desejo → /1980s/Satellite/Brazilian Exploitation/

**NOTE:** 1970s Brazilian is over cap - need to identify 3 weakest to cut.

**B. Hong Kong Action/Category III**

Films with HK production, Cantonese/Mandarin titles:
- Angel Terminators, Peking Opera Blues, etc.
- Sort by decade:
  - 1970s: Drunken Master → /1970s/Satellite/Hong Kong Action/
  - 1980s: Shanghai Blues, Angel Terminators → /1980s/Satellite/Hong Kong Action/
  - 1990s: The Heroic Trio, Women on the Run → /1990s/Satellite/Hong Kong Action/

**C. Giallo (Italian Horror-Thriller)**

Italian directors (Bava, Argento, Martino), distinct aesthetic:
- A Bay of Blood, Your Vice Is a Locked Room, Strip Nude for Your Killer
- Sort by decade:
  - 1960s-1970s mostly
  - Move to: /[Decade]/Satellite/Giallo/

**D. Pinku Eiga (Japanese Pink Films)**

Japanese softcore/exploitation:
- Go Go Second Time Virgin, Inflatable Sex Doll, Zero Woman
- Sort by decade
- Move to: /[Decade]/Satellite/Pinku Eiga/

**E. American Exploitation/Grindhouse**

US exploitation (not Blaxploitation):
- Russ Meyer films → /[Decade]/Satellite/Russ Meyer/ (separate folder)
- Other exploitation → /[Decade]/Satellite/American Exploitation/

**F. Blaxploitation**

1970s Black action cinema:
- Coffy, Foxy Brown, Shaft, Hell Up in Harlem
- Move to: /1970s/Satellite/Blaxploitation/

**G. European Sexploitation**

European erotic cinema:
- Emanuelle films, Radley Metzger, etc.
- Move to: /[Decade]/Satellite/European Sexploitation/

**H. Music/Concert Films (Non-Core)**

Music docs not by Core directors:
- The Beatles docs, Rolling Stones, etc.
- Move to: /[Decade]/Satellite/Music Films/

**I. Cult Oddities (Catch-All)**

Everything that doesn't fit other categories:
- Weird films, VHS oddities, uncategorizable
- Move to: /[Decade]/Satellite/Cult Oddities/

### Step 4.2: Check Caps After Sorting

Review each Satellite category against caps:
- Brazilian: 45 cap (currently ~48 - CUT 3)
- HK Action: 65 cap (currently ~38 - OK)
- American Exploitation: 80 cap (currently ~65 - OK)
- Giallo: 30 cap (currently ~12 - OK)
- Pinku: 35 cap (currently ~10 - OK)

**Cut weakest films in over-cap categories to /Out/**

**CHECKPOINT:** All Satellite films categorized and under caps.

---

## PHASE 5: SORT POPCORN FILMS

Popcorn uses "tonight test" + format curation signals.

### Step 5.1: Look for Format Signals

**HIGH PRIORITY - 35mm Scans/Open Matte:**
- Spider-Man trilogy 35mm → /2000s/Popcorn/Spider-Man/
- Back to the Future trilogy 35mm → /1980s/Popcorn/Back to the Future/
- Batman (1989) 35mm → /1980s/Popcorn/Batman/
- Who Framed Roger Rabbit 35mm → /1980s/Popcorn/
- Se7en 35mm → /1990s/Popcorn/ [BORDERLINE: could be Reference]
- You Only Live Twice 35mm → /1960s/Popcorn/
- Drive Open Matte → /2010s/Popcorn/ [Check if Refn is Core first]

**If you have 35mm/open matte version, it's probably Popcorn.**

### Step 5.2: Apply "Tonight Test"

For each remaining film, ask:
"Would I actually put this on tonight for pleasure?"

**YES → Popcorn:**
- Rush Hour trilogy → /[1990s-2000s]/Popcorn/
- The Breakfast Club → /1980s/Popcorn/
- Weird Science → /1980s/Popcorn/
- Clue → /1980s/Popcorn/
- Explorers → /1980s/Popcorn/
- House Party → /1990s/Popcorn/
- Go (1999) → /1990s/Popcorn/

**NO → Not Popcorn** (check other tiers or Staging)

### Step 5.3: Organize Popcorn Internally

**Franchise folders for multi-film series:**
- /1980s/Popcorn/Back to the Future/ (3 films)
- /1980s/Popcorn/Batman/ (2+ films)
- /2000s/Popcorn/Spider-Man/ (4 films)
- /1990s/Popcorn/Rush Hour/ (3 films)

**Flat organization for single films:**
- /1980s/Popcorn/The Breakfast Club
- /1980s/Popcorn/Weird Science
- /1980s/Popcorn/Clue

**CHECKPOINT:** All clear Popcorn films sorted.

---

## PHASE 6: EVERYTHING ELSE → STAGING

### Step 6.1: Identify Staging Categories

Any film not yet sorted goes to Staging subdirectories:

**A. /Staging/Borderline**
Films that could go to multiple tiers:
- Buffalo '66 → Core (Gallo auteur) OR Popcorn?
- Se7en 35mm → Reference (canonical) OR Popcorn (format)?
- Re-Animator → Satellite (exploitation) OR Popcorn (rewatchable)?
- Various films needing your personal decision

**B. /Staging/Unwatched**
Films you haven't watched yet:
- Can't classify without viewing
- Watch first, then sort

**C. /Staging/Unknown**
Films with unclear metadata:
- Unknown director
- Unknown year
- Need research before classifying

**D. /Staging/Evaluate**
Films you're considering cutting:
- Low quality
- Redundant
- "Completionist" acquisitions
- Never watched in 2+ years

### Step 6.2: Move Everything Unclear to Staging

If you can't immediately determine the tier, move to Staging.

**Don't spend too long deciding - Staging is for later review.**

**CHECKPOINT:** Collection is now sorted into:
- Core folders ✓
- Reference folders ✓
- Satellite categories ✓
- Popcorn folders ✓
- Staging subdirectories ✓

---

## PHASE 7: STAGING TRIAGE (MONTHLY REVIEW)

Don't let Staging grow forever. Monthly review required.

### Step 7.1: Schedule Monthly Review

Set calendar reminder: "Movie Library Staging Review"

### Step 7.2: Review Borderline Films

For each film in /Staging/Borderline:
- Make a decision: Core, Reference, Satellite, or Popcorn?
- Move to appropriate tier
- If still unclear after 3 months → Cut to /Out

### Step 7.3: Watch Unwatched Films

For films in /Staging/Unwatched:
- Watch the film
- Classify based on experience
- Move to appropriate tier
- If you don't want to watch it → Cut to /Out

### Step 7.4: Research Unknown Metadata

For films in /Staging/Unknown:
- Look up director on IMDb
- Identify year/decade
- Check if director is on Core whitelist
- Classify and move
- If research takes >10 minutes → Low priority, evaluate later

### Step 7.5: Evaluate Potential Cuts

For films in /Staging/Evaluate:
- Apply "Would I ever watch this?" test
- If NO → Move to /Out
- If YES → Classify properly
- If MAYBE → Stay in Staging for next month

**RULE:** After 3 months in Staging, film must be promoted or cut.

---

## PHASE 8: ENFORCE CAPS & CUT TO /OUT

### Step 8.1: Check All Satellite Caps

Count films in each Satellite category:
- Giallo: Max 30
- Pinku: Max 35
- Brazilian: Max 45 (currently ~48 - CUT 3)
- HK Action: Max 65
- American Exploitation: Max 80
- European Sexploitation: Max 25
- Blaxploitation: Max 20
- Nunsploitation: Max 15
- WIP/Rape-Revenge: Max 15
- Music Films: Max 20
- Mondo: Max 10
- Cult Oddities: Max 50

### Step 8.2: Cut Weakest Films from Over-Cap Categories

**Brazilian Exploitation is over cap (48 vs. 45):**

Identify 3 weakest films:
- Lowest quality rips
- Least interesting content
- Most redundant within category
- Never rewatched

Move to /Out/Cut

### Step 8.3: Identify Other Cuts

Films to cut:
- Duplicate versions of same film
- Low-quality rips (< 480p, bad encoding)
- Completionist acquisitions (full filmographies you don't care about)
- Films kept "just in case" but never watched

Move all to /Out/Cut

### Step 8.4: Quarantine Period (30 Days)

**Do NOT delete files from /Out immediately.**

Wait 30 days.

If you realize you need a film back → Move it back.
After 30 days → Permanent deletion safe.

---

## PHASE 9: FINAL POLISH

### Step 9.1: Decade Coherence Check

Review each decade folder:
- Does 1960s feel like "modernist rupture"?
- Does 1970s reflect "political cinema + exploitation boom"?
- Does 1980s capture "postmodern genre + VHS cult"?
- Are there films that belong in adjacent decades?

Make adjustments if needed.

### Step 9.2: Verify Tier Ratios

Check that:
- Core is smallest and sharpest (tight auteur focus)
- Reference is capped at 50
- Satellite is largest (margins/texture)
- Popcorn is substantial but not bloated

### Step 9.3: Create README Files

For each decade, create a README.txt:

```
1970s CINEMA WAVE: Political Cinema + Exploitation Boom

CORE DIRECTORS:
- John Cassavetes (3 films)
- Rainer Werner Fassbinder (3 films)
- Martin Scorsese (4 films)
- Francis Ford Coppola (4 films)
[etc.]

SATELLITE BOUNDARIES:
- Brazilian exploitation capped at 25
- Giallo peak era (8 films)
- American grindhouse boom

NOTES:
- Heaviest Core decade (political cinema wave)
- Largest Satellite decade (exploitation boom)
- Keep tight, resist adding "important" films
```

---

## PHASE 10: MAINTENANCE SYSTEM

### Step 10.1: New Download Workflow

When you download a new film:

1. **Immediately move to /Staging/Unwatched**
2. Do NOT add to main library yet
3. Watch the film
4. Classify using decision tree
5. Move to appropriate tier

**NEVER let new downloads accumulate in a flat "Downloads" folder.**

### Step 10.2: Monthly Staging Review

Last Sunday of every month:
1. Review all files in /Staging subdirectories
2. Promote to tiers OR cut to /Out
3. Enforce: Nothing stays in Staging > 3 months

### Step 10.3: Annual Boundary Review

Once per year (January):
1. Review all Satellite caps
2. Cut weakest films if over cap
3. Review Core director whitelist - add/remove directors?
4. Review Reference gaps - acquisition priorities?
5. Update decade READMEs if needed

---

## TROUBLESHOOTING

### Problem: "I don't know the director of this film"
**Solution:** Move to /Staging/Unknown, research during monthly review

### Problem: "This film could be Core OR Satellite"
**Solution:** Move to /Staging/Borderline, decide during monthly review

### Problem: "I have 200 films in Staging"
**Solution:** Dedicate 2-3 hours to bulk review, be ruthless with cuts

### Problem: "I'm over cap in multiple Satellite categories"
**Solution:** Cut weakest films first (low quality, never rewatched, redundant)

### Problem: "A Core director's film feels like Satellite content"
**Solution:** Core tier wins - director on whitelist = automatic Core

### Problem: "Popcorn feels too small"
**Solution:** This is fine - collection is auteur/arthouse heavy by design

### Problem: "Should I add sub-folders within director folders?"
**Solution:** Only if director has 10+ films, otherwise keep flat

---

## SUCCESS METRICS

After full implementation:

□ **Core is tight** (~140 films, 26% of collection)
□ **Reference is capped** (50 films, 9% of collection)
□ **Satellite is largest** (~240 films, 45% of collection)
□ **Popcorn is substantial** (~100 films, 19% of collection)
□ **Staging is manageable** (<50 films at any time)
□ **1960s-1970s = collection spine** (48% of Core films)
□ **Every film has a reason** (auteur, canon, texture, pleasure)
□ **Browsable by decade** (historical coherence)
□ **Monthly review system active** (Staging doesn't grow)

---

## FINAL NOTES

### This Is a Process, Not a One-Time Task

- Budget 2-4 weeks for initial sort
- Budget 2-3 hours monthly for maintenance
- Budget 1 day annually for review

### The Library IS the Thesis

You're not just organizing files.

You're building a **cinema museum** that reflects:
- Modernist rupture (1960s)
- Political cinema (1970s)
- Postmodern margins (1980s-1990s)
- Studio canon (Popcorn)
- Exploitation texture (Satellite)

### Stay Ruthless

- When in doubt, cut to /Out
- Caps exist for a reason
- No "important" films without pleasure or purpose
- Staging must stay lean

### The System Works If You Maintain It

Monthly reviews are non-negotiable.

Without them, the library drifts back to chaos.

---

**Your decade-driven, wave-structured cinema archive is ready to implement.**

**Begin with Phase 1: Create Folder Structure.**

**Good luck. The library IS the thesis.**
