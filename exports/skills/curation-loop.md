# Skill: Curation Loop (Bidirectional Feedback for Classification Systems)

**Purpose:** Transform a one-directional classifier into a curation assistant with feedback from curator decisions back into routing rules.
**Addresses:** Lifecycle stalling at Stage 2 (clustering), diagnostic tools that produce reports no one acts on, no execution path from "problem found" to "problem fixed," and curatorial knowledge trapped outside the system.

---

## Core Principle

**Every classification is a suggestion until a curator confirms it. Curatorial decisions feed back into the system. A classifier without a feedback loop can only degrade — it cannot learn.**

Without a curation loop:
- The system classifies films and moves them, but never learns from mistakes
- Diagnostic tools (re-audit, tentpole ranking) produce markdown reports that no tool can act on
- The curator's corrections (editing SORTING_DATABASE.md by hand) bypass the system instead of feeding back into it
- The curatorial lifecycle (Define → Cluster → Refine → Retain/Discard → Reinforce) stalls at Stage 2 because Stages 3-5 have no execution tools
- Films placed before the pipeline existed (~500) are never re-evaluated against current routing rules

---

## The Classifier vs. Curation Assistant Distinction

These are structurally different systems:

| Property | Classifier | Curation Assistant |
|----------|-----------|-------------------|
| Data flow | One-directional: data → rules → output | Bidirectional: data → rules → suggestion → curator → rules |
| Output semantics | "This film IS Giallo" | "This film is PROBABLY Giallo (confidence 0.7)" |
| Outcome states | Binary: classified or unsorted | Ternary: classified, uncertain (review), or unsorted |
| Authority | System is the authority | Curator is the authority; system is a tool |
| Error handling | Errors accumulate silently | Errors surface as review items |
| Improvement | Only through code changes | Through curatorial decisions that feed back into rules |

The film sorting system was built as a classifier. It needs to become a curation assistant.

---

## The Four Curator Actions

When a classification surfaces for review (via the review queue, re-audit, or tentpole ranking), the curator has exactly four actions:

### Accept

The classification is correct. The curator confirms the system's suggestion.

**System effect:**
- Film moves to its classified destination (if not already there)
- Classification confidence is recorded as confirmed
- No rule changes needed

**When to accept:** The film matches the category definition. The curator recognizes it as belonging there. The confidence level, even if moderate, reflects genuine membership.

### Override

The classification is wrong. The curator knows the correct destination.

**System effect:**
- An entry is generated for SORTING_DATABASE.md: `Title (Year) → Correct/Destination/Path`
- The entry is written to a staging file (`output/sorting_database_additions.txt`), not directly to SORTING_DATABASE.md (which is never modified programmatically)
- On next classification run, the explicit lookup catches this film before heuristic routing fires
- If the override reveals a systematic routing error (e.g., a country code mapping is wrong), the curator escalates to a routing rule change

**When to override:** The system classified the film, but into the wrong category. The curator knows where it belongs because of knowledge the system doesn't have — movement membership, director biography, historical context.

### Enrich

The classification is uncertain because data is missing. The curator can supply the missing metadata.

**System effect:**
- Curator provides missing fields (director, country, genres) via the manual enrichment pathway
- Data is written to `output/manual_enrichment.csv`
- On next classification run, the enrichment data is loaded before API queries
- The film's data readiness level rises (R1 → R2 or R3), enabling routing stages that were previously skipped

**When to enrich:** The film went to Unsorted with `unsorted_insufficient_data` (R1). The curator recognizes the film and knows its director or country. Rather than adding a full SORTING_DATABASE entry, the curator provides the missing metadata and lets the routing rules do their work.

**The distinction from Override:** Override says "the answer is X, trust me." Enrich says "here's the data — now let the system figure it out." Enrich is preferred when the curator believes the routing rules are correct but the input data was insufficient.

### Defer

The curator is uncertain and needs more research.

**System effect:**
- Film is flagged as deferred in the review queue
- Removed from the active review list for this cycle
- Preserved for the next review cycle (not lost)
- No classification change, no data change

**When to defer:** The curator doesn't recognize the film, or the classification is ambiguous (could be Giallo or European Sexploitation, need to research). Deferral is honest uncertainty — better to defer than to accept a classification you're not sure about.

---

## The Review Queue

The review queue is the interface between the system and the curator. It is a staging area for classifications that need human confirmation before they can be considered final.

### What Enters the Review Queue

Three populations:

1. **Low-confidence classifications:** Films classified by the pipeline but with confidence below the review threshold (initially 0.5). This includes all Tier 3 (Indie Cinema, Music Films) and Tier 4 (manual-only) auto-classifications.

2. **Enriched-but-unsorted films:** Films with R2 or R3 data readiness that still landed in Unsorted. These are genuine taxonomy gaps — the system had enough data to classify but no rule matched. The curator should evaluate whether a new rule is needed or if the film belongs in an existing category via SORTING_DATABASE.

3. **Re-audit discrepancies:** Films where the current folder location disagrees with what the current routing rules would classify them as. These come from `scripts/reaudit.py` output — the diagnostic tool that already exists but has no execution path.

### What the Review Queue Contains

Same schema as the sorting manifest, plus:

| Field | Purpose |
|-------|---------|
| `filename` | The film file |
| `suggested_tier` | What the pipeline suggests |
| `suggested_destination` | Full path the pipeline would build |
| `confidence` | How confident the pipeline is |
| `data_readiness` | R0/R1/R2/R3 — what data is available |
| `reason` | Why this is in the review queue (low_confidence, unsorted_with_data, reaudit_discrepancy) |
| `available_actions` | accept, override, enrich, defer |

### Review Queue Lifecycle

```
classify.py produces:
  sorting_manifest.csv  ← high-confidence results (confidence ≥ threshold)
  review_queue.csv      ← low-confidence + unsorted-with-data

Curator reviews review_queue.csv:
  ACCEPT    → film added to sorting_manifest for next move.py run
  OVERRIDE  → entry staged for SORTING_DATABASE.md
  ENRICH    → metadata written to manual_enrichment.csv
  DEFER     → film stays in queue for next cycle

On next classify.py run:
  manual_enrichment.csv loaded → R1 films may become R2/R3
  new SORTING_DATABASE entries loaded → explicit lookups catch overrides
  review_queue.csv regenerated with updated results
```

---

## The Manual Enrichment Pathway

When API enrichment fails (R1 readiness), the curator has knowledge that the system doesn't. The manual enrichment pathway is how that knowledge enters the system.

### How It Works

The curator creates or appends to `output/manual_enrichment.csv`:

```
filename,director,country,genres
"A Fêmea do Mar (1980).mp4","Fernando Lopes","PT","Drama"
"Lo scopone scientifico (1972).mkv","Luigi Comencini","IT","Comedy,Drama"
```

**Rules:**
- Only fields the curator is confident about should be filled. Empty fields are left blank (the system will still query APIs for them).
- Country must be a 2-letter ISO code (same as OMDb/TMDb output).
- Genres must match TMDb genre names (Drama, Horror, Thriller, etc.).
- Director must be the commonly-used director name (system will normalize).

### Trust Level

Manual enrichment data has the same trust level as API data — it fills in missing fields but does not override existing API data. It sits below SORTING_DATABASE (which overrides everything) and at the same level as TMDb/OMDb results.

**Priority for each field when manual enrichment exists:**
- Director: SORTING_DATABASE > OMDb > manual enrichment > TMDb > filename
- Country: SORTING_DATABASE > OMDb > manual enrichment > TMDb > filename
- Genres: SORTING_DATABASE > TMDb > manual enrichment > OMDb

**Why not higher trust?** Manual enrichment is curator-provided but not curator-verified-in-context. The curator typed a director name from memory — it might have a spelling variant. SORTING_DATABASE entries are verified against the full classification context.

---

## Lifecycle Completion

The curation loop completes the curatorial lifecycle defined in `docs/theory/REFINEMENT_AND_EMERGENCE.md`:

| Lifecycle Stage | Theory | Current Code | Curation Loop Adds |
|----------------|--------|-------------|-------------------|
| **1. Define** | Establish category identity | SATELLITE_CATEGORIES.md + constants.py | No change needed |
| **2. Cluster** | Route films into categories | classify.py + move.py | No change needed |
| **3. Refine** | Compare placement to rules, flag discrepancies | reaudit.py (read-only report) | Review queue execution: accept/override/enrich/defer |
| **4. Retain/Discard** | Within-category hierarchy, tentpoles vs texture | rank_category_tentpoles.py (read-only report) | Curation execution tool: apply ranking decisions |
| **5. Reinforce** | Feed decisions back into routing rules | Nothing | Override → SORTING_DATABASE growth; Enrich → manual_enrichment.csv; systematic pattern → routing rule change |

**The critical gap closed:** Stages 3-5 currently produce reports. The curation loop adds execution. Accept moves files. Override grows SORTING_DATABASE. Enrich improves data quality. Each action is the execution tool for its lifecycle stage.

---

## Design Rules

### Rule 1: The Curator Is Always in the Loop

No classification is final without curator confirmation. For high-confidence results (Tier 1-2, confidence ≥ 0.7), confirmation may be implicit — the curator runs `move.py` and accepts the manifest. For low-confidence results (Tier 3-4), confirmation must be explicit — the curator reviews the queue and takes an action.

This does not mean every film needs manual review. It means the system always provides a path for the curator to intervene, and low-certainty classifications are routed to that path by default.

### Rule 2: Feedback Is Structured, Not Ad-Hoc

Curator decisions are captured in structured formats (CSV files with defined schemas), not free-form edits. This enables:
- Auditing: what did the curator decide, and when?
- Rollback: if a batch of decisions was wrong, revert the CSV
- Learning: patterns in override decisions reveal systematic routing gaps

### Rule 3: The System Never Writes to SORTING_DATABASE.md

SORTING_DATABASE.md is human-curated (CLAUDE.md project rule). The curation loop generates entries in `output/sorting_database_additions.txt`. The curator reviews these additions and manually copies confirmed entries to SORTING_DATABASE.md. This preserves the "human writes, code reads" invariant.

### Rule 4: Enrich Before Override

When a film is misclassified, the curator should first ask: "Would providing the missing data fix this?" If yes, use Enrich (let the routing rules work with better data). If no, use Override (the routing rules can't handle this film, bypass them).

**Why enrich-first:** Enrich improves the system's general capability. A director name added via manual enrichment helps classify ALL films by that director. An override is a point fix — it only helps the specific film. Prefer the systemic fix.

### Rule 5: Defer Is Not Failure

Deferring a classification is the correct action when the curator is uncertain. The system is designed to cycle: deferred films re-enter the queue on the next run, possibly with new data (API caches updated, manual enrichment from other films providing context). A film deferred three cycles in a row signals that more research is needed or that the film genuinely doesn't fit the taxonomy.

---

## Diagnostic: When the Loop Stalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| Review queue grows every cycle | More films entering than being triaged | Set a per-cycle review budget (e.g., review top 20 by confidence) |
| Same films deferred repeatedly | No new information arriving | These films need manual research outside the system, or a new category |
| Override rate > 30% | Routing rules are systematically wrong | Don't override individually — fix the routing rule that's producing wrong results |
| Enrich rate > 50% | API enrichment is failing for most films | Investigate API coverage — are titles parsing correctly? Is cache poisoned? |
| Accept rate = 100% | Everything is correct (unlikely) or curator is rubber-stamping | Spot-check a sample of accepted films against category definitions |

---

## Integration with Other Skills

| Skill | How Curation Loop Connects |
|---|---|
| **Data Readiness** | R1 films are the primary enrichment candidates. The curation loop's Enrich action raises readiness levels. |
| **Certainty-First** | Certainty tiers determine which films enter the review queue (Tier 3-4) vs. auto-classify (Tier 1-2). |
| **Failure Gates** | Override decisions that reveal systematic routing errors should trigger a Failure Gate investigation — is a gate too soft? Too hard? |
| **Constraint Gates** | If the review queue is dominated by one failure mode (e.g., all deferred films are from the same country), the constraint is in the enrichment stage for that country's data. |
| **Domain Grounding** | Override decisions must be grounded in the same published film-historical scholarship as routing rules. A curator overriding "Giallo → Core" must have a reason defensible against the category definition. |
| **Measurement-Driven** | Track the curation loop's metrics: accept/override/enrich/defer rates per cycle, review queue size trend, time-to-resolution. These are the system's learning metrics. |
| **Creative & Discovery** | When override patterns suggest a missing category (e.g., 10 Portuguese films all overridden from Indie Cinema to a non-existent "Portuguese Cinema" category), the Creative & Discovery protocol applies: is there a new category to define? |

---

## Checklist

When setting up the curation loop:
- [ ] Review queue output exists (`output/review_queue.csv`)
- [ ] Confidence threshold is set (default 0.5)
- [ ] Low-certainty categories (Tier 3-4) route to review queue
- [ ] R2/R3 unsorted films route to review queue
- [ ] Manual enrichment pathway exists (`output/manual_enrichment.csv`)
- [ ] SORTING_DATABASE additions staging file exists (`output/sorting_database_additions.txt`)
- [ ] Curation execution tool can process accept/override/enrich/defer

When running a review cycle:
- [ ] Reviewed top N films by confidence (highest first — most likely to be quick accepts)
- [ ] For each film: chose accept, override, enrich, or defer
- [ ] Override entries reviewed before adding to SORTING_DATABASE.md
- [ ] Manual enrichment entries verified (correct ISO codes, TMDb genre names)
- [ ] Deferred films noted for next cycle
- [ ] Ran classify.py again to pick up enrichment and SORTING_DATABASE changes
- [ ] Compared new results to previous — did the loop improve classification?
