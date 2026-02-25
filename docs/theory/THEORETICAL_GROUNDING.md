# Theoretical Grounding: Why These Frameworks

> Every design decision in a classification system carries implicit theoretical commitments. This essay makes them explicit.

The architecture document (`docs/architecture/RECURSIVE_CURATION_MODEL.md`) describes **how** the system works: recursive curation cycles, data readiness levels, certainty tiers, the curation feedback loop, and the country deepening model. This essay describes **why** those frameworks take the forms they do, grounding each in published research traditions.

SATELLITE_DEPTH.md already grounds within-category depth in six film-studies frameworks (Sarris, Bloom, Bourdieu, Baxandall, Foucault, Altman). This essay extends that grounding to the system-level frameworks that SATELLITE_DEPTH does not cover.

---

## 1. The Recursive Curation Cycle

**Architecture claim:** The system is a recursive loop — Gather → Classify → Audit → Refine → Reinforce — where each pass improves both data quality and category precision (RECURSIVE_CURATION_MODEL §1).

### Grounding: Iterative Classification in Information Science

The idea that classification improves through repeated application is foundational to library and information science. S.R. Ranganathan's *Prolegomena to Library Classification* (1967) establishes that a classification scheme is not designed once and applied forever — it must be periodically revised as the universe of subjects evolves. Ranganathan's "hospitality" principle requires that a good classification can accommodate new subjects without restructuring — precisely the split protocol (§4) in the architecture doc.

More directly, the recursive cycle mirrors the **Plan-Do-Check-Act (PDCA)** cycle formalised by W. Edwards Deming (*Out of the Crisis*, 1986). Deming's insight was that quality improves through iteration, not through getting it right the first time. Each pass through the cycle produces measurements (Check) that feed adjustments (Act) that improve the next pass. The architecture's five-pass structure (broad strokes → satellite differentiation → within-category depth → cross-category refinement → feedback) is a domain-specific instantiation of this general principle.

In machine learning, the same pattern appears as **active learning** (Settles, 2012, *Active Learning*). Active learning systems select the most informative examples for human labelling, then retrain. The architecture's review queue — where low-confidence classifications are surfaced for curator confirmation — is structurally identical. The difference is that the "model" being improved is not a statistical classifier but a rule-based routing system, and the "retraining" is manual adjustment of routing rules and whitelists rather than parameter updates.

### What the grounding adds

These traditions predict specific failure modes:
- **Deming:** If the Check stage (audit) is skipped, the system cannot improve. This grounds the requirement that every pass must include re-audit.
- **Settles:** If the system always asks the curator about the same kinds of films (e.g., always surfacing Indie Cinema edge cases), the feedback loop is inefficient. Query diversity matters.
- **Ranganathan:** If the classification cannot accommodate new categories without restructuring, it will break under growth. The split protocol's three conditions (density, coherence, archival necessity) are a form of Ranganathan's hospitality test.

---

## 2. Data Readiness Levels (R0–R3)

**Architecture claim:** Every film has a measurable data readiness level (R0 through R3) that determines which routing stages can meaningfully execute (RECURSIVE_CURATION_MODEL §2).

### Grounding: Data Quality Dimensions

Richard Y. Wang and Diane M. Strong's "Beyond Accuracy: What Data Quality Means to Data Consumers" (1996, *Journal of Management Information Systems*) established that data quality is not a single property but a multi-dimensional concept. Their framework identifies four categories: intrinsic quality (accuracy, objectivity), contextual quality (relevance, completeness, timeliness), representational quality (interpretability, consistency), and accessibility quality.

The R0–R3 model is a domain-specific projection of Wang & Strong's completeness dimension onto the classification pipeline's requirements. R0 (no year) means the most critical contextual field is missing. R3 (director + country + genres) means all fields required for full routing are present. The architecture's decision to gate routing stages based on readiness — rather than running all stages regardless — follows directly from Wang & Strong's principle that downstream operations on incomplete data produce misleading results, not useful approximations.

### Grounding: Signal Detection Theory

The confidence caps at each readiness level (R1 = 0.3, R2 = 0.6, R3 = uncapped) reflect a principle from signal detection theory (Green & Swets, *Signal Detection Theory and Psychophysics*, 1966). In SDT, a decision made with less evidence should have lower confidence — not because the decision is necessarily wrong, but because the probability of a false positive is higher. The architecture's confidence caps formalise this: a classification based on year-only (R1) carries structural uncertainty that no amount of routing sophistication can resolve. The cap prevents the system from expressing certainty it does not have.

### What the grounding adds

Wang & Strong's multi-dimensional model suggests the R0–R3 ladder could be refined further. Currently, R2 treats "has director but no country" the same as "has country but no director." But for Satellite routing (which is country-gated), missing country is more damaging than missing director. A future refinement could weight readiness by which fields are missing relative to which routing stages need them.

---

## 3. The Four-Tier Hierarchy

**Architecture claim:** Core, Reference, Satellite, and Popcorn name four categorically different relationships between collector and film — not degrees of the same thing (RECURSIVE_CURATION_MODEL §3).

### Grounding: Sarris's Ranked Argument

Andrew Sarris's *The American Cinema: Directors and Directions, 1929–1968* (1968) demonstrated that classification of directors into ranked tiers is itself a critical argument, not just an organisational convenience. Sarris's Pantheon / Far Side of Paradise / Expressive Esoterica / Less Than Meets the Eye hierarchy makes claims about the nature of cinematic achievement. The four-tier hierarchy makes analogous claims about the nature of curatorial engagement.

### Grounding: Bourdieu's Distinction

Pierre Bourdieu's *Distinction: A Social Critique of the Judgement of Taste* (1979) argues that cultural consumption is structured by habitus — the accumulated dispositions that shape how we perceive and evaluate cultural objects. Crucially, Bourdieu demonstrates that different modes of engagement with culture are not on a single continuum. The cultivated gaze that appreciates Godard and the popular gaze that enjoys mainstream entertainment are structurally different dispositions, not degrees of the same disposition.

The four tiers encode this insight. Core (identity), Reference (acknowledgment), Satellite (interest), and Popcorn (pleasure) are four distinct modes of engagement. A Kubrick film is not "liked more" than a Spider-Man film. The relationship is categorically different. The architecture's insistence on tier-first organisation (rather than decade-first or country-first) is a Bourdieuian commitment: the mode of engagement is the primary organising principle.

### Grounding: Canon Formation

Harold Bloom's *The Western Canon* (1994) argues that canons form through influence and contestation, not consensus. The Reference tier (50-film canon of non-Core directors) is explicitly a canonical claim — these are the films that define the conversation. Bloom's framework predicts that the canon will be contested (different curators would choose different 50 films) and that this contestation is productive, not a flaw. The architecture accommodates this: the Reference canon is hardcoded, but it is explicitly a design decision subject to revision, not a discovered truth.

### What the grounding adds

Bourdieu's framework raises a question the architecture doesn't address: are the four modes of engagement stable across time? A film that was Popcorn in 1975 might be Reference by 2025 (canonisation through retrospective critical attention). The architecture currently handles this through re-audit and SORTING_DATABASE overrides, but it has no explicit theory of temporal instability in tier assignment.

---

## 4. Category Definition and the Split Protocol

**Architecture claim:** Satellite categories are split when three conditions converge: density, coherence, and archival necessity (RECURSIVE_CURATION_MODEL §4).

### Grounding: Faceted Classification

Ranganathan's faceted classification (developed from the 1930s onwards; synthesised in *Prolegomena to Library Classification*, 1967) demonstrated that subjects can be classified along multiple independent axes (facets) rather than into a single hierarchical tree. The architecture's Satellite routing uses exactly this principle: country, decade, genre, and director are independent facets that combine to identify a category. A film is Italian AND 1970s AND Thriller AND by Argento → Giallo. Each facet is a separate signal; the combination is more specific than any single facet.

The split protocol's three conditions map onto established criteria in taxonomy design:
- **Density** corresponds to what Bowker & Star (*Sorting Things Out: Classification and Its Consequences*, 1999) call "membership": a category must have enough members to be useful.
- **Coherence** corresponds to what they call "consistency": members of a category should share a property that non-members lack.
- **Archival necessity** is the architecture's original contribution, grounded in Domain Grounding (Skill 4): the category must correspond to a historically documented phenomenon, not just a cluster in the collection.

### Grounding: Positive-Space vs Negative-Space

The distinction between historical categories (positive-space: defined by what they are) and functional categories (negative-space: defined by what they are not) draws on Rick Altman's *Film/Genre* (1999). Altman distinguishes between genres defined by semantic elements (specific iconography, settings, character types) and those defined syntactically (narrative structures, relationships). Positive-space categories like Giallo have strong semantic definition (Italian, 1970s, thriller, specific visual conventions). Negative-space categories like Indie Cinema have only syntactic definition (not-mainstream, not-exploitation, not-Core) — they are what remains after semantic categories have claimed their members.

Altman's framework predicts that negative-space categories will be unstable — as new semantic categories are defined, the negative-space category shrinks. This is exactly what the architecture observes: Indie Cinema absorbs films that should be elsewhere, and each new Satellite category (Japanese New Wave, HK New Wave) removes films from it.

### What the grounding adds

Bowker & Star's infrastructure studies add a critical warning: "Each category valorises some point of view and silences another" (*Sorting Things Out*, p.5). Every Satellite category boundary is a decision about what counts as a distinct tradition. The choice to have Giallo but not Poliziotteschi, French New Wave but not Cinéma du look, is a curatorial argument encoded as infrastructure. The architecture's Domain Grounding requirement (categories must be grounded in published scholarship) is the system's defence against arbitrary boundary-drawing.

---

## 5. Certainty Tiers and the Inverse Gate Rule

**Architecture claim:** Categories are ranked by the number of independent corroborating signals available for classification. As certainty decreases, gates get stricter, not looser (RECURSIVE_CURATION_MODEL §5).

### Grounding: Bayesian Evidence Combination

The principle that multiple independent signals produce more reliable classification than any single signal is formalised in Bayesian probability theory. If country, genre, decade, and director are conditionally independent given the true category, then each additional signal multiplicatively reduces the probability of a false positive. A Tier 1 category (4 independent gates) has exponentially lower false-positive probability than a Tier 3 category (2 gates).

The Inverse Gate Rule — that lower-certainty matches require stricter review, not looser acceptance — follows from the same logic. In signal detection theory (Green & Swets, 1966), when the signal-to-noise ratio is low (fewer independent signals), the optimal decision criterion shifts toward caution (higher threshold for declaring a detection). Accepting a weak signal as confidently as a strong one increases false positives without proportionally increasing true positives.

### Grounding: Active Learning and Confidence-Based Sampling

Burr Settles' *Active Learning* (2012) demonstrates that the most informative examples for human review are those where the classifier is least confident — the decision boundary cases. The architecture's review queue, which surfaces Tier 3 and Tier 4 classifications for curator review, is structurally equivalent to uncertainty sampling in active learning. The curator's time is spent where it adds the most value: confirming or correcting the cases where the system is uncertain.

### What the grounding adds

Bayesian reasoning suggests a refinement the architecture has not yet implemented: gates should not just count signals but weight them by informativeness. For Satellite routing, country is more informative than decade (many countries have distinctive traditions; most decades do not). Director is more informative than genre (directors define movements; genres cross movements). A weighted gate model would assign different confidence contributions to each signal type.

---

## 6. The Curation Loop

**Architecture claim:** The system needs bidirectional feedback — curator decisions must flow back into routing rules, whitelists, and enrichment data (RECURSIVE_CURATION_MODEL §7).

### Grounding: Human-in-the-Loop Systems

The curation loop's four actions (Accept, Override, Enrich, Defer) map onto established patterns in human-in-the-loop (HITL) machine learning (Amershi et al., "Power to the People: The Role of Humans in Interactive Machine Learning," *AI Magazine* 35(4), 2014). Amershi et al. identify four modes of human interaction with classification systems:
- **Labelling** (= Accept) — confirming the system's output
- **Correcting** (= Override) — providing the correct label when the system is wrong
- **Feature engineering** (= Enrich) — providing additional data that improves future classification
- **Deferring** (= Defer) — marking examples as requiring further investigation

The architecture's preference for Enrich over Override ("systemic improvement over point fix") is a specific design choice grounded in the HITL literature: feature engineering has higher long-term return than label correction because it improves all future classifications, not just the current one.

### Grounding: Curatorial Practice

In museum studies, Eilean Hooper-Greenhill (*Museums and the Shaping of Knowledge*, 1992) argues that classification is not a neutral act but a form of knowledge production. Every classification decision carries curatorial authority. The curation loop formalises what museum practice has always known: curators do not simply apply rules; they shape rules through their decisions. The system's distinction between Override (human overrules system) and Reinforce (human decision improves system) encodes the two directions of curatorial authority.

### What the grounding adds

Amershi et al. identify a failure mode the architecture should guard against: **feedback loops** where correcting one error introduces new errors elsewhere. If a curator overrides a Giallo classification to Indie Cinema, and this triggers a routing rule change, the rule change might misclassify other films. The architecture's "enrich before override" preference partially addresses this, but a formal impact-assessment gate ("how many other films would this rule change affect?") would be more robust.

---

## 7. The Country Deepening Model

**Architecture claim:** National cinemas are explored recursively — apex (Core directors) → named margins (Satellite categories) → splits when traditions diverge. A country is "hierarchically complete" when its Core apex is established and its named margins cover its distinct traditions (RECURSIVE_CURATION_MODEL §8).

### Grounding: National Cinema Theory

Andrew Higson's "The Concept of National Cinema" (1989, *Screen* 30(4)) argues that national cinema is not a natural category but a constructed one — shaped by critical attention, institutional support, and international circulation. Higson distinguishes between "inward-looking" national cinema (the domestic industry) and "outward-looking" national cinema (how a country's films are perceived internationally).

The architecture's country deepening model operates on the outward-looking definition: "Japanese cinema" means the traditions of Japanese filmmaking as they appear in an international collection. This is why the model has more categories for US, Japan, and Hong Kong than for Italy or France — not because those countries have richer cinematic traditions, but because their traditions are more differentiated in international circulation and in this specific collection.

### Grounding: Canon and the Core-Apex Principle

The "Core-Apex Principle" (a national cinema is hierarchically complete when its greatest work is in Core) echoes Sarris's *The American Cinema*, which assumes that the apex of a national cinema is its auteurs. Sarris's hierarchy is explicitly national — his ranking of American directors is a statement about the structure of American cinema. The architecture generalises this: every national cinema explored deeply enough reveals an auteur apex and distinct margins.

Mette Hjort and Scott Mackenzie (*Cinema and Nation*, 2000) complicate this by arguing that national cinema categories are always contested and politically charged. The architecture partially addresses this through Domain Grounding (categories must be grounded in published scholarship, not invented from collection contents). But the choice of which national cinemas to deepen — US, Japan, HK, Italy, France — reflects the collection's biases as much as any neutral scholarly assessment.

### What the grounding adds

Higson's distinction between inward-looking and outward-looking national cinema suggests that the country deepening model may systematically underrepresent cinematic traditions that circulate primarily domestically. Films from countries with small international distribution (e.g., Iranian cinema beyond Kiarostami, Turkish cinema beyond Ceylan) may appear sparse in the collection not because the tradition is thin but because international access is limited. The architecture should distinguish between "not enough films" (collection limitation) and "not a distinct tradition" (genuine absence).

---

## 8. Double-Loop Learning

**Architecture claim:** The system should question its governing variables when failure patterns recur, not just correct individual instances (EVIDENCE_ARCHITECTURE.md §1).

### Grounding: Argyris and Organisational Learning

Chris Argyris and Donald Schon (*Organizational Learning: A Theory of Action Perspective*, 1978; Argyris, "Double Loop Learning in Organizations," *Harvard Business Review*, 1977) identified two modes of learning:

**Single-loop:** Detect error → correct the specific action → governing variables unchanged. "Dennis Hopper is not in the directors list. Add him."

**Double-loop:** Detect error → question the governing variables → change the rules. "44 films fail the same gate. The assumption that genre data is always available for routing is wrong for this population."

Single-loop fixes the instance. Double-loop fixes the *kind of failure*. The classification pipeline currently operates in single-loop mode: each Issue (#14 through #34) adds a directors list entry, a SORTING_DATABASE pin, or a gate relaxation — correcting the specific symptom without questioning the structural assumption that produced it.

### What the grounding adds

Argyris identified **defensive routines** as the reason systems resist double-loop learning: patching the symptom is easier than questioning the architecture. The pattern is visible in the codebase: each Issue makes a specific failure disappear, but the pipeline continues to produce structurally identical failures because the information it would need to self-diagnose is destroyed at every stage.

Double-loop learning requires the system to *capture evidence about its own failures* so that recurring patterns can be detected and structural causes identified — rather than relying on a human to re-derive the diagnosis from source code each time.

---

## 9. Evidence Under Uncertainty

**Architecture claim:** Binary gates (pass/fail) destroy information by conflating negative evidence with absent evidence. Evidence-preserving gates would retain what was tested, what matched, and what could not be evaluated (EVIDENCE_ARCHITECTURE.md §2).

### Grounding: Dempster-Shafer Evidence Theory

Glenn Shafer (*A Mathematical Theory of Evidence*, 1976) developed a formal framework for reasoning under uncertainty that distinguishes three states: **belief** (evidence for), **disbelief** (evidence against), and **uncertainty** (absence of evidence). This is more expressive than Bayesian probability, which collapses uncertainty into a prior.

When a film has `country=IT, decade=1970s, genres=[]` and the Giallo gate requires Horror/Thriller genres:
- Belief: country + decade both match (evidence for Giallo)
- Disbelief: none (no evidence actively contradicts Giallo)
- Uncertainty: genres absent (cannot evaluate)

Binary gates collapse this to `True AND False = False`. The positive evidence is destroyed by the absence of genre data. Dempster-Shafer would maintain all three signals: "moderate support for Giallo with high uncertainty on one gate."

### What the grounding adds

Dempster-Shafer predicts a specific failure mode the pipeline exhibits: **the information destruction cascade**. When gates short-circuit on the first `False`, all accumulated evidence for that category is abandoned. The `continue` statement in the Satellite routing loop is the cascade trigger. The theory also predicts the remedy: **evidence accumulation across gates** — evaluate all gates for all categories, then select the category with the strongest evidence profile. This is what `scripts/category_fit.py` does post-hoc; it should be the primary routing mechanism.

This extends §5 (Certainty Tiers): Bayesian evidence combination described there assumes signals are present. Dempster-Shafer handles the case where signals are absent — the distinction that the current pipeline cannot make.

---

## 10. Collective Classification and Stigmergy

**Architecture claim:** Films should not be classified in isolation. The accumulated results of previous classifications in a run constitute collective evidence that should inform ambiguous cases (EVIDENCE_ARCHITECTURE.md §2).

### Grounding: Stigmergy (Grasse, 1959; Theraulaz and Bonabeau, 1999)

Pierre-Paul Grasse coined "stigmergy" in 1959 to describe how termites coordinate construction without direct communication: each agent modifies the shared environment, and those modifications guide subsequent agents. Guy Theraulaz and Eric Bonabeau ("A Brief History of Stigmergy," *Artificial Life* 5(2), 1999) generalised this to any system where agents coordinate through environmental traces rather than direct communication. The key insight: **the intelligence is in the accumulated traces, not in any individual agent**.

When 28 of 30 Italian 1970s films route to Giallo, the 29th film with missing genres receives no benefit from the 28 successful classifications. The pipeline has collective evidence that Italian 1970s films tend to be Giallo, but each film is a fresh start. The missing mechanism is environmental trace: each classification leaves a record (base rates, conditional probabilities, near-miss flags) that modifies the shared classification context within a run.

### What the grounding adds

Stigmergy predicts that classification quality should improve with corpus size — more films means richer context for ambiguous cases. The current architecture has the opposite property: corpus size is irrelevant because each film is classified in isolation. Stigmergy also predicts a natural mechanism for taxonomy gap detection: if a cluster of films leaves traces in the same unmatched region of the evidence space, that region is a candidate for a new category.

---

## 11. Shared Workspace vs Pipeline

**Architecture claim:** The pipeline's sequential stage architecture prevents stages from seeing each other's evidence. A shared workspace would allow each stage to read the full accumulated context (EVIDENCE_ARCHITECTURE.md §2-3).

### Grounding: Blackboard Architecture (Erman et al., 1980)

The Hearsay-II speech understanding system (Erman, Hayes-Roth, Lesser, and Reddy, "The Hearsay-II Speech-Understanding System: Integrating Knowledge to Resolve Uncertainty," *Computing Surveys* 12(2), 1980) introduced the **blackboard architecture**: multiple knowledge sources contribute to a shared data structure. Any source can read the current state and add information. The system converges through incremental evidence accumulation, not sequential filtering.

The blackboard was designed for problems where multiple independent knowledge sources exist, no single source suffices, evidence must be combined across sources, and the problem has inherent ambiguity. All four conditions describe the film classification problem.

In the current pipeline, the Satellite classifier cannot see that the parser struggled with the title. The Popcorn classifier cannot see that Satellite almost matched. Each stage is blind to context accumulated elsewhere.

### What the grounding adds

The blackboard literature identifies **opportunistic problem-solving**: the most informative knowledge source should contribute next, regardless of fixed ordering. The pipeline's priority order (Reference → Satellite → Core → Popcorn) is correct as a tiebreaker when evidence is equal, but it should not determine which stages execute — that should be driven by data availability. A film with strong director data and absent country data should route on director first, not follow the fixed sequence.

---

## 12. Requisite Variety

**Architecture claim:** The pipeline's response vocabulary (`unsorted_no_match`) is too impoverished to distinguish failure modes that require different remediation actions (EVIDENCE_ARCHITECTURE.md §3).

### Grounding: Ashby's Law of Requisite Variety (1956)

W. Ross Ashby (*An Introduction to Cybernetics*, 1956) proved that a controller can only regulate a system to the extent that the controller's variety matches the system's variety. If the system has more states than the controller has responses, some states go uncontrolled.

The film corpus has high variety: films differ in country, decade, genre, director, data completeness, category proximity, and ambiguity. The routing rules have low variety: binary gates, a fixed response set, and a single reason code for all failures. The mismatch is predictable: `unsorted_no_match` conflates films needing enrichment (R1), films needing rules (R2b taxonomy gaps), genuinely unroutable films (adult, TV), and near-misses. The controller cannot distinguish them because its vocabulary doesn't include "near-miss," "data quality issue," or "taxonomy gap."

### What the grounding adds

Ashby's law predicts the remedy: increase the controller's variety to match the system's. Richer reason codes, structured failure output (which gates passed/failed), and population-level analysis that groups similar failures. The controller needs enough variety to distinguish failure modes that require *different actions* — enrichment, review, deferral, or new category evaluation.

---

## 13. Relationship to Existing Theory Essays

This essay complements the theoretical grounding already present in the project:

| Framework | Grounded in | Covers |
|-----------|------------|--------|
| Within-category depth | SATELLITE_DEPTH.md §2 | Sarris, Bloom, Bourdieu, Baxandall, Foucault, Altman |
| Satellite boundaries and caps | MARGINS_AND_TEXTURE.md | Why exploitation cinema belongs in the archive |
| Category lifecycle | REFINEMENT_AND_EMERGENCE.md | How categories form, split, and mature |
| Collection identity | COLLECTION_THESIS.md | Decades, format, personal philosophy |
| Tier architecture | TIER_ARCHITECTURE.md | Why four tiers, auteur criteria |
| **Recursive curation** | **This essay** | Deming, Ranganathan, Settles (active learning) |
| **Data readiness** | **This essay** | Wang & Strong (data quality), Green & Swets (SDT) |
| **Tier hierarchy (system-level)** | **This essay** | Sarris, Bourdieu, Bloom |
| **Category design** | **This essay** | Ranganathan, Bowker & Star, Altman |
| **Certainty tiers** | **This essay** | Bayesian reasoning, signal detection theory |
| **Curation loop** | **This essay** | Amershi et al. (HITL), Hooper-Greenhill (museums) |
| **Country deepening** | **This essay** | Higson, Hjort & Mackenzie (national cinema) |
| **Double-loop learning** | **This essay** | Argyris (organisational learning) |
| **Evidence under uncertainty** | **This essay** | Dempster-Shafer (evidence theory) |
| **Collective classification** | **This essay** | Grasse, Theraulaz & Bonabeau (stigmergy) |
| **Shared workspace** | **This essay** | Erman et al. (blackboard architecture) |
| **Requisite variety** | **This essay** | Ashby (cybernetics) |

---

## References

Argyris, C. (1977). Double Loop Learning in Organizations. *Harvard Business Review*, 55(5), 115-125.

Altman, R. (1999). *Film/Genre*. London: BFI Publishing.

Ashby, W.R. (1956). *An Introduction to Cybernetics*. London: Chapman & Hall.

Amershi, S., Cakmak, M., Knox, W.B., & Kulesza, T. (2014). Power to the People: The Role of Humans in Interactive Machine Learning. *AI Magazine*, 35(4), 105-120.

Bloom, H. (1994). *The Western Canon: The Books and School of the Ages*. New York: Harcourt Brace.

Bourdieu, P. (1979/1984). *Distinction: A Social Critique of the Judgement of Taste*. Trans. R. Nice. Cambridge, MA: Harvard University Press.

Bowker, G.C. & Star, S.L. (1999). *Sorting Things Out: Classification and Its Consequences*. Cambridge, MA: MIT Press.

Deming, W.E. (1986). *Out of the Crisis*. Cambridge, MA: MIT Center for Advanced Engineering Study.

Erman, L.D., Hayes-Roth, F., Lesser, V.R., & Reddy, D.R. (1980). The Hearsay-II Speech-Understanding System: Integrating Knowledge to Resolve Uncertainty. *Computing Surveys*, 12(2), 213-253.

Grasse, P.-P. (1959). La reconstruction du nid et les coordinations interindividuelles chez Bellicositermes natalensis et Cubitermes sp. *Insectes Sociaux*, 6, 41-80.

Green, D.M. & Swets, J.A. (1966). *Signal Detection Theory and Psychophysics*. New York: Wiley.

Higson, A. (1989). The Concept of National Cinema. *Screen*, 30(4), 36-47.

Hjort, M. & Mackenzie, S. (Eds.) (2000). *Cinema and Nation*. London: Routledge.

Hooper-Greenhill, E. (1992). *Museums and the Shaping of Knowledge*. London: Routledge.

Ranganathan, S.R. (1967). *Prolegomena to Library Classification* (3rd ed.). Bombay: Asia Publishing House.

Sarris, A. (1968). *The American Cinema: Directors and Directions, 1929–1968*. New York: E.P. Dutton.

Settles, B. (2012). *Active Learning*. Synthesis Lectures on Artificial Intelligence and Machine Learning. Morgan & Claypool.

Shafer, G. (1976). *A Mathematical Theory of Evidence*. Princeton, NJ: Princeton University Press.

Theraulaz, G. & Bonabeau, E. (1999). A Brief History of Stigmergy. *Artificial Life*, 5(2), 97-116.

Wang, R.Y. & Strong, D.M. (1996). Beyond Accuracy: What Data Quality Means to Data Consumers. *Journal of Management Information Systems*, 12(4), 5-33.

*§8-§12 ground the evidence architecture described in [EVIDENCE_ARCHITECTURE.md](../architecture/EVIDENCE_ARCHITECTURE.md).*
