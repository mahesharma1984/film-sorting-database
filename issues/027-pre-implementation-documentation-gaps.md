# Issue #27: Pre-implementation documentation gaps blocking Phase 1 and Phase 2–3

**Severity:** Medium (no runtime impact; blocks next implementation phase)
**Component:** `docs/SATELLITE_CATEGORIES.md`, `REFACTOR_PLAN.md`, `docs/DEVELOPER_GUIDE.md`, `docs/SORTING_DATABASE.md`
**Type:** Documentation / architecture pre-work
**Discovered via:** Theory-vs-implementation gap analysis (post REFINEMENT_AND_EMERGENCE.md + SATELLITE_DEPTH.md authorship)

---

## Summary

The theory base (nine essays) is now ahead of the implementation. Two theory documents authored this session — `REFINEMENT_AND_EMERGENCE.md` and `SATELLITE_DEPTH.md` — fully specify the next two phases of work: Phase 1 (American New Hollywood as a new Satellite category) and Phase 2–3 (within-category Core/Reference depth hierarchy). Both phases are architecturally sound and theoretically complete.

What is missing is the operational specification layer that translates theory into developer instructions. Four documents need to be created or updated before any code is written. Two of them (SATELLITE_CATEGORIES.md American New Hollywood entry, and the Russ Meyer SORTING_DATABASE.md decision) gate Phase 1. Two of them (REFACTOR_PLAN.md v2.0 section, DEVELOPER_GUIDE.md theory bridge) gate Phase 2–3.

Additionally, two confirmed misclassifications in SORTING_DATABASE.md were identified during the gap analysis that need correction as part of this work.

---

## Gap 1: SATELLITE_CATEGORIES.md — No American New Hollywood entry

**Blocks:** Phase 1 (Issue #23 implementation)

### What the theory says

`REFINEMENT_AND_EMERGENCE.md` §3 marks American New Hollywood as meeting all three conditions for a new category:
- **Density:** 15–25 films in the collection currently misfiled in AmEx, Reference, or Unsorted
- **Coherence:** Documented historical movement — post-Production Code prestige studio cinema, c.1965–1985, with identifiable directors and a bounded industrial moment
- **Archival necessity:** Without this category, Fosse and Russ Meyer end up in the same folder, collapsing the distinction between a prestige auteur and a grindhouse specialist

`SATELLITE_DEPTH.md` §4 provides the within-category tier breakdown (Fosse/Ashby/Pakula as Category Core; Pollack/Lumet/Bogdanovich as Category Reference).

### What is missing

`docs/SATELLITE_CATEGORIES.md` has a formal entry for every Satellite category (Giallo, Pinku Eiga, Brazilian Exploitation, etc.) but no entry for American New Hollywood. A developer implementing this in `constants.py` needs:

**Unresolved curatorial decisions (require collector input before the entry can be written):**

| Decision | Question | Options |
|----------|----------|---------|
| **Director list** | The routing gate requires a finite director list. Fosse, Ashby, Pakula are Category Core. But how wide is the gate? | Narrow (Category Core only: Fosse, Ashby, Pakula) / Wide (add Pollack, Lumet, Bogdanovich, Altman) / Include Coppola, Scorsese (noting they are also Core whitelist candidates) |
| **Decade gate** | "1965–1985" spans three system decades. Include `1960s` (for the 1965–1969 films) or only `1970s` + `1980s`? | All three (`1960s`, `1970s`, `1980s`) / Two (`1970s`, `1980s` only) |
| **Cap** | Theory estimates 15–25 films. | Confirm cap number |
| **Genre gate** | Director-only routing (like French New Wave) or country+director+genre gate? | Director-only recommended (avoids false positives); confirm |
| **Routing position** | Must be positioned before American Exploitation in `SATELLITE_ROUTING_RULES`. Before or after Classic Hollywood? | Before Classic Hollywood (both are US historical categories but New Hollywood is more specific) |

### What to produce

A formal entry in `docs/SATELLITE_CATEGORIES.md` matching the format of existing entries:
- Definition and date bounds
- Director list (routing gate directors + Category Core/Reference designation)
- Cap per decade and total cap
- Boundary rules (what separates this from AmEx, Classic Hollywood, Indie Cinema, Core)
- Films currently in the collection that belong here (the ~15–25 misfiled films)

---

## Gap 2: SORTING_DATABASE.md — Two confirmed misclassifications and one legacy artefact

**Blocks:** Phase 1 — AmEx reclassification audit (Issue #23 Stage 3)

### Confirmed misclassifications

Two Bob Fosse films in SORTING_DATABASE.md are routed to `Satellite/Indie Cinema/`:

| Film | Current destination | Correct destination |
|------|--------------------|--------------------|
| All That Jazz (1979) | `Satellite/Indie Cinema/` | `Satellite/American New Hollywood/1970s/` |
| Being There (1979) | `Satellite/Indie Cinema/` | `Satellite/American New Hollywood/1970s/` |

These were routed to Indie Cinema because American New Hollywood did not exist as a category when they were classified. They should be updated when the category is formally created.

**Note:** These cannot be corrected until Gap 1 (the formal category spec) is resolved and the category is added to `SATELLITE_ROUTING_RULES`. Document the misclassification here; fix in SORTING_DATABASE.md as part of Issue #23 Stage 3.

### Legacy artefact: per-director category

`SORTING_DATABASE.md` contains a `Satellite - Russ Meyer` section routing three films to `1970s/Satellite/Russ Meyer/`:

```
Faster Pussycat! Kill! Kill! (1965)  | 1970s/Satellite/Russ Meyer/
Supervixens (1975)                    | 1970s/Satellite/Russ Meyer/
Beyond the Valley of the Dolls (1970) | 1970s/Satellite/Russ Meyer/
```

`REFINEMENT_AND_EMERGENCE.md` §6 explicitly states: *"Do not create a category for a single director — use the Core whitelist or SORTING_DATABASE.md lookup, not a new Satellite category."* This is exactly what `Satellite - Russ Meyer` is. It predates the routing system and has no corresponding entry in `SATELLITE_ROUTING_RULES`.

**Decision needed:** Move all three entries to `Satellite/American Exploitation/1970s/` (where they belong under the current taxonomy). This is a one-line decision per entry — no code change required, only SORTING_DATABASE.md edits.

**Note:** Russ Meyer's films are correctly categorised as American Exploitation. The `Satellite - Russ Meyer` folder on disk will also need to be removed as part of the legacy folder migration.

---

## Gap 3: REFACTOR_PLAN.md — No v2.0 section; critical architectural decision unrecorded

**Blocks:** Phase 2–3 (within-category depth implementation)

### Current state

`REFACTOR_PLAN.md` accurately describes the completed v0.1→v1.0 work (keyword matching → TMDb-structured-data routing, 4-script architecture). It is a completed plan, not a forward-looking one. It does not mention American New Hollywood, the `core_directors` field, within-category depth, or `SATELLITE_DEPTH.md`.

### What is missing

**The most critical unresolved architectural decision in the entire project:**

`SATELLITE_DEPTH.md` §7 proposes adding a `core_directors` field to `SATELLITE_ROUTING_RULES` and producing different file destinations for within-category Core directors (`Satellite/Giallo/Core Tier/1970s/`). But there are two fundamentally different architectures for implementing this, and the choice determines the scope of every downstream change:

**Option A: Destination-changing (what SATELLITE_DEPTH.md §7 describes)**
- Add `core_directors` field to `SATELLITE_ROUTING_RULES` in `constants.py`
- `satellite.py` returns `'Giallo/Core Tier'` for Bava/Argento vs. `'Giallo'` for Lenzi
- `_build_destination()` in `classify.py` produces `Satellite/Giallo/Core Tier/1970s/`
- `scaffold.py` creates `Core Tier/` and `Reference/` sub-folders inside mature categories
- SORTING_DATABASE.md entries updated to use sub-paths for known Category Core films
- **Scope:** Touches 4 files; requires folder migration; changes manifest schema

**Option B: Metadata-only (lighter, equally valid)**
- No changes to `constants.py`, `satellite.py`, `classify.py`, or `scaffold.py`
- Folder structure stays flat (`Satellite/Giallo/1970s/`)
- SORTING_DATABASE.md adds comments noting Category Core status (human-readable, no routing effect)
- Within-category hierarchy exists in the human record (theory essays + SORTING_DATABASE notes) but not in the folder structure
- **Scope:** Documentation only; no code changes; within-category depth is curatorial knowledge, not structural

Both options are architecturally legitimate. The theory describes Option A. Option B reflects the principle in `SATELLITE_DEPTH.md` §7: *"This is not required for every category. It is appropriate when the Category Core directors have filmographies large enough to warrant their own space, and when the distinction between Core and texture is clearly established."*

This decision must be made explicitly and recorded in `REFACTOR_PLAN.md` before any Phase 2 code is written.

### What to produce

A v2.0 section in `REFACTOR_PLAN.md` covering:
1. The architectural decision on within-category depth (Option A vs. B) with rationale
2. Phase 1: American New Hollywood — summary of changes required (constants.py, scaffold.py, SORTING_DATABASE.md, tests)
3. Phase 2–3: Within-category depth — summary of changes required (if Option A is chosen)
4. Explicit ordering: Phase 1 is independent of Phase 2–3; Phase 2–3 depends on Phase 1 (American New Hollywood is the test case for within-category depth)

---

## Gap 4: DEVELOPER_GUIDE.md — No theory→implementation bridge

**Blocks:** Developer orientation for any future work

### Current state

`docs/DEVELOPER_GUIDE.md` describes the current architecture accurately. It does not reference the new theory essays (added this session) or connect them to implementation priorities. A developer picking up this codebase sees nine theory essays and no map from them to what needs building.

### What to produce

A short section (not a full rewrite) in `DEVELOPER_GUIDE.md` — "Theory and Implementation Status" — covering:
- The theory knowledge base is in `docs/theory/` — nine essays organised by the reading order in `docs/theory/README.md`
- The theory is currently ahead of the implementation: the two most recent essays (REFINEMENT_AND_EMERGENCE.md, SATELLITE_DEPTH.md) describe Phase 1 and Phase 2–3 work not yet implemented
- The implementation gap is documented in Issue #27 (this issue)
- Within-category depth (SATELLITE_DEPTH.md) is intentionally deferred until Phase 1 is complete
- The single most actionable next step is Issue #23 (American New Hollywood), which is gated on this issue

---

## Dependency map

```
Gap 2 (Russ Meyer decision)          ← No dependencies; can be done immediately
Gap 1 (AmNH SATELLITE_CATEGORIES)   ← Requires collector input (4 curatorial decisions)
Gap 3 (REFACTOR_PLAN v2.0)          ← Requires Gap 1 decision + architectural choice
Gap 4 (DEVELOPER_GUIDE bridge)      ← Requires Gap 3 to know what Phase 2–3 will be

Issue #23 Stage 1–2 (code)          ← Requires Gap 1 + Gap 3 (REFACTOR_PLAN v2.0)
Issue #23 Stage 3 (SORTING_DATABASE audit) ← Requires Gap 1 + Gap 2
Phase 2–3 (within-category depth)  ← Requires Gap 3 (architectural decision)
```

---

## Proposed Fix: Staged approach

### Stage 1: Collector input session (curatorial, not code)

Resolve the four curatorial decisions in Gap 1:
- Director list boundary for American New Hollywood routing gate
- Decade gate (include `1960s` or not)
- Cap number
- Russ Meyer legacy entries decision (Gap 2)

**Output:** Notes sufficient to write the SATELLITE_CATEGORIES.md entry and resolve SORTING_DATABASE.md.

### Stage 2: Write SATELLITE_CATEGORIES.md entry for American New Hollywood

Using the decisions from Stage 1, write a formal entry matching the format of existing entries. This is the spec that gates all Phase 1 code work.

**Output:** New section in `docs/SATELLITE_CATEGORIES.md` (American New Hollywood, §18 or equivalent).

### Stage 3: Resolve SORTING_DATABASE.md

- Move the three Russ Meyer entries from `Satellite - Russ Meyer` to `Satellite/American Exploitation/1970s/`
- Note the All That Jazz and Being There misclassifications with a comment (do not update destinations yet — wait for American New Hollywood to be in `SATELLITE_ROUTING_RULES`)

**Output:** Three line edits in `docs/SORTING_DATABASE.md`.

### Stage 4: Write REFACTOR_PLAN.md v2.0 section

Record the architectural decision on within-category depth and outline Phase 1 + Phase 2–3.

**Output:** New `## v2.0` section in `REFACTOR_PLAN.md`.

### Stage 5: Update DEVELOPER_GUIDE.md

Add the "Theory and Implementation Status" section.

**Output:** New section in `docs/DEVELOPER_GUIDE.md`.

---

## Acceptance Criteria

- [ ] Four curatorial decisions for American New Hollywood recorded (director list, decade gate, cap, Russ Meyer)
- [ ] `docs/SATELLITE_CATEGORIES.md` has a formal American New Hollywood entry
- [ ] `docs/SORTING_DATABASE.md` Russ Meyer entries moved to American Exploitation
- [ ] `docs/SORTING_DATABASE.md` All That Jazz / Being There misclassifications noted with comment
- [ ] `REFACTOR_PLAN.md` has a v2.0 section with the within-category depth architectural decision
- [ ] `docs/DEVELOPER_GUIDE.md` has a "Theory and Implementation Status" section pointing to Issue #27 and Issue #23
- [ ] All four documents completed before any Phase 1 code is written
