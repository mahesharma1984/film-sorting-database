# Issue #24: Architecture documentation drift — three places where docs and code have diverged

**Severity:** Medium
**Component:** `CLAUDE.md`, `REFACTOR_PLAN.md`, `classify.py`
**Type:** Architecture / documentation correctness
**Discovered via:** Architecture analysis (exports/knowledge-base)

---

## Summary

Three places where the documented architecture no longer matches the running code. Each is independent but all three share the same root cause: the docs were written for the v0.1 design and were not fully updated when Issue #14 and the v0.2 pipeline refactor changed behaviour. A developer reading `CLAUDE.md` or `REFACTOR_PLAN.md` will build a mental model of the system that is wrong in three specific ways.

---

## Gap A: Popcorn/Satellite priority order contradiction

### What the docs say

`CLAUDE.md §3 Rule 2`:
```
Core (auteur identity) → Reference (canon, 50-film cap) → Satellite (margins/exploitation)
→ Popcorn (pleasure) → Unsorted
```

`REFACTOR_PLAN.md:140-162` pipeline diagram:
```
[REASONING via rules] Satellite classification
  │         ...
  ▼ (only if not Satellite)
  │
[REASONING via rules] Popcorn check
```

Both documents state: Satellite before Popcorn.

### What the code does

`classify.py:547` (comment added by Issue #14):
```python
# === Stage 6: Popcorn check (MOVED UP - Issue #14 priority reorder) ===
# Check Popcorn BEFORE Satellite to prevent mainstream films from
# being caught by exploitation categories (especially post-1980)
```

Popcorn runs at Stage 6. Satellite runs at Stages 7–8. The actual order is: **Popcorn before Satellite**.

### Why this matters

This is not an error in the code — Issue #14 made a deliberate, reasoned decision to flip the order. The problem is that `CLAUDE.md §3 Rule 2` still presents the old order as a canonical design principle with the phrase "This priority order is a design decision, not an implementation detail." A developer encountering an unexpected Popcorn classification for a 1970s exploitation film will look at `CLAUDE.md`, conclude the code has a bug, and attempt to "fix" it — when the code is correct and the docs are wrong.

### The downstream consequence

The current Popcorn-first logic means: any film that passes the Popcorn heuristics (`has_mainstream_country AND has_mainstream_genre AND (has_star_actor OR has_popularity)`) will be routed to Popcorn before Satellite is checked. For most mainstream films this is the right call. The risk case is a film that passes the Popcorn heuristics but also has exploitation signals — e.g., a high-popularity 1975 Italian film with Action genres. Issue #14 resolved this with the `EXPLOITATION_TITLE_KEYWORDS` guard in `popcorn.py:44-46`, which is the real gate preventing exploitation films from landing in Popcorn. That guard is not documented in `CLAUDE.md` at all.

---

## Gap B: Staging tier is dead code

### What the docs say

`REFACTOR_PLAN.md:155-162`:
```
[PRECISION] Staging assignment
            Has director but no tier match → Staging/Borderline
            Missing metadata even after TMDb → Staging/Unknown
```

The plan specifies two Staging destinations as the final-fallback output of the pipeline, distinguishing films with a director (resolvable) from films without metadata (unknown).

### What the code does

`classify.py:598-615` — the default branch produces `tier='Unsorted'` unconditionally. No path through the pipeline assigns `tier='Staging'`.

`classify.py:154-155` — `_build_destination()` contains a `Staging` branch:
```python
elif tier == 'Staging':
    return f'Staging/{decade}/' if decade else 'Staging/'
```

`write_staging_report()` (`classify.py:678-696`) filters for `r.tier == 'Unsorted'`, not `'Staging'`.

The scaffolding, destination builder, and reporting infrastructure for Staging all exist. The classification pipeline never produces the tier that would use them.

### Why this matters

`Staging/Borderline` and `Staging/Unknown` were designed as a triage layer — a holding space for films that are resolvable with more human input, distinguished from films that are genuinely unknown. Collapsing both into `Unsorted` means:
- Films with a director that simply didn't match (probably need a lookup entry) are mixed with films that have no metadata at all (need a different workflow)
- The Unsorted queue is larger and less actionable than it should be
- The `audit.py` inventory cannot distinguish these two populations

---

## Gap C: `--no-tmdb` silently disables OMDb

### What the flag name says

`--no-tmdb` implies: disable TMDb only. OMDb would continue running.

### What the code does

`classify.py:114`:
```python
if omdb_key and not self.no_tmdb:
    self.omdb = OMDbClient(...)
```

`--no-tmdb` disables both APIs. The log message at line 108 says only `"TMDb API enrichment disabled (--no-tmdb flag)"`. OMDb being disabled is not reported.

### Why this matters

`CLAUDE.md §4` explicitly documents dual-source enrichment as an architectural principle:

> **Why parallel not fallback:** TMDb often returns empty `countries: []` for foreign films. OMDb (= IMDb data) has superior country coverage. Country data is critical for Satellite routing.

`--no-tmdb` is described in the help text as an "offline classification" mode. A user running offline classification expects the explicit lookup, Core, Reference, and user tag stages to still work — which they do — but they also expect OMDb to be independent of TMDb. The current behaviour silently eliminates the API source that provides the most important data for Satellite routing (country), without any indication in the logs.

In practice, `--no-tmdb` makes Satellite routing significantly less accurate for any film where the country wasn't parsed from the filename, and the user has no way to know this has happened.

---

## Proposed Fix

### Stage 1: Update `CLAUDE.md §3 Rule 2`

Replace the pipeline order in the canonical hierarchy with the actual execution order:

```
Core (auteur identity) → Reference (canon, 50-film cap) → Popcorn (pleasure, guarded
by exploitation keyword check) → Satellite (margins/exploitation) → Unsorted

Note: Popcorn precedes Satellite since Issue #14. The EXPLOITATION_TITLE_KEYWORDS
guard in lib/popcorn.py prevents exploitation films from being misrouted to Popcorn.
```

Also update `CLAUDE.md §3 Rule 2`'s description paragraph to explain the Issue #14 rationale: mainstream films (US/GB, Action/Comedy, high popularity) should not be exposed to the Satellite heuristics because those heuristics have high false-positive rates for post-1980 mainstream content.

### Stage 2: Update `REFACTOR_PLAN.md` pipeline diagram

Swap Satellite and Popcorn in the pipeline diagram at lines 140–162 to match the actual execution order. Add a note: `(Popcorn moved before Satellite — Issue #14)`.

### Stage 3: Fix Staging tier or formally deprecate it

Two options — decide which before implementing:

**Option A: Implement Staging** — Modify `classify.py:598-615` to distinguish the two Unsorted sub-populations:
- `director is not None AND no tier match` → `tier='Staging'`, `destination='Staging/Borderline/{decade}/'`
- `director is None OR metadata missing` → `tier='Unsorted'`, `destination='Unsorted/'`

Update `write_staging_report()` to filter for both `'Staging'` and `'Unsorted'` (or separate reports).

**Option B: Formally retire Staging** — Remove the `Staging` branch from `_build_destination()`, add a comment to `REFACTOR_PLAN.md` noting it was designed but not built, and update the Unsorted report to surface the `reason` field (which already distinguishes `unsorted_no_director` from `unsorted_no_match`) as a proxy for the Staging/Borderline split.

Option B is lower cost and produces usable triage information without new tier complexity.

### Stage 4: Fix `--no-tmdb` flag

Two sub-tasks:

**4a: Rename or split the flag.** Either:
- Rename `--no-tmdb` to `--no-api` (disables both, name matches behaviour), keep `--no-tmdb` as a deprecated alias with a warning, OR
- Keep `--no-tmdb` for TMDb-only disable, add `--no-omdb` for OMDb-only, and add `--no-api` for both

**4b: Fix the log message.** At minimum, if `--no-tmdb` continues to disable both, the log should say:
```
API enrichment disabled (--no-tmdb flag disables both TMDb and OMDb)
```

Update the `--help` text to reflect actual behaviour.

### Stage 5: Update CLAUDE.md §4 dual-source section

Add a note to the `--no-tmdb` flag description:
> `--no-tmdb` disables both TMDb and OMDb. Use when operating fully offline. Satellite routing will be limited to films with country extracted from the filename.

---

## Acceptance Criteria

- [ ] `CLAUDE.md §3 Rule 2` priority order matches actual execution order (Popcorn before Satellite)
- [ ] `CLAUDE.md §3 Rule 2` explains the Issue #14 rationale and the `EXPLOITATION_TITLE_KEYWORDS` guard
- [ ] `REFACTOR_PLAN.md` pipeline diagram updated with correct order
- [ ] Staging tier either implemented (Option A) or formally retired (Option B) with docs updated
- [ ] `--no-tmdb` flag name, log output, and help text all accurately describe what is disabled
- [ ] No code changes to classification logic required (all changes are docs + flag naming)
