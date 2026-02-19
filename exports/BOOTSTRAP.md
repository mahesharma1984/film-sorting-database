# Bootstrap Guide: Setting Up a New Repo

This guide walks you through applying the Development Methodology Kit to a new project.

**Important:** Start with theory, not templates. The documentation structure is only useful if you understand the principles behind it.

---

## Step 0: Read the Knowledge Base (1-2 hours)

Before setting up anything, read the theoretical foundations. These are the mental models that make the skills and templates make sense.

### Minimum Reading (30 minutes)

If you're short on time, read these two — they cover the most critical concepts:

1. **[LLM Capability Model](knowledge-base/llm-capability-model.md)** — Understand what AI can and cannot do. This prevents the #1 failure mode in AI-assisted systems.
2. **[Task Design Theory](knowledge-base/task-design-theory.md)** — Understand how to decompose work correctly. This prevents building the wrong thing.

### Recommended Reading (1 hour)

Add these based on what you're building:

3. **[Causality & Systems](knowledge-base/causality-and-systems.md)** — If your project has multiple stages or components that depend on each other.
4. **[Domain Grounding Theory](knowledge-base/domain-grounding-theory.md)** — If your pipeline classifies entities into categories or types.
5. **[System Boundary Theory](knowledge-base/system-boundary-theory.md)** — If your pipeline has cheap analysis stages and expensive delivery stages.
6. **[Measurement Theory](knowledge-base/measurement-theory.md)** — If you need to track quality over time or across cases.
7. **[Failure Theory](knowledge-base/failure-theory.md)** — If your system processes data through a pipeline where errors can compound.

### Full Reading (2-3 hours)

Read all eight in order. Each builds on the previous.

**Why this matters:** The skills (Step 1) are procedures that implement these theories. Without the theory, you'll follow the procedures mechanically and won't recognize when to adapt them to your specific situation. With the theory, the procedures become obvious consequences of the mental models.

---

## Step 1: Choose Your Skills (5 minutes)

Not every project needs every skill. Choose based on your project type:

| If your project... | Start with these skills |
|---|---|
| Uses AI/LLMs for any task | **R/P Split** (critical) |
| Has multiple processing stages | **Pattern-First** + **Failure Gates** |
| Classifies entities into types/categories | **Domain Grounding** |
| Has cheap + expensive stages | **Boundary-Aware Measurement** + **Constraint Gates** |
| Needs quality tracking over time | **Measurement-Driven** |
| Is new/unfamiliar territory | **Prototype Building** |
| Is a complex system | All eight |

**Recommendation:** Start with **R/P Split** and **Prototype Building** — they provide the highest value with the lowest setup cost.

---

## Step 2: Set Up Documentation Structure (15 minutes)

### Minimal Setup (3 files)

```bash
mkdir -p docs

# Copy and customize these templates:
cp exports/templates/CLAUDE.md.template ./CLAUDE.md
cp exports/templates/DEVELOPER_GUIDE.md ./docs/DEVELOPER_GUIDE.md
cp exports/templates/CI_RULES.md ./docs/CI_RULES.md
```

Edit each file:
1. **CLAUDE.md** — Replace `[PLACEHOLDER]` values with your project specifics. This is the most important file — it's what Claude Code reads on every interaction.
2. **docs/DEVELOPER_GUIDE.md** — Add your testing commands, deployment steps, and project-specific rules.
3. **docs/CI_RULES.md** — Add your project-specific safety rules.

### Standard Setup (6 files)

Add to the minimal setup:

```bash
mkdir -p docs/architecture

cp exports/templates/CORE_DOCS_INDEX.md ./docs/CORE_DOCUMENTATION_INDEX.md
cp exports/templates/WORK_ROUTER.md ./docs/WORK_ROUTER.md
cp exports/templates/DEBUG_RUNBOOK.md ./docs/DEBUG_RUNBOOK.md
```

Edit each file with your project specifics.

### Full Setup (8+ files)

Add to the standard setup:

```bash
cp exports/templates/WORKFLOW_REGISTRY.md ./docs/WORKFLOW_REGISTRY.md

# Create architecture doc (no template — this is project-specific)
touch docs/architecture/SYSTEM_ARCHITECTURE.md

# Create changelog
touch docs/CHANGELOG.md
```

---

## Step 3: Add Skills to CLAUDE.md (10 minutes)

The key integration point is your `CLAUDE.md` file. Add the decision rules from each adopted skill to the "Decision Rules While Working" section.

### If adopting R/P Split:

Add to CLAUDE.md § 3:
```markdown
1. **Apply R/P Split:**
   - REASONING tasks (interpretation, judgment, synthesis) → Claude/LLM
   - PRECISION tasks (extraction, counting, formatting, verification) → Code
   - If a task contains BOTH, split it into separate steps
   - Never ask Claude to extract exact text AND reason about it in one call
```

### If adopting Pattern-First:

Add to CLAUDE.md § 3:
```markdown
2. **Enforce Pattern-First:**
   - Define pattern/schema/structure BEFORE populating instances
   - Trace causality before edits: What does this consume? Produce? What depends on it?
   - Keep stage boundaries stable unless explicitly redesigning
```

### If adopting Failure Gates:

Add to CLAUDE.md § 3:
```markdown
3. **Explicit failure gates:**
   - Every pipeline or script must declare hard vs soft failure gates
   - Hard gates stop execution; soft gates warn and continue
   - Level 0 (data integrity) gates everything downstream
```

### If adopting Measurement-Driven:

Add to CLAUDE.md § 3:
```markdown
4. **Measure before and after:**
   - Establish baseline before making changes
   - Measure depth after change (did target improve?)
   - Measure breadth after change (did anything else regress?)
   - Stabilize when both axes aligned
```

### If adopting Domain Grounding:

Add to CLAUDE.md § 3:
```markdown
5. **Ground classifications in published theory:**
   - Every taxonomy must cite a published framework
   - Entity processing priority follows abstraction level, not frequency
   - One canonical taxonomy; all stages reference it (no parallel systems)
```

### If adopting Boundary-Aware Measurement:

Add to CLAUDE.md § 3:
```markdown
6. **Scope measurement to subsystems:**
   - Identify the boundary between analysis and delivery stages
   - Validate handoffs ($0) before running expensive measurement ($$)
   - Measure the affected subsystem, not the whole pipeline
```

### If adopting Prototype Building:

Add to CLAUDE.md § 3:
```markdown
7. **Explore before executing:**
   - State the problem in one sentence before building
   - Have a real case to test against
   - Don't build until the pattern is confirmed
   - LLM output is hypothesis until tested
```

---

## Step 4: Copy Knowledge Base and Skills Reference (Optional, 5 minutes)

If you want the theory and skill documents in your repo for reference:

```bash
mkdir -p docs/knowledge-base docs/methodology

# Layer 0: Theory (recommended — these are the foundation)
cp exports/knowledge-base/llm-capability-model.md ./docs/knowledge-base/
cp exports/knowledge-base/task-design-theory.md ./docs/knowledge-base/
cp exports/knowledge-base/causality-and-systems.md ./docs/knowledge-base/
cp exports/knowledge-base/domain-grounding-theory.md ./docs/knowledge-base/
cp exports/knowledge-base/system-boundary-theory.md ./docs/knowledge-base/
cp exports/knowledge-base/measurement-theory.md ./docs/knowledge-base/
cp exports/knowledge-base/failure-theory.md ./docs/knowledge-base/
cp exports/knowledge-base/constraint-theory.md ./docs/knowledge-base/

# Layer 1: Skills
cp exports/skills/rp-split.md ./docs/methodology/
cp exports/skills/pattern-first.md ./docs/methodology/
cp exports/skills/domain-grounding.md ./docs/methodology/
cp exports/skills/boundary-aware-measurement.md ./docs/methodology/
cp exports/skills/measurement-driven.md ./docs/methodology/
cp exports/skills/failure-gates.md ./docs/methodology/
cp exports/skills/constraint-gates.md ./docs/methodology/
cp exports/skills/prototype-building.md ./docs/methodology/
```

Then reference them from your CLAUDE.md work modes section. The knowledge base documents are especially valuable for onboarding new team members — they explain *why* the practices exist, not just *what* to do.

---

## Step 5: Customize for Your Project (Varies)

### Add Project-Specific Symptoms to Debug Runbook

Think about your project's common failures and add them:
- What goes wrong most often?
- What's the diagnostic command?
- What's the fix?

### Add Project-Specific Workflows

Think about your project's common operations:
- How do you build/run?
- How do you test?
- How do you deploy?
- What's the rollback procedure?

### Add Project-Specific Architecture Docs

Document your system's:
- Component responsibilities
- Data flow between components
- API contracts
- Schema definitions

---

## Step 6: Add RAG Verification (When Ready)

When your `docs/` directory grows past ~15 files, add the RAG verification layer to turn your docs from passive reference into a queryable oracle.

**Signals you need it:**
- You catch yourself searching docs manually for "that section about X"
- Team members apply principles inconsistently
- WORK_ROUTER.md keeps growing and feels unmaintainable

**Setup:**
```bash
# Copy the RAG package
cp -r exports/rag/rag/ ./rag/

# Install dependencies
pip install sentence-transformers rank-bm25 numpy

# Build the index
python -m rag.indexer

# Query your docs
python -m rag.query "Does my error handling follow the gate pattern?"
```

See [`rag/INTEGRATION_GUIDE.md`](rag/INTEGRATION_GUIDE.md) for detailed setup instructions and customization.

---

## Step 7: Evolve (Ongoing)

The documentation structure will grow with your project:

1. **When you fix a bug** → Add the symptom to your debug runbook
2. **When you add a feature** → Update architecture docs and changelog
3. **When you establish a workflow** → Add it to the workflow registry
4. **When you learn something** → Add it to methodology docs
5. **When docs grow past ~15 files** → Add RAG verification (Step 6)

The goal is that **every lesson learned is captured** so it doesn't have to be re-learned.

---

## File Checklist

### Minimal (3 files)
- [ ] `CLAUDE.md` — AI assistant instructions
- [ ] `docs/DEVELOPER_GUIDE.md` — Change management
- [ ] `docs/CI_RULES.md` — Safety guardrails

### Standard (6 files)
- [ ] Everything in Minimal, plus:
- [ ] `docs/CORE_DOCUMENTATION_INDEX.md` — Documentation index
- [ ] `docs/WORK_ROUTER.md` — Symptom-based navigation
- [ ] `docs/DEBUG_RUNBOOK.md` — Triage and diagnosis

### Full (8+ files)
- [ ] Everything in Standard, plus:
- [ ] `docs/WORKFLOW_REGISTRY.md` — Named procedures
- [ ] `docs/architecture/SYSTEM_ARCHITECTURE.md` — System design
- [ ] `docs/CHANGELOG.md` — Change history
- [ ] `docs/knowledge-base/*.md` — Theoretical foundations (8 docs recommended)
- [ ] `docs/methodology/*.md` — Adopted skills (up to 8, optional)

### With RAG (15+ doc files)
- [ ] Everything in Full, plus:
- [ ] `rag/` — RAG verification package (from exports/rag/rag/)
- [ ] RAG index built: `python -m rag.indexer`
- [ ] CLAUDE.md updated with RAG query command

---

## Quick Validation

After setup, verify your documentation works:

1. **Can you find the build command?** → Check CLAUDE.md § 5
2. **Can you find debugging procedures?** → Check DEBUG_RUNBOOK.md
3. **Can you find the architecture?** → Check SYSTEM_ARCHITECTURE.md
4. **Can you find what changed?** → Check CHANGELOG.md
5. **Does Claude Code read CLAUDE.md?** → Start a session and verify it follows your rules
