# Investigation: Director Signal Coverage Post-Issue #42

**Type:** Category 0 — Implementation Problem (§0.1 Work Router)
**Date:** 2026-03-05
**Status:** Complete — spec written as Issue #44
**Supersedes:** `INVESTIGATION_DIRECTOR_FIRST_ROUTING.md` (pre-#42 baseline)
**Leads to:** `ISSUE_044_DIRECTOR_DATA_EXPANSION.md`

---

## §1 Problem Statement

Issue #42 (Unified Two-Signal Architecture) implemented the correct routing logic:
`score_director()` and `score_structure()` run independently and `integrate_signals()` combines
them with a named reason code. The architecture is correct. The routing logic is correct.

The director signal is still not contributing meaningfully to classification.

After #42, across 1,161 films:
- `structural_signal`: 212 classifications (27% of all classified)
- `director_signal`: 40 classifications (5.1%)
- `both_agree`: 22 (2.8%)
- `director_disambiguates`: 12 (1.5%)

**Director-led signals account for 9.5% of all classifications. Structural accounts for 27%.**
The two-signal architecture is working as designed — but one signal is nearly silent.

---

## §2 Work Router §0.1 Classification

**Category: IMPLEMENTATION PROBLEM (data sub-type)**

The theory is correct (director identity should be primary — confirmed in
`INVESTIGATION_DIRECTOR_FIRST_ROUTING.md §3`).
The architecture is correct (Issue #42 implemented the two-signal integration).
The code is correct (score_director, score_structure, integrate_signals all function).

The director lists in `lib/constants.py → SATELLITE_ROUTING_RULES` are not dense enough
to produce reliable signals. This is a data completeness gap, not a logic error.

**Diagnostic signal:** "Works for some films, fails for others" — director_signal fires
for French New Wave and American New Hollywood (movement categories with adequate lists)
but is nearly absent for tradition categories (Giallo, Blaxploitation, AmExploitation, etc.).

---

## §3 Evidence

### 3.1 Signal distribution (full library, n=785 classified, 2026-03-05)

| Reason code | Count | % of classified |
|---|---|---|
| `explicit_lookup` | 389 | 49.6% |
| `structural_signal` | 212 | 27.0% |
| `review_flagged` | 68 | 8.7% |
| `director_signal` | 40 | 5.1% |
| `both_agree` | 22 | 2.8% |
| `popcorn_auto` + variants | 36 | 4.6% |
| `director_disambiguates` | 12 | 1.5% |
| `reference_canon` | 10 | 1.3% |
| `user_tag_recovery` | 14 | 1.8% |

**Director-led classifications (director_signal + both_agree + director_disambiguates): 74 (9.4%)**

### 3.2 Lookup coverage audit — signal bypass test

`scripts/audit_lookup_coverage.py` re-classified all 389 `explicit_lookup` films using
only the signals layer (bypassing SORTING_DATABASE and corpus). Results:

| Verdict | Count | % | Meaning |
|---|---|---|---|
| AGREE | 123 | 31.6% | Signal matches manual destination — pin potentially retirable |
| DISAGREE | 171 | 44.0% | Signal routes to different destination — pin still needed |
| UNSORTED | 95 | 24.4% | Signal cannot classify at all — pin essential |

### 3.3 DISAGREE breakdown by signal reason

| Signal reason | Count | Interpretation |
|---|---|---|
| `structural_signal` | 104 | Structural fires alone; director silent |
| `director_disambiguates` | 23 | Director fired but routed to wrong destination |
| `review_flagged` | 23 | Multiple structural matches, no director to disambiguate |
| `director_signal` | 13 | Director fired but disagrees with curator decision |
| `both_agree` | 4 | Both agree but wrong destination |
| `popcorn_cast_popularity` | 3 | Popcorn signal |
| `reference_canon` | 1 | Reference canon mis-match |

**104/171 DISAGREE cases are pure structural dominance** — the director signal was silent and
structural fired alone into a wrong destination.

### 3.4 Core films mis-routed in bypass test

When explicit_lookup is bypassed, 93 films with explicit Core destinations are routed by
signals to Satellite categories:

| Signal destination | Count |
|---|---|
| Satellite/Indie Cinema/* | 35 (various decades) |
| Satellite/French New Wave/1960s | 8 |
| Satellite/Hong Kong Action/1990s | 6 |
| Satellite/Giallo/1960s-1980s | 11 |
| Satellite/European Sexploitation/* | 9 |
| Satellite/American New Hollywood/* | 5 |
| Satellite/Classic Hollywood/* | 6 |
| Other Satellite | 13 |

**These are Core auteur films (Godard, Wong Kar-wai, Scorsese, etc.) that the structural signal
is pulling into Satellite because their films share structural features with those movements —
which is historically accurate but curated as Core by design.**

Note: This is the expected behaviour per Issue #25 / Rule 2 priority ordering when explicit_lookup
is absent. The 93 films are NOT misclassifications — they expose that Core routing depends
almost entirely on explicit_lookup (115/138 Core films = 83% via lookup), with director_signal
catching only 22/138 (16%). This is a secondary finding addressed in §5.

### 3.5 Current director list sizes vs. target (post-#40 expansion)

| Category | Current directors | Est. needed | Gap | Notes |
|---|---|---|---|---|
| Giallo | 13 | 20–25 | ~40% | Expanded in #40; still missing Dallamano, Crispino, Di Leo |
| Blaxploitation | 10 | 15–18 | ~40% | Missing Van Peebles, Parks Jr., Bill Gunn |
| American Exploitation | 10 | 15–20 | ~40% | Missing Corman, Wishman, Findlay |
| Brazilian Exploitation | 8 | 12–15 | ~40% | Partially populated; missing Mauro, Mansur |
| Classic Hollywood | 8 | 15–20 | ~50% | Missing Hawks, Ford, Curtiz, Capra, Kazan, Huston |
| Pinku Eiga | 5 | 12–15 | ~60% | Severely sparse; missing Noboru Tanaka, Chusei Sone |
| Hong Kong Action | 11 | 18–22 | ~45% | Missing King Hu, Chang Cheh, Sammo Hung |
| European Sexploitation | 8 | 14–18 | ~45% | Missing Joe D'Amato, Jess Franco |
| Japanese Exploitation | 1 | 8–10 | ~90% | Critically sparse — 1 director |
| Hong Kong Category III | 0 | 8–10 | 100% | No directors at all |
| Music Films | 0 | 6–8 | 100% | No directors at all |

**Total gap: ~100–130 directors missing across Satellite categories.**

### 3.6 Per-category lookup coverage breakdown

From `output/lookup_coverage.csv`, filtering to AGREE verdicts (signals would route
correctly without the manual pin):

| Category | AGREE | Total | Auto-coverage |
|---|---|---|---|
| Satellite/Brazilian Exploitation | 18 | 26 | 69% — best coverage |
| Satellite/HK Action | 9 | 10 | 90% — nearly autonomous |
| Satellite/Music Films | 10 | 10 | 100% — fully autonomous |
| Satellite/American New Hollywood | 6 | 6 | 100% — fully autonomous |
| Satellite/French New Wave | 3 | 3 | 100% — fully autonomous |
| Core/Jean-Luc Godard | 0 | 13 | 0% — all via lookup |
| Core/Wong Kar-wai | 0 | 11 | 0% — all via lookup |
| Core/Billy Wilder | 0 | 6 | 0% — all via lookup |
| Core/Giallo (various directors) | 4 | 5 | 80% — Giallo structural works |
| Satellite/Japanese Exploitation | 2 | 4 | 50% — sparse |

**Categories with movement routing (FNW, AmNH, HK Action, Music Films) are already
autonomous or near-autonomous. Tradition categories (Giallo, Blaxploitation, AmExploit,
Pinku Eiga) are heavily lookup-dependent.**

---

## §4 Root Cause Analysis

### RC-1: Director lists are too sparse for signal reliability (confirmed, persists post-#40)

Issue #40 RC-1 identified this as the binding constraint. Data confirms it persists:
- Japanese Exploitation: 1 director (vs. 8–10 needed)
- HK Category III: 0 directors
- Music Films: 0 directors
- Pinku Eiga: 5 directors (vs. 12–15 needed)
- All tradition categories are 40–90% below target density

This is a DATA problem, not a code problem. The two-signal architecture (Issue #42) is
correct. It needs richer data to produce meaningful director signals.

### RC-2 (secondary hypothesis): Core director detection not firing reliably

93 Core films route to Satellite via structural_signal when explicit_lookup is bypassed.
If `score_director()` were finding these Core directors, `integrate_signals()` would apply
Priority #6 (Core director → director_signal) or Priority #5 (Core + structure → both_agree).
The fact that `structural_signal` fires instead suggests `score_director()` is either:
(a) not finding the Core director (name normalisation mismatch between CSV director field
    and `CoreDirectorDatabase` whitelist entries), OR
(b) finding it, but `integrate_signals()` Priority #5/#6 is not handling this case

**This is a hypothesis only.** The audit script uses CSV director names (from filename
parser / OMDb) to call `score_director()` — if these names don't match the whitelist
format, Core director detection silently fails. Requires a targeted probe before speccing.

---

## §5 Secondary Finding: Core routing depends 83% on explicit_lookup

| Route | Core films | % |
|---|---|---|
| `explicit_lookup` | 115 | 83% |
| `director_signal` | 22 | 16% |
| `user_tag_recovery` | 1 | 1% |

Core auteur routing works today because of the 486-entry SORTING_DATABASE. If those
entries were removed, 83% of Core films would route to Satellite (which, per Issue #25,
is the correct fallback for Core directors who also match a Satellite tradition).

This is not a bug — it is the correct pipeline behaviour. But it means the director signal
for Core is doing only 16% of the work it could theoretically do. Expanding director
data for Satellite categories (Issue #44) does not address Core routing.

**A separate investigation should probe RC-2 to determine whether Core director detection
has a name-normalisation bug before speccing a fix.**

---

## §6 What Changed vs. Pre-#42 Baseline

| Metric | Pre-#42 | Post-#42 | Change |
|---|---|---|---|
| Director-led reason codes | `core_director` (opaque) | `director_signal`, `both_agree`, `director_disambiguates` | Named, measurable |
| Structural reason codes | `tmdb_satellite`, `country_satellite` | `structural_signal`, `review_flagged` | Named, measurable |
| Director-led classifications | Unmeasurable (bundled in `tmdb_satellite`) | 74 (9.4%) | Now visible |
| Structural-only classifications | Unmeasurable | 212 (27%) | Now visible |
| Signal ratio director:structural | Unknown | 1:2.9 | **Director signal needs 2–3× expansion** |

**Issue #42's primary contribution: made the signal imbalance measurable.**
The director signal fired before #42 — it was just invisible. Now we can see it's
outratio'd 1:2.9 and set a concrete target for improvement.

---

## §7 Conclusion and Recommended Next Steps

**Priority 1 — Issue #44 (Director Data Expansion):**
Expand tradition category director lists to target density. Data-only change in
`lib/constants.py`. No code changes. Scholarship-sourced per `SATELLITE_CATEGORIES.md`.
Expected outcome: director_signal count rises from 40 → 100+; structural_signal falls
as more films confirm via director identity.

**Priority 2 — RC-2 probe (separate investigation, before speccing):**
Test whether `score_director()` finds Core director names from the manifest correctly.
Run: `python3 -c "from lib.signals import score_director; from lib.core_directors import
CoreDirectorDatabase; db=CoreDirectorDatabase(...); print(score_director('Jean-Luc Godard',
1962, db))"` and check if Core match is returned. If not, trace to normalisation mismatch
in `lib/core_directors.py is_core_director()`.

**Priority 3 — Lookup retirement (after Issue #44 is stable):**
Use `output/lookup_coverage.csv` AGREE list to identify explicit_lookup pins that are now
redundant. Retire them from SORTING_DATABASE in batches, running reaudit after each batch
to confirm no regressions.
