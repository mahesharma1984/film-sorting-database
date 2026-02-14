# Developer Guide

<!--
  TEMPLATE: Change management guide for your project.
  Replace [PLACEHOLDER] values. Add your project-specific rules.
-->

**Purpose:** How to make changes safely in this project.

---

## Rule 0: Explicit Failure Gates

Every pipeline, script, or workflow must declare:
- **Hard gates:** Failures that stop execution
- **Soft gates:** Failures that warn and continue

Don't leave failure handling implicit. If you don't know what should stop vs warn, you'll find out at the worst time.

---

## Before Making Changes

### 1. Understand What You're Changing

Before editing:
- **What does this component consume?** (inputs, dependencies)
- **What does it produce?** (outputs, downstream consumers)
- **What depends on it?** (trace the dependency chain)

### 2. Classify Your Tasks

Use the R/P Split:
- **REASONING tasks** (interpretation, judgment) → LLM
- **PRECISION tasks** (extraction, formatting, verification) → Code
- **Mixed tasks** → Split them

### 3. Check Causality

Use the Pattern-First audit:
- Does this change introduce backwards causality?
- Should this be a new stage or modify existing?
- Are stage boundaries still clean?

---

## Making Changes

### Small Changes (Single File, Clear Scope)

1. Make the change
2. Run tests
3. Verify output still valid
4. Commit with clear message

### Medium Changes (Multiple Files, Single Feature)

1. Backup current state
2. Measure baseline (if quality-relevant)
3. Make changes
4. Run tests
5. Measure after (compare to baseline)
6. Commit with clear message

### Large Changes (Architecture, New Stage, Breaking)

1. Document the change plan
2. Backup current state and pin baseline
3. Make changes incrementally (commit each step)
4. Run tests after each step
5. Measure depth (target case)
6. Measure breadth (all cases)
7. Update architecture docs in same commit
8. Update CHANGELOG

---

## Testing Guidelines

<!-- Replace with your project-specific testing approach -->

### What to Test

- [ ] Unit tests for changed code
- [ ] Integration tests for changed workflows
- [ ] Quality measurement for changed output
- [ ] Manual spot-check for edge cases

### When to Test

| Change Type | Unit Tests | Integration | Quality Measure |
|---|---|---|---|
| Bug fix | Yes | If workflow touched | If output affected |
| New feature | Yes | Yes | Yes |
| Refactor | Yes | Yes | Verify no regression |
| Config change | No | Maybe | If output affected |

---

## Documentation Rules

When code changes require doc updates:

1. **Architecture change** → Update `docs/architecture/SYSTEM_ARCHITECTURE.md`
2. **Workflow change** → Update `docs/WORKFLOW_REGISTRY.md`
3. **New capability** → Update `docs/CORE_DOCUMENTATION_INDEX.md`
4. **Bug fix or improvement** → Update `docs/CHANGELOG.md`

**Critical rule:** Update docs in the same commit as code changes. Stale docs are worse than no docs.

---

## Communication

### Commit Messages

Follow the pattern:
```
[type]: [what changed] ([why])

[details if needed]
```

Types: `fix`, `feat`, `refactor`, `docs`, `test`, `chore`

### Handoff Documents

When leaving work for someone else (or future you):
- State what was done
- State what's next
- State what's blocked
- Include relevant measurements/baselines
