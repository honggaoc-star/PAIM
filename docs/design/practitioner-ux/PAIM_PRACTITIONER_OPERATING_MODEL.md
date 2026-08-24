# PAIM Practitioner Operating Model

## Status and decision boundary

This document is the product operating-model checkpoint required by Issue #123. It is a design
proposal for owner review, not a system specification, domain change, deployment claim, or
authorization to implement further UI work. The contracts under [`docs/system/`](../../system/)
remain authoritative.

Further practitioner-UI redesign is paused until this package is accepted and any required
normative changes are separately approved.

The assessment basis includes the governing
[Roles and Accountability Specification](../../system/specifications/PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md),
[Integrity Specification](../../system/specifications/PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md),
current [M1 browser architecture](../../engineering/PAIM_UI_M1_IMPLEMENTATION_ARCHITECTURE_DECISION_v0.1.md),
and [local operational boundary](../../operations/PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md).

## Product principles

> The engineering model must be rigorous enough to protect the management process. The
> practitioner experience should be as simple as that rigor allows.

> PAIM should expose the minimum information and interaction necessary for a practitioner to
> perform legitimate management work. Engineering machinery remains underneath unless revealing
> it is necessary to understand or authorize a consequential action.

These principles mean:

- do not ask for information PAIM already legitimately knows;
- do not ask a practitioner to perform a safe system operation manually;
- do not expose an internal concept merely because persistence or validation needs it;
- preserve exact identity, version, scope, effective and knowledge time, conflict, access,
  accountability, authority, and append-only history underneath; and
- remove text entirely when it adds no legitimate understanding, judgment, or consequence.

## Intended organizational setting

PAIM is optimized first for a small-to-medium organization. A Case may involve one to five people,
one participant may perform several functions, and specialist or independent review may be added
only where the situation or organizational policy warrants it. PAIM must also scale upward without
making enterprise staffing patterns mandatory.

PAIM therefore assumes neither thirteen distinct practitioners nor one all-powerful user. It makes
function, responsibility, and authority explicit while allowing the same attributable participant
to hold multiple legitimate assignments.

## What `local` means

`Local` should mean **deployed under the organization's control**, not inherently single-user.
Control includes the authoritative data location, identity administration, network exposure,
backup, restore, and operational policy.

| Mode | Product meaning | Current support | Direction |
|---|---|---|---|
| Single-workstation local | One organization-controlled installation and database. Different attributable practitioners may use the workstation at different times. | Supported only as one loopback browser process/worker with process-local sessions and one managed write interface. Sequential practitioner use is compatible with the current architecture. | Retain as the smallest supported deployment. Add participant/work handoffs only after their domain contract exists. |
| Organization-local multi-practitioner | One organization-controlled server/private environment. Multiple practitioners use the same authoritative Cases through browsers, potentially concurrently. | Not supported. Non-loopback access, HTTPS, durable sessions, remote identity, multi-worker operation, and concurrent use are outside M1. | Recommended product direction after the operating model and work/responsibility contract are accepted. It is a separate deployment increment, not a UI toggle. |

Single-workstation local assumes loopback networking, process-local sessions, SQLite durability,
operator-managed backup/restore, and application restart signing every user out. Organization-local
deployment will require HTTPS, explicit host/proxy policy, durable shared sessions, organization
identity lifecycle, availability objectives, tested contention behavior, backup/restore operations,
and a supported single-writer or transactional server boundary. SQLite may remain suitable for a
small deployment only after measured concurrency and recovery evidence; this checkpoint does not
select a future database.

Privacy is not implied by the word local. Both modes require access filtering, credential
protection, audit attribution, secure backup handling, and an explicit deployment boundary.

## Four distinct concepts

| Concept | Practitioner meaning | What it is not |
|---|---|---|
| Participant | An attributable person involved in a Case. | A permission, responsibility, or authority merely because the person can sign in. |
| Practical role | A broad, understandable relationship to the Case that helps people coordinate. | A complete list of every governed function or a source of automatic authority. |
| Responsibility | A specific piece of work, judgment, review, coordination, or implementation obligation in an exact context. | A job title, generic queue, software permission, or Decision Authority. |
| Authority | A separately established right to make or authorize a consequential act when the specifications require it. | Ownership of work, authorship, access, practical role, or seniority. |

The application must not use `role` as shorthand for all four. A participant may have several
practical roles and responsibilities. One responsibility may move between participants through an
explicit, historical handoff. Authority is evaluated independently at the consequential act.

## Minimal standing Case role model

PAIM should need only two primary standing Case roles, plus one optional role:

1. **Case Coordinator** — keeps the Case coherent, routes work, and makes missing responsibility
   visible. `Case Owner` may remain the formal trace label during transition.
2. **Assessor** — performs one or more explicitly assigned analytical or information-review
   responsibilities. Value and Risk remain separate responsibilities and records, not mandatory
   separate job roles.
3. **Reviewer** — optional practical role only where independent or second-line review is actually
   needed.

Subject-matter expertise is normally a participant attribute or assigned responsibility, not a
standing Case role. The person expected or authorized to decide is presented through the separate
Decision Authority relationship, not a `Decision Maker` role. Post-decision actions and
Interventions are assigned directly as specific responsibilities and may have different responsible
participants; there is no broad `Implementation Owner` Case role. Technical administration remains
an organization/application function outside Case staffing.

Fine-grained functions such as Value, Risk, information Applicability, Fitness, Selection,
Authority-question resolution, Trigger Determination, Reassessment, intervention execution, and
Completion Acceptance remain rigorously distinguished obligations underneath, but appear as
specific work rather than permanent organizational personas.

This minimal standing-role model is a proposed practitioner model. It does not rename or retire
normative roles by itself; the required reconciliation is recorded in the
[Role Consolidation Map](PAIM_ROLE_CONSOLIDATION_MAP.md).

## Responsibility model

A responsibility answers: **who is accountable for this exact obligation in this exact context and
time?** It needs more precision than a practical role:

- obligation kind, such as assess Value, judge information applicability, determine a Trigger, or
  accept an Intervention Completion Result;
- exact Case and relevant Configuration/record Versions;
- purpose, use, or assessed scope where the governing contract requires it;
- responsible participant or genuinely governed mechanism;
- effective interval, assignment source, delegation/supersession, and current state; and
- vacancy/conflict rather than an inferred winner.

One participant may receive both Value and Risk responsibilities. PAIM still commits independent
Value and Risk Inputs, readiness, Fitness, Selection, provenance, and attribution. Staffing
consolidation must never become analytical-record consolidation.

The existing Role Assignment model cannot fully express this responsibility contract because its
primary discriminator is a free-form `role` plus one typed target; it has no first-class obligation
kind or exact purpose/use/assessed-scope discriminator. That gap must be resolved normatively before
ordinary responsibility assignment is implemented. `Applicability Owner` is an implementation
conservatism, not a proposed practical role.

## Case work model

PAIM needs a bounded Case-work concept, not a generic workflow engine. It should answer:

- what work is ready;
- what is waiting and on what exact prerequisite;
- who is responsible;
- what Case context travels with the work;
- what governed result legitimately completes it; and
- where the result returns next.

Some work can be derived from authoritative PAIM state. For example, a ready Value Input with one
missing exact Applicability relationship yields a visible prerequisite. Derivation is preferable
when it remains deterministic and does not need durable assignment, due date, request, or handoff
history. A durable Work Item is needed when PAIM must preserve a request, participant assignment,
cross-person handoff, due time, return relationship, cancellation, or coordination outcome.

A Work Item coordinates work; it never replaces Evidence, Applicability, Value/Risk Input,
Fitness, Selection, Authority, Decision, Intervention, or another substantive record. Completion
requires the exact governed result when the prerequisite requires one. Details are defined in the
[Case Work & Handoff Model](PAIM_CASE_WORK_AND_HANDOFF_MODEL.md).

## Work-centered communication and notifications

The authoritative object is the work and its governed result; communication is secondary. A
handoff carries what is needed, why, the Case/proposed use, relevant exact context, requester,
responsible participant, due time if legitimate, and the valid completion outcome. A short note may
clarify the request but cannot become the authoritative judgment.

Notifications are delivery and attention aids. `Your work` may show assigned ready or changed work,
but a notification never becomes Case state and deleting or failing to deliver one changes no
responsibility or governed result.

## Authority boundary

Assigning work does not grant authority. In particular:

- Case coordination does not create Decision Authority;
- an Assessor assignment does not authorize a Decision;
- a participant assigned an implementation action cannot self-accept completion unless separately
  accountable for that exact obligation;
- identifying who is expected to decide is not an Authorization Basis; and
- technical administration remains separate from every substantive act.

The UI should ask ordinary questions such as `Who will assess Risk?` or `Who is responsible for
this review?`, while the authoritative layer retains exact identities, Versions, targets,
effective intervals, and conflicts. Consequential confirmation must still explain the authority
basis when understanding it is necessary.

## Practitioner and engineering boundaries

The practitioner surface shows the situation, relevant information, responsibility, substantive
judgment, consequence, next action, unresolved condition, and management/operating state. User and
administrator guidance covers setup, participants, access, responsibility administration,
deployment, and backup/restore. Engineering documentation retains commands, selectors, Versions,
append-only persistence, internal composition, and security rationale. Authorized audit inspection
retains exact trace without making that trace the ordinary workflow.

Every proposed screen item must pass this test:

> If removing an item would not impair the practitioner's ability to understand the situation,
> make a legitimate judgment, or understand the consequence of an action, why is it on the screen?

## Decisions and gates

This checkpoint recommends:

- organization-controlled local as the long-term product meaning, with current support honestly
  limited to the single-workstation topology;
- two primary standing Case roles (Case Coordinator and Assessor), optional Reviewer only where
  needed, and rigorous responsibility separation;
- a bounded, context-carrying Case Work concept where coordination must be durable;
- work-centered handoffs and secondary notifications; and
- a normative responsibility/work design before any Role Assignment or multi-practitioner UI.

It does not authorize new records, migrations, networking, screens, or specification edits. The
[Architecture Feasibility & Gap Assessment](PAIM_PRACTITIONER_OPERATING_MODEL_ARCHITECTURE_GAP_ASSESSMENT.md)
defines the separate gates.
