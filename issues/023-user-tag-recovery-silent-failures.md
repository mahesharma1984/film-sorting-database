# Issue #23: User tag recovery produces silent malformed destinations and skips Core whitelist validation

**Severity:** Medium
**Component:** `classify.py` (Stage 5: User tag recovery)
**Type:** Bug — silent bad output + validation gap
**Discovered via:** Architecture analysis (exports/knowledge-base)

---

## Summary

Stage 5 of the classifier (`classify.py:519–545`) recovers human-applied tags like `[Core-1960s-Jacques Demy]` or `[Satellite-1970s-Giallo]` from filenames. It has two distinct failure modes that produce silently wrong output:

1. **Bare Satellite tags produce a structurally broken destination.** A tag like `[Satellite-1970s]` (without a subdirectory) falls through all the `if/elif` branches and produces `dest = 'Satellite/'` — no decade, no category. `move.py` will attempt to create a file directly in `Satellite/` with no further path components.

2. **Core tags are trusted at confidence 0.8 without any cross-check against the Core director whitelist.** A tag `[Core-1960s-Unknown Person]` produces `dest = 'Core/1960s/Unknown Person/'` at confidence 0.8 and is returned immediately. The Core whitelist exists precisely to validate Core attribution — it is never consulted here.

Both failures are silent: no warning is logged, no confidence is lowered, and the malformed result propagates into the manifest and then into `move.py`.

---

## Bug 1: Bare Satellite tag produces `'Satellite/'` destination

### Code path

`classify.py:525–534`:
```python
extra = parsed_tag.get('extra', '')

if tier == 'Core' and extra:
    dest = f'Core/{tag_decade}/{extra}/'
elif tier == 'Satellite' and extra:                  # requires extra
    dest = f'Satellite/{extra}/{tag_decade}/'
elif tier in ('Reference', 'Popcorn'):
    dest = f'{tier}/{tag_decade}/'
else:
    dest = f'{tier}/'                                # ← fallback
```

For a tag `[Satellite-1970s]`:
- `tier = 'Satellite'`, `tag_decade = '1970s'`, `extra = ''`
- `tier == 'Satellite' and extra` → **False** (empty string is falsy)
- `tier in ('Reference', 'Popcorn')` → **False**
- Falls to `else: dest = f'{tier}/'` → `dest = 'Satellite/'`

The resulting `ClassificationResult` has:
```
tier='Satellite', decade='1970s', subdirectory=None, destination='Satellite/'
```

### Why this matters

`move.py` uses `destination` directly as the target path. A film with `destination='Satellite/'` would be moved to the root `Satellite/` folder with no decade or category subdirectory. If multiple films share this malformed destination, they pile up in `Satellite/` as an unorganised dump.

The `subdirectory=None` field is also a signal that downstream tooling (e.g., `audit.py`, `dashboard.py`) may use to determine category. A Satellite film with `subdirectory=None` would be invisible to any category-level stats.

### Valid vs invalid Satellite tags

| Tag | Expected destination | Actual destination |
|---|---|---|
| `[Satellite-1970s-Giallo]` | `Satellite/Giallo/1970s/` | ✅ Correct |
| `[Satellite-1970s]` | Should warn → Unsorted | ❌ `Satellite/` |
| `[Satellite-Giallo]` (no decade) | `'tier'` and `'decade'` both required → tag ignored | ✅ Already handled (no decade parsed → tag not recovered) |

---

## Bug 2: Core user tags are not validated against the Core whitelist

### Code path

`classify.py:527–528`:
```python
if tier == 'Core' and extra:
    dest = f'Core/{tag_decade}/{extra}/'
```

`extra` is the director name parsed from the tag (e.g., `'Jacques Demy'`). This path fires with confidence 0.8 (`classify.py:544`) without ever calling `self.core_director_db.is_core_director()`.

### Why this matters

User tags are human-applied and can contain errors:
- Typos: `[Core-1960s-Godart]` (misspelled Godard) → `Core/1960s/Godart/`
- Outdated tags: a director who was considered Core and later reclassified
- Fabrications: someone manually tagging `[Core-1960s-Steven Spielberg]` on a Jaws file — Spielberg is Popcorn, not Core

The Core tier has a whitelist (`CoreDirectorDatabase`) precisely to prevent this. The whitelist is authoritative. User tag recovery at Stage 5 bypasses it entirely.

### Priority precedence note

`CLAUDE.md §4` states: _"Reference Canon Takes Priority Over User Tags."_ Reference canon is checked at Stage 4 — before user tag recovery at Stage 5. So the Reference protection works. However, the same principle logically extends to Core: the Core whitelist should also take priority over user tags, or at minimum, user tags for Core should be validated against it. Currently only Reference is protected; Core is not.

---

## Proposed Fix

### Stage 1: Fix bare Satellite tag destination

In `classify.py`, modify the `Satellite` branch to require `extra`. When `extra` is absent, degrade gracefully to Unsorted with a warning:

```python
if tier == 'Core' and extra:
    dest = f'Core/{tag_decade}/{extra}/'
elif tier == 'Satellite':
    if extra:
        dest = f'Satellite/{extra}/{tag_decade}/'
    else:
        # Satellite tag without category — cannot build a valid destination
        logger.warning(
            f"User tag '[Satellite-{tag_decade}]' has no category subdirectory — "
            f"cannot recover. Falling through to heuristics. File: {metadata.filename}"
        )
        # Do not return — allow pipeline to continue to Stages 6-9
        pass  # (skip the return statement)
elif tier in ('Reference', 'Popcorn'):
    dest = f'{tier}/{tag_decade}/'
else:
    dest = f'{tier}/'
```

This means bare `[Satellite-1970s]` tags no longer short-circuit the pipeline; the film continues through Popcorn and Satellite heuristics, which may correctly identify the category that the user intended but failed to specify.

### Stage 2: Add Core whitelist cross-check

In `classify.py`, for `tier == 'Core' and extra`, add a whitelist validation before returning:

```python
if tier == 'Core' and extra:
    # Cross-check against the Core director whitelist before trusting the tag
    if self.core_director_db.is_core_director(extra):
        dest = f'Core/{tag_decade}/{extra}/'
    else:
        logger.warning(
            f"User tag '[Core-{tag_decade}-{extra}]' — '{extra}' is not in Core "
            f"whitelist. Treating as Unsorted. File: {metadata.filename}"
        )
        # Fall through to heuristics — do not return here
        pass
```

This preserves the intent of user tag recovery (trust human curation) while preventing silent misclassification when the human made an error or the whitelist has changed.

**Note on confidence:** If we want to allow a soft-recovery path — trust the tag but at lower confidence, and flag for review — an alternative is to retain the Core destination but lower confidence to 0.5 and add a `reason='user_tag_core_unverified'` code. This produces a usable manifest while flagging the item for human review in the dashboard. Discuss preferred behaviour before implementing.

### Stage 3: Extend `_parse_user_tag()` to detect and report malformed tags

`classify.py:188–205` currently returns a partial dict silently. Add a `warnings` key:

```python
result['warnings'] = []
if tier == 'Satellite' and not result.get('extra'):
    result['warnings'].append('satellite_tag_missing_category')
if tier == 'Core' and not result.get('extra'):
    result['warnings'].append('core_tag_missing_director')
```

Use these warnings in the caller to determine whether to trust the recovery or fall through.

### Stage 4: Add tests

Create or extend `tests/test_user_tag_recovery.py`:

- `test_bare_satellite_tag_falls_through()` — `[Satellite-1970s]` should NOT produce `destination='Satellite/'`; pipeline should continue to Stage 6
- `test_satellite_tag_with_category_works()` — `[Satellite-1970s-Giallo]` → `Satellite/Giallo/1970s/`
- `test_core_tag_valid_director_accepted()` — `[Core-1960s-Jean-Luc Godard]` → Godard is in whitelist → `Core/1960s/Jean-Luc Godard/`
- `test_core_tag_invalid_director_falls_through()` — `[Core-1960s-Fake Director]` → not in whitelist → falls through to heuristics
- `test_core_tag_typo_director_falls_through()` — `[Core-1960s-Godart]` (typo) → not in whitelist → falls through

### Stage 5: Update documentation

Update `CLAUDE.md §4` (or `docs/DEVELOPER_GUIDE.md`) with user tag format requirements:

```
User tag format: [Tier-Decade-Extra]
  Core:      [Core-1960s-Director Name]     — Director must be in Core whitelist
  Satellite: [Satellite-1970s-Category]     — Category is required (e.g. Giallo)
  Reference: [Reference-1960s]              — No extra field needed
  Popcorn:   [Popcorn-1990s]               — No extra field needed

Malformed tags (missing required fields) fall through to heuristic classification.
```

---

## Acceptance Criteria

- [ ] `[Satellite-1970s]` (no category) falls through to Stages 6–9 instead of producing `destination='Satellite/'`
- [ ] `[Core-1960s-Director]` tags are validated against `CoreDirectorDatabase`; unrecognised directors log a warning and fall through (or use soft confidence — document which approach is chosen)
- [ ] `_parse_user_tag()` reports structured warnings for malformed tags
- [ ] New tests cover all four tag failure modes above
- [ ] No regression in existing user tag recovery for valid tags
- [ ] User tag format documented in `CLAUDE.md` or `DEVELOPER_GUIDE.md`
