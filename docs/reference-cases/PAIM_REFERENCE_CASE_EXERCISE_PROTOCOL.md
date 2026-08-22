# PAIM Reference Case Exercise Protocol

## Purpose and claim boundary

This protocol supports repeatable, framework-revealing exercises using the fictional Harborlight
case. It is not an empirical study result, a product validation claim, or a script for obtaining a
favorable Decision. The protocol may reveal that PAIM is confusing, duplicative, or unnecessary for
a scenario.

Use these inputs together:

- [PAIM Small-Business Lending Reference Case](PAIM_SMALL_BUSINESS_LENDING_CASE.md);
- [Multi-Stage Scenarios](PAIM_SMALL_BUSINESS_LENDING_SCENARIOS.md);
- [Framework-Revealing Map](PAIM_SMALL_BUSINESS_LENDING_FRAMEWORK_MAP.md); and
- [Provisional Practitioner Vocabulary](PAIM_REFERENCE_CASE_PRACTITIONER_VOCABULARY.md).

## Roles

- **Practitioner:** performs the management work and states judgments in their own words.
- **Facilitator:** reveals only the facts scheduled for the current scenario and provides procedural
  help without recommending an outcome.
- **Recorder:** captures actions, questions, failures, and exact observations without inference.
- **Optional comparator practitioner:** handles the same scenario using the organization's ordinary
  governance method, if a separately approved comparative design is being run.

One person may fill facilitator and recorder roles in an exploratory exercise, but that limitation
must be recorded.

## Four evidence categories

Keep these categories separate in every exercise record:

1. **Supplied facts:** the fictional case materials and scenario events disclosed by the facilitator.
2. **Practitioner judgments:** Applicability, Value, Risk, selection, Integration, Boundary, proposed
   action, authority interpretation, and other conclusions made by the participant.
3. **Hard constraints:** PAIM contract properties that the exercise must not violate, such as Value/Risk
   independence, exact Configuration binding, historical preservation, and proposal/authorization
   separation.
4. **Observed behavior:** what the practitioner and system actually did, including friction, confusion,
   corrections, unsupported inferences, time, and abandoned steps.

Do not rewrite a practitioner judgment as a supplied fact, or a system invariant as proof that the
framework helped the practitioner.

## Preparation

1. Record exercise identifier, date, participant role/background, facilitator, recorder, PAIM version
   or commit, interface, and any ordinary-governance comparator.
2. Provide the case status, organization/activity, roles, C0/C1 definitions, initial packet, and claim
   boundaries. Do not reveal later scenario facts.
3. State that there is no preferred Decision and that participants may conclude PAIM adds no value.
4. Confirm that only fictional policy and authority materials govern the exercise; no real loan or
   legal decision is being made.
5. Start from a clean exercise state whose provenance can be reconstructed. Record any fixture or
   facilitator-created state separately from practitioner actions.

## Bounded exercise sequence

Run each scenario as a separate checkpoint. A facilitator may stop after any checkpoint; later stages
must not be used to repair or reinterpret earlier observations.

### Checkpoint 1 — baseline reconstruction

Ask the practitioner to identify the continuing Case, exact current Configuration, proposed action,
available Evidence, unresolved questions, roles, authority source, and feasible alternatives. Capture
what required explanation.

### Checkpoints 2–7 — Scenarios A through F

For each scenario:

1. reveal only its new supplied facts and proposed decision context;
2. ask the practitioner which sources are Applicable to which exact question and Configuration;
3. obtain independent Value and Risk work without suggesting that they must converge;
4. ask which assessment, if any, should be selected in each lane and why;
5. if an action is supportable, ask the practitioner to record Integration, Boundary, and a proposal;
6. require separate accountability and substantive-authority checks before authorization;
7. capture the action actually taken, including defer, narrow, decline, suspend, use ordinary change
   control, or request more evidence; and
8. stop for the checkpoint questions below before revealing the next scenario.

For Scenario C, record whether the practitioner can find the correct Evidence/Trigger/Reassessment
path without treating the event or Trigger as a Decision. For Scenario D, require explicit C1/C2
Applicability and current-basis judgments. For Scenario E, prohibit automated ranking. For Scenario F,
do not force a PAIM lifecycle merely to complete the exercise.

## Checkpoint questions

Record answers verbatim where practical:

1. What objective did you try to accomplish, and did you accomplish it?
2. What supplied fact most affected your judgment?
3. Which PAIM distinction clarified the management problem?
4. Which distinction or step was confusing, duplicative, or unnecessary?
5. Could you identify the exact current basis, next owning action, accountable role, and substantive
   authority without undisclosed guidance?
6. Did PAIM appear to infer Applicability, synthesis, priority, ranking, equivalence, authority, or a
   Decision that you had not established?
7. Could you reconstruct the prior Configuration, Evidence, selections, Boundary, and Decision after
   later events?
8. Would ordinary governance have produced a credible result with less effort? What, if anything,
   would have been lost?
9. Did the scenario expose a possible semantic defect, operational/security defect,
   usability/documentation defect, research question, or no finding? State the observation before any
   classification.

## Hard-oracle checks

The recorder verifies these separately from practitioner opinion:

- Value and Risk inputs and selections remain independently identified.
- Later evidence and Configurations do not rewrite prior records or authorized Decisions.
- An exact Configuration and its current selected bases support any Integration, Boundary, proposal,
  and authorization presented as current.
- Software access does not establish accountability or substantive authority.
- Evidence is not treated as Applicable solely through shared labels, proximity, or semantic
  similarity.
- Proposal is not authorization; Boundary is not Decision; Trigger is not Decision.
- Alternatives and operating states are not automatically scored, ranked, or reduced to a strongest
  value.
- Scenario F can end with ordinary change control and no fabricated PAIM action.

If a hard oracle fails, preserve the exact state and stop the affected pathway. Do not silently repair
the result or coach around it.

## Exercise record

Each checkpoint record should contain:

- exact supplied-fact identifiers and disclosure time;
- practitioner actions and stated reasoning;
- any facilitator prompt or correction;
- relevant current and historical object identities under progressive disclosure;
- hard-oracle results;
- elapsed time and interruptions;
- practitioner answers;
- the unclassified observation, followed by any later independently reviewed classification; and
- the stop point and whether subsequent work was authorized.

## Analysis and reporting

Analyze favorable, adverse, and low-value observations together. Separate conceptual clarity from
interface usability and from conformance to hard constraints. Report missing evidence and abandoned
paths, not only completed pathways.

An exercise may generate hypotheses for the
[PAIM Empirical Research Agenda](../research/PAIM_EMPIRICAL_RESEARCH_AGENDA_v0.1.md), but it does not
itself establish causal effects, comparative superiority, practitioner effectiveness, or empirical
validation. Any formal study, product change, or semantic change requires separate design and review.
