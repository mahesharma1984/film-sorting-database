# Issue #47: Core Director P2 Bypass Bug — Dual-Listed Directors Route to Satellite

| Field | Value |
|---|---|
| Status | SPEC |
| Priority | P2-High |
| Date Opened | 2026-03-05 |
| Component | Signals / Constants / Satellite Routing |
| Change Type | Bug Fix |
| Estimated Effort | ~2 hours |
| Blocked By | None |
| Blocks | Lookup retirement (#45 follow-up) |
| Supersedes | None |

---

## 1. Manager Summary

**Problem:** Six Core directors (Godard, Scorsese, Demy, Denis, Jarmusch, Rivette) appear in both the Core director whitelist (`docs/CORE_DIRECTOR_WHITELIST_FINAL.md`) and the `SATELLITE_ROUTING_RULES['directors']` list for their movement category (FNW, AmNH, Indie Cinema). In `integrate_signals()`, P2 (Satellite director + structural match → `both_agree`) fires before Core logic (P5/P6). These directors are routed to Satellite with 0.85 confidence when they should be recognised as Core.

**Impact if unfixed:**
- 17 films routed to Satellite/FNW, Satellite/AmNH, or Satellite/Indie Cinema by two-signal despite the director being Core
- Any Godard, Scorsese, Demy, Denis, Jarmusch, or Rivette film NOT yet pinned in SORTING_DATABASE will mis-route to Satellite — silently, at high confidence (0.85 `both_agree`)
- SORTING_DATABASE pins are masking the bug for the 17 known cases; future films added to the library without pins will be affected
- The bypass audit AGREE rate is suppressed: SORTING_DATABASE pins save these films, but the two-signal layer's actual routing is wrong

**Risk if fixed wrong:**
- Removing a director from the Satellite list who should NOT be in Core whitelist → their films lose director routing entirely (falls back to structural_signal or unsorted)
- Removing the wrong directors → movement films by genuine Satellite-only directors lose routing

**Estimated effort:** ~2 hours. Change is data-only (remove names from 3 director lists). No logic changes.

---

## 2. Evidence

### Observation

Post-Issue #45 bypass audit on 389 explicit_lookup films:

```
AGREE    : 122 / 389  (31.4%)  — two-signal reaches same destination as SORTING_DATABASE
DISAGREE : 172 / 389  (44.2%)  — two-signal routes elsewhere
UNSORTED :  95 / 389  (24.4%)  — two-signal cannot classify
```

Of the 172 DISAGREE films, 93 are Core films routed to Satellite. These break into two structurally distinct populations:

### Data

**Population A — 73 films, structural_signal (P5): designed behaviour**

P5 rule (Issue #25): when a Core director's film has Satellite structural coordinates, Satellite wins. These are correct per architecture — SORTING_DATABASE pins are the designed resolution for cases where the curator wants Core to win. NOT a bug.

Top structural misroutes:
- Core → Indie Cinema: 33 (Satyajit Ray, Kieslowski, Kiarostami etc. — correct country coordinates)
- Core → Giallo: 11 (Italian Core directors — correct country+genre coordinates)
- Core → European Sexploitation: 9 (FR/IT Core directors + Drama/Romance coordinates)
- Core → Hong Kong Action: 7 (Wong Kar-Wai — HK + 1980s-1990s + Crime coordinates)
- Core → Classic Hollywood: 6 (Billy Wilder — US + 1940s-1950s coordinates)

**Population B — 17 films, both_agree (P2): this is the bug**

Directors appearing in BOTH CoreDirectorDatabase AND SATELLITE_ROUTING_RULES directors lists. P2 (Satellite director + structural match) fires before P5/P6 can apply Core logic.

| Director | Core Films Mis-routed | Satellite Category (wrong) |
|---|---|---|
| Jean-Luc Godard | 6 | French New Wave |
| Martin Scorsese | 5 | American New Hollywood |
| Jacques Demy | 3 | French New Wave |
| Claire Denis | 1 | Indie Cinema |
| Jim Jarmusch | 1 | Indie Cinema |
| Jacques Rivette | 1 | French New Wave |
| **Total** | **17** | |

**Population C — 3 films, director_signal: minor format mismatch**

Core canonical_name format differs between whitelist and SORTING_DATABASE key. Not related to the P2 bug.

### Code path (lib/signals.py `integrate_signals()`)

```python
# Line ~271
sat_dir_valid = [m for m in director_matches if m.tier == 'Satellite' and m.decade_valid]
core_dir      = [m for m in director_matches if m.tier == 'Core']

# Line ~289 — P2/P3/P4 fires FIRST
if sat_dir_valid:                          # ← Godard has FNW Satellite match → True
    dm = sat_dir_valid[0]
    structural_same = any(sm.category == dm.category for sm in sat_struct)
    if structural_same:
        reason = 'both_agree'              # ← fires here — Core match never checked
        ...
    return IntegrationResult(tier='Satellite', ...)

# P5/P6 never reached for dual-listed directors
```

`score_director()` correctly returns both Core and Satellite matches. The bug is in integration priority: P2 (Satellite) precedes P5 (Core+structural) and P6 (Core alone). When a director has a valid Satellite match (decade_valid=True in the active movement period), P2 fires unconditionally.

---

## 3. Root Cause Analysis

### RC-1: Dual-listed directors in SATELLITE_ROUTING_RULES

**Location:** `lib/constants.py` → `SATELLITE_ROUTING_RULES`

**Mechanism:** The SATELLITE_ROUTING_RULES directors lists for French New Wave, American New Hollywood, and Indie Cinema contain directors who are also in the Core whitelist. These directors were added to the Satellite lists to enable director-only routing in the old sequential pipeline (pre-Issue #42), where Core check fired at Stage 3 before Satellite routing at Stages 4-8. In the two-signal architecture, both signals fire independently — `score_director()` returns ALL matches across all lists, and P2 fires for the Satellite match before Core logic applies.

**Affected entries in SATELLITE_ROUTING_RULES:**

| Category | Dual-listed directors (also in Core whitelist) |
|---|---|
| French New Wave | `godard`, `varda`, `chabrol`, `demy`, `duras`, `resnais`, `rivette` |
| American New Hollywood | `fosse`, `ashby`, `pakula`, `coppola`, `scorsese` (check each against whitelist) |
| Indie Cinema | `denis`, `assayas`, `jarmusch`, `linklater`, `haynes`, `reichardt` (check each) |

Note: not all listed directors are in Core whitelist — only those confirmed in `docs/CORE_DIRECTOR_WHITELIST_FINAL.md` are the problem. The 17 films in the bypass audit identify exactly which directors are causing the bug.

### RC-2: No Core-priority guard in integrate_signals() P2-P4 block

**Location:** `lib/signals.py` → `integrate_signals()` lines ~289-317

**Mechanism:** The P2-P4 block fires when `sat_dir_valid` is non-empty, regardless of whether `core_dir` is also non-empty. For dual-listed directors, `sat_dir_valid` contains the Satellite match and `core_dir` contains the Core match simultaneously. P2 fires for the Satellite match; Core is never considered.

**Alternative fix (secondary option):** Add a guard `if sat_dir_valid and not core_dir:` in the P2-P4 block. This is defensively correct but treats the symptom rather than the cause. The data fix (RC-1) is preferred because:
- It removes invalid data entries (the lists were wrong for the new architecture)
- It makes the intent explicit without adding conditional complexity to integration logic
- A director who is Core should not appear in Satellite director lists at all

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| SATELLITE_ROUTING_RULES → score_director() | `lib/constants.py` DIRECTOR_REGISTRY | `lib/signals.py score_director()` | Yes — directors removed from registry |
| score_director() → integrate_signals() | `lib/signals.py` | `lib/signals.py integrate_signals()` | Yes — sat_dir_valid no longer contains Core directors |
| integrate_signals() → classify.py | `lib/signals.py` | `classify.py` | Yes — reason code changes: both_agree→director_signal (Core) for affected films |
| SATELLITE_ROUTING_RULES → classify() | `lib/constants.py` | `lib/satellite.py classify()` | Yes — movement director check no longer fires for these directors |

**Gate impact:**
- Reaudit confirmed count should remain ≥ 718. Affected films are currently rescued by SORTING_DATABASE (explicit_lookup fires before two-signal), so reaudit verdicts won't change.
- Bypass audit AGREE rate: the 17 both_agree Core→Satellite cases become either AGREE (if two-signal now produces Core correctly) or DISAGREE via structural_signal (P5 fires for films with Satellite coordinates).

**Downstream consumers of changed output:**
- `lib/satellite.py classify()`: movement director check no longer fires for Godard, Scorsese, etc. — they fall through to structural checks, which are gated by country+decade in the old pipeline.
- `classify.py` two-signal path: `score_director()` returns Core-only match for these directors → P4/P6 fires instead of P2.

---

## 5. Proposed Fix

### Fix Description

Remove the dual-listed directors from `SATELLITE_ROUTING_RULES` director lists. A director who is in the Core whitelist should not also appear in a Satellite category's director list. Their Core whitelist membership is the authoritative signal. For their movement-period films, the structural signal (country + decade) still fires independently — if that structural match is correct, it routes via P5 (Satellite wins) or P7 (structural_signal). If the curator wants a specific film to stay in Core against structural evidence, SORTING_DATABASE is the correct pin mechanism (as designed in Issue #25).

### Execution Order

#### Step 1: Confirm which directors are dual-listed

Cross-reference `SATELLITE_ROUTING_RULES` directors lists against `docs/CORE_DIRECTOR_WHITELIST_FINAL.md`. The 17-film bypass audit identifies the active cases, but the full list of entries to remove is:

From the bypass audit `both_agree` mis-routes:
- `godard`, `demy`, `rivette` — in FNW directors list, confirmed Core
- `scorsese` — in AmNH directors list, confirmed Core
- `denis` — in Indie Cinema directors list, confirmed Core
- `jarmusch` — in Indie Cinema directors list, confirmed Core

Cross-check for completeness (may have additional dual-listed directors not yet exposed by bypass audit):
```bash
python3 -c "
import sys; sys.path.insert(0,'.')
from lib.constants import SATELLITE_ROUTING_RULES
from lib.core_directors import CoreDirectorDatabase
from pathlib import Path
core_db = CoreDirectorDatabase(Path('docs/CORE_DIRECTOR_WHITELIST_FINAL.md'))
for cat, rules in SATELLITE_ROUTING_RULES.items():
    for d in (rules.get('directors') or []):
        match = core_db.find(d.title(), None)
        if match:
            print(f'DUAL-LISTED: {d!r} in {cat} AND Core ({match.canonical_name})')
"
```

#### Step 2: Remove dual-listed directors from SATELLITE_ROUTING_RULES

**File:** `lib/constants.py`

For each confirmed dual-listed director, delete their entry from the relevant category's `directors` list. Add a comment explaining why:

```python
# Note: [director name] removed (Issue #47) — in Core whitelist.
# Core identity takes priority; structural signal still fires for their films via country+decade.
# Use SORTING_DATABASE pins to override Satellite structural routing for specific films.
```

Entries to remove:
- `'French New Wave'` directors: `'godard'`, `'varda'`, `'chabrol'`, `'demy'`, `'duras'`, `'resnais'`, `'rivette'` — ALL confirmed Core
- `'American New Hollywood'` directors: `'fosse'`, `'ashby'`, `'pakula'`, `'coppola'`, `'scorsese'` — verify each against whitelist
- `'Indie Cinema'` directors: `'denis'`, `'assayas'`, `'jarmusch'`, `'linklater'`, `'haynes'`, `'reichardt'` — verify each against whitelist

#### Step 3: Run full test suite

```bash
pytest tests/ -v
```

Expected: 378 pass, 1 skip. If any signal tests fail, check `tests/test_signals.py` for tests that assume these directors produce Satellite matches.

#### Step 4: Verify Core routing for affected directors

```bash
python3 -c "
import sys; sys.path.insert(0,'.')
from pathlib import Path
from lib.signals import score_director, integrate_signals, score_structure
from lib.core_directors import CoreDirectorDatabase
from lib.satellite import SatelliteClassifier
from lib.popcorn import PopcornClassifier
from types import SimpleNamespace

core_db = CoreDirectorDatabase(Path('docs/CORE_DIRECTOR_WHITELIST_FINAL.md'))
sc = SatelliteClassifier(); pc = PopcornClassifier()

# Godard 1960 — should now route via Core, not Satellite/FNW
meta = SimpleNamespace(title='Breathless', year=1960, country='FR', director='Jean-Luc Godard')
tmdb = {'countries': ['FR'], 'genres': ['Crime', 'Drama'], 'keywords': [], 'popularity': 8, 'vote_count': 500}
d = score_director('Jean-Luc Godard', 1960, core_db)
s = score_structure(meta, tmdb, sc, pc)
result = integrate_signals(d, s, '1960s', 'R3')
print(f'Godard 1960: {result.reason} → {result.destination} (conf={result.confidence})')
# Expected: director_signal → Core/1960s/Jean-Luc Godard/ (P6)
# OR: structural_signal → Satellite/French New Wave/1960s/ (P5, if FNW structural fires)

# Scorsese 1976 — should route via Core
meta2 = SimpleNamespace(title='Taxi Driver', year=1976, country='US', director='Martin Scorsese')
tmdb2 = {'countries': ['US'], 'genres': ['Crime', 'Drama'], 'keywords': [], 'popularity': 8, 'vote_count': 1000}
d2 = score_director('Martin Scorsese', 1976, core_db)
s2 = score_structure(meta2, tmdb2, sc, pc)
result2 = integrate_signals(d2, s2, '1970s', 'R3')
print(f'Scorsese 1976: {result2.reason} → {result2.destination} (conf={result2.confidence})')
# Expected: structural_signal → Satellite/American New Hollywood/1970s/ (P5)
# NOTE: P5 fires because Core + AmNH structural → Satellite wins (Issue #25 design).
# SORTING_DATABASE pin keeps Taxi Driver in Core. Two-signal correctly reflects ambiguity.
"
```

**Note on expected output:** After the fix, Godard and Scorsese may still route to Satellite via P5 (Core director + Satellite structural coordinates → Satellite wins, Issue #25). This is correct — P5 is designed behaviour. The important change is the reason code: `both_agree` (wrong — implies Satellite director identity) → `structural_signal` (correct — ambiguous, structural wins over Core). SORTING_DATABASE pins handle specific films that should stay in Core.

#### Step 5: Run bypass audit and compare

```bash
python scripts/audit_lookup_coverage.py
```

Expected change: the 17 `both_agree` Core→Satellite DISAGREE cases become `structural_signal` Core→Satellite DISAGREE (still DISAGREE, but now for the correct reason — P5 structural wins, not P2 mis-routing). AGREE count stays at ~122.

#### Step 6: Reaudit regression check

```bash
python scripts/reaudit.py --review
```

Expected: confirmed ≥ 718. No new `wrong_tier`. Affected films stay in Core because SORTING_DATABASE pins fire before two-signal.

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `lib/constants.py` | Data | Remove dual-listed Core directors from `SATELLITE_ROUTING_RULES` FNW, AmNH, Indie Cinema director lists |
| `tests/test_signals.py` | Fix | Update any tests that assert Godard/Scorsese/Demy etc. produce Satellite `director_signal` or `both_agree` — they should now produce only Core matches from `score_director()` |

---

## 6. Scope Boundaries

**In scope:**
- Removing confirmed-Core directors from Satellite DIRECTOR_REGISTRY entries
- Updating tests that assert incorrect Satellite director matches for Core directors
- Adding explanatory comments in constants.py for removed entries

**NOT in scope:**
- Changing integrate_signals() priority table (P1-P10) — the P2-before-Core ordering is correct; the data was wrong
- Adding a `core_dir` guard to P2-P4 in integrate_signals() — this treats the symptom; removing the data is the correct fix
- Changing SORTING_DATABASE pins for affected films — they remain correct and necessary (P5 still routes these films to Satellite structurally; SORTING_DATABASE keeps them in Core as curator overrides)
- Fixing Population A (73 structural_signal Core→Satellite films) — these are P5 designed behaviour (Issue #25); SORTING_DATABASE is the resolution mechanism
- Increasing the bypass audit AGREE rate beyond what this fix produces — Population A (73 films) requires a broader architectural discussion about SORTING_DATABASE vs two-signal priority

**Deferred to:** Post-fix measurement to confirm that Godard/Scorsese two-signal output is now `structural_signal` (P5) rather than `both_agree` (P2). If P5 fires and routes to Satellite where curator wants Core, new SORTING_DATABASE pins may be needed.

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Reaudit confirmed | 718 / 796 | ≥ 718 / 796 | `python scripts/reaudit.py --review` |
| Bypass audit AGREE | 122 / 389 (31.4%) | ~122 / 389 (stable) | `python scripts/audit_lookup_coverage.py` |
| `both_agree` Core→Sat in bypass | 17 | 0 | filter lookup_coverage.csv |
| `both_agree` reason in reaudit | 37 | 37 ± 2 | check reaudit_report.csv |
| `score_director(Godard)` Satellite matches | present | absent | inline python check |

**Note on AGREE rate:** Removing dual-listed directors does not increase AGREE — the 17 films move from `both_agree` DISAGREE (wrong reason) to `structural_signal` DISAGREE (P5, correct reason). They remain DISAGREE because structural coordinates still point to Satellite and P5 fires. SORTING_DATABASE pins handle their Core placement. The AGREE rate improvement requires addressing Population A (73 films, P5 structural) — a separate architectural question.

**Pre-implementation baseline (current):**
```
Reaudit: 718 confirmed, 78 discrepancies
both_agree: 37, director_signal: 30, structural_signal: 199, review_flagged: 64
Bypass audit: AGREE 122, DISAGREE 172, UNSORTED 95
Core→Satellite both_agree in bypass: 17 films (Godard×6, Scorsese×5, Demy×3, Denis×1, Jarmusch×1, Rivette×1)
```

---

## 8. Validation Sequence

```bash
# Step 1: Confirm dual-listed directors before making changes
python3 -c "
import sys; sys.path.insert(0,'.')
from lib.constants import SATELLITE_ROUTING_RULES
from lib.core_directors import CoreDirectorDatabase
from pathlib import Path
core_db = CoreDirectorDatabase(Path('docs/CORE_DIRECTOR_WHITELIST_FINAL.md'))
for cat, rules in SATELLITE_ROUTING_RULES.items():
    for d in (rules.get('directors') or []):
        match = core_db.find(d.title(), None)
        if match:
            print(f'DUAL-LISTED: {d!r} in {cat} AND Core ({match.canonical_name})')
"

# Step 2: Run tests
pytest tests/ -v

# Step 3: Verify Godard produces Core-only director match
python3 -c "
import sys; sys.path.insert(0,'.')
from pathlib import Path
from lib.signals import score_director
from lib.core_directors import CoreDirectorDatabase
core_db = CoreDirectorDatabase(Path('docs/CORE_DIRECTOR_WHITELIST_FINAL.md'))
matches = score_director('Jean-Luc Godard', 1965, core_db)
print('Godard director matches:')
for m in matches: print(f'  tier={m.tier}, category={getattr(m,\"category\",\"?\")}, source={m.source}')
# Expected: ONLY Core match (no Satellite/FNW match)
"

# Step 4: Bypass audit — confirm 0 both_agree Core→Satellite
python scripts/audit_lookup_coverage.py
python3 -c "
import csv
rows = list(csv.DictReader(open('output/lookup_coverage.csv')))
ba_core = [r for r in rows if r['verdict']=='DISAGREE'
           and r['explicit_destination'].startswith('Core/')
           and r['signal_reason']=='both_agree']
print(f'both_agree Core→Satellite: {len(ba_core)} (target: 0)')
for r in ba_core: print(f'  {r[\"director\"]}: {r[\"explicit_destination\"]} → {r[\"signal_destination\"]}')
"

# Step 5: Reaudit regression check
python scripts/reaudit.py --review
# Expected: confirmed ≥ 718, no new wrong_tier
```

**Expected results:**
- Step 1: Prints list of dual-listed directors (confirms what to remove)
- Step 2: All 378 tests pass, 1 skipped (some test assertions may need updating)
- Step 3: Godard returns Core match only — no Satellite/FNW entry
- Step 4: `both_agree Core→Satellite: 0`
- Step 5: Confirmed ≥ 718; discrepancies ≤ 78

---

## 9. Rollback Plan

**Detection:**
- Reaudit confirmed drops below 718
- New wrong_tier entries for Godard, Scorsese, Demy, Denis, Jarmusch, or Rivette films
- `score_director('Jean-Luc Godard')` returns no matches at all (removed too aggressively)

**Recovery:**
```bash
git revert [commit-hash]
pytest tests/ -v
python scripts/reaudit.py --review
```

Changes are data-only (director name strings removed from constants.py). No cache impact. Clean revert restores prior state in one command.

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-047
```

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `CLAUDE.md §3 Rule 1` (R/P Split): "Check Core director whitelist" is classified as REASONING (structured rules, Code actor). The whitelist should be the authoritative source — a director cannot simultaneously be Core and Satellite.
- `CLAUDE.md §3 Rule 2` (Pattern-First, Two-Signal): "Signal 1: Director Identity — who made this?" Director identity should resolve to one tier. Dual-listed directors produce contradictory identity signals.
- `CLAUDE.md §3 Rule 5` (Constraint Gates): "Map value flow at each stage boundary — what data is produced upstream, what is consumed downstream, what is lost." The data consumed by `score_director()` (DIRECTOR_REGISTRY) incorrectly includes Core directors; fixing the data source is the correct gate.

**Architecture reference:**
- `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md §2` — Signal 1 (Director Identity): "Core directors are NOT included [in DIRECTOR_REGISTRY] — they live in CoreDirectorDatabase." This is the stated contract. The bug violates it — Core directors ARE currently in DIRECTOR_REGISTRY via SATELLITE_ROUTING_RULES director lists.
- `docs/architecture/RECURSIVE_CURATION_MODEL.md §3` — Structural specificity takes priority over director prestige for Satellite routing. This applies when the structural signal correctly identifies the film's movement. It does NOT mean Core director identity should be suppressed by a Satellite director identity match in P2.

**Context — the two-population finding:**

This investigation also confirmed that Population A (73 Core→Satellite films via structural_signal P5) is **designed behaviour** from Issue #25, not a bug. For these films:
- The structural coordinates genuinely match a Satellite category (Kieslowski → Indie Cinema, Billy Wilder → Classic Hollywood, etc.)
- P5 correctly routes to Satellite in the two-signal layer
- SORTING_DATABASE pins keep them in Core when the curator has decided so
- These 73 SORTING_DATABASE entries are **necessary, not redundant** — they represent curatorial decisions that override structural evidence

This finding clarifies the bypass audit AGREE rate (31.4%): the ceiling is not 100%, because Population A and Population B films are legitimately ambiguous at the two-signal layer and require curatorial resolution via SORTING_DATABASE. The theoretically achievable AGREE rate after fixing Population B is approximately `(122 + 0) / 389 = 31.4%` — because Population A films still DISAGREE for good reason after this fix. Higher AGREE rates require a different architectural approach to the Core-in-Satellite problem.

**Related issues:**
- #25 — Core-in-Satellite resolution (SORTING_DATABASE pins as the designed fix; Population A is this issue's designed outcome)
- #42 — Two-signal architecture (created the P2-before-Core ordering)
- #44 — Director data expansion (added directors to Satellite lists without checking Core whitelist for duplicates)
- #45 — Movement structural signal (implemented; bypass audit data collected in this session)
- #46 — Two-signal contract realignment (broader scope; this issue is a targeted sub-fix)

---
