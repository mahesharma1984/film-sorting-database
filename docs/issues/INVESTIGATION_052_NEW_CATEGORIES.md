# Investigation: Issue #52 — New Satellite Category Candidates
## Session Notes, 2026-03-08

---

## 1. Scope

After Issue #51 removed Indie Cinema, Music Films, and Cult Oddities from auto-routing, 140 films in the organized library became `unroutable` — their physical location (Satellite/Indie Cinema or Satellite/Music Films) no longer corresponds to any active routing rule. The question is: are there coherent historical movements in this population that warrant new Satellite categories grounded in published film-historical scholarship?

This investigation maps the 140 films to candidate movements, evaluates density and scholarship grounding for each, and recommends which can proceed to category specification and which should remain in the review queue.

---

## 2. Method

Each film was assigned to a candidate movement based on:
- Production country and decade (structural coordinates)
- Director identity and documented movement membership
- Genre/subject matter

Candidates were then evaluated against the Add protocol (Rule 4, CLAUDE.md):
- **Density**: ≥3 films in collection (minimum for a category to be non-trivial)
- **Coherence**: films form an internally consistent population (same aesthetic/industrial tradition)
- **Archival necessity**: the category describes a real historical movement — it would exist as a description even if we removed all films from the collection
- **Scholarship**: a named published source grounds the category definition and director list

---

## 3. Candidate Movements

### 3.1 Czech New Wave (Czechoslovak New Wave)

**Collection films:**
| Film | Year | Director |
|---|---|---|
| Daisies | 1966 | Věra Chytilová |
| Ikarie XB 1 | 1963 | Jindřich Polák |
| When The Cat Comes | 1963 | Vojtěch Jasný |

Note: Two copies of Daisies (different encodes) — 3 distinct films, 2 unique directors.

**Movement:** The Czechoslovak New Wave (roughly 1963–1968, with a tail into the 1970s) is a well-defined national movement — formally experimental, politically allegorical, rooted in the brief liberalisation preceding the 1968 Warsaw Pact invasion. Chytilová, Forman, Menzel, Jasný, Schorm, Jireš are its canonical practitioners.

**Scholarship:**
- Peter Hames, *The Czechoslovak New Wave* (1985, revised University of California Press 2009) — the definitive English-language monograph
- Jonathan Owen, *Avant-Garde to New Wave: Czechoslovak Cinema, Surrealism and the Sixties* (Intellect, 2011)

**Assessment:** Strong scholarship grounding, coherent movement, tight decade bounds (1960s–1970s). Only 3 films currently — well below the density needed for auto-routing. **Recommend Tier 4 (SORTING_DATABASE-only).** Earn Tier 2 after corpus reaches 10+ films.

---

### 3.2 New Latin American Cinema

**Collection films:**
| Film | Year | Director | Country |
|---|---|---|---|
| Fin de fiesta | 1960 | Leopoldo Torre Nilsson | AR |
| El Romance Del Aniceto Y La Francisca | 1967 | Leonardo Favio | AR |
| El dependiente | 1969 | Rodolfo Kuhn | AR |
| La soldadera | 1967 | José Bolaños | MX |
| El Esqueleto De La Señora Morales | 1960 | Rogelio A. González | MX |
| El Escapulario | 1968 | unkn. | MX |
| Paraiso | 1970 | Luis Alcoriza | MX |
| The Castle of Purity | 1973 | Arturo Ripstein | MX |
| Juan Moreira | 1973 | Leonardo Favio | AR |
| Cecilia | 1982 | Humberto Solás | CU |
| Gatica, el mono | 1993 | Leonardo Favio | AR |
| Danzon | 1991 | María Novaro | MX |
| Herod's Law | 1999 | Luis Estrada | MX |
| Mango Yellow | 2002 | Cláudio Assis | BR |

14 films across Argentina, Mexico, Cuba, Brazil. Likely several more in the Unsorted queue.

**Movement:** "New Latin American Cinema" (Nuevo Cine Latinoamericano) is a documented pan-Latin movement originating in the late 1950s with Torre Nilsson and the Cuban revolutionary cinema of Tomás Gutiérrez Alea, gathering force through the 1960s-1970s with the "cinema of hunger" (Glauber Rocha, BR) and Mexican political cinema (Ripstein, Alcoriza), and continuing into the 1980s-1990s through individual national variants. Distinct industrial and aesthetic tradition: low-budget, politically engaged, influenced by Italian neorealism and French New Wave but rooted in Latin American social reality.

**Scholarship:**
- Ana M. López, "An 'Other' History: The New Latin American Cinema" in *Resisting Images* (1992) — foundational essay
- Michael Martin (ed.), *New Latin American Cinema* (2 vols., Wayne State University Press, 1997) — definitive anthology
- Julianne Burton (ed.), *Cinema and Social Change in Latin America* (University of Texas Press, 1986)
- John King, *Magical Reels: A History of Cinema in Latin America* (Verso, 2000)

**Assessment:** Strong scholarship, clear movement, good density (14 films identified, more likely in Unsorted). The multi-country scope is a structural challenge — no single `country_codes` gate isolates it cleanly (unlike Giallo with IT, or Pinku with JP). Director-driven routing is more appropriate here. **Recommend Tier 4 initially, Tier 2 via director-only structural gate** (similar to how FNW handles FR). Decade range: 1950s–1990s.

**Structural gate note:** Needs an explicit director list from the scholarship. Torre Nilsson, Favio, Ripstein, Alcoriza, Solás are confirmed. Requires research pass.

---

### 3.3 Korean New Wave

**Collection films:**
| Film | Year | Director |
|---|---|---|
| The Quiet Family | 1998 | Kim Jee-woon |
| Old Boy | 2003 | Park Chan-wook |
| Save the Green Planet | 2003 | Jang Joon-hwan |
| I'm A Cyborg But That's OK | 2006 | Park Chan-wook |
| The Good the Bad the Weird | 2008 | Kim Jee-woon |

5 films, 3 directors.

**Movement:** South Korean cinema underwent a dramatic renaissance beginning in the mid-1990s following the collapse of state censorship and the formation of new production companies. Directors including Park Chan-wook, Bong Joon-ho, Kim Jee-woon, Lee Chang-dong, and Hong Sang-soo developed a distinctive genre cinema — genre-inflected but formally adventurous, distinct from both Japanese and Hollywood models. "Korean New Wave" (sometimes "Korean Renaissance") describes this 1990s–2010s wave.

**Scholarship:**
- Chi-Yun Shin & Julian Stringer (eds.), *New Korean Cinema* (Edinburgh University Press, 2005) — the definitive English-language anthology
- Kyung Hyun Kim, *The Remasculinization of Korean Cinema* (Duke University Press, 2004)
- Darcy Paquet, *New Korean Cinema: Breaking the Waves* (Wallflower Press, 2009)

**Assessment:** Excellent scholarship grounding, globally recognised movement, coherent aesthetic and industrial tradition. 5 films currently — density is thin but the movement is real and more films are likely in the Unsorted queue. **Recommend Tier 4 initially.** Director list (Park Chan-wook, Bong Joon-ho, Kim Jee-woon, Hong Sang-soo, Lee Chang-dong) is well-established from scholarship.

---

### 3.4 Chinese Art Cinema — Fifth and Sixth Generations

**Collection films:**
| Film | Year | Director | Generation |
|---|---|---|---|
| Raise the Red Lantern | 1991 | Zhang Yimou | 5th |
| Farewell My Concubine | 1993 | Chen Kaige | 5th |
| Platform | 2000 | Jia Zhangke | 6th |
| Mountains May Depart | 2015 | Jia Zhangke | 6th |
| Long Day's Journey Into Night | 2018 | Bi Gan | 6th |

Note: Farewell My Concubine is currently in Music Films (wrong placement — it is a historical epic about Peking Opera, not a music film).

**Movement:** Two distinct waves. The Fifth Generation (1980s–1990s) emerged from the Beijing Film Academy's class of 1982 — Zhang Yimou, Chen Kaige, Tian Zhuangzhuang — making visually lush, historically allegorical films after the Cultural Revolution. The Sixth Generation (1990s–2010s) — Jia Zhangke, Zhang Yuan, Wang Xiaoshuai, Bi Gan — is more realist, urban, and underground, documenting post-socialist social transformation. Both generations are documented in dedicated scholarship.

**Scholarship:**
- Chris Berry & Mary Farquhar, *China on Screen: Cinema and Nation* (Columbia University Press, 2006)
- Jason McGrath, *Postsocialist Modernity: Chinese Cinema, Literature, and Criticism in the Market Age* (Stanford University Press, 2008)
- Sheldon Lu (ed.), *Transnational Chinese Cinemas* (University of Hawaii Press, 1997)
- Zhang Yingjin, *Chinese National Cinema* (Routledge, 2004)

**Note on Jia Zhangke:** Currently listed as a Core candidate ("potential additions," not yet in active whitelist). If added to Core, his films (Platform, Mountains May Depart) exit this category automatically and route to Core. The category still covers Fifth Generation (Zhang Yimou, Chen Kaige) and non-Core Sixth Generation directors.

**Assessment:** Well-grounded, two internally coherent sub-waves. Structural challenge: 5th and 6th Generation are meaningfully different — lumping them flattens a real distinction. Option A: single "Chinese Art Cinema" category (1980s–2020s, director-driven). Option B: two separate categories. **Recommend Tier 4 initially as a single "Chinese Art Cinema" entry**, defer 5th/6th split to a later audit once density is clearer.

---

### 3.5 New Japanese Cinema (1990s–2010s)

**Collection films:**
| Film | Year | Director |
|---|---|---|
| A Night in Nude | 1993 | Rokuro Mochizuki |
| Happiness of the Katakuris | 2001 | Takashi Miike |
| Survive Style 5+ | 2004 | Gen Sekiguchi |
| Kamikaze Girls | 2004 | Tetsuya Nakashima |
| Sawako Decides | 2010 | Yuya Ishii |
| Guilty of Romance | 2011 | Sion Sono |
| Helter Skelter | 2012 | Mika Ninagawa |
| Punk Samurai Slash Down | 2018 | Gakuryu Ishii |
| Labyrinth of Cinema | 2019 | Nobuhiko Obayashi |

9 films, 9 directors.

**Movement:** Japanese cinema of the 1990s–2010s saw a wave of genre-defying, formally experimental directors working outside (and sometimes within) the studio system. Takashi Miike, Sion Sono, Nobuhiko Obayashi's late period, and directors associated with the V-Cinema (direct-to-video) and independent scenes. Tom Mes and Jasper Sharp's *Midnight Eye Guide to New Japanese Film* (2005) is the definitive English-language source for this wave.

**Caution:** This candidate is broader and less historically cohesive than the others. "New Japanese Cinema" risks becoming a catch-all for Japanese films that don't fit Pinku Eiga or Japanese Exploitation — precisely the failure mode Issue #51 addressed. The population here includes horror (Miike), erotic thriller (Mochizuki), pop-art (Nakashima), extreme arthouse (Sono), and retrospective (Obayashi's 2019 film). That is not a movement — it is a residual.

**Assessment:** Scholarship exists but the collection films do not form a coherent movement. **Do not recommend as a new category.** Individual films should route to: Pinku Eiga (A Night in Nude — 1993 is outside the 1960s-1980s gate, which may need review), Japanese Exploitation (Miike), review queue (Sono, Ninagawa). The decade gate for Pinku Eiga (1960s-1980s) may be worth auditing — 1993 is still recognisably within the pink film industrial tradition.

---

## 4. Films That Belong Nowhere (Genuine Misplacements)

These films have no plausible Satellite category and should be moved to Unsorted or Popcorn:

**From Music Films — not music films:**
| Film | Actual subject |
|---|---|
| Wake in Fright (1971) | Australian outback thriller |
| Angela Davis Portrait of a Revolutionary (1972) | Political documentary |
| The Battle of Chile Part I (1975) | Political/historical documentary |
| The Complete Citizen Kane (1991) | Film-studies documentary |
| Val Lewton - The Man in the Shadows (2008) | Film-studies documentary |
| The Smashing Machine (2002) | MMA documentary |
| Adventures of Ford Fairlane (1990) | Action comedy |
| Bozzetto non troppo (2016) | Animation documentary |
| Buddha In Africa (2019) | Education documentary |

**From Indie Cinema — should be Popcorn:**
| Film | Reason |
|---|---|
| The Return of the Pink Panther (1975) | Blake Edwards commercial comedy |
| The Fantastic Four (1994) | Unlicensed Marvel adaptation (novelty/Popcorn) |
| Bordello of Blood (1996) | Tales from the Crypt franchise |

---

## 5. Summary and Recommendations

| Candidate | Films | Scholarship | Verdict | Tier |
|---|---|---|---|---|
| Czech New Wave | 3 | Hames (2009) | Proceed | Tier 4 |
| New Latin American Cinema | 14 | Martin (1997), Burton (1986), King (2000) | Proceed — priority | Tier 4 → Tier 2 |
| Korean New Wave | 5 | Shin & Stringer (2005), Paquet (2009) | Proceed | Tier 4 |
| Chinese Art Cinema | 5 | Berry & Farquhar (2006), McGrath (2008) | Proceed | Tier 4 |
| New Japanese Cinema | 9 | Mes & Sharp (2005) | Do not proceed — incoherent | — |

**Priority order:**
1. **New Latin American Cinema** — largest density (14 films), most robust scholarship, multi-decade span means more films will surface from the Unsorted queue
2. **Korean New Wave** — globally recognised movement, tight decade bounds, clear director roster from scholarship
3. **Chinese Art Cinema** — real movement, but needs a decision on 5th/6th Generation split before a structural gate can be written
4. **Czech New Wave** — valid but thin density; add as Tier 4 and wait for more films

---

## 6. Immediate Actions Enabled by This Investigation

Before new categories are implemented as Issue #52 specs:

1. **Fix Music Films misplacements** — 9 films above should have their SORTING_DATABASE pins removed or corrected. They will route to Unsorted, which is correct.
2. **Fix Popcorn misplacements** — Pink Panther, Fantastic Four, Bordello of Blood should be pinned to Popcorn.
3. **Farewell My Concubine** — currently in Music Films (wrong). If Chinese Art Cinema is added, it pins there. If not, it should go to Unsorted — it is not a music film.
4. **Thriller A Cruel Picture (1973)** — already identified as European Sexploitation. Single-film SORTING_DATABASE pin, no new category needed.

---

## 7. Feeds Into

**Issue #52 specification** should implement the 4 recommended new categories in priority order, following the `docs/ISSUE_SPEC_TEMPLATE.md` format. Each category spec requires:
- Published director roster from named scholarship
- Structural gates (country_codes, decades, genres)
- Minimum 3 SORTING_DATABASE anchor films before auto-routing is enabled
- Tier 4 entry with explicit pathway to Tier 2
