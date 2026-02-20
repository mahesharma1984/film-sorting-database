# Skill: Creative and Discovery Tasks

**Purpose:** Provide operational protocols for the two task types that the R/P Split skill does not cover — Creative (novel output, subjective quality) and Discovery (exploring a space before the problem is defined).
**Addresses:** Unbounded exploration, missing stopping criteria, Creative outputs that aren't grounded in stated criteria, and the gap between Discovery output and the Precision/Reasoning tasks it should feed.

---

## Core Distinction

The R/P Split covers work where the schema is already known: a Reasoning task interprets against it; a Precision task implements it. Creative and Discovery are the **prerequisite stages** — they produce the schemas and taxonomies that Reasoning and Precision then consume.

```
DISCOVERY → defines the question
CREATIVE  → produces the schema / decision
              ↓
REASONING → interprets against the schema
PRECISION → implements the schema
```

When something feels like "we need to figure out what we're doing before we can do it," that's Discovery. When something feels like "there's no single right answer but we need to make a defensible call," that's Creative. Both must produce a concrete handoff output or they haven't finished.

---

## Discovery Tasks

### The Core Problem

Discovery tasks have no natural stopping point. Exploration can always continue. Without explicit structure, Discovery collapses into the Rabbit Hole anti-pattern: increasing effort on diminishing returns, no output, and eventually an arbitrary decision that feels unjustified.

### Protocol

**Step 1: Define the output form before you explore.**

State what a completed Discovery looks like. Not what you'll find — that's unknown. What shape the answer takes.

```
BAD:  "Let's figure out which directors belong in Core"
GOOD: "We will produce a list of director names, each with
       a one-line justification citing TIER_ARCHITECTURE.md (Part II: Auteur Criteria).
       The list is complete when every director who appears
       in the collection has either a whitelist entry or a
       documented exclusion reason."
```

If you cannot state the output form, you're still in problem definition — not discovery. Stay there until you can.

**Step 2: Set stopping criteria before you explore.**

Discovery stops when you can specify the Precision or Reasoning task the discovery was meant to produce. State this explicitly:

```
This discovery is complete when:
→ [specific Precision task] can be written with no remaining unknowns
→ OR [specific Reasoning task] has a defined schema to reason against
→ OR we have established that the discovery target doesn't exist / isn't needed
```

**Step 3: Scope before depth.**

Survey breadth first. For a potential new Satellite category: how many films would it catch? Is there sufficient collection mass to justify a routing rule? A category that catches 3 films is probably a lookup entry, not a routing rule. Depth (detailed research on specific films) comes after you've confirmed the category is worth defining.

**Step 4: Rabbit hole detection.**

| Signal | What's Happening |
|---|---|
| "This changes everything" | Probably doesn't — restart from Step 1 |
| Same problem reframed 3+ times | You've lost the output form |
| New sub-questions keep appearing | Scope has not been bounded |
| Can't answer "what would done look like?" | Still in problem definition |

Fix: restate the output form from Step 1. If it's changed significantly, update it explicitly and restart the timer. If you can't restate it, the discovery was never properly scoped.

### Film Classification Examples

**"Which directors belong in Core?" (FNW Core audit, Issue #22)**

Output form: a list of director names, each with a justification against TIER_ARCHITECTURE.md (Part II: Auteur Criteria), plus a routing assignment for non-Core FNW directors (SATELLITE_ROUTING_RULES directors list entry or documented exclusion).

Stopping criterion: every director who appears in the collection with FNW-era films has been classified — either Core whitelist entry, or SATELLITE_ROUTING_RULES entry, or documented "falls to Unsorted (expected)."

Scope before depth: first pass — how many FNW-era directors appear in the collection? Are there any obvious Core cases (Godard, Varda, Resnais, Rivette, Chabrol, Demy, Duras — directors with self-consistent bodies of work across multiple decades)? Are there obvious non-Core cases (Truffaut — major figure but primarily associated with one period)? Depth (per-director justification) only after the scope is mapped.

**"Should Romanian New Wave be a Satellite category?"**

Output form: either a completed routing rule entry (country code, decade range, director list or genre conditions), or a documented decision: "not enough collection mass — add as lookup entries instead."

Stopping criterion: the discovery is complete when the output can be written as either a SATELLITE_ROUTING_RULES addition or a set of SORTING_DATABASE.md entries with a comment explaining why a routing rule wasn't warranted.

---

## Creative Tasks

### The Core Problem

Creative tasks have no single correct output. Without stated criteria, evaluation is impossible — you're choosing between options with no basis for preferring one over another. The common failure: generate options first, then invent justifications for the chosen one (post-hoc rationalization applied to Creative tasks).

### Protocol

**Step 1: State evaluation criteria before generating options.**

```
BAD:  "Let's pick the best 50 films for the Reference canon"
GOOD: "Reference canon films must satisfy all of these:
       1. Director is not in the Core whitelist
       2. Film is canonical within its tradition (documented
          by critical consensus, not just collection presence)
       3. The tradition it represents is not already covered
          by 5+ films in the canon
       4. Year falls within a tradition's historically active period"
```

If you can't state the criteria, you don't have a Creative task — you have an undefined one. Define it before generating options.

**Step 2: Apply criteria, don't reverse-engineer them.**

Select options that meet the stated criteria. Do not generate a preferred list and then write criteria that justify it. The criteria must be able to predict what a new option would look like — if removing all current options, the criteria should still be meaningful.

**Step 3: "Done" is criteria-passing, not consensus.**

A Creative task is complete when:
- All stated criteria are satisfied by the output
- The output is defensible against the published framework that grounded the criteria (see Domain Grounding)
- No criterion was silently dropped or modified to accommodate the output

"Everyone agrees" is not required and often not achievable. "Defensible against stated criteria" is the bar.

**Step 4: Bound the iteration.**

Creative tasks don't iterate indefinitely. Set a revision limit (typically 2-3 passes) or a time budget. After that, ship the decision and revisit if new evidence contradicts it. Indefinite Creative iteration is a symptom of either undefined criteria (go back to Step 1) or Rabbit Hole detection (treat it as Discovery that hasn't been scoped).

### Film Classification Examples

**Reference canon selection (50-film hardcoded list)**

Criteria (from CLAUDE.md and TIER_ARCHITECTURE.md): non-Core director; canonical within its tradition; tradition not over-represented; year within tradition's active period. Done when all 50 films pass all criteria and the list covers the major traditions the collection represents.

**Core whitelist entry decision**

Criteria (from TIER_ARCHITECTURE.md (Part II: Auteur Criteria)): director has a self-consistent body of work spanning multiple decades; the work constitutes a coherent artistic project; the director is not primarily associated with a single movement or period. Done when the decision is justified against those three criteria — not when everyone agrees the director is important.

**Decade boundary decision for a Satellite category**

Criteria: historically documented active period in published film scholarship; sufficient collection mass in those decades; no overlap with an adjacent category's decade range. Done when all three criteria are satisfied and the boundary is cited in SATELLITE_CATEGORIES.md with source.

---

## The Handoff

Discovery and Creative tasks are complete only when their output is documented and feeds the next task. An undocumented decision is not a valid handoff.

| Discovery/Creative output | Feeds | Form |
|---|---|---|
| Director classification decision | Precision: update whitelist or routing rule | Named entry in code constant or SORTING_DATABASE.md |
| New category definition | Precision: add routing rule | Completed SATELLITE_ROUTING_RULES entry |
| Category boundary decision | Reasoning: classify specific films | Decade range + country code in routing rule |
| Reference canon selection | Precision: update REFERENCE_CANON list | 50-line hardcoded list in lib/constants.py |

If the output cannot be written in the form shown above, the task hasn't finished. "We decided X" is not a handoff. "We updated SATELLITE_ROUTING_RULES with entry Y (PR #Z)" is a handoff.

---

## Integration with Other Skills

| Skill | How It Connects |
|---|---|
| **R/P Split** | Creative and Discovery are prerequisites to R/P Split. R/P Split assumes the schema is known; Creative/Discovery is how you build the schema when it isn't known yet. After a Creative task produces a taxonomy decision, R/P Split assigns who implements it (code for precision rules, LLM reasoning for per-film classification). |
| **Pattern-First** | Discovery produces the pattern. Pattern-First ensures instances are populated after the pattern is stable. Running Pattern-First without a prior Discovery/Creative phase assumes the schema is already known — which is fine for stable taxonomies, but not for new categories or changed boundaries. |
| **Domain Grounding** | Creative tasks that design taxonomies must still ground results in published frameworks. "I decided this through a Creative process" does not replace grounding. The Creative process should produce a decision; Domain Grounding ensures the decision is defensible against an external standard. |
| **Prototype Building** | The exploration stages in task-design-theory.md (Problem Definition → Decomposition → Pattern Recognition) are the Discovery phases. Prototype Building operationalizes the transition from Discovery to Execution: Real Case First, then extract the pattern, then build. |
| **Measurement-Driven** | After a Creative decision produces a rule change, Measurement-Driven validates the impact: run classify.py on the collection, measure how many films were affected, verify the delta matches expectations. This is the breadth check that confirms the Creative output was correctly translated into a Precision implementation. |

---

## Checklist

When starting a Discovery task:
- [ ] Stated what form the output takes (before exploring)
- [ ] Stated the stopping criterion (when can we specify the next Precision/Reasoning task?)
- [ ] Scoped breadth before depth (how many items are involved?)
- [ ] Set a rabbit-hole tripwire (what signal will tell us we've lost the thread?)

When completing a Discovery task:
- [ ] Output is documented in the form stated at the start
- [ ] Every item in scope has been resolved (no silent gaps)
- [ ] The Precision or Reasoning task that this discovery enables can now be written

When starting a Creative task:
- [ ] Stated evaluation criteria before generating options
- [ ] Criteria are grounded in published theory or explicit project standards (TIER_ARCHITECTURE.md (Part II: Auteur Criteria), TIER_ARCHITECTURE.md, etc.)
- [ ] Revision limit or time budget is set

When completing a Creative task:
- [ ] All stated criteria are satisfied by the output
- [ ] No criterion was silently modified to accommodate the output
- [ ] Output is documented in a handoff form (updated constant, rule entry, database record — not just a decision recorded in prose)
