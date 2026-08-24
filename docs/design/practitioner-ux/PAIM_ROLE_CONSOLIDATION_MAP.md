# PAIM Role Consolidation Map

## Purpose and status

This map evaluates the current named roles/functions against the proposed small-to-medium-
organization [Practitioner Operating Model](PAIM_PRACTITIONER_OPERATING_MODEL.md). It is a design
recommendation, not an amendment to the
[Roles and Accountability Specification](../../system/specifications/PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md).

The governing direction is:

> Distinguish responsibilities rigorously; consolidate roles aggressively.

`Practical role` below means ordinary Case-facing vocabulary. `Responsibility` means an exact
governed obligation. `Authority` remains separately established.

## Consolidation map

| Current named role/function | Proposed treatment | Practitioner presentation | Rationale and safeguards |
|---|---|---|---|
| Case Owner | Consolidate into practical role | **Case Coordinator** (formal history may retain Case Owner) | Coordinates the Case and routes missing work. Does not gain analytical conclusions, completion acceptance, or Decision Authority. |
| Value Evaluator | Convert to assignable responsibility under Assessor | **Assess Value** | Value remains an independent record/judgment. It need not be a standing organizational role or different person from Risk. |
| Risk Evaluator | Convert to assignable responsibility under Assessor | **Assess Risk and controls** | Risk remains independent and separately attributable. No shared score, overwrite, or combined acceptance. |
| Subject-Matter Contributor | Participant attribute plus contextual responsibility | **Provide security/legal/operations/etc. input** | Expertise is needed for particular work, not necessarily as a permanent Case persona. Contribution does not decide Applicability or authorize action. |
| Decision Authority | Preserve as authority concept | **Decision Maker** only as orientation; show `authority established/not established/conflicting` at the act | The participant label never substitutes for the exact Authorization Basis. Committee/delegated authority remains possible. |
| Intervention Owner | Consolidate into practical role | **Implementation Owner** for an exact Intervention | Implementation does not change the Decision or establish Completion Acceptance. Multiple interventions may have different owners. |
| Intervention Completion Acceptor | Preserve as exact responsibility | **Review whether this implementation result satisfies the requirement** | Separate from implementation authorship/ownership. Same participant is allowed only through independently established accountability. |
| Evidence Owner | Usually convert to responsibility; retain source stewardship only where useful | **Collect/maintain this information** | Ownership does not determine Applicability, Fitness, Value, Risk, or authority. Avoid presenting every evidence producer as a standing Case role. |
| Authority Owner | Convert to responsibility, optionally under Reviewer/specialist participation | **Resolve or maintain this requirement/authority question** | Does not create Decision Authority. Exact authority source and scope remain governed. |
| Reviewer/Auditor | Optional practical role | **Reviewer** | Appropriate for independent/second-line review. Review findings do not silently mutate authoritative records. |
| System Administrator | Preserve as technical role outside ordinary Case staffing | **Administrator** | Manages access, continuity, and support. Technical privilege never grants substantive responsibility or authority. |
| Integration Facilitator | Convert to Case coordination responsibility | **Coordinate Value/Risk integration** | The work may be done by the Case Coordinator or an Assessor. It does not create a Decision or Decision Authority. |
| Trigger Determiner | Convert to exact responsibility | **Decide whether this occurrence requires reassessment** | Source authorship, severity, ownership, notification, and software access do not satisfy accountability. |
| Reassessment Owner | Convert to exact responsibility, often coordinated by Case Coordinator or Assessor | **Lead this reassessment** | Owns one exact Reassessment and Trigger Set; does not create Interim Disposition or Decision Authority. |
| Reassessment Coordination Authority | Preserve as exact coordination responsibility; avoid `Authority` in ordinary task copy | **Resolve how these reassessments coexist/continue** | The formal function remains separately accountable. It cannot merge history, select by recency, or create Decision Authority. Normative naming may need revision to avoid confusing responsibility with substantive authority. |
| Shared Dependency Determiner | Convert to exact portfolio responsibility | **Decide whether these exact dependencies are the same governed dependency** | Exact Candidate Set and determination remain authoritative. Similarity, labels, ownership, or dashboard grouping do not establish equivalence. |
| Shared Dependency Owner | Optional coordination responsibility if later established | **Coordinate this shared dependency** | Never transfers Case authority, Applicability, satisfaction, outcome, or closure. |
| Learning Item owner | Convert to exact responsibility | **Obtain or maintain this learning evidence** | Result delivery does not decide whether a Decision changes. |
| Configuration owner/designated owner | Usually Case coordination responsibility | **Maintain this assessment setup** | Must not collapse setup currentness, Decision authorization, or operating state. |
| `Applicability Owner` implementation label | Retire as practitioner role; do not normalize it into the operating model | **Who is responsible for this information judgment?** | UX-3B uses the label conservatively because the current resolver lacks an obligation discriminator. The future model must resolve an exact Applicability responsibility across Evidence, target, purpose, assessed scope, and time. |

## Proposed practical role set

The ordinary participant directory should need no more than:

| Practical role | Broad relationship | Typical responsibilities that may be assigned separately |
|---|---|---|
| Case Coordinator | Coordinates one Case | maintain Case/setup, request work, route prerequisites, coordinate integration, prevent orphaned work |
| Assessor | Performs analytical or information work | Value, Risk, information Applicability, Fitness, Selection, Trigger Determination, Reassessment analysis |
| Decision Maker | Expected participant in a decision act | propose or authorize only where the exact governing responsibility/authority separately permits it |
| Implementation Owner | Performs approved implementation | Intervention planning/execution/result reporting |
| Reviewer | Optional independent review | completion acceptance, process review, authority review, exception review where assigned |
| Administrator | Technical operation | participants/access, configuration, backup/restore, availability |

These are not permission bundles and do not imply universal separation. The same participant may be
Case Coordinator and Assessor, or may assess both Value and Risk. PAIM must show that combination
without making the person impersonate different users.

## What must remain separate underneath

Consolidated practitioner vocabulary must not collapse:

- Value Input, readiness, Fitness, and Selection from the corresponding Risk records;
- Evidence production from Applicability;
- analytical responsibility from Decision Authority;
- Intervention implementation from Completion Acceptance;
- Trigger Determination from Reassessment ownership and coordination;
- Case coordination from shared-dependency equivalence; or
- administrator permission from any substantive act.

## Existing Role Assignment fit

The current Role Assignment carries an actor, free-form role, one typed target, Case context where
applicable, `accountable`, compatibility key, delegation relationship, effective interval, and
append-only Version history. It supports exact currentness, delegation, vacancy, and conflict for a
known role/target pair.

It does **not** cleanly represent the proposed model because it lacks:

- a distinction between practical role and granular responsibility;
- a first-class obligation type;
- an obligation identity to which work and result can bind;
- purpose, use, assessed-scope, and exact multi-record context discriminators;
- requester, assignee, due/return/completion relationships; and
- a durable Work Item or handoff identity.

Its `compatibility_key` is not a substitute for a normative obligation model. A free-form `role`
such as `Applicability Owner` cannot safely encode the exact Evidence/target/purpose/scope context.

## Required normative decisions before implementation

Design authority should decide, in separate specification work:

1. whether practical role is authoritative Case metadata, a derived directory label, or only
   presentation;
2. the authoritative Responsibility identity, Version, obligation taxonomy, context, effective
   interval, assignment/delegation/supersession, vacancy, and conflict rules;
3. which existing named functions remain normative obligation kinds rather than roles;
4. how one responsibility cites several exact targets without violating the current one-typed-
   target Role Assignment rule;
5. when completion of a Work Item requires a governed result and when an explicit unresolved
   coordination result is legitimate;
6. how Decision Authority and other true authority concepts relate to, but remain distinct from,
   responsibility; and
7. migration and historical interpretation of existing Role Assignments without rewriting them.

Until those decisions are accepted, the current normative roles and assignments remain controlling,
and further responsibility-assignment UI must not be implemented.
