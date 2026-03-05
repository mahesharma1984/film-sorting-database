# Two-Signal Classification Architecture

**Status:** Canonical (Issue #42 implemented, Issue #44 implemented)
**Implementation:** `lib/signals.py`
**Date established:** 2026-03-05

---

## 1. Overview

Every automated classification in this system is produced by two independent signals:

1. **Director Identity** — relational knowledge: "who made this?"
2. **Structural Triangulation** — coordinate knowledge: "where/when/what?"

Both signals run for every film. Neither short-circuits the other. The pattern of
agreement or disagreement between them determines classification confidence.

This model replaces the sequential gate chain (pre-Issue #42) where decade blocked
director and structure was a fallback. The old framing ("first match wins") is
deprecated. The correct framing: **both signals fire independently; their integration
determines the result.**

---

## 2. Signal Definitions

### Signal 1: Director Identity

Maps a director to one or more tradition associations based on body of work,
technique lineage, and documented historical membership.

**Properties:**
- Persists across the director's career (a 1998 Ferrara is still "from" American
  Exploitation even though the film's structural coordinates don't match)
- Not binary — directors have varying strengths of association
  (Category Core / Category Reference / Texture per SATELLITE_DEPTH.md §3)
- Can span categories (Jack Hill = Blaxploitation + AmExploitation)
- High precision, coverage-dependent recall — near-zero false positives when
  lists are correct, but gaps in director rosters cause silent misses

**Implementation:** `score_director()` in `lib/signals.py`
- Checks `DIRECTOR_REGISTRY` (all Satellite category directors) + `CoreDirectorDatabase`
- Returns all `DirectorMatch` objects (no early exit, no caps)
- For tradition categories (`is_tradition=True`): decade_valid is always True
  (director identity persists across eras)
- For movement categories (`is_tradition=False`): decade_valid only if
  film decade falls within the movement's active period

**Data source:** `SATELLITE_ROUTING_RULES[category]['directors']` in `lib/constants.py`

### Signal 2: Structural Triangulation

Country + decade + genre locate a film in a coordinate space. Some regions are
owned by a single tradition (IT+1970s+Horror = Giallo). Some overlap
(US+1970s+Crime = Blaxploitation OR AmExploitation OR AmNH).

**Properties:**
- High precision in distinctive regions (IT+1970s → Giallo at 88%,
  US+1940s → Classic Hollywood at 90%, BR+1970s → Brazilian Exploitation at 100%)
- Ambiguous in overlapping regions (US+1970s has 3-way overlap, FR+1960s 2-way)
- Blind to out-of-era films — structure says nothing about a 2014 Godard film

**Implementation:** `score_structure()` in `lib/signals.py`
- Checks: Reference canon, COUNTRY_TO_WAVE, SATELLITE_ROUTING_RULES
  (country+genre+keywords), Popcorn thresholds
- Returns all `StructuralMatch` objects (no early exit)

**Data source:** `SATELLITE_ROUTING_RULES[category]` country_codes, decades, genres,
keyword_signals in `lib/constants.py`

---

## 3. Integration

`integrate_signals()` combines both signal sets using a 10-level priority table:

| Priority | Director says | Structure says | Reason code | Confidence |
|---|---|---|---|---|
| P1 | — | Reference canon | `reference_canon` | 1.0 |
| P2 | Satellite A | Satellite A (same) | `both_agree` | 0.85 |
| P3 | Satellite A | Satellite B (different) | `director_disambiguates` | 0.75 |
| P4 | Satellite A | nothing | `director_signal` | 0.65 |
| P5 | Core | Satellite B | `structural_signal` | 0.65 |
| P6 | Core only | nothing | `director_signal` (Core) | 1.0 |
| P7 | nothing | Satellite B (unique) | `structural_signal` | 0.65 |
| P8 | nothing | Satellite B (ambiguous) | `review_flagged` | 0.4 |
| P9 | nothing | Popcorn | `structural_signal` | 0.65 |
| P10 | nothing | nothing | `unsorted_no_match` | — |

**Key design principles:**
- **Disagreement is information.** Director says A, structure says B → director
  disambiguates (the director is the expert on which tradition their film belongs to)
- **Confidence is evidence-dependent, not category-dependent.** A Giallo match with
  both signals = 0.85; with structure only = 0.65. Same category, different confidence.
- **Structural specificity takes priority over director prestige.** When a Core
  director's film matches a Satellite movement (P5), movement specificity wins —
  because movement membership gates more narrowly than auteur status. Core routing
  exists as identity-only fallback (P6). Resolution for specific films: SORTING_DATABASE
  pins (Issue #25).

---

## 4. The Literature Review Bridge

The two signals are connected by published scholarship:

```
Structural Signal (country + decade + genre)
    → identifies which scholarly field to consult
        → published monographs contain director rosters
            → rosters populate the Director Identity signal
```

Each structural region maps to one or two authoritative sources:

| Structural Region | Key Source | Directors Available |
|---|---|---|
| IT+1960s-80s (Giallo) | Koven 2006 *La Dolce Morte* | ~25 directors |
| US+1970s (Blaxploitation) | Guerrero 1993 + Lawrence 2008 | ~15-20 |
| US+1960s-80s (AmExploit) | Vale/Juno 1986 *Incredibly Strange Films* | ~13 |
| US+1930s-50s (Classic HW) | Sarris 1968 *The American Cinema* | ~200 classified |
| BR+1960s-90s (Pornochanchada) | Dennison/Shaw 2007 + Abreu 2015 | ~12-15 |
| HK+1970s-90s (HK Action) | Teo 1997 *HK Cinema: Extra Dimensions* | ~18+ |
| JP+1960s-80s (Pinku Eiga) | Sharp 2008 *Behind the Pink Curtain* | ~20+ |
| FR/IT/DE+1960s-80s (EuroSex) | Mathijs/Mendik 2004 *Alternative Europe* | ~14-18 |
| JP+1970s-80s (JExploit) | Desjardins 2005/2013 *Gun and Sword* | ~14+ |
| HK+1980s-90s (Cat III) | No monograph (censorship category) | Manual only |
| FR+1950s-70s (FNW) | Neupert 2007 + Marie 2003 | ~15-20 |
| US+1967-80 (AmNH) | Biskind 1998 *Easy Riders, Raging Bulls* | ~15-20 |

This means director list expansion (Issue #44) is a **literature review task**:
consult the authoritative source for each structural region, extract the director
roster, apply the SATELLITE_DEPTH §3 quality gates (body of work, formal
distinctiveness, scholarship citation), and add verified entries to
`SATELLITE_ROUTING_RULES`.

**Methodology:** See `docs/SATELLITE_CATEGORIES.md` for per-category scholarly
anchoring. See `SATELLITE_DEPTH.md §3` for director inclusion criteria.

---

## 5. Signal Populations

Classification sources form a trust hierarchy. Two-signal routing applies only to
Population C (heuristic pipeline):

| Population | Source | Trust | Two-Signal? |
|---|---|---|---|
| A | `explicit_lookup` (SORTING_DATABASE.md) | 1.0 | No — human override |
| B | `corpus_lookup` (data/corpora/*.csv) | 1.0 | No — scholarship ground truth |
| C | Pipeline (signals.py) | 0.4–0.85 | **Yes** — this is where integration happens |

Population C films are classified by `integrate_signals()`. Their confidence depends
on which signals fired and whether they agreed. The target: expand director rosters
until `both_agree` is the dominant reason code for tradition categories, reducing
reliance on `structural_signal` (one-signal routing) and `review_flagged` (no
director to disambiguate).

**Current signal ratio (2026-03-05):** Director-led 9.4%, Structural-only 27%.
Target: Director-led 19%+, with `both_agree` as the largest director-led code.

---

## 6. Relationship to Existing Architecture

### Pre-signals layers (unchanged)
- **SORTING_DATABASE** (Stage 2) — human override, fires before any signal
- **Corpus lookup** (Stage 2.5) — scholarship ground truth, fires before signals
- These are NOT part of two-signal routing. They are trust-1.0 overrides.

### Two-signal layer (Issue #42, replaces Stages 3-8)
- `score_director()` + `score_structure()` → `integrate_signals()`
- Replaces: reference_canon check, country_satellite, tmdb_satellite,
  user_tag_recovery, core_director, popcorn — all now unified under
  `integrate_signals()` priority table

### Deprecated terminology
- "Sequential gate chain" → "independent signals with integration"
- "First match wins" → "both signals fire; agreement determines confidence"
- "Decade blocks director" → "decade bounds are structural signal; director
  identity persists across eras for tradition categories"
- Stage numbers 3-8 as independent stages → unified signal layer

---

## 7. Theory Grounding

| Concept | Theory Document | Signal Connection |
|---|---|---|
| Directors as primary units | COLLECTION_THESIS.md §7 | Director Identity signal |
| Decades as structural, not arbitrary | COLLECTION_THESIS.md §12, MARGINS_AND_TEXTURE.md §2 | Structural Triangulation signal |
| Domain Grounding requirement | CLAUDE.md Rule 4 | Literature review methodology |
| Category Core/Reference/Texture | SATELLITE_DEPTH.md §3 | Director quality gates |
| Certainty tiers | CLAUDE.md Rule 11 | Signal agreement → confidence |
| Within-category depth | SATELLITE_DEPTH.md §3 | Recursive two-signal application |
| Category emergence | REFINEMENT_AND_EMERGENCE.md §2 | Both signals required for coherent categories |

---

## 8. Files Reference

| File | Role |
|---|---|
| `lib/signals.py` | Implementation — score_director, score_structure, integrate_signals |
| `lib/constants.py` | Data — SATELLITE_ROUTING_RULES, DIRECTOR_REGISTRY |
| `lib/satellite.py` | Component — classify_structural() used by score_structure() |
| `lib/core_directors.py` | Component — CoreDirectorDatabase used by score_director() |
| `classify.py` | Orchestrator — calls signals layer after lookup/corpus |
| `scripts/reaudit.py` | Measurement — accuracy by reason code |
| `output/accuracy_baseline.json` | Metrics — per-stage accuracy snapshot |
| `docs/SATELLITE_CATEGORIES.md` | Specification — per-category signal definitions |
| `docs/theory/SATELLITE_DEPTH.md` | Theory — director inclusion criteria (§3) |
