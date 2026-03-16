# Issue #57: LLM Interpretive Classification Pass (Tier 2 Reasoning)

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P1-Critical |
| Date Opened | 2026-03-16 |
| Component | Classify / New: LLM Resolver |
| Change Type | Feature |
| Estimated Effort | 2-3 days |
| Blocked By | None |
| Blocks | None |
| Supersedes | #56 (subsumes the "partial match" approach — LLM reasoning replaces binary gate expansion) |

---

## 1. Manager Summary

**Problem:** The current pipeline classifies only 245 of 796 organised films (31%) — those with exact corpus/whitelist/canon matches. The remaining 551 films are in staging because the heuristic pipeline (P4 two-signal integration) attempts interpretive classification with precision tools (binary gates, exact string matching). This is an R/P Split violation: classification is a reasoning task assigned to code.

**Impact if unfixed:** 551 films remain unsorted. The pipeline can only classify films it has seen before (corpus) or that exactly match structural rules (country + decade + genre gates). Any film outside these narrow paths — which is most films — falls through to `unsorted_no_match`.

**Risk if fixed wrong:** LLM hallucination produces confident but wrong classifications. LLM costs compound if not gated. Prompt drift creates unreproducible results. These risks are addressed by the Context → Reasoning → Verification architecture (§5).

**Estimated effort:** 2-3 days. Phase 1 (MVP) is ~1 day. Phase 2 (feedback loop) is ~1-2 days.

---

## 2. Evidence

### Observation

After establishing a clean scholarship-only baseline, coverage dropped from 796 to 245 confirmed films:

| Tier | Before | After | Change |
|---|---|---|---|
| Core | 136 | 119 | −17 to staging |
| Reference | 38 | 21 | −17 to staging |
| Satellite | 506 | 100 | −406 to staging |
| Popcorn | 116 | 5 | −111 to staging |
| **Confirmed** | **796** | **245** | |
| **Unsorted (incl. staging)** | **280** | **831** | +551 |

Satellite corpus coverage by category shows the gap is not matching failure — it's coverage:

| Category | In Library | Corpus Size | Coverage |
|---|---|---|---|
| American Exploitation | 24/24 | 24 | 100% |
| Blaxploitation | 9/9 | 9 | 100% |
| Giallo | 2/41 | 41 | 5% |
| Pinku Eiga | 2/22 | 22 | 9% |
| French New Wave | 3/31 | 31 | 10% |

Giallo has 41 canonical films in its corpus but only 2 of 24 library films match — because the corpus lists scholarly exemplars, not the broader population of films that belong in the category.

### Data

The pipeline's resolve chain:
- P1 `explicit_lookup`: ~400 SORTING_DATABASE entries → precision match
- P2 `corpus_lookup`: 338 scholarship films → precision match
- P3 `reference_canon`: 50 films → precision match
- P4 `two_signal`: binary gates → **precision tool doing reasoning work** ← ROOT CAUSE
- P5 `popcorn`: threshold check → precision match
- P6 `user_tag`: tag recovery → precision match
- P7 `unsorted`: fallback

P1-P3 and P5-P6 are legitimate precision operations. P4 is the violation.

---

## 3. Root Cause Analysis

### RC-1: R/P Split Violation — reasoning task assigned to code

**Location:** `lib/signals.py` → `score_structure()`, `integrate_signals()` + `lib/satellite.py` → `classify_structural()`

**Mechanism:** Film classification is inherently interpretive. "Does this 1972 Italian thriller belong in Giallo?" requires judgment about genre conventions, historical context, and movement boundaries. The pipeline treats this as a precision task: `country=IT AND decade=1970s AND genre∈{Horror,Thriller} → Giallo`. This works for canonical exemplars (which is why the corpora work) but fails for the broader population where data is incomplete, genre labels are ambiguous, or films sit at movement boundaries.

**Theoretical basis:** `exports/knowledge-base/llm-capability-model.md` — LLMs excel at classification, interpretation, and judgment (reasoning tasks). Code excels at exact matching, formatting, and verification (precision tasks). The current pipeline inverts this.

### RC-2: Binary gates destroy evidence

**Location:** `lib/satellite.py` → `classify_structural()` — `continue` statement on first gate failure

**Mechanism:** When a film has `country=IT, decade=1970s, genres=[]`, the Giallo genre gate fails (empty genres ≠ Horror/Thriller). The `continue` discards the country + decade evidence entirely. Dempster-Shafer theory (`docs/theory/THEORETICAL_GROUNDING.md` §9) predicts this exact failure: absent evidence (no genres) is treated as negative evidence (wrong genres). An LLM given the same context would recognise: "Italian film from the 1970s, genre data missing — likely Giallo or possibly European Sexploitation, needs genre context to disambiguate."

### RC-3: Context isolation prevents reasoning

**Location:** `classify.py` → resolve chain is sequential and blind

**Mechanism:** Each resolver sees only its own inputs. The LLM pass would see everything: film metadata, all candidate categories with their corpus exemplars, gate evidence (what passed, what failed, what was untestable), and accumulated run context (stigmergy — `docs/theory/THEORETICAL_GROUNDING.md` §10). This is the blackboard architecture (`THEORETICAL_GROUNDING.md` §11): multiple knowledge sources contributing to a shared workspace.

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| Enrichment → LLM Resolver | `classify.py:_merge_api_results()` | New `_resolve_llm()` | Yes — new resolver |
| LLM Resolver → Result Builder | New `_resolve_llm()` | `classify.py:_build_result()` | No — returns `Resolution` (Issue #54 L3 contract) |
| Corpora → LLM Context | `data/corpora/*.csv` | New `_build_llm_context()` | Yes — corpora become context, not just lookup |
| LLM Output → Verification | LLM response | New `_verify_llm_output()` | Yes — new verification step |

**Gate impact:** New resolver slots into existing resolve chain at P4.5 (after two-signal, before popcorn). Two-signal (P4) remains as a fast $0 precision path; LLM fires only for films that reach `unsorted_no_match`.

**Downstream consumers of changed output:**
- `move.py` reads `destination` from manifest — no change (LLM resolver produces same `Resolution` type)
- `scripts/reaudit.py` reads `reason` code — new reason code `llm_classification` added
- `output/sorting_manifest.csv` — new reason code appears in output
- `dashboard.py` — new reason code in signal health display

---

## 5. Proposed Fix

### Design Principles (Governance Chain)

**L1 — Theory (Film Scholarship):**
- Classification is interpretive judgment grounded in film-historical knowledge (Bourdieu's modes of engagement, Altman's genre theory, Sarris's auteur tiers)
- Scholarship provides the criteria; an informed agent applies them
- The corpora are exemplars that define "what films in this category look like" — context for judgment, not exhaustive lookup tables

**L2 — Architecture (Context → Reasoning → Verification):**
- `llm-capability-model.md`: LLMs excel at classification, interpretation, judgment
- The three-step pattern: CODE prepares context ($0) → LLM reasons ($$$) → CODE verifies ($0)
- Blackboard model: LLM sees all accumulated evidence, not just one stage's output
- R/P Split: reasoning and precision are never mixed in one step

**L3 — Components (Typed Contracts):**
- LLM resolver returns `Resolution` (Issue #54 L3 contract) — same as every other resolver
- Prompt template is a typed component: `LLMClassificationContext` dataclass
- Verification is a typed component: `_verify_llm_output()` checks against allowed categories, decades, tiers
- LLM is called through a defined interface, not raw API calls

**L4 — Dev Rules:**
- **MVP-First:** Phase 1 classifies Satellite films only (largest pool, best-defined categories). Core/Reference/Popcorn deferred.
- **Import-Don't-Rebuild:** Use existing `Resolution` type, existing `CorpusLookup` for context, existing `EnrichedFilm` for input
- **Handoff composition > individual complexity:** LLM resolver is one simple step in the existing chain, not a replacement for the chain
- **Fix at highest divergent level:** This is an L2 fix (architecture — who does reasoning?) not an L5 fix (code — better regex)
- **Prototype Building (Rule 8):** Start with one real film, one real classification. Build prompt from concrete case before abstracting

### Context → Reasoning → Verification Architecture

```
CONTEXT (Code, $0):
├── Film metadata (title, year, director, country, genres)
├── API enrichment data (TMDb/OMDb overview, keywords, plot)
├── Gate evidence from two-signal pass (which gates passed/failed/untestable)
├── Top 3 candidate categories with corpus exemplars (5 films each)
└── Category definitions (decade bounds, key directors, country associations)

REASONING (LLM, $$$):
├── Input: structured context above
├── Task: "Which category does this film belong in? Or is it unsorted?"
├── Output: { category, tier, confidence, reasoning }
└── Constraint: must pick from allowed categories or explicitly decline

VERIFICATION (Code, $0):
├── Category is in SATELLITE_ROUTING_RULES or known tier
├── Decade bounds are valid for chosen category
├── Confidence is in [0.0, 1.0]
├── Destination path is well-formed
└── If verification fails → unsorted_llm_unverified
```

### Execution Order

1. **Step 1:** Create `lib/llm_resolver.py` — LLM context builder + prompt template + output parser

   - `LLMClassificationContext` dataclass: film metadata, gate evidence, candidate categories with exemplars
   - `build_context(enriched: EnrichedFilm, gate_evidence: dict, corpus: CorpusLookup) → LLMClassificationContext` — CODE step, assembles all evidence
   - `format_prompt(ctx: LLMClassificationContext) → str` — renders context into structured prompt
   - `parse_response(response: str) → Optional[Resolution]` — CODE step, extracts structured classification from LLM output
   - `verify_output(resolution: Resolution) → bool` — CODE step, validates category/decade/tier against allowed values
   - **Verify:** `pytest tests/test_llm_resolver.py -v` (unit tests with mocked LLM responses)

2. **Step 2:** Create `lib/llm_client.py` — thin API wrapper

   - Single function: `classify_film(prompt: str, model: str = "claude-haiku-4-5-20251001") → str`
   - Uses Anthropic SDK (already a project dependency pattern)
   - Handles: API key from config.yaml, rate limiting, error handling, cost tracking
   - **No reasoning logic** — this is a precision wrapper. Prompt construction and output parsing are in `lib/llm_resolver.py`
   - **Verify:** manual test with one film

3. **Step 3:** Add `_resolve_llm()` to `classify.py`

   - Slots into resolve chain between `_resolve_two_signal` (P4) and `_resolve_popcorn` (P5)
   - **Only fires for films that reached `unsorted_no_match`** — the 551 staging films
   - Returns `Resolution` with reason code `llm_classification`
   - Confidence: LLM-provided, capped at 0.75 (below corpus 1.0, above review_flagged 0.4)
   - **Verify:** `python classify.py <source_directory>` — check that previously-unsorted films now classify

4. **Step 4:** Build the prompt template

   The prompt is the L3 component that bridges L1 theory and L5 code. It must encode:
   - **Category definitions** from scholarship (not invented — imported from `SATELLITE_ROUTING_RULES` + `docs/SATELLITE_CATEGORIES.md`)
   - **Corpus exemplars** as reference points ("films like these belong in this category")
   - **Decision criteria** from tier architecture ("Core = auteur identity, Reference = canonical achievement, Satellite = movement membership, Popcorn = mainstream pleasure")
   - **Explicit uncertainty option** ("If you cannot confidently classify this film, say so")

   Template structure:
   ```
   You are classifying a film into a library organised by film-historical scholarship.

   FILM:
   {title} ({year}) dir. {director}
   Country: {country} | Genres: {genres}
   Plot: {overview}

   CANDIDATE CATEGORIES (ranked by structural evidence):
   1. {category_1}: {definition}. Exemplars: {corpus_sample_1}
      Evidence: {gate_evidence_1}
   2. {category_2}: ...
   3. {category_3}: ...

   TIER DEFINITIONS:
   - Core: auteur filmography (director on Core whitelist)
   - Reference: canonical film by non-Core director
   - Satellite: belongs to a named historical film movement
   - Popcorn: mainstream entertainment

   Based on the film's metadata and the category definitions above,
   classify this film. Respond with:
   - category: [category name or "unsorted"]
   - tier: [Core/Reference/Satellite/Popcorn/Unsorted]
   - confidence: [0.0-1.0]
   - reasoning: [1-2 sentences grounding your decision in the category definition]
   ```

   - **Verify:** Test with 5 known films from staging (films you know the correct answer for)

5. **Step 5:** Add `anthropic_api_key` to `config.yaml` schema

   - **Verify:** `python classify.py <source>` loads key without error

6. **Step 6:** Add `--llm` flag to `classify.py` CLI

   - LLM pass is **opt-in** (costs money). Default pipeline behaviour unchanged.
   - `python classify.py <source> --llm` enables the LLM resolver
   - Without `--llm`, P4 two-signal remains terminal for heuristic classification
   - **Verify:** `python classify.py <source>` (no flag) produces identical output to current

7. **Step 7:** Add cost tracking and batch control

   - Log per-film LLM cost (input tokens × rate + output tokens × rate)
   - Log cumulative run cost
   - `--llm-limit N` flag: stop LLM calls after N films (budget control)
   - `--llm-batch N` flag: process N films at a time with confirmation prompt
   - **Verify:** Run on 10 films, check cost log

8. **Step 8:** Write tests

   - `tests/test_llm_resolver.py`:
     - `test_build_context_includes_all_evidence` — context has metadata + gates + exemplars
     - `test_format_prompt_encodes_categories` — prompt contains category definitions
     - `test_parse_response_valid` — well-formed LLM output → Resolution
     - `test_parse_response_malformed` — bad output → None (falls through to unsorted)
     - `test_verify_output_rejects_invalid_category` — made-up category → rejected
     - `test_verify_output_rejects_invalid_decade` — decade outside category bounds → rejected
     - `test_resolve_llm_skips_already_classified` — films with P1-P4 resolution don't trigger LLM
   - **Verify:** `pytest tests/test_llm_resolver.py -v`

9. **Step 9:** Update documentation

   - `CLAUDE.md` §2 — add LLM resolver to resolve chain diagram
   - `CLAUDE.md` §5 — add `--llm` command documentation
   - `docs/DEVELOPER_GUIDE.md` — add LLM resolver to component table
   - `docs/WORKFLOW_REGISTRY.md` — add WF-LLM-CLASSIFY procedure
   - **Verify:** grep for outdated resolve chain references

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `lib/llm_resolver.py` | **Create** | Context builder, prompt template, output parser, verifier |
| `lib/llm_client.py` | **Create** | Thin Anthropic API wrapper |
| `classify.py` | Modify | Add `_resolve_llm()`, `--llm` CLI flag, cost tracking |
| `config.yaml` | Modify | Add `anthropic_api_key` field |
| `tests/test_llm_resolver.py` | **Create** | Unit tests for LLM resolver components |
| `CLAUDE.md` | Update | §2 resolve chain, §5 commands |
| `docs/DEVELOPER_GUIDE.md` | Update | Component table |
| `docs/WORKFLOW_REGISTRY.md` | Update | New workflow entry |

---

## 6. Scope Boundaries

**In scope:**
- LLM resolver for Satellite classification (14 categories with scholarship-defined boundaries)
- Context builder that assembles enrichment data + gate evidence + corpus exemplars
- Verification layer that validates LLM output against allowed categories/decades
- Opt-in `--llm` flag with cost controls
- Core whitelist check (already P3) — LLM confirms Core-eligible directors
- Reference canon check (already P3) — LLM confirms canonical status

**NOT in scope:**
- Popcorn classification via LLM — Popcorn is negative-space (not a named movement), LLM would need different criteria. Deferred.
- Automated SORTING_DATABASE updates from LLM results — human curation principle. LLM suggests, human commits.
- Multi-turn LLM reasoning — MVP is single prompt per film. Iterative disambiguation deferred.
- Fine-tuning or custom model — use general-purpose Claude with good context
- Stigmergy / within-run learning — Phase 2 stretch goal, not MVP
- Replacing the existing resolve chain — LLM is additive (new P4.5 resolver), not a replacement

**Deferred to:** Future issue for Popcorn LLM classification and within-run base rates.

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Confirmed total | 245 | 400+ (conservative) | `python classify.py <source> --llm` |
| Satellite classified | 100 | 300+ | manifest reason code counts |
| Unsorted (staging) | 831 | <500 | manifest unsorted count |
| LLM accuracy | N/A | >80% on spot-check | manual review of 20 LLM classifications |
| Cost per film | N/A | ~$0.001 (Haiku) | cost log output |
| Total run cost | N/A | <$1 for 551 films | cost log output |

**Pin baseline before implementing:**
```bash
git tag pre-issue-057
python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted > output/pre-057-manifest.txt
```

---

## 8. Validation Sequence

```bash
# Step 1: Run full test suite (existing tests unaffected)
pytest tests/ -v

# Step 2: Run without --llm flag (identical to current behaviour)
python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted
diff output/sorting_manifest.csv output/pre-057-manifest.csv  # should be identical

# Step 3: Run with --llm on small batch
python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted --llm --llm-limit 10

# Step 4: Spot-check 10 LLM classifications manually
# Verify: category makes sense, reasoning cites scholarship criteria, decade is valid

# Step 5: Run full LLM pass
python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted --llm

# Step 6: Reaudit with new classifications
python audit.py && python scripts/reaudit.py
```

**Expected results:**
- Step 1: All tests pass (0 failures, 1 skipped allowed)
- Step 2: Zero diff — no behavioural change without flag
- Step 3: 10 films classified, cost logged, all pass verification
- Step 4: ≥8/10 correct (80% accuracy floor)
- Step 5: 300+ films classified from staging pool
- Step 6: No regressions in corpus-confirmed films

**If any step fails:** Stop. Do not proceed. Report the failure output.

---

## 9. Rollback Plan

**Detection:** LLM classifications produce wrong_category or wrong_tier at >20% rate in reaudit; or cost exceeds $5 per run; or LLM returns hallucinated categories not in SATELLITE_ROUTING_RULES.

**Recovery:**
```bash
git revert [commit-hash]
# LLM resolver is opt-in (--llm flag), so removing it has zero impact on default behaviour
# No cache invalidation needed — LLM results are in manifest only, not cached
```

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-057
```

---

## 10. Theory & Architecture Grounding

### L1 — Film Scholarship Theory

**Bourdieu (Distinction, 1979):** The four tiers encode four modes of engaging with cinema — identity (Core), interest (Satellite), pleasure (Popcorn), acknowledgment (Reference). These are interpretive categories requiring judgment, not mechanical sorting rules. A binary gate cannot determine whether a film represents "identity-based auteur engagement" — that's a reasoning task.

**Altman (Film/Genre, 1999):** Genre is not a fixed property of a film but a social construction negotiated between industry, critics, and audiences. A 1973 Italian thriller is "Giallo" not because it mechanically satisfies country+decade+genre gates, but because it participates in a historically situated production/reception context. LLM reasoning with corpus exemplars can assess this participation; binary gates cannot.

**Sarris (The American Cinema, 1968):** Auteur classification is inherently evaluative — Sarris ranked directors into tiers based on critical judgment, not measurable properties. The Core whitelist imports Sarris's method; the LLM pass extends it to films outside the whitelist.

**Dempster-Shafer (A Mathematical Theory of Evidence, 1976):** Three-state evidence (belief/disbelief/uncertainty) replaces binary gates. The LLM naturally handles uncertainty: "Italian, 1970s, no genre data → probably Giallo based on corpus similarity, but could be European Sexploitation." Code gates collapse this to `False`.

### L2 — Architecture

**Context → Reasoning → Verification** (`exports/knowledge-base/llm-capability-model.md`):
- CODE assembles context (film metadata + gate evidence + corpus exemplars) — precision, $0
- LLM reasons about context (which category?) — reasoning, $$$
- CODE verifies output (valid category? valid decade? well-formed?) — precision, $0

**Blackboard Architecture** (`docs/theory/THEORETICAL_GROUNDING.md` §11):
- LLM sees all evidence in a shared workspace, not sequential blind pipeline
- Context includes what two-signal found, what gates passed/failed/were untestable

**R/P Split** (`exports/skills/rp-split.md`):
- Classification = REASONING (multiple valid answers, qualitative evaluation)
- File movement = PRECISION (one correct path, binary success/failure)
- These must never be mixed in one step

### L3 — Components

- `Resolution` dataclass (`lib/pipeline_types.py`) — all resolvers return this type
- `EnrichedFilm` dataclass (`lib/pipeline_types.py`) — enrichment stage output
- `LLMClassificationContext` dataclass (new) — typed input to prompt builder
- `_verify_llm_output()` function (new) — typed verification gate

### L4 — Dev Rules

- **MVP-First:** Satellite only, single prompt, Haiku model. Complexity through composition later.
- **Import-Don't-Rebuild:** Uses existing `Resolution`, `EnrichedFilm`, `CorpusLookup`, `SATELLITE_ROUTING_RULES`
- **Prototype Building (Rule 8):** Start with one known film, build prompt from concrete case
- **Failure Gates (Rule 3):** LLM failure → `unsorted_llm_unverified`, not silent fallthrough
- **Measurement-Driven (Rule 7):** Spot-check accuracy on known films before full run
- **Curation Loop (Rule 12):** LLM classifications are suggestions until curator confirms via `move.py --execute`

### Related issues

- #54 — Governance chain pipeline consolidation (provides `Resolution` L3 contract this issue imports)
- #55 — Doc-routing consolidation (provides `Reference` and `Popcorn` standalone resolvers)
- #56 — Canonical governance chain model (diagnosed the L1→L5 gaps this issue fixes; superseded)
- #38 — Layer 1 Ground Truth Corpora (provides the corpus exemplars used as LLM context)
- #42 — Two-Signal Architecture (provides gate evidence used as LLM context)

---

## Section Checklist

- [x] §1 Manager Summary is readable without code knowledge
- [x] §3 Root causes reference specific files and functions
- [x] §4 ALL downstream consumers are listed
- [x] §5 Execution Order has verify commands for each step
- [x] §5 Files to Modify is complete
- [x] §6 NOT in scope is populated
- [x] §7 Measurement Story has concrete before/after numbers
- [x] §8 Validation Sequence commands are copy-pasteable
- [x] §9 Baseline is pinned before implementation starts
- [x] §10 Theory grounding exists at all 4 governance levels (L1-L4)
