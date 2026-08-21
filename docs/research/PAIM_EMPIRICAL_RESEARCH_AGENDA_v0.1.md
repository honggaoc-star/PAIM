# PAIM Empirical Research Agenda v0.1

## 1. Purpose and status

This agenda identifies empirical questions that become possible or more precise because Practical
AI Management (PAIM) now exists as a conceptual model and bounded released implementation. It is
a research-planning artifact, not a product specification, experimental protocol, or validation
claim. It does not require that every question be pursued.

The [PAIM v0.1 Conceptual Guide](../PAIM_CONCEPTUAL_GUIDE_v0.1.md) is the current conceptual
exposition. The [system specifications](../system/specifications/) define released PAIM semantics,
and the [Increment 9 validation results](../system/testing/PAIM_INCREMENT_9_V0_1_VALIDATION_RESULTS_v0.1.md)
record bounded conformance and practitioner evidence. None of those sources proves that PAIM
improves organizational decisions or outcomes.

> PAIM is being developed in a domain where both AI technology and management practice remain
> unsettled. The research program therefore treats its own conceptual positions as revisable.
> Prior work—including RWR, AIVM, earlier PAIM design, and related research—provides motivation,
> hypotheses, concepts, and provisional understanding rather than conclusions that subsequent work
> is obliged to preserve. New evidence may support, refine, qualify, or contradict earlier
> positions. Such revision is treated as learning rather than failure.

The shorter governing principle is:

> **No prior PAIM-related proposition is protected from reassessment by virtue of being prior.**

The program must not optimize for confirmation of published work. Consistency with prior work is
desirable only when supported by evidence; it must not be manufactured.

## 2. Core question and research posture

The agenda is organized around one question:

> **What can we learn about practical AI management by studying PAIM, its concepts, its use,
> alternatives to it, and the management behavior that emerges around it?**

This question permits several outcomes. Evidence may show that a PAIM distinction improves
clarity or challenge. It may show that the distinction has value only in higher-consequence or
less mature settings. It may show that a simpler mechanism works as well, or that the distinction
creates burden without sufficient benefit. It may reveal a missing concept or behavior that no
prior PAIM document anticipated.

Research reports should separate four epistemic states:

- **defined:** a concept or behavior appears in a PAIM contract;
- **validated within a bounded test:** evidence shows conformance under stated conditions;
- **hypothesized:** a relationship or benefit is plausible but not established; and
- **unknown:** available evidence does not support a directional conclusion.

The released application and practitioner pathways provide a research object and feasibility
evidence. They do not convert PAIM design choices into empirically proven management principles.

## 3. Where research questions come from

PAIM research questions have three distinct origins. Keeping them visible reduces the risk that a
research program simply restates the design as a set of expected findings.

### 3.1 PAIM-derived questions

These questions arise from designing, specifying, implementing, validating, and operating PAIM.
They concern distinctions such as Managed Configuration, Evidence Applicability, independent Value
and Risk histories, explicit absence and conflict, authority layers, activation prerequisites,
Reassessment, and exact historical reconstruction. The existence of a distinction is evidence
that it can be studied, not evidence that it is correct or proportionate.

### 3.2 Prior-research questions

These questions are inherited or adapted from Return-Weighted Risk (RWR), AI Value Management
(AIVM), AI risk management, adaptive management, benefits realization, organizational governance,
evaluation, assurance, and related work. Prior research can motivate hypotheses and comparisons.
It does not control PAIM findings or require that PAIM preserve an earlier proposition.

### 3.3 Emergent-use questions

These questions appear when practitioners use PAIM in ways that theory and design did not predict.
They may concern workarounds, misunderstanding, omitted concepts, redundant controls, authority
conflict, organizational variation, or behavior induced by the interface itself. The agenda
reserves room for these surprises before studies begin; otherwise unanticipated evidence may be
misclassified as noise.

Questions may move between categories over time. An emergent behavior can become a PAIM-derived
design question, and a prior-research proposition can be reframed after observing real use.

## 4. PAIM-derived research domains

The following domains define a starting portfolio. Each treats the PAIM design choice as
revisable. Candidate observables are illustrative; every study still needs an independent construct
definition and a design suited to the question.

### 4.1 Managed Configuration and Evidence portability

PAIM manages an exact bounded Configuration and Versions of it rather than “the AI” generally.
That choice may improve decision relevance, but it may also demand distinctions practitioners do
not consistently need.

Research questions include:

- Does managing an exact Configuration produce more relevant or internally consistent judgments
  than managing an AI system or use at a broader level?
- Does explicit Evidence Applicability reduce unsupported transfer of pilot evidence to expanded,
  changed, or differently operated uses?
- Which Configuration changes cause practitioners to revisit evidence, and which changes are
  treated as immaterial in practice?
- When do Record/Version and identity-continuity distinctions improve management, and when do they
  become burdensome recordkeeping?
- Would a simpler boundary representation produce comparable decisions with lower effort?

Candidate observations include the scope of evidence cited, unsupported portability assumptions,
missed configuration differences, time to establish scope, disagreement, and later correction.
A study should allow the result that only some configuration dimensions are decision-relevant.

### 4.2 Independent Value and Risk

PAIM preserves separate Value and Risk inputs, histories, boundaries, uncertainty, provenance, and
accountability. Independence is intended to prevent one conclusion from determining the other,
but it may duplicate work or create artificial separation.

Research questions include:

- Does maintaining independent Value and Risk inputs materially change evidence requests,
  challenge, alternatives, rationale, or disposition?
- Does independence improve credible challenge, or merely require the same information to be
  processed twice?
- Under what conditions do Value and Risk require separate histories and accountabilities?
- How do power, information control, and professional role affect the independence achieved in
  practice?
- Are there low-consequence or well-understood cases in which the separation should be simplified
  or refined?

Candidate designs should compare both reasoning and burden. Different conclusions are not
automatically better conclusions, and agreement is not automatically evidence that independence
failed.

### 4.3 Uncertainty, conflict, and non-inference

PAIM preserves absence, conflict, and Decision-Limiting Uncertainty rather than filling them with
recency, hierarchy, similarity, or favorable defaults. The empirical issue is whether this
discipline improves judgment enough to justify the friction it creates.

Research questions include:

- Does explicit absence or conflict change what practitioners investigate, escalate, or decide?
- When does fail-closed behavior prevent an unsupported inference, and when does it unnecessarily
  delay or block action?
- Which non-inference rules prevent consequential errors in real practice?
- Do practitioners understand an explicit conflict as useful management information or as a
  system failure to be bypassed?
- Can alternative representations preserve epistemic honesty with less procedural burden?

Useful observations may include unsupported assumptions, workaround attempts, time to resolution,
quality of escalation, reversals after missing information appears, and practitioner confidence.

### 4.4 Identity, access, visibility, accountability, and authority

PAIM distinguishes authenticated identity, permission to attempt an exact action, visibility of
the exact governed context, accountable Role Assignment, and substantive Authority or
Authorization Basis.

Research questions include:

- Does the five-layer distinction improve management clarity, control, challenge, or auditability?
- Which layers remain genuinely distinct in organizational practice, and under what conditions?
- Where do practitioners systematically confuse software permission or administrative status with
  organizational authority?
- Does exact Case/Configuration visibility prevent harmful disclosure without making work
  impractical?
- Does explicit authority modeling expose meaningful gaps and conflicts, or create procedural
  burden without changing decisions?

Studies should examine both failures prevented and legitimate work obstructed. A successful access
denial is not automatically a successful management outcome.

### 4.5 Decision, implementation, and activation

PAIM separates an authorized Decision from Intervention, Completion Result, accountable Completion
Acceptance, prerequisite satisfaction, and Activation Authorization. This chain is intended to
prevent “approved” from silently becoming “operating.”

Research questions include:

- Does the separation prevent material operation before required work is complete and accepted?
- Which boundaries catch errors that ordinary change or project management misses?
- Which separations are essential, and which may be overly elaborate for some uses?
- Does explicit Activation Authorization change when, how, or by whom operation is permitted?
- How often do Completion Results, accountable Acceptances, and actual operating conditions
  diverge?

Candidate observations include premature activation, obligation omissions, self-acceptance,
scope mismatch, time and role burden, and the quality of fallback or remediation.

### 4.6 Learning, Trigger, and Reassessment

PAIM separates new information, Trigger promotion, Trigger Determination, Reassessment, and the
eventual confirmation or successor Decision. This may reduce both overreaction and unjustified
persistence, but it may also add delay.

Research questions include:

- Does explicit Trigger Determination distinguish material from non-material change more
  consistently than ordinary practice?
- Does governed Reassessment reduce the persistence of weak, stale, or purpose-shifted Decisions?
- How much coordination and documentation burden does continuing Reassessment introduce?
- When does new evidence lead practitioners to confirm the existing Decision, authorize a
  successor, narrow operation, or stop?
- Do explicit Trigger coverage and completion rules reduce lost or repeatedly reconsidered
  concerns?

Study designs should distinguish responsiveness from mere activity. A higher Trigger count does
not establish better detection or better reconsideration.

### 4.7 Concurrency and interim operation

PAIM represents overlapping Reassessments, explicit coordination, and restrictive Interim
Operating Dispositions without inferring an ordering among operating-state identities.

Research questions include:

- How do practitioners recognize and manage overlapping Reassessments?
- Does explicit coexistence, grouping, supersession, or cancellation improve coordination, or
  simply formalize conflict?
- Are restrictive exact-scope interim dispositions useful while uncertainty remains unresolved?
- Does refusal to rank unordered operating states prevent false inference or hinder practical
  decisions?
- How often do indeterminate combined effects occur, and are affected-scope suspensions
  proportionate?

Research must not use these questions to design IRR-014 operating-state relations. They test the
released refusal to infer relations; future semantics would require separate design authority.

### 4.8 Cross-Case Management Register

The Register derives source-traceable views, preserves access filtering, and groups Shared
Dependencies only through exact Candidate Sets and accountable equivalence determinations. It
returns contextual action to the owning domain rather than resolving concerns itself.

Research questions include:

- Does the Register improve cross-Case attention, coordination, or discovery of shared concerns?
- Can a derived view remain useful without transferring authority or becoming a competing source
  of truth?
- Do practitioners infer semantic similarity or dependency even when PAIM refuses to do so?
- What aggregation is useful without leaking protected facts or creating false authority?
- Does contextual return to an owning-domain action improve follow-through or create navigation
  burden?

Candidate observations include missed cross-Case concerns, false grouping, leakage, authority
confusion, action completion, and reliance on stale projections.

### 4.9 Exact history and dual-time reconstruction

PAIM preserves stable Record identity, immutable Version identity, effective time, recorded time,
and knowledge-time reconstruction. Exactness may improve later challenge but increases cognitive
and operational demands.

Research questions include:

- Does exact historical reconstruction materially improve Reassessment, audit, assurance, or
  challenge?
- Which identity and time distinctions do practitioners actually use?
- How often would a latest-state or single-time account lead to a different interpretation?
- Is the cost of exact versioning justified by observed management benefit?
- Can tools reduce identity burden without replacing exactness with broad semantic selection?

Outcomes should include errors prevented as well as time, training, and recovery cost. More
traceability is not automatically better governance.

### 4.10 Usability and governance burden

The v0.1 practitioner evidence found correct governed behavior alongside substantial
documentation and procedure friction. One practitioner and three guided pathways are useful
signals, not generalizable usability evidence.

Research questions include:

- Which PAIM distinctions are valuable to practitioners, and which feel unnecessarily complex?
- Does greater explicitness improve confidence and reconstructability at an acceptable cost?
- Where does PAIM shift burden among business, Risk, governance, operations, and assurance rather
  than reduce it?
- How much training, documentation, interface support, and organizational maturity are needed for
  independent use?
- Do usability constraints cause workarounds that weaken the intended governance behavior?

Burden is an outcome to measure, not automatically a defect or virtue. A burdensome step may
prevent consequential error; a smooth step may conceal unsupported inference.

## 5. Questions adapted from prior research

Prior research expands the question set but does not establish the agenda’s expected answers.

### 5.1 Return-Weighted Risk

The working paper
[*Return-Weighted Risk for Navigating an Evolving AI Landscape*](https://github.com/honggaoc-star/AI-Risk-Management/blob/main/Return-Weighted-Risk/Return-Weighted-Risk-for-Navigating-an-Evolving-AI-Landscape.pdf)
was an important motivating influence for PAIM, especially in reconnecting an evolving Value case
and independently assessed Risk case with continuing organizational action. RWR remains one prior
research source among several.

RWR §8.4 proposes five future empirical questions:

1. **Risk discovery:** Does purpose-directed inquiry identify different or earlier risks than
   category-based assessment alone?
2. **Decision effects:** Does explicit separation of Risk permissibility and Value justification
   change continuation or scaling decisions?
3. **Persistence versus burden:** Does formal reauthorization after purpose or Value revision
   prevent weak projects from persisting, or merely add procedural burden?
4. **Institutional design:** What arrangements produce credible Value challenge without
   transferring business judgment to Risk functions?
5. **Learning versus delay:** Under what conditions does concurrent Learning justify staged action
   rather than delay or termination?

The paper also proposes a modest first test: practitioners assess the same AI-use case under
ordinary governance and under the RWR three-test approach, then compare evidence requested,
dependencies identified, rationale, and disposition. That comparison could show whether the
reasoning intervention changes decision-relevant reasoning at all. It could not establish that
RWR improves real-world outcomes.

These are candidate questions PAIM may help study, not obligations for PAIM research. PAIM has no
obligation to back-support, prove, implement, or defend RWR. PAIM v0.1 does not empirically
validate RWR, and RWR does not validate PAIM. Future PAIM findings may support, refine, extend,
qualify, or challenge propositions discussed in RWR; findings with no RWR mapping remain
independent PAIM contributions. Aster Vale may be used as a constructed stimulus, but it is not
empirical evidence and should not organize the agenda.

### 5.2 AIVM, Value, and related work

The current PAIM repository establishes only the interface boundary relevant here: AIVM may
provide an upstream Value input, while PAIM also accepts compatible inputs from other analytical
capabilities. PAIM’s Value/Risk interface preserves finding, boundary, uncertainty, implication,
and provenance without prescribing AIVM’s internal method.

That boundary motivates questions without attributing unverified propositions to AIVM:

- Do different Value methods produce materially different PAIM-facing inputs for the same
  Configuration?
- Which Value evidence and uncertainty distinctions survive the handoff into management judgment?
- How do control burden, alternatives, attribution, and downstream outcomes affect the Value
  position over time?
- Does an upstream analytical capability improve the quality or efficiency of PAIM work compared
  with constructing a Value input directly from fuller evidence?
- What information is lost, duplicated, or distorted at the analytical-to-management interface?

No authoritative AIVM research source is included in the current PAIM worktree for this task.
Exact AIVM propositions and additional AIVM-specific questions are therefore reserved as a
placeholder for later source-grounded expansion; they are not reconstructed from memory here.

### 5.3 Other adjacent research

AI risk management, benefits realization, adaptive management, organizational governance,
evaluation, assurance, and implementation research may motivate comparisons about risk discovery,
benefit persistence, staged action, institutional roles, evidence quality, and organizational
outcomes. A later source-grounded review may select specific propositions. This agenda does not
attempt a literature review or imply that a named tradition is validated by PAIM.

## 6. Emergent-use research and deliberate room for surprise

Some of the most useful research questions will not be identifiable before real use. Every pilot
or deployment study should reserve a documented channel for unanticipated observations and permit
new question families to emerge.

Candidate categories include:

- unexpected workarounds or shadow records;
- systematic misunderstanding of PAIM concepts;
- omitted management concepts or actors;
- controls that prove redundant, overdesigned, or easy to game;
- novel forms of coordination, accountability, or authority conflict;
- unexpected relationships among Value, Risk, Learning, and Decision;
- behavior changes caused by documentation, workflow, or interface design; and
- differences by organizational size, sector, consequence, maturity, power structure, or
  regulatory environment.

Researchers should distinguish a one-off procedural problem from a recurring behavior without
dismissing either prematurely. Emergent findings may justify revising PAIM, simplifying it,
changing a research construct, or rejecting an earlier proposition. Findings that do not fit RWR,
AIVM, or prior PAIM categories remain legitimate PAIM research contributions.

## 7. PAIM as research object and research instrument

PAIM can play two roles in a study, and confusing them can bias the design.

### 7.1 PAIM as research object

Here the study asks whether PAIM’s concepts, distinctions, workflows, and governance mechanisms
are useful, correct, proportionate, or understandable. PAIM is the intervention or object being
evaluated. Comparators might include ordinary practice, another structured approach, or a
simplified PAIM variant.

### 7.2 PAIM as research instrument

Here PAIM is used to preserve or observe Evidence, rationale, identity, authority, Decisions,
actions, and longitudinal history for another empirical question. Exact records may support
analysis of decision persistence, evidence use, organizational roles, or reconsideration.

PAIM must not be assumed to be a neutral instrument. The required instrumentation-effect question
is:

> **Does using PAIM itself change practitioner reasoning or decisions rather than merely recording
> reasoning that would otherwise have occurred?**

Study designs should address that question through suitable comparators, order controls,
qualitative observation, or other defensible methods. If PAIM changes what practitioners notice or
record, PAIM-generated data cannot be interpreted as an untouched view of prior practice.

## 8. Measurement discipline

PAIM records are not automatically research constructs. A stored field may be easy to count while
remaining a poor measure of the phenomenon a study claims to examine.

In particular:

- Trigger count is not responsiveness to material change;
- Evidence count is not Evidence quality;
- Risk finding count is not better Risk discovery;
- a changed Decision is not a better Decision;
- fewer steps are not better governance;
- more traceability is not a better organizational outcome; and
- completion is not proof that the intended effect occurred.

Each research construct needs a defensible operational definition independent of what PAIM happens
to store. Where possible, studies should combine record-derived measures with independent review,
practitioner explanation, observed behavior, and external outcomes.

### 8.1 Reasoning measures

Candidate measures include evidence requested, dependencies identified, alternatives considered,
uncertainty preserved, unsupported inferences made, rationale completeness, challenge quality,
and agreement or disagreement among independent reviewers. Coding schemes should be defined before
outcome inspection and should allow reasoning to become simpler as well as more elaborate.

### 8.2 Decision measures

Candidate measures include disposition, boundary specificity, decision reversibility, alignment
between stated rationale and selected action, authority completeness, sensitivity to new evidence,
and independent ratings of decision defensibility. A different or more restrictive Decision is not
automatically better.

### 8.3 Process and burden measures

Candidate measures include elapsed and active time, handoffs, duplicated work, training demand,
errors, recovery effort, unresolved conflicts, cognitive load, perceived clarity, bypass attempts,
and distribution of work among roles. Burden should be related to consequences and benefits rather
than reported as a context-free count.

### 8.4 Longitudinal measures

Candidate measures include persistence of rationale, time to material-change recognition,
Reassessment initiation and completion, confirmation versus successor behavior, preservation of
history, control and Evidence refresh, repeated gaps, and lost or duplicate concerns. These
measures require an explicit time horizon and independent materiality definitions.

### 8.5 Eventual real-world outcome measures

Candidate measures depend on the managed use and may include realized organizational or
stakeholder Value, adverse outcomes, control performance, reversibility, distributional effects,
resource use, and unintended consequences. Attribution will often be difficult. PAIM records can
support an account of context and reasoning, but they cannot establish causal outcome effects by
themselves.

## 9. A staged and falsifiable research progression

This is a possible starting sequence, not a mandatory program. Each stage has a stop or redirect
condition. A null, contradictory, or burden-heavy result is informative.

### Study 1: smallest reasoning experiment

Practitioners assess the same constructed AI-use case under ordinary governance practice and one
explicit alternative reasoning approach. RWR is a candidate because its paper already proposes
this comparison. PAIM should not be the intervention in the first RWR reasoning test: using PAIM
would confound the reasoning approach with PAIM’s instrumentation effect.

Observe at least evidence requested, dependencies identified, rationale, and disposition, plus
time and practitioner explanation. Randomized order, independent coding, or another suitable
control should address learning and carryover.

This study **could** establish whether the reasoning intervention changes observable
decision-relevant reasoning under the tested conditions. It **could not** establish better
decisions, real-world outcomes, general organizational effectiveness, or PAIM effectiveness.

If no meaningful reasoning difference appears, later RWR-focused work may stop or redirect rather
than escalating automatically.

### Study 2: PAIM operationalization and usability experiment

Only if justified, compare ordinary structured management with PAIM-supported management. Study
traceability, consistency, reconstructability, five-layer authority clarity, burden, reasoning,
and workarounds. A simplified PAIM condition may test whether every distinction is necessary.

This study **could** establish differences in observed reasoning, record quality, errors,
reconstruction, access/authority comprehension, and burden for the sampled tasks and participants.
It **could not** establish long-term Decision quality, organizational outcomes, causal safety or
Value improvement, or validity across sectors.

If PAIM adds burden without corresponding observable benefit, later work should simplify, narrow,
or stop rather than reinterpret burden as success.

### Study 3: longitudinal reconsideration experiment

After an initial Decision, introduce controlled new information at known times. Examine Learning,
Trigger promotion, Trigger Determination, Reassessment, interim operation, confirmation, successor
Decision, and historical reconstruction. Vary whether the new information affects Value, Risk,
authority, Configuration, alternatives, or several dimensions.

This study **could** establish how participants respond to change, whether history remains usable,
and whether PAIM affects persistence or reconsideration in the experimental setting. It **could
not** establish that a changed or confirmed Decision was objectively correct or that behavior
would persist in live organizations.

Results may redirect attention to a specific mechanism, such as Trigger Determination or authority,
without justifying a full-system field study.

### Later field or pilot work

Field work should occur only when earlier evidence justifies its cost, operational exposure, and
methodological complexity. It may study actual organizational burden, adoption, workarounds,
decision persistence, and eventual outcomes over time. This agenda does not design a full field
trial.

Field evidence **could** improve ecological validity and reveal institutional or sector variation.
Without suitable comparators and outcome definitions, it **could not** attribute observed outcomes
to PAIM or eliminate selection, implementation, and instrumentation effects.

## 10. Cross-study design considerations

Research should define the unit of analysis—person, team, Decision, Configuration, Case,
organization, or longitudinal episode—before measurement. Case consequence, novelty, maturity,
organizational size, and participant role may moderate effects and should not be treated as
background noise.

Constructed cases can support control and repeatability but do not establish live behavior. Aster
Vale is one constructed illustration and may be reused as a stimulus when appropriate; it is not
empirical evidence. Multiple cases are needed to avoid fitting conclusions to its particular
Value/Risk pattern.

Studies should anticipate learning, order, facilitation, documentation, and interface effects.
They should report facilitator intervention, training, failed attempts, workarounds, missing data,
and deviations rather than cleaning them out of the account. Qualitative evidence is particularly
important where the same recorded action can reflect different reasoning.

Falsification should be concrete. Before a study, researchers should state what evidence would
weaken the proposition, justify simplification, show unacceptable burden, or stop the next stage.
They should also state which outcomes remain outside the study’s reach.

## 11. Research principles to preserve

1. Point-in-time research conclusions may become inadequate as evidence and practice change.
2. Prior conclusions are revisable.
3. Contradiction of earlier work is evidence, not failure.
4. Findings must be allowed to weaken, narrow, or simplify PAIM.
5. Burden is an empirical outcome, not automatically a defect or virtue.
6. Different Decisions are not automatically better Decisions.
7. Traceability is not outcome quality.
8. Unexpected findings deserve investigation even when they do not fit prior theory.
9. No study should be optimized for consistency with published work.
10. Null results and stopped research sequences should be reported.
11. PAIM-generated data should be interpreted in light of PAIM’s instrumentation effect.
12. Scope, population, time, and uncertainty should remain visible in every conclusion.

## 12. Boundaries and non-goals

This agenda does not:

- change PAIM v0.1 product semantics, code, schema, runtime, or release claim;
- revise the RWR paper or claim that PAIM implements or validates RWR;
- claim that RWR validates PAIM;
- design features or announce a v0.2 scope;
- design IRR-009 Observation semantics or IRR-014 operating-state relation semantics;
- treat Aster Vale as empirical evidence;
- serve as a literature review or complete experimental protocol;
- make PAIM records self-validating research measures; or
- require that every listed question or study be pursued.

Research authority is distinct from product and design authority. An empirical finding can justify
a proposal to revise PAIM, but it does not silently amend the governing specifications. Conversely,
a current PAIM contract does not dictate what research must conclude.

## 13. Maintaining the agenda

This agenda should evolve through explicit, source-grounded revisions. Future updates should
record which questions were studied, which were reframed or retired, what unexpected questions
appeared, and why later work was continued, redirected, simplified, or stopped.

A useful agenda is not one that accumulates the most studies. It is one that makes uncertainty
testable, permits surprise, distinguishes management behavior from stored data, and remains willing
to change PAIM when evidence warrants it.
