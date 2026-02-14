# CI Rules: Safety Guardrails

**Purpose:** Safety guardrails for code changes in the film classification pipeline.

---

## Hard Rules (Never Violate)

1. **Never commit secrets** — No API keys, TMDb tokens, or filesystem paths in code
2. **Never force-push to main** — Protect shared history
3. **Never skip tests** — Run `pytest tests/` before committing
4. **Never move files without dry-run first** — `move.py` defaults to `--dry-run`; must pass `--execute` explicitly
5. **Never modify SORTING_DATABASE.md programmatically** — Human-curated, code reads only

---

## Pre-Commit Checklist

### Before Committing

- [ ] `pytest tests/` passes
- [ ] No secrets in diff: `git diff --staged | grep -i "key\|secret\|password\|token\|api_key"`
- [ ] Changes are scoped to intended files only
- [ ] Docs updated if behavior changed (same commit)
- [ ] No `output/*.csv` or `output/tmdb_cache.json` in staged files

### Before Pushing

- [ ] Commit messages are clear and follow `[type]: [what] ([why])` format
- [ ] No unintended files included (check `git status`)
- [ ] Branch is up to date with target

### Before Merging

- [ ] Self-reviewed all changes
- [ ] Tests pass on branch
- [ ] No regressions: manifest comparison shows expected changes only

---

## Files to Never Commit

| File | Reason |
|---|---|
| `config.yaml` | Contains local filesystem paths |
| `config_external.yaml` | Contains TMDb API key |
| `output/*.csv` | Generated manifests (regenerable) |
| `output/tmdb_cache.json` | API response cache |
| `.DS_Store` | macOS metadata |
| `__pycache__/`, `*.pyc` | Python bytecode |

---

## Project-Specific Safety Rules

1. **`move.py` defaults to `--dry-run`** — Must explicitly pass `--execute` to move files. This is by design. Never change the default.

2. **Classification never touches files** — `classify.py` reads filenames and writes a CSV. It never renames, moves, or deletes files. If you find yourself adding file operations to the classifier, stop — that belongs in `move.py`.

3. **Move never classifies** — `move.py` reads the manifest and moves files. It never decides where a film belongs. If you find yourself adding classification logic to the mover, stop — that belongs in `classify.py`.

4. **Normalization must stay symmetric** — If you change `normalize_for_lookup()`, verify that both the database builder (lookup.py) and the query path (classify.py) produce identical normalized forms for the same title. The v0.1 core bug was asymmetric normalization.

5. **Constants live in one place** — All shared constants in `lib/constants.py`. Never duplicate FORMAT_SIGNALS, RELEASE_TAGS, or REFERENCE_CANON elsewhere.

6. **Satellite routing is decade-bounded** — Country→category routing only applies within historically valid decades (see `COUNTRY_TO_WAVE` in constants.py). A 2010s Italian thriller is not Giallo.

---

## AI-Assisted Development Rules

When using Claude Code or similar AI tools:

1. **Review all generated code** — AI output is a hypothesis until tested
2. **Don't blindly accept refactors** — AI may "improve" working normalization or parser logic, breaking symmetric behavior
3. **Check file operations** — Verify AI isn't modifying `docs/SORTING_DATABASE.md` or other human-curated files
4. **Verify deletions** — Confirm removed code is truly unused (check imports across all scripts)
5. **Test after AI changes** — Run `pytest tests/` even for "simple" changes
6. **Watch for constant duplication** — AI may inline constants instead of importing from `lib/constants.py`
