# Issue #53: Corpus-Gated Category Addition Workflow

| Field | Value |
|---|---|
| Status | OPEN |
| Priority | P2-High |
| Date Opened | 2026-03-08 |
| Component | Corpus / Satellite / Infrastructure |
| Change Type | Feature + Infrastructure |
| Estimated Effort | 2–3 days (phased: tooling first, then per-category implementation) |
| Blocked By | None |
| Blocks | New category implementations (New Latin American Cinema, Korean New Wave, Chinese Art Cinema, Czech New Wave) |
| Supersedes | None |

---

## 1. Manager Summary

**Problem:** The system has no formal gate between "we think a new Satellite category exists" (discovery) and "we write routing rules for it" (implementation). Issue #51 removed catch-all categories, exposing 140 unroutable films. Investigation #52 identified 4 candidate movements — but the scholarship citations in that investigation were recalled from AI training data, not verified against the cited sources. Director lists and film-to-movement assignments are plausible but unconfirmed.

**Impact if unfixed:** New categories get added based on AI-generated scholarship claims rather than curator-verified sources. Director rosters may include wrong directors (e.g., Investigation #52 lists "El Romance Del Aniceto Y La Francisca" as directed by Leonardo Favio; cache data says Jorge Briand). Without a verification gate, these errors propagate into routing rules and produce systematic misclassification.

**Risk if fixed wrong:** Over-engineering the gate so that it blocks legitimate category additions indefinitely. The gate must be cheap enough that it doesn't become a bottleneck — the existing `build_corpus.py` tooling is the right weight.

**Estimated effort:** ~4 hours for the workflow formalization and tooling additions; per-category corpus building is curator time (30–60 min per category with scholarship in hand).

---

## 2. Evidence

### Observation

Investigation #52 (`docs/issues/INVESTIGATION_052_NEW_CATEGORIES.md`) identified 4 new Satellite category candidates from the 140 films made unroutable by Issue #51. The investigation followed Rule 4 (Domain Grounding) and the Add protocol (density + coherence + archival necessity). It cited published scholarship for each candidate:

| Candidate | Films | Cited Sources |
|---|---|---|
| New Latin American Cinema | 14 | Martin (1997), Burton (1986), King (2000), López (1992) |
| Korean New Wave | 5 | Shin & Stringer (2005), Paquet (2009), Kim (2004) |
| Chinese Art Cinema | 5 | Berry & Farquhar (2006), McGrath (2008), Lu (1997), Zhang (2004) |
| Czech New Wave | 3 | Hames (2009), Owen (2011) |

It correctly rejected a 5th candidate (New Japanese Cinema, 9 films) as incoherent — a residual, not a movement.

### Data — Cache Cross-Check (Session 2026-03-08)

Cross-checking the investigation's film lists against TMDb/OMDb caches revealed:

**New Latin American Cinema (14 films):**
- 13/14 found in caches; countries confirmed (AR, MX, CU, BR)
- **Director discrepancy:** "El Romance Del Aniceto Y La Francisca" (1967) — investigation says Leonardo Favio, cache says Jorge Briand (Briand was cinematographer; Favio directed — but which is correct requires the source, not the cache)
- 1 film (El Esqueleto De La Señora Morales) has no cache data

**Korean New Wave (5 films):**
- 3/5 in caches (The Quiet Family, Old Boy, The Good the Bad the Weird)
- 2/5 missing (Save the Green Planet, I'm A Cyborg But That's OK) — likely cached under different title romanizations

**Chinese Art Cinema (5 films):**
- **Only 1/5 in caches** (Farewell My Concubine). Raise the Red Lantern, Platform, Mountains May Depart, Long Day's Journey Into Night all missing — likely cached under Chinese-language titles or transliteration variants
- This category fails basic data readiness (Rule 10) for automated routing

**Czech New Wave (3 films):**
- All 3 in caches, clean country data (CS, XC)
- Thin density — investigation correctly flagged as Tier 4 only

### The Verification Gap

The investigation document is a valid **Discovery output** (Rule 9). The scholarship citations are real published works. But:

1. The citations were recalled from AI training data, not looked up from the books
2. No per-film verification: which of the 14 Latin American films actually appear in Martin (1997)?
3. Director rosters are AI-inferred, not extracted from the scholarship's filmographies
4. The investigation itself has no mechanism to distinguish "film in the movement's scholarship" from "film that shares a country and decade with the movement"

This is the gap the corpus gate fills.

---

## 3. Root Cause Analysis

### RC-1: No hard gate between discovery and implementation for new categories

**Location:** Process gap — no code location. The Add protocol is documented in `docs/theory/REFINEMENT_AND_EMERGENCE.md` §2–4 and `CLAUDE.md` Rule 4, but the protocol's "verify scholarship" step has no enforced artifact.

**Mechanism:** The designed workflow is: cohort analysis → investigation → category spec → implementation. But the investigation-to-spec handoff has no checkpoint. An investigation can claim "grounded in Hames (2009)" without producing evidence that specific films or directors appear in Hames. The spec author (human or AI) can proceed to routing rules with unverified claims.

### RC-2: Existing corpus tooling not wired into category addition workflow

**Location:** `scripts/build_corpus.py`, `lib/corpus.py`, `docs/WORK_ROUTER.md` §"Add a new satellite category"

**Mechanism:** The corpus infrastructure (Issue #38) exists and works — Giallo has 41 entries with source citations (Koven 2006, Lucas 2007). But `WORK_ROUTER.md` §"Add a new satellite category" doesn't mention corpus building as a prerequisite. The 5-step process goes straight from "Define the category in SATELLITE_CATEGORIES.md" to "Add the country→category mapping to lib/constants.py". No scholarship verification step.

### RC-3: CATEGORY_ALIASES in build_corpus.py doesn't include new categories

**Location:** `scripts/build_corpus.py:94-113` → `CATEGORY_ALIASES`

**Mechanism:** The alias dict is hardcoded to the 17 categories that existed at Issue #38. New categories (New Latin American Cinema, Korean New Wave, etc.) would need to be added before `--audit` or `--add` works for them. Minor but blocks the workflow test.

---

## 4. Affected Handoffs

| Boundary | Upstream Producer | Downstream Consumer | Contract Change? |
|---|---|---|---|
| Investigation → Corpus | `docs/issues/INVESTIGATION_052_*.md` | `data/corpora/{category}.csv` | Yes — new mandatory handoff |
| Corpus → Routing Rules | `data/corpora/{category}.csv` | `lib/constants.py SATELLITE_ROUTING_RULES` | Yes — corpus existence becomes a prerequisite |
| Corpus → Classifier | `lib/corpus.py CorpusLookup` | `classify.py` Stage 2 (corpus_lookup) | No — existing contract, just new CSV files |

**Gate impact:** Adds a hard gate: no new entry in `SATELLITE_ROUTING_RULES` without a corresponding `data/corpora/{category}.csv` containing ≥3 entries with non-empty `source` citations.

**Downstream consumers of changed output:**
- `lib/corpus.py` — reads new corpus CSVs at classification time (existing contract, no change)
- `scripts/build_corpus.py --audit` — reads new CSVs for anomaly detection (existing contract, needs CATEGORY_ALIASES update)
- `classify.py` — corpus_lookup fires before heuristic routing (existing contract, no change)
- `WORK_ROUTER.md` — process documentation must be updated
- `docs/CURATOR_WORKFLOW.md` — curator workflow must include corpus step

---

## 5. Proposed Fix

### Fix Description

Formalize the corpus-gated category addition workflow. The existing `build_corpus.py` + `lib/corpus.py` infrastructure (Issue #38) already implements the right artifact — a CSV with title, year, director, canonical_tier, **source citation**, and notes. The fix wires this into the category addition process as a hard gate: no routing rules without a verified corpus.

### Execution Order

**Phase A: Workflow formalization (tooling + documentation)**

1. **Step 1:** Update `scripts/build_corpus.py` — add CATEGORY_ALIASES for new categories
   - **What to change:** Add aliases for `'new latin american cinema'`, `'korean new wave'`, `'chinese art cinema'`, `'czech new wave'` to `CATEGORY_ALIASES` dict
   - **Verify:** `python scripts/build_corpus.py --audit "New Latin American Cinema"` runs without alias error (will fail on "no films in folder" — expected, category doesn't exist yet)

2. **Step 2:** Update `docs/WORK_ROUTER.md` § "Add a new satellite category" — insert corpus gate
   - **What to change:** Add Step 0 (build corpus from scholarship) before the current Step 1. Add hard gate language: "Do not proceed to Step 1 without ≥3 corpus entries with source citations."
   - **Verify:** Read the updated section; workflow now has 6 steps with corpus gate first

3. **Step 3:** Update `docs/CURATOR_WORKFLOW.md` — add corpus verification phase
   - **What to change:** Add Phase B3.5 (or equivalent) for corpus building between investigation and category spec
   - **Depends on:** Step 2 (consistent language)
   - **Verify:** Read the updated workflow

4. **Step 4:** Update `CLAUDE.md` § Rule 4 (Domain Grounding) — reference corpus gate
   - **What to change:** Add to verification table: "Category has ≥3 corpus entries with named source citations | Check `data/corpora/{category}.csv` — source column non-empty"
   - **Verify:** Rule 4 table has corpus row

5. **Step 5:** Create draft corpus CSVs for the 4 candidates from Investigation #52
   - **What to change:** Create `data/corpora/new-latin-american-cinema.csv`, `korean-new-wave.csv`, `chinese-art-cinema.csv`, `czech-new-wave.csv` with film entries from the investigation, `source` column left as `UNVERIFIED — [cited work]` where not yet confirmed by curator
   - **Verify:** Files exist, CSV schema matches `CORPUS_FIELDS`, `source` column marks unverified entries
   - **Note:** These are draft corpora. The `UNVERIFIED` prefix is the hard gate — routing rules cannot be written until the curator replaces `UNVERIFIED` with actual page/chapter citations

**Phase B: Per-category implementation (curator-driven, after Phase A)**

Each category follows this sequence — only proceeds when corpus source citations are verified:

6. **Step 6:** Curator verifies corpus entries for highest-priority category (New Latin American Cinema)
   - **What to change:** Replace `UNVERIFIED — Martin (1997)` with `Martin 1997 vol.1 p.XXX` (or reject entry if film doesn't appear in source)
   - **Verify:** `grep -c UNVERIFIED data/corpora/new-latin-american-cinema.csv` returns 0

7. **Step 7:** Write category spec and routing rules (standard Issue process)
   - **Depends on:** Step 6 complete (no UNVERIFIED entries)
   - **What to change:** Add to `SATELLITE_ROUTING_RULES` in `lib/constants.py`, add to `SATELLITE_CATEGORIES.md`, add tests
   - **Verify:** `pytest tests/test_satellite.py -v`, `python scripts/build_corpus.py --audit "New Latin American Cinema"`

### Files to Modify

| File | Change Type | What Changes |
|---|---|---|
| `scripts/build_corpus.py` | Modify | `CATEGORY_ALIASES` — add 4 new category aliases |
| `docs/WORK_ROUTER.md` | Update | § "Add a new satellite category" — insert corpus gate as Step 0 |
| `docs/CURATOR_WORKFLOW.md` | Update | Add corpus verification phase to Workflow B |
| `CLAUDE.md` | Update | § Rule 4 table — add corpus verification row |
| `data/corpora/new-latin-american-cinema.csv` | Create | Draft corpus, 14 entries, UNVERIFIED sources |
| `data/corpora/korean-new-wave.csv` | Create | Draft corpus, 5 entries, UNVERIFIED sources |
| `data/corpora/chinese-art-cinema.csv` | Create | Draft corpus, 5 entries, UNVERIFIED sources |
| `data/corpora/czech-new-wave.csv` | Create | Draft corpus, 3 entries, UNVERIFIED sources |

---

## 6. Scope Boundaries

**In scope:**
- Formalizing the corpus gate in documentation (WORK_ROUTER, CURATOR_WORKFLOW, CLAUDE.md)
- Creating draft corpus CSVs with UNVERIFIED markers for Investigation #52 candidates
- Adding CATEGORY_ALIASES for new categories in build_corpus.py
- Fixing misplacements identified in Investigation #52 §4 (Music Films non-music-films, Popcorn misplacements)

**NOT in scope:**
- Actually verifying scholarship citations — that is curator work requiring the physical books
- Writing SATELLITE_ROUTING_RULES for new categories — blocked by corpus verification (Phase B)
- Implementing routing for any new category — each category gets its own issue spec after corpus is verified
- Enrichment pipeline changes to fix cache gaps (Chinese Art Cinema has 4/5 films missing from caches — separate enrichment issue)
- Changing the `--add` command to support batch/non-interactive mode (nice-to-have, not blocking)

**Deferred to:** Individual category issues (Issue #54+) after corpus verification completes for each

---

## 7. Measurement Story

| Metric | Before (Current) | After (Target) | How to Measure |
|---|---|---|---|
| Categories with corpus files | 5 (Giallo, BrazExploit, AmExploit, Blaxploitation, HK Action) | 9 (+4 draft) | `ls data/corpora/*.csv \| wc -l` |
| UNVERIFIED corpus entries | 0 | 27 (14+5+5+3 drafts) | `grep -c UNVERIFIED data/corpora/*.csv` |
| WORK_ROUTER has corpus gate | No | Yes | Read § "Add a new satellite category" |
| Music Films misplacements fixed | 9 wrong films | 0 wrong films | Check SORTING_DATABASE.md |
| Reaudit confirmed | 572/796 (72.1%, post-#51) | ≥572/796 (no regression) | `python scripts/reaudit.py` |

**Pin baseline before implementing:**
```bash
git tag pre-issue-053
python scripts/reaudit.py > output/pre-053-reaudit.txt
```

---

## 8. Validation Sequence

```bash
# Step 1: Run full test suite
pytest tests/ -v

# Step 2: Verify draft corpus files have correct schema
python3 -c "
import csv
from pathlib import Path
for f in Path('data/corpora').glob('*.csv'):
    reader = csv.DictReader(open(f))
    fields = reader.fieldnames
    expected = ['title','year','imdb_id','director','country','canonical_tier','source','notes']
    if fields != expected:
        print(f'SCHEMA ERROR: {f.name} has {fields}')
    else:
        rows = list(reader)
        unverified = sum(1 for r in rows if 'UNVERIFIED' in r.get('source',''))
        print(f'{f.name}: {len(rows)} entries, {unverified} unverified')
"

# Step 3: Verify CATEGORY_ALIASES updated
python3 -c "
import sys; sys.path.insert(0,'.')
# Just import and check aliases exist - the actual audit will fail
# since these categories don't have library folders yet
from scripts.build_corpus import CATEGORY_ALIASES
for cat in ['new latin american cinema', 'korean new wave', 'chinese art cinema', 'czech new wave']:
    assert cat in CATEGORY_ALIASES, f'Missing alias: {cat}'
print('All aliases present')
"

# Step 4: Verify WORK_ROUTER has corpus gate language
grep -c "corpus" docs/WORK_ROUTER.md

# Step 5: Regression check
python audit.py && python scripts/reaudit.py
```

**Expected results:**
- Step 1: All tests pass (373 passed, 1 skipped)
- Step 2: All 9 corpus files have correct schema; 4 new files show UNVERIFIED counts
- Step 3: All 4 aliases present
- Step 4: WORK_ROUTER mentions corpus in category addition workflow
- Step 5: Confirmed count ≥ 572 (no regression from Phase A documentation changes)

**If any step fails:** Stop. Do not proceed. Report the failure output.

---

## 9. Rollback Plan

**Detection:** Reaudit confirmed count drops below 572; test suite failures; corpus files have wrong schema.

**Recovery:**
```bash
git revert [commit-hash]
# Draft corpus files are new (not modifying existing data), so revert is clean
```

**Pre-implementation checkpoint:**
```bash
git tag pre-issue-053
```

---

## 10. Theory & Architecture Grounding

### Methodology Basis

This issue is grounded in 5 Rules from `CLAUDE.md` §3:

- **Rule 4 (Domain Grounding):** "Every Satellite category must be grounded in published film-historical scholarship, not invented from collection contents." The corpus gate enforces this — the `source` column in corpus CSVs must cite a published work. The UNVERIFIED marker makes the verification state visible.

- **Rule 5 (Constraint Gates):** "Find the binding constraint before optimising. Don't run expensive stages on defective data." Building routing rules is expensive (code changes, tests, reaudit). Scholarship verification is cheap ($0, reading a book). The corpus gate puts the cheap check before the expensive work. From `exports/knowledge-base/system-boundary-theory.md` Principle 4: "Never spend $$ on delivery when $0 boundary validation would have caught the problem."

- **Rule 8 (Prototype Building):** "Don't build until the pattern is confirmed. Exploration must complete before execution." Investigation #52 is exploration output. The corpus is the checkpoint that confirms exploration is complete. Without it, implementation proceeds from unconfirmed patterns.

- **Rule 9 (Creative & Discovery):** "Discovery stops when you can specify the Precision or Reasoning task the discovery was meant to produce." The corpus CSV is the output form — Discovery is complete when the corpus exists with verified source citations. The UNVERIFIED marker means Discovery is still in progress for that entry.

- **Rule 12 (Curation Loop):** "Enrich before Override." Building a corpus (enrichment — helps all films in the movement) is preferred over SORTING_DATABASE pins (override — helps one film). The corpus gate naturally pushes toward enrichment because building the corpus creates the director list, decade bounds, and genre gates that feed SATELLITE_ROUTING_RULES.

### Architecture Reference

- `docs/architecture/VALIDATION_ARCHITECTURE.md` §3 — Corpus lookup architecture (Issue #38)
- `docs/architecture/RECURSIVE_CURATION_MODEL.md` §7 — The Curation Loop
- `docs/theory/REFINEMENT_AND_EMERGENCE.md` §2–4 — Add/Split/Retire protocol, category lifecycle
- `exports/skills/creative-discovery.md` — Discovery protocol (output form, stopping criteria)
- `exports/skills/constraint-gates.md` — Cost-ordering principle (cheap gates before expensive stages)

### Related Issues

- #38 — Layer 1 Ground Truth Corpora (created the corpus infrastructure this issue builds on)
- #51 — Remove catch-all categories (created the 140-film unroutable population this addresses)
- #52 — Investigation: New category candidates (the discovery output this issue gates)
- #54+ — Individual category implementations (blocked by this issue's corpus verification gate)

---

## Appendix A: Investigation #52 Provenance Analysis

### How Investigation #52 Was Derived

The investigation was produced by a Claude session on 2026-03-08. The workflow:

1. Issue #51 removed Indie Cinema, Music Films, Cult Oddities from auto-routing
2. Reaudit showed 140 films became `unroutable`
3. Claude session grouped the 140 films by country/decade/director
4. Matched clusters to historical movements known from training data
5. Cited published scholarship for each candidate from training-data recall
6. Applied the Add protocol (Rule 4) — density, coherence, archival necessity, scholarship
7. Correctly rejected one candidate (New Japanese Cinema) as incoherent

### What the Investigation Got Right

- The movements identified are real, well-documented film-historical movements
- The scholarship citations are real published works (verified against training data)
- The rejection of New Japanese Cinema follows the anti-catch-all principle from Issue #51
- The tier recommendations (all Tier 4 initially) follow Rule 11 (Certainty-First)
- The density assessments are accurate (14, 5, 5, 3 films respectively)

### What the Investigation Cannot Guarantee

- **Per-film scholarship presence:** Does "Fin de fiesta" (1960, Torre Nilsson) appear in Martin (1997)? Torre Nilsson almost certainly does; Rogelio A. González probably does not. The investigation doesn't distinguish.
- **Director roster accuracy:** The director lists are inferred from collection + training data, not extracted from the cited sources' filmographies. The Favio/Briand discrepancy on "El Romance" demonstrates this risk.
- **Decade bound accuracy:** The investigation says New Latin American Cinema spans 1950s–1990s. The scholarship may define tighter bounds. López (1992) focuses on 1960s–1980s.
- **Cache data completeness:** Chinese Art Cinema has 4/5 films with no cache data. Korean New Wave has 2/5 missing. These gaps affect whether routing rules can actually classify these films.

### Cache Cross-Check Results (2026-03-08)

**New Latin American Cinema:**

| Film | Year | Investigation Dir | Cache Dir | Countries | Cache? |
|---|---|---|---|---|---|
| Fin de fiesta | 1960 | Torre Nilsson | Torre Nilsson | AR | TMDb |
| El Romance Del Aniceto Y La Francisca | 1967 | Leonardo Favio | **Jorge Briand** | AR | TMDb+OMDb |
| El dependiente | 1969 | (not stated) | Leonardo Favio | AR | TMDb+OMDb |
| La soldadera | 1967 | José Bolaños | José Bolaños | MX | TMDb |
| El Esqueleto De La Señora Morales | 1960 | Rogelio A. González | **???** | — | NONE |
| El Escapulario | 1968 | unkn. | Servando González | MX | TMDb |
| Paraiso | 1970 | Luis Alcoriza | Luis Alcoriza | MX | TMDb+OMDb |
| The Castle of Purity | 1973 | Arturo Ripstein | Arturo Ripstein | MX | TMDb+OMDb |
| Juan Moreira | 1973 | Leonardo Favio | Leonardo Favio | AR | TMDb+OMDb |
| Cecilia | 1982 | Humberto Solás | Humberto Solás | CU,ES | TMDb+OMDb |
| Gatica, el mono | 1993 | Leonardo Favio | Leonardo Favio | AR,ES | TMDb |
| Danzon | 1991 | María Novaro | María Novaro | MX,ES | TMDb+OMDb |
| Herod's Law | 1999 | Luis Estrada | Luis Estrada | MX | TMDb |
| Mango Yellow | 2002 | Cláudio Assis | Cláudio Assis | BR | TMDb |

**Korean New Wave:**

| Film | Year | Cache Dir | Countries | Cache? |
|---|---|---|---|---|
| The Quiet Family | 1998 | Kim Jee-woon | KR | TMDb+OMDb |
| Old Boy | 2003 | Park Chan-wook | KR | TMDb |
| Save the Green Planet | 2003 | **???** | — | NONE |
| I'm A Cyborg But That's OK | 2006 | **???** | — | NONE |
| The Good the Bad the Weird | 2008 | Kim Jee-woon | KR | TMDb+OMDb |

**Chinese Art Cinema:**

| Film | Year | Cache Dir | Countries | Cache? |
|---|---|---|---|---|
| Raise the Red Lantern | 1991 | **???** | — | NONE |
| Farewell My Concubine | 1993 | Kaige Chen | CN,HK,KR | TMDb+OMDb |
| Platform | 2000 | **???** | — | NONE |
| Mountains May Depart | 2015 | **???** | — | NONE |
| Long Day's Journey Into Night | 2018 | **???** | — | NONE |

**Czech New Wave:**

| Film | Year | Cache Dir | Countries | Cache? |
|---|---|---|---|---|
| Daisies | 1966 | Vera Chytilová | CS | TMDb+OMDb |
| Ikarie XB 1 | 1963 | Jindřich Polák | XC | TMDb |
| When The Cat Comes | 1963 | Vojtech Jasný | CS | TMDb+OMDb |

---

## Appendix B: Designed Workflow — Category Addition with Corpus Gate

The following workflow integrates the existing Add protocol (Rule 4, `docs/theory/REFINEMENT_AND_EMERGENCE.md` §2), the Discovery protocol (Rule 9, `exports/skills/creative-discovery.md`), and the Constraint Gate principle (Rule 5, `exports/skills/constraint-gates.md`) into a gated sequence:

```
Phase 1: DISCOVERY (Rule 9)
  ├── Cohort analysis surfaces taxonomy_gap cluster
  │     (reaudit.py → analyze_cohorts.py → category_fit.py)
  ├── Investigation doc: is this a real movement?
  │     (Discovery protocol — define output form, set stopping criteria)
  └── Output: Investigation doc with candidate movements + cited scholarship

Phase 2: CORPUS GATE (Rule 5 — cheap check before expensive work)
  ├── Build draft corpus CSV from investigation findings
  │     (build_corpus.py --add ... --category "Category")
  │     source column = "UNVERIFIED — [cited work]"
  ├── HARD GATE: Curator verifies source citations
  │     (replace UNVERIFIED with page/chapter references or reject entry)
  │     Minimum 3 entries with verified sources to proceed
  ├── Corpus audit passes
  │     (build_corpus.py --audit "Category" — no HARD anomalies)
  └── Output: Verified corpus CSV with scholarship-backed entries

Phase 3: IMPLEMENTATION (Rule 8 — build only after pattern confirmed)
  ├── Write issue spec (ISSUE_SPEC_TEMPLATE.md)
  │     Director list FROM corpus (not from investigation)
  │     Decade bounds FROM scholarship (not from collection)
  ├── Add to SATELLITE_ROUTING_RULES + SATELLITE_CATEGORIES.md
  ├── Add tests
  ├── SORTING_DATABASE pins for boundary cases
  └── Reaudit — confirm no regressions

Phase 4: CURATION LOOP (Rule 12)
  ├── Review queue: low-confidence classifications in new category
  ├── Curator: Accept / Override / Enrich / Defer
  └── Feed decisions back into corpus + routing rules
```

### Why This Workflow (Principle Alignment)

| Principle | How It Applies |
|---|---|
| Rule 4 (Domain Grounding) | Corpus `source` column forces scholarship citation per-film |
| Rule 5 (Constraint Gates) | Corpus verification ($0) gates routing rule implementation ($$) |
| Rule 8 (Prototype Building) | Corpus = confirmed pattern; routing rules = execution |
| Rule 9 (Discovery) | Investigation = discovery output; corpus = stopping criterion |
| Rule 10 (Data Readiness) | Cache cross-check exposes enrichment gaps before routing |
| Rule 11 (Certainty-First) | Draft corpus at Tier 4; earn Tier 2 after verification |
| Rule 12 (Curation Loop) | Corpus = enrichment (systemic); SORTING_DATABASE pin = override (point fix) |

### Comparison with Alternatives Considered

**Option A (Curator-verified scholarship — manual gate):** The investigation doc gets flagged for curator review; curator verifies citations. Problem: no enforced artifact. The "verification" is a conversation, not a checkpoint. Violates Rule 5 — soft gate, not hard gate. No downstream tool can check whether verification happened.

**Option B (Corpus-backed verification — this proposal):** Draft corpus CSV with UNVERIFIED markers. Curator replaces markers with real citations. Routing rules blocked until UNVERIFIED count = 0. Aligns with Rule 5 (hard gate), Rule 9 (output form), Rule 12 (enrichment over override). The artifact (`data/corpora/{category}.csv`) is checkpointable, auditable, and feeds directly into the classification pipeline.

**Option C (Two-phase investigation — hybrid):** Phase 1 automated, Phase 2 curator. Problem: the "phases" have no artifact boundary — just a conversation split. Functionally equivalent to Option A with extra steps.

Option B was selected because it is the only approach where the gate produces a durable, machine-readable artifact that integrates with existing tooling (Issue #38's corpus infrastructure).
