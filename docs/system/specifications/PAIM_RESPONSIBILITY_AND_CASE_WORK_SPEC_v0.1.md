# PAIM Responsibility and Case Work Specification v0.1

## Status

Implementation-independent system specification for prospective **Responsibility**, practical Case
roles, derived work, durable Case Work, handoff, and governed-result return in Practical AI
Management (PAIM).

This specification adopts the prospective common integrity and semantic-era contract in
`PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §3A. It changes no existing v0.1 record,
command, schema, or historical interpretation and authorizes no implementation.

## 1. Purpose

PAIM must answer:

> **Who is responsible for this exact governed obligation in this exact Case, context, and time?**

It must also preserve a handoff when coordination itself has to survive without confusing the
handoff with the substantive governed result.

This specification therefore defines:

- the simple practitioner-role model;
- authoritative Responsibility identity, context, assignment, and current resolution;
- the boundary between derived work and durable Case Work;
- the minimum durable Work contract; and
- exact handoff, result-link, return, stale-context, access, and compatibility behavior.

## 2. Concept separation

| Concept | Meaning | Does not establish |
|---|---|---|
| Actor/participant | Attributable person or governed mechanism with an exact Case relationship or history | visibility, access, Responsibility, or authority |
| Case Practical Role Relationship | Orientation metadata for `CASE_COORDINATOR`, `ASSESSOR`, or optional `REVIEWER` | permission, granular obligation, substantive authority, or a result |
| Responsibility | Accountability for one controlled obligation signature | practical role, software access, Decision Authority, or the judgment itself |
| Software access | Permission to see or attempt an operation | Responsibility, assignment power, or substantive authority |
| Substantive authority | Separately governed right to perform a consequential act | Responsibility merely because the same Actor holds it |
| Work | Coordination of an obligation, request, handoff, and return | the required governed result |

Administrator is an organization/application technical function outside ordinary Case staffing.
Subject-matter expertise is contextual participation or Work, not a standing target Case role.
There is no prospective standing `Applicability Owner`, `Decision Maker`, or `Implementation Owner`
practical role.

One Actor may be Case Coordinator and Assessor, assess both Value and Risk, review information, and
hold other independent Responsibilities. PAIM retains every Responsibility, act, Value record, and
Risk record separately; same-Actor staffing never collapses their meaning or history.

## 3. Case Practical Role Relationship

A Case Practical Role Relationship is an authoritative Record with immutable Versions containing:

- stable relationship ID and immutable Version ID;
- exact Case ID and Actor ID;
- one controlled role value: `CASE_COORDINATOR`, `ASSESSOR`, or `REVIEWER`;
- assignment source and separately valid establishment basis;
- effective interval and recorded time;
- status; and
- predecessor, successor, supersession, and withdrawal history.

The current selector resolves per exact Case, Actor, role value, effective time, and knowledge
cutoff under the owning contract. These relationships orient practitioners and access-filtered
participant views. They never grant software permission, assignment authority, Responsibility,
Decision Authority, Completion Acceptance authority, activation authority, or any substantive
judgment.

## 4. Responsibility identity and signature

A Responsibility is a stable Record whose semantic identity is one exact governed obligation, not
its current holder. Each immutable Responsibility Version must preserve:

- Responsibility ID and Version ID;
- Semantic Contract ID and Version;
- one controlled obligation kind;
- exact owning Case;
- an immutable typed exact context set satisfying the kind's schema;
- purpose, bounded use, assessed scope, or discriminator where the schema requires it;
- required governed-result family and completion condition where applicable;
- responsible Actor or exact governed organizational mechanism;
- assignment source and exact Responsibility Assignment Basis Version;
- effective interval, recorded time, and eligibility status;
- predecessor/successor and explicit delegation, reassignment, supersession, or withdrawal type;
- reason; and
- exact Work and governed-result links where subsequently established.

The **obligation signature** is the canonical tuple of Semantic Contract Version, obligation kind,
owning Case, exact typed context set, and every required purpose/use/scope discriminator. Actor,
display label, practical role, access, creation time, and storage order are not signature fields.
No free-form role, compatibility key, question text, or broad target may substitute for the exact
signature.

## 5. Controlled obligation kinds and context schemas

The initial controlled taxonomy is below. `Version` means exact immutable source Version. Where a
context member does not yet exist, the obligation must cite the exact originating prerequisite and
required result contract; it must not invent a future source identity.

| Obligation kind | Required exact context roles | Required result family |
|---|---|---|
| `COORDINATE_CASE` | Case | coordination only; no substantive result implied |
| `DETERMINE_CASE_CONTINUITY` | exact Case and current continuity Status Version; controlled discriminator (`SAME_OR_NEW_CASE`, `CASE_CLOSURE`, `CASE_REOPENING`, or `CASE_SUPERSESSION`); exact changed-basis/guard context required by the Case Lifecycle contract; candidate/successor Case and Configuration context where applicable | Case Continuity Determination Version and, only through its owning atomic command, the permitted status/relationship facts |
| `MAINTAIN_CONFIGURATION_CONTEXT` | Case; Managed Configuration Version | Managed Configuration result named by the request |
| `PRODUCE_VALUE_INPUT` | Case; Managed Configuration Version; bounded use/purpose | Value Input Version |
| `PRODUCE_RISK_INPUT` | Case; Managed Configuration Version; bounded use/purpose | Risk Input Version |
| `JUDGE_EVIDENCE_APPLICABILITY` | Case; Managed Configuration Version; Evidence Version; exact target Record/Version; purpose/use; assessed scope | Evidence Applicability Version |
| `ACCEPT_VALUE_INPUT_FOR_USE` | Case; Managed Configuration Version; Value Input Version; bounded use/purpose; exact material Applicability basis | Value Acceptance/Selection Version under the current Value/Risk contract |
| `ACCEPT_RISK_INPUT_FOR_USE` | Case; Managed Configuration Version; Risk Input Version; bounded use/purpose; exact material Applicability basis | Risk Acceptance/Selection Version under the current Value/Risk contract |
| `COMPLETE_VALUE_RISK_INTEGRATION` | Case; Managed Configuration Version; exact Value and Risk Input and Acceptance/Selection Versions; bounded use | Integration Version |
| `RESOLVE_AUTHORITY_QUESTION` | Case; Managed Configuration Version where applicable; exact Authority/Authority Gap Version or originating question context | Authority or Authority Gap result Version |
| `DETERMINE_TRIGGER` | Case; exact Trigger Version; initiating Decision Version and target Configuration Version when established; declared management question/scope | Trigger Determination Version |
| `LEAD_REASSESSMENT` | Case; exact Reassessment Version; immutable Trigger Set Version; Decision and Configuration Versions | Reassessment result named by its governing command |
| `COORDINATE_REASSESSMENT` | Case; exact Reassessment/Trigger Set Versions participating in the coordination question; Decision and Configuration Versions | exact coordination determination Version |
| `PLAN_NEXT_REVIEW` | Case; exact Decision and Configuration Versions where established; review purpose/scope; exact applicable Required Review Constraint set or explicit absence | Planned Review Point Version |
| `NORMALIZE_REQUIRED_REVIEW_CONSTRAINT` | Case; exact governing source Version; exact Applicability Version; Decision/Configuration/purpose/scope where applicable | Required Review Constraint Version |
| `COMPLETE_CONTINUING_REVIEW` | Case; exact Review Episode Version; source Trigger and Planned Review Point/Required Review Constraint Versions; Decision and Configuration Versions | Review Episode completion Version; any Decision Confirmation, successor Decision, or next Planned Review Point remains a separately valid intended fact |
| `PERFORM_INTERVENTION` | Case; Decision Version; target Configuration Version; exact Intervention Version/obligation | Completion Result Version where required |
| `ACCEPT_INTERVENTION_COMPLETION` | Case; Decision Version; target Configuration Version; exact Intervention and Decision-to-Intervention Obligation Versions; Completion Result Version | Completion Acceptance Version |
| `OBTAIN_LEARNING_EVIDENCE` | Case; Decision Version; target Configuration Version; exact Learning Item Version | Evidence Version and exact Learning link |
| `DETERMINE_SHARED_DEPENDENCY_EQUIVALENCE` | exact Candidate Set Version and every constituent owning Case/context permitted by the Management Register contract | Shared Dependency Equivalence Determination Version |

Decision authorization is not a Responsibility kind. It continues to require the exact Decision
Authorization Basis. The accepted Gate-3 Case Lifecycle contract owns the meaning and exact context
of `DETERMINE_CASE_CONTINUITY`; this contract supplies only the Responsibility mechanics. Gate 5
owns the meaning and exact context of its three review kinds above; this contract supplies their
assignment, resolution, delegation, and history mechanics. Future assessment-adequacy, reliance,
or quantitative Value/Risk kinds are not created here; Gate 6 owns those semantics.

## 6. Responsibility Assignment Basis

Establishing, delegating, reassigning, withdrawing, or superseding a Responsibility is itself a
governed act. The exact Responsibility Assignment Basis Version must preserve:

- stable basis identity and immutable Version;
- assigning Actor or genuine governed organizational mechanism;
- exact authority, policy, delegation, charter, or rule Version permitting the assignment act;
- allowed obligation kinds, Cases, contexts, scope, limits, and conditions;
- effective interval and recorded time;
- provenance; and
- predecessor, revocation, withdrawal, supersession, and delegation history.

The basis must be effective, in scope, complete, accessible to the command, and valid for the exact
assignment operation. A practical role—including Case Coordinator—seniority, directory group,
source authorship, ownership label, software permission, or technical administration is not an
assignment basis. A mechanism is eligible only when PAIM has its governed identity, rule/version,
scope, source, limits, effective period, and history; free-form mechanism text is ineligible.

Assignment does not perform the obligation, make the judgment, grant access, or confer Decision or
other substantive authority. A command that establishes both a Responsibility and another intended
fact must declare both facts and commit all or none under the Gate-1 semantic-transaction contract.

## 7. Delegation, reassignment, withdrawal, and supersession

- **Delegation** creates an explicit successor/delegated Responsibility Version and cites the
  complete delegation chain. It does not erase the delegator or broaden scope.
- **Reassignment** creates an explicit successor Version for the same obligation signature with a
  valid assignment basis and reason.
- **Withdrawal** ends prospective eligibility without creating a successor.
- **Supersession** names the exact predecessor and successor and their prospective relationship.

Every chain fails closed when a link is missing, expired, revoked, withdrawn, superseded outside
the declared relationship, unrelated in context, or conflicting. Later change does not rewrite a
historically valid assignment or result.

## 8. Current Responsibility resolution

For an exact obligation signature, effective time, and knowledge cutoff, the owning selector first
applies access and then returns exactly one of:

1. one eligible accountable Responsibility Version;
2. `RESPONSIBILITY NOT ESTABLISHED`; or
3. `RESPONSIBILITY CONFLICT — UNRESOLVED`, with every accessible incompatible candidate and reason.

Multiple compatible contributors do not become co-accountable. Specificity, breadth, recency,
practical role, organizational hierarchy, workload, directory order, access, software permission,
and presentation order never choose a winner. Expiry or withdrawal without an eligible successor
produces vacancy. Co-current incompatible prospective Responsibilities and legacy candidates
produce conflict unless the adopting domain's explicit cutover relation validly displaces or links
one.

## 9. Legacy Role Assignment cutover and compatibility

All existing Role Assignment Records and Versions retain their original actor/function, free-form
role, typed target, Case context, accountable flag, compatibility key, delegation, interval,
status, provenance, and historical meaning. PAIM must never rewrite or relabel them as
Responsibilities.

There is no global date or `newer era wins` rule. Prospective Responsibility semantics apply to one
consumer only when a separately accepted implementation/migration contract:

1. declares that consumer and obligation kind adopted;
2. binds new writes to this exact Semantic Contract ID/Version;
3. declares its cutover effective and knowledge boundary; and
4. names any bounded legacy adapter and cross-era coexistence rule.

Before that cutover, the current domain specification and Role Assignment selector remain
controlling. After cutover, new obligation writes use Responsibility only. A failed prospective
write never retries through Role Assignment, and PAIM never synthesizes Responsibility from UI
state, practical roles, access, history, or Role Assignment.

An adopting consumer may read a named, versioned legacy Role Assignment adapter only for the exact
pre-cutover action and only with the legacy Version as labelled provenance. Ambiguity or missing
context remains vacancy/conflict; the adapter cannot manufacture context or become prospective
write authority. `Applicability Owner` is permitted only on that bounded legacy Evidence
Applicability path until its accepted consumer cutover. It is not a target practical role or
prospective Responsibility kind.

## 10. Derived work boundary

Work remains a read-side derivation when authoritative state already answers all of these without
preserving a coordination fact:

- what legitimate act is available or waiting;
- the exact context and prerequisites;
- the current Responsibility one/vacancy/conflict result; and
- the return location after the act.

Derived work has no authoritative Work ID, assignee, completion status, or due time. Examples
include a ready analytical candidate awaiting its current governed review or an authorized proposal
awaiting a separately governed act when no request, handoff, or return history must persist.

A durable Work Item is permitted only when at least one of these must survive: a cross-person
request/assignment; explicit handoff; legitimate requester/request basis; due/expected point;
waiting history; context packet across sessions; reassignment/delegation/cancellation history;
exact result link; or return relationship. PAIM must not mirror every domain-record status as Work.

## 11. Durable Work identity and Version

A Work Item is a stable authoritative Record with immutable Versions. Each Version preserves:

- Work ID and Version ID and this Semantic Contract ID/Version;
- exact owning Case;
- controlled obligation/work kind and exact Responsibility Version, or explicit vacancy/conflict
  when resolving assignment is itself the legitimate requested result;
- immutable context packet containing every exact originating source, prerequisite, and context
  Version plus purpose/use/scope discriminators;
- requester Actor and exact request/assignment basis;
- responsible Actor/mechanism only through the cited Responsibility;
- ordinary-language reason that cannot alter the governed context;
- optional due/expected time only when legitimately established, plus created, assigned,
  effective, completed, and recorded times as applicable;
- one bounded coordination state and exact waiting reason;
- required governed-result family, contract, and completion condition;
- exact committed result Version links when completed;
- exact return relationship; and
- predecessor, delegation, reassignment, cancellation, supersession, and reason history.

## 12. Coordination states

The controlled states are:

- `READY`: exact prerequisites currently permit the responsible Actor to attempt the work;
- `WAITING`: an exact prerequisite, Responsibility vacancy/conflict, or unavailable required
  context prevents the attempt;
- `COMPLETED`: every result required by the Work contract exists and is linked exactly;
- `CANCELLED`: the request ended without the required result; and
- `SUPERSEDED`: one named successor Work Version/identity prospectively replaces it.

These are coordination states only. `READY` is not access or authority. `COMPLETED` does not state
that another independent prerequisite is satisfied. No percentage complete, generic workflow
phase, inferred priority, severity/rank, arbitrary task tree, workflow graph, or authoritative chat
is permitted.

## 13. Result-link and return contract

> **Work coordinates; it never substitutes for the substantive governed result.**

The owning domain command creates the substantive result. A Work command may link only an exact
eligible result Version whose family, Case, context, purpose/use/scope, effective time, responsible
attribution, and contract satisfy the Work completion condition. Completing Work cannot create or
imply Evidence Applicability, Input Fitness or Acceptance/Selection, Integration, Authority,
Decision, Trigger Determination, Reassessment result, Intervention Completion Acceptance,
Activation Authorization, or Learning interpretation.

Result linkage and Work completion are one declared semantic transaction when both are intended:
all access, Responsibility, authority, context, result, and replay guards pass and all facts commit,
or none commit. Exact replay returns the original outcome without a duplicate Work, link, result,
audit fact, or notification intent. A different context, result Version, or intended fact is not a
replay.

After completion, PAIM follows the exact return relationship and recomposes originating work from
authoritative state. Each independent prerequisite is reevaluated independently. One completed
result cannot complete, hide, or waive another.

## 14. Handoff packet

Subject to access, the receiving practitioner gets the already-established exact context needed to
act: the request and reason; Case and bounded use; relevant visible Configuration, information,
assessment, Decision, and prerequisite Versions; requester; responsible participant; legitimately
established due/expected point; required governed result; and exact return relationship.

The practitioner must not reconstruct context PAIM already governs. Ordinary views may hide raw
IDs and command details, but authorized inspection retains them. A bounded note may clarify the
request; it cannot change context, Responsibility, authority, priority, or the required result.

## 15. Context change and stale Work

Review and commit re-resolve the exact context set, Responsibility, access, substantive authority,
and current domain guards at effective and knowledge time. If any controlling source is no longer
eligible:

1. the old Work cannot commit against, or silently retarget to, a replacement Version;
2. the old context and Work remain historical;
3. a separately accountable command cancels or supersedes it, unless a future owning contract
   explicitly authorizes one exact mechanical rule; and
4. replacement Work receives a new or explicitly linked successor identity and exact context.

Stale review, assignment, result-link, or return failure leaves every authoritative fact unchanged.
No silent retarget, status copying, auto-completion, or notification-driven mutation is allowed.
A `SUPERSEDED` Case is terminal for new Work and Responsibility writes from the supersession
effective time. A `CLOSED` Case accepts only the exact continuity, correction, audit, retention, or
historical operations permitted by the Case Lifecycle contract; reopening does not revive or
retarget prior Work or Responsibility.

## 16. Access and non-disclosure

Gate-1 access-before-composition and access-before-command rules apply. Work queues, participant
views, vacancy/conflict explanations, assignment choices, handoff packets, result links, counts,
and history include only facts the principal may know. Filtering must not disclose a hidden Case,
Actor, source, conflict, global count, or excluded candidate through labels, absence reasons,
ordering, timing, or aggregates.

Access never creates Responsibility; Responsibility never grants access. A responsible Actor who
lacks separately valid access cannot act and must receive a non-disclosing failure. Assignment may
not append an access grant implicitly.

## 17. Harborlight Scenario-A hard oracle

Without mutating the live Harborlight Case, the normative sequence is:

```text
Value review needs two independent Evidence Applicability judgments
  -> resolve first JUDGE_EVIDENCE_APPLICABILITY signature: RESPONSIBILITY NOT ESTABLISHED
  -> separately authorized assignment establishes its exact Responsibility
  -> contextual durable Work cites that Responsibility and exact Evidence, Value Input,
     Configuration, purpose, assessed scope, requester, and return
  -> responsible practitioner commits the Evidence Applicability through its owning command
  -> Work links that exact Applicability Version and completes atomically
  -> originating Value review is recomposed
  -> second independent Applicability prerequisite remains outstanding
```

Assignment makes no Applicability judgment, grants no Decision Authority, and does not satisfy the
second prerequisite. The same Actor may hold Case Coordinator, Value, Risk, and both information-
review Responsibilities only as separately retained facts. A different-Actor handoff carries the
same exact context and return without expanding visibility or authority.

## 18. Required normative oracles

An implementation gate must prove at least:

1. exact obligation signatures resolve one, vacancy, and incompatible conflict deterministically;
2. practical role, participation, access, authorship, and hierarchy create no Responsibility or
   authority;
3. assignment, delegation, reassignment, withdrawal, and supersession require exact valid bases
   and preserve history;
4. same-Actor multiple Responsibilities retain independent Value/Risk and result histories;
5. legacy Role Assignment history remains exact, no new `Applicability Owner` target exists, and
   prospective failure never falls back;
6. derived work has no invented authoritative task state, while durable Work exists only at the
   coordination-history boundary;
7. Work completion requires the exact owning-domain result and never creates it;
8. a different-Actor handoff preserves exact context and return, and independent prerequisites
   remain independent;
9. stale context, Responsibility, access, or authority fails closed without retargeting;
10. inaccessible sources, candidates, vacancy/conflict details, counts, and participants do not
    leak;
11. cancelled/superseded Work and all prior results remain reconstructable by effective and
    knowledge time;
12. assignment/result-link transactions commit all intended facts or zero facts and replay exactly;
13. planning, constraint normalization, and Review Episode completion resolve independently;
    Case Coordinator, software permission, timing, or source authority cannot substitute for them;
    and
14. no workflow graph, project-management state, universal score, priority, rank, strongest-state,
    semantic-similarity, or authority inference appears.

## 19. Explicit exclusions

Gate 3 defines Case continuity and supplies the exact `DETERMINE_CASE_CONTINUITY` context used
here. Gate 5 now defines the review contexts consumed by its three Responsibility kinds. This
contract does not define Gate-6 readiness/assessment-adequacy/reliance/quantitative Value-Risk
semantics. It adds no domain code,
persistence, schema, migration, UI, notification, chat, scheduler, organization-local deployment,
analytics, or Harborlight mutation.

## 20. Conclusion

PAIM uses simple practical roles for orientation, exact Responsibility for accountability, and
minimal durable Work only when coordination must survive. Access, Responsibility, substantive
authority, and the governed result remain separate at every step.
