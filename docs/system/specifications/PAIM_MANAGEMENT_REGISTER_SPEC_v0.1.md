# PAIM Management Register Specification v0.1

## Status

Implementation-independent system specification for the **PAIM Management Register and Portfolio View**.

This specification derives from the PAIM system architecture and the completed single-case specifications for lifecycle, configuration, evidence/authority, Value/Risk interfaces, integration/decision, intervention/learning, and reassessment.

It defines how management should see and manage multiple AI configurations and PAIM cases together.

It does not prescribe dashboards, database technology, visualization libraries, reporting software, or UI layout.

**Normative cross-cutting contract:** `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md` governs the scope/time/current-selection and conflict semantics used to derive Register facts. The Register remains non-authoritative and must reproduce exact source-version links.

## 1. Purpose

Individual PAIM cases support individual management judgments.

The Management Register provides the organizational view across those cases.

It must help management answer:

> **What AI-enabled configurations are currently operating or proposed?**

> **What has management authorized for each one?**

> **Which configurations require attention now?**

> **Where are authority, evidence, control, intervention, or reassessment gaps accumulating?**

> **Where do multiple cases share dependencies such as providers, models, controls, reviewers, or capacity?**

The register is not merely an AI inventory. It is an active management view.

## 2. Register Principle

Conceptually:

```text
PAIM Case 001 ----+
PAIM Case 002 ----+
PAIM Case 003 ----+----> PAIM Management Register
PAIM Case 004 ----+              |
...                |              v
                                 Management Attention
                                 Portfolio Decisions
                                 Prioritization
                                 Reassessment
```

The register summarizes authoritative case records without replacing them.

## 3. Register Unit

The base Register unit is one stable **Register Concern Entry** under §38.2. A Configuration summary is the normal management-position grouping over those entries; it is not itself the concern identity.

A single Case may contain multiple concern entries and historical Configuration/Decision Versions. The Register must make the current management position clear without collapsing independent concerns. PAIM v0.1 represents independent concurrent governing Configurations through separately linked Cases; finalized non-governing work may appear only under §38.3.

## 4. Register Entry Identity

Exact concern identity fields:

- owning Case ID
- applicable Configuration ID, or permitted explicit absence/not-established context
- concern kind
- authoritative source family
- stable source Record ID

Exact rendering/basis fields include:

- selected source Version ID(s), including all incompatible candidates
- configuration title
- business/process area
- case owner
- decision authority
- current Decision ID/version or explicit absence/conflict
- current status
- last material update
- next required management action where applicable

## 5. Current Management Position

Each active entry should make visible:

- case lifecycle state;
- configuration status;
- AI operating state;
- current Integrated Operating Boundary;
- decision date;
- decision authority;
- current intervention status;
- reassessment status.

These states must not be collapsed into one generic traffic-light status.

## 6. Operating State View

The register should support visibility across operating states such as:

- experiment;
- bounded continuation;
- targeted scale;
- institutionalized use;
- broader deployment;
- controlled transition/redesign;
- suspended;
- discontinued.

Organizations may define additional states, but their meaning should remain explicit.

## 7. Boundary View

Management should be able to identify:

- what is currently authorized;
- major exclusions;
- required controls;
- capacity/operating conditions;
- material boundary changes;
- boundary breaches.

The register need not reproduce the full Integrated Operating Boundary in every row, but it should provide a concise summary and access to the authoritative boundary.

## 8. Value Position

The register may summarize the current Value position using fields such as:

- Value Input status;
- Value implication;
- Value Boundary;
- realized vs. expected value where relevant;
- material Value uncertainty;
- refresh-required status.

The register should not reduce Value to a single score unless a domain-specific measure is separately justified.

## 9. Risk Position

The register may summarize:

- Risk Input status;
- Risk implication;
- Risk Boundary;
- material residual pathways;
- required controls;
- material Risk uncertainty;
- refresh-required status.

The register should not reduce Risk to one generic score as the sole management representation.

## 10. Authority View

The register should make visible:

- established material authority;
- `AUTHORITY UNRESOLVED`;
- decision affected;
- authority owner;
- resolution status;
- whether the current bounded decision may proceed.

Unresolved authority requiring management attention should be discoverable across the portfolio.

## 11. Uncertainty View

The register should distinguish:

### Accepted Uncertainty

Unknowns compatible with current operation.

### Decision-Limiting Uncertainty

Unknowns blocking a stronger, broader, or different decision.

Management should be able to identify configurations with material Decision-Limiting Uncertainty and the decisions currently blocked.

## 12. Intervention View

The register should surface:

- interventions required;
- owner;
- status;
- blocked interventions;
- failed interventions;
- overdue interventions;
- target configuration;
- operational consequence of non-completion.

A decision should not appear fully implemented merely because it has been authorized.

## 13. Learning View

Management should be able to see:

- active Learning Items;
- decision/uncertainty addressed;
- owner;
- status;
- evidence-generation progress;
- decisions potentially unlocked;
- inconclusive/overdue learning.

This supports management of evidence generation rather than generic monitoring.

## 14. Reassessment View

The register should identify:

- reassessment due;
- trigger;
- date;
- interim operating disposition;
- analytical refresh required;
- decision pending;
- overdue reassessment;
- completed reassessment awaiting intervention.

The register should support a management reassessment queue.

## 15. Boundary Breach View

Material boundary breaches should be visible across the portfolio.

Minimum summary:

- configuration;
- breach;
- date;
- affected decision/boundary;
- immediate disposition;
- intervention;
- reassessment status.

Boundary breaches should not be hidden inside case notes.

## 16. Evidence Status View

The register may summarize:

- current Value/Risk input status;
- evidence refresh required;
- stale evidence;
- conflicting evidence;
- major learning evidence pending;
- configuration/evidence mismatch.

This is an evidence-management view, not a universal evidence-quality score.

## 17. Provider / Model Dependency View

Where provider/model dependency is material, the register should support cross-case identification of:

- shared provider;
- shared model/service;
- affected configurations;
- material dependency;
- current incidents/changes;
- reassessment exposure.

This allows management to see concentration that individual cases may not reveal.

## 18. Shared Control Dependency View

Multiple configurations may depend on the same:

- review team;
- specialist capacity;
- reference source;
- external provider;
- escalation function;
- human adjudication process;
- monitoring capability.

The register should eventually support identification of shared control dependencies where operationally useful.

## 19. Capacity View

Where capacity is part of a supported boundary, management should be able to identify:

- configurations dependent on constrained human capacity;
- current capacity condition;
- competing demand;
- cases near or beyond supported capacity;
- reassessment exposure.

This is particularly important where a control remains effective only within a bounded workload.

## 20. Management Attention

The register should support explicit management-attention conditions.

Examples:

- unresolved authority blocking current or proposed action;
- Decision-Limiting Uncertainty;
- required intervention blocked/failed/overdue;
- reassessment due;
- boundary breach;
- configuration changed without completed review;
- Value/Risk input refresh required;
- required control unavailable;
- provider/model change affecting multiple cases;
- proposed stronger operating state;
- case with no decision authority.

Presentation sorting and the boundary against substantive priority are governed by §38.9. No universal prioritization method is created.

## 21. No Universal Portfolio Score

The Management Register should not require one aggregate AI risk/value score.

Management may use counts, financial measures, domain-specific metrics, or prioritization indicators.

However, the register must preserve the underlying management reasons for attention.

A high-level indicator should never replace the authoritative case record.

## 22. Portfolio Filters

A future platform should be able to filter or group entries by dimensions such as:

- business/process area;
- case owner;
- decision authority;
- operating state;
- lifecycle state;
- provider/model;
- unresolved authority;
- Decision-Limiting Uncertainty;
- reassessment due;
- intervention status;
- boundary breach;
- Value/Risk refresh status.

This is a system requirement for discoverability, not a prescribed UI.

## 23. Portfolio History

The register should support historical questions such as:

- How many configurations moved from experiment to continuation?
- Which configurations were suspended or discontinued?
- What decisions changed after reassessment?
- Which authority gaps recur?
- Which controls repeatedly become bottlenecks?
- Where did Value fail to persist?
- Which provider/model changes affected multiple cases?

Historical portfolio analysis should derive from preserved case records rather than rewritten summaries.

## 24. Management Register Entry

Minimum content:

### Identity
- owning Case ID
- applicable Configuration ID, or permitted explicit absence/not-established context
- concern kind
- authoritative source family and stable source Record ID
- exact selected source Version ID(s) and all conflict candidates
- title/business area
- owner
- decision authority

### Current position
- case lifecycle state
- configuration status
- operating state
- Decision ID/version/date
- boundary summary

### Analytical status
- Value Input status/implication
- Risk Input status/implication
- evidence refresh status

### Management attention
- unresolved authority
- Accepted Uncertainty summary
- Decision-Limiting Uncertainty
- intervention status
- learning status
- reassessment status
- boundary breach
- next management action

### Dependencies
- provider/model
- material shared controls/capacity where relevant

## 25. Register Source of Truth

The register is a **derived management view**.

Authoritative detail remains in:

- Managed Configuration Record;
- Value/Risk Inputs;
- Authority Records/Gaps;
- Integration Record;
- Management Decision Record;
- Intervention Record;
- Learning Items;
- Reassessment Record;
- Shared Dependency, Dependency Candidate Set, Shared Dependency Equivalence Determination, and optional Concentration Determination Records for dependency grouping/classification only.

The register must not become an independent competing source of truth.

For every displayed current fact, the Register must apply `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §3.11 for an explicit scope and effective time and retain the selected source Record Version ID. Absence or incompatible current-record conflict must be displayed as such; the Register must not resolve it by selecting the newest or most convenient source.

## 26. Update Behavior

A register entry should reflect authoritative changes when:

- configuration changes;
- new decision is authorized;
- intervention status changes;
- authority resolves/changes;
- uncertainty changes;
- learning completes;
- reassessment is triggered/completed;
- boundary breach occurs;
- case closes/supersedes.

Detailed technical synchronization is deferred to platform architecture.

## 27. Closed / Historical Cases

Closed or superseded cases should remain discoverable but distinguishable from active management entries.

The default management view may focus on active configurations, while history remains accessible.

## 28. Multi-Configuration Cases

If one PAIM case governs multiple simultaneously active configurations, the register should avoid hiding material differences.

Possible approach:

```text
Case C1
  |
  +-- Configuration A — bounded continuation
  +-- Configuration B — experiment
```

Each active configuration may have its own entry linked to the common case.

## 29. Portfolio-Level Management Action

The register may reveal issues requiring action above any single case.

Examples:

- shared review capacity overloaded;
- one provider change affects many configurations;
- repeated authority gaps;
- common control weakness;
- systemic boundary drift;
- concentration in one model/provider.

A portfolio-level issue may create:

- new PAIM case;
- cross-case intervention;
- policy/authority review;
- system-level reassessment program.

Detailed portfolio governance is deferred.

## 30. Relationship to Organizational AI Inventory

An organization may already maintain an AI inventory.

PAIM Management Register is not necessarily a replacement.

Possible relationship:

```text
AI Inventory
   |
   +--> identifies AI systems/use cases
             |
             v
      PAIM-managed configurations
             |
             v
      Management Register
```

The platform may later integrate with an external inventory.

## 31. Relationship to Risk Register

PAIM is not simply a risk register.

A PAIM entry includes:

- Value;
- Risk;
- operating boundary;
- decision;
- intervention;
- learning;
- reassessment.

Risk-register integration may be useful but should not collapse PAIM into risk-only governance.

## 32. Relationship to Value Portfolio

Likewise, PAIM should not become a benefits-tracking dashboard only.

Value is one contributing management leg.

The register should preserve Value and Risk as distinct but integrated dimensions.

## 33. Management Reporting

Minimum future reports may include:

### Active PAIM portfolio

Current configurations and operating states.

### Management attention report

Items requiring decision/intervention/reassessment.

### Authority-gap report

Unresolved authority across configurations.

### Reassessment report

Due/overdue reassessments and triggers.

### Intervention report

Incomplete/failed/blocked interventions.

### Learning report

Decision-specific evidence generation.

### Historical decision report

Decision changes over time.

Exact formats are deferred.

## 34. Register Integrity Checks

The system should surface:

- active configuration with no current decision;
- current decision linked to superseded configuration;
- case marked operating while required intervention incomplete;
- unresolved authority omitted from register;
- Decision-Limiting Uncertainty omitted;
- reassessment due but not surfaced;
- boundary breach not reflected;
- closed case shown as active;
- register summary inconsistent with authoritative decision;
- provider/model change affecting multiple entries but not linked where known.

## 35. Human Judgment Points

Human/accountable judgment remains necessary for:

- determining what requires management attention;
- prioritizing competing cases;
- interpreting concentration/dependency;
- deciding portfolio-level action;
- allocating review/capacity;
- determining whether recurring issues warrant policy/system change.

The register should inform management rather than automate executive judgment.

## 36. Platform Implications

A future platform will likely require:

- management dashboard/register;
- filters/search;
- attention queue;
- drill-down to case/configuration;
- reassessment queue;
- intervention queue;
- authority-gap view;
- dependency/concentration view;
- historical reporting;
- portfolio exports.

This specification does not prescribe visual layout.

## 37. Behavioral Test Candidates

Future tests should include:

1. New decision updates current operating state in register.
2. Reassessment becomes due and appears in attention queue.
3. Authority gap resolves and register updates without deleting history.
4. Intervention fails and management attention is raised.
5. Boundary breach appears across portfolio.
6. A change to one exact Shared Dependency identity makes every exact affected constituent discoverable without transferring Case-local outcome.
7. Closed case leaves active view but remains historically accessible.
8. One case has two active configurations with different states.
9. Register summary conflicts with authoritative decision; integrity check detects it.
10. Capacity dependency affects several cases and becomes visible as a cross-case issue.

## 38. Open Questions

Deferred to later system/platform work:

- exact management-attention prioritization;
- portfolio hierarchy;
- business-unit structure;
- AI-inventory integration;
- risk-register integration;
- value-portfolio integration;
- provider/model normalization;
- portfolio analytics;
- reporting cadence;
- cross-case intervention objects;
- organization-wide policy escalation.

## 38.1 Normative IRR-012 Management Register Contract

This section resolves IRR-012 for specification purposes. It governs every Management Register concern entry, Configuration summary, Shared Dependency group, dashboard, queue, report, export, drill-down view, search index, attention indicator, schedule, and notification intent. Those outputs are derived, rebuildable, and non-authoritative.

No Register row, group, count, acknowledgement, dismissal, sort, filter, queue transition, report sign-off, notification event, or projection state may resolve or supersede a source fact; create authority or accountability; satisfy an Intervention obligation; accept Completion; alter Trigger Coverage or a Reassessment outcome; change a Decision, Boundary, Configuration, lifecycle state, or operating state; or transfer authority, satisfaction, applicability, ownership, outcome, or closure across Cases. A substantive action launched from Register context invokes the owning authoritative domain command or an explicitly governed Shared Dependency determination under §§38.7–38.9.

### 38.2 Stable Register Concern Entry identity

One base **Register Concern Entry** has the exact stable key:

1. owning Case ID;
2. applicable Configuration ID, or explicit absence/not-established context only where §38.3 permits population;
3. concern kind;
4. authoritative source family; and
5. stable source Record ID.

The exact selected source Version or incompatible co-current Versions are rendering and historical basis, not entry identity. A materially different source Record or concern kind creates another concern entry. Co-current incompatible source Versions produce one `CURRENT_CONFLICT` concern context retaining every candidate and reason; the Register never selects a winner.

Where an upstream authoritative aggregate has its own stable subject identity, the concern key uses that aggregate subject Record ID and retains every exact contributing source Version. Configuration summaries and Shared Dependency groups are presentation groupings over concern entries, never concern-entry identities or new sources of truth.

### 38.3 Population eligibility and attention

Population uses family-specific authoritative meanings and the common current-selection rule. The Register reports an upstream result; it does not recompute it through a universal status order, traffic light, “worst” value, or generic null rule.

| Authoritative source family/result | Normative current treatment |
|---|---|
| Governing Configuration, current Decision, Boundary, and Authorization Basis | Display the exact current management position. Required absence/not established or conflict creates attention. |
| Finalized non-governing proposed/experimental Configuration | Eligible only when linked eligible authoritative work or explicit authoritative attention exists. It remains labeled non-governing and not authorized; a draft or inventory mention is ineligible. |
| Authority Gap or Decision Authority Gap | Open/unresolved/conflicted Gap creates attention. Authoritative resolution removes it prospectively from current unresolved attention and preserves history. |
| Value selection/fitness | Display independently from Risk. Absence, conflict, rejected/withdrawn current eligibility, or explicit refresh-required affecting the exact current/proposed use creates attention. Non-selected history remains discoverable and is not collapsed into a “worst” result. |
| Risk selection/fitness | Apply the same rule independently from Value. The lanes never satisfy, overwrite, rank, or summarize one another. |
| Evidence Applicability | Missing required applicability, current conflict, `NOT_APPLICABLE`, material unresolved `INDETERMINATE`, or explicit `REFRESH REQUIRED` creates attention for the exact target/use. Conditional/partial results retain exact scope and conditions. |
| Decision uncertainty and conditions | Exact Accepted Uncertainty and conditions may be informational. Explicit Decision-Limiting, blocked, due, breached, or conflicted facts create attention without operating-state ranking. |
| Intervention Obligation/aggregate and Completion Acceptance | `INCOMPLETE`, `BLOCKED`, `CONFLICT`, or `NOT_ESTABLISHED` creates attention according to exact requirement type. Completion without eligible Acceptance remains attention. `SATISFIED` and `NOT_REQUIRED` retain their upstream meanings. |
| Learning Item/commitment/result | Active, blocked, failed, inconclusive, overdue, or required incomplete work creates attention only where the authoritative Learning contract gives it that meaning. Completion never changes a Decision automatically. |
| Trigger Determination/Coverage | `REASSESSMENT_REQUIRED_UNASSIGNED`, `BLOCKED_CONFLICT`, coverage conflict, or determination conflict creates attention. Informational/monitor outcomes are current informational only where their source rule requires visibility. |
| Reassessment | Eligible active, overdue, owner-vacant/conflicted, overlap-conflicted, or outcome-blocked work creates attention. Completed, cancelled, or superseded work is historical unless another current concern cites it. |
| Interim Operating Disposition | Display every current exact-scope partition. Suspension, conflict, and explicit expiry facts retain exact scope; no operating-state rank or cross-scope contamination is permitted. |
| Lifecycle/currentness/integrity/Boundary breach | Eligible absence, conflict, breach, or integrity condition creates attention only when an accepted authoritative source family establishes the fact. |
| Role/accountability | Vacancy or conflict creates attention only for an identified current obligation. A Role Assignment alone is not a concern. |

Raw telemetry, drafts, unsupported inference, semantic similarity, and unaccepted Observation-like objects are ineligible. Another source family becomes eligible only through an accepted versioned population rule consistent with its governing specification.

### 38.4 Derived lifecycle categories

The exact v0.1 Register categories are:

- `CURRENT_ATTENTION` — eligible current source result requires attention;
- `CURRENT_CONFLICT` — eligible current source selection or aggregate is conflicted;
- `CURRENT_INFORMATIONAL` — a current fact is intentionally visible but not itself unresolved work;
- `RESOLVED_HISTORICAL` — the source is authoritatively resolved/satisfied/completed and no current attention rule applies;
- `SUPERSEDED_HISTORICAL` — the source subject has an eligible successor;
- `WITHDRAWN_OR_INELIGIBLE_HISTORICAL` — prospective reliance has ended; and
- `PROJECTION_STALE_OR_INCONSISTENT` — projection delivery cannot prove current consistency.

These are derived projection results, not authoritative source statuses. Concern lifecycle and closure derive only from authoritative source selection plus the exact population-rule Version. There is no generic authoritative Register close, resolve, dismiss, archive, or delete action. A Shared Dependency group remains partially unresolved while any constituent is current attention or conflict; after all constituents cease current attention, the group leaves current attention prospectively and remains historically reconstructable.

### 38.5 Dual-time currentness and staleness

The controlling Register answer is deterministic derivation for declared scope, `effective_at`, optional `known_at`, and active projection/population/aggregation rule Version. Direct query versus asynchronous materialization is an engineering choice and does not change the answer.

A materialized output claimed as current must expose and validate:

- calculation/generated time;
- requested effective/known context;
- projection rule ID and Version;
- source recorded-time high-water mark relevant to the requested scope;
- processed projection watermark; and
- consistency/inconsistency state.

If the watermark cannot prove processing through the relevant authoritative high-water mark under the active rule Version, the output is `PROJECTION_STALE_OR_INCONSISTENT`, visibly `STALE`/`PROJECTION INCONSISTENCY`, or rebuilt before it is claimed current. A guarded substantive command always re-evaluates authoritative source facts and never trusts projection state as authority.

### 38.6 Shared Dependency identity and cross-Case grouping

A stable authoritative **Shared Dependency** identity supports descriptive grouping without creating a cross-Case authority model. Sharing is established only by:

1. exact citation of the same stable authoritative dependency Record ID; or
2. one eligible Shared Dependency Equivalence Determination under §§38.7–38.9 binding exact candidates to one stable Shared Dependency ID.

Provider, system, model, or control names; normalized strings; URLs; ownership; Evidence-source equality; external-event provenance; text similarity; semantic/AI matching; embeddings; co-occurrence; and dashboard grouping never establish dependency identity. Equivalence preserves every candidate identity and may be limited to its declared scope; it never rewrites source Records.

Concern entries from different Cases may be grouped only when they resolve to the same exact Shared Dependency identity. Every constituent retains its exact Case, Configuration, source Versions, local owners/roles/authorities, status, applicability, satisfaction, Trigger Coverage, Reassessment outcome, and closure. Grouping never transfers or infers Evidence Applicability, Decision effect, Intervention satisfaction, Completion Acceptance, Trigger Coverage, Reassessment outcome, lifecycle/operating state, Case closure, ownership, accountability, or authority. Common provenance, business unit, source event, domain, or owner is a filter only.

### 38.7 Immutable Dependency Candidate Set

`DEPENDENCY_CANDIDATE_SET` is a first-class stable/versioned authoritative typed target governed by the Integrity and Roles specifications. It is never a free-form scope string, transient query result, mutable list, or software-selected candidate collection.

Each Version retains stable Candidate Set ID, immutable Version ID, exact typed candidate Record IDs and required Version IDs, dependency kind for each candidate, equivalence scope/purpose, owning organizational accountability context where required, effective/recorded time, establishment provenance/rationale, predecessor/correction/supersession/withdrawal history, and deterministic canonical membership checksum or equivalent integrity basis.

Finalized membership is immutable. Adding, removing, or rebinding a candidate creates a successor Candidate Set Version. Historical accountability and determination selection use the exact cited Candidate Set Version, never membership recomputed from a current query.

### 38.8 Equivalence and optional concentration determinations

An authoritative Shared Dependency Equivalence Determination retains stable identity and immutable Version; exact Candidate Set Version; exact stable Shared Dependency ID where the outcome is `EQUIVALENT`; dependency kind; exact outcome (`EQUIVALENT`, `NOT_EQUIVALENT`, or `INDETERMINATE`) and equivalence scope; rationale; exact accountable actor and Shared Dependency Determiner assignment/mechanism/delegation basis; effective/recorded time; and correction/supersession/withdrawal history. Only `EQUIVALENT` establishes grouping for its exact declared scope. `NOT_EQUIVALENT` preserves separate candidate identities, and `INDETERMINATE` establishes no group.

Current selection returns exactly one eligible determination, `SHARED DEPENDENCY EQUIVALENCE NOT ESTABLISHED`, or `SHARED DEPENDENCY EQUIVALENCE CONFLICT — UNRESOLVED` with every incompatible candidate and reason. Recency, majority, name, similarity, owner, hierarchy, or software permission never chooses a winner. Conflict blocks authoritative combined grouping while constituent concerns remain independently visible.

Safe aggregation is limited to exact counts and sets over an exact constituent manifest, including affected Case/Configuration IDs and counts, concern counts by exact kind/category, unresolved/conflict counts, exact obligation counts, dependency exposure sets, due-date ranges and age from authoritative dates, current blocker-presence flags, and source materiality/priority labels as identities.

A descriptive exposure count or set is not risk, severity, materiality, priority, or authority. If `MATERIAL CONCENTRATION` or equivalent is used, it is a separate stable/versioned authoritative Concentration Determination retaining exact Shared Dependency ID, exact constituent/input basis, outcome, rationale, accountable actor/assignment/mechanism/delegation, dual time, and history. Its current selection returns one eligible determination, `CONCENTRATION DETERMINATION NOT ESTABLISHED`, or `CONCENTRATION DETERMINATION CONFLICT — UNRESOLVED`. This specification introduces no universal risk, severity, concentration, priority score, or automatic threshold.

### 38.9 Accountability and presentation ordering

Shared Dependency Determiner accountability and typed targets are governed by the Roles specification. Vacancy or incompatible plurality produces the named not-established/conflict result; dashboard ownership, Case/source ownership, report authorship, administration, and software permission never substitute.

For a consumer explicitly cut over under
`PAIM_RESPONSIBILITY_AND_CASE_WORK_SPEC_v0.1.md`,
`DETERMINE_SHARED_DEPENDENCY_EQUIVALENCE` binds the exact immutable Candidate Set Version, every
constituent owning Case/context permitted by this specification, equivalence scope/purpose, and
time. Responsibility permits the accountable Actor to attempt the existing Equivalence
Determination command; it does not establish equivalence, grouping, concentration, priority,
authority, or any constituent result. Before cutover, the current Shared Dependency Determiner
Role Assignment/mechanism rule remains controlling. Register-derived work remains non-authoritative
unless the Case Work contract's durable coordination boundary is independently met.

Safe presentation sorting uses exact source facts such as due date, effective/recorded date, age, stable identity, exact lifecycle/blocker category, and explicit authoritative materiality/priority labels. Sorting changes no substantive priority or source state. Stable-ID tie-breaking is presentation only. No cross-family worst-state logic, weighted score, enum order, operating-state rank, color, queue position, drag/drop order, or notification frequency creates substantive priority. Any future substantive prioritization beyond exact source facts requires a separate accepted authority/policy contract.

`CONFLICT`, `NOT ESTABLISHED`, `INDETERMINATE`, `STALE`, and `PROJECTION INCONSISTENCY` remain visible. Conflict may be counted or grouped descriptively, but a field requiring one winner remains unset/conflicted. Projection inconsistency is quarantined/rebuilt or handled equivalently fail closed; it neither repairs source conflict nor authorizes a command.

### 38.10 Register-context actions

- Assign owner: invoke the exact typed Role Assignment command in the owning domain.
- Acknowledge/read/snooze notification: non-authoritative user preference only; it cannot suppress required organizational attention.
- Defer: invoke an existing source-family command only where that family permits deferral.
- Accept residual concern: invoke the exact Decision/uncertainty/authority command with its complete authorization basis.
- Link shared dependency: create an Equivalence Determination under §§38.7–38.9.
- Link duplicate: invoke the owning family’s accepted identity/duplicate command.
- Create Trigger/Reassessment: invoke the Reassessment commands and all their guards.
- Create or modify Decision/Intervention: invoke the owning commands and all their guards.
- Generic `mark resolved`: unavailable.

Launch-context provenance may be retained, but authoritative effect belongs only to the invoked domain record and semantic transaction.

### 38.11 Historical reconstruction manifest and output boundary

A reconstructable Register view/export manifest retains requested scope/access context where relevant; `effective_at` and `known_at`; projection/population/aggregation rule IDs and Versions; every selected source Record/Version and absent/conflict candidate; Shared Dependency identity and exact Candidate Set/Equivalence/Concentration Determination Versions; constituent concern keys and group membership; calculation time; source recorded-time high-water mark; projection watermark and inconsistency state; and visible filter, grouping, and ordering basis.

Rendered snapshots may be retained for evidence/performance, but the exact source/determination/rule/time basis controls reconstruction. Later correction, rule change, equivalence change, source supersession, or rebuild never rewrites a prior manifest.

Dashboards, queues, reports, export snapshots, drill-down views, search indexes, attention indicators, schedules, and notification intents are non-authoritative projections. Delivery receipt, retry, or failure is a technical fact only. Every durable output claiming PAIM management state retains sufficient basis, rule Version, and watermark to identify the exact derived state represented.

### 38.12 Deferred boundaries

- **IRR-009 remains open.** No Observation identity/version/cardinality, monitoring retention contract, or automated Observation-to-Evidence/Trigger/Register conversion is defined. External monitoring information enters the Register only through an already accepted authoritative source family with retained provenance, or remains clearly non-authoritative UI context.
- **IRR-014 remains open.** Exact operating-state values may be displayed, filtered, counted, and grouped only by identity. No stronger, broader, more restrictive, severity, escalation, target-state, or priority relation is inferred from enum order, label, color, workflow sequence, numeric code, frequency, or product convention.

## 39. Completion Impact

This specification adds the first formal cross-case management layer to PAIM.

The system now has specifications for:

- single-case lifecycle;
- configuration;
- evidence/authority;
- Value/Risk inputs;
- integration/decision;
- intervention/learning;
- reassessment;
- portfolio/register view.

The principal remaining implementation-independent system specifications are:

- Roles and Accountability;
- System Behavioral Validation Strategy.

## 40. Next Specification

Create:

`PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md`

It should define:

- case owner;
- Value evaluator;
- Risk evaluator;
- decision authority;
- intervention owner;
- evidence/authority owner;
- reviewer/auditor;
- system administrator;
- separation-of-role principles;
- delegated authority;
- accountability relationships;
- role conflicts;
- platform permission implications.

## 41. Repository Placement

```text
400. Practical AI Management/
└── system/
    └── specifications/
        ├── PAIM_CASE_LIFECYCLE_SPEC_v0.1.md
        ├── PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md
        ├── PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md
        ├── PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md
        ├── PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md
        ├── PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md
        ├── PAIM_REASSESSMENT_SPEC_v0.1.md
        └── PAIM_MANAGEMENT_REGISTER_SPEC_v0.1.md
```

## 42. Conclusion

The PAIM Management Register turns a collection of individual management cases into an organizational AI-management capability.

Its central principle is:

> **The register should show management where attention is required without collapsing the underlying Value, Risk, authority, boundary, decision, intervention, and learning records into a single score.**

This provides the portfolio layer needed for a practical PAIM platform.
