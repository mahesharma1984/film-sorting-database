# Issue #45: Enable Structural Signal for Movement Categories (Two-Signal Data Alignment)

| Field | Value |
|---|---|
| Status | SPEC |
| Priority | P1-Critical |
| Date Opened | 2026-03-05 |
| Component | Satellite Routing / Constants / Signals |
| Change Type | Data Configuration + Logic Fix |
| Estimated Effort | 1 session (data changes + 1 logic line + doc updates) |
| Blocked By | None |
| Blocks | Lookup retirement; `both_agree` metric improvement |
| Supersedes | None |

---

## 1. Manager Summary

**Problem:** The two-signal architecture (Issue #42) has a structural signal that is permanently disabled for 5 movement categories: French New Wave, American New Hollywood, Japanese New Wave, Hong Kong New Wave, and Hong Kong Category III. These categories have `country_codes: []` and `genres: []` in `SATELLITE_ROUTING_RULES`, which prevents `classify_structural()` from producing any structural matches. The reason code `both_agree` — requiring both director AND structural signals to fire — is structurally impossible for these categories.

This explains why Issue #44 (director data expansion) did not increase `both_agree`: expanding director lists has no effect when the structural signal cannot fire. The director signal fires alone (P4 `director_signal`, confidence 0.65) rather than being confirmed by structure (P2 `both_agree`, confidence 0.85).

**Impact if unfixed:**
- `both_agree` permanently impossible for 5 categories (~30% of Satellite taxonomy)
- Director expansion (Issue #44) delivers no confidence improvement for movement films
- Signal bypass audit AGREE rate stuck at ~31% regardless of director list quality
- Movement-period films by known directors get 0.65 confidence instead of 0.85

**Risk if fixed wrong:**
- Adding `country_codes` without fixing `is_tradition` derivation would make movement directors decade-agnostic (a 2020 Godard film would be decade_valid for FNW — incorrect)
- Broad structural matching (country+decade with no genre filter) could produce noise for US/FR films in those decades — but this is architecturally expected and handled by director disambiguation (P3)

**Estimated effort:** 1 session. Changes are minimal: 5 data entries in constants.py, 1 line in `_build_director_registry()`, stale doc notes, test updates.

---

## 2. Evidence

### Observation

After Issue #44 added 28 directors to tradition category lists, the bypass audit showed:
- AGREE: 122/389 (31.4%) — virtually unchanged from pre-#44
- `both_agree` count: unchanged for movement categories (0 for all 5)

Movement category films by known directors produce `director_signal` (0.65) instead of `both_agree` (0.85) because the structural signal never fires.

### Data

**`classify_structural()` output for movement category films (tested):**

| Film | Director | Country | Year | Structural matches | Expected |
|---|---|---|---|---|---|
| Taxi Driver | Scorsese | US | 1976 | [] (empty — no AmNH structural) | `[('American New Hollywood', 'country_genre')]` |
| Breathless | Godard | FR | 1960 | EuroSex only (no FNW structural) | `[('French New Wave', 'country_genre')]` |
| In the Mood for Love | Wong Kar-wai | HK | 2000 | HK Action only (no HK NW structural) | `[('Hong Kong New Wave', 'country_genre')]` |

**Root mechanism (satellite.py lines 497-499):**
```python
country_match = True
if rules['country_codes'] is not None:          # [] is not None → enters check
    country_match = any(c in countries for c in rules['country_codes'])  # any(... for c in []) → False
```

`country_codes: []` makes `country_match = False` for every film. No structural path can fire.

**`genres: []` compounds the problem (satellite.py lines 502-507):**
```python
genre_match = True
if rules['genres'] is not None:                 # [] is not None → enters check
    genre_match = any(g in genres for g in rules['genres'])  # any(... for g in []) → False
```

Even if country_match were fixed, `genres: []` would block the country_genre match (line 518: `if country_match and genre_match is True`).

---

## 3. Root Cause Analysis

### RC-1: SATELLITE_ROUTING_RULES data configuration drift (§0.6)

**Location:** `lib/constants.py` → `SATELLITE_ROUTING_RULES` → 5 movement category entries

**Mechanism:** Movement categories were designed with `country_codes: []` and `genres: []` for the **old sequential pipeline** (pre-Issue #42), where they used director-only routing. The empty lists meant "don't do structural matching — only match via director list." This was correct under the old pipeline where each stage was a hard gate.

Under two-signal (Issue #42), `classify_structural()` replaced the old structural stage. It reads `country_codes` and `genres` from `SATELLITE_ROUTING_RULES` to compute the structural signal. Empty lists silence the signal entirely. The routing rules were never updated to reflect the new architecture.

**Work Router classification:** §0.6 Drift Audit — "A new upstream stage was added — do downstream processes consume its output?" The two-signal layer was added; the routing rules data was not updated to feed it.

### RC-2: `is_tradition` derived from `bool(country_codes)` — accidental conflation

**Location:** `lib/constants.py` line 1035

**Mechanism:**
```python
is_tradition = bool(rules.get('country_codes'))
```

This derives a semantic property (tradition vs movement) from a structural gate configuration (whether country_codes is populated). Currently works by coincidence: traditions have country_codes, movements don't. After fixing RC-1 (adding country_codes to movements), this derivation flips `is_tradition` to `True` for movements — making movement directors decade-agnostic in `score_director()`, which is incorrect.

**Effect if unfixed:** A 2020 Godard film would produce `decade_valid=True` for FNW (should be False — Godard's FNW period was 1960s-1970s).

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| SATELLITE_ROUTING_RULES → classify_structural() | `lib/constants.py` data | `lib/satellite.py classify_structural()` | Yes — movement entries gain country_codes and genres=None |
| SATELLITE_ROUTING_RULES → _build_director_registry() | `lib/constants.py` data | `lib/constants.py _build_director_registry()` | Yes — reads explicit `is_tradition` field |
| classify_structural() → score_structure() | `lib/satellite.py` | `lib/signals.py score_structure()` | No — same return type, more results |
| score_structure() → integrate_signals() | `lib/signals.py` | `lib/signals.py integrate_signals()` | No — same StructuralMatch type, more matches |
| integrate_signals() → manifest | `lib/signals.py` | `classify.py` | No — same IntegrationResult, different reason codes (both_agree instead of director_signal) |

**Gate impact:** Adding structural paths can change reason codes (director_signal → both_agree) and confidence (0.65 → 0.85) for films that already route correctly. Destinations remain the same — same Satellite category, same decade. No tier changes.

**Exception risk:** FR+1960s now structurally matches both FNW AND European Sexploitation. US+1970s now matches AmNH AND (if keyword gate passes) AmExploitation/Blaxploitation. These are expected overlaps — TWO_SIGNAL_ARCHITECTURE.md §2 documents them. P3 `director_disambiguates` and P8 `review_flagged` handle them correctly.

---

## 5. Proposed Fix

### Fix Description

Two root causes, two targeted fixes:

**RC-1 fix:** Add `country_codes` and fix `genres` for 5 movement categories in `SATELLITE_ROUTING_RULES`. This enables `classify_structural()` to produce structural matches for movements.

**RC-2 fix:** Add explicit `is_tradition` field to each `SATELLITE_ROUTING_RULES` entry. Update `_build_director_registry()` to read it instead of deriving from `bool(country_codes)`.

### Execution Order

#### Step 1: Add `is_tradition` field to ALL SATELLITE_ROUTING_RULES entries

Add `'is_tradition': True` to all tradition categories.
Add `'is_tradition': False` to all 5 movement categories.

#### Step 2: Update `_build_director_registry()` (line 1035)

```python
# Before:
is_tradition = bool(rules.get('country_codes'))

# After:
is_tradition = rules.get('is_tradition', bool(rules.get('country_codes')))
```

#### Step 3: Fix `country_codes` and `genres` for 5 movement categories

| Category | `country_codes` | `genres` |
|---|---|---|
| French New Wave | `[]` → `['FR']` | `[]` → `None` |
| American New Hollywood | `[]` → `['US']` | `[]` → `None` |
| Japanese New Wave | `[]` → `['JP']` | `[]` → `None` |
| Hong Kong New Wave | `[]` → `['HK']` | `[]` → `None` |
| Hong Kong Category III | `[]` → `['HK']` | `[]` → `None` |

`genres: None` rationale: movements span all genres (FNW includes drama, crime, comedy; AmNH includes crime, horror, drama). Genre is not a discriminator. `None` = "no genre restriction" (gate passes). `[]` = "empty match list" (gate blocks everything).

COUNTRY_TO_WAVE is NOT modified — it remains for tradition categories only. Movement structural matching goes through `classify_structural()` which applies the full country+genre+decade+keyword logic.

#### Step 4: Update stale CLAUDE.md §4 FNW note

Current: "France ('FR') is intentionally excluded from COUNTRY_TO_WAVE — adding it would auto-route all French films in those decades to FNW regardless of movement membership."

Update to reflect: FR is added to FNW's `country_codes` in SATELLITE_ROUTING_RULES (not COUNTRY_TO_WAVE). Under two-signal, structural match = candidate signal (0.65); director identity confirms or denies. No auto-routing without director confirmation.

#### Step 5: Update TWO_SIGNAL_ARCHITECTURE.md §2

Add note that movement categories participate in structural matching via country+decade coordinates (no genre restriction). Genres discriminate traditions (IT+Horror→Giallo) but not movements (FR+any genre→FNW candidate).

#### Step 6: Update tests

Fix/add test cases in `tests/test_signals.py` for movement structural matching.

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `lib/constants.py` | Data + logic | Add `is_tradition` to all entries; fix country_codes/genres for 5 entries; update `_build_director_registry()` line 1035 |
| `CLAUDE.md` | Documentation | Update §4 FNW note |
| `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` | Documentation | §2 movement structural note |
| `tests/test_signals.py` | Tests | Fix/add movement structural test cases |

---

## 6. Scope Boundaries

**In scope:**
- Adding `is_tradition` field to all SATELLITE_ROUTING_RULES entries
- Fixing `country_codes` and `genres` for 5 movement categories
- Updating `_build_director_registry()` to read explicit `is_tradition`
- Updating stale CLAUDE.md and architecture doc notes
- Fixing/adding tests for movement structural matching

**NOT in scope:**
- Changing integration priority table (P1-P10) in `integrate_signals()`
- Adding directors to any category lists (that's Issue #44)
- Modifying COUNTRY_TO_WAVE
- Adding new Satellite categories
- Core-vs-Satellite routing priority (P5 behavior is intentional per RECURSIVE_CURATION_MODEL §3)
- Lookup retirement

**Deferred to:** Post-implementation measurement to determine if overlap handling (FR+1960s FNW+EuroSex, US+1970s AmNH+AmExploit) produces acceptable or excessive `review_flagged` noise.

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| `both_agree` for movement categories | 0 (impossible) | >0 (enabled) | `grep both_agree output/sorting_manifest.csv` and check category |
| `director_signal` → `both_agree` upgrades | 0 | 10+ | Movement films that had `director_signal` should now show `both_agree` |
| Confidence for movement director films | 0.65 (director_signal) | 0.85 (both_agree) | Check confidence column in manifest |
| Bypass audit AGREE rate | ~122/389 (31%) | Higher | `python scripts/audit_lookup_coverage.py` |
| Reaudit confirmed | Current baseline | ≥ current baseline | `python scripts/reaudit.py` |

**Signal ratio shift:** Movement films with known directors gain structural confirmation, upgrading from single-signal (0.65) to dual-signal (0.85). The structural signal now fires for all categories, not just tradition categories.

**Regression gate:** Reaudit confirmed count must not drop. Any new `wrong_tier` or `wrong_category` entry is a stop condition.

---

## 8. Validation Sequence

```bash
# Step 1: Verify is_tradition field is correctly read
python3 -c "
import sys; sys.path.insert(0,'.')
from lib.constants import DIRECTOR_REGISTRY
# Check a movement director — should have is_tradition=False
for key in ['truffaut', 'martin scorsese']:
    entries = DIRECTOR_REGISTRY.get(key, [])
    for e in entries:
        print(f'{key} → {e.category}: is_tradition={e.is_tradition}, decades={e.decades}')
"

# Step 2: Verify structural matching now fires for movements
python3 -c "
import sys; sys.path.insert(0,'.')
from lib.satellite import SatelliteClassifier
from types import SimpleNamespace
sc = SatelliteClassifier()
# French film 1965 — should match FNW structurally
meta = SimpleNamespace(title='Test', year=1965, country='FR', director='Test')
results = sc.classify_structural(meta, {'countries': ['FR'], 'genres': ['Drama']})
print('FR 1965 structural:', results)
# US film 1975 — should match AmNH structurally
meta2 = SimpleNamespace(title='Test', year=1975, country='US', director='Test')
results2 = sc.classify_structural(meta2, {'countries': ['US'], 'genres': ['Drama']})
print('US 1975 structural:', results2)
"

# Step 3: Verify both_agree fires for movement directors
python3 -c "
import sys; sys.path.insert(0,'.')
from lib.signals import score_director, score_structure, integrate_signals
from lib.satellite import SatelliteClassifier
from lib.popcorn import PopcornClassifier
from lib.core_directors import CoreDirectorDatabase
from types import SimpleNamespace
core_db = CoreDirectorDatabase('docs/CORE_DIRECTOR_WHITELIST_FINAL.md')
sc = SatelliteClassifier()
pc = PopcornClassifier()
# Truffaut (FNW director, not Core) + FR 1962
meta = SimpleNamespace(title='Jules and Jim', year=1962, country='FR', director='François Truffaut')
tmdb = {'countries': ['FR'], 'genres': ['Drama', 'Romance'], 'keywords': [], 'popularity': 5, 'vote_count': 100}
d = score_director('François Truffaut', 1962, core_db)
s = score_structure(meta, tmdb, sc, pc)
result = integrate_signals(d, s, '1960s', 'R3')
print(f'Truffaut 1962: {result.reason} → {result.destination} (conf={result.confidence})')
# Expected: both_agree → Satellite/French New Wave/1960s/ (conf=0.85)
"

# Step 4: Verify is_tradition=False prevents decade leakage
python3 -c "
import sys; sys.path.insert(0,'.')
from lib.constants import DIRECTOR_REGISTRY
# Truffaut in FNW should have is_tradition=False
entries = DIRECTOR_REGISTRY.get('truffaut', [])
for e in entries:
    print(f'is_tradition={e.is_tradition}, decades={e.decades}')
# With is_tradition=False, a 2020 Truffaut film should NOT be decade_valid
from lib.signals import score_director
from lib.core_directors import CoreDirectorDatabase
core_db = CoreDirectorDatabase('docs/CORE_DIRECTOR_WHITELIST_FINAL.md')
d = score_director('François Truffaut', 2020, core_db)
for m in d:
    print(f'{m.category}: decade_valid={m.decade_valid}')
# Expected: decade_valid=False for FNW (2020 outside 1950s-1970s)
"

# Step 5: Run full test suite
pytest tests/ -v

# Step 6: Classify organized library
python classify.py "/Volumes/One Touch/Movies/Organized"

# Step 7: Check signal distribution
python3 -c "
import csv; from collections import defaultdict
counts = defaultdict(int)
with open('output/sorting_manifest.csv') as f:
    for row in csv.DictReader(f):
        counts[row['reason']] += 1
for r in ['both_agree','director_signal','director_disambiguates','structural_signal','review_flagged']:
    print(f'{r}: {counts[r]}')
"

# Step 8: Bypass audit
python scripts/audit_lookup_coverage.py

# Step 9: Regression check
python audit.py && python scripts/reaudit.py --review
```

**Expected results:**
- Step 1: Movement directors show `is_tradition=False`
- Step 2: FR 1965 → includes `('French New Wave', 'country_genre')`; US 1975 → includes `('American New Hollywood', 'country_genre')`
- Step 3: Truffaut 1962 → `both_agree`, confidence 0.85
- Step 4: Truffaut 2020 → `decade_valid=False` for FNW
- Step 5: All tests pass
- Step 7: `both_agree` count > pre-implementation baseline
- Step 9: Confirmed count ≥ baseline; no new `wrong_tier`

---

## 9. Rollback Plan

**Detection:**
- `is_tradition=True` for movement directors (decade leakage)
- New `wrong_tier` or `wrong_category` in reaudit
- Excessive `review_flagged` noise from country+decade overlap

**Recovery:**
```bash
git revert [commit-hash]
python classify.py "/Volumes/One Touch/Movies/Organized"
python audit.py && python scripts/reaudit.py
```

Changes are data-only (no new files, no new functions, no cache impact). Clean revert restores previous state.

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` §1 — "Both signals run for every film. Neither short-circuits the other." Movement categories currently violate this: structural signal is disabled.
- `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` §2 — Structural Triangulation: "Country + decade + genre locate a film in a coordinate space. Some regions are owned by a single tradition. Some overlap." Overlap is expected and handled by integration.
- `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` §5 — Signal Populations: Two-signal applies to Population C (heuristic pipeline). Movement categories are heuristic pipeline films — they should get both signals.
- `CLAUDE.md §3 Rule 2` — Pattern-First: the two-signal architecture is the pattern. Movement categories must conform to it.
- `CLAUDE.md §3 Rule 7` — Measurement-Driven: `both_agree` count is the metric that Issue #44 was supposed to improve. It can't improve while the structural signal is disabled.

**Work Router classification:**
- §0.6 Drift Audit: "A new upstream stage was added — do downstream processes consume its output?" Two-signal (Issue #42) was added; SATELLITE_ROUTING_RULES data for 5 movement categories was not updated to feed it.
- §0.1 Problem classification: "The logic and architecture are right, but the DATA doesn't match." The integration logic (P1-P10) works correctly. The data configuration (empty country_codes/genres) prevents it from receiving input.

**Related issues:**
- #42 — Implemented two-signal architecture (created the dependency on structural signal)
- #44 — Expanded director lists (impact blocked by this issue)
- #40 — First two-signal implementation (movement categories already had `country_codes: []`)

---
