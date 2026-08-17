# PAIM Managed Configuration Specification v0.1

## Status

Implementation-independent system specification for the **Managed Configuration** in Practical AI Management (PAIM).

This specification derives from:

- `PAIM_SYSTEM_ARCHITECTURE_v0.1.md`
- `PAIM_SYSTEM_COMPLETION_BASELINE_GAP_MAP_v0.1.md`
- `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`
- `PAIM_MINIMUM_MANAGEMENT_CASE_v0.3.md`
- `PAIM_PRACTITIONER_PLAYBOOK_v0.2.md`

It defines what the PAIM system must represent, preserve, version, compare, and reassess when managing an AI-enabled configuration.

It does not prescribe database schemas, UI implementation, APIs, or software technology.

## 1. Purpose

The Managed Configuration is the bounded AI-enabled system of work to which PAIM evidence, analytical findings, management judgments, interventions, and reassessment apply.

PAIM does not manage an abstract AI model in isolation.

The configuration may include:

- AI capability/system;
- task/activity;
- workflow;
- users and affected parties;
- information/data;
- AI authority;
- human authority;
- controls;
- escalation/review;
- provider/model;
- operating conditions;
- dependencies;
- explicit exclusions.

The system must be able to answer:

> **Exactly what configuration was evaluated, what changed, which evidence applies to it, and whether the current management decision remains valid after the change?**

## 2. Configuration Identity

Every Managed Configuration must have a durable identity independent of its descriptive title.

Minimum identity elements:

- Configuration ID
- Case ID
- Configuration version
- Configuration title/label
- status
- effective date/time where relevant
- predecessor configuration, if any
- successor configuration, if any
- creation source/owner
- reason for creation/change

A human-readable title is not sufficient as the authoritative identity.

## 3. Configuration Version

A configuration version represents a specific bounded state of the AI-enabled system of work.

Example:

```text
CFG-001 v1
    |
    | material change
    v
CFG-001 v2
```

The system must preserve both versions.

A later version must not overwrite the earlier configuration to which historical evidence and decisions were bound.

## 4. Configuration Status

At minimum, a configuration may be:

- draft;
- current;
- proposed;
- experimental;
- superseded;
- retired.

Configuration status is distinct from:

- case lifecycle state;
- AI operating state;
- decision status.

For example:

```text
Configuration status: current
Case lifecycle: OPERATING_OBSERVING
AI operating state: bounded continuation
```

## 5. Core Configuration Elements

### 5.1 AI capability/system

Record the AI capability relevant to the management decision.

Possible content:

- model/system identity;
- AI function;
- application/service;
- provider;
- major capability mode;
- material version where relevant.

The record should describe only what matters to the management object.

### 5.2 Activity/process

Record the work the AI participates in.

Examples:

- customer inquiry handling;
- visual quality inspection;
- administrative document intake;
- internal research;
- drafting/summarization;
- decision support.

The activity should be bounded enough that Value and Risk findings can meaningfully apply.

### 5.3 Users and affected parties

Record relevant:

- operators/users;
- reviewers;
- decision makers;
- customers;
- employees;
- counterparties;
- other affected groups.

Do not add groups merely because they could theoretically be affected.

### 5.4 Information/data

Record information conditions material to the configuration.

Examples:

- public information;
- internal information;
- customer information;
- structured/unstructured data;
- approved knowledge base;
- proprietary sources;
- restricted information;
- source/version requirements.

Authority concerning information use belongs in the Authority model, not as an unsupported configuration assumption.

### 5.5 AI authority

Record what the AI is permitted or configured to do.

Examples:

- draft;
- classify;
- extract;
- recommend;
- prioritize;
- route;
- generate a signal;
- communicate;
- execute an action.

Where material, distinguish:

- recommendation;
- provisional action;
- final action.

### 5.6 Human authority and responsibility

Record what humans must do or retain authority over.

Examples:

- verify;
- interpret;
- approve;
- override;
- escalate;
- adjudicate;
- make final disposition;
- communicate consequential decisions.

Human participation is part of the configuration, not an external footnote.

### 5.7 Controls

Record material controls that define the operating configuration.

Examples:

- verification;
- review;
- source checking;
- threshold;
- escalation;
- HOLD state;
- human handoff;
- monitoring;
- restricted scope;
- independent source re-verification.

Detailed Control Dependency analysis belongs in PAIM Integration, but the configuration must identify which controls are present.

### 5.8 Escalation/review

Record conditions and pathways for:

- exception handling;
- secondary review;
- specialist review;
- human handoff;
- external provider escalation;
- unresolved-case treatment;
- fallback.

### 5.9 Provider/model

Record provider/model conditions when they materially affect evidence or operation.

The system should not require unnecessary model metadata when it has no bearing on the management decision.

### 5.10 Operating conditions

Record environmental or organizational conditions on which evidence depends.

Examples:

- production/imaging conditions;
- workload;
- analyst capacity;
- downstream capacity;
- customer complexity;
- document types;
- geographic scope;
- supported languages;
- operating hours;
- network/system dependencies.

### 5.11 Dependencies

Record material dependencies not already captured.

Examples:

- external provider;
- human review capacity;
- approved reference source;
- downstream team;
- adjudication process;
- data feed.

### 5.12 Explicit exclusions

Record what the configuration does **not** include.

Exclusions are important because they prevent later interpretation from silently broadening the evidence boundary.

## 6. Configuration Snapshot

A configuration version should be reconstructable as a coherent snapshot.

Conceptually:

```text
Managed Configuration vN
|
+-- AI capability
+-- activity/process
+-- users/affected parties
+-- information/data
+-- AI authority
+-- human authority
+-- controls
+-- escalation/review
+-- provider/model
+-- operating conditions
+-- dependencies
+-- exclusions
```

The system should preserve the snapshot used by each Value Input, Risk Input, Integration Record, and Management Decision.

## 7. Material Change Principle

A change is material when it may invalidate or materially alter the applicability of existing evidence, analytical findings, controls, authority, or the management judgment.

The test is not:

> **Did anything change?**

It is:

> **Would a reasonable Value, Risk, authority, or management conclusion potentially change because this element changed?**

## 8. Material Change Categories

Changes that may be material include:

### AI capability/model

- materially different model;
- materially changed model behavior;
- new tool/function;
- material provider change;
- changed retrieval/data capability.

### Scope/task

- new activity;
- broader assignment type;
- new customer/use population;
- new defect/document/research class;
- materially greater complexity.

### AI authority

- recommendation becomes execution;
- draft becomes autonomous communication;
- attention signal becomes final disposition;
- increased action authority.

### Human authority/control

- verification removed or weakened;
- review burden reduced;
- escalation removed;
- threshold changed;
- handoff changed;
- final human authority reduced.

### Information/data

- new data class;
- private/restricted information introduced;
- source quality changes;
- new knowledge base;
- materially different source environment.

### Operating conditions

- volume/capacity changes;
- new production conditions;
- new geography/language;
- workload changes;
- downstream capacity changes.

### Authority

- new governing requirement;
- prior authority resolved;
- authority scope changes.

## 9. Non-Material Change

A change may be non-material when it does not reasonably affect the applicability of existing evidence or the management decision.

Examples may include:

- descriptive correction;
- administrative owner change with no authority change;
- formatting change;
- non-substantive provider metadata correction.

Whether a change is material is a management/system judgment, not merely a technical comparison.

## 10. Change Assessment

For each proposed or detected change, record:

- changed element;
- prior value;
- proposed/current value;
- reason;
- materiality assessment;
- rationale;
- affected evidence;
- affected Value Input;
- affected Risk Input;
- affected authority;
- affected controls;
- affected decision/boundary;
- required action.

Possible outcomes:

- no management impact;
- evidence review required;
- Value refresh required;
- Risk refresh required;
- authority review required;
- PAIM reassessment required;
- successor configuration/case required.

## 11. Configuration Versioning Rule

If a change is material:

1. preserve the prior configuration version;
2. create a successor version or successor configuration;
3. assess evidence applicability;
4. identify analytical refresh required;
5. reassess the current PAIM decision where necessary.

Do not mutate the historical configuration record in place.

## 12. Same Configuration vs. New Configuration

Use a **new version of the same configuration** when continuity remains meaningful and the management object is still recognizably the same system of work.

Use a **new configuration identity** when the change creates a materially different management object.

Factors favoring a new identity include:

- different core activity;
- materially different AI authority;
- different population/use context;
- different value mechanism;
- materially different adverse pathways;
- evidence cannot reasonably transfer;
- prior and new configurations should be independently interpretable.

## 13. Evidence Applicability

Evidence must be bound to the configuration or configuration conditions under which it was generated.

When configuration changes, evidence may be:

- directly applicable;
- conditionally applicable;
- partially applicable;
- refresh required;
- not applicable;
- unknown.

The system must not assume that evidence remains applicable solely because the configuration retains the same name.

## 14. Value Input Applicability

A Value Management Input should identify the configuration/version to which its:

- Finding;
- Boundary;
- Uncertainty;
- Implication;
- Provenance

apply.

A material change affecting the value-production mechanism, complete cost, control burden, assignment scope, capacity, or other Value dependency should trigger applicability review.

## 15. Risk Input Applicability

A Risk Management Input should identify the configuration/version to which its conclusions apply.

Changes to:

- AI authority;
- controls;
- human participation;
- information/data;
- scope;
- thresholds;
- provider/model;
- operating conditions

may require Risk refresh.

## 16. Authority Applicability

Authority may apply to:

- a configuration;
- a configuration element;
- a data class;
- an activity;
- a user population;
- an operating state;
- a decision.

Authority applicability must be reviewed when relevant configuration elements change.

`AUTHORITY UNRESOLVED` remains explicit until resolved or rendered immaterial to the bounded decision.

## 17. Boundary Relationships

The Managed Configuration is not the same as any analytical or decision boundary.

```text
Managed Configuration
      |
      +--> Value Boundary
      +--> Risk Boundary
      +--> Constraints / Authority
      +--> Control Dependencies
      |
      v
Integrated Operating Boundary
```

The Managed Configuration defines **what is being evaluated**.

The Integrated Operating Boundary defines **where and under what conditions the final PAIM judgment is supportable**.

The final boundary may:

- equal the proposed configuration;
- narrow it;
- condition it;
- exclude parts;
- authorize only an experimental subset;
- require fallback or transition.

## 18. Proposed vs. Current Configuration

The system must be able to distinguish:

- current configuration;
- proposed configuration;
- experimental configuration;
- authorized configuration;
- historical configuration.

A management case may compare multiple alternatives simultaneously.

For example:

```text
Current: Configuration A
Alternative: Configuration B
Experimental redesign: Configuration C
Fallback: Configuration D
```

Each alternative should be separately identifiable.

## 19. Configuration and Operating State

Operating state belongs to the management decision, not inherently to the configuration identity.

The same configuration may move through:

- experiment;
- bounded continuation;
- targeted scale;
- institutionalized use;
- suspension;
- discontinuation.

A state change may itself require reassessment even if configuration elements are unchanged, because the evidence required for a stronger state may differ.

## 20. Configuration and Controls

Controls may be:

- inherent to configuration;
- required by authority;
- required by Value finding;
- required by Risk finding;
- imposed by PAIM judgment;
- proposed experimentally.

The system should preserve these provenance distinctions where relevant.

Removing a control that is a condition of the Integrated Operating Boundary is a material change unless explicitly shown otherwise.

## 21. Configuration and Capacity

Human/downstream capacity can be part of the configuration when Value or Risk depends on it.

Examples:

- secondary-review capacity;
- analyst verification capacity;
- human handoff capacity;
- downstream sales/technical capacity.

Capacity changes may therefore trigger configuration reassessment rather than being treated merely as operational metrics.

## 22. Configuration History

The system should support a history such as:

```text
CFG-001 v1
  |
  | threshold/control redesign
  v
CFG-001 v2
  |
  | increased AI authority
  v
CFG-002 v1
```

Each decision and analytical input remains linked to the configuration version it governed.

## 23. Configuration Comparison

For material changes, the system should be able to display:

| Element | Prior configuration | Proposed/new configuration | Material? | Evidence impact |
|---|---|---|---|---|
| AI authority | | | | |
| Human authority | | | | |
| Controls | | | | |
| Scope | | | | |
| Information | | | | |
| Provider/model | | | | |
| Operating conditions | | | | |

This is an inspectability aid, not a mandatory UI design.

## 24. Minimum Managed Configuration Record

Minimum fields:

### Identity
- Configuration ID
- Case ID
- version
- title
- status
- effective date
- predecessor/successor

### Management object
- AI capability/system
- activity/process
- users/affected parties
- information/data
- AI authority
- human authority/responsibility
- controls
- escalation/review
- provider/model
- operating conditions
- dependencies
- exclusions

### Change/provenance
- created by/source
- reason
- change summary
- materiality assessment
- related prior configuration

### Relationships
- Value Input(s)
- Risk Input(s)
- Authority Record(s)
- Integration Record(s)
- Management Decision(s)
- Intervention(s)
- Reassessment(s)

## 25. Configuration Integrity Checks

The system should be able to surface:

- missing AI/human authority where material;
- undefined scope;
- missing exclusions where scope ambiguity exists;
- control referenced by a decision but absent from current configuration;
- Value/Risk inputs bound to different configuration versions;
- decision applied to a superseded configuration;
- operating state changed without reassessment where required;
- evidence used outside its configuration applicability;
- unresolved material change.

These are integrity checks, not automatic substantive decisions.

## 26. Reassessment Triggers from Configuration Change

Potential triggers include:

- new model/provider;
- new AI capability;
- scope expansion;
- increased autonomy;
- control removal/change;
- threshold change;
- new data/information;
- new user population;
- workload/capacity shift;
- new operating environment;
- new downstream dependency;
- new authority requirement.

A material trigger should connect to the Case Lifecycle specification and create `REASSESSMENT_DUE` where appropriate.

## 27. Human Judgment Points

Human/accountable judgment remains necessary for:

- defining the management object;
- deciding whether a change is material;
- determining evidence applicability;
- deciding whether continuity warrants a version or new identity;
- deciding whether current operation may continue pending reassessment;
- determining whether a stronger operating state requires new evidence.

The platform should support these judgments rather than hide them.

## 28. Platform Implications

A future platform will likely require:

- configuration editor/view;
- version history;
- comparison/diff view;
- current/proposed/experimental labels;
- evidence applicability indicators;
- control relationships;
- authority relationships;
- decision linkage;
- change/reassessment workflow.

This specification does not prescribe UI or persistence design.

## 29. Behavioral Test Candidates

Future tests should include:

1. Remove mandatory human verification and confirm reassessment is triggered.
2. Change only the model version with no demonstrated behavioral effect and test materiality judgment.
3. Expand from public-information research to proprietary-data research and ensure prior evidence does not silently transfer.
4. Increase AI authority from recommendation to execution and require new assessment.
5. Change a threshold that improves Value but changes Risk exposure.
6. Reduce review capacity below the evidence-supported level.
7. Resolve an authority gap without changing the technical configuration.
8. Compare current, proposed, experimental, and fallback configurations.
9. Attempt to bind a frozen Value Input to the wrong configuration version.
10. Attempt to apply a historical decision to a superseded configuration.

## 30. Open Questions

Deferred to later specifications/platform design:

- exact configuration ID convention;
- formal materiality decision authority;
- machine-detectable vs. human-declared changes;
- evidence applicability status taxonomy;
- whether configuration versions require effective-time intervals;
- how external provider/model metadata are normalized;
- cross-case shared configurations;
- reusable control definitions.

## 31. Completion Impact

This specification substantially advances the Managed Configuration capability identified in the system gap map.

Remaining work includes:

- formal Evidence/Authority model;
- formal Value/Risk interface record;
- integration/decision record;
- platform data model;
- UI/version workflow;
- behavioral validation.

## 32. Next Specification

Create:

`PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md`

This should define:

- Evidence Record;
- evidence provenance;
- observation/inference/estimate/assumption/unknown treatment;
- authority identity and applicability;
- `AUTHORITY UNRESOLVED`;
- evidence/authority versioning;
- supersession;
- binding to configurations/findings/decisions.

## 33. Repository Placement

```text
400. Practical AI Management/
└── system/
    └── specifications/
        ├── PAIM_CASE_LIFECYCLE_SPEC_v0.1.md
        └── PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md
```

## 34. Conclusion

The Managed Configuration specification gives PAIM a durable answer to a foundational question:

> **What exactly are we managing, and when has it changed enough that the old evidence or decision can no longer be assumed to apply?**

That capability is essential for turning PAIM from a case-analysis method into a traceable management system.
