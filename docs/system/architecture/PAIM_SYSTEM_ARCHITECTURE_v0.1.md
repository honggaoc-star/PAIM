# PAIM System Architecture v0.1

## Status

Provisional complete-system architecture for **Practical AI Management (PAIM)**.

This document defines the system-level target above the validated PAIM analytical method and practitioner package and below any specific software implementation.

**Governing artifacts**
- `PAIM_MINIMUM_MANAGEMENT_CASE_v0.3.md`
- `PAIM_PRACTITIONER_PLAYBOOK_v0.2.md`
- `PAIM_MINIMUM_PRACTITIONER_TEMPLATES_v0.2.md`
- `PAIM_PHASE_II_VALIDATION_CHECKPOINT_v0.1.md`

> **The PAIM system defines what practical AI management must do. The PAIM platform will define how software implements those requirements.**

This document does not prescribe a database, programming language, UI framework, deployment model, or software architecture.

Cross-cutting authoritative-record, boundary, lifecycle-transition, decision-authorization, and interim-reassessment integrity semantics are governed by `../specifications/PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`. That specification hardens this architecture without changing its analytical or practitioner meaning.

Gate 1 of the accepted Normative Model Redesign adds a prospective common integrity and
semantic-era boundary to that specification and to this architecture. Accepted Gates 2/4 and 3
define prospective Responsibility/Case Work and continuing-Case semantics, while existing v0.1
consumers remain controlling until separately authorized implementation/migration cutover. This
architecture does not predefine physical payloads, workflows, or substantive judgments; §20D
records the accepted Gate-5 logical architecture and §20E records the accepted Gate-6 logical
architecture.

## 1. System Purpose

PAIM is an integrated management system for making, implementing, observing, and revisiting decisions about bounded AI-enabled configurations.

Its central question is:

> **Given what is known now, what should management do with this AI-enabled configuration, under what operating boundary, why, what action should follow, what should be learned, and what would cause the decision to change?**

PAIM integrates value, risk, constraints, uncertainty, management judgment, intervention, learning, and reassessment.

## 2. Complete-System Flow

```text
Management Entry
      |
      v
Managed AI Configuration
      |
      v
Evidence / Authority
      |
      +--------------------+
      |                    |
      v                    v
Value Management      Risk Management
      |                    |
      +---------+----------+
                |
                v
         PAIM Integration
                |
                v
       Management Judgment
                |
                v
           Intervention
                |
                v
            Operation
                |
                v
      Observation / Learning
                |
                v
          Reassessment
                |
                +-----------> revised configuration / decision
```

The system must preserve traceability across this cycle.

## 3. Core Architectural Principles

### 3.1 Manage configurations, not abstract AI

The primary management object is a bounded configuration consisting, as relevant, of AI capability, task/activity, workflow, users, information/data, AI authority, human authority, controls, escalation/review, provider/model, operating conditions, dependencies, and exclusions.

A material configuration change may require new evidence and a reopened or new decision.

### 3.2 Preserve analytical independence

Value Management and Risk Management remain distinct contributing capabilities. Neither should be rewritten merely to make integration easier.

Their PAIM-facing interfaces preserve:

1. Finding
2. Boundary
3. Uncertainty
4. Implication
5. Provenance

### 3.3 Make management judgment explicit

PAIM does not replace accountable judgment with a universal score. The system must show evidence relied upon, alternatives, interactions, uncertainty, operating boundary, decision authority, and rationale.

### 3.4 Controls can affect value and risk

A control may reduce exposure, consume cost/time, preserve quality, enable value, or create value. PAIM therefore represents **Control Dependency**, not merely a control inventory.

### 3.5 Uncertainty is decision-relative

- **Accepted uncertainty:** unknowns compatible with the current bounded decision.
- **Decision-Limiting Uncertainty:** unknowns preventing a stronger, broader, or different decision.

### 3.6 Authority is not invented

Where a decision depends on missing governing authority:

> **AUTHORITY UNRESOLVED**

### 3.7 Learning is decision-specific

`missing evidence → blocked/conditional decision → evidence to generate → decision that may change`

### 3.8 Decisions are revisable

A PAIM decision is a current management judgment, not permanent approval.

## 4. Major System Capabilities

### 4.1 Management Entry and Intake

Bring an AI-management issue into PAIM as a decision problem.

Required functions include opening a case, identifying why attention is required, assigning a case owner, identifying decision authority or an authority gap, recording relevant horizon, linking prior cases/configurations, and recording the trigger.

**Primary record:** PAIM Case Record.

### 4.2 Managed Configuration

Define exactly what is being managed and preserve configuration history.

**Primary record:** Managed Configuration Record.

A materially changed configuration must not silently inherit evidence from an earlier configuration.

### 4.3 Evidence and Authority Management

Register evidence/provenance, link evidence to findings, record governing authority and unresolved authority, and preserve context/version.

**Primary records:** Evidence Record, Authority Record, Authority Gap Record.

Development artifacts are not the eventual practitioner interface. Relevant evidence should be surfaced in context.

### 4.4 Value Management Capability

Establish organizational value, boundary, uncertainty, implication, and provenance.

**Primary record:** Value Management Input.

Detailed value analysis may reside in AIVM or another compatible capability.

### 4.5 Risk Management Capability

Establish adverse pathways, controls, residual exposure, boundary, uncertainty, implication, and provenance while remaining independent of the Value conclusion.

**Primary record:** Risk Management Input.

### 4.6 PAIM Decision Integration

Preserve contributing implications; identify constraints and authority gaps; analyze Control Dependencies; classify uncertainty; establish Integrated Operating Boundary; generate alternatives; analyze Reinforcement, Conflict, Constraint, and Configuration Trade-off.

**Primary record:** PAIM Integration Record.

### 4.7 Management Judgment and Authorization

Record decision/action, operating state, Integrated Operating Boundary, rationale, evidence relied upon, uncertainty, conditions, decision authority, and date.

**Primary record:** Management Decision Record.

Possible operating states include experiment, bounded continuation, targeted scale, institutionalized use, broader deployment, controlled transition/redesign, suspended, and discontinued.

Phase II indicates that operating-state semantics—especially continuation vs. institutionalization—require further practitioner validation.

### 4.8 Intervention and Execution

Translate judgment into operational action: what changes, owner, effective configuration, controls, prohibited activities, escalation/fallback/remediation, and implementation status.

**Primary record:** Intervention Record.

### 4.9 Observation, Learning, and Reassessment

Observe value, risk, control performance, and boundary adherence; manage learning items and reassessment triggers; reopen decisions when needed.

**Primary records:** Observation Record, Learning Item, Reassessment Trigger, Reassessment Record.

### 4.10 Portfolio / Management View

Allow management to see multiple AI configurations: current states, unresolved authority, Decision-Limiting Uncertainty, pending interventions, reassessments, boundary breaches, evidence maturity, control dependencies, and concentrations.

**Primary construct:** PAIM Management Register / Portfolio View.

This capability requires further system-level design.

## 5. Core Information Model

```text
AI Management Case
    |
    +-- Managed Configuration
    +-- Evidence Records
    +-- Authority Records / Gaps
    +-- Value Management Input
    +-- Risk Management Input
    +-- PAIM Integration Record
    +-- Integrated Operating Boundary Snapshot
    +-- Management Decision
    +-- Decision Authorization Basis
    +-- Intervention(s)
    +-- Learning Item(s)
    +-- Observation(s)
    +-- Reassessment Trigger(s)
    +-- Interim Operating Disposition(s)
    +-- Reassessment / Successor Decision

All authoritative families
    +-- immutable Record/Version identity and semantic-contract identity
    +-- exact context sets where adopted by the owning contract
    +-- dual-time history and exact relationships
    +-- family-owned selection yielding one / absent / conflict
    +-- access-filtered, non-authoritative read composition
```

The implementation should preserve relationships and history rather than overwrite prior decisions.

## 6. Case Lifecycle

The prospective Case-level continuity vocabulary is:

```text
OPEN <---- explicit accountable reopening ---- CLOSED
  |
  +---- exact named successor ----> SUPERSEDED (terminal predecessor)
```

`OPEN` is continuing eligibility for management, not a universal active-work or operating phase.
`CLOSED` requires no current operation and no remaining required PAIM management obligation.
`SUPERSEDED` routes prospective management to one named successor. An explicit reopening event
returns the same coherent subject from `CLOSED` to `OPEN`; `REOPENED` is not a long-lived status.

Decision, operation, Intervention/action, Learning, Value/Risk refresh, Trigger/Reassessment, and
Work states coexist independently. Current management position is a non-authoritative composition;
no subordinate condition becomes a universal Case phase.

The owning substantive rules are in `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`, §3A and the common
integrity/transaction rules are in
`PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §5A. The legacy v0.1 phase model and its
Transition Events remain controlling before explicit cutover and immutable history afterward.

## 7. Decision Boundary Model

```text
Managed Configuration
        |
        +-- Value Boundary
        +-- Risk Boundary
        +-- Constraints / Authority
        +-- Control Dependencies
        |
        v
Integrated Operating Boundary
```

The Integrated Operating Boundary is the actionable management boundary.

Every boundary used by an authorized Decision is preserved as the immutable hybrid Boundary Snapshot defined in `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §4, combining structured integrity references with narrative human-judgment clauses.

## 8. Authority Model

Authority records may represent organizational policy, contractual requirements, law/regulation, safety requirements, data restrictions, delegated authority, or mandatory oversight.

Where authority is missing:

`AUTHORITY UNRESOLVED → decision affected → authority/evidence needed → can bounded decision proceed?`

Absence of authority evidence must not become implied permission.

Every authorized Decision must retain the auditable Decision Authorization Basis defined in `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §6. `DECISION AUTHORITY UNRESOLVED` is an Authority Gap classification and blocks authorization of the affected Decision.

## 9. Control Dependency Model

For each material control, the system should be capable of recording:

- control identity;
- configuration relationship;
- risk function;
- value function/burden;
- Value dependence;
- Risk dependence;
- boundary status;
- reassessment consequence if changed;
- observed effectiveness where available.

## 10. Uncertainty Model

Each material uncertainty should support description, provenance, classification, decision affected, operating state affected, evidence needed, learning plan, and reassessment relationship.

Classification may change when the proposed decision changes.

## 11. Alternatives

For each alternative record:

- configuration;
- operating state;
- Value implication;
- Risk implication;
- controls;
- evidence maturity;
- uncertainty created/resolved;
- authority implications;
- management disposition.

Evidence maturity may use simple states such as demonstrated, supported, plausible, and unknown.

## 12. Management Decision Model

A PAIM decision should remain reconstructable later.

Minimum content includes case/configuration, decision/action, selected operating state, Integrated Operating Boundary, rationale, Value and Risk evidence relied upon, constraints/authority, uncertainty, alternatives, conditions/limits, decision authority/date, intervention linkage, and reassessment linkage.

Historical decisions should remain immutable or versioned.

Every substantive amendment is an authorized successor Decision version; no authorized Decision or Boundary Snapshot is edited in place.

## 13. Learning and Reassessment

```text
Missing Evidence
      |
Blocked / Conditional Decision
      |
Evidence Generation
      |
Observation
      |
Reassessment
      |
Decision May Change
```

Triggers may include incidents, material errors, value change, control failure/change, provider/model change, scope/autonomy change, data change, operating-condition change, authority resolution/change, completed learning experiment, or scheduled review.

## 14. Practitioner Experience Architecture

The practitioner-facing system should **not expose the development repository as the operating interface**.

A representative experience:

```text
1. Open/review AI management case
2. See exact managed configuration
3. See evidence and authority relevant to the current decision
4. Review Value Management Input
5. Review Risk Management Input
6. Inspect interactions and alternatives
7. Establish Integrated Operating Boundary
8. Make/approve management judgment
9. Assign intervention
10. Observe signals/learning
11. Reassess when triggered
```

Definitions and guidance should be surfaced contextually. Practitioners should not need to know which historical Markdown document originally defined a concept.

## 15. Human Validation Architecture

Formal human validation is intentionally deferred until an integrated practitioner-facing system/prototype exists.

> **Requiring humans to navigate development artifacts would confound PAIM usability with document-navigation and reconstruction burden.**

The eventual test should evaluate observable system behavior:

`controlled inputs/scenario → PAIM platform → outputs/boundaries/decisions/questions/learning/reassessment`.

Human testers need not understand PAIM's development history.

## 16. Behavioral / Black-Box Validation

Potential scenario families include:

- hold Value constant and vary Risk;
- hold Risk constant and vary Value;
- change a control affecting both;
- increase uncertainty without changing core evidence;
- propose institutionalization instead of continuation;
- introduce unresolved authority;
- change configuration enough to invalidate prior evidence;
- create Type A recommendation conflict;
- create Type B configuration trade-off;
- remove material evidence;
- change provider/model;
- exceed human-review capacity;
- resolve previously Decision-Limiting Uncertainty.

Human evaluators can study whether the system narrows boundaries appropriately, preserves conflicting conclusions, asks for human judgment at the right point, exposes unresolved authority, avoids unsupported stronger decisions, generates decision-specific learning, reopens decisions after material change, and behaves coherently across related scenarios.

This provides a basis for systematic input/output testing and surrogate behavioral understanding without requiring testers to reconstruct PAIM's internal development artifacts.

## 17. System vs. Platform Boundary

### `system/`

Defines **what PAIM must do**: capabilities, records, states, relationships, decision logic, authority, evidence, learning, reassessment, and expected behavior.

### `platform/`

Will define **how software implements PAIM**: application architecture, persistence, APIs, UI, identity/permissions, notifications, reporting, deployment, and technical testing.

Software design should implement the management system rather than redefine it accidentally.

## 18. Roles and Accountability

The system should support, without assuming every organization separates them physically:

- case owner;
- Value evaluator;
- Risk evaluator;
- subject-matter contributor;
- decision authority;
- intervention owner;
- evidence/authority owner;
- reviewer/auditor;
- system administrator.

Detailed role and permission design remains a system/platform specification task.

## 19. Minimum System Outputs

A complete PAIM system should be able to produce or display:

1. current AI-management register;
2. exact managed configuration;
3. Value Management Input;
4. Risk Management Input;
5. evidence and authority provenance;
6. Integrated Operating Boundary;
7. alternatives and interaction analysis;
8. management decision/rationale;
9. intervention status;
10. unresolved authority;
11. accepted and Decision-Limiting Uncertainty;
12. learning items;
13. observation status;
14. reassessment triggers;
15. decision/configuration history.

## 20. System Integrity Requirements

The eventual implementation should preserve:

- traceability;
- version/history;
- configuration/evidence binding;
- analytical independence;
- explicit authority gaps;
- non-destructive decision history;
- provenance of practitioner-designed actions;
- boundary visibility;
- reassessment linkage;
- per-Version semantic-contract identity for explicitly adopting prospective families;
- immutable typed exact context sets without inferred substantive meaning;
- access-filtered, deterministic, non-authoritative read composition;
- dual-time and exact Decision-bound cross-era reconstruction;
- all-or-nothing semantic transactions with exact replay/idempotency;
- explicit legacy adapters and no silent prospective-to-legacy fallback;
- deterministic scope/time current-record selection and explicit conflict;
- immutable Integrated Operating Boundary Snapshots;
- auditable Decision Authorization Basis;
- time-bounded authorized Interim Operating Dispositions;
- completed-Reassessment confirmation-or-successor outcome.

Detailed technical controls are deferred to platform architecture.

## 20A. Gate-1 common integrity and semantic-era architecture

### 20A.1 Logical placement

The common integrity layer sits below substantive record-family contracts and above persistence or
transport implementation:

```text
Practitioner actions and read experiences
                 |
                 v
Later substantive contracts (Gates 2–6)
  Responsibility | Case continuity | Case Work | Review Timing |
  assessment adequacy/reliance | quantitative Value/Risk
                 |
                 v
Common integrity and semantic-era contract
  semantic identity | authoritative envelope | exact context set |
  selector outcome | dual-time reconstruction | semantic transaction |
  compatibility/access/read-composition boundaries
                 |
                 v
Platform persistence, audit, access enforcement, APIs, and projections
```

This is logical ownership, not a prescribed service topology. A platform may implement the
mechanisms in one module or several components only if observable semantics remain identical.

### 20A.2 Semantic-contract boundary

Every adopting prospective Version/event binds an exact Semantic Contract ID/Version. The logical
semantic-contract catalog records its normative owner, supported record families, adapters, and
allowed successor transitions. Historical readers interpret each fact under its bound contract.
No deployment version, timestamp, or “latest” rule changes meaning or chooses a winner.

Legacy compatibility adapters form an explicit boundary. They are versioned, source-labelled,
read-safe, and non-authoritative unless a later substantive contract grants one exact effect. A
failed prospective path cannot fall back to a legacy path.

### 20A.3 Shared integrity mechanisms

- **Authoritative envelope:** conditional common identity, semantic contract, time, attribution,
  provenance, relationship, checksum, access, and eligibility vocabulary. The owning family uses
  only what it semantically needs.
- **Exact context set:** immutable typed references to exact Record Versions; unordered by default,
  canonically represented, access-filtered, and never a source of implied substantive meaning.
- **Selector framework:** a family-supplied scope, eligibility predicate, temporal basis, and
  authority/coordination relations produce exactly one, explicit absence, explicit conflict, or an
  explicitly permitted compatible set. The common layer supplies no winner.
- **Temporal reconstruction:** effective-at and known-at queries plus exact Decision-bound
  reconstruction preserve later corrections/observations as later knowledge.
- **Semantic transaction boundary:** one natural action may atomically commit several separately
  identified facts with one exact guard basis, idempotency, audit linkage, and zero partial mutation.
- **Read composition boundary:** current-position, attention, participant, derived-work, and
  historical views are deterministic access-filtered compositions with exact source traceability,
  not master records or command authority.

### 20A.4 Access ordering

Access/non-disclosure is enforced before context construction, selection visible to a caller,
counting/grouping, read composition, historical reconstruction, or command use. Hidden records do
not leak through counts, conflict/blocker labels, participant/work lists, timing hints, or output
shape. Technical/audit detail requires explicit authorization. Gate 1 changes neither identity nor
session/deployment architecture.

### 20A.5 Modules deferred by Gate 1

At Gate-1 acceptance, the architecture reserved integration points but did not define:

- Responsibility taxonomy, assignment, or authority (Gate 2);
- Case continuity states/determinations (Gate 3);
- Case Work payload, coordination states, result, or return (Gate 4);
- Planned Review Point and required-review constraints (Gate 5); or
- readiness, assessment adequacy, reliance, or quantitative Value/Risk payloads (Gate 6).

Gates 2 and 4 adopt the common mechanisms in §20B, Gate 3 in §20C, Gate 5 in §20D, and Gate 6 in
§20E. Every adopted module defines its own context roles, eligibility, conflict/coexistence,
authority/accountability, access, temporal, migration, and transaction rules. Existing v0.1
families continue unchanged until a separately accepted consumer cutover.

### 20A.6 Non-authoritative product projections

Future `current management position`, `What needs me?`, participant, derived work, and “Case as it
stood” experiences use the read-composition boundary. Their source manifests, query/rule Versions,
watermarks, and access context make them reproducible. Cache, export, label, notification, queue
position, or display order creates no priority, completion, responsibility, authority, currentness,
or substantive fact. A command reconstructs its own exact authoritative basis.

## 20B. Responsibility and Case Work architecture

### 20B.1 Logical capabilities

The accepted Gate-2/4 normative contract resolves two previously deferred logical capabilities:

- **Responsibility and practical-role governance** owns controlled obligation signatures, exact
  assignment bases, delegation/reassignment/supersession, and one/vacancy/conflict resolution;
- **Case Work coordination** owns the derived-versus-durable boundary, exact handoff context,
  bounded coordination state, governed-result link, and return relationship.

They depend on Gate-1 semantic-contract identity, exact context sets, family selectors,
transactions, reconstruction, and access ordering. Substantive domain capabilities continue to own
their results. Decision Authorization, Completion Acceptance, and activation authority remain
separate authority paths.

### 20B.2 Practitioner and authority boundary

Ordinary Case staffing presents Case Coordinator, Assessor, and optional Reviewer. Those practical
roles are orientation metadata, not permission or obligation bundles. Administrator remains outside
ordinary Case staffing; subject-matter expertise is contextual participation/Work. The architecture
does not create standing Applicability Owner, Decision Maker, or Implementation Owner roles.

The same Actor may occupy multiple roles and Responsibilities, including Value and Risk, while
each obligation and result remains independently attributable. Assignment requires a separately
valid Responsibility Assignment Basis; Case Coordinator orientation alone is insufficient.

### 20B.3 Work is coordination, not workflow authority

Most available/waiting work remains an access-filtered read composition. A durable Work Item exists
only when request, cross-person assignment, handoff, due/expected point, waiting history, result
link, or return must survive. It is not a generic workflow engine and does not create a substantive
result, authority, priority, percentage complete, task tree, or authoritative chat.

Review and commit revalidate exact context. A stale Work Item fails closed and remains historical;
it cannot retarget to a current Version. Result linking returns to the originating context and
recomposes independent prerequisites independently.

### 20B.4 Semantic-era and implementation boundary

There is no global cutover. Each adopting consumer requires a separately accepted implementation
and migration contract naming the semantic contract, obligation kind, cutover boundary, bounded
legacy adapter, and cross-era rule. Legacy Role Assignment history is never rewritten. A failed
prospective path never falls back.

This architecture section authorizes no module, schema, migration, persistence, UI, notification,
or Harborlight mutation. Physical design remains a later implementation-readiness decision.

## 20C. Continuing Case and Configuration continuity architecture

### 20C.1 Logical ownership

The accepted Gate-3 contract adds two prospective authoritative families:

- **Case Continuity Status/Event** owns exact `OPEN`, `CLOSED`, or `SUPERSEDED` continuity for one
  Case and time; and
- **Case Continuity Determination** owns accountable same/new Case, closure, reopening, and
  supersession judgments with exact changed basis and context.

Case Lifecycle owns status meaning, determination kinds/outcomes, closure guards, reopening, and
terminal supersession. Managed Configuration owns Configuration identity, materiality, lineage,
governing selection, and exact owning-Case relationships. Gate-1 integrity supplies semantic-era,
context, selector, transaction, access, and reconstruction mechanics. Gate-2/4 Responsibility/Work
supplies exact accountability and no-retarget behavior.

### 20C.2 No universal workflow phase

An `OPEN` Case may simultaneously operate under a Decision, execute actions/Interventions, obtain
Learning, refresh independent Value and Risk, handle information, and undergo Reassessment. Those
states remain in their owning records and compose into practitioner explanation. They do not
advance one universal lifecycle, overwrite each other, or become a master management-position
record.

`Current management position` is an access-filtered non-authoritative composition of exact sources,
rule Version, effective/known-at basis, and watermark. It creates no continuity, priority,
authority, closure, or command basis.

### 20C.3 Same/new Case and Configuration lineage

Case identity is the bounded materially coherent business use/management subject, not provider,
model, title, inventory identity, ownership, or shared information. Where exact accepted rules do
not mechanically establish continuity, a Case Continuity Determination supplies the accountable
same/new outcome. A materially different business use requires a new Case.

A successor Configuration Version or identity may remain within the same Case only when its
bounded subject remains coherent. No successor silently retargets historical Evidence,
Value/Risk, Decision, Responsibility, Work, Intervention, Reassessment, or Learning. A new Case and
any predecessor/successor relationship transfer none of those facts by inference.

### 20C.4 Closure, reopening, and terminal behavior

Stopping operation does not close a Case while required action/retirement, acceptance, Learning,
Trigger coverage/Reassessment, Authority/existing review, Work, or another management obligation
remains. Closure is an atomic accountable determination/status command over an exact guard manifest.

Reopening is an explicit accountable continuity event that appends `OPEN` and preserves closure;
it revives no subordinate record. Supersession atomically names one successor and makes the
predecessor terminal for new substantive work. All failures commit zero intended facts.

### 20C.5 History, cutover, and implementation boundary

Decision-bound reconstruction always starts from the Decision's exact Configuration, inputs,
Integration, Boundary, and Authorization Basis. Effective-at/known-at views preserve Case status,
legacy phase, Configurations, Responsibility/Work, and subordinate facts without hindsight rewrite.

There is no global cutover or automatic phase-to-status mapping. Each adopting Case/population needs
a separately accepted initialization/migration contract; legacy phase events remain exact and a
failed prospective path never falls back. This architecture authorizes no code, schema, migration,
UI, scheduler, notification, deployment, analytics, or Harborlight mutation.

## 20D. Continuing Review and Review Timing architecture

### 20D.1 Logical ownership and separation

The accepted Gate-5 contract adds three prospective authoritative families:

- **Planned Review Point** owns one optional bounded next review point and its revision history;
- **Required Review Constraint** owns one normalized applicable governing timing requirement; and
- **Review Episode** owns one bounded practitioner review and its exact completion basis.

Reassessment owns their substantive contract and practitioner-started handoff into existing
Trigger Determination/Reassessment. Evidence/Authority owns source Applicability and exact claim
comparability. Integration/Decision owns any timing that is Decision/Boundary content and every
unchanged/successor Decision path. Intervention/Learning owns independently justified Learning and
action horizons. Responsibility/Work owns accountable planning, normalization, review completion,
and coordination. Integrity owns record mechanics, selectors, intersection, atomicity,
reconstruction, semantic era, and access.

### 20D.2 Attention and orchestration boundary

Event-driven and time-driven sources meet only through an exact Trigger established by a
practitioner or later accepted governed mechanism. Reaching or missing a point/constraint creates
an access-filtered attention composition, not a Trigger, Reassessment, stale-Evidence result,
Decision judgment, suspension, violation, priority, or outcome. Required windows are a mechanical
intersection of every applicable exact constraint, not a winner chosen by source hierarchy or
strictness.

Review Work is coordination and cannot substitute for its source, Trigger Determination,
Value/Risk assessment, Reassessment, Decision Confirmation, successor Decision, or next Review
Point. A no-change/focused review and a formal Reassessment remain distinguishable. Independent
Value and Risk remain separate even when both are reviewed in one episode.

### 20D.3 Authority, transactions, and history

Planning Responsibility establishes accountable planning only. Required-constraint normalization
requires its own Responsibility and source/Applicability. Decision timing changes, unchanged
Confirmation, and successor Decisions retain their separate exact authority paths. No role,
calendar, access, source authority, or software permission crosses those boundaries.

The same natural confirmation may complete an episode, confirm a Decision, and establish a next
point only as separately valid intended facts in one Gate-1 semantic transaction. Review and commit
reconstruct exact current context and fail closed on stale/conflicting basis. Effective-at and
known-at views preserve every point, constraint, intersection, Trigger, episode, carry-forward,
Work/Reassessment, Decision relationship, and later knowledge without hindsight rewrite.

### 20D.4 Physical and later-gate boundary

This logical architecture chooses no persistence aggregate, table, endpoint, scheduler, worker,
reminder, notification, job queue, UI, deployment, or analytics design. It performs no consumer
cutover and synthesizes no prospective fact from legacy scheduled-like records. Gate 6 still owns
assessment adequacy, reliance, and quantitative Value/Risk payloads. Architecture/readiness and
implementation remain separately authorized, and Harborlight remains unmodified.

## 20E. Value/Risk assessment, adequacy, reliance, and quantitative architecture

### 20E.1 Logical ownership and lane independence

The accepted Gate-6 contract adds independent prospective Value and Risk Assessment/Input,
Readiness Event, Assessment Adequacy Determination, Assessment Reliance Designation, and optional
Quantitative Claim capabilities. Value/Risk owns their substantive meaning and selectors.
Evidence/Authority owns exact information and Applicability. Responsibility/Work owns accountable
production, finish, adequacy review, reliance, and coordination. Integration/Decision consumes the
exact relied bases. Continuing Review owns refresh/carry-forward/comparison. Gate-1 integrity owns
record mechanics, semantic transactions, dual time, access, and cross-era preservation.

The lanes never share identity, completion, adequacy, reliance, quantitative claim, or outcome.
One Actor may serve both only through separately valid Responsibilities and facts. The architecture
contains no offset, net score, strongest-state result, universal Value/Risk/RWR/ROI/risk formula,
ranking, or automated Decision rule.

### 20E.2 Practitioner actions and authoritative facts

Practitioner expression may expose **Finish Value/Risk assessment** and **Complete Value/Risk
review** without requiring users to operate internal readiness states. Underneath, readiness,
neutral adequacy, explicit reliance, and Decision remain separate. One natural complete-review
confirmation may create separate adequacy/reliance facts atomically only for the exact one-candidate,
same-Actor/two-Responsibility case. Candidate uniqueness never derives reliance.

Prospective Integration readiness is a non-authoritative access-filtered composition of one exact
eligible relied Value chain and one exact eligible relied Risk chain for the same Configuration/use.
Review and commit revalidate each chain. Work coordinates but never creates an Assessment,
Readiness, Adequacy, Reliance, Integration, or Decision result.

### 20E.3 Optional quantitative capability

Quantitative Claims preserve exact semantic type separately from representation and retain only the
context material to interpretation: construct, value/range/distribution, unit/direction, scope,
period, baseline, coverage, Configuration, provenance, method, uncertainty, limitations, and dual
time as applicable. Known exact Case context may be composed without practitioner re-entry.

Numbers are optional. Qualitative inability to estimate is legitimate. Targets, estimates,
observations, thresholds, Risk estimates, and cost/resource measures remain distinct. Gate-5
comparison consumes exact comparable claims but produces no causality, materiality, adequacy,
reliance, priority, Decision error, acceptable Risk, or management outcome.

### 20E.4 History, cutover, and physical boundary

Legacy readiness, Fitness, Acceptance/Selection, freeze, Input, Integration, and Decision facts
retain original semantic-era meaning and names. No bulk rewrite, global cutover, newer-era winner,
or synthesized adequacy/reliance/claim exists. Each consumer needs a separately accepted cutover,
adapter, effective/knowledge boundary, migration, and recovery contract.

This logical architecture chooses no domain module, persistence aggregate, table, index, endpoint,
workflow, UI, analytics, or deployment design and authorizes no implementation, Harborlight
mutation, release, or tag. Gate 7 performs the coordinated architecture and implementation-
readiness review and decides physical placement without weakening Gates 1–6.

## 21. What Is Already Designed / Validated

### Substantially developed

- bounded management object;
- Value/Risk compact interface;
- analytical independence principle;
- Integrated Operating Boundary;
- Control Dependency;
- uncertainty classification;
- alternatives;
- interaction analysis;
- management judgment structure;
- intervention;
- decision-specific learning;
- reassessment logic;
- practitioner Playbook/Templates.

### Independently exercised

- compatible-input integration;
- Type B configuration conflict;
- Type A recommendation conflict;
- compact Value-input construction from fuller evidence;
- compact Risk-input construction from fuller evidence;
- frozen-input Decision Integration.

### Still incomplete at system/platform level

- management intake specification;
- durable case lifecycle;
- portfolio/register behavior;
- evidence/authority record model;
- configuration versioning rules;
- decision/intervention status model;
- reassessment workflow;
- role/permission model;
- system-level reporting;
- platform architecture;
- integrated prototype;
- human system validation.

## 22. Required Next Specifications

After this architecture is reviewed and frozen, develop implementation-independent specifications for:

1. PAIM Case Lifecycle
2. Managed Configuration Record
3. Evidence and Authority Model
4. Value/Risk Interface Record
5. PAIM Integration and Decision Record
6. Intervention and Learning Record
7. Reassessment Model
8. Management Register / Portfolio View
9. Roles and Accountability
10. System Behavioral Validation Strategy
11. System Record and Decision Integrity

These belong under `system/specifications/` or `system/testing/` as appropriate.

## 23. Platform Entry Gate

Do not begin detailed platform implementation merely because a `platform/` folder exists.

Platform design should begin when the system architecture and minimum core specifications are sufficiently stable to answer:

- what records exist;
- how they relate;
- what lifecycle/state transitions matter;
- what decisions require authority;
- what history must be preserved;
- what practitioners must see/do;
- what system behaviors must be testable.

## 24. Completion Baseline

This architecture changes the denominator for project completion.

The full PAIM target now includes:

1. Method architecture
2. Practitioner method
3. Independent component validation
4. Integrated system architecture
5. System specifications
6. Platform architecture
7. Platform implementation/prototype
8. System/behavioral testing
9. Human practitioner/system validation
10. Release consolidation

A new completion percentage should be calculated only after this architecture is accepted and the remaining specification/platform work is decomposed.

## 25. Current Architecture Decision

> **PAIM v0.3 remains the governing analytical method.**

> **Practitioner Package v0.2 remains frozen.**

> **Human validation is intentionally deferred to integrated system/platform testing.**

> **The next development focus moves from component validation to complete-system specification.**

## 26. Repository Placement

```text
400. Practical AI Management/
└── system/
    └── architecture/
        └── PAIM_SYSTEM_ARCHITECTURE_v0.1.md
```

Future system work:

```text
system/
├── architecture/
├── specifications/
└── testing/

platform/
```

## 27. Next Step

Gate 1 establishes the common integrity and semantic-era contract; the accepted accelerated
Gate-2/4 contract establishes prospective Responsibility and minimal Case Work; Gate 3 establishes
continuing Case and Configuration continuity; Gate 5 establishes continuing-review timing; and
Gate 6 establishes Value/Risk readiness, adequacy, reliance, and optional quantitative capability.
Gate 7 remains separately reviewed under the accepted
[Downstream Specification Plan](../../design/normative-model/PAIM_DOWNSTREAM_SPECIFICATION_PLAN.md).
No domain/persistence implementation or UI redesign begins from this architecture update.

## 28. Overall Conclusion

PAIM has moved beyond development of a single analytical method.

The validated analytical core now needs to become an integrated management system whose practitioner-facing behavior can eventually be implemented and tested without exposing humans to the development repository.

The architecture separates three layers:

> **Practitioner layer — how people perform PAIM**

> **System layer — what PAIM must do**

> **Platform layer — how software implements it**

This separation allows continued development now while reserving formal human validation for the stage where testers can evaluate PAIM through a coherent integrated system rather than fragmented internal artifacts.
