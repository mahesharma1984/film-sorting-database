# SATELLITE TIER - CATEGORY DEFINITIONS & CAPS

## Purpose
- Genre extremities, exploitation, cult oddities
- Kept intentionally but capped
- Texture, not spine
- This is the margins of cinema, not the center

---

## SATELLITE CATEGORIES (Identified from Collection)

### 1. GIALLO / ITALIAN HORROR-THRILLER

**Definition:**
- Italian genre cinema (horror, thriller, erotic thriller)
- 1960s-1980s peak
- Directors: Mario Bava, Dario Argento, Lucio Fulci, Sergio Martino, Michele Soavi, Umberto Lenzi

**Keyword signals (Issue #29):**
- TMDb tags: `giallo`, `italian horror`, `psychosexual thriller`, `black-gloved killer`
- Text terms: `giallo`, `stylized violence`, `voyeurism`, `whodunit`, `fetishism`, `italian genre`
- Routing tier: **A only** (keyword reinforces country+decade match; cannot route alone)

**Films in Collection:**
- Blood and Black Lace (likely Bava)
- A Bay of Blood (Bava)
- Your Vice Is a Locked Room and Only I Have the Key (1972)
- The Bloodstained Lawn (1973)
- Femina Ridens (1969)
- Strip Nude for Your Killer (1975)
- (Others likely)

**Cap per decade:**
- 1960s: max 5 films
- 1970s: max 15 films (peak era)
- 1980s: max 10 films
- **Total cap: 30 giallo films**

**Boundary rule:**
- If director becomes auteur obsession (e.g., full Argento retrospective), promote to Core
- Otherwise stays Satellite

---

### 2. PINKU EIGA / JAPANESE PINK FILMS

**Definition:**
- Japanese softcore/exploitation cinema
- 1960s-1980s
- Roman Porno, independent pink films
- Directors: Kōji Wakamatsu, Tatsumi Kumashiro, Noboru Tanaka, Yasuzō Masumura (Issue #6)

**Keyword signals (Issue #29):**
- TMDb tags: `pink film`, `roman porno`, `pinku eiga`, `nikkatsu`, `erotic drama`
- Text terms: `pink film`, `roman porno`, `erotica`, `softcore`, `pinku`, `nikkatsu`
- Routing tier: **A only** (keyword reinforces country+decade match; cannot route alone)

**Films in Collection:**
- Go Go Second Time Virgin (1969)
- Gate of Flesh (1964) - Seijun Suzuki (this is Core, not Satellite!)
- Inflatable Sex Doll of the Wastelands (1967)
- (Others likely)

**Cap per decade:**
- 1960s: max 10 films
- 1970s: max 15 films
- 1980s: max 10 films
- **Total cap: 35 pink films**

**Boundary rule:**
- Seijun Suzuki films → Core (he's on Core whitelist)
- Generic Roman Porno → Satellite
- Wakamatsu, Takechi → promote to Core if collection expands

---

### 3. JAPANESE EXPLOITATION (NEW - Issue #6)

**Definition:**
- Japanese yakuza, action, and crime films
- 1970s-1980s exploitation era
- Distinct from Pinku Eiga (erotic) - focuses on violence/action
- Directors: Kinji Fukasaku (Battle Royale, Battles Without Honor and Humanity series)

**Keyword signals (Issue #29):**
- TMDb tags: `yakuza`, `jidaigeki`, `toei`, `chambara`, `japanese crime film`
- Text terms: `yakuza`, `gang war`, `crime syndicate`, `organized crime`, `samurai`, `toei`
- Routing tier: **A only** (keyword reinforces country+decade match; cannot route alone)

**Films in Collection:**
- (To be classified)

**Cap per decade:**
- 1970s: max 15 films (peak yakuza era)
- 1980s: max 10 films
- **Total cap: 25 films**

**Boundary rule:**
- If director becomes auteur obsession (e.g., full Fukasaku retrospective), promote to Core
- Otherwise stays Satellite
- Focused on exploitation/genre works, not late career films

---

### 3b. JAPANESE NEW WAVE (NEW - Issue #33)

**Definition:**
- Japanese art cinema, political cinema, underground films
- Peak: 1960s–1970s (movement active c.1959–1975); extended: 1950s–1980s
- Distinct from Pinku Eiga (erotic) and Japanese Exploitation (genre action)
- Scholaraly grounding: Isolde Standish, *Japanese New Wave Cinema* (BFI, 2011);
  David Desser, *Eros Plus Massacre* (1988); Criterion "Japanese New Wave" collection

**Routing design:**
- **Director-only routing** — no country+genre+decade auto-match
- `country_codes: []` (like French New Wave) prevents all-Japanese-Drama auto-routing
- Without a director match, a Japanese 1960s Drama falls to Indie Cinema (JP is in its country_codes)

**Core directors (documented movement members):**
- Nagisa Oshima — *In the Realm of the Senses*, *Death by Hanging*, *Boy*
- Shûji/Shoji Terayama — *Throw Away Your Books, Rally in the Streets*, *Grass Labyrinth*
- Masao Adachi — *AKA Serial Killer*, *Red Army/PFLP*
- Yoshishige/Kiju Yoshida — *Eros + Massacre*, *Heroic Purgatory*, *Woman of the Lake*
- Masahiro Shinoda — *Pale Flower*, *Double Suicide*, *Demon Pond* (Shochiku Nouvelle Vague)
- Shôhei Imamura (early work only) — *Pigs and Battleships*, *The Insect Woman*
- Note: Seijun Suzuki is in the Core whitelist — his films route via Core check, not JNW routing

**Keyword signals (Issue #29):**
- TMDb tags: `japanese new wave`, `nuberu bagu`, `political cinema`, `underground film`, `avant-garde`
- Text terms: `new wave`, `underground`, `political`, `rebellion`, `nuberu bagu`
- Routing tier: **director match only** (tier_b_eligible: False — movement requires director evidence)

**Overlap/split rules:**
- Wakamatsu's pink films → Pinku Eiga (via SORTING_DATABASE pins; director appears in both lists)
- Late Imamura (Narayama 1983, Black Rain 1989) → Indie Cinema (pinned in SORTING_DATABASE)
- Fukasaku yakuza films → Japanese Exploitation (Doberman Cop, Battles Without Honor)
- Teshigahara (*Woman in the Dunes*) → Core candidate (pending whitelist promotion; Indie Cinema fallback)

**Cap:**
- **Total cap: 15 films** (tighter than Giallo at 30 — specialized movement)

**Boundary rule:**
- If director becomes full auteur obsession (complete Oshima, complete Yoshida), promote to Core
- Late/post-movement work by JNW directors → Indie Cinema via SORTING_DATABASE pin

---

### 4. BRAZILIAN PORNOCHANCHADA / EXPLOITATION

**Keyword signals (Issue #29):**
- TMDb tags: `pornochanchada`, `boca do lixo`, `brazilian exploitation`
- Text terms: `pornochanchada`, `chanchada`, `boca do lixo`, `embrafilme`, `erotic comedy`
- Routing tier: **A only** — note: expected low hit rate (TMDb/OMDb coverage of Brazilian exploitation is thin). Keywords are supplementary to the primary country+decade routing gate.

**Definition:**
- Brazilian erotic comedies and exploitation
- Boca do Lixo cinema tradition
- Pornochanchada peak: 1970–1989; broader tradition: 1960s–1990s (WIDENED - Issue #20)
- Pre-pornochanchada roots visible in mid-1960s genre films (e.g., O Padre e a Moça, 1966); tradition extends to early 1990s (e.g., Vai Trabalhar Vagabundo II, 1991)

**Films in Collection:**
- Escola Penal de Meninas Violentadas (1977)
- O Olho Mágico do Amor (1982)
- O Império do Desejo (1981)
- A Super Fêmea (1973)
- Os Homens que Eu Tive (1973)
- Toda Nudez Será Castigada (1973)
- Rio Babilônia (1982)
- Vai Trabalhar Vagabundo! (likely)
- as intimidades de analu e fernanda (1980)
- 1976 - Amadas e Violentadas
- 1978 - Noite em Chamas
- 1978 - A Força dos Sentidos
- 1981 - Karina, Objeto de Prazer
- 1984 - Estranho Desejo
- 1983 - Tchau, Amor
- 1976 - Possuídas pelo Pecado
- 1979 - A Mulher que Inventou o Amor
- 1979 - A Ilha dos Prazeres Proibidos
- (Many more in collection)

**Cap per decade:**
- 1960s: max 5 films (pre-pornochanchada roots)
- 1970s: max 25 films (boom era)
- 1980s: max 20 films
- 1990s: max 5 films (late tradition)
- **Total cap: 45 Brazilian exploitation films** (caps redistributed, total unchanged)

**Boundary rule:**
- Carlos Reichenbach, Rogério Sganzerla, Júlio Bressane → Core auteurs
- Generic pornochanchada → Satellite
- Ozualdo Candeias → Core if collection expands

---

### 5. HONG KONG ACTION / MARTIAL ARTS / CATEGORY III

**Keyword signals (Issue #29):**
- TMDb tags: `martial arts`, `wuxia`, `kung fu`, `triad`, `heroic bloodshed`, `shaw brothers`, `hong kong action`
- Text terms: `martial arts`, `kung fu`, `wuxia`, `swordplay`, `triad`, `heroic bloodshed`, `shaw brothers`, `golden harvest`, `category iii`
- Routing tier: **A only** (keyword reinforces country+decade match; cannot route alone)

**Definition:**
- HK genre cinema outside of Core auteurs (Wong Kar-wai, Johnnie To, Ann Hui)
- Martial arts, action, Category III exploitation
- 1970s-1990s
- Directors: Tsui Hark, Ringo Lam, John Woo, Lam Nai-Choi (Issue #6)

**Films in Collection:**
- Drunken Master (1978)
- Rush Hour Trilogy (1990s-2000s) - actually Popcorn?
- Angel Terminators (1987)
- Angel Terminators 2
- Women on the Run (1993)
- She Shoots Straight (1990)
- Red Wolf (1995)
- The Seventh Curse (1986)
- Erotic Ghost Story (1990)
- Erotic Ghost Story II (1991)
- Erotic Ghost Story III (1992)
- The Heroic Trio (1993)
- So Close (2002)
- Curry and Pepper (1990)
- Shanghai Blues (1984)
- Peking Opera Blues (1986)
- Robotrix (1991)
- Once a Thief (1991)
- The Cat (1992)
- Beyond Hypothermia (1996)
- Iceman Cometh (1989)
- My Heart is That Eternal Rose (1989)
- Girls Without Tomorrow (1988)
- Center Stage (1991) - Stanley Kwan (Core auteur?)
- Green Snake (1993) - Tsui Hark
- Perfect Match (1991)
- (Many more)

**Cap per decade:**
- 1970s: max 10 films
- 1980s: max 20 films
- 1990s: max 25 films (peak HK action boom)
- 2000s: max 10 films
- **Total cap: 65 HK genre films**

**Boundary rule:**
- Wong Kar-wai, Johnnie To, Ann Hui → Core
- Tsui Hark, Ringo Lam, Lam Nai-Choi → Satellite (genre masters, not auteurs)
- Jackie Chan → Satellite unless it's a Core auteur collaboration
- Category III exploitation → Satellite

---

### 6. AMERICAN NEW HOLLYWOOD (NEW - Issue #27)

**Keyword signals (Issue #29):**
- TMDb tags: `new hollywood`, `american new wave`, `counterculture`, `post-code`
- Text terms: `new hollywood`, `new american cinema`, `post-production code`, `counterculture`, `vietnam era`, `anti-establishment`
- Routing tier: **A and B** — Tier B eligible because "new hollywood" and "american new wave" as TMDb tags are movement-specific enough to route without a director match. Text terms alone are insufficient for Tier B.

**Definition:**
- Post-Production Code prestige studio cinema, c.1965–1985
- The bounded industrial moment when a generation of directors reshaped American studio filmmaking between the collapse of the Code and the blockbuster era
- Distinct from American Exploitation (grindhouse/cult) and from Core (auteur identity)

**Date bounds:** 1960s–1980s (captures 1965–1985 span across three system decades)

**Directors (routing gate — widest configuration):**
- **Category Core:** Bob Fosse, Hal Ashby, Alan J. Pakula
- **Category Reference:** Sydney Pollack, Sidney Lumet, Peter Bogdanovich, Robert Altman
- **Overlapping Core candidates:** Francis Ford Coppola, Martin Scorsese
  - NOTE: Coppola and Scorsese are also strong Core whitelist candidates. With Satellite routing firing before Core (Issue #25), their 1960s–1980s films route to Satellite/AmNH when they match the decade and director gate. Their post-movement work (1990s+) falls through to the Core director check. Prestige films by either director can be pinned to Core via SORTING_DATABASE.md entries, which fire before Satellite routing.

**Cap:** 25 films

**Cap per decade:**
- 1960s: max 5 films (only late-60s: 1965–1969)
- 1970s: max 15 films (peak of the movement)
- 1980s: max 5 films (movement fading into blockbuster era)

**Rationale:**
- Without this category, Fosse and Russ Meyer end up in the same folder (American Exploitation), collapsing the distinction between a prestige auteur and a grindhouse specialist
- Density: 15–25 films in the collection currently misfiled in AmEx, Indie Cinema, or Unsorted
- Coherence: documented historical movement with identifiable directors and a bounded industrial moment
- Archival necessity: the collection needs this distinction to be meaningful

**Boundary rules:**
- Fosse, Ashby, Pakula → Satellite/American New Hollywood (Category Core)
- Pollack, Lumet, Bogdanovich, Altman → Satellite/American New Hollywood (Category Reference)
- Coppola, Scorsese → Core if on whitelist; otherwise Satellite/American New Hollywood
- Russ Meyer → American Exploitation (genre specialist, not prestige cinema)
- John Waters → American Exploitation or Core (depending on collection expansion)
- Generic 1970s US dramas without a listed director → Unsorted (no country-gate; director-only routing like FNW)

**Routing design:** Director-only routing (like French New Wave). US ('US') is NOT added to `COUNTRY_TO_WAVE` — that would auto-route all American films in those decades. Only films by listed directors qualify.

**Routing position:** Before American Exploitation in `SATELLITE_ROUTING_RULES`. Both are US historical categories, but American New Hollywood is more specific — it must be checked first to prevent its films from being caught by AmEx's broader net.

**Films currently in collection that belong here (examples):**
- All That Jazz (1979) — currently misclassified as Indie Cinema
- Being There (1979) — currently misclassified as Indie Cinema
- (Full audit of ~15–25 misfiled films to be completed as part of Issue #23 Stage 3)

---

### 7. AMERICAN EXPLOITATION / GRINDHOUSE / VHS CULT

**Keyword signals (Issue #29):**
- TMDb tags: `grindhouse`, `exploitation film`, `b-movie`, `troma`, `slasher`, `drive-in movie`
- Text terms: `grindhouse`, `drive-in`, `exploitation`, `splatter`, `gore`, `b-movie`, `troma`, `low budget horror`
- Routing tier: **A only** — supplements the existing title keyword gate; keyword evidence is additive, not a replacement for the gate.

**Definition:**
- American exploitation, grindhouse, direct-to-video cult
- 1960s-2000s (extended to include Larry Clark's 1990s-2000s work)
- Not auteur-driven, not rewatchable American entertainment (that's Popcorn)
- Directors: Russ Meyer, Abel Ferrara, Larry Cohen, Herschell Gordon Lewis, Larry Clark (Issue #6)

**Films in Collection:**
- Faster Pussycat! Kill! Kill! (1965) - Russ Meyer
- Supervixens (1975) - Russ Meyer
- Vixen (1968) - Russ Meyer
- Beneath the Valley of the Ultra Vixens (1979) - Russ Meyer
- Cherry Harry & Raquel (1970) - Russ Meyer
- Hollywood Chainsaw Hookers (1988)
- Frankenhooker (1990)
- Re-Animator (1985) - actually this might be Popcorn?
- From Beyond (1986)
- Society (1989)
- Brain Damage (1988)
- The Brain That Wouldn't Die (1962)
- Ms 45 (1981) - Abel Ferrara (Core auteur?)
- Wild Zero (1999)
- Freaks of Nature (2015)
- Werewolf Bitches From Outer Space (2016)
- Turkey Shoot (1982)
- Teenage Gang Debs (1966)
- The Violent Years (1956)
- Troma's War (1988)
- Switchblade Sisters (1975)
- Christmas Evil (1980)
- Mixed Blood (1984)
- Plan 9 From Outer Space (1959)
- Attack of the 50 ft. Woman
- Terminal City Ricochet (1990)
- (Many more)

**Cap per decade:**
- 1960s: max 10 films
- 1970s: max 20 films (grindhouse peak)
- 1980s: max 25 films (VHS boom)
- 1990s: max 15 films
- 2000s-2010s: max 10 films
- **Total cap: 80 American exploitation films**

**Boundary rule:**
- Russ Meyer → Satellite (genre specialist, not Core auteur)
- Abel Ferrara → Core (if collection expands with King of New York, Bad Lieutenant)
- Larry Clark → Satellite (transgressive exploitation: Kids, Bully, Ken Park)
- Generic exploitation → Satellite
- John Waters → Core (if collection expands)
- Troma → Satellite (always)

---

### 8. NUNSPLOITATION / RELIGIOUS EXPLOITATION

**Definition:**
- Exploitation films with religious/convent themes
- 1970s mostly
- European + American

**Films in Collection:**
- Nasty Habits: The Nunsploitation Collection (Severin box set)
- (Others in collection?)

**Cap:**
- **Total cap: 15 films** (niche subgenre, keep curated)

---

### 9. EUROPEAN SEXPLOITATION / ARTHOUSE-ADJACENT EROTICA

**Keyword signals (Issue #29):**
- TMDb tags: `erotic film`, `softcore`, `sexploitation`, `european erotica`
- Text terms: `erotic film`, `softcore`, `erotica`, `sexploitation`, `adult film`, `european erotica`
- Routing tier: **A only** (keyword reinforces country+decade+genre match; cannot route alone)

**Definition:**
- European erotic cinema that's not quite auteur, not quite pure exploitation
- 1960s-1980s
- Directors: Just Jaeckin, Walerian Borowczyk, Radley Metzger, Tinto Brass, Roger Vadim (Issue #6)

**Films in Collection:**
- Emanuelle series (likely)
- Immoral Tales (Borowczyk - actually might be Core?)
- The Seduction of Angela (Cinemax)
- Love Rites (1987)
- Ars amandi (1983)
- The Awakening of Annie (1976)
- (Others)

**Cap per decade:**
- 1960s-1970s: max 15 films
- 1980s: max 10 films
- **Total cap: 25 European sexploitation films**

**Boundary rule:**
- Walerian Borowczyk → Core auteur
- Radley Metzger, Roger Vadim → Satellite (genre specialists)
- Generic eurotica → Satellite or cut

---

### 10. BLAXPLOITATION

**Keyword signals (Issue #29):**
- TMDb tags: `blaxploitation`, `african american`, `inner city`, `black power`
- Text terms: `blaxploitation`, `soul`, `ghetto`, `black power`, `inner city`, `african american exploitation`
- Routing tier: **A only** — supplements the existing title keyword gate.

**Definition:**
- 1970s Black action/exploitation cinema (extended to 1990s for Ernest Dickerson - Issue #6)
- Not auteur-driven (those would be Core)
- Directors: Gordon Parks, Jack Hill, Ernest R. Dickerson (Juice, Tales from the Hood)

**Films in Collection:**
- Coffy (1973)
- Foxy Brown (1974)
- Shaft (1971)
- Hell Up in Harlem (1973)
- (Others?)

**Cap per decade:**
- 1970s: max 15 films (classic blaxploitation era)
- 1990s: max 5 films (Ernest Dickerson era)
- **Total cap: 20 blaxploitation films**

**Boundary rule:**
- Gordon Parks → Core if collection expands
- Ernest R. Dickerson → Satellite (extends tradition into 1990s)
- Generic blaxploitation → Satellite

---

### 11. WOMEN IN PRISON / RAPE-REVENGE / FEMINIST EXPLOITATION

**Definition:**
- WIP films, rape-revenge, exploitation with feminist readings
- 1970s-1980s mostly

**Films in Collection:**
- Escola Penal de Meninas Violentadas (1977) - overlaps with Brazilian
- Ms 45 (1981)
- Savage Streets (1984)
- I Spit on Your Grave (likely?)
- (Others)

**Cap:**
- **Total cap: 15 films** (keep selective, avoid pure misery)

---

### 12. MUSIC / CONCERT FILMS (NON-CORE)

**Keyword signals (Issue #29):**
- TMDb tags: `concert film`, `rockumentary`, `musical performance`, `rock documentary`
- Text terms: `concert film`, `rockumentary`, `music documentary`, `live performance`
- Routing tier: **A only** — supplements the genre gate (Music/Musical/Documentary).

**Definition:**
- Concert films, music documentaries not by Core directors
- Scorsese's The Last Waltz → Core
- Others → Satellite

**Films in Collection:**
- The Beatles - First U.S. Visit
- The Rolling Stones Rock and Roll Circus (1996)
- Louie Bluie (Terry Zwigoff 1985) - actually Core auteur?
- 200 Motels (1971) - Frank Zappa
- Tommy (1975)
- (Others)

**Cap:**
- **Total cap: 20 music films**

---

### 13. MONDO / SHOCKUMENTARY

**Definition:**
- Mondo films, shockumentaries, documentary exploitation
- 1960s-1980s

**Films in Collection:**
- (Need to check if Mondo Cane, etc. are present)

**Cap:**
- **Total cap: 10 films** (niche, keep tight)

---

### 14. CULT ODDITIES / UNCATEGORIZABLE

**Definition:**
- Films that don't fit other Satellite categories
- VHS-era oddities, late-night cable, pure weirdness

**Films in Collection:**
- Zeroville (2019)
- Vibrations (1996)
- Skidoo (1968)
- Head (likely 1968)
- The Forbidden Zone (likely)
- Santa Sangre (1989) - Jodorowsky (Core auteur!)
- El Topo (1970) - Jodorowsky (Core!)
- Werewolf Bitches From Outer Space (2016)
- Italian Spiderman (2007)
- Roofman
- (Many more)

**Cap:**
- **Total cap: flexible, absorbs overflow** (max 50 films)

**Boundary rule:**
- Jodorowsky → Core
- Pure oddities → Satellite
- If film has cult following but no auteur claim → here

---

### 15. FRENCH NEW WAVE (NEW - Issue #14)

**Keyword signals (Issue #29):**
- TMDb tags: `nouvelle vague`, `french new wave`, `new wave`, `cinéma vérité`, `cinema verite`
- Text terms: `nouvelle vague`, `new wave`, `jump cut`, `cinéma vérité`, `left bank`, `french new wave`
- Routing tier: **A and B** — Tier B eligible because "nouvelle vague" and "french new wave" as TMDb tags are movement-specific enough to route without a director match. Text terms alone are insufficient for Tier B.

**Definition:**
- French art cinema from the Nouvelle Vague movement
- Non-Core directors who participated in or orbited the movement
- 1958-1973 (from Breathless to post-May '68 decline)

**Directors:**
- Chris Marker (La jetée, Sans Soleil)
- Eric Rohmer (Six Moral Tales)
- Alain Resnais (Last Year at Marienbad) - if not Core
- Jacques Rivette (if not Core)
- Louis Malle (Elevator to the Gallows)

**Cap:** 30 films

**Rationale:**
- Textural context for Core Godard/Varda
- Analogous to Giallo providing context for Italian modernism
- Prevents misrouting to European Sexploitation

**Boundary rules:**
- Godard, Varda → Core (already on whitelist)
- Marker, Rohmer, Resnais → Satellite (unless promoted to Core)
- Reference-level films (Hiroshima Mon Amour) → may override to Reference

---

### 16. INDIE CINEMA (NEW - Issue #14, WIDENED - Issue #20)

**Keyword signals (Issue #29):** NONE — no keyword routing.

Indie Cinema is a **negative-space category** defined by what it is NOT (not exploitation, not Popcorn mainstream, not Core auteur, not a named historical movement). No keyword set can define it positively without widespread false positives: "art house", "independent film", "festival film" all appear in texts about Core auteurs, French New Wave films, and prestige Popcorn alike. Indie Cinema is reached structurally — when all other satellite routing fails — and keyword signals cannot accelerate or improve this. See `docs/theory/MARGINS_AND_TEXTURE.md` §8.

**Definition:**
- Functional arthouse catch-all for non-exploitation, non-Popcorn, non-Core films
- NOT a historical wave category — defined negatively by what it is NOT
- Covers international art/character-driven films from 30+ countries, 1960s–2020s
- Issue #20: expanded from post-1980 to 1960s–2020s; added CN, TW, KR, IR, JP, HU, IN, RO

**Directors (examples):**
- US: Jim Jarmusch, Hal Hartley, Kelly Reichardt, Todd Haynes
- International: Michael Haneke, Lars von Trier, Ken Loach

**Cap:** 40 films (review after Issue #20 expansion — scope has broadened)

**Rationale:**
- Fills gap between Core (auteur obsession) and Popcorn (mainstream entertainment)
- Unlike Giallo or Brazilian Exploitation (historical events with specific start/end dates),
  Indie Cinema is a functional routing label. It is analogous to Music Films (no decade
  restriction) — organized by what it serves, not what historical moment it names.
- JP in 1970s–1980s still routes to Pinku Eiga/Japanese Exploitation first; JP here only
  catches post-1980s Japanese films that fall through those categories.

**Boundary rules:**
- Coen Brothers, Lynch, P.T. Anderson → Core (on whitelist)
- Unknown indie dramas from covered film countries → Indie Cinema
- Mainstream studio films → Popcorn
- Exploitation directors' post-category films → Indie Cinema (decade bounds respected)

---

### 17. CLASSIC HOLLYWOOD (NEW - Issue #14)

**Keyword signals (Issue #29):**
- TMDb tags: `film noir`, `pre-code`, `golden age of hollywood`, `screwball comedy`, `classical hollywood`
- Text terms: `film noir`, `golden age`, `studio system`, `pre-code`, `screwball comedy`, `hays code`
- Routing tier: **A only** — supplements the country+decade gate (US 1930s-1950s is already a tight structural gate; keywords confirm genre classification within that window).

**Definition:**
- American studio cinema from classical era
- Pre-1960 (before New Hollywood rupture)
- Genre cinema: Film Noir, Westerns, Musicals, Melodrama

**Cap:** 25 films

**Rationale:**
- Reference canon only covers ~10 classic Hollywood films (Casablanca, Sunset Blvd)
- Genre classics that aren't Reference-tier but provide historical context
- Films like The Searchers, Sweet Smell of Success, Touch of Evil (if not by Core directors)

**Boundary rules:**
- Orson Welles, Billy Wilder → Core (if on whitelist)
- Canonical classics → Reference (Casablanca, Citizen Kane)
- Genre classics → Satellite (The Big Sleep, Out of the Past)

---

### 18. HONG KONG NEW WAVE (NEW - Issue #34)

**Movement:** Hong Kong New Wave (late 1970s–1990s) — art cinema emerging alongside but distinct from the genre-action tradition. David Bordwell's "Planet Hong Kong" (2000) is the primary scholarly reference. Criterion selections (Rouge, Center Stage) confirm institutional recognition.

**Decade bounds:** 1970s–1990s (movement active 1979–1997, pre-handover era)

**Routing:** Director-only (like French New Wave). No country+genre auto-match — too many HK films would catch.

**Directors:** Ann Hui, Patrick Tam, Allen Fong, Stanley Kwan, Peter Ho-Sun Chan, Clara Law, Yim Ho.
Note: Wong Kar-wai and Johnnie To are Core directors — their films route to Core, not here.

**Cap:** 15 films. **Certainty tier:** 2 (director-anchored movement).

**Boundary with HK Action:** Action genre films (Tsui Hark, John Woo, Ringo Lam) → HK Action. Drama/romance/art films by the above directors → HK New Wave. Use SORTING_DATABASE pins to resolve per-film ambiguity.

---

### 19. HONG KONG CATEGORY III (NEW - Issue #34)

**Classification:** MPIA Category III rating (1988+) — films made to exploit Hong Kong's adult-content rating, typically erotic horror or supernatural erotica. Real institutional classification system with distinct commercial identity.

**Routing:** MANUAL CURATION ONLY via SORTING_DATABASE pins. No auto-routing — ratings system ≠ genre, and country+genre combos would produce false positives.

**Cap:** 10 films. **Certainty tier:** 4 (manual only).

**Boundary with HK Action:** Films like Green Snake (Tsui Hark) are Category III despite the director being in HK Action. SORTING_DATABASE pin overrides director routing.

---

## TOTAL SATELLITE CAPS BY CATEGORY

1. Giallo: 30 films
2. Pinku eiga: 35 films
3. Japanese New Wave: 15 films (Issue #33)
4. Japanese Exploitation: 25 films (Issue #6)
5. Brazilian exploitation: 45 films
6. Hong Kong New Wave: 15 films (NEW - Issue #34)
7. Hong Kong Category III: 10 films (NEW - Issue #34)
8. Hong Kong Action: 65 films
9. **American New Hollywood: 25 films** (Issue #27)
10. American exploitation/grindhouse: 80 films (NARROWED - Issue #14: now 1960s-1980s only)
11. Nunsploitation: 15 films
12. European sexploitation: 25 films
13. Blaxploitation: 20 films
14. WIP/rape-revenge: 15 films
15. Music/concert films: 20 films
16. Mondo: 10 films
17. Cult oddities: 50 films
18. **French New Wave: 30 films** (Issue #14)
19. **Indie Cinema: 40 films** (Issue #14)
20. **Classic Hollywood: 25 films** (Issue #14)

**TOTAL SATELLITE CAP: ~560 films maximum across 20 categories**

This is intentionally large because Satellite is the margins/texture tier. But individual category caps keep it from sprawling.

---

## SATELLITE ORGANIZATION (Issue #6 Update)

**New Structure: Category-First (Satellite/{category}/{decade}/)**

Based on Issue #6 implementation, Satellite is now organized by category first, then decade:

```
Satellite/
├── Giallo/
│   ├── 1960s/
│   ├── 1970s/
│   └── 1980s/
├── Pinku Eiga/
│   ├── 1960s/
│   ├── 1970s/
│   └── 1980s/
├── Japanese Exploitation/
│   ├── 1970s/
│   └── 1980s/
├── Brazilian Exploitation/
│   ├── 1960s/
│   ├── 1970s/
│   ├── 1980s/
│   └── 1990s/
├── Hong Kong Action/
│   ├── 1970s/
│   ├── 1980s/
│   └── 1990s/
├── American Exploitation/
│   ├── 1960s/
│   ├── 1970s/
│   ├── 1980s/
│   ├── 1990s/
│   └── 2000s/
├── European Sexploitation/
│   ├── 1960s/
│   ├── 1970s/
│   └── 1980s/
├── Blaxploitation/
│   ├── 1970s/
│   └── 1990s/
└── Music Films/
    └── (decade-agnostic)
```

**Rationale:**
- Browse all Giallo together, all Pinku Eiga together, etc.
- Decades are subdivisions WITHIN each thematic category
- More intuitive navigation than decade-first structure

---

## BOUNDARY ENFORCEMENT RULES

### What Qualifies for Satellite?

**YES:**
- Genre extremities (giallo, pinku, exploitation)
- Cult films without auteur claim
- VHS/grindhouse texture
- Category filmmaking (HK action, blaxploitation)
- Films kept for margins/context, not spine

**YES (Core director's movement-period films):**
- A Core director's films in their documented movement period route to Satellite, not Core
- Examples: Godard 1960s–1970s → Satellite/French New Wave; Scorsese 1970s → Satellite/American New Hollywood
- The director must be listed in that movement's SATELLITE_ROUTING_RULES director list
- Exception: films added to SORTING_DATABASE.md with an explicit Core destination bypass Satellite entirely

**NO (goes to Core instead):**
- A Core director's films pinned in SORTING_DATABASE.md (their most important work — manually curated)
- A Core director's non-movement work (decade gate fails — film's year outside movement bounds)
- Auteur-driven cult without movement membership (Jodorowsky, Waters)
- Films that define your collection identity

**NO (goes to Popcorn instead):**
- Rewatchable American entertainment
- Studio films you return to for pleasure
- Format-curated mainstream (35mm open matte Spider-Man)

**NO (gets cut to /Out):**
- Pure obligation, no pleasure
- Redundant within category (e.g., 10th generic giallo)
- Low-quality exploitation you don't care about

---

## PER-DECADE SATELLITE DENSITY

Based on collection analysis:

**1960s Satellite: ~30 films**
- Early exploitation, giallo origins, pinku eiga

**1970s Satellite: ~150 films** (largest wave)
- Brazilian pornochanchada boom
- Giallo peak
- American grindhouse
- Blaxploitation
- Pinku eiga peak

**1980s Satellite: ~120 films**
- VHS cult boom
- HK action explosion
- Late giallo/Italian horror
- American DTV exploitation

**1990s Satellite: ~80 films**
- HK action peak (pre-handover)
- Late exploitation
- DTV cult

**2000s-2010s Satellite: ~30 films**
- Selective cult oddities
- Digital-era exploitation

**TOTAL SATELLITE ESTIMATE: ~410 films** (within caps)

---

## CRITICAL NOTES

### Satellite ≠ Dump Tier
- Every film in Satellite should be there intentionally
- "I want this texture in my archive" not "I guess I'll keep it"
- When in doubt, cut to /Out

### Satellite Expands Core
- Satellite shows what orbits around your auteur spine
- It's the margins that make Core feel centered
- But it can't overwhelm Core

### Monthly Review
- Check if any Satellite category is over cap
- Cut weakest films in that category
- Resist "but it's rare!" unless you actually care

---

## NEXT STEPS

1. Verify current Satellite film count per category
2. Adjust caps if needed
3. Move to Phase 1, Task 4: Popcorn Rules

**Does this Satellite structure work? Any categories to add/remove/adjust?**
