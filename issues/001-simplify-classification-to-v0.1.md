# Issue #001: Simplify classification system to v0.1 — Two-Pass Binary Sort

**Priority:** High
**Type:** Refactor / Simplification
**Status:** Open

---

## Problem

The current classification system is too complex for reliable AI-assisted execution. With staging at ~90%, the system works well for clear-cut cases but the heuristic stack is too deep:

- 7+ classification strategies in priority order
- Multi-strategy fuzzy matching (exact, substring, last-name, 85% threshold)
- TMDb API dependency with caching layer
- 12 Satellite subcategories with individual hard caps
- Subjective Popcorn "Tonight Test" criteria
- Multi-decade director routing logic
- Staging subcategory routing (Borderline/Unknown/Unwatched/Evaluate)

~42% of the collection still lands in Staging because the middle ground between "obvious match" and "no match" is massive. The system needs to be rebuilt from a minimal base that achieves near-100% accuracy on what it does classify, and leaves the rest for manual review.

---

## Proposal: v0.1 — Two-Pass Binary Sort

### Pass 1: Known vs. Unknown

One question per film: **do we have an explicit, exact rule for this?**

| Check | Method | Result |
|---|---|---|
| Director is on Core whitelist | **Exact string match only** (case-insensitive, no fuzzy) | → Core/{Decade}/{Director}/ |
| Film is in SORTING_DATABASE.md | Explicit lookup, already manually classified | → Whatever path is specified |
| Neither | — | → Unsorted/ |

Expected outcome: ~200-250 films placed with 100% accuracy.

### Pass 2: Country-Based Satellite Triage

For remaining Unsorted films, use **one signal only** — country of origin (parsed from filename or basic metadata):

| Signal | Classification |
|---|---|
| Brazil | → Satellite/Brazilian Exploitation |
| Japan + pre-1990 | → Satellite/Pinku Eiga |
| Italy + horror/thriller genre | → Satellite/Giallo |
| Hong Kong | → Satellite/HK Action |
| USA + format signal in filename (35mm, Open Matte, etc.) | → Popcorn/ |
| Everything else | → Unsorted/ (manual review) |

No fuzzy matching. No API calls. No caps. No confidence scores.

---

## What Gets Removed in v0.1

| Feature | Reason for removal |
|---|---|
| Fuzzy director matching (ratio, substring, last-name) | High error rate on edge cases, false positives |
| TMDb API integration + caching | External dependency, adds complexity for marginal gain at this stage |
| Category caps per Satellite subcategory | Premature — sort first, curate later |
| Popcorn "Tonight Test" / subjective criteria | Can't be automated, manual decision |
| Reference tier auto-detection | Only ~35 films — faster to just hardcode or do manually |
| Satellite subcategory boundary rules | Nuanced curatorial judgment, not automatable |
| Multi-decade director routing | Sort by director first, organize into decades manually |
| Staging subcategories (Borderline/Unknown/Unwatched/Evaluate) | One bucket: Unsorted. That's it. |
| Format signal detection for tier promotion | Keep detection, but only for Popcorn hint, not tier logic |

---

## Target Architecture

```
classify_v01.py          (~100 lines)
lib/
  core_directors.py      (simplified: exact match dict only)
  lookup.py              (unchanged: reads SORTING_DATABASE.md)
  parser.py              (unchanged: filename parsing)
```

**Output:** Single CSV manifest with columns:
- `filename`, `title`, `year`, `director`, `tier`, `destination`, `reason`

**Three possible `reason` values:**
1. `core_director_exact` — director matched whitelist exactly
2. `explicit_lookup` — found in SORTING_DATABASE.md
3. `country_signal` — country-based Satellite/Popcorn routing
4. `unsorted` — no match, needs manual review

---

## Incremental Build-Up Path

| Version | Adds | Complexity |
|---|---|---|
| **v0.1** | Exact director match + explicit lookup + country routing | ~100 lines |
| **v0.2** | Hardcoded Reference tier (~35 films) | +20 lines |
| **v0.3** | TMDb enrichment for films with missing directors only | +50 lines |
| **v0.4** | Fuzzy director matching with manual review queue (not auto-sort) | +80 lines |
| **v0.5** | Category caps + Staging subcategories | +60 lines |
| **v1.0** | Full system as currently designed | Current codebase |

Each version should be tested against the full collection before moving to the next. The metric that matters: **accuracy of what it classifies** (not coverage). 100% accuracy on 250 films beats 80% accuracy on 500.

---

## Acceptance Criteria

- [ ] `classify_v01.py` runs against the full collection
- [ ] Every Core director match is exact (no false positives)
- [ ] Every explicit lookup match is correct
- [ ] Unsorted bucket catches everything else cleanly
- [ ] Output CSV is generated with clear `reason` column
- [ ] No external API calls required
- [ ] Dry-run mode (classify only, no file moves)
- [ ] Runs in under 5 seconds for 850 files
