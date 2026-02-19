# Issue #22: French New Wave routing is structurally incomplete — missing `FR` in `COUNTRY_TO_WAVE`, incomplete directors list, undocumented Core exclusions

**Severity:** Medium-High
**Component:** `lib/constants.py`, `classify.py`
**Type:** Missing feature / architecture gap
**Discovered via:** Architecture analysis (exports/knowledge-base)

---

## Summary

French New Wave was added as a Satellite category in Issue #14, but its routing is only half-implemented. The country-first path (`COUNTRY_TO_WAVE`) does not include France (`FR`), so French films with no director match are never routed to French New Wave via the fast country gate. The director list only contains 6 names and omits the four most prominent figures of the movement — but this is _intentional_ for Godard and Truffaut (who are Core directors). The problem is that this architectural decision is undocumented, leaving a trap for anyone adding non-Core Nouvelle Vague directors in the future.

Additionally, the interplay between Core routing and French New Wave routing has never been tested or specified.

---

## Current State

### `COUNTRY_TO_WAVE` (lib/constants.py:153–170)
```python
COUNTRY_TO_WAVE = {
    'BR': { ... },
    'IT': { ... },
    'JP': { ... },
    'HK': { ... },
}
```
France (`FR`) is absent. This means Stage 7 of the classifier (`classify.py:565–580`) will never fire for a French film, regardless of decade.

### French New Wave in `SATELLITE_ROUTING_RULES` (lib/constants.py:228–238)
```python
'French New Wave': {
    'country_codes': [],  # Director-only (no country fallback)
    'decades': ['1950s', '1960s', '1970s'],
    'genres': [],
    'directors': ['marker', 'rohmer', 'resnais', 'rivette', 'malle', 'eustache'],
},
```

`country_codes: []` makes the empty-list design explicit — this category is director-only by design. But the directors list (6 names) omits the major figures:

| Director | Status | Routing path |
|---|---|---|
| Jean-Luc Godard | Core director | Exits at Stage 3 (Core check) — never reaches French New Wave |
| François Truffaut | Core director | Exits at Stage 3 — never reaches French New Wave |
| Agnès Varda | Core director (assumed) | Exits at Stage 3 — never reaches French New Wave |
| Claude Chabrol | Unknown — not documented | Falls through to Unsorted |
| Jacques Demy | Unknown | Falls through to Unsorted |
| Alain Robbe-Grillet | Unknown | Falls through to Unsorted |
| Chris Marker | ✅ In list | Routes to French New Wave |
| Éric Rohmer | ✅ In list | Routes to French New Wave |

The comment `# Director-only (no country fallback)` documents the routing strategy but not _why_ Godard and Truffaut are absent. A developer adding Chabrol would not know he is expected to be in this list (if non-Core) or in the Core whitelist (if Core).

---

## Root Cause: Undocumented Architectural Decision

When Issue #14 designed French New Wave as "director-only", the implicit assumption was:

> The most prominent Nouvelle Vague directors (Godard, Truffaut, Varda) are Core directors and will be caught at Stage 3. French New Wave (Satellite) is a catch-basin for the remainder — the "second tier" of the movement.

This is a valid architectural decision. It is not documented anywhere. Consequences:

1. **Chabrol gap:** Claude Chabrol directed ~50 films in the Nouvelle Vague period and is not a Core director in the whitelist (likely — this is unverified). If not Core, he routes to Unsorted. He should be in the French New Wave directors list.

2. **No `FR` in `COUNTRY_TO_WAVE`:** This is correct if the category is purely director-driven (an unknown French film from 1965 without a recognisable director should not automatically become French New Wave). However, the _reason_ it is absent is not stated. The existing four entries in `COUNTRY_TO_WAVE` all have broad country-first routing. The absence of `FR` looks like an omission, not a decision.

3. **European Sexploitation overlap:** `FR` appears in `European Sexploitation.country_codes` (`constants.py:299`). A 1968 French drama with no director match will route to European Sexploitation (country + genre match) before French New Wave is checked. This may be the intended priority order but it is not tested.

---

## Impact Scenarios

### Scenario A: Non-Core Nouvelle Vague director → Unsorted
A file `Claude Chabrol - Les Biches (1968).mkv` is classified. Chabrol is not in the Core whitelist (unverified). He is not in `SATELLITE_ROUTING_RULES['French New Wave']['directors']`. TMDb returns director `Claude Chabrol`, country `FR`, genres `Crime/Drama`. The film passes through all stages and lands in Unsorted with reason `unsorted_no_match`. Expected: `Satellite/French New Wave/1960s/`.

### Scenario B: French 1965 drama with unknown director → European Sexploitation
A file `Unknown Director - French Drama (1965).mkv`. Country `FR` is not in `COUNTRY_TO_WAVE` so Stage 7 does not fire. TMDb stage fires: country `FR` is in `European Sexploitation.country_codes`, genres contain Drama. Film routes to `Satellite/European Sexploitation/1960s/`. Expected behaviour is ambiguous — but undocumented.

### Scenario C: Core Nouvelle Vague director — correctly handled but untested
`Jean-Luc Godard - Breathless (1960).mkv` exits at Stage 3 (Core). This is correct but there is no test that explicitly asserts Godard goes to Core and _not_ French New Wave. A regression that removes Godard from the Core whitelist would silently drop him to Unsorted (because he is also absent from the French New Wave directors list).

---

## Proposed Fix

### Stage 1: Audit and document the Core/FNW boundary

Verify which Nouvelle Vague directors are in `CoreDirectorDatabase` (the Core whitelist). Document this explicitly in a comment in `SATELLITE_ROUTING_RULES`:

```python
'French New Wave': {
    # DIRECTOR-ONLY routing (Issue #14). No country fallback by design.
    # Core directors (Godard, Truffaut, Varda) are handled at Stage 3 and never
    # reach this check. This list covers non-Core FNW directors only.
    # If adding a director, first verify they are NOT in the Core whitelist.
    'country_codes': [],
    'decades': ['1950s', '1960s', '1970s'],
    'genres': [],
    'directors': ['marker', 'rohmer', 'resnais', 'rivette', 'malle', 'eustache'],
},
```

### Stage 2: Audit and extend the directors list

Verify each of the following against the Core whitelist. Add to `French New Wave` directors if not Core:

- Claude Chabrol (`'chabrol'`)
- Jacques Demy (`'demy'`)
- Alain Robbe-Grillet (`'robbe-grillet'`)
- Marguerite Duras (films-as-director, 1960s–1970s) (`'duras'`)
- Jacques Rivette is already in the list (`'rivette'` ✅)

Note on substring matching: the satellite director matching is substring-based (`satellite.py:103`). `'duras'` would match any director name containing "duras". Verify no collision before adding short strings.

### Stage 3: Add explicit `COUNTRY_TO_WAVE` comment for France absence

Add a comment to `COUNTRY_TO_WAVE` explaining why `FR` is absent:

```python
COUNTRY_TO_WAVE = {
    # NOTE: France ('FR') is intentionally excluded.
    # French New Wave is director-only (see SATELLITE_ROUTING_RULES).
    # Non-Core French films not caught by a director match fall to Unsorted
    # or European Sexploitation — this is the designed behaviour.
    'BR': { ... },
    ...
}
```

### Stage 4: Add regression tests

Create or extend `tests/test_satellite_routing.py` (or `tests/test_french_new_wave.py`):

- `test_core_godard_never_reaches_satellite()` — mock Core whitelist match, assert tier=Core
- `test_chabrol_routes_to_french_new_wave()` — after adding chabrol to directors list
- `test_unknown_french_1965_routes_correctly()` — assert expected destination for country-only French film with no director match (document the expected behaviour, even if it is Unsorted)
- `test_french_new_wave_decade_gate()` — 2010 French film with Rohmer-style director should NOT route to French New Wave (decade gate)
- `test_european_sexploitation_priority_over_french_drama()` — verify the routing priority between FNW and EurSex for ambiguous cases

### Stage 5: Update CLAUDE.md

Revise `CLAUDE.md §4` French New Wave entry to reflect the Core/Satellite split:

```
France → French New Wave: 1950s–1970s only (Issue #14)
  - Director-only routing (no country fallback)
  - Godard, Truffaut, Varda → Core (excluded from this Satellite category)
  - Chabrol, Demy, Rohmer, Resnais, Marker, etc. → Satellite/French New Wave
```

---

## Acceptance Criteria

- [ ] `SATELLITE_ROUTING_RULES['French New Wave']` has a comment documenting the Core/FNW boundary
- [ ] `COUNTRY_TO_WAVE` has a comment explaining France's absence
- [ ] Audit of Core whitelist against non-Core FNW directors is complete and documented
- [ ] At minimum `chabrol` and `demy` added to directors list if confirmed non-Core
- [ ] Regression tests cover Godard (Core), Chabrol/Rohmer (Satellite), decade gate, and unknown-director French film
- [ ] `CLAUDE.md §4` updated with Core/Satellite split note
