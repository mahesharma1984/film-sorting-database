# CLAUDE.md — Film Sorting Database

## §1 Startup

On every interaction, read:
1. `docs/CORE_DOCUMENTATION_INDEX.md` — find any doc quickly
2. `docs/DEVELOPER_GUIDE.md` — how to make changes safely

For curatorial context, read `docs/theory/README.md` → individual essays as needed.

---

## §2 Work Modes

### Build / Feature Mode
Read first:
- `REFACTOR_PLAN.md` — v1.0 architecture (3-script design)
- `docs/theory/TIER_ARCHITECTURE.md` — why tiers work this way
- `docs/theory/MARGINS_AND_TEXTURE.md` — satellite logic rationale

### Debug / Regression Mode
Read first:
- `docs/DEBUG_RUNBOOK.md` — symptom → diagnosis → fix
- `issues/` — past bugs and their root causes
- `docs/WORK_ROUTER.md` — route symptoms to the right doc

### Understanding Mode
Read first:
- `docs/theory/README.md` — reading order for all 7 theory essays
- `docs/PROJECT_COMPLETE_SUMMARY.md` — collection stats and tier ratios

---

## §3 Decision Rules

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
Core (auteur identity) → Reference (canon, 50-film cap) → Satellite (margins/exploitation) → Popcorn (pleasure) → Unsorted
```

This priority order is a design decision, not an implementation detail. The classifier checks tiers in this order — first match wins. Never reorder without explicit redesign.

The classification pipeline checks in this priority:
1. Explicit lookup (SORTING_DATABASE.md) — human-curated, highest trust
2. Core director check — whitelist match
3. Reference canon check — 50-film hardcoded list
4. User tag recovery — trust previous human classification
5. Language/country → Satellite routing (decade-bounded)
6. Default → Unsorted with reason code

### Rule 3: Failure Gates

Every check declares what happens on failure:

| Check | Hard Gate (stops) | Soft Gate (continues) |
|-------|-------------------|-----------------------|
| Parser: no year extracted | Cannot route to decade → Unsorted | — |
| Parser: no director | — | Continue without director (still classifiable via lookup/reference) |
| Filesystem: dest drive not mounted | Cannot move files → abort | — |
| TMDb/OMDb: no API keys or both fail | — | Continue with filename-only classification |
| Lookup: no match in SORTING_DATABASE | — | Continue to heuristic checks |
| Core director: no whitelist match | — | Continue to Reference check |

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
- Brazil → Brazilian Exploitation: 1970s–1980s only
- Italy → Giallo: 1960s–1980s only
- Japan → Pinku Eiga: 1960s–1980s only
- France → French New Wave: 1950s-1970s only (NEW - Issue #14)
- Hong Kong → HK Action: 1970s–1990s only
- US → American Exploitation: 1960s-1980s only (NARROWED - Issue #14)
- US → Classic Hollywood: 1930s-1950s only (NEW - Issue #14)
- International → Indie Cinema: 1980s-2020s (NEW - Issue #14)

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
```

---

## §6 Files to Never Commit

- `config.yaml` / `config_external.yaml` — contain paths and API keys
- `output/*.csv` — generated manifests
- `output/tmdb_cache.json` — API response cache
- `.DS_Store`
- `__pycache__/`, `*.pyc`
