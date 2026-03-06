# Issue #51: Clean Up Satellite Categories — Remove Catch-Alls, Hone Definitions

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P1-Critical |
| Date Opened | 2026-03-06 |
| Component | lib/constants.py (SATELLITE_ROUTING_RULES) / docs/SORTING_DATABASE.md |
| Change Type | Curatorial — Category Cleanup |
| Estimated Effort | 1–2 days |
| Blocked By | None |
| Blocks | Issue #52 (new category development) |
| Supersedes | None |
| Investigation | docs/issues/INVESTIGATION_051_CATEGORY_REDESIGN.md |

---

## 1. Manager Summary

**Problem:** Three of 18 Satellite categories are not real film movements — they are catch-alls. Indie Cinema is defined by exclusion across 30 countries and 6 decades. Music Films has a single genre gate and no country, decade, or director constraints. Cult Oddities has no routing rules at all. The two-signal system routes films to these categories with the same confidence it uses for Giallo or French New Wave, but the categories have no coherent structural definition to match against. The result is false confidence: films land in catch-alls because nothing better matched, not because something positive fired.

The two-signal system works. Giallo, French New Wave, HK Action, Brazilian Exploitation — these are named historical movements with clear structural profiles (country + decade + genre + directors from published scholarship). The routing machinery produces correct results for them. The problem is not the machinery. The problem is that three of the categories it routes into are not real categories.

**Impact if unfixed:** The accuracy baseline is inflated by ~100+ films auto-classified into catch-alls. New category development (Issue #52) cannot begin because Indie Cinema absorbs the films that should populate new categories. The system reports ~275 auto-classifications when the honest number is ~150–180.

**Risk if fixed wrong:** SORTING_DATABASE pins for films currently in Indie Cinema, Music Films, and Cult Oddities must continue to work via `explicit_lookup`. Removing a category from `SATELLITE_ROUTING_RULES` must not break explicit_lookup routing for films pinned to that destination.

**Estimated effort:** 1–2 days. The changes are deletions and SORTING_DATABASE corrections. No new machinery.

---

## 2. Evidence

### The investigation (INVESTIGATION_051) found:

**Indie Cinema is three populations mixed together (§7):**
1. Genuine international arthouse (Assayas, Moretti, Peter Weir, Laloux)
2. Films that belong elsewhere but have no rule (Braindead → horror/exploitation, Akira → animation)
3. Misplacements from the Core-adjacent zone (Wyler is in Core whitelist; Polanski is Core-adjacent)

A category that contains The Cook The Thief His Wife and Her Lover, Akira, Braindead, Fantastic Planet, and House Party is not a category. It is a bin.

**Music Films has no structural definition (§7):** Single genre gate (Music/Musical/Documentary), no country, no decade, no director list. The Smashing Machine (2002, MMA documentary), 200 Motels (1971, Zappa concert film), and Streets of Fire (1984, rock musical action) all route to the same category. These films share nothing except a TMDb genre tag.

**Cult Oddities already has no auto-routing.** It is reached only via SORTING_DATABASE pins (4 films: Plan 9, Skidoo, Head, Putney Swope). This issue formalises what is already true.

**The Kubrick structural simulation (§4):** Every Kubrick film from 1960–1999 matched 2–4 categories simultaneously on structural signal alone. 2001: A Space Odyssey (GB, 1968, Sci-Fi) → Indie Cinema via structural gates. The Shining (GB, 1980, Horror) → Indie Cinema. Structural gates define a territory (country + era + broad genre), not a movement. This is acceptable for Tier 1 categories where director lists disambiguate. It is not acceptable for Indie Cinema where the "territory" is 30 countries across 6 decades.

**`director_disambiguates` is a coin flip (§3):** 52.9% accuracy (27/51). When director and structure point to different categories, the system routes to the director's category. This is wrong nearly half the time. Two signals in conflict is ambiguity, not a case for director override. Secondary fix — addressed in this issue because removing catch-all categories changes the conflict population.

### Manifest data (1,215 films in Unsorted work queue):

| Reason code | Count | Notes |
|---|---|---|
| `explicit_lookup` | 389 | Human-curated — unaffected by this change |
| `structural_signal` | 212 | Many are Indie Cinema catch-all matches |
| `unsorted_no_year` | 173 | Enrichment gap — unaffected |
| `unsorted_insufficient_data` | 106 | Enrichment gap — unaffected |
| `unsorted_no_match` | 97 | Will grow as catch-all removals redirect films here |
| `review_flagged` | 67 | Will grow |
| `director_disambiguates` | 51 | 52.9% accuracy — replaced with `review_flagged` |
| `director_signal` | 40 | Unaffected (Tier 1/2 directors) |
| `both_agree` | 23 | 4 are Indie Cinema — those 4 will become unsorted |
| `user_tag_recovery` | 14 | Unaffected |

---

## 3. Root Cause Analysis

### RC-1: Three categories in SATELLITE_ROUTING_RULES are not named film movements

**Location:** `lib/constants.py` → `SATELLITE_ROUTING_RULES` entries for Indie Cinema, Music Films, Cult Oddities

**Mechanism:** Every other Satellite category corresponds to a documented film-historical movement with published scholarship: Giallo (Koven 2006, Lucas 2007), French New Wave, Brazilian pornochanchada, Hong Kong martial arts cinema, etc. These three do not. Indie Cinema is "everything arthouse that isn't exploitation." Music Films is "anything with a Music/Musical/Documentary genre tag." Cult Oddities has no routing rules at all. They exist as catch-all destinations, not as movement definitions.

**Why this matters:** The two-signal architecture (Issue #42) assumes each category represents a coherent structural profile: if country + decade + genre + director converge on a single category, that convergence is meaningful. For catch-alls, convergence is meaningless — Indie Cinema's 30 country codes and 4 genre tags will match any arthouse film from any era. The signal fires, but it signals nothing.

### RC-2: Indie Cinema absorbs films that should populate future well-defined categories

**Location:** `lib/constants.py` → Indie Cinema entry: 30+ country codes, 1960s–2020s, Drama/Romance/Thriller/Sci-Fi genres

**Mechanism:** Films that don't match any exploitation/movement category fall to Indie Cinema because its gates are so broad. A Romanian New Wave film, a German New Cinema film, an Italian art-cinema film — none of these have their own category yet, so they all land in Indie Cinema. This prevents the evidence accumulation that would justify creating those categories (Issue #52). You can't discover that you have 15 Romanian New Wave films if they're all hidden inside a 40-film Indie Cinema bin.

### RC-3: `director_disambiguates` treats signal conflict as director victory

**Location:** `lib/signals.py` → `integrate_signals()`, P3 priority rule

**Mechanism:** When director matches Category A and structure matches Category B (different category), P3 routes to Category A at 0.75 confidence. 52.9% accuracy. Removing catch-all categories will change this population (many current conflicts involve Indie Cinema as one side), but the rule itself is architecturally wrong: conflicting signals should produce `review_flagged`, not a forced choice.

---

## 4. Affected Handoffs

| Boundary | What changes |
|---|---|
| `SATELLITE_ROUTING_RULES` → `score_structure()` | 3 fewer categories to match against. Structural matches for Indie Cinema / Music Films no longer produced. |
| `SATELLITE_ROUTING_RULES` → `score_director()` via `DIRECTOR_REGISTRY` | 8 Indie Cinema directors removed from registry. No Music Films or Cult Oddities directors exist. |
| `score_structure()` → `integrate_signals()` | Fewer structural match objects. Films that previously matched Indie Cinema now either match a remaining Tier 1/2 category or produce no match. |
| `integrate_signals()` → manifest | Films that matched only catch-alls → `unsorted_no_match`. Films that matched catch-all + real category → now match only real category (cleaner signal). |
| Manifest → `review_queue.csv` | Review queue grows. More `unsorted_no_match` films with R2/R3 data readiness enter the queue as `enriched_unsorted`. |
| SORTING_DATABASE → `explicit_lookup` | **UNAFFECTED.** Explicit lookup fires before signals (Stage 2). SORTING_DATABASE pins to `Satellite/Indie Cinema/`, `Satellite/Music Films/`, `Satellite/Cult Oddities/` continue to work. The destination paths are strings — they do not require a matching entry in `SATELLITE_ROUTING_RULES`. |
| `integrate_signals()` P3 → reason codes | `director_disambiguates` reason code eliminated. Replaced by `review_flagged`. |

**Critical gate:** Verify that `explicit_lookup` for Indie Cinema/Music Films/Cult Oddities destinations still works after removing routing rules. Test with a known SORTING_DATABASE pin (e.g., Akira → Satellite/Indie Cinema/1980s/).

---

## 5. Proposed Fix

### Fix Description

Remove the three catch-all categories from auto-routing. Fix known bad SORTING_DATABASE pins. Replace `director_disambiguates` with `review_flagged` for signal conflicts. The two-signal system keeps routing to the 15 remaining well-defined categories. Everything else goes to the review queue.

### Execution Order

**Step 1: Pin the baseline**
```bash
git tag pre-issue-051
python scripts/reaudit.py > output/pre-051-reaudit.txt
cp output/accuracy_baseline.json output/accuracy_baseline_pre051.json
```

**Step 2: Remove Indie Cinema from `SATELLITE_ROUTING_RULES`**
- Delete the `'Indie Cinema'` entry from `SATELLITE_ROUTING_RULES` in `lib/constants.py`
- This removes: 30+ country codes, 1960s–2020s decades, Drama/Romance/Thriller/Sci-Fi genres, 8 directors (assayas, denis, laloux, weir, moretti, etc.)
- **Verify:** `python3 -c "from lib.constants import SATELLITE_ROUTING_RULES; assert 'Indie Cinema' not in SATELLITE_ROUTING_RULES; print('Removed')"`

**Step 3: Remove Music Films from `SATELLITE_ROUTING_RULES`**
- Delete the `'Music Films'` entry from `SATELLITE_ROUTING_RULES` in `lib/constants.py`
- This removes: any-country, any-decade, Music/Musical/Documentary genres, 0 directors
- **Verify:** `python3 -c "from lib.constants import SATELLITE_ROUTING_RULES; assert 'Music Films' not in SATELLITE_ROUTING_RULES; print('Removed')"`

**Step 4: Remove Cult Oddities from `SATELLITE_ROUTING_RULES`**
- Delete the `'Cult Oddities'` entry from `SATELLITE_ROUTING_RULES` in `lib/constants.py`
- This removes: no routing rules (already empty) — formalises what was already true
- **Verify:** `python3 -c "from lib.constants import SATELLITE_ROUTING_RULES; assert 'Cult Oddities' not in SATELLITE_ROUTING_RULES; print('Removed')"`

**Step 5: Fix known bad SORTING_DATABASE pins**

These were identified in INVESTIGATION_051 §7. Fix before regenerating the baseline.

| Film | Current Pin | Problem | Fix |
|---|---|---|---|
| Orpheus (1950, Cocteau) | Classic Hollywood | Cocteau is French, not Hollywood | → Review (determine correct category) |
| A Man and a Woman (1966, Lelouch) | Indie Cinema | Should be French New Wave | → Satellite/French New Wave/1960s/ |
| The Collector (1965, Wyler) | Indie Cinema | Wyler is in Core whitelist | → Core/1960s/William Wyler/ |
| The Oily Maniac (1976, Ho) | American Exploitation | Shaw Brothers HK production | → Satellite/Hong Kong Action/1970s/ |
| Braindead (1992, Jackson) | Indie Cinema | Horror/splatter, not arthouse | → Review (no matching category yet) |
| The Fearless Vampire Killers (1967, Polanski) | Indie Cinema | Polanski is Core-adjacent | → Review (determine Core or Satellite) |

For films marked "Review": remove the SORTING_DATABASE pin. They will appear in `unsorted_no_match` and enter the review queue naturally. Better to be honestly unsorted than falsely classified.

**Step 6: Replace `director_disambiguates` with `review_flagged`**
- In `lib/signals.py` → `integrate_signals()`, P3 priority rule
- When director matches Category A and structure matches Category B (conflict): return `review_flagged` at 0.4 instead of routing to director's category at 0.75
- Remove the `director_disambiguates` reason code
- **Verify:** `pytest tests/test_signals.py -v`

**Step 7: Update tests**
- Remove or update any tests that assert Indie Cinema / Music Films / Cult Oddities routing via structural or director signals
- Add test: film that previously matched Indie Cinema structurally now gets `unsorted_no_match`
- Add test: SORTING_DATABASE pin to `Satellite/Indie Cinema/1980s/` still works via `explicit_lookup`
- Add test: signal conflict → `review_flagged` (not `director_disambiguates`)
- Add test: Giallo `both_agree` still works (regression gate)
- **Verify:** `pytest tests/ -v` — all pass

**Step 8: Update documentation**
- `CLAUDE.md` §4: note that Indie Cinema, Music Films, Cult Oddities are removed from auto-routing; films reach these destinations only via SORTING_DATABASE pins
- `docs/SATELLITE_CATEGORIES.md`: mark these three categories as "SORTING_DATABASE only — no auto-routing"
- `CLAUDE.md` Rule 11: update to reflect the principle — Satellite categories must be named historical movements with published scholarship; catch-alls are not categories

**Step 9: Regenerate and measure**
```bash
python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted
python audit.py
python scripts/reaudit.py > output/post-051-reaudit.txt
diff output/pre-051-reaudit.txt output/post-051-reaudit.txt
```

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `lib/constants.py` | Delete | Remove 3 entries from `SATELLITE_ROUTING_RULES` (Indie Cinema, Music Films, Cult Oddities) |
| `lib/signals.py` | Modify | P3 (`director_disambiguates`) → `review_flagged` for signal conflicts |
| `docs/SORTING_DATABASE.md` | Modify | Fix 4–6 known bad pins (Cocteau, Lelouch, Wyler, Ho, etc.) |
| `tests/test_signals.py` | Modify | Update tests for removed categories; add conflict → review_flagged tests |
| `CLAUDE.md` | Modify | §4 project rules + Rule 11 updates |
| `docs/SATELLITE_CATEGORIES.md` | Modify | Mark 3 categories as SORTING_DATABASE-only |

---

## 6. Scope Boundaries

**In scope:**
- Remove Indie Cinema, Music Films, Cult Oddities from `SATELLITE_ROUTING_RULES`
- Fix known bad SORTING_DATABASE pins (6 films)
- Replace `director_disambiguates` with `review_flagged` for signal conflicts
- Update docs to reflect what Satellite means: named historical movements only

**NOT in scope:**
- Adding new categories (German New Cinema, Italian Art Cinema, etc.) — Issue #52
- Adding a `certainty_tier` field to `SATELLITE_ROUTING_RULES` — not needed; the vague categories are removed, not suppressed
- Modifying `integrate_signals()` P2 or P7 logic — those priority rules are correct for well-defined categories
- Building corpora for removed categories — separate issue if/when those categories are redefined
- Reference canon migration — Issue #50
- Changing Tier 1/2 routing logic — untouched

**Why not `certainty_tier`?** The old spec proposed adding a `certainty_tier` integer field to every category and checking it at each decision point in `integrate_signals()`. This adds complexity to suppress categories that shouldn't exist in the routing rules at all. If a category cannot be structurally defined well enough to auto-classify, it should not be in `SATELLITE_ROUTING_RULES`. Removing it is simpler, more honest, and easier to reverse than adding a field that says "this category exists but please ignore it."

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Categories in SATELLITE_ROUTING_RULES | 18 | 15 | Count entries |
| Films auto-classified (non-lookup) | ~275 | ~150–180 | Manifest reason code counts |
| `structural_signal` films in Indie Cinema | ~80–100 | 0 | Manifest filter by destination |
| `both_agree` films in Indie Cinema | 4 | 0 | Manifest filter |
| `director_disambiguates` films | 51 | 0 | Reason code removed |
| `unsorted_no_match` count | 97 | ~150–200 (grows) | Manifest reason count |
| `review_flagged` count | 67 | ~100–130 (grows) | Manifest reason count |
| Review queue size | ~67 | ~200+ | `review_queue.csv` row count |
| Tier 1 `both_agree` accuracy | 73.8% (contaminated) | ≥75% (clean) | `accuracy_baseline.json` |
| SORTING_DATABASE pins to Indie Cinema | 37 | 37 (unchanged) | grep count — these still work |
| SORTING_DATABASE pins to Music Films | 12 | 12 (unchanged) | grep count — these still work |

**Expected direction:** The system routes fewer films, but routes them honestly. The review queue absorbs the difference. The aggregate classification rate drops but the per-category accuracy rises. This is the clean baseline from which Issue #52 (new category development) can work.

**What "hone" means going forward:** After this change, the 15 remaining categories have clean populations. Future work (not this issue) can:
1. Run the API cache against confirmed films per category → derive empirical structural profiles
2. Compare empirical profiles against current gates → tighten where they diverge
3. Use the review queue to discover films that cluster into potential new categories

---

## 8. Validation Sequence

```bash
# Step 1: Full test suite before changes
pytest tests/ -v
# Expected: 372+ passing, 0 new failures

# Step 2: After removing categories — verify they're gone
python3 -c "
from lib.constants import SATELLITE_ROUTING_RULES
removed = ['Indie Cinema', 'Music Films', 'Cult Oddities']
for cat in removed:
    assert cat not in SATELLITE_ROUTING_RULES, f'{cat} still in SATELLITE_ROUTING_RULES'
print(f'Categories remaining: {len(SATELLITE_ROUTING_RULES)}')
print('Removed categories confirmed gone')
"
# Expected: Categories remaining: 15

# Step 3: Verify SORTING_DATABASE pins still work via explicit_lookup
python3 -c "
from lib.lookup import LookupDatabase
db = LookupDatabase('docs/SORTING_DATABASE.md')
result = db.lookup('Akira', '1988')
print(f'Akira (1988) → {result}')
assert result is not None, 'Akira SORTING_DATABASE pin broken!'
assert 'Indie Cinema' in result, f'Expected Indie Cinema, got {result}'
print('PASS: explicit_lookup still works for removed category destinations')
"
# Expected: Akira routes to Satellite/Indie Cinema/1980s/ via explicit_lookup

# Step 4: Verify Giallo still auto-classifies (regression gate)
python3 -c "
from lib.signals import integrate_signals, DirectorMatch, StructuralMatch
dm = [DirectorMatch(tier='Satellite', category='Giallo', canonical_name=None, source='satellite_rules', decade_valid=True)]
sm = [StructuralMatch(tier='Satellite', category='Giallo', match_type='country_genre')]
result = integrate_signals(dm, sm, '1970s', 'R3')
print(f'Giallo both_agree: reason={result.reason}, confidence={result.confidence}')
assert result.reason == 'both_agree', f'REGRESSION: Giallo got {result.reason}'
print('PASS')
"
# Expected: both_agree, 0.85

# Step 5: Verify signal conflict → review_flagged (not director_disambiguates)
python3 -c "
from lib.signals import integrate_signals, DirectorMatch, StructuralMatch
dm = [DirectorMatch(tier='Satellite', category='Giallo', canonical_name=None, source='satellite_rules', decade_valid=True)]
sm = [StructuralMatch(tier='Satellite', category='Brazilian Exploitation', match_type='country_genre')]
result = integrate_signals(dm, sm, '1970s', 'R3')
print(f'Conflict: reason={result.reason}')
assert result.reason == 'review_flagged', f'Expected review_flagged, got {result.reason}'
print('PASS: signal conflict produces review_flagged')
"

# Step 6: Full test suite after changes
pytest tests/ -v
# Expected: all pass (some tests updated for removed categories)

# Step 7: Classify and check manifest
python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted
python3 -c "
import csv
from collections import Counter
with open('output/sorting_manifest.csv') as f:
    rows = list(csv.DictReader(f))
reasons = Counter(r['reason'] for r in rows)
print('Reason distribution:')
for reason, count in reasons.most_common():
    print(f'  {reason}: {count}')
# Key checks
assert reasons.get('director_disambiguates', 0) == 0, 'director_disambiguates should be gone'
indie_structural = sum(1 for r in rows if 'Indie Cinema' in r.get('destination','') and r['reason'] == 'structural_signal')
assert indie_structural == 0, f'{indie_structural} films still structural_signal to Indie Cinema'
print('PASS: no auto-routing to removed categories')
"

# Step 8: Reaudit regression check
python audit.py && python scripts/reaudit.py > output/post-051-reaudit.txt
diff output/pre-051-reaudit.txt output/post-051-reaudit.txt
# Expected: Tier 1/2 confirmed count STABLE
# Expected: Indie Cinema/Music Films confirmed count drops (those were false confirmations)
# Expected: No new wrong_tier for Giallo, HK Action, Brazilian Exploitation, etc.
```

**If Tier 1 regression detected:** Stop. `git revert`. The three-category removal is isolated — reverting restores them to `SATELLITE_ROUTING_RULES` and all routing returns to prior state.

---

## 9. Rollback Plan

**Detection:** Tier 1 confirmed count (Giallo, HK Action, Brazilian Exploitation, Pinku Eiga, etc.) drops in reaudit compared to pre-051 baseline. Any film that was correctly classified to a Tier 1 category now routes elsewhere.

**Recovery:**
```bash
git revert [commit-hash]
# Restores the 3 category entries in SATELLITE_ROUTING_RULES
# Restores director_disambiguates in integrate_signals()
# No cache invalidation needed — routing logic only
cp output/accuracy_baseline_pre051.json output/accuracy_baseline.json
```

**Why rollback is safe:** The change is purely subtractive. No new machinery was added. No existing fields were modified. Reverting re-adds the deleted entries and restores the old P3 rule. The SORTING_DATABASE pin fixes (Step 5) can be kept or reverted independently.

---

## 10. Theory & Architecture Grounding

**Core principle:** Satellite categories are named historical film movements grounded in published scholarship (CLAUDE.md Rule 4, Domain Grounding). A category that does not correspond to a documented movement does not belong in `SATELLITE_ROUTING_RULES`.

**Positive-space vs negative-space** (`docs/theory/MARGINS_AND_TEXTURE.md` §8): Well-defined categories are positive-space — they describe something specific (Italian horror-thrillers of the 1960s–1980s). Indie Cinema and Music Films are negative-space — defined by what they are not. The two-signal system produces meaningful results for positive-space categories and noise for negative-space categories. Removing negative-space categories from auto-routing is the structural fix.

**Anchor-then-expand** (`exports/skills/certainty-first.md`): Establish anchors (SORTING_DATABASE pins, corpora, Tier 1 routing). Expand outward with decreasing certainty but increasing gates. Indie Cinema was attempting to be an anchor (auto-routing at 0.85 confidence) when it should have been expansion territory (review queue with suggestions). After this issue, the 15 remaining categories are the anchors. The review queue is the expansion frontier.

**What "hone" means** (Rule 7, Measurement-Driven): With catch-alls removed, the remaining 15 categories have clean populations. Their accuracy can be measured honestly. Where structural gates are too broad (the Kubrick simulation showed Italian territory is wider than Giallo movement), those gates can be tightened with evidence — but only after the baseline is clean.

**Related issues:**
- Issue #42 — Built the two-signal system. This issue cleans up the categories it routes into.
- Issue #49 — Dashboard revealed the accuracy contamination.
- Issue #50 — Core/Reference bypass. Separate scope.
- Issue #52 (planned) — New category development. Requires a clean baseline — this issue provides it.

---

### Section Checklist

- [x] §1 Manager Summary: no code jargon, states what and why
- [x] §2 Evidence: investigation findings cited with section numbers
- [x] §3 Root causes: the categories are wrong, not the integration function
- [x] §4 Handoffs: explicit_lookup unaffected (critical gate)
- [x] §5 Execution order: deletions and corrections, not new machinery
- [x] §6 NOT in scope: certainty_tier field explicitly excluded with rationale
- [x] §7 Measurement: honest numbers — classification rate drops, accuracy rises
- [x] §8 Validation: copy-pasteable, regression gate on Tier 1
- [x] §9 Rollback: simple revert, purely subtractive change
- [x] §10 Theory: grounded in Domain Grounding, positive/negative-space, anchor-then-expand
