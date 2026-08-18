# PAIM Evidence and Authority Specification v0.1

## Status

Implementation-independent system specification for evidence and governing authority in Practical AI Management (PAIM).

This specification derives from:

- `PAIM_SYSTEM_ARCHITECTURE_v0.1.md`
- `PAIM_SYSTEM_COMPLETION_BASELINE_GAP_MAP_v0.1.md`
- `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`
- `PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md`
- `PAIM_MINIMUM_MANAGEMENT_CASE_v0.3.md`
- `PAIM_PRACTITIONER_PLAYBOOK_v0.2.md`

It defines what the PAIM system must preserve about evidence, provenance, authority, unresolved authority, applicability, versioning, and relationships to configurations, analytical findings, decisions, interventions, and reassessment.

It does not prescribe storage technology, database schemas, document formats, or user-interface design.

**Normative cross-cutting contract:** `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md` governs stable record identity vs. immutable version identity, finalization, status events, recorded/effective time, correction/supersession/withdrawal, authoritative current selection, exact historical retrieval, Decision Authorization Basis, and the treatment of Decision Authority Gap as an Authority Gap classification.

## 1. Purpose

PAIM management judgments must remain inspectable after the decision is made.

The system must be able to answer:

> **What evidence supported this finding or decision?**

> **What was observed, inferred, estimated, assumed, or unknown?**

> **What governing authority applied?**

> **What authority remained unresolved?**

> **Which configuration and decision did the evidence or authority apply to?**

> **Has the evidence or authority since changed, expired, been superseded, or become inapplicable?**

Evidence and authority therefore require durable system representation rather than informal references scattered across case documents.

## 2. Evidence Is Not the Same as a Finding

An Evidence Record represents source material, observation, measurement, analysis result, or other evidentiary input.

A Finding is an analytical conclusion drawn from one or more Evidence Records.

Conceptually:

```text
Evidence Record(s)
       |
       v
Analytical Reasoning
       |
       v
Finding
       |
       v
PAIM-facing Input / Decision
```

The system must not collapse evidence and conclusion into one undifferentiated field.

## 3. Evidence Record

Every material Evidence Record should support:

### Identity

- Evidence ID
- title/label
- case relationship
- configuration relationship
- evidence type
- status
- source
- owner/custodian where relevant

### Time/context

- observation/effective period where relevant
- date obtained/recorded
- version/vintage where relevant
- operating context

### Content

- evidence statement or reference
- relevant measurement/result
- unit/basis where applicable
- scope
- known limitations

### Provenance

- originating source
- source record/document/system
- method of collection where material
- analyst/producer where relevant
- transformation/derivation relationship

### Applicability

- exact Evidence Applicability Record/Version relationships governed by §7;
- current first-class target types: Managed Configuration Version, Value Input Version, Risk Input Version, Authority Record Version, and Authority Gap Version/question; and
- later typed target extensions only when their owning specifications establish substantive identity and workflow semantics.

Applicability is not mutable metadata on the Evidence Version. Evidence content and each target-specific applicability judgment have separate authoritative identities and histories.

## 4. Evidence Classification

PAIM should support a compact evidence-status vocabulary without pretending that every domain uses identical epistemology.

At minimum, the system should be capable of distinguishing:

### Observed evidence

Directly observed or recorded in the relevant context.

Examples:

- measured cost;
- observed error;
- completed transaction;
- realized sourcing substitution;
- actual review volume.

### Supported inference

A conclusion reasonably derived from evidence but not directly observed as the final fact.

Examples:

- likely adverse pathway;
- inferred control dependency;
- estimated avoided loss using explicit assumptions.

### Estimate

A quantified value derived from assumptions, models, ranges, counterfactuals, or projections.

### Assumption

A proposition used for analysis that is not itself established by the current evidence.

### Unknown

A material question for which the evidence does not support a conclusion.

These labels are provenance aids, not universal confidence scores.

## 5. Evidence Maturity

Where useful, PAIM may additionally represent evidence maturity such as:

- demonstrated;
- supported;
- plausible;
- unknown.

Evidence maturity should not replace the more precise evidence classification above.

Example:

```text
Evidence classification: Estimate
Evidence maturity: Supported
```

The exact vocabulary should remain configurable until further validation.

## 6. Evidence Scope

Every material Evidence Record should state or imply the scope in which it is relevant.

Possible scope dimensions include:

- configuration;
- task/assignment class;
- user/customer population;
- information environment;
- control state;
- model/provider;
- geography;
- time period;
- operating condition;
- volume/capacity range.

Evidence outside its scope must not silently become general evidence for the entire AI system.

## 7. Evidence and Managed Configuration

Evidence must be bound to the configuration/version under which it was generated or to explicit applicability conditions.

When the Managed Configuration changes, evidence applicability must be reviewed.

Normative applicability outcomes are:

- `APPLICABLE`;
- `CONDITIONALLY_APPLICABLE`;
- `PARTIALLY_APPLICABLE`;
- `NOT_APPLICABLE`; and
- `INDETERMINATE`.

The system must preserve the original evidence even when later judged inapplicable.

`REFRESH REQUIRED` is a prospective status/attention condition, not an applicability outcome. Conflict is a deterministic current-selection result from incompatible co-current judgments, not an assessor-entered outcome.

### 7.1 Evidence Applicability identity and cardinality

Evidence Applicability is a first-class authoritative, versioned many-to-many relationship.

- One exact Evidence Version may have Applicability judgments for many targets.
- One exact target may have Applicability judgments involving many Evidence Versions.
- One Applicability Record identifies a continuing applicability subject for one exact Evidence/target/purpose/scope context.
- Every substantive judgment or scope/rationale change creates an immutable Applicability Version.

An Evidence Applicability record supports at minimum:

- stable Applicability Record ID;
- immutable Applicability Version ID;
- exact Evidence ID and Evidence Version ID;
- target type and target stable identity;
- exact target Version ID whenever the target is versioned or applicability depends on target content;
- purpose/use and assessed scope sufficient to distinguish competing judgments;
- Case and Managed Configuration context where applicable, without substituting for the exact target;
- one normative applicability outcome;
- conditions and limitations;
- rationale;
- assessor PAIM actor;
- exact accountable Role Assignment Version or explicitly governed accountable mechanism;
- effective interval and recorded/known time;
- finalization/status;
- predecessor, correction, supersession, or withdrawal relationship and reason; and
- affected Input, Integration, Decision, or other finalized-use references where later correction materially affects prior or current reliance.

### 7.2 Increment 3 target types

The first-class v0.1 Evidence Applicability target types implemented by Increment 3 are exactly:

1. Managed Configuration Version;
2. Value Input Version;
3. Risk Input Version;
4. Authority Record Version; and
5. Authority Gap Version/question.

Integration, Decision, Finding, Uncertainty, Control, Boundary Clause, Intervention, Learning, Reassessment, and Observation may be reserved as typed extension categories only. This specification does not define their substantive target identity or workflow semantics. Observation remains deferred under IRR-009.

### 7.3 Outcome meaning

- `APPLICABLE` means the Evidence Version is applicable within the complete recorded assessed scope.
- `CONDITIONALLY_APPLICABLE` means applicability depends on explicit recorded conditions. Omitted or failed conditions make the judgment ineligible for that use.
- `PARTIALLY_APPLICABLE` means only an explicit recorded subset of the proposed target scope is supported.
- `NOT_APPLICABLE` means the Evidence Version must not support the declared target/use.
- `INDETERMINATE` preserves an unresolved applicability judgment. It is neither permission nor prohibition and must not be automatically mapped to eligible or ineligible analytical use.

Conditional and partial outcomes require explicit assessed scope, conditions, exclusions/limitations, and rationale. No outcome is a universal evidence-quality, sufficiency, or confidence score.

### 7.4 Accountable judgment

The assessor actor and the accountable assignment/mechanism are separate provenance facts. A finalized Applicability judgment must resolve accountability for the exact target context, purpose, scope, and effective time to:

- exactly one applicable accountable Role Assignment or one explicitly governed accountable mechanism;
- explicit vacancy/not established; or
- explicit incompatible-accountability conflict.

Evidence ownership, analytical authorship, Case ownership, technical-principal identity, software permission, directory hierarchy, integrator participation, or a generic role label does not establish applicability accountability. An Evidence Owner, Value Evaluator, Risk Evaluator, Authority Owner, or another governed function may be accountable only through the exact applicable assignment/mechanism. Broad and narrow assignments have no implicit precedence.

### 7.5 Current selection and conflict

For an explicit Evidence Version, target identity/version, purpose/use, assessed scope, effective time, and optional knowledge cutoff, current Applicability selection returns exactly one of:

- one eligible current Applicability Version;
- `APPLICABILITY NOT ESTABLISHED`; or
- `EVIDENCE APPLICABILITY CONFLICT — UNRESOLVED` with every incompatible candidate and provenance.

No recency, specificity, ownership, directory hierarchy, mutable current flag, software permission, row order, or convenience selects a winner. Distinguishable non-competing scopes may coexist only when their differences are explicit.

An accountable successor or supersession may resolve prospective conflict only by recording exact scope, rationale, displaced Applicability Versions, effective/recorded time, and preserved predecessor history. Resolution never erases the conflicting judgments.

### 7.6 Correction, supersession, staleness, and reuse

- Evidence-content correction creates a corrected Evidence Version and does not mutate the prior Evidence Version or its Applicability Versions.
- Applicability-judgment correction creates a corrected Applicability Version against the exact declared endpoints/context and identifies affected uses.
- Evidence supersession/currentness and applicability to a particular target/use are separate. Supersession does not rewrite historical applicability or historical Inputs, Integrations, or Decisions.
- Evidence may carry broad staleness/attention status, but fitness for one target/version/use remains target-specific. PAIM has no universal Evidence expiry period.
- New target identity/version use requires a new Evidence Applicability judgment. Prior applicability is provenance only and never silently carries forward.
- `REFRESH REQUIRED` creates prospective attention/review and does not modify historical Evidence or Applicability content.

### 7.7 Material-Evidence fitness for Input acceptance

Every Evidence item declared material to a new Value or Risk Input acceptance/use must have a current Applicability result for its exact target context.

- Absence, unresolved Applicability conflict, `NOT_APPLICABLE`, or unresolved `REFRESH REQUIRED` blocks acceptance when that Evidence is required to support the Input's Finding, Boundary, or Implication.
- `CONDITIONALLY_APPLICABLE` and `PARTIALLY_APPLICABLE` support only their recorded scope/conditions and cannot justify a broader Input Boundary.
- `INDETERMINATE` remains unresolved. The separate accountable lane-level fitness determination defined by the Value/Risk Interface records whether the bounded Input remains supportable for that exact use and why. It blocks when decision-limiting to that analytical Input/use; general management-level uncertainty classification remains with Integration/Decision.
- Evidence linked as limitation, dissent, or conflict need not become favorable support, but its role/provenance remains explicit.

The platform may enforce references, time, scope, status, and conflict. It may not automatically decide substantive applicability or Input fitness.

### 7.8 Normative examples

1. Evidence applicable to Configuration A does not apply to Configuration B or a changed Version B without a new Applicability judgment.
2. `PARTIALLY_APPLICABLE` Evidence scoped to one population cannot support a broader Value or Risk Input Boundary.
3. Two incompatible co-current Applicability judgments return explicit conflict. An accountable successor may resolve prospective use while retaining both predecessors.
4. An assignment accountable only for unrelated Configuration B cannot finalize Applicability for Configuration A. Applicable broad and narrow competing accountable assignments remain conflict absent explicit supersession/delegation.
5. `INDETERMINATE` Evidence can support or block only through the separate exact lane-level fitness determination; it has no global default.

## 8. Evidence Versioning and Supersession

Evidence may be updated, corrected, replaced, or superseded.

The system should distinguish:

### New evidence

Adds information without invalidating prior evidence.

### Correction

Repairs an error in a prior evidence record while preserving traceability to the original.

### Superseding evidence

Provides a newer or more authoritative basis that changes which evidence should govern current analysis.

### Conflicting evidence

Materially disagrees with existing evidence and requires analytical treatment rather than silent replacement.

Historical evidence should remain available for reconstructing prior decisions.

Every correction, supersession, withdrawal, and current-evidence determination follows `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §3. Conflicting Evidence content remains explicit; Evidence currentness and Applicability currentness use separate selection contexts, and neither chooses a winner merely because one record is newer.

## 9. Evidence Provenance Chain

Derived evidence should preserve its source chain.

Example:

```text
Source records
    |
    v
Measured observations
    |
    v
Derived calculation
    |
    v
Value finding
    |
    v
Value Management Input
    |
    v
PAIM Decision
```

The system need not expose every transformation to every practitioner at all times, but the chain should be inspectable when needed.

## 10. Evidence Quality and Limitations

PAIM should not impose one universal evidence-quality score.

Instead, material limitations may include:

- incomplete coverage;
- small sample;
- enriched sample;
- short observation period;
- counterfactual dependence;
- measurement uncertainty;
- unresolved cases;
- source-quality limitation;
- selection bias;
- model dependence;
- stale evidence;
- operating-condition mismatch.

These limitations should be available to analytical and management users.

## 11. Authority Is Distinct from Evidence

Authority answers:

> **What requirement, permission, prohibition, responsibility, or decision right governs this configuration or decision?**

Evidence answers:

> **What do we know about the configuration, its value, risk, controls, or operation?**

An authority record may itself rely on documentary evidence, but PAIM must preserve the conceptual distinction.

## 12. Authority Record

A material Authority Record should support:

### Identity

- Authority ID
- title/label
- authority category
- source
- owner/interpreter where relevant
- status

### Scope

- configuration(s);
- activity/process;
- data/information;
- users/population;
- geography/jurisdiction where relevant;
- operating state;
- decision type;
- control/oversight requirement.

### Requirement

- obligation;
- prohibition;
- permission;
- decision right;
- required control;
- required oversight;
- escalation requirement;
- other binding condition.

### Time

- effective date/period where relevant;
- review/expiry date where relevant;
- superseding authority if any.

### Provenance

- governing source;
- source reference;
- interpretation source where necessary;
- version/vintage.

## 13. Authority Categories

Possible categories include:

- organizational policy;
- delegated management authority;
- contractual requirement;
- legal/regulatory requirement;
- safety requirement;
- privacy/confidentiality requirement;
- cybersecurity requirement;
- data/information restriction;
- records/retention requirement;
- mandatory oversight/review;
- provider/vendor requirement;
- other binding organizational requirement.

The system should not assume all categories are relevant to every case.

## 14. Authority Status

Possible authority statuses include:

- established/current;
- under review;
- unresolved;
- superseded;
- expired/inactive;
- not applicable.

The platform may later refine this vocabulary.

## 15. AUTHORITY UNRESOLVED

Where a decision depends on governing authority that has not been established, PAIM records:

> **AUTHORITY UNRESOLVED**

Minimum unresolved-authority content:

- Authority Gap ID
- question/subject
- decision affected
- configuration/scope affected
- authority/source needed
- owner responsible for resolution where assigned
- whether current bounded decision may proceed
- rationale
- status
- date raised
- resolution linkage when completed

An unresolved authority is neither a favorable nor unfavorable conclusion.

`DECISION AUTHORITY UNRESOLVED` is an Authority Gap classification governed by `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §6.3. A narrower bounded decision may proceed with another Authority Gap unresolved only through the separately valid bounded-proceed authorization rule in §6.4 of that specification; the gap itself never grants permission.

## 16. Authority Gap Outcomes

An Authority Gap may resolve as:

- requirement established;
- prohibition established;
- permission/authority established;
- not applicable to bounded decision;
- decision reframed so authority is no longer material;
- remains unresolved.

Resolution must preserve the prior unresolved record.

## 17. Authority Applicability

Authority may bind:

- an entire case;
- one configuration/version;
- a data class;
- one activity;
- one user/customer population;
- one jurisdiction;
- one operating state;
- one decision;
- one control.

When relevant configuration elements change, authority applicability must be reassessed.

## 18. Authority Conflict

Two authority sources may conflict or appear inconsistent.

The system should not automatically choose a winner unless an established authority hierarchy governs the situation.

Record:

- conflicting authorities;
- scope;
- affected decision;
- interpretation needed;
- governing resolution if obtained.

Until resolved, use `AUTHORITY UNRESOLVED` where the conflict is material to the decision.

## 19. Evidence-to-Finding Relationship

A Finding should be traceable to the Evidence Records supporting it.

A finding relationship may identify evidence as:

- primary support;
- corroborating support;
- limitation;
- conflicting evidence;
- contextual evidence.

This supports later review without requiring a universal evidence score.

## 20. Evidence-to-Uncertainty Relationship

Uncertainty should also be traceable.

The system should support:

```text
Known evidence
     |
     +--> supports current finding
     |
     +--> leaves gap
              |
              v
          Uncertainty
              |
              v
       Learning / Reassessment
```

A new Evidence Record may reduce, resolve, or reclassify uncertainty.

## 21. Evidence-to-Control Relationship

Evidence may support:

- control presence;
- control design;
- control effectiveness;
- control burden;
- control failure;
- control dependency.

The system should distinguish a control being **documented** from a control being **demonstrated effective**.

## 22. Evidence-to-Decision Relationship

A Management Decision Record should identify the material Value/Risk evidence and authority relied upon.

The decision does not need to duplicate the full evidence package.

It should preserve enough linkage to reconstruct the basis later.

## 23. Evidence Freeze and Analytical Inputs

When a Value or Risk Management Input is frozen for integration:

- the input remains immutable as the contributing conclusion for that decision;
- underlying evidence remains historically linked;
- later evidence does not silently rewrite the frozen input;
- new evidence may trigger a refreshed/successor input and reassessment.

This preserves the discipline demonstrated in IET 004.

## 24. Frozen-Input Fidelity

Phase II identified a risk that integration may paraphrase frozen implications inaccurately.

System safeguard candidate:

> **Display/reproduce the frozen Value and Risk Implications verbatim during Decision Integration.**

The system may permit interpretation around them but should preserve the original text/status.

## 25. Evidence Refresh

Evidence refresh may be triggered by:

- staleness;
- configuration change;
- provider/model change;
- new operating conditions;
- new incident;
- new observation;
- new authority;
- completed learning item;
- scheduled review;
- conflicting evidence.

Refresh does not necessarily invalidate the prior decision immediately. It creates a reassessment question.

## 26. Evidence Staleness

PAIM should not impose one universal expiration period.

Evidence may become stale when:

- its operating context no longer matches;
- relevant model/provider changes;
- source data changes materially;
- business conditions change;
- control design changes;
- time-sensitive facts age;
- authority changes.

Staleness is contextual.

## 27. Evidence and Decision-Limiting Uncertainty

A Decision-Limiting Uncertainty should identify what evidence would allow reconsideration of the blocked stronger/broader/different decision.

Example:

```text
Uncertainty: selective control effectiveness unknown
Blocked decision: normal operation under redesigned configuration
Evidence needed: prospective validation
```

This relationship should be first-class in the system.

## 28. Evidence and Accepted Uncertainty

Accepted Uncertainty should identify:

- why current evidence is sufficient for the bounded decision;
- what remains unknown;
- what should be observed;
- what change would make the uncertainty decision-limiting.

## 29. Minimum Evidence Record

Minimum fields:

- Evidence ID
- Evidence Version ID
- title
- case/configuration relationship
- classification
- maturity where used
- source/provenance
- date/context
- recorded time and effective time/interval
- evidence statement/result
- scope
- limitations
- status
- exact Evidence Applicability Record/Version relationships
- related finding/uncertainty/control/decision
- predecessor/superseding evidence where applicable

### 29.1 Minimum Evidence Applicability Record

Minimum fields are those in §7.1, including exact endpoint Versions, target type, purpose/use, assessed scope, outcome, conditions/limitations, rationale, assessor, accountable assignment/mechanism, effective/recorded time, status, history relationships, and affected-use references.

## 30. Minimum Authority Record

Minimum fields:

- Authority ID
- Authority Version ID
- title
- category
- source/provenance
- status
- scope/applicability
- requirement/decision right
- effective period where relevant
- recorded time
- affected configuration/decision/control
- predecessor/superseding authority where applicable

## 31. Minimum Authority Gap Record

Minimum fields:

- Authority Gap ID
- Authority Gap Version ID
- question
- decision affected
- scope/configuration affected
- authority needed
- current proceed/block status
- rationale
- owner
- status
- date raised
- recorded/effective time
- resolution record

## 32. Integrity Checks

The system should be able to surface:

- Finding with no supporting evidence linkage;
- evidence used outside configuration applicability;
- Evidence Applicability stored only as mutable Evidence/target metadata;
- missing exact Evidence or target Version for a content-dependent judgment;
- Applicability outcome outside the normative §7.3 vocabulary;
- conditional/partial judgment missing scope, conditions, or limitations;
- `REFRESH REQUIRED` or conflict treated as a stored applicability outcome;
- `INDETERMINATE` treated as permission or prohibition without a separate accountable fitness judgment;
- Applicability absence/conflict hidden by newest, most-specific, current-flag, or permission fallback;
- applicability finalized under vacant, conflicting, unrelated-scope, or permission-derived accountability;
- Evidence reused for a new target/version without a new Applicability judgment;
- stale/superseded evidence still treated as current;
- unresolved conflicting evidence hidden from integration;
- authority cited without source/provenance;
- decision relying on unresolved authority without explicit treatment;
- authority applied outside its scope;
- frozen input silently changed after new evidence;
- uncertainty marked resolved without new evidence/authority;
- control treated as effective with no effectiveness evidence where effectiveness is material.

These are integrity checks, not automated substantive judgments.

## 33. Human Judgment Points

Human/accountable judgment remains necessary for:

- interpreting evidence;
- determining material limitations;
- deciding applicability;
- determining the exact assessed scope, conditions, limitations, and rationale;
- determining target-context Applicability accountability and resolving incompatible judgments;
- distinguishing supported inference from assumption;
- resolving conflicting evidence;
- interpreting authority;
- deciding whether unresolved authority blocks the current bounded decision;
- determining whether new evidence requires reassessment.

## 34. Platform Implications

A future platform will likely require:

- evidence register;
- evidence detail/provenance view;
- source attachment/reference;
- evidence-to-finding linkage;
- authority register;
- authority-gap queue;
- applicability/status indicators;
- supersession/history;
- uncertainty-learning linkage;
- contextual display during Value/Risk/Integration;
- audit/history view.

This specification does not prescribe the UI.

## 35. Behavioral Test Candidates

Future system tests should include:

1. Add new evidence that conflicts with a current finding.
2. Supersede an evidence record and confirm historical decisions retain original provenance.
3. Apply evidence to a materially different Configuration/version and require a new Applicability judgment.
4. Introduce an unresolved legal/authority question and ensure the system does not imply permission.
5. Resolve an Authority Gap and trigger reassessment of the blocked decision.
6. Mark evidence stale after a model/provider change.
7. Attempt to modify a frozen Value/Risk Input after new evidence arrives.
8. Introduce an estimate and ensure it is not represented as observed evidence.
9. Introduce a control with documented presence but no effectiveness evidence.
10. Remove evidence supporting a Decision-Limiting Uncertainty resolution and require review.
11. Create incompatible co-current Applicability judgments and return explicit conflict.
12. Resolve Applicability conflict with an accountable successor while preserving both prior judgments.
13. Reject conditional/partial Evidence as support outside its recorded scope.
14. Reject unrelated-scope applicability accountability and expose broad/narrow accountability conflict.
15. Exercise `INDETERMINATE` with separate supportable and blocked lane-level fitness judgments.
16. Correct Evidence content and Applicability judgment independently, preserving every prior Version.

## 36. Open Questions

Deferred for later specifications/platform design:

- exact evidence classification vocabulary;
- whether maturity states are mandatory or optional;
- source-document storage vs. reference behavior;
- authority interpretation workflow;
- formal authority hierarchy;
- evidence retention policy;
- confidentiality/access restrictions;
- automated staleness-attention suggestions, which must not replace target-specific judgment;
- evidence deduplication;
- external-system ingestion.

## 37. Completion Impact

This specification substantially advances the Evidence and Authority Management capability in the system gap map.

Remaining work includes:

- Value/Risk Interface Record;
- Integration/Decision Record;
- intervention/learning records;
- platform persistence/access design;
- authority permissions;
- behavioral validation.

## 38. Next Specification

Create:

`PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md`

This should formalize:

- common five-part interface;
- configuration binding;
- input identity/version;
- freeze/supersession;
- evidence linkage;
- analytical independence;
- applicability;
- refresh/reassessment;
- frozen-implication fidelity.

## 39. Repository Placement

```text
400. Practical AI Management/
└── system/
    └── specifications/
        ├── PAIM_CASE_LIFECYCLE_SPEC_v0.1.md
        ├── PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md
        └── PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md
```

## 40. Conclusion

The Evidence and Authority specification establishes the evidentiary backbone required for PAIM to operate as a durable management system.

It preserves a critical separation:

> **Evidence tells management what is known.**

> **Authority tells management what governs.**

> **Analysis converts evidence into findings.**

> **PAIM converts independent findings, authority, uncertainty, and alternatives into accountable management judgment.**

Without this separation, a platform could make decisions appear more certain or more authorized than the underlying record supports.
