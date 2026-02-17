# Issue #17: Manifest Reconciliation — Decade-First to Tier-First Migration

**Status:** Closed (2026-02-17)
**Branch:** feature/v02-enhanced-classification
**Priority:** High

---

## Background

The library has been through two pipeline generations:

- **v0.1 pipeline** — organized files into **decade-first** paths: `1960s/Core/Jean-Luc Godard/`
- **v0.2 pipeline** — switched to **tier-first** paths: `Core/1960s/Jean-Luc Godard/`

The v0.2 pipeline (classify.py + move.py) correctly targets tier-first destinations, but the physical files on disk were moved by the v0.1 pipeline into decade-first paths. This structure mismatch was never reconciled.

A full audit against `full_library_manifest.csv` (1,202 entries, the most complete historical record) reveals:

| Category | Count | Share |
|----------|-------|-------|
| File at expected location | 954 | 79% |
| File exists, wrong location | 248 | 21% |
| File missing from disk entirely | 0 | 0% |

**Nothing is lost.** All 1,202 manifest entries exist on disk. The problem is purely structural.

---

## Root Cause Analysis

### Cause 1: Decade-first paths not migrated (142 files, 57% of mismatches)

The largest group. Files are **correctly classified** (tier, director, decade all correct) but live in the old decade-first path format. The manifest expects tier-first.

```
Manifest expects:  Core/1960s/Jean-Luc Godard/Bande a part (1964).mkv
On disk at:        1960s/Core/Jean-Luc Godard/Bande a part (1964).mkv
```

These files span all tiers. No reclassification needed — just a path migration.

**Affected legacy folders:**
- `1950s/` — 3 files
- `1960s/` — 7 files
- `1970s/` — 4 files
- `1980s/` — 2 files
- `1990s/` — 3 files
- Decade-first paths inside tier folders (remainder) — ~123 files

### Cause 2: Core director films stranded in Popcorn (29 files, 12% of mismatches)

Films by Core directors (Scorsese, De Palma, others) that the classifier correctly assigned to `Core/` but `move.py` never executed. They remain in `Popcorn/` from a prior placement.

```
Classifier output:  Core/1990s/Brian De Palma/Snake Eyes (1998).mkv
On disk at:         Popcorn/1990s/Snake Eyes (1998).mkv
```

These are genuine tier errors, not just path format errors.

### Cause 3: Previously unsorted, now correctly placed (53 files, 21% of mismatches)

Files the manifest once tracked as `Unsorted` that have since been correctly routed by an improved classifier. These are in the right place. No action needed — this category is informational only.

### Cause 4: Manifest coverage gap

`sorting_manifest.csv` (current, 693 entries) is a **work queue**, not a permanent inventory. Once files were moved, they fell off the manifest. `full_library_manifest.csv` (1,202 entries) is the more complete record, but even that covers only 70% of the 1,715 files on disk. The remaining ~500 files were manually curated before any pipeline ran and have never been enumerated.

---

## Stages

### Stage 1: Migrate legacy decade-first folders (Cause 1, ~19 files)

The small set of files still in top-level `1950s/`–`1990s/` folders. These are the most visible and easy to verify.

**Files to move:**

| From | To |
|------|----|
| `1950s/Reference/` | `Reference/1950s/` |
| `1960s/Core/Júlio Bressane/` | `Core/1960s/Júlio Bressane/` |
| `1960s/Core/Orson Welles/` | `Core/1960s/Orson Welles/` |
| `1960s/Core/Pier Paolo Pasolini/` | `Core/1960s/Pier Paolo Pasolini/` |
| `1960s/Satellite/American Exploitation/` | `Satellite/American Exploitation/1960s/` |
| `1960s/Satellite/Classic Hollywood/` | `Satellite/Classic Hollywood/1960s/` |
| `1970s/Core/John Cassavetes/` | `Core/1970s/John Cassavetes/` |
| `1970s/Satellite/Giallo/` | `Satellite/Giallo/1970s/` |
| `1980s/Core/Claude Chabrol/` | `Core/1980s/Claude Chabrol/` |
| `1980s/Satellite/Hong Kong Action/` | `Satellite/Hong Kong Action/1980s/` |
| `1990s/Popcorn/` | `Popcorn/1990s/` |

**Approach:** Write a targeted migration script. Dry-run first, then execute. Remove empty legacy decade folders after.

**Success criteria:** `1950s/`–`1990s/` top-level folders no longer exist or are empty.

---

### Stage 2: Move Core director films out of Popcorn (Cause 2, 29 files)

Run `move.py --dry-run` and verify the 29 Core-director films are correctly targeted, then execute.

**Spot-check examples before executing:**
- `Who's that Knocking at My Door` (Scorsese, 1967) → `Core/1960s/Martin Scorsese/`
- `The Bonfire of the Vanities` (De Palma, 1990) → `Core/1990s/Brian De Palma/`
- `Snake Eyes` (De Palma, 1998) → `Core/1990s/Brian De Palma/`

**Approach:** Run `python move.py --dry-run`, inspect output for these 29 files, then run `python move.py --execute`.

**Success criteria:** No Core-director films remain in `Popcorn/`.

---

### Stage 3: Full library enumeration (Cause 4, ~500 untracked files)

The ~500 manually curated files that have never been processed by classify.py. These exist correctly on disk but are invisible to the manifest.

**Approach options:**
- A) Point `classify.py` at the existing tier folders to enumerate them (check if supported)
- B) Write a standalone inventory script that walks the organized library and generates manifest rows for files already in place, without reclassifying them
- C) Accept the gap — treat the manifest as a work-queue artifact, not a full inventory

**Decision (2026-02-17): Option C — accept the gap.** The manifest is a classification *work queue*, not a permanent inventory. The ~500 manually curated files were placed correctly by human curation before any pipeline ran and do not need re-processing. If a full inventory is later needed, it should be a separate issue (new standalone script, distinct from the work-queue manifest).

**Success criteria:** N/A — Stage 3 explicitly deferred.

---

### Stage 4: Reconcile sorting_manifest.csv against full_library_manifest.csv

After Stages 1–3, regenerate `sorting_manifest.csv` from a fresh classify run so it reflects the current state of the full library. The current manifest (693 entries) is stale relative to the 1,202-entry full library manifest.

**Success criteria:** Single authoritative manifest covering all files; no phantom entries for files that don't exist.

---

## Files Implicated

| File | Role |
|------|------|
| `output/full_library_manifest.csv` | Most complete historical record (1,202 entries) |
| `output/sorting_manifest.csv` | Current active manifest (stale, 693 entries) |
| `move.py` | Executes physical file moves |
| `classify.py` | Generates manifest entries |
| `docs/SORTING_DATABASE.md` | Human-curated lookup — do not modify programmatically |

---

## Resolution (2026-02-17)

| Stage | Status | Result |
|-------|--------|--------|
| Stage 1: Migrate decade-first folders | ✅ Done | 16 files moved, all 1950s–1990s legacy folders removed |
| Stage 2: Move Core films out of Popcorn | ✅ Done | 5 Core films moved (Scorsese, De Palma ×2, Jarmusch, Wong Kar-wai) |
| Stage 3: Full library enumeration | ⏭ Deferred | Option C accepted — manifest remains a work queue |
| Stage 4: Regenerate sorting_manifest.csv | ✅ Done | Fresh classify run against Unsorted queue |

**Regression check:** 0 regressions. No previously-classified films dropped to Unsorted.

**Residuals:** A small number of Core films with dirty filenames may remain Unsorted. Deferred to Issue #18 (normalize.py pre-classification stage).

---

## Known Pre-Existing State (Do Not Regress)

- `Staging/` folders (Borderline, Evaluate, Unknown, Unwatched) — manual curator workflow, do not touch
- `Out/Cut/` — archived/culled films, do not move
- `Core (Gallo) OR Popcorn?/` and `Reference OR Popcorn?/` — curator indecision markers, leave for manual resolution
- `ANGEL TERMINATORS 2 x264.mkv` — correctly placed in `Satellite/Hong Kong Action/1980s/` despite parser failure (no year in filename); do not move to Unsorted
