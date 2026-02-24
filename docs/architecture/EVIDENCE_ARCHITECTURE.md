# Evidence Architecture: Closing the Feedback Loop

> A system that classifies 491 films and produces 44 identical failures is not failing 44 times. It is failing once — and describing it 44 times.

**Type:** Architecture document (HOW the system should change)
**Theoretical grounding:** `docs/theory/THEORETICAL_GROUNDING.md` §8-§12
**Depends on:** RECURSIVE_CURATION_MODEL.md (the lifecycle this document completes)

---

## 1. The Diagnosis: Open Loop Disguised as Recursive

The architecture document (RECURSIVE_CURATION_MODEL.md) describes a five-stage recursive loop:

```
Define → Cluster → Refine → Retain/Discard → Reinforce
  ↑                                              │
  └──────────────────────────────────────────────┘
```

The theory is correct. The implementation is not recursive. Here is what actually happens:

**Within a single classification run**, the pipeline is a one-pass funnel. Each stage receives the film, tests a single condition, returns a name or `None`, and discards all intermediate evidence. When 44 films fail the Satellite genre gate with identical symptoms (country + decade present, genres absent), the pipeline produces 44 individual `unsorted_no_match` results with no record of what they share, why they failed, or what would fix them.

**Between runs**, the "feedback loop" is a human reading a staging report, manually diagnosing why films failed, and hand-editing constants or SORTING_DATABASE entries. This is not a feedback loop. This is a human performing the system's job because the system discards the information it would need to do it itself.

The evidence: every Issue from #14 through #34 follows the same cycle:

1. A population of stuck films is discovered (usually by running classify and reading the output)
2. A human diagnoses which gate blocks them (by reading the source code and reasoning about the data)
3. The human manually adds directors to a list, or pins films to SORTING_DATABASE, or relaxes a gate
4. The pipeline runs again, classifying the specific films that were fixed
5. A new population of stuck films is discovered

This is single-loop learning (THEORETICAL_GROUNDING §8): fixing instances without questioning governing variables. The pipeline was designed as a classifier. It needs to become an evidence accumulator.

---

## 2. The Information Destruction Map

Where evidence is currently lost, stage by stage:

```
FILENAME
  │
  ├─[Stage 0: Parser]
  │   Produces: title, year, director, language, country, user_tag, format_signals
  │   Destroys: format_signals (stripped during cleaning)
  │             parser confidence (no record of which regex matched)
  │             alternative parses (only the first successful match survives)
  │
  ├─[Stage 1: API Enrichment + Merge]
  │   Produces: merged tmdb_data dict
  │   Destroys: source attribution (which API provided which field)
  │             merge conflicts (when TMDb and OMDb disagree, the losing value is discarded)
  │             API confidence (TMDb search match score not preserved)
  │
  ├─[Stage 2: Explicit Lookup]
  │   Produces: destination path string OR None
  │   Destroys: lookup metadata (which entry matched, were there close misses?)
  │
  ├─[Stage 3: Reference Canon]
  │   Produces: decade OR None
  │   Destroys: canon proximity (was the title close to a canon entry?)
  │
  ├─[Stage 4-5: Satellite Routing]
  │   Produces: category name OR None
  │   Destroys: ALL intermediate evidence:
  │     - which categories were tested
  │     - which gates passed for each category
  │     - which gates failed for each category
  │     - which gates were untestable (data absent vs data contradictory)
  │     - the nearest-match category and its evidence profile
  │     - director match details, keyword signal hits
  │
  ├─[Stage 6-7: User Tag Recovery + Core Director Check]
  │   Produces: tier + decade OR None
  │   Destroys: tag parsing failures, director matching confidence
  │
  ├─[Stage 8: Popcorn Check]
  │   Produces: reason code OR None
  │   Destroys: individual signal states (popularity value, vote count)
  │             threshold distances (popularity=6.8 vs threshold=7.0)
  │
  └─[Stage 9: Unsorted]
      Produces: reason code (unsorted_no_match, unsorted_no_director, etc.)
      Destroys: everything above — conflates data problems, taxonomy gaps,
                and genuine non-matches into a single label
```

The largest information loss is at Stages 4-5 (Satellite routing), where the entire evidence profile for every category tested is discarded. The second largest is at Stage 1 (API merge), where source attribution and merge conflicts are lost. Together, these two points account for most of the system's inability to self-diagnose.

---

## 3. Three Missing Capabilities

The theoretical frameworks (THEORETICAL_GROUNDING §8-§12) converge on three capabilities the system lacks.

### A. Evidence Trail (Per-Film)

**Problem:** When a film fails to classify, the system records a reason code and nothing else. The curator cannot determine why the film failed without reading the source code.

**What it should produce:** Every routing stage produces an evidence record, not just a verdict. The record preserves what was tested, what matched, what failed, and what couldn't be evaluated (THEORETICAL_GROUNDING §9: Dempster-Shafer distinction between absent and negative evidence).

**The evidence trail per film would include:**
- Data readiness level (R0/R1/R2/R3) and which fields are present/absent
- For each category considered: which gates passed, which failed, which were untestable
- The nearest-match category and what evidence would complete the match
- Confidence vector across all categories (not just the winning one)
- Source attribution: which API provided which field

**What this enables:** The curator sees: "This film almost matched Indie Cinema (country=FR pass, decade=1970s pass, genre gate untestable due to absent data; suggest enriching genres)." Actionable without reading source code.

### B. Failure Cohort Analysis (Per-Run)

**Problem:** The pipeline classifies films individually and reports individually. When 44 films fail for the same structural reason, this is invisible — the staging report lists 44 separate entries with the same reason code.

**What it should produce:** After all films are classified, analyse accumulated traces to detect population-level patterns (THEORETICAL_GROUNDING §10: stigmergy — individual failures are noise, cohort failures are signal).

**Cohort analysis would include:**
- Group Unsorted films by failure pattern (which gate failed, what data was present)
- Name the pattern: "genre-data-absent cohort (44 films): country+decade present, genres=[]"
- Identify the binding constraint: "These films would classify if genres were available"
- Distinguish data cohorts from taxonomy cohorts: "These 8 HU films have full data but no rule matches Hungary"

**What this enables:** The curator sees three named problems instead of 44 anonymous failures.

### C. Hypothesis Generation (Per-Cycle)

**Problem:** Even when the curator diagnoses a failure pattern, the remedy must be invented by the human. The system never proposes its own improvements.

**What it should produce:** When a cohort failure is detected, generate a hypothesis about what rule change would resolve it. Present to curator for validation (THEORETICAL_GROUNDING §8: double-loop learning — question governing variables, not just instances).

**Hypothesis generation would include:**
- "HYPOTHESIS: Add 'dennis hopper' to American New Hollywood directors. EVIDENCE: 3 Hopper films unsorted, all US/1970s. CONFIDENCE: high."
- "HYPOTHESIS: Genre gate too strict for R2b population. EVIDENCE: 44 films fail genre gate with country+decade present but genres=[]. CONFIDENCE: medium."
- "HYPOTHESIS: Missing category for Hungarian arthouse. EVIDENCE: 5 HU films with R3 data, no category covers HU in 1970s-1980s. CONFIDENCE: low (may not meet density threshold)."

**What this enables:** The manual patch cycle (Issues #14-#34) becomes system-assisted. The system generates the diagnosis and proposes the fix. The curator validates or rejects.

---

## 4. The New Information Contract

The five-stage lifecycle remains correct. What changes is the information contract between stages.

### Current contract

```
Cluster produces:   sorting_manifest.csv    (final verdicts)
                    staging_report.txt      (human-readable Unsorted list)
                    review_queue.csv        (low-confidence + unsorted-with-data)

Refine consumes:    sorting_manifest.csv    (to detect regressions via reaudit.py)
                    staging_report.txt      (human reads and manually diagnoses)
```

The problem: Cluster outputs *verdicts*, not *evidence*. Refine has nothing to work with except the verdict. The curator re-derives evidence by reading code.

### Required contract

```
Cluster produces:   sorting_manifest.csv    (verdicts — unchanged)
                    evidence_trails.csv     (per-film evidence profiles — NEW)
                    failure_cohorts.json    (population-level failure patterns — NEW)
                    hypotheses.md           (proposed rule changes with evidence — NEW)

Refine consumes:    evidence_trails.csv     (what matched, what didn't, what's missing)
                    failure_cohorts.json    (named failure populations with remediations)
                    hypotheses.md           (proposed improvements for curator review)
```

The evidence trail is the raw material. The cohort analysis is the digest. The hypotheses are the actionable proposals. Together, they provide the inputs Stages 3-5 need to function without manual re-derivation.

### Impact on the curation loop

The four curator actions (Accept, Override, Enrich, Defer) remain the same. What changes is the quality of information:

| Curator action | Currently sees | Would see |
|---|---|---|
| **Accept** | "This film is Giallo (confidence 0.7)" | "Giallo: country=IT pass, decade=1970s pass, genre=Horror pass, director=Argento pass. All gates passed." |
| **Override** | "This film is Unsorted (no match)" | "Nearest: Indie Cinema (FR + 1970s pass, genre untestable). Override to Indie Cinema? Or enrich genres first?" |
| **Enrich** | "This film needs data" | "Genre is the binding constraint. With genres, this film would likely route to Indie Cinema (2/3 gates pass)." |
| **Defer** | "This film is uncertain" | "Conflicting evidence: near-miss Giallo (IT + 1970s) AND near-miss European Sexploitation (IT + erotica keyword). Needs human judgment." |

Better evidence → better curator decisions → better feedback → better classification on the next pass. This is where the recursion actually closes.

---

## Cross-References

- [RECURSIVE_CURATION_MODEL.md](RECURSIVE_CURATION_MODEL.md) — The lifecycle this document completes; §1-§9 describe the existing architecture
- [THEORETICAL_GROUNDING.md](../theory/THEORETICAL_GROUNDING.md) — §8-§12 ground the frameworks cited here (Argyris, Dempster-Shafer, stigmergy, blackboard, Ashby)
- [REFINEMENT_AND_EMERGENCE.md](../theory/REFINEMENT_AND_EMERGENCE.md) — §4a (lifecycle stages 3-5); this document specifies the information contract those stages need
- [MARGINS_AND_TEXTURE.md](../theory/MARGINS_AND_TEXTURE.md) — §8 (positive-space vs negative-space); evidence architecture applies differently to each type
