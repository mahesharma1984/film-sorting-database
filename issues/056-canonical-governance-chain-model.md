# Issue #56: Canonical Governance Chain Model — L1/L2 Alignment with Film Scholarship

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P1-Critical |
| Date Opened | 2026-03-16 |
| Component | Theory / Architecture / Pipeline |
| Change Type | Refactor |
| Estimated Effort | 3-5 days |
| Blocked By | None |
| Blocks | All future classification improvements |
| Supersedes | None (extends #55) |

---

## 1. Manager Summary

**Problem:** The project has extensive film scholarship grounding (THEORETICAL_GROUNDING.md cites 15+ published frameworks) and a well-documented architecture, but the classification pipeline doesn't implement them. L1 theory says evidence accumulation with uncertainty (Dempster-Shafer). L5 code does binary gates with short-circuit. L1 says shared workspace (Erman blackboard). L5 does sequential pipeline where each stage is blind to others. The governance chain is broken between L1/L2 and L3/L5.

**Impact if unfixed:** The pipeline continues to destroy information at every stage. Films with partial data get `unsorted_no_match` when the theory says they should accumulate evidence and express uncertainty. The 134 `unsorted_no_director` and 54 `unsorted_no_match` films (38% of unsorted queue) are symptoms of this L1→L5 gap.

**Risk if fixed wrong:** Classification regressions on the 91.2% pipeline accuracy baseline. Over-engineering — adding Dempster-Shafer formalism when a simpler evidence model achieves the same result.

**Estimated effort:** 3-5 days. Phase 1 (evidence-preserving gates in routing) is the MVP. Phase 2 (shared workspace / collective classification) is stretch.

---

## 2. Evidence

### Observation

The project's own theory documents diagnose the exact gaps in the implementation:

**THEORETICAL_GROUNDING.md §9 (Dempster-Shafer):**
> "Binary gates collapse this to `True AND False = False`. The positive evidence is destroyed by the absence of genre data."

**THEORETICAL_GROUNDING.md §11 (Blackboard Architecture):**
> "The Satellite classifier cannot see that the parser struggled with the title. The Popcorn classifier cannot see that Satellite almost matched. Each stage is blind to context accumulated elsewhere."

**THEORETICAL_GROUNDING.md §12 (Ashby Requisite Variety):**
> "`unsorted_no_match` conflates films needing enrichment (R1), films needing rules (R2b taxonomy gaps), genuinely unroutable films (adult, TV), and near-misses."

**THEORETICAL_GROUNDING.md §10 (Stigmergy):**
> "When 28 of 30 Italian 1970s films route to Giallo, the 29th film with missing genres receives no benefit from the 28 successful classifications."

### Data — The four L1→L5 gaps

| # | L1 Theory Says | L5 Code Does | Source |
|---|---|---|---|
| 1 | Absent evidence ≠ negative evidence. Three states: belief, disbelief, uncertainty. | `genres=[] → gate fails → category skipped`. Binary pass/fail. | Dempster-Shafer §9 |
| 2 | Shared workspace — all knowledge sources see accumulated context. | Sequential pipeline — each stage blind to others. | Erman blackboard §11 |
| 3 | Controller variety must match system variety. | `unsorted_no_match` for 5+ distinct failure modes. | Ashby §12 |
| 4 | Previous classifications inform ambiguous cases (collective evidence). | Every film classified from scratch. | Stigmergy §10 |

### Data — Partial implementation exists

`evaluate_category()` in `lib/satellite.py` already has three-valued gate logic (pass/fail/untestable) from Issue #35. But this is only used in the diagnostic shadow pass (`_gather_evidence()`), not in actual routing. The evidence architecture exists but routes through a dead-end — it produces `evidence_trails.csv` that nobody reads, while the actual classifier uses binary gates.

---

## 3. Root Cause Analysis

### RC-1: Evidence gates exist but don't route
**Location:** `lib/satellite.py` → `evaluate_category()` (three-valued) vs `classify_structural()` (binary)
**Mechanism:** `evaluate_category()` returns `GateResult` with pass/fail/untestable. But `classify_structural()` (used by `score_structure()` in actual routing) calls `evaluate_category()` and discards the untestable signals — it only returns categories that pass. A category with country=pass, decade=pass, genre=untestable gets skipped instead of being surfaced as a partial match with uncertainty.

### RC-2: Signal integration has no uncertainty representation
**Location:** `lib/signals.py` → `integrate_signals()`
**Mechanism:** `IntegrationResult` has `confidence` (float) but no uncertainty field. The confidence score conflates "high evidence for" (0.85 both_agree) with "low evidence against" (0.65 single signal). Dempster-Shafer would distinguish: "strong belief + low uncertainty" from "moderate belief + high uncertainty". These require different curator actions — the first is auto-classifiable, the second needs review.

### RC-3: No near-miss output
**Location:** `classify.py` → `_resolve_unsorted()`
**Mechanism:** When no resolver matches, the film gets `unsorted_no_match` with no information about which categories came closest. The evidence trail shadow pass computes nearest misses but stores them in a CSV that isn't connected to the review queue. A curator seeing `unsorted_no_match` gets no guidance about what to investigate.

### RC-4: No collective context
**Location:** `classify.py` → `process_directory()` iterates films independently
**Mechanism:** Each film is classified without knowledge of what other films in the same batch resolved to. If 28/30 Italian 1970s films route to Giallo, the 29th with missing data gets no benefit. No base-rate accumulation within a run.

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| satellite.evaluate_category → classify_structural | `evaluate_category()` returns GateResult | `classify_structural()` discards untestable | Yes — preserve untestable |
| score_structure → integrate_signals | Returns StructuralMatch list | Integration reads category + match_type | Yes — add uncertainty field |
| integrate_signals → _resolve_two_signal | Returns IntegrationResult | Resolver reads tier/category/confidence | Yes — add uncertainty + near_misses |
| _resolve_unsorted → manifest | Returns reason code only | Manifest shows reason, review_queue | Yes — add nearest_miss info |

**Gate impact:** `classify_structural()` will return partial matches alongside full matches, distinguished by a flag. `integrate_signals()` will factor uncertainty into confidence scoring. Near-miss data flows to the review queue.

**Downstream consumers:**
- `dashboard.py` — could display near-miss info for unsorted films (stretch)
- `output/review_queue.csv` — gains nearest-miss category + evidence profile
- `scripts/reaudit.py` — reason codes preserved, may gain new uncertainty-tagged codes

---

## 5. Proposed Fix

### Fix Description

Implement the L1 theory's evidence model as the actual routing mechanism, not just a diagnostic shadow pass. MVP: make `classify_structural()` return partial matches with uncertainty. Use the evidence that already exists in `evaluate_category()` — don't build new infrastructure.

### Phase 1: Evidence-Preserving Routing (MVP)

**Principle:** The three-valued gate logic already exists. Stop discarding it.

#### Step 1: Extend StructuralMatch to carry uncertainty

Modify `lib/signals.py` `StructuralMatch` dataclass:
```python
@dataclass
class StructuralMatch:
    tier: str
    category: str
    match_type: str
    uncertainty: float  # NEW: 0.0 = all gates tested, 1.0 = most gates untestable
    gates_passed: int   # NEW
    gates_tested: int   # NEW
```
**Verify:** `pytest tests/test_signals.py`

#### Step 2: Make classify_structural() return partial matches

Modify `lib/satellite.py` `classify_structural()` to return categories where:
- All tested gates pass (current behavior: full match)
- Some gates pass, remainder untestable (NEW: partial match with uncertainty > 0)
- Exclude categories with any gate that actively FAILS (disbelief)

Mark partial matches with `match_type='partial_structural'` and `uncertainty` proportional to untestable gates.

**Verify:** `pytest tests/test_satellite.py`

#### Step 3: Factor uncertainty into integrate_signals()

Modify `lib/signals.py` `integrate_signals()`:
- Full structural matches behave as before (current P3-P7)
- Partial structural matches with uncertainty get capped confidence: `base_confidence * (1.0 - uncertainty)`
- Partial + director agree → `both_agree` but lower confidence (e.g. 0.65 instead of 0.85)
- Partial + no director → `review_flagged` (not auto-classified, surfaces in review queue)

**Verify:** `pytest tests/test_signals.py`

#### Step 4: Surface near-miss in unsorted output

Modify `classify.py` `_resolve_unsorted()`:
- If `_resolve_two_signal()` returned None but partial matches exist from signal scoring, attach nearest-miss category to the ClassificationResult evidence
- Change reason code vocabulary: `unsorted_no_match` → `unsorted_near_miss` (has partial evidence) vs `unsorted_no_evidence` (no signals fired at all)

**Verify:** `pytest tests/ -v` full suite

#### Step 5: Route near-miss films to review queue with evidence

Modify `classify.py` `write_review_queue()`:
- Films with `unsorted_near_miss` include the nearest category, which gates passed, which were untestable
- Curator sees: "This film is probably Giallo (country=IT, decade=1970s match; genre data missing)"

**Verify:** Run on source directory, inspect review_queue.csv

### Phase 2: Collective Classification (Stretch)

#### Step 6: Within-run base rates

Modify `classify.py` `process_directory()`:
- After first pass, compute base rates: {(country, decade) → category distribution}
- Second pass on `unsorted_near_miss` films: apply base rate as tiebreaker for partial matches
- E.g., if 28/30 IT 1970s films → Giallo, an IT 1970s film with missing genres gets Giallo with `reason='base_rate_inference'`, `confidence=0.5`

**Verify:** Run twice, compare manifests — second pass should classify some near-miss films

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `lib/signals.py` | Modify | `StructuralMatch` gains uncertainty fields; `integrate_signals()` factors uncertainty |
| `lib/satellite.py` | Modify | `classify_structural()` returns partial matches |
| `classify.py` | Modify | `_resolve_unsorted()` gains near-miss; `write_review_queue()` gains evidence |
| `lib/pipeline_types.py` | Modify | `Resolution` may gain `nearest_miss` field |
| `tests/test_signals.py` | Modify | New tests for uncertainty handling |
| `tests/test_satellite.py` | Modify | New tests for partial match return |

---

## 6. Scope Boundaries

**In scope:**
- Making `classify_structural()` return partial matches using existing three-valued gate logic
- Extending StructuralMatch with uncertainty
- Factoring uncertainty into confidence scoring
- Surfacing near-miss information in review queue
- Splitting `unsorted_no_match` into `unsorted_near_miss` / `unsorted_no_evidence`

**NOT in scope:**
- Full Dempster-Shafer formalism (over-engineering — simple uncertainty ratio achieves the goal)
- Blackboard architecture rewrite (Phase 2 base rates are the MVP version of shared workspace)
- Changing any existing classification outputs (films currently classified correctly stay classified correctly)
- Modifying SORTING_DATABASE, corpora, or routing rules
- Dashboard changes

**Deferred to:** Future issue — full shared workspace architecture (THEORETICAL_GROUNDING.md §11)

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Pipeline accuracy | 91.2% | ≥ 91.2% (zero regression) | `python scripts/reaudit.py` |
| `unsorted_no_match` count | 54 | Lower (some become `unsorted_near_miss` with actionable guidance) | manifest reason codes |
| Review queue actionability | reason code only | reason + nearest category + evidence profile | inspect review_queue.csv |
| Tests | 402+ passed | ≥ 402 passed | `pytest tests/` |
| Near-miss recovery (stretch) | 0 films | 5-15 films gain partial classification | manifest classified count |

**Pin baseline before implementing:**
```bash
git tag pre-issue-056
cp output/sorting_manifest.csv output/sorting_manifest_pre056.csv
python scripts/reaudit.py > output/pre-056-reaudit.txt
```

---

## 8. Validation Sequence

```bash
# Step 1: Run full test suite
pytest tests/ -v

# Step 2: Classify and compare
python classify.py <source_directory> --output output/sorting_manifest_post056.csv

# Step 3: Verify zero regression on existing classifications
# Films previously classified must have same tier/category
python compare_manifests.py output/sorting_manifest_pre056.csv output/sorting_manifest_post056.csv

# Step 4: Verify near-miss data in review queue
head -20 output/review_queue.csv

# Step 5: Reaudit
python scripts/reaudit.py --review
```

**Expected results:**
- Step 1: ≥ 402 tests pass
- Step 3: Zero changes to previously classified films; some `unsorted_no_match` become `unsorted_near_miss`
- Step 4: Review queue entries show nearest category + evidence gates
- Step 5: Confirmed count ≥ baseline

---

## 9. Rollback Plan

**Detection:** Existing classifications change. Pipeline accuracy drops below 91.2%.

**Recovery:**
```bash
git revert [commit-hash]
```

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-056
```

---

## 10. Theory & Architecture Grounding

**L1 Theory — Film Scholarship:**
- `docs/theory/THEORETICAL_GROUNDING.md` §9 — Dempster-Shafer evidence theory: belief/disbelief/uncertainty triad replaces binary gates
- `docs/theory/THEORETICAL_GROUNDING.md` §5 — Bayesian evidence combination + signal detection theory: multiple independent signals, confidence proportional to evidence strength
- `docs/theory/THEORETICAL_GROUNDING.md` §10 — Stigmergy: collective classification from accumulated traces
- `docs/theory/THEORETICAL_GROUNDING.md` §11 — Blackboard architecture: shared workspace over sequential pipeline
- `docs/theory/THEORETICAL_GROUNDING.md` §12 — Ashby requisite variety: controller vocabulary must match system variety
- `docs/theory/TIER_ARCHITECTURE.md` §3 — Tier priority as philosophical statement: character determines tier
- `docs/theory/MARGINS_AND_TEXTURE.md` §2 — Historically bounded categories with decade-validated routing
- `docs/theory/MARGINS_AND_TEXTURE.md` §8 — Positive-space vs negative-space: keyword signals only for named movements

**L2 Architecture:**
- `docs/architecture/VALIDATION_ARCHITECTURE.md` §2 — Evidence trails, information destruction diagnosis
- `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` — Director + structure as independent signals
- `docs/architecture/RECURSIVE_CURATION_MODEL.md` §5 — Certainty tiers: inverse gate rule

**L3 Components (existing, to be extended):**
- `lib/satellite.py` `evaluate_category()` — already has three-valued gates (Issue #35)
- `lib/signals.py` `StructuralMatch` / `IntegrationResult` — to gain uncertainty fields
- `lib/pipeline_types.py` `Resolution` — typed boundary

**L4 Dev Rules:**
- `CLAUDE.md` Rule 13 — Fix at highest divergent level (L1 theory → L5 code gap)
- `CLAUDE.md` Rule 7 — Measurement-driven: near-miss recovery is measurable
- `CLAUDE.md` Rule 5 — Constraint gates: absent evidence ≠ failure

**Related issues:**
- #35 — Created three-valued gate logic and evidence trails (this issue makes them route, not just diagnose)
- #42 — Created two-signal architecture (this issue extends signals with uncertainty)
- #55 — Cleaned up resolve chain (this issue extends the signal layer within the clean chain)
