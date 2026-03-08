# Issue #52: Unify Normalisation with Classification Pipeline

| Field | Value |
|---|---|
| Status | COMPLETE |
| Priority | P2-High |
| Date Opened | 2026-03-08 |
| Date Completed | 2026-03-08 |
| Component | Normaliser / Parser / API Enrichment |
| Change Type | Refactor + Feature |
| Supersedes | Issue #18 (partially — standalone normalize.py still exists) |

---

## 1. Manager Summary

**Problem:** Three independent normalisation systems existed with no shared token list or coordination. The normaliser (`lib/normalizer.py`) predated the two-signal architecture and operated as an external script that renamed files on disk. Information was lost at the filesystem boundary — the normaliser's analysis was discarded and the classifier re-derived everything from scratch. 106 R1 films entered routing with no data because dirty titles produced failed API queries, but the system had no mechanism to try again.

**Impact if unfixed:** R1 films (106) permanently stuck as unsorted — the pipeline measures their readiness but cannot improve it. Classification rate stays at 1.9%. Each normalisation system drifts independently — tokens added to one don't appear in the others.

**Risk if fixed wrong:** Parser title cleaning uses token-boundary regex in space-separated titles. Tokens safe in dot-separated filenames (like `theatrical`, `doc`, `por`) can truncate film titles when added to the parser's token list. Non-ASCII word boundary failures cause 3-letter language codes to match inside words (e.g., `por` inside `zápor`).

---

## 2. Evidence

### Observation
Three normalisation systems with independent hardcoded token lists:
- `lib/normalizer.py` — 78 hardcoded tokens in `_JUNK_TOKENS`
- `lib/parser.py` `_clean_title()` — uses `RELEASE_TAGS` from constants
- `classify.py._clean_title_for_api()` — additional ad-hoc residual patterns

106 films assessed as R1 (title+year, no director/country from API). Many have subtitle-contaminated titles that produce failed API queries.

### Data
- R1 population: 106 films (pre-fix)
- Classification rate: 1.9% (7/365 films classified from Unsorted)
- `_JUNK_TOKENS` overlap with `RELEASE_TAGS`: ~60%. Unique to normaliser: ~25 tokens. Missing from normaliser: ~15 tokens.

---

## 3. Root Cause Analysis

### RC-1: No shared token list
**Location:** `lib/normalizer.py` lines 20-78 (hardcoded `_JUNK_TOKENS`), `lib/constants.py` (`RELEASE_TAGS`)
**Mechanism:** Normaliser and parser each maintained independent lists. Tokens added to RELEASE_TAGS after the normaliser was built never appeared in the normaliser.

### RC-2: Filesystem boundary loses information
**Location:** `normalize.py` writes `rename_manifest.csv` → `classify.py` reads renamed files
**Mechanism:** The normaliser's analysis (what it stripped, what type of cleaning) was lost at the filesystem boundary. The classifier re-derived everything using its own token lists.

### RC-3: No CLASSIFY→GATHER feedback
**Location:** `classify.py` `_assess_readiness()` and `classify()` method
**Mechanism:** R1 films were measured but not promoted. The system reported "this film has no data" but never tried alternative query strategies (shorter title, subtitle truncation).

### RC-4: Token context safety
**Location:** `lib/parser.py` `_clean_title()` regex patterns
**Mechanism:** The parser uses `(?<![a-zA-Z0-9])tag(?![a-zA-Z0-9])` boundaries (ASCII-only). Tokens like `theatrical` appear in title strings ("Theatrical Cut" → truncated to ""). Language codes like `por` match inside non-ASCII words (`zápor` → `zá`). These tokens cannot safely go in `RELEASE_TAGS`.

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| Normaliser → Parser | `lib/normalizer.py:normalize()` | `lib/parser.py:parse()` | Yes — now called in-memory, not via filesystem |
| Parser → API query | `classify.py:_clean_title_for_api()` | `lib/tmdb.py`, `lib/omdb.py` | Yes — simplified, residual patterns removed |
| API result → Readiness | `classify.py:_merge_api_results()` | `classify.py:_assess_readiness()` | No |
| Readiness → Routing | `classify.py:_assess_readiness()` | `classify.py:classify()` | Yes — R1 promotion added between assessment and routing |

**Downstream consumers of changed output:**
- `move.py` reads `source_path` from manifest — `metadata.filename` changed from basename to relative path (fixes subdirectory files)
- `output/staging_report.txt` — new "DATA QUALITY FEEDBACK" section added

---

## 5. Proposed Fix

### Fix Description
Integrate normaliser as Stage 0 inside classify.py, unify token lists in constants.py with a two-list architecture (parser-safe vs normaliser-only), add R1 promotion via subtitle truncation, add data quality feedback to staging report.

### Execution Order

1. **Step 1:** Expand `RELEASE_TAGS` in `lib/constants.py` with parser-safe tokens from normaliser's list. Create `DOT_SEPARATOR_TAGS` for normaliser-only tokens.
   - **Verify:** `pytest tests/ -v`

2. **Step 2:** Update `lib/normalizer.py` — derive `_JUNK_TOKENS` from `RELEASE_TAGS | DOT_SEPARATOR_TAGS` instead of hardcoded list.
   - **Depends on:** Step 1
   - **Verify:** `pytest tests/test_normalizer.py -v`

3. **Step 3:** Add Stage 0 to `classify.py` `process_directory()` — call `normalizer.normalize()` before `parser.parse()`.
   - **Depends on:** Steps 1-2
   - **Verify:** `python classify.py <source> && diff manifests`

4. **Step 4:** Simplify `classify.py._clean_title_for_api()` — remove residual patterns absorbed into expanded RELEASE_TAGS.
   - **Depends on:** Step 1
   - **Verify:** `pytest tests/ -v`

5. **Step 5:** Add `_attempt_r1_promotion()` to `classify.py` — subtitle truncation for R1 films.
   - **Depends on:** Step 3
   - **Verify:** Run classify, check R1 count dropped and promotions are correct

6. **Step 6:** Add data quality feedback section to `write_staging_report()`.
   - **Depends on:** Step 5
   - **Verify:** Check `output/staging_report.txt` for DATA QUALITY FEEDBACK section

7. **Step 7:** Update documentation — RECURSIVE_CURATION_MODEL §2a, CURATOR_WORKFLOW, DEVELOPER_GUIDE, WORK_ROUTER, CORE_DOCUMENTATION_INDEX, Issue #18.
   - **Verify:** All docs reference Stage 0, token lists, R1 promotion

### Files Modified

| File | Change Type | What Changed |
|---|---|---|
| `lib/constants.py` | Modify | `RELEASE_TAGS` expanded; new `DOT_SEPARATOR_TAGS` |
| `lib/normalizer.py` | Modify | `_JUNK_TOKENS` derived from constants instead of hardcoded |
| `classify.py` | Modify | Stage 0 integration, `_clean_title_for_api()` simplified, `_attempt_r1_promotion()` added, staging report feedback |
| `docs/architecture/RECURSIVE_CURATION_MODEL.md` | Update | §2a expanded with exploration findings |
| `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` | Update | §1a data quality dependency added |
| `docs/DEVELOPER_GUIDE.md` | Update | Dependency chain fixed |
| `docs/WORK_ROUTER.md` | Update | Normaliser in component table + data flow |
| `docs/CORE_DOCUMENTATION_INDEX.md` | Update | Normalizer entries added |
| `docs/CURATOR_WORKFLOW.md` | Update | Phase 0/0.5 expanded |
| `issues/018-*.md` | Update | Marked partially superseded |

---

## 6. Scope Boundaries

**In scope:**
- Unify token lists (RELEASE_TAGS + DOT_SEPARATOR_TAGS)
- Integrate normaliser as Stage 0 in classify.py
- R1 promotion via subtitle truncation
- Data quality feedback in staging report
- Documentation updates

**NOT in scope:**
- Merging `lib/normalizer.py` with `lib/normalization.py` (different purposes — filename cleaning vs lookup normalisation)
- Removing standalone `normalize.py` (still useful for optional batch renames)
- Changing the normaliser's cleaning logic (only changing where it gets its token list)
- R0 promotion (no-year films need structural changes, not title cleaning)

---

## 7. Measurement Story

| Metric | Before | After | Status |
|---|---|---|---|
| R1 count | 106 | 93 | Improved (13 promoted) |
| R3 count | 68 | 80 | Improved |
| Classification rate | 1.9% (7/365) | 3.0% (11/365) | Improved |
| New correct classifications | — | 4 (Alphaville→FNW, A Mulher→BrazExploit, Gendai koshoku-den→PinkuEiga, Rumble→HKAction) | Improved |
| Test suite | 373 passed, 1 skipped | 373 passed, 1 skipped | Stable |
| Manifest regressions | — | 0 (1 improvement: "Remux" properly stripped) | No regressions |

---

## 8. Validation Sequence

```bash
# Step 1: Run full test suite
pytest tests/ -v

# Step 2: Classify and compare manifests
python classify.py /Volumes/One\ Touch/Movies/Organized/Unsorted
diff output/sorting_manifest.csv output/sorting_manifest_baseline.csv

# Step 3: Check staging report for DATA QUALITY FEEDBACK
tail -30 output/staging_report.txt

# Step 4: Verify R1 promotions are correct
grep "R1.*promoted" output/staging_report.txt
```

---

## 9. Rollback Plan

**Detection:** R1 promotions produce false matches (wrong film matched to title prefix). Test regressions in parser title cleaning.

**Recovery:**
```bash
git revert [commit-hash]
python scripts/invalidate_null_cache.py conservative
```

---

## 10. Theory & Architecture Grounding

**Methodology basis:**
- `CLAUDE.md` Rule 1 (R/P Split) — normalisation is PRECISION, routing is REASONING
- `CLAUDE.md` Rule 5 (Constraint Gates) — normalisation is the binding constraint upstream of all signals
- `CLAUDE.md` Rule 10 (Data Readiness) — R1 promotion closes the CLASSIFY→GATHER feedback loop

**Architecture reference:**
- `docs/architecture/RECURSIVE_CURATION_MODEL.md` §2a — data quality → signal quality → route quality
- `docs/architecture/TWO_SIGNAL_ARCHITECTURE.md` §1a — both signals depend on upstream data quality

**Related issues:**
- #18 — partially superseded (standalone normalize.py remains; Stage 0 integration is new)
- #42 — two-signal architecture that Issue #52's data quality work supports
