# Investigation: Category Redesign — Two-Signal System Alignment
## Session Notes, 2026-03-06

---

## 1. How We Got Here

This investigation began during Issue #49 (dashboard refocus). Stripping the dashboard to a two-signal health monitor forced a direct confrontation with the accuracy numbers. What was visible was not reassuring:

| Reason code | Films | Accuracy |
|---|---|---|
| `both_agree` | 42 | 73.8% |
| `director_disambiguates` | 51 | 52.9% |
| `director_signal` | 37 | 73.0% |
| `structural_signal` | 304 | 67.4% |
| `review_flagged` | 125 | 65.6% |
| `popcorn` | 45 | 66.7% |
| `user_tag_recovery` | 29 | 86.2% |

The combined accuracy (scholarship_only contract, 796 films): **53.6%**. Nearly half of all classifications are wrong when measured against the organised library.

The initial interpretation was that this reflects contamination from old routing rules — the organised library was partially classified before Issue #42 introduced the two-signal system, so agreement with historical placement is not the same as correctness. That remains true. But further investigation revealed the problem is deeper than measurement contamination.

---

## 2. The Director Signal is Sparse

**Finding:** Only 159 total directors across 16 Satellite categories in `SATELLITE_ROUTING_RULES`. In the current manifest (Unsorted work queue, 1,215 films):

| Reason code | Count | % of total |
|---|---|---|
| `explicit_lookup` | 389 | 32% |
| `structural_signal` | 212 | 17.4% |
| `unsorted_no_year` | 173 | 14.2% |
| `unsorted_insufficient_data` | 106 | 8.7% |
| `unsorted_no_match` | 97 | 8.0% |
| `non_film_supplement` | 94 | 7.7% |
| `review_flagged` | 67 | 5.5% |
| `director_signal` | 40 | 3.3% |
| `both_agree` | 23 | 1.9% |
| `user_tag_recovery` | 14 | 1.2% |

Only 40 films (3.3%) routed via `director_signal` and 23 (1.9%) via `both_agree`. The two-signal system's highest-confidence outputs — where director and structure agree — account for fewer than 2% of the work queue.

**Why so few?** The director registry covers movement-specific practitioners (Argento → Giallo, Jean Garret → Brazilian Exploitation). Most directors in the Unsorted queue are either Core (caught by identity gate before signals fire) or have no entry in any Satellite director list. The structural signal carries most of the load — but it's doing so without director confirmation, producing `structural_signal` classifications at 0.65 confidence with 67.4% accuracy.

---

## 3. `director_disambiguates` Is a Coin Flip

The P3 rule in `integrate_signals()` fires when: director matches Category A, structural signal matches Category B (different). Director "wins" and routes to Category A at confidence 0.75.

**Result:** 52.9% accuracy. The director override is wrong more than it is right.

**Why this is architecturally wrong:** P3 treats conflicting signals as an ambiguity to be resolved by director. But two signals pointing to different categories is a *conflict*, not an ambiguity. The correct output for conflicting signals is `review_flagged` — we don't know. Routing to the director's category against structural evidence that points elsewhere produces coin-flip accuracy.

**Contrast with the correct use of director:** When structural matches Category A *and* director also matches Category A (`both_agree`), accuracy is 73.8%. Director as *confirmation* of structural evidence works. Director as *override* of conflicting evidence does not.

---

## 4. The Kubrick Structural Simulation

To understand why structural signal is noisy, a simulation was run: what Satellite categories would Stanley Kubrick's films match on structural signal alone (country + decade + genre), with no director registry entry?

**Result:** Every Kubrick film from 1960–1999 matched 2–4 categories simultaneously:
- *2001: A Space Odyssey* (GB, 1968, Sci-Fi) → Indie Cinema (GB ∈ country_codes, 1960s ∈ decades, Sci-Fi ∈ genres)
- *A Clockwork Orange* (GB, 1971, Sci-Fi/Drama/Thriller) → Indie Cinema, American New Hollywood (if US co-production flagged)
- *The Shining* (GB, 1980, Horror) → Indie Cinema, and any category that takes GB + 1980s + Horror

The structural gates define a *territory* (country + era + broad genre) not a *movement*. `IT + Thriller + 1970s` describes a zone that contains real Giallo AND non-Giallo Italian thrillers. The structural signal cannot distinguish between "this matches the movement's aesthetic" and "this happens to share the coordinates."

**The underlying problem:** Genre tags from TMDb are broad labels applied by community editors, not movement-specific identifiers. `Drama` applies to thousands of films. `Thriller` applies to hundreds. The three-coordinate system is necessary but insufficient.

---

## 5. TIER_ARCHITECTURE.md vs. the Code

`docs/theory/TIER_ARCHITECTURE.md` describes a comprehensive auteur narrative — ~38–43 Core directors across decades, with Satellite categories representing the exploitation margins around that spine. The code implements:

- Core whitelist: ~38–43 directors (exact match) ✓
- SORTING_DATABASE: hundreds of per-film human pins ✓
- Satellite director lists: 159 directors, mostly exploitation movements ✓

**The gap:** TIER_ARCHITECTURE.md describes movements like German New Cinema (Fassbinder's contemporaries, Wenders non-Core work), Italian Art Cinema (non-Giallo Italian drama), Polish cinema, Iranian cinema, Romanian New Wave. None of these have `SATELLITE_ROUTING_RULES` entries. Films by directors adjacent to Core auteurs — the natural Satellite candidates per the theory — have no category to route to. They fall to Indie Cinema (catch-all) or Unsorted.

TIER_ARCHITECTURE.md's theoretical framework is intact. The code only implements the exploitation half of Satellite, not the art-cinema-adjacent half.

---

## 6. The Certainty Tier Framework Exists But Isn't Enforced

`exports/skills/certainty-first.md` and `docs/architecture/RECURSIVE_CURATION_MODEL.md §5` define explicit certainty tiers:

| Tier | Categories | Gates | Auto-classify? |
|---|---|---|---|
| 0 | Corpus-matched | Scholarship corpus (IMDb ID) | Yes, confidence 1.0 |
| 1 | Giallo, Brazilian Exploitation, HK Action, Pinku Eiga, American Exploitation, European Sexploitation, Blaxploitation | country + genre + decade + directors (4) | Yes, 0.7–0.85 |
| 2 | Classic Hollywood, French New Wave, American New Hollywood | director/country + decade + keywords (3) | Yes, 0.6–0.75 |
| 3 | Music Films, Indie Cinema | genre/country + decade (2, negative-space) | Review-flagged only |
| 4 | Japanese Exploitation, Cult Oddities | Manual only | No auto-classification |

`certainty-first.md` Rule 1 states explicitly:
> *"This prevents the failure mode that created the current dysfunction: defining 17 categories before proving the data can populate them."*

The framework was written. It was never enforced in `integrate_signals()`. The function applies identical confidence logic to Giallo (Tier 1) and Indie Cinema (Tier 3). P7 (`structural_signal`, unique category match) routes to manifest regardless of the matched category's certainty tier.

**Consequence:** `both_agree` at 0.85 appears for:
- `To Be Twenty (1978, Fernando Di Leo) → Giallo` ← correct, Tier 1
- `Irma Vep (1996, Olivier Assayas) → Indie Cinema` ← wrong, Tier 3, should be review_flagged
- `Demonlover (2002, Olivier Assayas) → Indie Cinema` ← wrong, Tier 3
- `Vers Mathilde (2005, Claire Denis) → Indie Cinema` ← wrong, Tier 3
- `Nouvelle Vague (2025, Richard Linklater) → Indie Cinema` ← wrong, Tier 3

The confidence score machinery is correct. The category tier constraint is missing.

---

## 7. The Explicit Lookup Baseline Analysis

The confirmed Satellite films (explicit_lookup + both_agree, ≥0.8 confidence) from the organised library were reviewed. 201 films across 16 categories. Key findings:

**Tier 1 categories look healthy** — Brazilian Exploitation, Giallo, HK Action, Pinku Eiga, American Exploitation, European Sexploitation, Blaxploitation have substantial film counts with recognisable movement practitioners. The structural gates for these categories are defensible.

**Indie Cinema is being used as a catch-all for at least three distinct populations:**
1. Genuine international arthouse (Nanni Moretti, Peter Weir, René Laloux, Olivier Assayas)
2. Films that belong in other categories but have no explicit rule (Braindead → horror/exploitation, Akira → animation)
3. Misplacements from the Core-adjacent zone (The Collector with William Wyler, who is in the Core whitelist; The Fearless Vampire Killers with Polanski, who is Core-adjacent)

**Several explicit_lookup placements are wrong:**
- *Orpheus* (1950, Jean Cocteau) → Classic Hollywood — Cocteau is French, not Hollywood
- *A Man and a Woman* (1966, Claude Lelouch) → Indie Cinema — should be French New Wave
- *The Collector* (1965, William Wyler) → Indie Cinema — Wyler is in Core whitelist
- *The Oily Maniac* (1976, Meng-Hua Ho) → American Exploitation — it's a Shaw Brothers HK production
- *Braindead* (1992, Peter Jackson) → Indie Cinema — horror/splatter, closer to exploitation

These errors will propagate if the explicit_lookup list is used as a training corpus without a review pass first.

**Music Films has no structural definition** — single genre gate (Music/Musical/Documentary), no country, no decade, no director list. `The Smashing Machine` (2002) is in there, which is a documentary about MMA fighters. `200 Motels` (1971, Tony Palmer) is a Zappa concert film. `Streets of Fire` (1984, Walter Hill) is a rock musical action film. These three films do not belong in the same category by any coherent definition.

---

## 8. What the Two-Signal System Actually Gets Right

The correct theory-to-code translation exists and is demonstrably working. The Giallo chain is the canonical example:

**Theory** (SATELLITE_CATEGORIES.md): Giallo = IT + 1960s–1980s + Horror/Thriller/Mystery + directors from Koven (2006), Lucas (2007)

**Code** (SATELLITE_ROUTING_RULES['Giallo']): `country_codes: ['IT'], decades: ['1960s','1970s','1980s'], genres: ['Horror','Thriller','Mystery'], directors: [bava, argento, fulci, martino, ...]`

**Corpus** (data/corpora/giallo.csv): 41 films with IMDb IDs, canonical tiers, and per-film scholarship citations

**Film:** `To Be Twenty (1978, Fernando Di Leo, IT) → both_agree, Giallo, 0.85`

Signal 1 fires independently (Fernando Di Leo ∈ director list). Signal 2 fires independently (IT + 1970s + Thriller). They converge on the same category. `both_agree` at 0.85 is the correct output.

The same chain works for Classic Hollywood (John Ford, Howard Hawks both produce `both_agree`), Pinku Eiga (Masumura → `both_agree`), and HK Action (King Hu, Yuen Woo-Ping, John Woo all produce `both_agree`).

**The system works when:** the category has a clear structural definition AND a director list grounded in published scholarship AND the film's API data is complete.

**The system fails when:** the category is negative-space (Indie Cinema), or has a single gate (Music Films), or the structural gates are so broad they fire for films that don't belong (Kubrick → Indie Cinema via GB + 1960s + Sci-Fi).

---

## 9. Conclusions

### C1: The confidence score machinery is correct
`both_agree` (0.85), `structural_signal` (0.65), `review_flagged` (0.4) reflect genuine differences in classification certainty. The scores are not the problem.

### C2: The categories are not aligned with the certainty tier framework
`integrate_signals()` applies the same logic to all categories. Tier 3 categories (Indie Cinema, Music Films) produce `both_agree` at 0.85 — a confidence score that the framework explicitly says requires 4 independent gates, which these categories do not have.

### C3: `director_disambiguates` should be removed
P3 in `integrate_signals()` uses director to override conflicting structural evidence. 52.9% accuracy makes this statistically indistinguishable from a coin flip. When director and structure point to different categories, the correct output is `review_flagged`, not director-routing.

### C4: Three categories should be removed from auto-routing
- **Indie Cinema** (Tier 3, negative-space): films currently auto-routed here should enter the review queue with a suggestion. Indie Cinema remains as a destination reachable only via SORTING_DATABASE pin, corpus match, or review queue acceptance.
- **Music Films** (Tier 4, single gate): same treatment. No auto-routing.
- **Cult Oddities** (Tier 4, no routing rules): already manual-only in practice; formalise this.

### C5: The explicit_lookup baseline needs a review pass before use
201 confirmed films are the best available ground truth. But ~6–8 placements are wrong (Cocteau, Lelouch, Wyler, Polanski adjacents, Shaw Brothers film in American Exploitation). These must be corrected before this list is used to derive structural profiles or build corpora.

### C6: New categories should start at Tier 4 and earn automation
German New Cinema, Italian Art Cinema (non-Giallo), and other art-movement categories identified in TIER_ARCHITECTURE.md should be added as SORTING_DATABASE-only (Tier 4) entries. They earn Tier 2 status (director-only auto-routing) by demonstrating a director list from published scholarship and 10+ confirmed films.

### C7: The clean baseline
After dropping vague categories from auto-routing, the auto-classified population is approximately:
- `explicit_lookup`: ~389 films (SORTING_DATABASE pins)
- `corpus_lookup`: ~50 films (Giallo corpus + future corpora)
- Core identity gate: ~150 films
- Reference canon: ~50 films
- Tier 1 `both_agree`: ~15–20 films (genuine four-gate agreements)
- Tier 1/2 `structural_signal`: ~60–80 films (genuine movement matches)

Everything else — currently ~212 `structural_signal` films and ~23 `both_agree` films in Tier 3 categories — becomes `review_flagged` with a ranked suggestion. The baseline is smaller but honest.

---

## 10. Feeds Into

This investigation directly feeds **Issue #51: Category Certainty Enforcement and Vague Category Removal**. See `docs/issues/ISSUE_051_CATEGORY_CERTAINTY_ENFORCEMENT.md`.

**Deferred to follow-up issues:**
- Explicit_lookup review pass (correct misplacements identified in §7)
- New category development: German New Cinema, Italian Art Cinema (Tier 4 → Tier 2 pathway)
- Reference canon corpus migration (Issue #50, recommended path)
- Structural gate refinement for Tier 1 categories (keyword signals as required, not corroborating)
