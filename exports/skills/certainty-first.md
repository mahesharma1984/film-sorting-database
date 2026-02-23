# Skill: Certainty-First Classification (Anchor-Then-Expand Routing)

**Purpose:** Classify what you can prove first, use proven classifications as anchors, then expand outward with decreasing certainty but increasing gates.
**Addresses:** Categories expanding faster than data can populate them, false confidence from weak routing rules, binary classification when graduated certainty is needed.

---

## Core Principle

**A classification system should grow outward from certainty, not inward from aspiration. Define categories by what you can prove, not what you hope to catch.**

Without certainty-first:
- Categories are defined for historical movements that the collection may or may not contain
- Routing rules are written for data fields the API may or may not return
- All categories are treated as equally reliable, when some have 4 independent corroborating signals and others have 1
- Catch-all categories (Indie Cinema, Music Films) absorb films that failed other checks, creating populations defined by exclusion rather than inclusion
- The system produces confident-looking classifications from weak evidence, and uncertain-looking "Unsorted" results from strong evidence that simply doesn't match a rule

---

## The Certainty Hierarchy

Not all classification methods have equal reliability. The system already implicitly encodes a trust hierarchy (explicit lookup > reference canon > satellite routing > popcorn check). Certainty-first makes this explicit and extends it to within-tier variation.

### Level 1: Explicit (Confidence 1.0)

Human-curated mappings. No heuristic involved.

- **SORTING_DATABASE.md** — hundreds of `Title (Year) → Destination` entries
- **REFERENCE_CANON** — 50-film hardcoded list
- **Core Director Whitelist** — director name → Core tier

These are the system's anchors. Every other classification is measured against the reliability of these.

### Level 2: High-Certainty Heuristic (Confidence 0.7–0.8)

Categories with 4+ independent, orthogonal gates. A false positive requires simultaneous failure of country detection, genre classification, decade extraction, AND director matching — each from independent data sources.

**Categories at this level:** Giallo, Brazilian Exploitation, Hong Kong Action, Pinku Eiga, American Exploitation, European Sexploitation, Blaxploitation.

**Why these are high-certainty:** Each requires:
1. Country code match (from OMDb/TMDb, independent of filename)
2. Genre match (from TMDb structured data)
3. Decade within historically valid bounds
4. Director list or keyword signals as additional corroboration

A film matching all four is overwhelmingly likely to belong. The signals are orthogonal — knowing the country doesn't predict the genre, knowing the decade doesn't predict the director. Each gate independently filters the population.

### Level 3: Moderate-Certainty Heuristic (Confidence 0.6–0.7)

Categories with 3 independent gates. Reliable but narrower — typically director-driven categories where the routing depends heavily on recognizing specific names.

**Categories at this level:** Classic Hollywood, French New Wave, American New Hollywood.

**Why moderate:** These categories route primarily on director lists + decade + keywords. Country is either implicit (US for Classic Hollywood) or intentionally excluded (FR excluded from French New Wave to prevent false positives). The director list is the critical signal — if it's incomplete, films by unlisted directors of the movement won't route.

### Level 4: Low-Certainty Heuristic (Confidence 0.4–0.5)

Categories with 2 or fewer independent gates, or negative-space definitions (defined by what they're NOT rather than what they ARE).

**Categories at this level:** Music Films, Indie Cinema.

**Why low-certainty:**
- **Music Films:** Single gate (genre = Music/Musical/Documentary). No country, no decade, no director restriction. A music documentary by a Core director can land here.
- **Indie Cinema:** Defined by exclusion — not exploitation, not Core, not Popcorn, not a named movement. 30-country list, 6-decade range, 4-genre filter. The broadest possible net. No keyword signals (by design — "indie" and "art house" are too ambiguous).

Films classified at this level should be flagged for human review, not auto-routed to the library.

### Level 5: Manual Only (Confidence 0.3)

Categories that cannot be reliably automated with available data. Either the collection is too sparse or the distinguishing signals are too subtle for heuristic routing.

**Categories at this level:** Japanese Exploitation (0 auto-routed films; single-director list), Cult Oddities (no routing rules at all).

Films in these categories should only arrive via explicit SORTING_DATABASE.md entries.

---

## The Anchor-Then-Expand Pattern

Certainty-first classification works in three steps, each building on the previous:

### Step 1: Establish Anchors

Anchors are classifications with confidence 1.0 — they are correct by definition because a human curated them or they match an explicit list.

**Anchor sources:**
- Every entry in SORTING_DATABASE.md (human-curated)
- Every film in REFERENCE_CANON (expert-curated)
- SATELLITE_TENTPOLES entries per category (category-defining films)

Anchors serve two purposes:
1. **Direct classification** — the film is classified, done
2. **Category definition** — the anchor population defines what "Giallo" or "French New Wave" concretely looks like in this collection

### Step 2: High-Certainty Routing

Tier 1 and Tier 2 categories with 3-4 orthogonal gates auto-classify films. These newly classified films expand the anchor population for each category.

At this point, each well-defined category has:
- Tentpole films (from SATELLITE_TENTPOLES)
- Director anchors (from SATELLITE_ROUTING_RULES director lists)
- Structurally-routed films (from country+genre+decade gates)

This population is the category's "known good" set.

### Step 3: Fuzzy Expansion (Gated)

For films that don't match any rule but have partial data (R2 readiness), the system can compare against established anchors:

**The comparison:** "Does this film's available metadata place it near any category's known-good population?"

Signals that can contribute:
- Decade overlap with a category's active decades
- Partial country match (e.g., language tag suggests Italian origin)
- Director name fragment matching a category's director list
- TMDb keyword overlap with a category's keyword signals
- Thematic proximity (text signals in overview matching category text terms)

**The gate:** Fuzzy expansion requires:
1. At least one structural signal (decade, country, or director) must be present — pure text/keyword match is insufficient
2. The suggested category must be Tier 1 or Tier 2 (high-certainty categories only — you cannot fuzzy-expand into Indie Cinema)
3. The result is a SUGGESTION, not a classification — it goes to the review queue, not the manifest

**Why gated:** Without gates, fuzzy matching degrades rapidly. A 1970s film with vaguely horror-adjacent keywords could match Giallo, Pinku Eiga, Brazilian Exploitation, and American Exploitation simultaneously. The gates ensure: one structural signal narrows the field, the category must be well-defined enough to validate against, and a human confirms.

---

## Category Certainty Tier Assignment

Each category in SATELLITE_ROUTING_RULES should have an explicit `certainty_tier` field. The tier is determined by counting independent gates:

### Counting Independent Gates

A gate is a routing signal that filters the population independently:

| Gate | Source | Independence |
|------|--------|-------------|
| Country code | OMDb/TMDb API → ISO code | Independent of genre, decade, director |
| Genre | TMDb structured genres | Independent of country, decade, director |
| Decade | Parsed from filename year | Independent of country, genre, director |
| Director list | Whitelist match against API/filename director | Independent of country, genre, decade |
| Keyword signals | TMDb tags, text terms | Corroborating (not independent — keywords correlate with genre) |

**Counting rule:** Count country, genre, decade, and director as independent gates. Keywords are corroborating — they strengthen a match but don't count as a separate gate.

| Gates Present | Certainty Tier | Auto-classify? |
|--------------|---------------|---------------|
| 4 (country + genre + decade + director) | Tier 1 | Yes |
| 3 (any three of the four) | Tier 2 | Yes |
| 2 (any two) | Tier 3 | Review-flagged |
| 1 or 0 | Tier 4 | Manual only |

### Negative-Space Penalty

Categories defined by exclusion (what they're NOT) rather than inclusion (what they ARE) receive a one-tier penalty:

- Indie Cinema has country + genre + decade (3 gates → would be Tier 2), but its definition is negative-space: "non-exploitation, non-Core, non-Popcorn films from 30 countries." Penalized to Tier 3.
- Popcorn has popularity + format + genre (3 signals), but it's the "everything else that's mainstream" catch-all. Penalized appropriately.

**Why the penalty:** Negative-space categories have higher false-positive rates because they don't match films TO something specific — they catch films that failed to match anything else. A film misclassified by an upstream stage silently falls into the negative-space category.

---

## Design Rules

### Rule 1: Categories Must Earn Automation

A new Satellite category starts at Tier 4 (manual only). It earns higher tiers by demonstrating:
- **Tier 3:** At least 2 independent gate signals implemented and tested
- **Tier 2:** At least 3 independent gate signals, with ≥10 films successfully auto-classified
- **Tier 1:** All 4 gate signals, with ≥20 films successfully auto-classified and tentpoles established

This prevents the failure mode that created the current dysfunction: defining 17 categories before proving the data can populate them.

### Rule 2: Certainty Tier Is Structural, Not Adjustable

A category's certainty tier is determined by its gate count, not by how well it's performing. If Giallo (Tier 1) has a bad month and misclassifies 3 films, it's still Tier 1 — the fix is to improve the gates, not to downgrade the tier. Conversely, if Indie Cinema starts performing well on a particular decade, it's still Tier 3 — the structural weakness (negative-space definition) hasn't changed.

### Rule 3: Fuzzy Expansion Never Overrides Rules

If a film matches a routing rule (even a low-certainty one), the rule takes precedence over fuzzy anchor matching. Fuzzy expansion only applies to films that matched NO rule. This prevents: a film classified as Indie Cinema (Tier 3, confidence 0.5) being "fuzzy-upgraded" to Giallo because it happens to be Italian.

### Rule 4: Anchors Are Immutable Within a Run

During a single classification run, the anchor population is fixed (SORTING_DATABASE + REFERENCE_CANON + SATELLITE_TENTPOLES). Newly classified films do not become anchors within the same run. This prevents cascading errors where one bad classification influences subsequent fuzzy matches.

Between runs, anchors grow: accept/override decisions from the curation loop add entries to SORTING_DATABASE and SATELLITE_TENTPOLES.

---

## The Inverse Gate Rule

As certainty decreases, gates should get stricter — not looser. This is counterintuitive but prevents the most common failure mode.

```
Tier 1 (high certainty):  Match one rule → auto-classify
Tier 2 (moderate):        Match one rule → auto-classify (lower confidence)
Tier 3 (low certainty):   Match one rule → flag for review (human must confirm)
Tier 4 (manual):          No rule fires → SORTING_DATABASE entry required
Fuzzy expansion:          No rule fires → structural signal + anchor proximity → SUGGEST only
```

**Why inverse:** A Tier 1 category has enough orthogonal gates that a match is overwhelmingly correct. A Tier 3 category has so few gates that a match could easily be a false positive. Requiring human confirmation for Tier 3 matches prevents the catch-all categories from silently absorbing misclassified films.

---

## Integration with Other Skills

| Skill | How Certainty-First Connects |
|---|---|
| **Data Readiness** | Data readiness determines which certainty tier a classification can achieve. An R1 film cannot reach Tier 1 certainty even in a Tier 1 category — the data isn't there. |
| **Domain Grounding** | Certainty tiers respect grounding: categories grounded in published film-historical scholarship (specific movements, named directors) tend to be Tier 1-2. Categories defined by collection contents tend to be Tier 3-4. |
| **Pattern-First** | The 4-tier priority hierarchy (Reference → Satellite → Core → Popcorn) is the pattern. Certainty-first adds a second dimension: within each tier, categories have different certainty levels. |
| **Failure Gates** | Certainty tiers determine gate severity. Tier 1 misclassification is a soft gate (rare, low impact). Tier 3 misclassification is expected (high volume, requires review). |
| **Curation Loop** | Certainty-first creates the populations that feed the curation loop: Tier 1-2 auto-classified films are accepted; Tier 3 flagged films enter the review queue; Tier 4 manual films bypass the pipeline entirely. |
| **Measurement-Driven** | Measure accuracy per certainty tier, not globally. A 95% accuracy rate that's 99% on Tier 1 and 60% on Tier 3 reveals the real issue — aggregate accuracy hides tier-specific weakness. |

---

## Checklist

When adding a new Satellite category:
- [ ] Counted independent gate signals (country, genre, decade, director)
- [ ] Assigned certainty tier based on gate count
- [ ] If Tier 3 or 4: documented why automation is limited
- [ ] If negative-space definition: applied one-tier penalty
- [ ] Added `certainty_tier` field to SATELLITE_ROUTING_RULES entry
- [ ] Set confidence values appropriate to tier
- [ ] If Tier 4: ensured no auto-classification path exists (manual only via SORTING_DATABASE)

When evaluating classification quality:
- [ ] Segmented accuracy by certainty tier (not global average)
- [ ] Checked Tier 3 classifications against review queue (are they being reviewed?)
- [ ] Verified Tier 1-2 false positive rate is low (if not: gate signal is unreliable, investigate)
- [ ] Verified fuzzy expansion suggestions are going to review queue, not manifest
