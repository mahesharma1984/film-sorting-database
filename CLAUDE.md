# CLAUDE.md — Film Sorting Database

## §1 Startup

On every interaction, read:
1. `docs/CORE_DOCUMENTATION_INDEX.md` — find any doc quickly
2. `docs/DEVELOPER_GUIDE.md` — how to make changes safely

For curatorial context, read `docs/theory/README.md` → individual essays as needed.

For cross-concept questions or quick verification: `python3 -m lib.rag.query "your question"` — returns top-5 ranked doc sections with file paths and line ranges. See `docs/RAG_QUERY_GUIDE.md` for query patterns.

---

## §2 Work Modes

### Build / Feature Mode
Read first:
- `REFACTOR_PLAN.md` — v1.0 architecture (3-script design)
- `docs/theory/TIER_ARCHITECTURE.md` — why tiers work this way
- `docs/theory/MARGINS_AND_TEXTURE.md` — satellite logic rationale

Primary skills: Prototype Building (Rule 8), Pattern-First (Rule 2), R/P Split (Rule 1), Domain Grounding (Rule 4)

### Debug / Regression Mode
Read first:
- `docs/DEBUG_RUNBOOK.md` — symptom → diagnosis → fix
- `issues/` — past bugs and their root causes
- `docs/WORK_ROUTER.md` — route symptoms to the right doc

Primary skills: Constraint Gates (Rule 5), Failure Gates (Rule 3), Measurement-Driven (Rule 7), Boundary-Aware Measurement (Rule 6)

### Discovery / Curatorial Mode
Use when exploring new categories, auditing director lists, or making taxonomy decisions.

Read first:
- `docs/theory/REFINEMENT_AND_EMERGENCE.md` — how categories are built
- `docs/theory/SATELLITE_DEPTH.md` — within-category depth hierarchies
- `docs/SATELLITE_CATEGORIES.md` — existing category specifications

Primary skills: Creative & Discovery (Rule 9), Domain Grounding (Rule 4), Prototype Building (Rule 8)

### Understanding Mode
Read first:
- `docs/theory/README.md` — reading order for all 5 theory essays

---

## §3 Decision Rules

Rules 1–9 below are operational summaries of the full methodology in `exports/skills/`. For detailed theory, examples, and checklists, see individual skill docs.

### Rule 1: R/P Split (Reasoning vs Precision)

Every operation is either REASONING or PRECISION. Never mix them in one step.

| Task | Type | Actor |
|------|------|-------|
| Parse filename → title, year, director | PRECISION | Code (regex) |
| Normalize title for lookup | PRECISION | Code (`normalize_for_lookup()`) |
| Look up known film in SORTING_DATABASE.md | PRECISION | Code (lookup table) |
| Check Core director whitelist | REASONING (structured rules) | Code (whitelist match) |
| Check Reference canon | REASONING (structured rules) | Code (canon list match) |
| Classify satellite category | REASONING (structured rules) | Code (country + decade rules) |
| Move file from A to B | PRECISION | Code (`os.rename` / `shutil.copy2`) |
| Format manifest CSV | PRECISION | Code (`csv.DictWriter`) |

**Test:** If a step requires both parsing AND judgment, split it into two steps.

### Rule 2: Pattern-First

The 4-tier priority hierarchy is the PATTERN. All films are instances classified into it:

```
Reference (canon) → Satellite (movement match) → Core (prestige non-movement) → Popcorn (pleasure) → Unsorted
```

(Explicit lookup always fires first — SORTING_DATABASE overrides everything. This describes the heuristic chain.)

This priority order is a design decision, not an implementation detail. The classifier checks tiers in this order — first match wins. Never reorder without explicit redesign.

The classification pipeline checks in this priority (Issue #25):
1. Explicit lookup (SORTING_DATABASE.md) — human-curated, highest trust
2. Reference canon check — 50-film hardcoded list
3. Satellite routing — country + decade + director rules (decade-bounded, movement-first)
4. User tag recovery — trust previous human classification (after Satellite, so stale Core tags don't block movement routing)
5. Core director check — whitelist match (fallback for non-movement prestige work)
6. Popcorn check — popularity + format signals
7. Default → Unsorted with reason code

### Rule 3: Failure Gates

Every check declares what happens on failure. Gate type determines severity:

| Check | Hard Gate (stops) | Soft Gate (continues) |
|-------|-------------------|-----------------------|
| Parser: no year extracted | Cannot route to decade → Unsorted | — |
| Parser: no director | — | Continue without director (still classifiable via lookup/reference) |
| Filesystem: dest drive not mounted | Cannot move files → abort | — |
| TMDb/OMDb: no API keys or both fail | — | Continue with filename-only classification |
| Lookup: no match in SORTING_DATABASE | — | Continue to heuristic checks |
| Core director: no whitelist match | — | Continue to Reference check |

**Gate design rules:**
- **Level 0 gates everything** — If the data source is unreliable (e.g. TMDb returns wrong film), all downstream metrics describe the error, not the film. Validate inputs first.
- **Hard gates have no repair logic** — If repair is needed, add a separate stage with its own gates.
- **Soft gates accumulate** — Individual soft failures are fine; accumulation signals systemic issues.
- **Absence-based properties need scope gates** — "No Core director in Satellite" requires checking all N items and reporting N, not just failing to find a counterexample.

### Rule 4: Domain Grounding

Every Satellite category must be grounded in published film-historical scholarship, not invented from collection contents.

| Requirement | How to verify |
|-------------|---------------|
| Category cites a historical movement | Check `docs/SATELLITE_CATEGORIES.md` — each entry names its tradition and date bounds |
| Director lists reflect documented membership | Directors must appear in published filmographies of the movement, not just "seem to fit" |
| Decade bounds match historical record | A category active 1965–1982 uses `1960s`, `1970s`, `1980s` — not extended to 1990s without evidence |
| New categories follow Add/Split/Retire protocol | Add: demonstrate density + coherence + archival necessity. Split: existing category has ≥2 internally distinct sub-populations. Retire: category catches <3 films for 2+ audit cycles |

**Test:** If you remove all films from the collection, does the category definition still make sense as a description of a real film-historical movement? If yes, grounding is working. If the category only exists because of specific films you own, it's post-hoc.

### Rule 5: Constraint Gates

Find the binding constraint before optimising. Don't run expensive stages on defective data.

**The constraint protocol:**
1. **Map value flow** at each stage boundary — what data is produced upstream, what is consumed downstream, what is lost
2. **Identify the binding constraint** — the handoff where the most valuable information is destroyed
3. **Add a gate** — validate that critical data survived the boundary ($0, reads checkpoint files)
4. **Fix the root cause** — fix the upstream stage so the gate passes; then the constraint moves

**Cost ordering — cheap checks first:**

| Check | Cost | Run when |
|-------|------|----------|
| Handoff validation (checkpoint read) | $0 | After every stage |
| Schema contract check | $0 | After every stage |
| Full API measurement | $$ | Only when all gates pass |
| Manual review | Time | Only when metrics are ambiguous |

**This project's binding constraints (known):**
- TMDb result validation (`_validate_result()` in `lib/tmdb.py`) — prevents cache poisoning that compounds over runs
- OMDb country code mapping (`_map_countries_to_codes()` in `lib/omdb.py`) — corrupt 2-letter codes silently misroute all downstream Satellite classification
- Director matching (`_director_matches()` in `lib/satellite.py`) — substring vs whole-word determines false-positive rate for all Satellite routing

### Rule 6: Boundary-Aware Measurement

The classification pipeline has a natural boundary: **enrichment** (API queries + data merge) vs. **routing** (tier assignment + destination building).

| What changed | Measure on |
|-------------|------------|
| Parser or API logic | Enrichment metrics only (data completeness, field coverage) |
| Routing rules, constants, tier logic | Routing metrics only (classification rate, tier distribution) |
| Both sides | Full pipeline |

**Cost-ordering principle:** If only enrichment changed, don't re-run the full classification on 491 films ($$ in API calls). Validate the handoff ($0), measure enrichment quality ($), skip routing measurement entirely.

**Scoping rule:** `classify.py` Stage 1–4 is enrichment. Stages 5–8 are routing. A change to `lib/tmdb.py` only requires re-measuring Stages 1–4; a change to `lib/satellite.py` only requires Stages 5–8.

### Rule 7: Measurement-Driven Development

After any pipeline change, follow this cycle:

```
IDENTIFY (what failed?) → DIAGNOSE (which stage? use R/P Split, Pattern-First)
  → FIX → VALIDATE HANDOFFS ($0) → MEASURE DEPTH (target case before/after)
  → REBALANCE (if new metric/stage added) → MEASURE BREADTH (regressions?)
  → STABILIZE (document what changed with metric evidence)
```

**Two modes:**
- **Frontier (depth-first):** Pushing capability — targets single case or small set. High-risk, high-reward. Use when a case is missing something obviously important.
- **Consistency (breadth-first):** Preventing regressions — targets full corpus. Lower-risk, systematic. Use after frontier changes, before declaring stable.

**The ratio shifts over time.** Early development is mostly frontier (build capability). Mature development is mostly consistency (prevent regressions). This project is transitioning: enrichment is mature (consistency work), routing still has frontier gaps (American New Hollywood, US 1960s–1970s mainstream).

### Rule 8: Prototype Building

Don't build until the pattern is confirmed. Exploration must complete before execution.

```
EXPLORATION (must complete first):
1. Problem Definition    → State it in one sentence
2. Decomposition         → What are the sub-problems?
3. Pattern Recognition   → What approach will work? Test against real case
4. Abstraction           → Classify tasks as R/P before building
─────────────────────────────────────────────────────────
EXECUTION (only after exploration):
5. Build                 → Follow the confirmed pattern
```

**Real Case First:** Never build in the abstract. Start with one real film, one real classification, one real failure case. The real case forces concrete decisions and reveals hidden assumptions.

**Rabbit hole detection:**

| Signal | Recovery |
|--------|----------|
| "This changes everything" | Probably doesn't — restate original problem |
| Same problem reframed 3+ times | Lost the thread — what's the one concrete test case? |
| 1000+ words explaining a simple fix | Over-engineering — what's the simplest thing that works? |
| Building infrastructure for hypothetical use | Premature optimisation — can you do it manually first? |

### Rule 9: Creative & Discovery

Two task types that Rules 1–3 don't cover: **Discovery** (exploring before the problem is defined) and **Creative** (no single correct answer).

**Discovery protocol (e.g. "Should Romanian New Wave be a Satellite category?"):**
1. Define the output form before exploring — not what you'll find, but what shape the answer takes
2. Set stopping criteria — discovery is complete when the next Precision/Reasoning task can be written with no unknowns
3. Scope before depth — survey breadth first (how many films?), depth (per-film research) second
4. Rabbit-hole tripwire — if you can't answer "what would done look like?", you're still in problem definition

**Creative protocol (e.g. "Which 50 films belong in the Reference canon?"):**
1. State evaluation criteria before generating options — criteria must predict what a new option looks like
2. Apply criteria, don't reverse-engineer them — select options that meet criteria; don't generate a list then write criteria to justify it
3. "Done" is criteria-passing, not consensus — defensible against the published framework (Domain Grounding) is the bar
4. Bound the iteration — 2–3 revision passes max, then ship and revisit if new evidence contradicts

**Handoff rule:** Discovery and Creative tasks are complete only when their output is documented in a form that feeds the next task. "We decided X" is not a handoff. "We updated SATELLITE_ROUTING_RULES with entry Y" is.

### Rule 10: Data Readiness

Before routing, assess whether enough data exists to produce a meaningful classification.

**Readiness levels:**

| Level | Data Present | Action |
|-------|-------------|--------|
| R0 | No year | Hard stop → `unsorted_no_year` (already implemented) |
| R1 | Title + year, no director AND no country | Skip Stages 4-8 → `unsorted_insufficient_data` |
| R2 | Partial (director OR country, not both) | Route but cap confidence at 0.6 |
| R3 | Full (director AND country AND genres) | Full pipeline, no confidence cap |

**Key principle:** Don't run routing on films that lack the data routing needs. 126 films currently enter all 9 routing stages with empty data and fail at each one — the reason code `unsorted_no_director` conflates "no data available" with "no rule matched." R1 early exit distinguishes these populations.

**Assessment point:** After `_merge_api_results()` (Stage 1), before routing (Stages 2+). $0 cost field check.

### Rule 11: Certainty-First Classification

Classify what you can prove first. Use proven classifications as anchors. Expand outward with decreasing certainty but increasing gates.

**Category certainty tiers:**

| Tier | Categories | Gates | Auto? |
|------|-----------|-------|-------|
| 1 | Giallo, Brazilian Exploitation, HK Action, Pinku Eiga, American Exploitation, European Sexploitation, Blaxploitation | country + genre + decade + directors (4+) | Yes |
| 2 | Classic Hollywood, French New Wave, American New Hollywood | director/country + decade + keywords (3) | Yes |
| 3 | Music Films, Indie Cinema | genre/country + decade (2, negative-space) | Review-flagged |
| 4 | Japanese Exploitation, Cult Oddities | Manual only | No |

**The anchor-then-expand pattern:**
1. Establish anchors — explicit lookups (SORTING_DATABASE) + Reference canon + SATELLITE_TENTPOLES
2. High-certainty routing — Tier 1-2 categories auto-classify with standard confidence
3. Fuzzy expansion (gated) — R2 films with no rule match get SUGGESTED to review queue based on anchor proximity, not auto-classified

**Inverse gate rule:** As certainty decreases, gates get stricter. Tier 1 match → auto-classify. Tier 3 match → flag for review. Tier 4 → manual only via SORTING_DATABASE.

### Rule 12: Curation Loop

Every classification is a suggestion until a curator confirms it. Curatorial decisions feed back into the system.

**Four curator actions:**

| Action | When | System Effect |
|--------|------|--------------|
| Accept | Classification correct | Move file to destination |
| Override | Classification wrong, curator knows correct | Stage entry for SORTING_DATABASE.md |
| Enrich | Data missing, curator can supply | Write to `manual_enrichment.csv`, reclassify |
| Defer | Uncertain, needs research | Park in review queue for next cycle |

**The review queue:** Films with confidence < 0.5 go to `output/review_queue.csv` — a staging area for classifications that need human confirmation. Tier 3-4 auto-classifications, R2/R3 unsorted films, and re-audit discrepancies populate the queue.

**Lifecycle completion:** Accept = Stage 3 execution. Override = Stage 5 reinforcement. Enrich = Stage 3 input quality improvement. This closes the lifecycle gap where Stages 3-5 produce reports but have no execution tools.

**Enrich before Override:** Prefer enrichment (systemic improvement — helps all films by that director) over override (point fix — helps only this specific film).

---

## §4 Project-Specific Rules

### Format Signals Are Metadata, Not Classification
`35mm`, `4K`, `Criterion`, `Open Matte` are edition metadata. They describe HOW a film is collected, not WHERE it belongs. A 35mm print of Breathless is Core (Godard), not Popcorn. Format signals are stripped during normalization but preserved in the manifest for curatorial reference.

### Symmetric Normalization
`normalize_for_lookup()` in `lib/normalization.py` MUST be used identically when:
- Building the lookup database (parsing SORTING_DATABASE.md)
- Querying against it (classifying a filename)

The v0.1 core bug was asymmetric normalization — building stripped format signals, querying didn't. If you change normalization, change it in ONE place and verify both paths use it.

### Single Source of Truth
All constants live in `lib/constants.py` ONLY:
- `FORMAT_SIGNALS` — 22 format/edition markers
- `RELEASE_TAGS` — 30+ encoding/release metadata markers
- `LANGUAGE_PATTERNS` — 13 language detection regexes
- `COUNTRY_TO_WAVE` — country → satellite category routing
- `REFERENCE_CANON` — 50-film hardcoded canon
- `SUBTITLE_KEYWORDS` — 21 parser subtitle detection terms

Never duplicate these lists. Import from `lib/constants`.

### Lookup Before Heuristics
SORTING_DATABASE.md contains hundreds of human-curated `Title (Year) → Destination` mappings. The classifier checks this BEFORE any heuristic (Core/Reference/Satellite checks). Human curation overrides algorithmic classification.

### Reference Canon Takes Priority Over User Tags
If a film is in the 50-film Reference canon, it's Reference — even if a user previously tagged it differently. The canon is an explicit design decision.

### Satellite Categories Are Decade-Bounded
Country → satellite routing only applies within historically valid decades:
- Brazil → Brazilian Exploitation: 1960s–1990s (pornochanchada peak 1970–1989; wider tradition extends to mid-1960s and early 1990s — WIDENED Issue #20)
- Italy → Giallo: 1960s–1980s only
- Japan → Pinku Eiga: 1960s–1980s only
- France → French New Wave: 1950s-1970s only (Issue #14, audited Issue #22)
  - Director-only routing. France ('FR') is intentionally excluded from COUNTRY_TO_WAVE — adding it would auto-route all French films in those decades to FNW regardless of movement membership.
  - Core directors (Godard, Varda, Chabrol, Demy, Duras, Resnais, Rivette) exit at Stage 3 and never reach this Satellite entry.
  - Non-Core FNW directors: Truffaut, Marker, Malle, Eustache, Robbe-Grillet, Rohmer (1960s-1970s), Resnais/Rivette (safety net; Core check fires first when core_db active).
  - Unknown French film with no director match falls to European Sexploitation (FR + Drama/Romance + 1960s) then Unsorted — documented expected behaviour (Issue #22 Scenario B).
- Hong Kong → HK Action: 1970s–1990s only
- US → American Exploitation: 1960s-1980s only (NARROWED - Issue #14)
- US → Classic Hollywood: 1930s-1950s only (NEW - Issue #14)
- International → Indie Cinema: 1960s-2020s, 30+ countries (WIDENED Issue #20 — functional catch-all, not a historical wave; see MARGINS_AND_TEXTURE.md §2)
  - NOTE: US intentionally excluded from country_codes. US has Classic Hollywood (1930s-1950s), American Exploitation (1960s-1980s), Blaxploitation. Non-matching US films → Unsorted. US indie directors (Jarmusch, Hartley, Larry Clark etc.) still route via directors list.

A 2010s Italian thriller is NOT Giallo. Decades are structural, not arbitrary.

### Never Modify SORTING_DATABASE.md Programmatically
`docs/SORTING_DATABASE.md` is human-curated. Code reads it; humans edit it. Never write to it from scripts.

### Dual-Source API Enrichment (v0.2+)
The classifier uses **parallel query with smart merge**, not fallback:

**Why parallel not fallback:**
- TMDb often returns empty `countries: []` for foreign films
- OMDb (= IMDb data) has superior country coverage
- Country data is critical for Satellite routing (Italy→Giallo, Brazil→Brazilian Exploitation)
- Querying both maximizes data quality

**Field-specific merge priority:**
- **Director:** OMDb > TMDb > filename (OMDb = IMDb = authoritative)
- **Country:** OMDb > TMDb > filename (OMDb fixes TMDb's weakness)
- **Genres:** TMDb > OMDb (TMDb has richer structured data)
- **Year:** filename > OMDb > TMDb (filename is curated, highest trust)
- **Text (overview/plot):** longer source wins — Wikipedia > TMDb overview > OMDb plot (encyclopedic preferred; deferred pending Issue #29)

**Fields extracted from each API (Issue #29 adds text fields):**

| Field | TMDb | OMDb | Notes |
|---|---|---|---|
| director | ✓ | ✓ | OMDb wins |
| countries | ✓ | ✓ | OMDb wins |
| genres | ✓ | ✓ | TMDb wins |
| keywords | ✓ | — | Used for Satellite keyword routing (Issue #29) |
| overview | ✓ | — | Plot summary — add to result dict (Issue #29) |
| tagline | ✓ | — | Marketing tagline — add to result dict (Issue #29) |
| plot | — | ✓ | Add `plot=full` param; extract `Plot` field (Issue #29) |
| popularity | ✓ | — | Popcorn signal |
| vote_count | ✓ | ✓ | Popcorn signal |

**Keyword routing (Issue #29):** Each satellite category defines a `keyword_signals` list in `SATELLITE_ROUTING_RULES`. Keyword evidence adds two new routing sub-rules inside the Satellite stage:
- **Tier A:** country + decade + keyword match → route (keyword substitutes for genre gate)
- **Tier B:** TMDb keyword alone → route (French New Wave and American New Hollywood only — movement-specific tags are high-confidence without structural corroboration)

Keyword signals apply to **positive-space categories only** (named historical movements with distinctive vocabulary). Indie Cinema and Popcorn have no keyword routing — they are negative-space categories defined by the absence of other signals. See `docs/theory/MARGINS_AND_TEXTURE.md` §8.

**Implementation:** `classify.py` methods `_query_apis()` and `_merge_api_results()` handle parallel querying and intelligent merging. Both APIs use persistent JSON caching to minimize costs.

### Tier-First Folder Structure (v0.2+)
The library uses **tier-first** organization, not decade-first:

```
✅ CORRECT (tier-first):
Core/1960s/Jean-Luc Godard/
Reference/1960s/
Satellite/Giallo/1970s/
Popcorn/1980s/

❌ WRONG (decade-first, legacy):
1960s/Core/Jean-Luc Godard/
1960s/Reference/
1970s/Satellite/Giallo/
1980s/Popcorn/
```

**Why tier-first?** The 4-tier hierarchy is the PRIMARY organizational pattern. Decades are secondary metadata. This allows:
- Each tier to be a separate Plex library
- Core = complete auteur filmographies
- Reference = canonical films from non-Core directors
- Satellite = margins/exploitation by category
- Popcorn = pleasure viewing

**Curatorial rule:** Core directors stay in Core even for canonical films. A Kubrick masterpiece goes in Core/1960s/Stanley Kubrick/, not Reference. Reference is for canonical films by NON-Core directors.

---

## §5 Key Commands

```bash
# Run tests
pytest tests/

# Normalize filenames — Stage 0 pre-stage (Issue #18)
python normalize.py <source_directory>              # dry-run, writes rename_manifest.csv
python normalize.py <source_directory> --execute   # apply renames
python normalize.py <source_directory> --nonfim-only  # show only TV/supplementary flags

# Classify films (never moves files)
python classify.py <source_directory>

# Dry-run moves (DEFAULT — safe to run)
python move.py --dry-run

# Execute moves (requires explicit flag)
python move.py --execute

# Create folder structure
python scaffold.py

# Thread discovery (Issue #12)
python scripts/build_thread_index.py --summary      # Build keyword index
python scripts/thread_query.py --discover "Film"    # Find thread connections
python scripts/thread_query.py --thread "Category"  # Query category keywords
python scripts/thread_query.py --list --verbose     # List all tentpoles

# Cache invalidation (Issue #16) — run after title cleaning changes
python scripts/invalidate_null_cache.py conservative  # Remove entries missing both director AND country
python scripts/invalidate_null_cache.py aggressive    # Remove all null entries

# Handoff validation (Issue #16) — quality gates for pipeline handoffs
python scripts/validate_handoffs.py                   # Self-test demonstration

# Full library inventory — run after each batch of moves (Issue #17)
python audit.py                                       # Walk all tier folders → output/library_audit.csv
# Load library_audit.csv in dashboard for collection-wide classification rate
# (sorting_manifest.csv = Unsorted work queue only; library_audit.csv = full library)

# RAG semantic search — cross-concept questions across all docs
python3 -m lib.rag.query "How does Satellite routing work?"           # Top-5 results
python3 -m lib.rag.query "Satellite decade boundaries" --filter AUTHORITATIVE  # Authority-filtered
python3 -m lib.rag.query "Films by Lucio Fulci" --json --top 10      # JSON output, more results
python3 -m lib.rag.indexer --force                                    # Rebuild index after doc changes
```

---

## §6 Files to Never Commit

- `config.yaml` / `config_external.yaml` — contain paths and API keys
- `output/*.csv` — generated manifests (sorting_manifest.csv, rename_manifest.csv)
- `output/tmdb_cache.json` — API response cache
- `output/rag/` — RAG index and embeddings (rebuilt locally with `python3 -m lib.rag.indexer --force`)
- `.DS_Store`
- `__pycache__/`, `*.pyc`
