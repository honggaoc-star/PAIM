# PAIM Next UI Redesign Design Brief

## Gate and purpose

This brief frames the next practitioner-centered redesign after owner acceptance of the
[Practitioner Operating Model](PAIM_PRACTITIONER_OPERATING_MODEL.md). It is not authorization to
implement UX-4, M1D, responsibility administration, Case Work, multi-user deployment, or any screen.

The existing [task-oriented information architecture](PAIM_TASK_ORIENTED_INFORMATION_ARCHITECTURE.md)
and [practitioner-language standard](PAIM_PRACTITIONER_LANGUAGE_STANDARD.md) remain inputs rather
than predetermined navigation or copy.

The redesign must be evaluated after the required normative Responsibility/Work decisions. It must
not use UI state to fill architecture gaps.

## Experience outcome

A participant opening a Case should understand within the ordinary workspace:

- what is being considered and the current management position;
- what legitimate work they can do now;
- what is waiting, why, and on whom;
- which people are involved and for what broad purpose;
- which information, assessment, Decision, and operating conditions matter; and
- the consequence and return path of the action they are about to take.

The participant should not need to learn PAIM's record taxonomy or reconstruct known context.

## Information-architecture alternatives

The current navigation is:

`Overview | Proposal setup | What we know | Value & Risk | Management judgment | Source & history`

It is useful for domain-area inspection but weak for cross-participant coordination. Three
conceptual alternatives should be prototyped before selection:

### Alternative A — work-first Case

`Where things stand | Your work | Waiting on others | Information | Assessment | Decision | History`

Strength: immediate orientation and coordination. Risk: `Your work` cannot be truthful until
Responsibility/Work is authoritative and access-filtered.

### Alternative B — status-first with embedded work

`Where things stand | People & work | Information | Assessment | Decision | Implementation | History`

Strength: fewer top-level items and a coherent team view. Risk: people and work can become a dense
administration screen rather than the participant's selected task.

### Alternative C — retained domain areas plus work hub

`Overview & work | Proposal | Information | Assessment | Decision | Implementation | History`

Strength: evolutionary path from the current UI. Risk: old ontology-first habits may survive under
new labels.

No label is predetermined. Prototype evaluation should use the Harborlight scenarios and ask which
structure lets participants find status, their work, waits, context, and consequence with least
translation.

## Proposed Case opening composition

Regardless of navigation, the opening view should test these concepts:

1. **Where things stand** — plain current position derived from authoritative state, without a
   universal Case status or progress percentage.
2. **Your work** — exact assigned ready/waiting work plus genuinely available independent work,
   separated and unranked.
3. **Waiting on others** — exact work, responsible participant/vacancy/conflict, and prerequisite;
   never a notification count without meaning.
4. **People involved** — participant names, compact practical relationships, and current relevant
   responsibilities; no implication that access or labels create authority.
5. **Unresolved conditions** — missing information, responsibility, authority, conflict, stale
   context, or other explicit blockers, each with a legitimate resolution route.

## Selected-work surface

Choosing work should open a focused surface that carries:

- Case and concrete proposed use;
- the exact setup and substantive question in ordinary language;
- only relevant visible information/authority/assessment context;
- requester and responsible participant where a handoff exists;
- prerequisites and independent related work without ranking;
- fields for the genuine practitioner judgment only;
- a review-before-commit consequence; and
- the return destination after the governed result is recorded.

The practitioner should not reselect known Record/Version context. PAIM may require reconfirmation
only when the practitioner must make a genuine choice or authoritative context has changed.

## Responsibility interaction concept

Where a legitimate participant is authorized to assign work, use ordinary actions such as:

- `Assign this work`
- `Who will assess Value?`
- `Who will assess Risk?`
- `Who is responsible for this review?`
- `Who will implement this action?`

The UI may list only eligible participants/responsibilities returned by the future authoritative
contract. It must not offer a free-text role/mechanism, infer the signed-in participant, or choose
among conflicts. Decision work separately states whether Decision Authority is established.

Until that contract exists, the correct UI is an explicit vacancy/conflict explanation and no
assignment control.

## Practitioner/administrator/technical separation

### Ordinary practitioner surface

Show situation, work, relevant context, judgment, consequence, next action, unresolved condition,
and current decision/operating position. Suppress raw IDs, internal statuses, command names,
compatibility keys, selector reasons, and routine satisfied guards.

### Participant and administrator guidance

Provide separate setup for participant identity/access, organization configuration, responsibility
administration, backup/restore, deployment, and support. Administration never creates substantive
authority.

### Governance history and authorized inspection

Expose readable source/history/accountability/authority basis when needed. Exact technical trace is
a separately authorized inspection mode, not an expandable block on every ordinary card.

### Engineering documentation

Keep persistence, Version identity, algorithms, command contracts, schema, security mechanisms,
and architecture rationale in technical documents and tests.

## The minimum-content test

For every item, ask:

> If removing this would not impair understanding of the situation, a legitimate judgment, or the
> consequence of an action, why is it on the screen?

Apply the test especially to:

- repeated Configuration/currentness text;
- raw Record/Version identity;
- internal function names;
- access/accountability/authority layers that are already satisfied and irrelevant to the current
  action;
- counts with no actionable meaning;
- generic help text; and
- technical explanation exposed before a failure or consequential confirmation.

The correct replacement may be nothing.

## Semantic constraints

The redesign must preserve:

- independent Value and Risk records, stages, Fitness, Selection, attribution, and history even
  when one participant performs both responsibilities;
- exact Configuration/record/version/currentness at review and commit;
- access before aggregation/disclosure;
- responsibility vacancy/conflict with no inferred winner;
- separate Decision Authority and complete Authorization Basis;
- one-prerequisite completion without silent completion of another;
- append-only work, responsibility, and governed-result history;
- notification non-authority; and
- stale/superseded/cancelled work that never silently retargets.

No universal score, priority, recommendation, workflow percentage, automatic owner, automatic
next-step ranking, or generic `mark resolved` is permitted.

## Prototype and owner-review plan

Before implementation, create low-cost prototypes for the three IA alternatives using only
constructed/non-authoritative presentation data. Evaluate them with:

- one-person Harborlight staffing;
- small-team contextual security handoff;
- the current Applicability responsibility vacancy;
- same participant assigned Value and Risk; and
- responsibility and authority conflicts.

Review questions should measure whether participants can identify status, their work, waits,
responsibility, separate authority, relevant context, legitimate completion, and return path without
corrective instruction. Prototype content must not mutate the live Case or imply the architecture
already supports the interaction.

## Implementation entry criteria

No redesign implementation should begin until:

1. owner accepts the operating model and selects the next bounded question;
2. required Responsibility/Work normative changes are accepted;
3. domain, persistence, access, history, and migration contracts are implemented where required;
4. the target deployment topology is explicit;
5. the chosen IA passes Harborlight design review; and
6. a bounded issue defines production capabilities, hard semantic oracles, browser checks, and
   explicit exclusions.

UX-4, M1D, organization-local deployment, external notification integrations, and generic
messaging remain separate decisions.
