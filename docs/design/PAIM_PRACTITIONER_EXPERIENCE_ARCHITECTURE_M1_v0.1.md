# PAIM Practitioner Experience Architecture M1 v0.1

Status: design proposal for implementation planning; technology-neutral and non-normative.

This document defines a bounded practitioner experience for the first PAIM browser milestone. It
organizes existing PAIM v0.1 capabilities; it does not amend the system architecture,
specifications, authority model, released runtime, or persistence model. If this design conflicts
with a contract under `docs/system/`, the system contract controls.

## 1. Purpose and M1 boundary

M1 should let a practitioner use a local browser to create or open a Case, understand its exact
governing context and current management position, and progress this ordinary path:

```text
Case
  -> governing Managed Configuration
  -> Evidence and independent Value/Risk Inputs
  -> Integration and Integrated Operating Boundary
  -> proposed Decision
  -> authorized Decision
  -> Intervention prerequisites
  -> Completion Result and accountable Completion Acceptance
  -> Activation Authorization
  -> bounded target operation
```

The interface is a presentation and interaction layer over existing PAIM semantics. It may compose
read models so practitioners can understand a position, but it must not create an authoritative
fact by inference or presentation.

M1 includes only the I9-P1 pathway and the administration required to operate it. It excludes:

- Trigger, Trigger Determination, Reassessment, Interim Operating Disposition, and Management
  Register workflows;
- first-class Observation, continuous monitoring, or telemetry automation;
- cloud, distributed, multi-tenant, mobile, or live-provider integration;
- a generalized workflow engine, scheduler, or generic approval/resolution action;
- scores, tiers, rankings, priorities, severity/strength order, or semantic matching;
- new substantive authority, implicit delegation, or authority supplied by software permission;
- UI code, framework choice, transport choice, deployment topology, or database changes; and
- implementation or empirical validation of Return-Weighted Risk or any external method.

The browser experience must preserve PAIM's refusal to infer. Missing Evidence is not favorable
Evidence; applicability is not portable across Configurations; one analytical lane does not decide
the other; a completed checklist does not authorize operation; and presentation order does not
create priority.

## 2. Practitioner mental model: Orient, Manage, Reconsider

The top-level experience uses management work, not record machinery:

1. **Orient** — What exact Case and Configuration am I looking at? What changed? What is the
   current management position? What is established, absent, conflicted, or blocked?
2. **Manage** — What legitimate action is available now, what prerequisites govern it, who is
   accountable, and what authority is required?
3. **Reconsider** — What new information or event could require reassessment, and where would that
   future work begin?

M1 implements Orient and Manage for the ordinary Case-to-operation pathway. Reconsider is shown
only as a safe, read-only handoff: it explains that Learning does not rewrite a Decision and that
future Trigger/Reassessment work is outside M1. It is not a disabled imitation of a workflow.

The Case Workspace is the center of M1 because the Case is the bounded management context that
connects one exact governing Configuration to its Evidence, analytical inputs, management
judgments, authority, intervention, operation, Learning, and history. Home and Cases help the
practitioner orient; consequential management work returns to that context.

“Current management position” is a read composition of the exact Case lifecycle state, governing
Configuration Version, selected analytical inputs, Decision and authorization state, Intervention
and prerequisite state, and material absences/conflicts. It is not a new authoritative status.

## 3. Application shell and navigation

The persistent shell contains:

- **Home** — active orientation and attention;
- **Cases** — safe Case discovery and entry to the Case Workspace;
- **Administration** — identity, access, roles/accountability, authority mechanisms, and local
  health, separated into their distinct layers;
- **Reassessments** — labeled “Future milestone”; explanatory route only; and
- **Management Register** — labeled “Future milestone”; explanatory route only.

Future routes are not dead buttons. Each opens a short boundary page that states what is not in
M1, names the controlling PAIM concept, and returns the practitioner to the relevant Case area.
They cannot create approximate records or generic tasks.

The shell always shows the authenticated Actor and local application health. It never labels an
operational administrator as a Decision Authority. If health is `DEGRADED`, the shell changes to a
clearly announced degraded state and consequential commands fail closed.

## 4. Home: attention without scoring

Home answers “Where does legitimate management attention belong?” It groups visible Cases by
exact, explainable conditions rather than by a computed score:

- configuration definition or governing designation needed;
- Evidence, authority, Value, or Risk work needed;
- integration or Boundary work needed;
- Decision proposal or authorization needed;
- Intervention, Completion Acceptance, prerequisite, or Activation work needed; and
- operating under an authorized Decision.

Every group is a deterministic read composition from existing authoritative facts. Counts are
limited to the Actor's visible population. No hidden Case identity or global count leaks through
group labels, empty states, filters, error text, or totals.

Each Case row shows its title, exact lifecycle state, governing Configuration label and Version
identity, a plain-language management position, material blockers, and the next owning area. The
row does not show “high risk,” readiness scores, red/amber/green grades, recommendation scores, or
queue priority. Ordering is stable and user-selectable only on neutral fields such as title or
recorded date; it has no governing meaning.

## 5. Cases: safe find, create, and open

The Cases screen supports:

- text search over visible Case titles and explicitly visible identifiers;
- filtering by exact lifecycle state, governing-Configuration presence, explainable work area,
  assigned/accountable work, and recorded change time;
- sorting by neutral visible labels or recorded change time, with no implied priority;
- creating a Case through the existing Case command;
- opening a visible Case Workspace; and
- displaying a bounded denial when Case or Configuration visibility is absent.

Search similarity never establishes equivalence, dependency, duplicate identity, or priority.
Filters never disclose whether hidden Cases match. “Create Case” first explains identity,
`COMMAND` access, and the required exact input; success returns the new Case identity and opens its
Overview. It does not assign an owner or create authority implicitly.

## 6. Case Workspace

The Case Workspace is the primary management surface. Its areas are:

1. **Overview**
2. **Evidence & Assessment**
3. **Decision**
4. **Implementation & Operation**
5. **Learning & Reassessment**
6. **History**

A persistent Case summary remains visible across all areas. It contains:

- Case title and exact Record identity;
- exact lifecycle state, explicitly distinguished from operating state;
- exact governing Configuration Record and Version;
- current authorized Decision Version, or explicit absence/conflict;
- target operating state and current operation statement, when established;
- material Authority Gaps and accountability vacancy/conflict;
- the next legitimate action and its owning work area;
- an “as effective at / known by” context; and
- application health and last reconstructed time.

Version identities are initially abbreviated for readability but are copyable and expandable in
full. The summary never silently advances from one Version to another while a practitioner is
editing. A newer current Version produces a stale-context stop requiring review.

## 7. Case Overview

Overview explains the whole position before asking for action. It contains:

- **Management question** — the bounded question the Case exists to answer;
- **Managed context** — capability, intended use, users, workflow, conditions, and exclusions from
  the exact Configuration content;
- **Current position** — lifecycle state, governing designation, Decision/operation summary, and
  explicit absences/conflicts;
- **Current Boundary** — exact permitted, conditional, and prohibited/out-of-scope uses from the
  governing Boundary, presented as Case-specific management constraints rather than a universal
  compliance checklist;
- **Pathway** — the M1 sequence with completed, current, and not-yet-reachable steps. This is an
  explanation of existing facts, not a new workflow status;
- **What needs attention** — grouped prerequisites with links to owning areas; and
- **Why this position / What can change it** — the shared explanation pattern in section 13.

When no governing Configuration exists, Overview shows finalized candidates and the exact
designation action. It never chooses “latest,” “most specific,” or “most complete.” A designation
conflict remains explicit. Creating or changing a Configuration creates a new exact Version; the
interface never edits authoritative history in place.

## 8. Evidence & Assessment

This area keeps four concerns visible without collapsing them:

### Evidence and applicability

Evidence cards show source/provenance, exact Evidence Version, target/question, applicability
state, fitness/use constraints, uncertainty, and accountable basis. Material absence, missing,
conflicting, stale, inapplicable, indeterminate-fitness, vacancy, and conflict states are explicit.
Evidence arrival or existence does not imply applicability, fitness, acceptance, or favorable
meaning. Provenance and applicability basis are progressively disclosed from a concise state card
to the exact Version/target/question/time detail.

### Authority and Authority Gaps

Authority records and gaps show the exact question, target, state, provenance, owner/accountability
position, and history. A gap is not hidden merely because bounded proceeding may be legitimate.
Software access, a role label, or Case ownership cannot close it.

### Independent Value and Risk lanes

Value and Risk occupy equal-width peer panels with distinct language, sources, candidate Inputs,
acceptance selections, fitness, and frozen current selections. A practitioner can compare them,
but no shared badge, combined score, averaged tier, or automatic consensus is produced.

Each lane independently displays one of:

- exact selected accepted/frozen Input and Acceptance/Selection Version;
- input selection not established; or
- input selection conflict — unresolved.

Non-selected, dissenting, and ineligible candidates remain inspectable. Value does not determine
Risk, Risk does not determine Value, and one acceptance action cannot satisfy both lanes.

### Integration preparation

Once both exact Inputs and their material Evidence/authority basis are ready, the integration
workspace displays reinforcement, conflict, constraint, Control Dependency, uncertainty,
alternatives, and Configuration trade-offs. These are recorded PAIM judgments and relationships,
not UI-generated analysis.

M1 must not infer Evidence quality from source appearance, treat missing Evidence as favorable,
reuse applicability across Configurations, or offer a universal Value/Risk score or risk tier.

## 9. Decision

The Decision area presents four separate positions:

- integration/Boundary not established;
- proposed Decision;
- authorization blocked or not established; and
- authorized Decision.

The proposal composer binds exact Configuration, selected Value and Risk Inputs and selections,
integration, Boundary, uncertainty, alternatives, conditions, and rationale. It shows the bound
Version set before submission. A stale bound Version blocks submission and asks for deliberate
reconstruction; it is never silently replaced.

Authorization is a separate action and panel. It shows:

- the proposed Decision Version;
- exact Decision Authority or explicit `DECISION AUTHORITY UNRESOLVED` gap;
- accountable Actor and assignment/mechanism;
- complete Decision Authorization Basis, scope, limits, and effective period;
- actor identity and software access as separate prerequisites; and
- the resulting authorized Decision Version and immutable basis after success.

The UI never equates proposal with authorization, a Role Assignment with authorization, or an
administrator/technical principal with Decision Authority. Bounded-proceed behavior, if the exact
contract permits it, must retain the unresolved gap and full authorization basis rather than show
an exception or override.

The shared explanation answers why authorization is or is not established and what exact fact can
change that result. There is no generic “Approve,” “Override,” or “Mark resolved” action.
Decision history remains visible in this area as a concise predecessor/successor chronology, with
exact basis available through the read-only provenance view.

## 10. Implementation & Operation

This area deliberately preserves the following facts as separate objects and steps:

1. authorized Decision;
2. Intervention and exact obligation set;
3. implementation progress;
4. Completion Result and supporting Evidence;
5. accountable Completion Acceptance;
6. exact all-of prerequisite evaluation; and
7. Activation Authorization for the exact target Configuration, Decision, Boundary, operating
   state, and effective time.

A pathway panel may visually connect them, but it must not flatten them into one checklist. Every
step exposes its own identity, state, accountable basis, authority where required, rationale,
effective/recorded time, and source Versions.

Completion status alone is not acceptance. Completion Acceptance alone is not prerequisite
satisfaction. Satisfied prerequisites do not authorize activation. Activation authority is shown
as either the applicable Decision Authority acting explicitly or an exact genuine organizational
activation mechanism pre-authorized in the Decision Authorization Basis. A technical rule,
administrator, permission, owner, or completed checklist cannot substitute.

The final operation card says exactly which Configuration Version may operate, under which
authorized Decision and Boundary, in which operating state, from what effective time, and on what
Prerequisite Evaluation Basis and Activation Authorization. The Case lifecycle state remains
separately visible.

## 11. Learning & Reassessment

In M1 this area supports existing Decision-specific Learning creation and inspection. It explains:

- what should be learned and why;
- which exact Decision, Configuration, Boundary, uncertainty, or condition the Learning Item is
  linked to;
- whether a method is evidence-supported or practitioner-designed; and
- that Learning does not automatically change, supersede, or reopen a Decision.

The Reassessment portion is a read-only future handoff. It can state that a material event may
need the future Trigger/Reassessment pathway, but it cannot create an Observation approximation,
infer a Trigger from telemetry, or use a generic “reopen” action. It links back to History and the
current authorized basis so the handoff remains exact.

## 12. History and provenance

History has two depths:

### Practitioner history

A chronological, human-readable sequence of material Case events shows what changed, by whom,
when effective, when recorded, why, and which exact Versions were involved. Filters separate Case,
Configuration, Evidence/authority, Value, Risk, Decision, Intervention, activation, and Learning
events. Corrections, supersession, withdrawal, and conflicts remain visible.

### Provenance detail

An expandable detail view exposes complete Record/Version identities, relationships, command and
audit identities, effective/recorded/knowledge time, source provenance, authorization basis, and
immutable content digests where available. It supports exact reconstruction rather than a
“current snapshot only” view.

History never rewrites a predecessor, hides a dissenting analytical Input, or treats a broad
semantic key as an exact Version. Effective-time and knowledge-time controls state their cutoff
explicitly and show when the result differs from current knowledge. Both history depths are
read-only; editing creates a governed successor through an owning-domain command elsewhere.

## 13. Shared “Why?” and “What can legitimately change it?” pattern

Every material state card uses the same explanation structure:

1. **State** — the exact established, absent, conflicted, blocked, or authorized result.
2. **Why?** — controlling exact facts and Versions; required conditions that passed or failed;
   accountable basis; and authority basis where applicable.
3. **What can legitimately change it?** — a named owning-domain action, the actor/accountability
   and authority needed, exact context it would bind, and facts that action must not infer or
   mutate.

An optional **Inspect basis** action opens provenance detail. A separate **Can I act?** explanation
shows five layers without merging them:

- authenticated identity and mapped PAIM Actor;
- software access for the exact command;
- visibility of the exact Case and Configuration;
- current applicable accountable Role Assignment or mechanism; and
- substantive Authority or Authorization Basis.

When the current Actor cannot act, the UI identifies the missing layer and the legitimate owner of
the remedy. It does not imply that an access administrator can cure accountability or authority.

## 14. Administration

Administration is organized by meaning rather than by a single permissions table:

- **Identity** — principals, mapped Actors, enabled/disabled/revoked versions;
- **Software access** — exact permission/action/scope ALLOW or DENY facts;
- **Governed-context visibility** — Case and Configuration read access;
- **Accountability** — Role Assignments, typed targets, currentness, delegation, vacancy, and
  conflict; and
- **Substantive authority** — Authority records, gaps, Decision Authorization Basis, Completion
  Acceptance authority, and activation mechanisms.

The UI may place these layers on one route for usability, but it cannot combine their effects.
Every access or assignment change is append-only and shows exact scope and effective time.
Competing broad/narrow, recent/older, or role-hierarchy assignments have no implicit winner.

Local operational administration also includes health, authentication/access diagnostics,
counters, backup, and restore guidance. `READY` means the application is operationally usable; it
does not claim that a Case, Evidence set, Decision, or authority basis is substantively valid.
Ordinary practitioners should not visit Administration to progress normal Case work. A Case
explanation may route an authorized administrator or owning role there only when the missing layer
is genuinely administrative, accountability-related, or authority-related.

## 15. First use and constructed illustration

After local initialization, first use offers three clear choices:

- **Explore a constructed demonstration Case** — conceptually available when a production-created,
  explicitly constructed demonstration is provided in a later issue;
- **Start a new Case** — use the normal production Case path; and
- **Resume existing work** — open the visible Cases or Home attention view.

First use separates local initialization from ordinary management work:

1. an operator establishes the supported local instance, protected credential, initial identity,
   and bounded administration;
2. the browser confirms health and the five action layers; and
3. the practitioner creates a real Case through production PAIM paths.

The Quick Start remains the initialization authority until a later technical architecture decides
which setup capabilities move into the browser. After a local instance is initialized and
administered, the ordinary M1 Case-to-operation pathway must not require hidden CLI intervention.

Aster Vale/Navigator may appear as an explicitly labeled constructed illustration that explains
concepts. Any additional lifecycle event must be labeled a constructed PAIM extension. M1 does not
create a special fixture, seed the database, inject test helpers, or claim that Aster Vale is an
empirical case. If a future demo is populated, it must use the same production commands and guards
as practitioner data.

PAIM does not implement or empirically validate Return-Weighted Risk. PAE risk tiers, readiness
scores, and recommendation mechanics, and APRM portfolio concepts are not PAIM semantics and are
not imported into this design. Prior interfaces may supply usability observations only; PAIM's own
contracts control identity, state, action, accountability, and authority.

## 16. Accessibility

M1 targets WCAG 2.2 AA behavior as an implementation acceptance concern:

- full keyboard operation with visible focus and logical focus order;
- semantic headings, landmarks, labels, tables, and status announcements;
- no information conveyed by color, position, icon, animation, or sound alone;
- text alternatives for diagrams and meaningful icons;
- sufficient contrast and support for zoom/reflow without loss of action or provenance;
- explicit error summaries linked to fields and preservation of entered data after validation;
- plain-language labels paired with exact PAIM terms and definitions;
- reduced-motion support and no time-limited consequential action; and
- explicit review/confirmation for consequential actions, showing exact bound Versions and the
  effect before commit;
- desktop-first responsive reflow that remains usable at narrower desktop/tablet widths without
  defining a mobile product; and
- screen-reader announcements for stale context, denial, conflict, vacancy, successful commit, and
  degraded state.

Equal Value/Risk presentation must remain usable at narrow widths by using ordered peer sections,
not by visually demoting one lane.

## 17. Errors, denials, and degraded operation

| Condition | Required experience | Prohibited behavior |
|---|---|---|
| Authentication expired or lost | Preserve safe unsent input locally, require reauthentication, and reconstruct exact context before submission. | Silent command replay or credential persistence. |
| Software access denied | Name the required permission/action/scope without leaking protected context and link an authorized administrator to the exact access fact. | Present denial as lack of substantive authority. |
| Case/Configuration visibility absent | Fail closed with a bounded message; expose no protected identifier, fact, matching count, or relationship. | Existence confirmation through filters, totals, or errors. |
| Accountability vacancy | State “not established,” identify the exact typed target and owning assignment action. | Choose an owner from participation, recency, specificity, hierarchy, or permission. |
| Accountability conflict | Show all visible incompatible bases and the legitimate supersession/delegation/policy path. | Select an implicit winner. |
| Substantive authority absent or out of scope | Preserve the proposed work and show the exact Authority Gap or incomplete basis. | Offer administrator override or generic approval. |
| Stale Record/Version context | Stop before commit, show the changed exact Versions, and require deliberate review/recomposition. | Substitute current Versions or retry automatically. |
| Duplicate submission or unknown outcome | Disable repeated clicks, preserve the command/idempotency identity, inspect the existing outcome, and retry only the same intent when the contract permits. | Generate a new semantic command merely because a response was lost. |
| Application `DEGRADED` | Stop new consequential commands, show bounded health reasons and operator recovery guidance, and leave established history untouched. | Claim substantive invalidity or modify an existing authorized Decision. |
| Unexpected domain rejection | Preserve field input and exact correlation/command/audit identity; explain the failed guard and stop. | Hide failure, mutate inputs, or route around a guard. |

## 18. Screen inventory and interaction architecture

### Screen inventory

| Screen | Practitioner goal and key information | Available actions | Prerequisites | Success / blocked / next step |
|---|---|---|---|---|
| Home | Orient across visible Cases using exact lifecycle and explainable attention groups. | Open Case; create Case. | Identity; visible population; health. | Success opens a Case. Blocked state identifies access or health layer. Next: Cases or owning area. |
| Cases | Find, filter, create, or open a visible Case without semantic ranking. | Search/filter; create Case; open Case. | `case.create` access for creation; `CASE_READ` for opening. | New Case opens Overview; hidden matches never leak. Next: governing Configuration. |
| New Case | Establish a bounded Case identity and management question. | Commit Case. | Exact inputs; Actor; `COMMAND`; healthy application. | Shows exact Case Record/Version. Block preserves input and basis. Next: Overview. |
| Case Overview | Understand exact Case, governing Configuration, pathway, blockers, and operating position. | Create/version Configuration; designate governing Configuration; follow owning link. | Case and Configuration visibility; action-specific access/accountability. | Exact designation shown; vacancy/conflict explicit. Next: Evidence & Assessment. |
| Configuration detail | Inspect content, purpose, maturity, history, and exact governing status. | Create successor Version; propose/designate exact governing Version. | Existing configuration contracts and exact Version context. | New Version never rewrites predecessor. Next: Overview or assessment. |
| Evidence & Authority | Establish and inspect Evidence, Applicability, fitness, Authority, and Gaps. | Commit Evidence, Authority, Gap, and Applicability judgments through owning commands. | Exact target/question; visibility; command access; accountable basis. | State becomes exact established/absent/conflicted result. Next: independent lanes. |
| Value lane | Build, assess, accept/select, and freeze the exact Value Input independently. | Commit candidate/readiness/fitness/selection actions. | Governing Configuration; Evidence basis; Value accountability; exact Versions. | One exact selected Input or explicit absence/conflict. Next: Risk or Integration. |
| Risk lane | Build, assess, accept/select, and freeze the exact Risk Input independently. | Commit candidate/readiness/fitness/selection actions. | Governing Configuration; Evidence basis; Risk accountability; exact Versions. | One exact selected Input or explicit absence/conflict. Next: Value or Integration. |
| Integration & Boundary | Make accountable judgments about interaction, uncertainty, alternatives, controls, and exact Boundary. | Commit Integration, uncertainty, Boundary snapshot/determination. | Both exact selected lanes and material basis; accountability. | Exact integration/Boundary Versions. Block identifies missing/conflicted basis. Next: Decision. |
| Decision | Propose and separately authorize an exact management Decision. | Commit proposal; authorize Decision; inspect basis. | Exact integration/Boundary; command access; accountability; complete authority basis. | Proposed or authorized exact Version. Gap remains visible. Next: Implementation & Operation. |
| Intervention | Define intervention and exact obligations; record implementation progress and Completion Result. | Commit Intervention, obligation set, result, replacement/validity where applicable. | Authorized Decision; exact scope; owner/accountability; command access. | Exact result and unmet obligations shown. Next: Completion Acceptance. |
| Completion Acceptance | Record accountable acceptance of the exact Completion Result. | Commit acceptance. | Exact result/evidence; eligible acceptor assignment/mechanism; command access. | Accepted/rejected result with exact basis. Next: prerequisite evaluation. |
| Activation | Inspect all-of prerequisite evaluation and separately authorize target operation. | Evaluate prerequisites; authorize activation/transition through existing activation command. | Exact accepted completion, current Decision/Boundary, valid activation authority. | Exact Activation Authorization and bounded operation statement. Block identifies each failed layer. Next: Learning. |
| Learning & Reassessment | Record Decision-specific Learning and understand future reconsideration boundary. | Commit Learning Item; inspect links. Reassessment is read-only in M1. | Existing Decision/Configuration context; action-specific access/accountability. | Learning linked without Decision mutation. Next: History or future handoff. |
| History | Reconstruct effective-time and knowledge-time facts and provenance. | Filter; select time context; inspect/copy exact IDs. | Visibility to exact governed context. | Exact reconstruction with differences from current knowledge made explicit. |
| Administration | Manage distinct identity, access, visibility, accountability, authority, and health layers. | Existing administrative and owning-domain commands only. | Layer-specific operational access and substantive guards. | Append-only fact/version and audit identity. No authority transfer by administration. |
| Future boundary | Understand why Reassessments/Register are outside M1. | Return to Case; open governing documentation. | None beyond application access. | No domain record or approximate workflow is created. |

### Ordinary-path interaction map

```text
Home
  -> Cases -> New Case -> Case Overview
                         |
                         +-> Configuration detail -> exact governing designation
                         |
                         +-> Evidence & Assessment
                               |-> Evidence / Applicability / Authority Gaps
                               |-> Value lane (independent selection)
                               |-> Risk lane  (independent selection)
                               +-> Integration & Boundary
                                      |
                                      +-> Decision proposal
                                             |
                                             +-- authority vacancy/conflict --> Why / owning action
                                             |
                                             +-> Decision authorization
                                                    |
                                                    +-> Intervention / obligations
                                                           |
                                                           +-> Completion Result
                                                                  |
                                                                  +-> Completion Acceptance
                                                                         |
                                                                         +-> prerequisite evaluation
                                                                                |
                                                                                +-- failed --> exact unmet basis
                                                                                |
                                                                                +-> Activation Authorization
                                                                                       |
                                                                                       +-> bounded operation
                                                                                              |
                                                                                              +-> Learning
                                                                                                    -> History
```

At every side route, returning to the pathway reconstructs current exact Versions. The browser
does not trust a stale tab, URL, form value, or client-side cache as the continuity authority.

## 19. M1 acceptance scenarios

The experience is acceptable only if a practitioner can complete these scenarios using the
browser after the local instance has been initialized and administered, without hidden CLI repair,
test helpers, raw SQL, or direct database mutation:

1. Create a Case, create/finalize a candidate Configuration, establish visibility, and designate
   the exact governing Configuration through production capabilities.
2. Establish required accountable Role Assignments while seeing that access, accountability, and
   authority remain distinct.
3. Establish Evidence, exact Configuration-bound Applicability/fitness, Authority records, and
   visible Authority Gaps; demonstrate that absence does not become favorable Evidence.
4. Create and freeze one exact Value Input and one exact Risk Input independently, including
   distinct acceptance/selection bases and retained dissenting candidates.
5. Establish Integration, uncertainty, alternatives, Control Dependencies, and an exact Integrated
   Operating Boundary without a combined score or inferred recommendation.
6. Propose a Decision, observe that it is not authorized, then authorize it only through the exact
   complete Decision Authorization Basis.
7. Establish an Intervention and obligations; record a Completion Result; show that completion
   does not equal acceptance.
8. Record accountable Completion Acceptance; evaluate every prerequisite; show that satisfied
   prerequisites do not equal Activation Authorization.
9. Authorize activation separately and display the exact bounded target-operation basis.
10. Create a Learning Item linked to the exact Decision without altering that Decision.
11. Reconstruct the pathway at effective time and knowledge cutoff using exact Record/Version
    identities, with predecessor history unchanged.
12. Encounter missing `COMMAND`, `CASE_READ`, and `CONFIGURATION_READ` prerequisites and receive
    distinct, non-leaking explanations and owning next actions.
13. Encounter accountability vacancy and incompatible assignment conflict; receive no implicit
    winner by specificity, breadth, recency, role hierarchy, or permission.
14. Encounter missing/out-of-scope Decision authority and Activation authority; receive no admin
    override or generic approval.
15. Encounter a stale exact Version during proposal or authorization; stop, compare, and
    deliberately reconstruct rather than silently rebinding.
16. Encounter degraded health or an unknown command outcome; preserve evidence and fail closed
    without duplicate semantic effects.

Acceptance also requires that each material state answers “Why?” and “What can legitimately
change it?”, and that the answer names an existing owning-domain action or a clearly identified
future boundary.

## 20. Deferred technical architecture and read needs

This design deliberately leaves the following to a later implementation-architecture issue:

- server-rendered pages versus a richer client frontend;
- templating system and component library;
- HTTP/API shape;
- session and cookie mechanics;
- CSS system and design tokens;
- JavaScript strategy;
- packaging and local launcher; and
- browser testing stack.

That later issue must preserve the released local application's security and integrity boundaries.

M1 requires read/query composition that the current command-oriented application may not expose as
one public interface. The future technical design should map, without creating new semantics:

- visible Case discovery and neutral filtering;
- current management-position composition for one exact Case and knowledge context;
- governing Configuration selection and candidate/conflict explanation;
- side-by-side Value/Risk selection and handoff-readiness explanation;
- Evidence/authority/applicability and accountability resolution explanations;
- Decision, Intervention, Completion, prerequisite, activation, and operation basis views;
- action eligibility across identity, access, visibility, accountability, and authority;
- “Why?” guard/basis composition and legitimate owning-action routing;
- exact effective-time and knowledge-time history reconstruction; and
- bounded health, audit, provenance, and non-leaking denial details.

These are read compositions of authoritative records, existing selection/resolution rules, and
existing command results. They must not be persisted as new governing facts merely for display.
Any cache or projection is disposable, reconstructable, access-filtered, and subordinate to exact
source Versions and knowledge context.

### Existing-capability trace

The names below identify the released production capability families, not a proposed browser API.
They demonstrate that M1 actions have an existing semantic owner.

| M1 interaction | Existing production capability or bounded read need |
|---|---|
| Create/open a Case | `commit_case` / operational `case-create`; visible-Case discovery is a bounded read composition. |
| Create/version or designate a Configuration | `commit_configuration`, `commit_governing_designation`, and `select_governing_configuration`. |
| Establish roles and explain accountability | `commit_role_assignment`, `resolve_role_performers`, and `resolve_accountability`. |
| Establish Evidence, Authority, Gaps, and Applicability | `commit_evidence`, `commit_authority_record`, `commit_authority_gap`, `commit_evidence_applicability`, and `select_evidence_applicability`. |
| Establish independent Value/Risk Inputs | `commit_analytical_input`, lane-specific readiness/fitness/disposition capabilities, `commit_acceptance_selection`, and `select_input`, invoked independently for each lane. |
| Establish Integration and Boundary | `commit_integration`, `commit_uncertainty_classification`, `commit_boundary_snapshot`, and `commit_boundary_determination`. |
| Propose and authorize a Decision | `commit_decision_proposal`, `commit_bounded_proceed` where its exact guards apply, `authorize_decision`, and `current_authorized_decision`. |
| Establish Intervention and obligations | `commit_intervention`, `commit_obligation_set`, and existing Case transition capabilities. |
| Record and accept completion | `commit_completion_result`, completion-accountability resolution, and `commit_completion_acceptance`. |
| Evaluate prerequisites and authorize activation | `evaluate_prerequisites` and `activate_target`; their separate guards remain controlling. |
| Record Learning | `commit_learning_item`. |
| Explain position and reconstruct history | Existing current selection/resolution functions plus exact Record/Version, status-event, relationship, effective-time, recorded-time, knowledge-time, audit, and provenance reads; this requires bounded query composition only. |
| Explain identity/access/visibility | Existing principal authentication, `permission_allowed`, `accessible_case_ids`, and `accessible_configuration_ids` behavior, composed separately from accountability and authority. |

The future transport may expose these capabilities differently, but it may not duplicate their
rules in a client or replace them with a generic state-transition endpoint.

The implementation issue must produce a trace from every browser action to an existing production
capability such as Case/Configuration commit and designation; role/accountability resolution;
Evidence, Authority Gap, Applicability, and analytical-input commands; Integration/Boundary and
Decision commands; Intervention, Completion Acceptance, prerequisite, activation, and Learning
commands. If no production command exists, M1 may expose only a read-only explanation or defer the
action. The UI must never bridge that gap with `tests.*`, fixture injection, raw SQL, or a semantic
shortcut.

## Source and authority basis

This design is derived from:

- [PAIM v0.1 Conceptual Guide](../PAIM_CONCEPTUAL_GUIDE_v0.1.md);
- [PAIM v0.1 Practitioner Pathways](../operations/PAIM_V0_1_PRACTITIONER_PATHWAYS_v0.1.md);
- [PAIM v0.1 Quick Start](../operations/PAIM_QUICK_START_v0.1.md);
- [PAIM Local Operational Application](../operations/PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md);
- [PAIM System Architecture](../system/architecture/PAIM_SYSTEM_ARCHITECTURE_v0.1.md);
- the current [PAIM system specifications](../system/specifications/); and
- [Increment 9 Practitioner Findings Cross-Pathway Review](../engineering/PAIM_INCREMENT_9_PRACTITIONER_FINDINGS_CROSS_PATHWAY_REVIEW_v0.1.md).

The source hierarchy remains unchanged. This experience architecture defines navigation,
presentation, explanation, and interaction boundaries; it does not become a substitute for PAIM's
implementation contracts.
