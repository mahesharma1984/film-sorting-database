# Issue #40: Two-Signal Satellite Routing

**Type:** Feature / Refactor — Satellite routing architecture
**Severity:** High (structural — Satellite auto-classification at ~10% coverage, 76% of library depends on manual curation)
**Discovered via:** Exploration session 2026-03-03 (triggered by INVESTIGATION_DIRECTOR_FIRST_ROUTING.md pattern recognition)
**Depends on:** Issue #35 (evidence architecture — `evidence_classify()` and `GateResult`/`CategoryEvidence` infrastructure)
**Blocks:** Scalable Satellite auto-classification without per-film manual triage
**Investigation docs:**
- `docs/issues/INVESTIGATION_DIRECTOR_FIRST_ROUTING.md` — precursor: RC-1 (sparse lists) and RC-2 (gate ordering)
- `docs/issues/INVESTIGATION_TWO_SIGNAL_ARCHITECTURE.md` — this session: structural precision map, signal reachability, integration model
**Issue spec:** `docs/issues/ISSUE_040_TWO_SIGNAL_SATELLITE_ROUTING.md`

---

## Problem

Satellite classification entangles two independent signals — director identity (relational) and country+decade+genre (structural) — in a sequential gate chain. The decade gate fires before the director check, making director lists functionally decorative for tradition categories. 76% of the organized Satellite library is unreachable by either signal and depends entirely on SORTING_DATABASE entries.

## Root Causes

1. **RC-1: Director lists too sparse.** ~87 directors across all categories vs ~200+ needed. Brazilian Exploitation has 0. Blaxploitation has 4. Even with correct routing logic, most canonical directors' films fall through.

2. **RC-2: Gate ordering inverts theory priority.** `satellite.py` line 117: decade gate fires first, skips entire category including director check. A 1998 Ferrara film never reaches the AmExploit director list.

3. **RC-3: No integration logic.** First match wins. No mechanism to compare evidence from both signals, rank categories, or produce evidence-dependent confidence scores. `evidence_classify()` computes this evidence but it's diagnostic-only.

## Key Findings

- **Structural precision map:** IT+1970s → Giallo (88%), US+1940s → Classic Hollywood (90%), BR+1970s → BrExploit (100%). But US+1970s is 3-way ambiguous (AmExploit/Blaxploitation/AmNH), FR+1960s is 2-way (FNW/EuroSex), HK+1990s is 3-way.

- **Director groups by routing value:**
  - Group A (disambiguators): resolve ambiguous structural zones — ~30-40 directors across US+1970s, HK+1990s, FR+1960s, JP+1970s
  - Group B (confirmers): raise confidence in high-precision zones — Giallo, BrExploit, HK Action directors
  - Group C (rescuers): route out-of-era tradition directors — late Godard, Ferrara, Miike

- **The intersection is multiplicative:** Director signal disambiguates where structure is ambiguous. Structure covers where director lists are sparse. Together they approximate curatorial judgment.

## Implementation

Three phases, each independently valuable:

1. **Phase 1 (data-only):** Expand director lists in `lib/constants.py` (~60 directors). Zero code risk.
2. **Phase 2 (~10 lines):** Reorder gate in `lib/satellite.py` — director before decade for tradition categories. Movement categories unchanged.
3. **Phase 3 (deferred):** Integration function using `evidence_classify()` as engine — evidence-based ranking with confidence scores.

## Measurement Targets

| Metric | Before | Target |
|---|---|---|
| Queue classification rate | 14.6% (59/403) | 18-22% |
| Indie Cinema % of satellite | 52% | <40% |
| Director gate passes | 10 | 50+ |
| Reaudit confirmed | ≥668 | ≥668 (no regression) |
