# Issue #40: Two-Signal Satellite Routing

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P2-High |
| Date Opened | 2026-03-03 |
| Component | Satellite |
| Change Type | Feature / Refactor |
| Estimated Effort | 2-3 days (3 phases, can be implemented incrementally) |
| Blocked By | None |
| Blocks | None |
| Supersedes | Subsumes the routing-order fix from INVESTIGATION_DIRECTOR_FIRST_ROUTING.md §8/§10 |

---

## 1. Manager Summary

**Problem:** Satellite classification has two useful signals — director identity and structural coordinates (country+decade+genre) — but they're entangled in a sequential gate chain where the decade gate blocks the director check. 76% of the organized Satellite library (386/506 films) is unreachable by either signal and depends entirely on manual SORTING_DATABASE entries. Indie Cinema absorbs 52% of all auto-classified Satellite films because it functions as a catch-all, not a category.

**Impact if unfixed:** Satellite auto-classification remains at ~10% coverage. Every new film that enters the queue requires manual triage. Tradition categories (Giallo, Blaxploitation, Brazilian Exploitation) receive near-zero auto-classifications. The system cannot scale.

**Risk if fixed wrong:** Existing correctly-routed films regress — particularly movement categories (FNW, AmNH, JNW) where the current director-only routing already works. Expanded director lists could create false positives if directors span multiple categories without proper handling. Indie Cinema count may drop but films shouldn't disappear — they should reclassify, not become unsorted.

**Estimated effort:** ~2-3 days across 3 phases. Phase 1 (director list expansion, data-only) is lowest risk. Phase 2 (gate reordering) is ~10 lines of code. Phase 3 (integration function) is the most complex but can be deferred.

---

## 2. Evidence

### Observation

The evidence trail system already runs both signals independently for every film × every category. Analysis reveals:

- **Zero agreement** between director and structural signals across all categories (`both_pass = 0`). The two signals never confirm each other because director lists are too sparse.
- **Structural signal is noisy in overlapping regions.** US+1970s matches 3 categories simultaneously (AmExploit, Blaxploitation, AmNH). FR+1960s matches 2 (FNW, EuroSex). 12 films in the queue have ambiguous structural matches.
- **Director signal barely fires.** Only 10 director gate passes across 403 films in the queue. All in movement categories (FNW, AmNH) which already use `country_codes=[]`.
- **76% of organized Satellite library is unreachable** by either signal with current rules.

### Data

Signal reachability per category (organized library, current rules):

| Category | Library | Dir only | Struct only | Both | Neither |
|---|---|---|---|---|---|
| Indie Cinema | 155 | 0 | 38 | 1 | 116 |
| Music Films | 57 | 0 | 0 | 0 | 57 |
| Classic Hollywood | 49 | 0 | 26 | 0 | 23 |
| Brazilian Exploitation | 40 | 0 | 4 | 0 | 36 |
| American Exploitation | 36 | 4 | 8 | 0 | 24 |
| Giallo | 24 | 0 | 5 | 2 | 17 |
| Blaxploitation | 9 | 0 | 0 | 0 | 9 |

Queue classification (n=403):
- `unsorted_no_match`: 65 films with full data but no rule match
- `tmdb_satellite` → Indie Cinema: 26/50 (52%)
- `tmdb_satellite` → Tradition categories (Giallo, Pinku, BrExploit, Blaxploitation): 2/50 (4%)

Structural overlap analysis (evidence_trails.csv):
- AmExploitation + Blaxploitation: 5 films ambiguous
- EuroSex + Indie Cinema: 6 films ambiguous
- EuroSex + Giallo: 1 film ambiguous

Key misclassifications surfaced by investigation:
- Le Samourai (Melville) → Giallo (structural false positive: FR co-production counted as IT)
- Adieu au langage (Godard, 2014) → Indie Cinema (should flag as FNW director, out-of-era)
- New Rose Hotel (Ferrara, 1998) → Unsorted (decade gate blocks AmExploit director match)
- A Summer's Tale (Rohmer, 1996) → Indie Cinema (should flag as FNW director, out-of-era)

---

## 3. Root Cause Analysis

### RC-1: Director lists are too sparse to function as a routing signal

**Location:** `lib/constants.py` → `SATELLITE_ROUTING_RULES` → `directors` lists
**Mechanism:** Tradition categories have 0-6 directors listed vs. 10-20 needed per scholarship. Brazilian Exploitation has 0 directors. Blaxploitation has 4. Even if the routing logic checked directors first, the sparse lists would miss most canonical directors' films. This is a data problem, not a code problem.

### RC-2: Decade gate fires before director check for tradition categories

**Location:** `lib/satellite.py` → `classify()` → lines 117-118
**Mechanism:** `if rules['decades'] is not None and decade not in rules['decades']: continue` — skips the entire category, including the director check at line 121. A 1998 Abel Ferrara film never reaches the American Exploitation director list because the decade gate (1960s-1980s) rejects first. Director lists function as tiebreakers within the decade window, not as primary routing signals.

### RC-3: No integration logic — first match wins

**Location:** `lib/satellite.py` → `classify()` → line 125 (`return`) and line 153 (`return`)
**Mechanism:** Both director match and country+genre match immediately return the first matching category. There is no mechanism to: (a) collect evidence from both signals across all categories, (b) compare them, (c) produce a confidence score reflecting evidence quality. `evidence_classify()` (line 188+) computes this evidence but it's diagnostic-only — it doesn't feed back into routing decisions.

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| Constants → Satellite | `lib/constants.py` SATELLITE_ROUTING_RULES | `lib/satellite.py` classify() | Yes — expanded director lists |
| Satellite → classify.py | `lib/satellite.py` classify() return value | `classify.py` _route_film() | Yes — may return confidence metadata |
| Satellite → evidence trails | `lib/satellite.py` evidence_classify() | `classify.py` _gather_evidence() | No change (read-only) |
| classify.py → manifest | `classify.py` process_directory() | `output/sorting_manifest.csv` | Possible — new reason codes |
| manifest → move.py | `output/sorting_manifest.csv` | `move.py` | No change (reads destination + confidence) |
| manifest → reaudit | `output/sorting_manifest.csv` | `scripts/reaudit.py` | No change |

**Gate impact:** Satellite decade bounds are NOT changed. Country codes are NOT changed. The change is to routing PRIORITY (director before decade for tradition categories) and director list COMPLETENESS. Reaudit baseline will shift because films that were `unsorted_no_match` will now classify.

**Downstream consumers of changed output:**
- `move.py` reads `destination` and `confidence` from manifest — no format change, but new films will appear as classified
- `scripts/reaudit.py` compares manifest classification to filesystem placement — new classifications may surface as discrepancies if the organized library has films in different locations
- `output/evidence_trails.csv` — more director gates will show `pass` instead of `fail`, changing the evidence landscape

---

## 5. Proposed Fix

### Fix Description

Three-phase implementation that can be done incrementally. Each phase is independently valuable and testable. Phase 1 is data-only (zero code risk). Phase 2 is ~10 lines. Phase 3 is the architectural change.

### Phase 1: Expand director lists (data-only, no code change)

**Rationale:** RC-1 is the binding constraint. Even with perfect routing logic, sparse lists mean most films fall through. Expand lists first so Phase 2 has something to work with.

**Priority:** Group A directors (disambiguators in ambiguous zones) first, then Group B (confirmers), then Group C (rescuers).

#### Step 1.1: Add Group A directors to `lib/constants.py`

- **What to change:** `SATELLITE_ROUTING_RULES` → `directors` lists for tradition categories
- **Directors to add (sourced from Wikipedia, per INVESTIGATION_DIRECTOR_FIRST_ROUTING.md §9):**

  **Blaxploitation** (4 → ~10): `melvin van peebles`, `gordon parks jr.`, `michael schultz`, `bill gunn`, `barry shear`, `arthur marks`

  **American Exploitation** (5 → ~10): `roger corman`, `andy milligan`, `david friedman`, `michael findlay`, `doris wishman`

  **Giallo** (6 → ~13): `massimo dallamano`, `ruggero deodato`, `paolo cavara`, `armando crispino`, `fernando di leo`, `lamberto bava`, `enzo castellari`

  **Classic Hollywood** (0 → ~9): `john ford`, `howard hawks`, `orson welles`, `frank capra`, `michael curtiz`, `george cukor`, `fred zinnemann`, `elia kazan`, `john huston`

  **Brazilian Exploitation** (0 → ~8): `carlos reichenbach`, `victor di mello`, `ody fraga`, `roberto mauro`, `fauzi mansur`, `claudio cunha`, `jose miziara`, `jean garret`

  **Pinku Eiga** (4 → ~6): verify `noboru tanaka` not already matched by 'tanaka'; add `hisayasu sato` if not matched by 'hisayasu'

  **Hong Kong Action** (4 → ~11): `king hu`, `chang cheh`, `sammo hung`, `yuen woo-ping`, `jackie chan`, `ching siu-tung`, `corey yuen`

  **European Sexploitation** (6 → ~8): `joe d'amato`, `jess franco` (note: Franco is Spanish — ES; verify country_codes or use director-only match)

- **Verify:** `pytest tests/test_satellite.py -v` — existing tests must still pass. New directors should not conflict with Core whitelist (check `CORE_DIRECTORS` in constants.py for overlap).

#### Step 1.2: Remove larry clark dual-listing regression risk

- **What to change:** Consider removing `larry clark` from American Exploitation `directors` list. His 1970s-1980s films route via country+genre correctly. His 1990s films should route to Indie Cinema. Under director-first routing (Phase 2), keeping him in AmExploit would pull 1990s films into AmExploit incorrectly.
- **Alternative:** Keep him listed, handle via confidence modifier in Phase 3 (decade match = 0.8, decade mismatch = 0.6 + review flag).
- **Verify:** Check Clark's films in cache: `grep -i "larry clark" output/tmdb_cache.json`

#### Step 1.3: Add SORTING_DATABASE pins for known misclassifications

- **What to change:** `docs/SORTING_DATABASE.md` — add entries for films surfaced by the investigation:
  - Ferrara's The Blackout (1997) → AmExploitation (if confirmed by curator)
  - Ferrara's Pasolini (2014) → review (documentary about Pasolini, may not be AmExploit)
- **Verify:** `python classify.py <source>` — check these films route correctly

### Phase 2: Reorder gate — director before decade for tradition categories

**Rationale:** RC-2. Tradition categories (those with `country_codes != []`) should check director BEFORE decade. Movement categories (FNW, AmNH, JNW with `country_codes == []`) keep current order — their decade gate is intentional.

#### Step 2.1: Modify `lib/satellite.py` classify() — reorder gates

- **What to change:** `classify()` method, lines 113-125. For tradition categories (`rules['country_codes']` is not None and not empty), check director BEFORE the decade gate. Director match returns immediately (as now). If no director match, THEN check decade gate → country+genre fallback.
- **Discriminant:** `rules['country_codes'] not in (None, [])` → tradition category (director first). `rules['country_codes'] in (None, [])` → movement category (keep current order).
- **Code sketch:**

```python
for category_name, rules in SATELLITE_ROUTING_RULES.items():
    is_tradition = rules['country_codes'] not in (None, [])

    # For tradition categories: director check FIRST (regardless of decade)
    if is_tradition and rules['directors'] and director:
        director_tokens = set(director_lower.split())
        if any(self._director_matches(director_lower, director_tokens, d)
               for d in rules['directors']):
            return self._check_cap(category_name)

    # Decade gate (applies to both tradition and movement categories)
    if rules['decades'] is not None and decade not in rules['decades']:
        continue

    # For movement categories: director check after decade gate (existing behavior)
    if not is_tradition and rules['directors'] and director:
        director_tokens = set(director_lower.split())
        if any(self._director_matches(director_lower, director_tokens, d)
               for d in rules['directors']):
            return self._check_cap(category_name)

    # Country+genre fallback (unchanged)
    ...
```

- **Verify:** `pytest tests/test_satellite.py -v` — all pass. Then:
  - `python classify.py <source>` — New Rose Hotel (Ferrara, 1998) should route to AmExploit
  - Grep manifest for known director films — verify movement categories unchanged

#### Step 2.2: Update `evidence_classify()` to match new gate order

- **What to change:** `evidence_classify()` should mirror the new logic. For tradition categories, record director gate BEFORE decade gate skip. Currently, decade gate `fail` + `continue` on line 250 skips the director gate entirely for tradition categories — this needs to change so the evidence trail shows what the director signal would have said.
- **Verify:** `pytest tests/test_evidence_trails.py -v`

### Phase 3: Integration function (deferred — can be follow-up issue)

**Rationale:** RC-3. Replace first-match-wins with evidence-based ranking. This is the architectural change that makes confidence evidence-dependent.

#### Step 3.1: New function `_integrate_signals()` in `lib/satellite.py`

- **What to change:** Add method that takes `SatelliteEvidence` from `evidence_classify()` and returns a ranked list of (category, confidence, explanation) tuples.
- **Integration rules:**

| Director | Structure | Confidence | Explanation |
|---|---|---|---|
| pass | pass (same category) | 0.85 | "Director + structural confirmation" |
| pass | pass (different category) | 0.75 | "Director {A} overrides structural {B}" |
| pass | fail/untestable | 0.6 | "Director match, outside structural window" |
| fail | pass (unique region) | 0.65 | "Structural match, no director confirmation" |
| fail | pass (ambiguous region) | 0.4 | "Ambiguous structural match, review" |
| fail | fail | — | No match |

- **Verify:** Unit tests with known films (Ferrara 1998, Godard 2014, A Touch of Zen)

#### Step 3.2: Wire integration function into `classify.py`

- **What to change:** `_route_film()` in `classify.py` — after heuristic stages, use `_integrate_signals()` instead of raw `classify()` return. The integration function becomes the Satellite routing stage.
- **New reason codes:** `satellite_director` (director signal primary), `satellite_structural` (structure primary), `satellite_integrated` (both signals combined)
- **Verify:** Full pipeline run + reaudit

### Files to Modify

| File | Change Type | What Changes | Phase |
|---|---|---|---|
| `lib/constants.py` | Modify | Expand `directors` lists in SATELLITE_ROUTING_RULES (~60 directors added) | 1 |
| `docs/SORTING_DATABASE.md` | Modify | Add 2-5 pins for misclassified films | 1 |
| `lib/satellite.py` | Modify | `classify()` gate reorder (~10 lines); `evidence_classify()` mirror | 2 |
| `lib/satellite.py` | Add | `_integrate_signals()` method | 3 |
| `classify.py` | Modify | Wire integration into `_route_film()` | 3 |
| `tests/test_satellite.py` | Add | Tests for director-first routing, integration function | 2, 3 |
| `docs/issues/INVESTIGATION_TWO_SIGNAL_ARCHITECTURE.md` | Reference | Investigation findings (already written) |  |
| `docs/issues/INVESTIGATION_DIRECTOR_FIRST_ROUTING.md` | Reference | Precursor findings | |

---

## 6. Scope Boundaries

**In scope:**
- Expanding tradition category director lists with Wikipedia-sourced names (Phase 1)
- Reordering director check before decade gate for tradition categories (Phase 2)
- Removing/handling larry clark dual-listing regression (Phase 1)
- Adding SORTING_DATABASE pins for known misclassifications (Phase 1)
- Updating `evidence_classify()` to match new gate order (Phase 2)

**NOT in scope:**
- Integration function (Phase 3) — deferred to follow-up issue once Phase 1+2 are validated
- Within-category confidence tiering (Category Core/Reference/Texture) — data structure exists in theory (SATELLITE_DEPTH.md) but routing doesn't need it yet
- Movement categories (FNW, AmNH, JNW) — gate ordering is intentional for these, no change
- Changing country_codes or decade bounds for any category — structural signal rules unchanged
- Adding new Satellite categories — out of scope
- Wikipedia API integration — director research is manual, results go into constants.py
- Music Films or Indie Cinema routing changes — negative-space categories not affected by this issue

**Deferred to:** Follow-up issue for Phase 3 (integration function + evidence-based confidence)

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Queue classification rate | 59/403 (14.6%) | 75-90/403 (18-22%) | `python classify.py <source>` |
| Satellite auto-classified | 50 | 65-75 | Count `tmdb_satellite` + `country_satellite` in manifest |
| Indie Cinema % of satellite | 26/50 (52%) | <40% | Count Indie Cinema in satellite destinations |
| `unsorted_no_match` | 65 | 45-55 | Count in manifest |
| Director gate passes (evidence trails) | 10 | 50+ | Count `pass` in `*_director` columns of evidence_trails.csv |
| Reaudit confirmed | ≥668 (current baseline) | ≥668 (no regression) | `python scripts/reaudit.py` |
| Tests passing | 335 | 335+ (new tests added) | `pytest tests/ -v` |

**Phase 1 alone** should increase director gate passes from 10 to 50+ (data improvement). Classification rate may not change much because the decade gate still blocks.

**Phase 2** should decrease `unsorted_no_match` by 10-20 films (director-first routing catches out-of-era tradition directors).

**Pin baseline before implementing:**
```bash
git tag pre-issue-040
python scripts/reaudit.py > output/pre-040-reaudit.txt
python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted > output/pre-040-classify.txt
```

---

## 8. Validation Sequence

```bash
# Phase 1 validation (after director list expansion):
pytest tests/test_satellite.py -v
# Verify no Core whitelist conflicts:
python3 -c "
from lib.constants import SATELLITE_ROUTING_RULES, CORE_DIRECTORS
sat_dirs = set()
for rules in SATELLITE_ROUTING_RULES.values():
    sat_dirs.update(rules.get('directors') or [])
core_dirs = set(d.lower() for d in CORE_DIRECTORS)
overlap = sat_dirs & core_dirs
print(f'Overlap: {overlap}' if overlap else 'No overlap — safe')
"

# Phase 2 validation (after gate reorder):
pytest tests/ -v
python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted

# Check specific directors route correctly:
grep -i "ferrara\|corman\|van peebles\|john ford\|king hu" output/sorting_manifest.csv

# Check movement categories unchanged:
grep -i "french new wave\|american new hollywood\|japanese new wave" output/sorting_manifest.csv

# Regression check:
python audit.py && python scripts/reaudit.py

# Evidence trail check (director gates should fire more):
python3 -c "
import csv
from collections import Counter
with open('output/evidence_trails.csv') as f:
    rows = list(csv.DictReader(f))
passes = 0
for r in rows:
    for k,v in r.items():
        if k.endswith('_director') and v == 'pass':
            passes += 1
print(f'Director gate passes: {passes} (was: 10)')
"
```

**Expected results:**
- Phase 1: All existing tests pass. No Core whitelist conflicts. Director gate passes increase from 10 to 50+.
- Phase 2: All tests pass. New Rose Hotel (Ferrara, 1998) → American Exploitation. The Quiet Man (Ford, 1952) → Classic Hollywood. Movement categories (FNW, AmNH, JNW) routing unchanged.
- Reaudit: Confirmed count ≥ 668. No new wrong_tier entries. Some new wrong_category may appear if expanded directors pull films from Indie Cinema to tradition categories (these are corrections, not regressions — verify manually).

**If any step fails:** Stop. Do not proceed to next phase. Report the failure output.

---

## 9. Rollback Plan

**Detection:** Reaudit confirmed count drops below 668. Movement category films (FNW, AmNH) change routing. Indie Cinema films disappear without reclassifying to a tradition category.

**Recovery:**
```bash
# Phase 1 is data-only — revert constants.py:
git checkout pre-issue-040 -- lib/constants.py

# Phase 2 — revert satellite.py:
git checkout pre-issue-040 -- lib/satellite.py

# If cache was modified:
python scripts/invalidate_null_cache.py conservative
```

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-040
```

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `CLAUDE.md` §3 Rule 2 (Pattern-First) — the 4-tier hierarchy with Satellite routing priority. This issue fixes the internal priority within Satellite routing (director identity before structural coordinates) to match the collection thesis.
- `CLAUDE.md` §3 Rule 4 (Domain Grounding) — director lists must be sourced from published scholarship, not invented from collection contents. Wikipedia + published filmographies are the sources.
- `CLAUDE.md` §3 Rule 5 (Constraint Gates) — RC-1 (sparse director lists) is the binding constraint. Fix the data first, then the routing logic.
- `CLAUDE.md` §3 Rule 7 (Measurement-Driven) — Phase 1 is frontier (depth-first: expand director data). Phase 2 is frontier (routing logic). Validation is consistency (breadth: reaudit regression check).
- `CLAUDE.md` §3 Rule 11 (Certainty-First) — the integration model classifies high-certainty signals first (both-agree), then expands outward with decreasing certainty (director-only, structure-only) with increasing gates (review flags).

**Theory documents:**
- `docs/theory/COLLECTION_THESIS.md` §7 — "Directors are the primary units of cinema evolution." This is the thesis that director-first routing implements.
- `docs/theory/SATELLITE_DEPTH.md` §3 — Category Core / Reference / Texture within-category tiers. The director groups (A/B/C) in the investigation map to this.
- `docs/theory/TIER_ARCHITECTURE.md` §13 — "The whitelist is the thesis." Satellite needs its own equivalent: the director matrix IS the curatorial position on which directors belong to which traditions.
- `docs/theory/MARGINS_AND_TEXTURE.md` §8 — Positive-space vs negative-space categories. Director disambiguation applies to positive-space (named traditions with distinctive directors). Indie Cinema is negative-space (no director disambiguation possible).

**Architecture reference:**
- `docs/architecture/VALIDATION_ARCHITECTURE.md` §2 — Evidence trails. `evidence_classify()` is the infrastructure this issue builds on.

**Related issues:**
- `INVESTIGATION_DIRECTOR_FIRST_ROUTING.md` — precursor investigation, root cause analysis, Wikipedia-sourced director lists
- `INVESTIGATION_TWO_SIGNAL_ARCHITECTURE.md` — this session's investigation, structural precision map, signal reachability analysis, integration model
- Issue #35 (Evidence Architecture) — built `evidence_classify()` and `GateResult`/`CategoryEvidence` dataclasses that this issue's Phase 3 would use
- Issue #34 (R2B Genre Gate) — three-valued genre gate logic that this issue preserves
- Issue #25 / #32 (Core-auteurs-in-Satellite) — Core director check fires before Satellite; this issue does not change that priority

---

### Section Checklist

- [x] §1 Manager Summary is readable without code knowledge
- [x] §3 Root causes reference specific files and functions
- [x] §4 ALL downstream consumers are listed
- [x] §5 Execution Order has verify commands for each step
- [x] §5 Files to Modify is complete
- [x] §6 NOT in scope is populated
- [x] §7 Measurement Story has concrete before/after numbers
- [x] §8 Validation Sequence commands are copy-pasteable
- [x] §9 Baseline is pinned before implementation starts
- [x] §10 Theory grounding exists
