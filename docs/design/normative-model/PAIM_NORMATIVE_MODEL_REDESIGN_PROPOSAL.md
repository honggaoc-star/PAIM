# PAIM Normative Model Redesign Proposal

## Decision boundary

This proposal is the integrated Issue #127 semantic checkpoint. It defines a prospective target
model; it does not amend the current [system specifications](../../system/specifications/), which
remain controlling. It authorizes no domain, persistence, migration, UI, scheduler, notification,
deployment, analytics, Harborlight, UX-4, M1D, or release change.

The design is governed by the
[Product Design Foundation](../practitioner-ux/PAIM_PRODUCT_DESIGN_FOUNDATION.md),
[Practitioner Operating Model](../practitioner-ux/PAIM_PRACTITIONER_OPERATING_MODEL.md), and four
rules:

> The engineering model must be rigorous enough to protect the management process. The
> practitioner experience should be as simple as that rigor allows.

> Expose the user's action; absorb the system operation.

> Show state as meaning, not status.

> Preserve history so practitioners can learn from it; never make them maintain history as a
> separate task.

Value and Risk remain independent. Responsibility remains distinct from authority. Later knowledge
never contaminates earlier knowledge. Presentation, access, history, recency, or similarity never
establishes Applicability, materiality, responsibility, authority, priority, or a Decision.

## Smallest rigorous target

The current integrity kernel already supplies stable Records, immutable Versions, exact
relationships, effective and recorded time, explicit absence/conflict, current selection, and
historical reconstruction. The target reuses that foundation and adds only the concepts for which
authoritative continuity cannot be derived safely:

1. **Case practical-role relationship** — optional authoritative orientation metadata for Case
   Coordinator, Assessor, and Reviewer; never a permission, Responsibility, or authority bundle.
2. **Responsibility** — the exact attributable answer to who is responsible for one governed
   obligation in one context and time.
3. **Case Work Item** — durable coordination only when a request, assignment, handoff, due point,
   result, or return history must survive.
4. **Review Timing** — a planned next review point and exact required-review constraints, each with
   source, applicability, time, and history.

No separate Participant record is required: the existing PAIM Actor remains the attributable
person/mechanism identity. No current-management-position record is required: it remains an
access-filtered read composition. No universal lifecycle, priority, score, automatic Selection, or
workflow graph is introduced.

The accepted operating-model boundaries remain fixed: ordinary Case staffing centers on Case
Coordinator and Assessor, with Reviewer optional; subject-matter expertise is contextual
participation/work; post-Decision actions are assigned directly rather than through a standing
Implementation Owner; and technical Administrator remains outside ordinary Case staffing. `Local`
continues to mean organization-controlled as product direction, while supported operation remains
the current single-workstation/loopback topology until a separate deployment gate succeeds.

## Integrated concept model

```text
Actor
  |-- Case practical-role relationship (orientation only)
  |-- Responsibility (exact obligation and context)
  |       |-- may receive durable Case Work
  |       `-- never supplies substantive authority
  |
Case (continuing bounded management identity)
  |-- Configurations / Information / independent Value and Risk
  |-- Decisions and Authorization Bases
  |-- Actions / Interventions / Learning
  |-- event occurrences and planned/required review timing
  |-- Triggers / focused review / Reassessments
  `-- exact longitudinal history and derived current position
```

Each authoritative concept uses the common integrity contract. Derived work, current position,
attention, counts, labels, and practitioner summaries retain exact source Versions and may never
become write authority.

## Continuing Case

A Case is the durable identity for one bounded AI-related business management question/use. It can
preserve multiple Configurations, assessments, Decisions, actions, review episodes, and learning
over time without rewriting any prior position.

The current phase-style Case lifecycle is useful v0.1 workflow history but is too broad as the
future organizing model: a Case can be operating while assessment, intervention, focused review,
and Reassessment coexist. The target therefore reduces Case-level status to continuity:

- `OPEN` — the same bounded management subject remains eligible for continuing management,
  whether or not work is presently active;
- `CLOSED` — an accountable determination establishes that no active operation or remaining
  required PAIM management obligation continues under this identity; history remains available;
  and
- `SUPERSEDED` — a named successor Case prospectively carries the management subject.

`Completed`, `active`, `ready`, `decided`, and `reopened` are not universal Case statuses in the
target. They belong to exact work, Decision, operation, or Reassessment contexts or are derived
descriptions. A discontinued AI use does not close the Case while required action, learning,
review, or authority treatment remains. A closed Case may be reopened only through an explicit
continuity determination; a superseded Case remains terminal.

A materially different business use becomes a new Case. When that boundary is not mechanically
clear, an accountable **Case Continuity Determination** preserves the exact prior Case, changed
basis, same/new-Case outcome, rationale, actor/Responsibility, time, and successor relationship.
Similarity, shared provider, or convenience never decides identity.

The detailed recommendation is in the
[Case Continuity & Historical Reconstruction Review](PAIM_CASE_CONTINUITY_AND_RECONSTRUCTION_REVIEW.md).

## Participant, practical Role, Responsibility, and Authority

- **Participant:** a Case participant is an Actor related through a current/historical practical
  role, Responsibility, Work request/assignment, substantive act, or authority relationship.
  Participation is derived from those exact sources; software access alone never creates it.
- **Practical Role:** Case Coordinator, Assessor, and optional Reviewer are authoritative Case
  relationship metadata only when the organization needs current and historical orientation.
  They never grant permissions, select Responsibility, or create authority.
- **Responsibility:** an authoritative, versioned obligation assignment with exact kind, Case,
  context basis, purpose/scope, responsible Actor/mechanism, assignment basis, interval,
  predecessor/delegation/supersession, and history. Current resolution returns exactly one,
  vacancy, or conflict.
- **Authority:** the separately established right to perform a consequential act. Decision
  Authority and other true authority remain governed by their exact authorization contracts.

One Actor may coordinate the Case, assess Value and Risk, and perform information reviews when each
Responsibility is separately established. The records and accountability remain independent.
`Applicability Owner` is not a target practical role or new obligation label; future
Responsibility names the exact information Applicability obligation and context.

Existing Role Assignment remains controlling for v0.1 history and current paths until migration.
The target Responsibility model supersedes its free-form role/compatibility-key use prospectively,
without recasting old records.

## Derived and durable Case Work

PAIM derives work when authoritative state alone answers that work is ready or waiting and no
request, assignment, due point, handoff, or coordination history must persist. It creates durable
Case Work only when that coordination fact must survive sessions or participants.

A Work Item preserves exact Case/context, obligation, Responsibility, requester and legitimate
request basis, reason/prerequisite, optional due/expected time, coordination state, required result
contract, result Version, return relationship, and history. Work completion only links the
substantive governed result. It cannot create Applicability, assessment adequacy, reliance,
Decision, Completion Acceptance, Trigger Determination, or another domain judgment.

If authoritative context changes, commit revalidation fails closed. Work is explicitly cancelled
or superseded and a new exact Work Version/identity is created when needed; it is never silently
retargeted. PAIM does not add arbitrary task trees, progress percentages, inferred priority,
authoritative chat, or duplicated domain status.

## Continuing review and timing

Event-driven and time-driven review share an accountable determination path but have different
origins:

- an event occurrence can become an exact Trigger through the existing provenance and Trigger
  Determination contract; and
- a review point becoming due creates derived attention only. A practitioner beginning the review
  may establish an exact Trigger sourced from that Review Point; due time alone creates no Trigger
  or substantive conclusion.

The organization generally sets the **next planned review point**, subject to applicable governing
requirements and earlier events. The record names one exact Case/current Decision/Configuration
context, date/time or bounded window, purpose, rationale only when substantive, responsible review
planning Responsibility, establishment basis, effective/recorded time, and supersession or
cancellation history. It is a revisable next point, not a permanent cadence.

A **required review constraint** comes from an applicable policy, Authority, contract, Decision
condition, Boundary clause, or other governing source. It retains exact source Version,
Applicability, scope, operator (`by`, `not-before`, or bounded window), time, and history. All
applicable constraints are conjoined. Compatible deadlines yield their exact intersection; an
empty or indeterminate intersection is explicit conflict, not a selected winner. A planned point
may be earlier where permitted but cannot defeat a stricter requirement.

Arrival never implies stale Evidence, material change, Reassessment, Decision invalidity,
priority, or outcome. Review may record no material follow-up, focused work, analytical refresh,
or formal Reassessment. A Decision change still requires the separate authority path.

Case/Decision-level timing plus bounded due/expected points on existing Learning and Work is
sufficient initially. PAIM need not schedule every measure. Realized Value and Risk/control
questions may mature on different horizons and remain independent.

## Readiness, assessment adequacy, and reliance recommendation

Analytical readiness has genuine meaning: the producing Assessor states that one exact Value or
Risk Input is complete enough for independent adequacy/use review. Retain the attributed event, but
let the practitioner action be **Finish assessment**. That action can atomically finalize the exact
candidate Version and record readiness. A material later edit creates a successor Input Version;
the predecessor readiness remains historical and the successor is not ready until finished.

Prospectively, **assessment adequacy for decision use** replaces the advocacy-prone Fitness framing.
The neutral accountable judgment asks whether the exact assessment is faithful, materially complete,
proportionate, appropriate to its bounded use, and transparent about limitations and uncertainty.
Its smallest outcome model is adequate, not adequate, or indeterminate, with explicit limitations
and rationale. A favorable or unfavorable Value/Risk conclusion can be adequate. Evidence
Applicability remains a distinct prerequisite and judgment.

Adequacy establishes eligibility, not reliance. An exact reliance designation remains genuine
because it identifies and freezes the lane assessment actually used for the Case and preserves the
basis for Integration and Decision reconstruction. With one adequate candidate, **Complete Value
review** or **Complete Risk review** may atomically record separate adequacy and reliance facts only
when the same Actor holds both exact Responsibilities and all guards pass. With multiple adequate
candidates, explicit choice and material candidate dispositions are mandatory. Uniqueness never
auto-selects.

Value and Risk adequacy and reliance remain independent. Adequacy is not reliance; reliance is not
Decision; readiness is neither. Legacy Fitness and Acceptance/Selection records retain their
original names and semantics. The
[Assessment Adequacy & Reliance Necessity Review](PAIM_ASSESSMENT_ADEQUACY_AND_RELIANCE_NECESSITY_REVIEW.md)
records the complete evaluation.

## End-to-end composition examples

### Harborlight current stopping point

```text
exact Applicability prerequisite
  -> Responsibility resolution returns vacancy
  -> authorized Responsibility assignment
  -> durable contextual Work Item and handoff
  -> owning Evidence Applicability command records the result
  -> Work links that exact result and returns to the assessment
  -> the remaining independent prerequisite stays visible
```

Assignment makes no Applicability judgment and grants no Decision Authority. The live Harborlight
Case remains unchanged by this proposal.

### Time-driven review

```text
next planned Review Point becomes due
  -> derived unranked attention
  -> assigned review Responsibility / durable Work only if coordination is needed
  -> practitioner establishes exact review Trigger and determines significance
  -> no follow-up, focused Value/Risk work, or Reassessment as justified
  -> current Decision Confirmation through its governing accountability/authority path,
     or an authorized successor path
  -> next Review Point may be established for the resulting exact context
```

### Required review earlier than plan

An applicable required-by constraint and a later planned point remain separate. The combined view
shows both and flags that the plan does not satisfy the requirement. It does not move the Decision,
invent a priority score, or choose another date silently.

### Event before planned review

The event proceeds through exact source provenance and accountable Trigger Determination. If it
starts earlier review, the future Review Point is explicitly retained, cancelled, or superseded
for its exact context; history is not deleted and the event does not inherit the Review Point's
meaning.

### Same Actor, multiple Responsibilities

Each Responsibility and governed result remains separate even when one Actor holds all of them.
The product may reduce repeated sign-in and context selection but may not collapse attribution,
Value/Risk records, review acts, or authority.

## Product-to-normative traceability

| Concept | Practitioner problem / product behavior | Authoritative fact to persist | Derived/read-side only | Accountability or authority | History preserved | Do not expose ordinarily |
|---|---|---|---|---|---|---|
| Participant | Know who is involved without inventing membership from access | no separate Participant record; existing Actor and exact Case relationships/acts | access-filtered current/historical participant composition | each source relationship keeps its own basis; no authority from participation | every source relationship and attributed act | directory/access resolution machinery |
| Case continuity | Keep one bounded question coherent across Decisions and review | Case Versions and continuity/closure/supersession determinations | current management position and phase wording | Case-continuity Responsibility; Decision Authority where operation/conditions change | every prior status, Decision, Configuration, and successor link | universal lifecycle machinery |
| Case practical role | Know broadly who coordinates, assesses, or reviews | exact Actor-Case-role relationship | participant list and labels | assignment basis; no substantive authority | effective interval and predecessor/supersession/withdrawal | role as a permission bundle |
| Responsibility | Know who owns one exact obligation | Responsibility ID/Version, obligation signature, context, Actor/mechanism, assignment basis, and interval | vacancy/conflict explanation and compact labels | exact assignment accountability; authority separate | reassignment, delegation, supersession, expiry, and cited-result history | compatibility keys or raw target IDs |
| Derived work | See legitimate work without task duplication | no new Work record; exact source records remain authoritative | ready/waiting/actionability from exact sources | governing domain checks at action | source family history only | synthetic task status |
| Durable Case Work | Preserve request, handoff, result, and return | Work ID/Version, exact context, request/assignee, state, result, and return | practitioner summary and notifications | request/assignment basis; domain authority still separate | every assignment, wait, result, cancellation, and successor | workflow graph or command names |
| Planned review point | Let the organization choose the next reconsideration point | exact Review Point Version and context | due attention | review-planning Responsibility; Decision Authority only if changing a Decision condition | every prior point, change, cancellation, supersession, and review link | scheduler mechanics |
| Required review | Prevent a plan defeating governing time constraints | exact constraint/source/Applicability/operator/window | combined compliant/conflict view | governing source authority and Applicability | correction, supersession, withdrawal, and prior applicability | opaque winner or compliance score |
| Analytical readiness | Finish an assessment for independent adequacy review | exact Input Version and attributed readiness event | plain-language progress | producing Responsibility | predecessor readiness and successor-on-edit chain | backend `ready` transition |
| Assessment adequacy | Decide neutrally whether the exact assessment may enter the bounded management decision | exact adequacy outcome, Input/use/information basis, limitations, rationale, and time | natural adequacy explanation | adequacy-review Responsibility; no Decision Authority | every review, correction, and successor basis | legacy Fitness vocabulary or a mechanical checklist |
| Reliance designation | Identify the exact adequate lane assessment the Case will use | exact lane reliance, adequacy basis, candidate dispositions, and time | combined one-candidate review confirmation | reliance Responsibility; no Decision Authority | freeze, reuse, non-selection, withdrawal, and supersession | Selection/freeze machinery |
| Current management position | Understand what holds now | existing exact source records; no new master record | access-filtered exact composition | none created by presentation | all source Versions remain unchanged | a universal Case score/status |
| Historical view | Understand what was known and decided then | existing exact records, relationships, effective/recorded time | Decision-bound reconstruction | authorized access only | exact Decision basis and later facts remain temporally separate | UUID/version machinery in ordinary view |

## Prospective normative boundaries

- Practical role, Responsibility, access, software permission, accountability, and substantive
  authority remain distinct.
- Work never substitutes for its result or silently completes another prerequisite.
- Review timing creates attention, never a conclusion.
- Carry-forward means continued reliance on exact still-eligible state, not copying or presumption.
- Historical experience is information requiring current Applicability/relevance judgment.
- Current management position remains a rebuildable composition.
- No universal Case lifecycle, review frequency, score, priority, Selection, or automated Decision.

## Gates

The exact coordinated revisions are listed in the
[Downstream Specification Plan](PAIM_DOWNSTREAM_SPECIFICATION_PLAN.md). No specification edit or
implementation begins until this integrated target is independently accepted and a separately
bounded issue authorizes that gate.
