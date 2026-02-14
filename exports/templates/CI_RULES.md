# CI Rules: Safety Guardrails

<!--
  TEMPLATE: Lightweight safety rules for AI-assisted development.
  These rules prevent common mistakes when working with Claude Code or similar tools.
  Replace [PLACEHOLDER] values with your project specifics.
-->

**Purpose:** Safety guardrails for code changes, especially AI-assisted ones.

---

## Hard Rules (Never Violate)

1. **Never commit secrets** — No API keys, passwords, tokens, or credentials in code
2. **Never force-push to main/master** — Protect shared history
3. **Never skip tests** — Run the test suite before committing
4. **Never delete data without backup** — Always verify backup exists first
5. **Never change schema without migration** — Breaking changes need transition plans

---

## Change Safety Rules

### Before Committing

- [ ] Tests pass
- [ ] No secrets in diff (`git diff --staged | grep -i "key\|secret\|password\|token"`)
- [ ] Changes are scoped to the intended files only
- [ ] Docs updated if behavior changed

### Before Pushing

- [ ] Commit messages are clear and descriptive
- [ ] No unintended files included
- [ ] Branch is up to date with target

### Before Merging

- [ ] PR reviewed (or self-reviewed for solo projects)
- [ ] CI passes
- [ ] No regressions in quality metrics (if applicable)

---

## AI-Assisted Development Rules

When using Claude Code or similar AI tools:

1. **Review all generated code** — AI output is hypothesis until verified
2. **Don't blindly accept refactors** — AI may "improve" working code unnecessarily
3. **Check file operations** — Verify AI isn't modifying unrelated files
4. **Verify deletions** — Confirm removed code is truly unused
5. **Test after AI changes** — Run tests even if "the change is simple"

---

## Project-Specific Rules

<!-- Add rules specific to your project -->

<!--
  EXAMPLES:

  - Always run `npm run lint` before committing JavaScript changes
  - Database migrations must be reversible
  - API changes require version bump
  - Never modify production config files directly
  - All new endpoints need auth middleware
-->
