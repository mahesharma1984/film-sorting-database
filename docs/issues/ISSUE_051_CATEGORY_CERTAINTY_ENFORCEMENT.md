# Issue #51: Category Certainty Enforcement — Remove Vague Categories from Auto-Routing

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P1-Critical |
| Date Opened | 2026-03-06 |
| Component | lib/signals.py / lib/constants.py / SATELLITE_ROUTING_RULES |
| Change Type | Architecture — Theory Alignment |
| Estimated Effort | 2–3 days |
| Blocked By | None |
| Blocks | Issue #52 (new category development) |
| Supersedes | None |
| Investigation | docs/issues/INVESTIGATION_051_CATEGORY_REDESIGN.md |

---

## 1. Manager Summary

**Problem:** The two-signal classification system applies identical confidence logic to all 16 Satellite categories, regardless of how well-defined those categories are. A category like Giallo — grounded in four independent signals (Italian origin, 1960s–1980s, horror/thriller genre, scholarship-sourced director list) — gets the same treatment as Indie Cinema, which is defined by exclusion ("not exploitation, not Core, not Popcorn") across 30 countries and 6 decades. Both produce `both_agree` at 0.85 confidence. One is correct. One is false confidence.

Additionally, the `director_disambiguates` reason code uses director identity to override conflicting structural evidence — and is wrong 47% of the time (52.9% accuracy, statistically indistinguishable from a coin flip).

**Impact if unfixed:** The accuracy baseline is meaningless because Indie Cinema and Music Films absorb all films that fail to match better categories, inflating classified counts while degrading accuracy. The system cannot be measured honestly. New category development cannot begin until the baseline is clean.

**Risk if fixed wrong:** Confirmed Tier 1 classifications (Giallo, Brazilian Exploitation, HK Action etc.) regress if the certainty tier logic is applied too broadly. The change must be additive — new constraints on Tier 3+ categories only, no changes to Tier 1/2 routing logic.

**Estimated effort:** 2–3 days. `integrate_signals()` change is low-risk and isolated. `SATELLITE_ROUTING_RULES` field addition is mechanical. Reaudit regeneration is the longest step.

---

## 2. Evidence

### Observation

The certainty tier framework is documented in `exports/skills/certainty-first.md` and `docs/architecture/RECURSIVE_CURATION_MODEL.md §5`. It defines which categories should auto-classify and which should produce review-flagged results. This framework was never enforced in `integrate_signals()`.

From the manifest (1,215 films in Unsorted work queue):

| Reason code | Count | Notes |
|---|---|---|
| `explicit_lookup` | 389 | Correct — human-curated |
| `structural_signal` | 212 | 67.4% accuracy — many are Indie Cinema false positives |
| `unsorted_no_year` | 173 | Enrichment gap |
| `unsorted_insufficient_data` | 106 | Enrichment gap |
| `unsorted_no_match` | 97 | Genuine no-match |
| `review_flagged` | 67 | Correct output for ambiguous cases |
| `director_signal` | 40 | 73.0% accuracy |
| `both_agree` | 23 | 73.8% accuracy — but 4 of 23 are Indie Cinema (Tier 3) |
| `user_tag_recovery` | 14 | Prior human placement, ~86% accurate |

### Data

**`director_disambiguates` accuracy: 52.9%** (27/51 confirmed in organised library). This is the P3 rule: director matches Cat-A, structure matches Cat-B → route to Cat-A at 0.75 confidence. With 47% wrong, this rule actively damages routing quality.

**Indie Cinema `both_agree` films (false 0.85 confidence):**
- Irma Vep (1996, Assayas) → Indie Cinema, 0.85
- Demonlover (2002, Assayas) → Indie Cinema, 0.85
- Vers Mathilde (2005, Denis) → Indie Cinema, 0.85
- Nouvelle Vague (2025, Linklater) → Indie Cinema, 0.85

These films have a director in the Indie Cinema director list AND structural coordinates matching Indie Cinema's broad country/decade/genre gates. The machinery fires correctly — but the category should not be auto-classifying at all.

**Current `both_agree` and `structural_signal` films that correctly belong in Tier 1 categories** remain unaffected by this change — the new constraint only applies to Tier 3+ categories.

---

## 3. Root Cause Analysis

### RC-1: `integrate_signals()` has no knowledge of category certainty tier
**Location:** `lib/signals.py` → `integrate_signals()` — P2, P3, P7, P8
**Mechanism:** P7 (`structural_signal`, unique category match) routes any single structural match to the manifest regardless of the matched category's certainty tier. P2 (`both_agree`) fires when director and structure agree regardless of whether the agreed category is Tier 1 or Tier 3. The function receives `DirectorMatch` and `StructuralMatch` objects that carry category names but not certainty tiers. There is no lookup from category name to certainty tier.

### RC-2: `SATELLITE_ROUTING_RULES` has no `certainty_tier` field
**Location:** `lib/constants.py` → `SATELLITE_ROUTING_RULES`
**Mechanism:** Each category entry has `country_codes`, `decades`, `genres`, `directors`, `keyword_signals`. There is no `certainty_tier` field. Without this field, `integrate_signals()` cannot enforce tier constraints even if it wanted to. The tier framework is documented in theory but has no code representation.

### RC-3: P3 (`director_disambiguates`) treats signal conflict as director victory
**Location:** `lib/signals.py` → `integrate_signals()` lines ~307–318
**Mechanism:** When `structural_diff` is True (structure has matches, none matching the director's category), P3 routes to the director's category at 0.75. Two independent signals pointing to different categories is not ambiguity — it is conflict. Routing to director's category against conflicting structural evidence produces 52.9% accuracy.

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| `integrate_signals()` → reason code | `lib/signals.py` | `classify.py:_build_result()` | Yes — new reason codes for Tier 3 downgrade |
| Reason code → manifest | `classify.py` | `output/sorting_manifest.csv` | Yes — `structural_signal` / `both_agree` for Tier 3 → `review_flagged` |
| Manifest → reaudit | `output/sorting_manifest.csv` | `scripts/reaudit.py` | Yes — confirmed count will drop (Tier 3 films no longer auto-classified) |
| Manifest → accuracy baseline | `output/sorting_manifest.csv` | `output/accuracy_baseline.json` | Yes — `structural_signal` and `both_agree` populations shrink; `review_flagged` grows |
| Manifest → dashboard | `output/sorting_manifest.csv` | `dashboard.py` | Yes — classification rate drops; review queue grows |

**Gate impact:** Reaudit confirmed count will drop. Films currently auto-routed to Indie Cinema and Music Films will become `review_flagged` — they will no longer appear as "confirmed" in reaudit. This is expected and correct: those were false confirmations. Pin the pre-051 baseline before implementing.

**Downstream consumers of changed output:**
- `scripts/reaudit.py` — reads `reason` column; `_STAGE_GROUPS` must include `review_flagged` as a tracked group
- `dashboard.py` → `render_signal_accuracy()` — reads `accuracy_baseline.json`; will show lower aggregate accuracy but higher per-category accuracy for Tier 1 categories
- `output/failure_cohorts.json` — generated by `scripts/failure_cohorts.py`; Indie Cinema cohorts will disappear or shrink

---

## 5. Proposed Fix

### Fix Description

Three coordinated changes:
1. Add `certainty_tier` (int, 1–4) to every entry in `SATELLITE_ROUTING_RULES`
2. In `integrate_signals()`, check certainty tier before routing: Tier 3+ structural matches → `review_flagged` regardless of signal agreement
3. Replace P3 (`director_disambiguates`) with conflict → `review_flagged`; add new P3a (`director_confirms`) for the valid case: structural ambiguous AND director confirms one of the ambiguous candidates

### Execution Order

**Step 1:** Add `certainty_tier` to `SATELLITE_ROUTING_RULES` in `lib/constants.py`
- **What to change:** Add `'certainty_tier': N` to each category. Use the framework from `RECURSIVE_CURATION_MODEL.md §5`:
  - Tier 1: Giallo, Brazilian Exploitation, HK Action, Pinku Eiga, American Exploitation, European Sexploitation, Blaxploitation
  - Tier 2: Classic Hollywood, French New Wave, American New Hollywood, Japanese New Wave, HK New Wave, HK Category III, Japanese Exploitation
  - Tier 3: Music Films, Indie Cinema
  - Tier 4: Cult Oddities
- **Verify:** `python3 -c "from lib.constants import SATELLITE_ROUTING_RULES; print({k: v['certainty_tier'] for k,v in SATELLITE_ROUTING_RULES.items()})"`

**Step 2:** Update `DIRECTOR_REGISTRY` builder in `lib/constants.py` to pass `certainty_tier` through to registry entries
- **What to change:** `build_director_registry()` → `DirectorEntry` dataclass needs `certainty_tier` field
- **Verify:** `pytest tests/test_signals.py -v` — all existing tests must pass

**Step 3:** Modify `integrate_signals()` in `lib/signals.py`
- **What to change — P2 (`both_agree`):** Before returning `both_agree`, check `certainty_tier` of the matched category. If Tier 3+, return `review_flagged` at 0.4 instead.
- **What to change — P3 (`director_disambiguates`) → split into P3a and P3b:**
  - **P3a (new — `director_confirms`):** director matches Cat-A AND structure matches {Cat-A, Cat-B} (ambiguous, Cat-A is one of them) → route to Cat-A at 0.75. Director confirms one valid structural candidate.
  - **P3b (replaces old P3 — `review_flagged`):** director matches Cat-A AND structure matches Cat-B only (conflict, Cat-A ≠ Cat-B) → `review_flagged` at 0.4. Two signals in conflict, not confirmation.
- **What to change — P7 (`structural_signal`, unique match):** Before routing, check `certainty_tier`. If Tier 3+, return `review_flagged` at 0.4 with explanation including the suggested category.
- **What to change — P8 (`review_flagged`, ambiguous):** No change needed — already produces `review_flagged`.
- **Verify:** `pytest tests/test_signals.py -v`

**Step 4:** Add tests for new Tier 3 behaviour in `tests/test_signals.py`
- Test: Indie Cinema structural match → `review_flagged` (not `structural_signal`)
- Test: Indie Cinema `both_agree` scenario → `review_flagged` (not `both_agree`)
- Test: Music Films structural match → `review_flagged`
- Test: Giallo structural match → `structural_signal` (unchanged — Tier 1)
- Test: director conflict (Cat-A ≠ Cat-B) → `review_flagged` (old P3 behaviour removed)
- Test: director confirms ambiguous structural (Cat-A ∈ {Cat-A, Cat-B}) → `director_confirms`
- **Verify:** `pytest tests/ -v` — all tests pass, new tests pass

**Step 5:** Update `CLAUDE.md` Rule 11 (Certainty-First Classification)
- **What to change:** Add explicit statement: Tier 3+ categories (Music Films, Indie Cinema, Cult Oddities) never auto-classify. All matches produce `review_flagged` with a suggestion annotation. Films reach these categories only via SORTING_DATABASE pin, corpus match, or review queue acceptance.
- **Verify:** grep `review_flagged` in `CLAUDE.md` — confirms enforcement is documented

**Step 6:** Update `docs/SATELLITE_CATEGORIES.md`
- **What to change:** Mark Indie Cinema, Music Films, Cult Oddities with `certainty_tier: 3/4` and note "no auto-routing — review queue only"
- **Verify:** Visual scan of updated sections

**Step 7:** Regenerate outputs
- Run `python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted`
- Run `python scripts/reaudit.py > output/post-051-reaudit.txt`
- Compare against pre-051 baseline
- **Verify:** See §8 Validation Sequence

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `lib/constants.py` | Modify | Add `certainty_tier` field to every `SATELLITE_ROUTING_RULES` entry; add `certainty_tier` to `DirectorEntry` dataclass |
| `lib/signals.py` | Modify | `integrate_signals()`: enforce certainty tier in P2, P7; replace P3 with P3a (`director_confirms`) + P3b (conflict → `review_flagged`) |
| `tests/test_signals.py` | Modify | Add 6+ new tests covering Tier 3 downgrade and new P3a/P3b behaviour |
| `CLAUDE.md` | Modify | Rule 11 — explicit statement of Tier 3+ no-auto-routing |
| `docs/SATELLITE_CATEGORIES.md` | Modify | Mark Indie Cinema, Music Films, Cult Oddities with certainty tier and routing restriction |

---

## 6. Scope Boundaries

**In scope:**
- Adding `certainty_tier` to `SATELLITE_ROUTING_RULES`
- Enforcing certainty tier in `integrate_signals()` (P2, P3, P7)
- Replacing `director_disambiguates` with P3a (`director_confirms`) + P3b (conflict → `review_flagged`)
- Removing Indie Cinema, Music Films, Cult Oddities from auto-routing
- Documentation updates (CLAUDE.md Rule 11, SATELLITE_CATEGORIES.md)

**NOT in scope:**
- Adding new categories (German New Cinema, Italian Art Cinema etc.) — Issue #52
- Correcting misplaced explicit_lookup films (Cocteau, Wyler, Lelouch etc.) — separate review pass
- Rebuilding explicit_lookup films as formal corpora — separate issue
- Reference canon corpus migration — Issue #50
- Changing Tier 1/2 routing logic — this change adds constraints only; existing correct routing is untouched
- Changing confidence values for existing reason codes

**Deferred to:** Issue #52 (new category development — Tier 4 entries for German New Cinema etc.)

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Films auto-classified (non-lookup) | ~275 (structural + both_agree + director) | ~150–180 (Tier 1/2 only) | `sorting_manifest.csv` reason code counts |
| `both_agree` films in Tier 3 categories | 4 (Indie Cinema) | 0 | grep `both_agree` in manifest, filter by destination |
| `structural_signal` films in Indie Cinema | ~80–100 (estimate) | 0 | manifest filter |
| `review_flagged` count | 67 | ~150–180 (grows to absorb Tier 3 reclassification) | manifest reason count |
| `director_disambiguates` films | 51 | 0 (reason code removed) | manifest reason count |
| Tier 1 `both_agree` accuracy | 73.8% (contaminated) | ≥75% (clean Tier 1 only) | `accuracy_baseline.json` |
| Tier 1 `structural_signal` accuracy | 67.4% (contaminated) | ≥70% (clean Tier 1 only) | `accuracy_baseline.json` |

**Expected direction:** Auto-classified count drops. Review queue grows. Accuracy per reason code rises because the contaminating Tier 3 population is removed from measurement. This is the clean baseline.

**Pin baseline before implementing:**
```bash
git tag pre-issue-051
python scripts/reaudit.py > output/pre-051-reaudit.txt
cp output/accuracy_baseline.json output/accuracy_baseline_pre051.json
```

---

## 8. Validation Sequence

```bash
# Step 1: Run full test suite (must pass before any changes)
pytest tests/ -v
# Expected: 372+ passing, 1 skipped, 0 new failures

# Step 2: Verify certainty_tier field is present on all categories
python3 -c "
from lib.constants import SATELLITE_ROUTING_RULES
missing = [k for k,v in SATELLITE_ROUTING_RULES.items() if 'certainty_tier' not in v]
print('Missing certainty_tier:', missing or 'none')
"
# Expected: none missing

# Step 3: Run new signal tests
pytest tests/test_signals.py -v -k "certainty or tier3 or director_confirms"
# Expected: all new tests pass

# Step 4: Verify Indie Cinema no longer auto-classifies
python3 -c "
from lib.signals import integrate_signals, DirectorMatch, StructuralMatch
# Simulate Assayas + Indie Cinema structural match
dm = [DirectorMatch(tier='Satellite', category='Indie Cinema', canonical_name=None, source='satellite_rules', decade_valid=True)]
sm = [StructuralMatch(tier='Satellite', category='Indie Cinema', match_type='country_genre')]
result = integrate_signals(dm, sm, '1990s', 'R3')
print('Reason:', result.reason, '— Expected: review_flagged')
assert result.reason == 'review_flagged', f'FAIL: got {result.reason}'
print('PASS')
"

# Step 5: Verify Giallo still auto-classifies
python3 -c "
from lib.signals import integrate_signals, DirectorMatch, StructuralMatch
dm = [DirectorMatch(tier='Satellite', category='Giallo', canonical_name=None, source='satellite_rules', decade_valid=True)]
sm = [StructuralMatch(tier='Satellite', category='Giallo', match_type='country_genre')]
result = integrate_signals(dm, sm, '1970s', 'R3')
print('Reason:', result.reason, '— Expected: both_agree')
assert result.reason == 'both_agree', f'FAIL: got {result.reason}'
print('PASS')
"

# Step 6: Classify Unsorted and check reason distribution
python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted
python3 -c "
import csv
from collections import Counter
with open('output/sorting_manifest.csv') as f:
    rows = list(csv.DictReader(f))
print(Counter(r['reason'] for r in rows).most_common())
"
# Expected: director_disambiguates count = 0
# Expected: review_flagged count > pre-051 baseline (grows)
# Expected: structural_signal count < pre-051 baseline (shrinks)

# Step 7: Regression check on organised library
python audit.py && python scripts/reaudit.py > output/post-051-reaudit.txt
diff output/pre-051-reaudit.txt output/post-051-reaudit.txt
# Expected: Tier 1/2 confirmed count stable or improved
# Expected: Indie Cinema / Music Films confirmed count drops (those were false confirmations)
# Expected: no new wrong_tier or wrong_category for Tier 1 categories (Giallo, HK Action, etc.)

# Step 8: Regenerate accuracy baseline
python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted \
  --routing-contract scholarship_only \
  --output output/scholarship_manifest.csv
# Then run reaudit against it to update accuracy_baseline.json
```

**Expected results:**
- Step 1: All existing tests pass
- Step 4: Indie Cinema → `review_flagged` confirmed
- Step 5: Giallo → `both_agree` unchanged, confirmed
- Step 6: `director_disambiguates` = 0; `review_flagged` grows by ~50–100
- Step 7: Tier 1 confirmed count stable; Indie Cinema/Music Films confirmed count drops (expected)
- Step 8: Accuracy baseline per-category rises; aggregate may drop (correct — we removed padding)

**If any step fails:** Stop. Do not proceed. Report the failure output. The Giallo regression check (Step 5) is the highest-priority gate — if Tier 1 routing is broken, roll back immediately.

---

## 9. Rollback Plan

**Detection:** Tier 1 confirmed count (Giallo, HK Action, Brazilian Exploitation, etc.) drops in reaudit. Any Tier 1 `both_agree` film that was previously classified correctly now routes to `review_flagged`. These are regressions.

**Recovery:**
```bash
git revert [commit-hash]
# The certainty_tier enforcement is isolated in integrate_signals()
# Revert restores old P2/P3/P7 behaviour
# No cache changes needed — routing logic only
cp output/accuracy_baseline_pre051.json output/accuracy_baseline.json
```

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-051
python scripts/reaudit.py > output/pre-051-reaudit.txt
cp output/accuracy_baseline.json output/accuracy_baseline_pre051.json
```

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `CLAUDE.md` Rule 11 (Certainty-First Classification) — "Classify what you can prove first." Tier 3 categories cannot be proven at the structural gate level; they require human confirmation.
- `CLAUDE.md` Rule 2 (Pattern-First / Two-Signal Architecture) — "Both signals fire for every film." This issue enforces what happens when they fire for a low-certainty category: the result is review-flagged, not auto-classified.
- `exports/skills/certainty-first.md` Rule 1 — "A new Satellite category starts at Tier 4. It earns higher tiers by demonstrating data support." Indie Cinema was defined as Tier 3 but treated as Tier 1 in code. This issue corrects the implementation to match the theory.

**Architecture reference:**
- `docs/architecture/RECURSIVE_CURATION_MODEL.md §5` — Category Certainty Tiers table. This issue adds the `certainty_tier` field that §5 describes but the code does not yet have.
- `exports/skills/certainty-first.md` — The Anchor-Then-Expand pattern and Inverse Gate Rule. Tier 3 matches → review queue, never manifest. This issue implements the Inverse Gate Rule.
- `docs/issues/INVESTIGATION_051_CATEGORY_REDESIGN.md` — Full investigation notes including Kubrick simulation, director sparsity analysis, explicit_lookup baseline analysis, and the `director_disambiguates` accuracy finding.

**Related issues:**
- Issue #42 — Unified two-signal architecture. This issue enforces the certainty tier constraints that #42 did not implement.
- Issue #49 — Dashboard refocus. Revealed accuracy baseline contamination that triggered this investigation.
- Issue #50 — Core/Reference bypass of two-signal system. Separate scope; both document architectural gaps introduced before or during #42.
- Issue #52 (planned) — New category development: German New Cinema, Italian Art Cinema, Tier 4 → Tier 2 pathway.

---

### Section Checklist

- [x] §1 Manager Summary is readable without code knowledge
- [x] §3 Root causes reference specific files and functions
- [x] §4 ALL downstream consumers listed (reaudit, accuracy baseline, dashboard, failure cohorts)
- [x] §5 Execution Order has verify commands for each step
- [x] §5 Files to Modify is complete
- [x] §6 NOT in scope populated (new categories, explicit_lookup review, Reference migration)
- [x] §7 Measurement Story has concrete before/after numbers
- [x] §8 Validation Sequence commands are copy-pasteable
- [x] §9 Rollback plan documented
- [x] §10 Theory grounding references specific rules and sections
