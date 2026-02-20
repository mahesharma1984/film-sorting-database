# Issue #28: Classification model revision — film character determines placement, not director prestige

**GitHub:** https://github.com/mahesharma1984/film-sorting-database/issues/25
**Severity:** High (philosophical conflict between design intent and implementation)
**Component:** `docs/theory/TIER_ARCHITECTURE.md`, `docs/SATELLITE_CATEGORIES.md`, `classify.py`, `lib/constants.py`
**Type:** Architecture revision — documentation first, then implementation
**Discovered via:** Taxonomy review session (2026-02-21)

---

## Summary

The current classification pipeline asserts that **director status alone determines tier** (Core director → Core, always). The correct model is that **the character of the film determines its placement** — a genre movement film by a great director belongs in its genre movement category, not in Core simply because of who made it.

---

## The Problem

### Current model (linear priority chain)

```
Core (director whitelist) → Reference → Popcorn → Satellite → Indie Cinema → Unsorted
```

**Philosophical claim in current docs:** *"identity trumps everything. A Kubrick film is Core even if it is also genre cinema."* (TIER_ARCHITECTURE.md §3)

**What this means in practice:**
- Every Godard film → Core (regardless of FNW period vs. late experimental)
- Every Scorsese film → Core (regardless of Mean Streets vs. The Departed)
- Core becomes a catch-all for "great directors" rather than curated prestige auteur work

### The correct model (character-first fork)

```
                         ┌─ Explicit lookup? ──────────────→ SORTING_DATABASE destination
                         │
                         ├─ Reference canon? ──────────────→ Reference (50 films)
                         │
ALL FILMS ───────────────┤
                         │                    ┌─ genre specialist director ──→ Satellite
                         ├─ Genre movement? ──┤
                         │                    └─ Core director, movement period → Satellite
                         │
                         ├─ Prestige auteur? ──────────────→ Core (non-genre, non-movement)
                         │
                         ├─ Popular/mainstream? ───────────→ Popcorn
                         │
                         ├─ International arthouse? ───────→ Indie Cinema
                         │
                         └─ none of the above ────────────→ Unsorted
```

**The fork:** Satellite checks before Core. A Core director's film routes to Satellite if it fits a movement; to Core if it doesn't. Director status no longer short-circuits genre membership.

---

## Tier Definitions (revised)

| Tier | Definition |
|------|-----------|
| **Reference** | The 50 canonical films. Typically one per director. Films that define cinema history, kept by obligation not just pleasure. |
| **Satellite** | Genre movement films — both from the genre's own key directors AND from Core directors whose film belongs to that movement. |
| **Core** | Best directors' prestige/non-genre work that didn't make Reference. The auteur's work outside their movement period. |
| **Popcorn** | Mainstream studio entertainment. Pleasure-driven, not identity-driven. |
| **Indie Cinema** | Arthouse catch-all — non-genre, non-prestige, non-Popcorn. |

---

## Concrete Examples of Classification Changes

| Film | Current | Correct | Why |
|------|---------|---------|-----|
| Godard — *Breathless* (1960) | Core | **Reference** | In the 50-film canon |
| Godard — *Contempt* (1963) | Core | **Satellite/FNW** | Quintessential movement film |
| Godard — *Band of Outsiders* (1964) | Core | **Satellite/FNW** | Movement period, movement style |
| Godard — *Every Man for Himself* (1980) | Core | **Core** | Late period, post-movement — stays Core |
| Scorsese — *Mean Streets* (1973) | Core | **Satellite/AmNH** | AmNH movement film |
| Scorsese — *Goodfellas* (1990) | Core | **Core** | Prestige work, past movement bounds |
| Bava — *Bay of Blood* (1971) | Satellite/Giallo | **Satellite/Giallo** | Unchanged (Bava not Core) |
| Kubrick — *2001* (1968) | Core | **Core** | Unchanged (no movement fits) |

**The natural differentiator:** The decade gate handles most cases automatically. Godard's 1960s–1970s films fall within FNW bounds; his 1980s+ films don't. The movement's historical period boundary IS the implicit scoring signal.

---

## The Scoring Model

Classification is not a linear chain — it is a scoring system where each film is evaluated against every category and placed where it fits best.

**Scoring signals (automatic + curated):**

| Signal | Source |
|--------|--------|
| Director on category director list | Curated list contents, automatic match |
| Country code match | TMDb/OMDb API |
| Decade within movement bounds | Historical bounds in constants.py |
| Genre tags match | TMDb API |
| In Reference canon | Human-curated 50-film list |
| In SORTING_DATABASE | Human override (highest trust) |

The curated layer IS the scoring. SORTING_DATABASE.md is a manual score override. The satellite director lists encode which Core directors' work routes to which movement.

---

## Documentation Conflicts (what current docs say that is now wrong)

### 1. `docs/theory/TIER_ARCHITECTURE.md` §3
> *"This priority order is a philosophical statement: **identity trumps everything**. A Kubrick film is Core even if it is also genre cinema."*

Wrong. Identity doesn't trump genre membership.

### 2. `docs/SATELLITE_CATEGORIES.md` — What Qualifies for Satellite?
> *"NO (goes to Core instead): Any film by a Core whitelist director"*

Too blunt. Core directors' genre-movement films DO qualify for Satellite.

### 3. `docs/theory/TIER_ARCHITECTURE.md` §11 — The Operational Rule
> *"Any film by a whitelisted director in their relevant decade = automatic Core tier."*

Should read: "...unless the film belongs to a genre movement the director was part of."

---

## Stages

### Stage 1: Documentation (no code changes)

**A. `docs/theory/TIER_ARCHITECTURE.md`**
- §3: Replace "identity trumps everything" with fork model
- §11: Qualify the operational rule with genre movement exception
- Add new section: "Classification as Character, Not Prestige"

**B. `docs/SATELLITE_CATEGORIES.md`**
- Add positive case: Core directors' movement-period films → Satellite
- Note which categories already have Core directors in director lists

**C. `docs/DEVELOPER_GUIDE.md`**
- Update priority order description
- Document "satellite director lists as scoring mechanism"

**D. `CLAUDE.md` Rule 2 (Pattern-First)**
- Update pipeline description to show the fork

---

### Stage 2: Satellite director lists — add Core directors for movement periods

| Category | Core directors to add | Notes |
|----------|----------------------|-------|
| French New Wave | godard, varda, chabrol, demy, duras, resnais, rivette | Currently blocked — exit at Core before reaching FNW |
| American New Hollywood | coppola, scorsese | Already present in constants.py |
| Giallo, Pinku, etc. | (mostly genre specialists, not Core directors) | Audit needed |

**Files:** `lib/constants.py` SATELLITE_ROUTING_RULES

---

### Stage 3: Pipeline reorder — Satellite before Core

**New order in `classify.py`:**
1. Explicit lookup (SORTING_DATABASE)
2. Reference canon
3. **Satellite** ← moved before Core
4. Core director check
5. Popcorn
6. Indie Cinema
7. Unsorted

**Test cases required:**
- Godard 1963 → Satellite/FNW (not Core)
- Godard 1985 → Core (outside FNW decade bounds)
- Kubrick 1968 → Core (no movement, unchanged)
- Bava 1971 → Satellite/Giallo (unchanged)
- Reference film by Core director → Reference (Reference check is before Satellite)

---

### Stage 4: Retroactive reclassification

After Stage 3 pipeline change, re-run classify.py on existing library. Films expected to move:
- All Godard 1960s–1970s: Core → Satellite/FNW
- All Varda, Chabrol, Demy, Duras 1950s–1970s: Core → Satellite/FNW

Use `move.py --execute` after manifest review.

---

## Dependencies

- Depends on: Issue #27 complete (AmNH implemented — Coppola/Scorsese already on AmNH list)
- Blocks: Further Core director whitelist additions until pipeline reorder done
- Related: Issue #6 (director-based Satellite classification), Issue #23 (retroactive reclassification)

## Related docs

- `docs/theory/TIER_ARCHITECTURE.md` §3, §11 — need revision
- `docs/theory/MARGINS_AND_TEXTURE.md` §2 — shadow cinema principle supports this model
- `docs/SATELLITE_CATEGORIES.md` — What Qualifies for Satellite?
- `lib/constants.py` — SATELLITE_ROUTING_RULES director lists
- `classify.py` — stage order
