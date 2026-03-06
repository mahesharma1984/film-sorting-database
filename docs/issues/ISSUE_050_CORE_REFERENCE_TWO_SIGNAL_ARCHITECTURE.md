# Issue #50: Architectural Question — Core/Reference Bypass of Two-Signal System

| Field | Value |
|---|---|
| Status | OPEN — Discovery phase |
| Priority | P2-High |
| Date Opened | 2026-03-06 |
| Component | classify.py / lib/signals.py / lib/constants.py |
| Change Type | Architecture Decision |
| Estimated Effort | 1–2 days investigation → separate implementation issue |
| Blocked By | None |
| Blocks | None |
| Supersedes | None |

---

## 1. Manager Summary

**Problem:** Core and Reference tier classifications bypass the two-signal system entirely. They exit the pipeline by identity match (director whitelist / canon list) before `score_director()` and `score_structure()` ever fire. This means approximately 200–300 films in the organized library have no signal confidence score, no `both_agree`/`structural_signal` reason code, and are invisible to the accuracy baseline. The two-signal system's diagnostic value — measuring how well the pipeline performs — is incomplete because its most "certain" classifications are excluded from measurement.

**Impact if unfixed:** The accuracy baseline (`accuracy_baseline.json`) can only measure the pipeline on films that reached the two-signal stage. Core and Reference films are not in that population. The `scholarship_only` contract was built specifically to work around this gap. If Core/Reference were brought inside the signal framework, we could produce a unified accuracy measurement across all tiers.

**Risk if fixed wrong:** Core directors (Kubrick, Godard, etc.) begin routing to Satellite categories that match their structural coordinates (e.g. Godard → French New Wave instead of Core). Decades of human curation in SORTING_DATABASE could be bypassed. Accuracy could appear to improve while actual routing quality degrades.

**Estimated effort:** Discovery/design phase: 1–2 days. Implementation (if decided): separate issue.

---

## 2. Evidence

### Observation

From the current `classify.py` pipeline:

```
Stage 1: explicit_lookup (SORTING_DATABASE)  → exit, confidence 1.0, reason=explicit_lookup
Stage 2: corpus_lookup                        → exit, confidence 1.0, reason=corpus_lookup
Stage 3: Core director whitelist check        → exit, confidence 1.0, reason=core_director [pre-signal]
Stage 4: Reference canon check                → exit, confidence 1.0, reason=reference_canon [pre-signal]
─────────────────────────────────────────────────────────────────────────────────────────
Two-signal system fires here (Stages 5+):
  score_director() + score_structure() → integrate_signals()
    → Satellite / Popcorn / Unsorted
```

Core and Reference never reach `score_director()` or `score_structure()`. They are classified by identity assertion, not by signal evidence.

### Data

From `output/accuracy_baseline.json` (scholarship_only contract, 796 films):

| Reason code | Films | Accuracy |
|---|---|---|
| `both_agree` | 42 | 73.8% |
| `director_disambiguates` | 51 | 52.9% |
| `director_signal` | 37 | 73.0% |
| `structural_signal` | 304 | 67.4% |
| `review_flagged` | 125 | 65.6% |
| `popcorn` | 45 | 66.7% |
| `user_tag_recovery` | 29 | 86.2% |
| **Core/Reference** | — | **not measured** |

The scholarship_only contract deliberately excludes Core/Reference to isolate two-signal performance. But this means we have never measured Core/Reference classification quality under a signal framework.

**Films affected by Core whitelist bypass (approximate):**
- Core tier: ~150+ films (all classified as `core_director`, no signal score)
- Reference tier: ~50 films (all classified as `reference_canon`, no signal score)
- Together these represent roughly 25% of the organized library that is outside the measurement framework.

---

## 3. Root Cause Analysis

### RC-1: Core/Reference are identity gates, not signal outputs
**Location:** `classify.py` → `_route_film()` (Stages 3–4)
**Mechanism:** The whitelist check (`if director in CORE_DIRECTORS`) fires as a binary match and returns immediately. No signal computation occurs. The classification decision is "this director name is in the list" — a precision operation — not "signals agree this film belongs in Core" — a reasoning operation. The gate was designed before the two-signal architecture existed (Issue #42 added signals; Core/Reference predate it).

### RC-2: Core has no structural definition
**Location:** `lib/constants.py` → `CORE_DIRECTORS` whitelist
**Mechanism:** Core is defined by a list of ~80 named directors. There is no structural definition: no country, decade, or genre coordinates that would let the structural signal fire independently of the director signal. This is by design — Core is a prestige tier for auteur directors regardless of country/era. But it means Signal 2 (structural) cannot independently confirm a Core classification. Signal 1 (director) is the only signal, and it's deterministic (whitelist match).

### RC-3: Reference is defined by curation, not scholarship
**Location:** `lib/constants.py` → `REFERENCE_CANON` (50-film hardcoded list)
**Mechanism:** The canon is a curated list of 50 films — a human editorial judgment about which non-Core films belong in the collection's reference tier. Unlike Satellite categories (which are grounded in published scholarship about historical movements), Reference has no external academic definition. It is the most subjective tier. This makes it the hardest to bring under a signal framework: what structural signal fires for "canonical prestige film by a non-Core director"?

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| Identity gates → two-signal | `classify.py:_route_film()` Stages 3–4 | `lib/signals.py:integrate_signals()` | Yes — if gates removed, signals fire for all films |
| Signal output → tier routing | `lib/signals.py:integrate_signals()` | `classify.py:_build_result()` | Yes — Core/Reference would become signal outputs, not bypass outputs |
| Manifest → reaudit | `output/sorting_manifest.csv` | `scripts/reaudit.py` | Yes — reason codes change for Core/Reference films |
| Manifest → accuracy baseline | `output/accuracy_baseline.json` | `dashboard.py:render_signal_accuracy()` | Yes — Core/Reference now appear in measurement |

**Gate impact:** Any change to Core/Reference routing will shift the reaudit baseline. Current confirmed count (744/796) includes Core/Reference films which confirm trivially because the library and classifier agree (they were placed by the same whitelist). Bringing Core/Reference into the signal framework may reduce the confirmed count if signals disagree with prior placement.

**Downstream consumers of changed output:**
- `scripts/reaudit.py` — compares classifier output to organized library. If Core films now route to Satellite (wrong), confirmed count drops significantly.
- `dashboard.py:render_signal_accuracy()` — currently shows scholarship_only data. If Core/Reference enter the signal framework, accuracy numbers change.
- `output/accuracy_baseline.json` — must be regenerated if routing changes.

---

## 5. Proposed Fix

**This is a discovery issue. No implementation is proposed until the architecture question is resolved.** The three options below are for evaluation, not execution.

### Option A: Keep the current architecture (status quo)
**Description:** Core/Reference remain as identity gates. The `scholarship_only` contract remains the measurement tool for two-signal performance. Accept that the system has two classification modes: identity (Core/Reference) and signal (everything else).

**Pro:** No regression risk. Core directors reliably route to Core. Reference canon films are stable.

**Con:** Core/Reference accuracy is never measured. The two-signal system's diagnostic coverage is permanently partial. The architecture is internally inconsistent — some films use signals, others don't.

**When to choose:** If the primary goal is collection stability and routing reliability for known films.

---

### Option B: Post-signal routing — signals fire for all films, Core/Reference are outcomes
**Description:** Remove the identity gates (Stages 3–4). Every film passes through `score_director()` + `score_structure()`. Add Core and Reference as possible outputs of `integrate_signals()`:
- If `director_signal` fires AND director is a Core whitelist member → route to Core
- If `explicit_lookup` or `corpus_lookup` matches a Reference canon film → route to Reference

**Pro:** Unified measurement framework. Every film gets a signal confidence score. Core/Reference appear in accuracy baseline.

**Con:** Core directors (Godard, Kubrick) will also match Satellite structural signals (French New Wave, etc.). Signal integration priority table (P1–P10) must explicitly handle "Core director who also matches Satellite structural gate." Risk: Godard routes to French New Wave instead of Core unless priority is carefully designed.

**Implementation risk:** HIGH. Priority table changes have historically caused cascading routing changes (see Issues #25, #32).

**Mitigation:** SORTING_DATABASE pins for any film that routes wrong after the change.

**When to choose:** If unified accuracy measurement is a high priority and you're willing to invest in regression management.

---

### Option C: Can Core/Reference become scholarship categories?
**Description:** Investigate whether Core and Reference can be grounded in published scholarship the same way Satellite categories are — giving them structural coordinates (country, decade, genre) that let Signal 2 fire independently.

**For Core:** The academic literature on auteur theory (Cahiers du Cinéma critics, Andrew Sarris's *The American Cinema*, V.F. Perkins) defines auteur directors by stylistic consistency across a body of work. This is a director-level property, not a structural one. Core cannot be defined by country + decade + genre because auteur directors span all of those. Structural Signal 2 cannot fire independently for Core.

**Conclusion for Core:** Core is fundamentally a director-identity category. The only structural definition available is "director with a recognized critical tradition" — which is Signal 1 (director identity) restated. Core cannot be a scholarship category in the Satellite sense. It must remain an identity gate OR become a post-signal output of Signal 1 alone (no Signal 2 corroboration possible).

**For Reference:** The Reference canon (50 films) is modeled on published film canons (Sight & Sound, Cahiers du Cinéma, Ebert's Great Movies). These external canons could be formalized as corpora (like `data/corpora/giallo.csv`) — making Reference a `corpus_lookup` classification rather than a hardcoded list match. This is structurally similar to what Issue #38 did for Giallo. Each canon film would have an IMDb ID and canonical tier.

**Conclusion for Reference:** Reference CAN be reframed as a scholarship corpus. The 50-film hardcoded list in `lib/constants.py` would become `data/corpora/reference_canon.csv`, classified via corpus_lookup at Stage 2. This is already inside the confidence-1.0 measurement framework. No change to signal architecture needed — just moving the data source.

**When to choose Option C (Reference):** Low risk. Reference corpus migration is isolated and adds IMDb ID-based matching (more reliable than title+year normalization). Recommended.

**When to choose Option C (Core):** Not applicable. Core cannot be a scholarship category under the current theory. Its defining property (auteur identity) is an identity assertion, not a structural coordinate.

---

### Recommended path
1. **Reference → corpus migration** (Option C, Reference only): Low risk, high value. Converts the hardcoded 50-film canon to `data/corpora/reference_canon.csv`. Reference films get `reason=corpus_lookup`, appear in accuracy measurement.
2. **Core → status quo** (Option A): Core remains an identity gate. Accept that Core accuracy is not measured by the signal framework. Document this explicitly in `TWO_SIGNAL_ARCHITECTURE.md`.
3. **Post-signal Core (Option B)**: Defer. Consider only if the priority table can be extended cleanly to handle "Core director who also structurally matches Satellite."

### Files to Modify (if Recommended path implemented)

| File | Change Type | What Changes |
|---|---|---|
| `data/corpora/reference_canon.csv` | Create | 50-film Reference canon with IMDb IDs and canonical tier |
| `lib/corpus.py` | Modify | `CorpusLookup` already handles this — no change needed |
| `classify.py` | Modify | Remove Stage 4 (reference_canon hardcoded check) — corpus_lookup at Stage 2 handles it |
| `lib/constants.py` | Modify | Remove `REFERENCE_CANON` dict (or keep for dashboard backwards compat) |
| `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` | Update | Document Core identity gate as intentional design decision |
| `CLAUDE.md` | Update | §3 Rule 2 — clarify Core as identity gate |

---

## 6. Scope Boundaries

**In scope (discovery):**
- Documenting the architectural gap between Core/Reference identity gates and the two-signal system
- Evaluating whether Core/Reference can be scholarship categories under current theory
- Recommending a path forward

**In scope (if Recommended path implemented):**
- Reference corpus migration to `data/corpora/reference_canon.csv`
- Removing hardcoded `REFERENCE_CANON` from `classify.py` Stage 4

**NOT in scope:**
- Changing Core routing (identity gate stays until a clear safe migration path exists)
- Modifying `integrate_signals()` priority table (high regression risk, separate issue)
- Redefining what "Core" means as a curatorial category

**Deferred to:** Follow-up issue for Option B (post-signal Core routing) if Reference migration succeeds without regression.

---

## 7. Measurement Story

| Metric | Before (Current) | After (Recommended path) | How to Measure |
|---|---|---|---|
| Reason codes with accuracy data | 7 signal codes (no Core/Ref) | 7 signal codes + `corpus_lookup` for Reference films | `accuracy_baseline.json` `by_stage` keys |
| Reference films in accuracy baseline | 0 | ~50 | `accuracy_baseline.json` `by_stage.corpus_lookup` |
| Reaudit confirmed (Reference films) | confirmed trivially (identity match) | confirmed via corpus_lookup (IMDb ID match, confidence 1.0) | `scripts/reaudit.py` |
| Core films measured by signals | 0 | 0 (no change — Core stays as identity gate) | — |

**Pin baseline before implementing:**
```bash
git tag pre-issue-050
python scripts/reaudit.py > output/pre-050-reaudit.txt
```

---

## 8. Validation Sequence

```bash
# Step 1: Run full test suite
pytest tests/ -v
# Expected: 372+ passing, 1 skipped, no new failures

# Step 2: Validate Reference corpus lookup
python scripts/build_corpus.py --audit "Reference Canon"
# Expected: 50 entries, 0 HARD anomalies

# Step 3: Classify known Reference films
python classify.py <source_directory>
# Expected: Breathless (1960, Godard) → Core (not Reference)
# Expected: 400 Blows (Truffaut, 1959) → Reference, reason=corpus_lookup

# Step 4: Regression check
python audit.py && python scripts/reaudit.py
# Expected: confirmed count ≥ pre-050 baseline
# Expected: no new wrong_tier for Reference films

# Step 5: Accuracy baseline regeneration
python scripts/reaudit.py  # generates accuracy_baseline.json
# Expected: corpus_lookup appears in by_stage with ~50 films and accuracy near 1.0
```

**Expected results:**
- Step 1: All tests pass
- Step 3: Godard films still route to Core (Core gate fires before corpus_lookup for Reference)
- Step 4: No regressions in confirmed count
- Step 5: Reference films now appear in accuracy measurement

---

## 9. Rollback Plan

**Detection:** Reaudit confirmed count drops below 744, or Reference films start routing to wrong tier.

**Recovery:**
```bash
git revert [commit-hash]
# Reference corpus lookup is isolated — revert restores hardcoded REFERENCE_CANON check
```

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-050
```

---

## 10. Theory & Architecture Grounding

**Core cannot be a scholarship category — theoretical basis:**

Satellite categories are grounded in film-historical scholarship (Rule 4: Domain Grounding). Each has a named tradition with date bounds, country of origin, and documented director membership. The structural signal fires because those coordinates (country + decade + genre) are measurable from API data.

Core directors are defined by auteur theory — a critical tradition that asserts certain directors impose a consistent personal vision across their filmographies regardless of production context, country, or era. Kubrick made films in the US, UK, and France across five decades in multiple genres. There are no structural coordinates that uniquely identify "Kubrick film" vs "competent studio film." The identification is entirely director-identity-based.

Therefore: **Core is a Signal 1-only category**. Signal 2 cannot fire independently for Core because there are no structural coordinates. Under the two-signal framework (Rule 2), a `director_signal`-only classification would have confidence 0.65 — lower than the identity assertion (1.0) the whitelist currently provides. Bringing Core into the signal framework would *lower* confidence for correctly classified films. This is the wrong direction.

**Reference can be a scholarship category — theoretical basis:**

The Reference canon (50 films) is modeled on external published canons: Sight & Sound Greatest Films, AFI 100, Ebert's Great Movies, Criterion Collection priorities. These are scholarship-backed curatorial decisions, equivalent in authority to the academic sources used for Satellite categories (Koven on Giallo, etc.). Moving Reference to a corpus (`data/corpora/reference_canon.csv`) with IMDb IDs is consistent with the ground truth architecture established in Issue #38. It gives Reference films a confidence-1.0 classification with an auditable source, and includes them in the accuracy measurement framework.

**Methodology basis:**
- `CLAUDE.md` Rule 2 (Two-Signal Architecture) — signals fire for classification; identity gates are pre-signal. This issue asks whether pre-signal gates belong in the architecture.
- `CLAUDE.md` Rule 4 (Domain Grounding) — categories must be grounded in published scholarship. Core cannot meet this bar structurally; Reference can via corpus migration.
- `CLAUDE.md` Rule 11 (Certainty-First Classification) — classify what you can prove first. Identity gates (Tier 1 certainty) are consistent with this rule; the question is whether they should remain outside the signal framework.

**Architecture reference:**
- `docs/architecture/VALIDATION_ARCHITECTURE.md` §3 (Ground Truth Corpora) — the corpus model is the right home for Reference canon
- `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` §3 (Integration) — priority table (P1–P10) currently has no Core/Reference entries; they exit before integration
- Issue #38 — established the corpus model; Reference migration follows the same pattern

**Related issues:**
- #38 — Ground truth corpora (Giallo). Reference migration follows identical pattern.
- #42 — Unified two-signal architecture. Core/Reference were not integrated at that time.
- #48 — Scholarship-only routing contract. Built specifically to work around the Core/Reference exclusion.
- #49 — Dashboard refocus. Signal Accuracy panel now surfaces the gap (Core/Reference not in `by_stage`).

---

### Section Checklist

- [x] §1 Manager Summary is readable without code knowledge
- [x] §3 Root causes reference specific files and functions
- [x] §4 ALL downstream consumers are listed
- [x] §5 Three options evaluated; recommended path identified
- [x] §5 Files to Modify listed for recommended path
- [x] §6 NOT in scope populated (Core stays as identity gate)
- [x] §7 Measurement Story has concrete before/after
- [x] §8 Validation Sequence commands are copy-pasteable
- [x] §9 Rollback plan documented
- [x] §10 Theory grounding explains why Core cannot / Reference can be scholarship categories
