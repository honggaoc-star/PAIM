# Provisional Practitioner Vocabulary for PAIM Reference Cases

## Status and design rule

This is provisional exercise vocabulary, not a replacement for the PAIM specifications and not a
final product glossary. It should be revised from practitioner evidence.

The Harborlight Scenario-A checkpoint produced a revised audience/task classification in
[Scenario-A Provisional Practitioner Vocabulary Classification](../design/practitioner-ux/PAIM_SCENARIO_A_VOCABULARY_CLASSIFICATION.md).
That refinement remains provisional and does not rename domain or API contracts.

**PAIM enforces engineering invariants; practitioners should not have to operate in engineering
terminology.** Exact identity and history still matter, but the interface should disclose their
technical representation only when it helps the task, audit, or troubleshooting need at hand.

## 1. Practitioner-facing management concepts

These concepts belong in ordinary management work, expressed in plain language with contextual help.

| Preferred term | Practitioner meaning |
|---|---|
| Case | The continuing management concern being governed. |
| Configuration | The exact version of the activity, system, workflow, people, controls, and scope under consideration. |
| Evidence | A preserved source that may inform a management question. |
| Applicability | The recorded judgment about whether that Evidence bears on this exact question and context. |
| Authority | A substantive source that permits an Actor to make a governed choice within an exact scope. |
| Authority Gap | A material question for which sufficient authority or authoritative support is not established. |
| Value assessment | An analysis of the benefits, purposes, costs, and alternatives relevant to the proposed action. |
| Risk assessment | An independent analysis of uncertainty, harm, exposure, controls, and acceptability. |
| Selected assessment | The assessment explicitly chosen as the current basis for the action; existence alone does not make an assessment current. |
| Integration | A practitioner's explicit account of how the selected Value and Risk assessments bear on the proposal. It is not automated synthesis. |
| Boundary | The exact limits, conditions, controls, population, and duration within which an action would operate. |
| Decision proposal | An action submitted for review; it is not yet authorized. |
| Authorized Decision | The Decision made effective by an authorized Actor against the exact reviewed basis. |
| Reassessment | A governed reconsideration after relevant change or new evidence. |
| Next owning action | The domain action that can legitimately advance the concern, including the accountable role and authority still required. |

Where a shorter label is safe, the interface may use phrases such as “current Value basis,” “current
Risk basis,” “proposed action,” “operating limits,” and “who can act.” It must not simplify away the
underlying distinction.

## 2. Governance and audit concepts under progressive disclosure

These concepts should be available in history, provenance, review, and explanation views without
dominating the ordinary workflow.

- exact source and provenance;
- governing Configuration at the time of an action;
- effective time, recorded time, and knowledge-time basis;
- prior and successor versions;
- supersession, withdrawal, and continuing historical status;
- exact Evidence, assessment, Integration, Boundary, and Authority basis reviewed;
- accountable Actor and applicable role assignment;
- Authority source, scope, and any Authority Gap;
- access-filtering context and excluded protected content; and
- why an item is current, historical, blocked, unresolved, or ineligible.

A practitioner should be able to answer “what did we know, what applied, who acted, and on what
basis?” without first learning database or API terms.

## 3. Engineering-only terms

These terms are necessary for implementation, diagnostics, and exact machine contracts, but should
not be the primary language of practitioner screens or exercises:

- Record ID, Version ID, UUID, record family, and version relationship row;
- exact-Version foreign-key binding;
- command gateway, adapter, projection, persistence session, and transaction;
- schema, constraint, trigger, index, migration, and foreign-key enforcement;
- idempotency key, replay identifier, payload checksum, and serialization form; and
- enum member name, internal status code, and authorization resolver output.

When one of these must be shown, pair it with the management object and purpose—for example, “exact
historical Value assessment” with a copyable Version ID in provenance details.

## Candidate wording refinements

| Avoid as the primary UI label | Prefer in practitioner context |
|---|---|
| `record_id` / `version_id` | Record / exact version, shown in provenance details |
| `commit_lane_fitness` | Confirm whether this assessment is fit for this use |
| `commit_integration` | Record how the current Value and Risk bases inform the proposal |
| `authorization_basis_version_id` | Authority basis reviewed for this authorization |
| `local practitioner workspace` | PAIM workspace, unless local deployment context materially matters |
| `current` without explanation | Current because it is the exact established selection for this Configuration and purpose |
| `blocked` without relation | Cannot proceed: state the missing evidence, accountability, authority, or prerequisite |

## Evidence questions for exercises

Record the participant's own language and do not translate it into these proposed terms before
analysis:

1. Which labels were immediately understandable?
2. Which labels concealed the difference between access, accountability, and authority?
3. Could the participant distinguish a record that exists from a basis selected for current use?
4. Could the participant explain Integration without describing scoring or automated synthesis?
5. Did exact history remain trustworthy when technical identifiers were progressively disclosed?
6. Which engineering terms were needed for audit or recovery, and which leaked into ordinary work?

Changes suggested by these observations remain proposals until separately reviewed against the PAIM
implementation contracts.
