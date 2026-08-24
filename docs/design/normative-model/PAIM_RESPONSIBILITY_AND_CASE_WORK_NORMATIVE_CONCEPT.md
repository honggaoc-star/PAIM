# PAIM Responsibility & Case Work Normative Concept

## Purpose and current-contract boundary

This document proposes the prospective normative distinction between Participant, practical Role,
Responsibility, Authority, derived work, and durable Case Work. Current
[Roles and Accountability](../../system/specifications/PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md)
and [Integrity](../../system/specifications/PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md)
specifications remain controlling until separately revised.

## Four concepts, no shortcuts

| Concept | Target meaning | Never means |
|---|---|---|
| Participant | Existing PAIM Actor with an exact Case relationship or history | access alone, employee directory membership, or authority |
| Practical Role | Broad Case orientation: Case Coordinator, Assessor, optional Reviewer | permission bundle, granular obligation, or substantive authority |
| Responsibility | Who is accountable for one exact obligation, context, and time | job title, task display, authorship, access, or Decision Authority |
| Authority | Separately established right to perform a consequential governed act | Responsibility, practical role, seniority, or software permission |

One Actor may occupy several practical roles and Responsibilities. Every obligation and substantive
record remains independently attributable.

## Participant and practical-role treatment

The target does not add a separate Participant record. Case participation is an access-filtered
read composition from exact current or historical:

- practical-role relationships;
- Responsibilities;
- Work requests or assignments;
- substantive PAIM acts; and
- Decision or other authority relationships.

Software access and visibility alone are excluded. If an organization needs to state that a person
is broadly involved before assigning exact work, it establishes a **Case Practical Role
Relationship** containing stable identity, immutable Version, exact Case, Actor, one controlled
role value (`CASE_COORDINATOR`, `ASSESSOR`, or `REVIEWER`), effective interval, source/assigner,
recorded time, and predecessor/supersession/withdrawal history.

This relationship is orientation metadata. Case Coordinator does not gain assignment power,
Assessor does not gain every analytical Responsibility, and Reviewer does not gain mutation or
acceptance authority. Any right to assign Responsibility uses a separate assignment basis.

## Responsibility identity

A Responsibility is a stable obligation identity with immutable Versions. Its semantic identity is
the obligation, not the assignee. A Version preserves:

- Responsibility ID and Version ID;
- controlled obligation kind;
- exact owning Case;
- exact context-basis set, with typed roles for every relevant Record Version;
- purpose, bounded use, assessed scope, or obligation discriminator where required;
- required governed-result family and completion condition where applicable;
- responsible Actor or exact governed organizational mechanism;
- assignment source and exact **Responsibility Assignment Basis**;
- effective interval and recorded time;
- predecessor/successor, reassignment, delegation, supersession, withdrawal, and reason;
- status needed for prospective eligibility; and
- exact links to Work and governed results where applicable.

The context set may contain multiple exact Versions because an information Applicability
Responsibility can require Evidence, target Input, Configuration, purpose, and assessed scope at
once. A free-form role, compatibility key, or one broad target cannot encode that obligation.

## Controlled obligation taxonomy

The taxonomy should begin with existing governed acts, not job titles. Candidate kinds include:

- coordinate Case;
- determine Case identity continuity and same/new-Case routing;
- establish or revise a planned Case review point;
- assign Responsibility when separately authorized;
- maintain Configuration context;
- assess Value;
- assess Risk;
- judge Evidence Applicability;
- determine lane Fitness;
- accept an Input for bounded use;
- integrate current Value and Risk;
- collect or maintain information;
- resolve an Authority question;
- determine a Trigger;
- lead a Reassessment;
- coordinate Reassessment overlap/coverage;
- perform an Intervention/action;
- accept an Intervention Completion Result; and
- obtain Learning evidence.

The later specification must assign canonical identifiers and exact context schemas per kind.
`Applicability Owner` is not one of them; the obligation is `JUDGE_EVIDENCE_APPLICABILITY` with
exact Evidence/target/purpose/scope context. Decision Authority remains an authority concept, not
a Responsibility kind.

## Assignment and current selection

Assigning or changing Responsibility is a governed act. A **Responsibility Assignment Basis**
identifies the Actor or governed mechanism, exact organizational Authority/rule/delegation that
permits assignment, scope, limits, effective period, and history. Case Coordinator orientation
alone is not that basis.

For an exact obligation signature and effective/knowledge time, current resolution returns:

- exactly one eligible accountable Responsibility Version;
- `RESPONSIBILITY NOT ESTABLISHED`; or
- `RESPONSIBILITY CONFLICT — UNRESOLVED` with all incompatible candidates and reasons.

Compatible contributors may assist but do not become multiple accountable owners. Broad/narrow
scope, recency, specificity, role hierarchy, workload, directory order, access, and software
permission never select a winner. Reassignment and delegation are explicit successor
relationships; expiry without successor produces vacancy.

Responsibility never grants Decision Authority, Completion Acceptance authority, activation
authority, or another true authority. One Actor can hold both only through separately valid facts.

## Existing Role Assignment disposition

The target prospectively supersedes Role Assignment as the source for granular obligation
accountability. Existing Role Assignment Versions retain their original role, target,
compatibility, delegation, time, and historical meaning. They are not rewritten as Responsibilities.

During a bounded compatibility period, each governing obligation may define an explicit legacy
adapter from eligible Role Assignment functions to the old action only. The adapter retains the
legacy Version as provenance and exposes ambiguity instead of inventing missing context. New writes
use controlled Responsibility kinds after the migration cutoff. Detailed rules are in the
[Migration & Compatibility Assessment](PAIM_NORMATIVE_MIGRATION_AND_COMPATIBILITY_ASSESSMENT.md).

## Derived work

Work is derived when exact authoritative state can answer all of the following without preserving
a new coordination fact:

- what legitimate act is available or waiting;
- which exact context and prerequisites control;
- whether Responsibility is established, vacant, or conflicting; and
- where the practitioner returns after the act.

Examples include an unassigned analytical draft, one ready Input missing an Applicability result,
or an authorized proposal awaiting the separate authority action. Derived work has no task ID,
assignee, completion flag, or due date. It is rebuilt from exact sources and revalidated at action.

## When durable Case Work is required

A durable Work Item is required when PAIM must preserve at least one of:

- a cross-person request or assignment;
- an explicit handoff;
- a requester and legitimate request basis;
- a due/expected point;
- a context packet that must survive sessions;
- reassignment/delegation/cancellation history;
- an exact result-to-request link; or
- a return relationship.

PAIM must not persist Work merely to mirror an Input, Decision, Intervention, or Reassessment
status.

## Minimal Work Item

Each Work Item has stable identity and immutable Versions preserving:

- exact owning Case;
- controlled work/obligation kind and Responsibility Version, or explicit vacancy/conflict;
- exact context packet and originating prerequisite/source Versions;
- ordinary-language purpose that is not semantic authority;
- requester Actor and request/assignment basis;
- responsible Actor/mechanism through the exact Responsibility;
- created, effective, assigned, due/expected, completed, and recorded times as applicable;
- coordination state and exact waiting reason;
- required governed-result contract;
- exact committed result Version(s), when complete;
- return relationship to originating work/context; and
- predecessor, reassignment, delegation, cancellation, supersession, and history.

## Coordination states

The smallest durable vocabulary is:

- `READY` — exact prerequisites currently permit the responsible Actor to attempt the work;
- `WAITING` — one or more exact prerequisites, vacancy, conflict, or unavailable required context
  prevents the work;
- `COMPLETED` — the required exact governed result exists and is linked;
- `CANCELLED` — the request ended without the required result; and
- `SUPERSEDED` — one named successor Work identity/Version prospectively replaces it.

These are coordination states only. Readiness is not software permission or authority. Completion
is not substantive satisfaction beyond the exact linked result. Vacancy and conflict are resolver
outcomes/reasons, not a hidden completed state. No percentage complete or universal priority is
permitted.

## Result and return rule

> A Work Item coordinates work; it never substitutes for the substantive governed result.

Completing Work must cite the exact result produced by the owning domain command. A Work command
cannot create or imply Evidence Applicability, Fitness, Input use acceptance, Authority,
Decision, Intervention Completion Acceptance, Trigger Determination, Reassessment outcome, or
Learning interpretation.

An explicit vacancy/conflict may complete only a coordination request whose legitimate requested
result was to determine whether assignment exists. It cannot satisfy a substantive judgment.
After result linkage, the originating context is rebuilt. Independent prerequisites remain
independent.

## Handoff packet

Subject to access, a handoff carries:

- what is needed and why;
- exact Case and bounded use;
- only relevant visible context Versions;
- requester and responsible participant;
- due/expected point only if legitimately established;
- the required governed result; and
- the exact return relationship.

Raw IDs, compatibility keys, selection algorithms, command names, and persistence detail remain
in authorized inspection. A bounded note may clarify the request but cannot alter context,
Responsibility, authority, or result. Chat is not authoritative Case state.

## Context change, stale work, and cancellation

Review and commit re-resolve every exact source, context Version, Responsibility, access fact, and
authority guard. If a Configuration, Evidence, Input, Decision, or other controlling context is no
longer eligible:

1. the old Work cannot commit against a replacement Version;
2. the old Work and original context remain historical;
3. an accountable action cancels or supersedes it, or an exact pre-authorized mechanical rule may
   append that outcome when the future specification explicitly permits it; and
4. replacement work receives a new/successor identity and context.

No silent retarget, auto-completion, status copying, or notification-driven mutation is allowed.

## Harborlight composition

At the preserved Harborlight stop:

```text
missing exact information judgment
  -> Responsibility resolver: vacancy
  -> authorized assignment of JUDGE_EVIDENCE_APPLICABILITY
  -> Work Item carries Evidence, Value Input, Configuration, purpose, requester, and return
  -> practitioner commits Evidence Applicability through its governing capability
  -> Work links the result
  -> originating support review is recomposed
  -> second independent information judgment remains
```

The assignment does not decide Applicability. Work completion does not establish Fitness or accept
the Input. The proposal does not add the assignment to the live fixture.

## Explicit exclusions

No generic workflow engine, arbitrary task tree, sprint, Gantt view, progress score, inferred
priority, authoritative chat, role-as-access bundle, automatic owner, or Decision Authority transfer
is introduced. Organization-local deployment and notification delivery remain separate gates.
