# PAIM Value/Risk Interface Specification v0.1

## Status

Implementation-independent system specification for the common interface by which Value Management and Risk Management contribute analytical conclusions to Practical AI Management (PAIM).

This specification derives from:

- `PAIM_SYSTEM_ARCHITECTURE_v0.1.md`
- `PAIM_SYSTEM_COMPLETION_BASELINE_GAP_MAP_v0.1.md`
- `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`
- `PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md`
- `PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md`
- `PAIM_MINIMUM_MANAGEMENT_CASE_v0.3.md`
- `PAIM_PRACTITIONER_PLAYBOOK_v0.2.md`
- IET 001–004 validation findings.

It defines what the PAIM system must preserve when receiving, freezing, versioning, refreshing, and integrating Value and Risk Management Inputs.

It does not prescribe the internal methodology used by AIVM, Risk Management, or another compatible contributing analytical capability.

**Normative cross-cutting contract:** `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md` governs stable Input identity vs. immutable Input Version identity, draft/finalization boundaries, freeze as finalization, status events, recorded/effective time, correction/supersession/withdrawal, authoritative current selection, conflict behavior, and exact historical retrieval.

## 1. Purpose

PAIM requires Value and Risk analyses to remain analytically distinct while exposing a compact common interface sufficient for management integration.

The common interface is:

1. **Finding**
2. **Boundary**
3. **Uncertainty**
4. **Implication**
5. **Provenance**

IET 004 provisionally demonstrated that independently constructed five-part inputs can be sufficient for downstream PAIM Decision Integration.

The system must preserve that interface without turning it into a universal score or forcing Value and Risk to use identical internal methods.

## 2. Interface Principle

The interface is a **management boundary between analytical capabilities and PAIM integration**.

Conceptually:

```text
Detailed Value Analysis
        |
        v
Value Management Input
[Finding / Boundary / Uncertainty / Implication / Provenance]
        |
        +----------------------+
                               |
                               v
                         PAIM Integration
                               ^
                               |
        +----------------------+
        |
Risk Management Input
[Finding / Boundary / Uncertainty / Implication / Provenance]
        ^
        |
Detailed Risk Analysis
```

PAIM consumes the compact interfaces, not necessarily every underlying analytical workpaper.

## 3. Common Structure, Different Meaning

The five fields are structurally common but retain domain-specific meaning.

### Value Finding

What organizational value is supported by the evidence?

### Risk Finding

What material adverse pathways, control conditions, residual exposure, or other Risk conclusions are supported?

### Value Boundary

Where does the Value finding apply?

### Risk Boundary

Where does the Risk finding apply?

### Value Uncertainty

What material Value questions remain unresolved?

### Risk Uncertainty

What material Risk questions remain unresolved?

### Value Implication

What operating action/state does Value Management alone support?

### Risk Implication

What operating action/state does Risk Management alone support?

### Provenance

What evidence and analytical record support the contributing conclusion?

The common interface must not imply that Value and Risk are interchangeable analytical domains.

## 4. Input Identity

Every Value or Risk Management Input should have a durable identity.

Minimum identity fields:

- Input ID
- Input Version ID
- input type: Value or Risk
- Case ID
- Managed Configuration ID/version
- input version
- status
- analytical owner/source
- creation date
- recorded time
- effective/current date where relevant
- predecessor/superseding input
- freeze status

## 5. Input Status

Possible statuses include:

- draft;
- in progress;
- ready;
- frozen/current;
- refresh required;
- superseded;
- withdrawn.

The exact platform vocabulary may later be refined.

A draft input must not be represented as a frozen contributing conclusion.

`frozen` and `current` are distinct properties. Freeze finalizes one immutable content version; currentness is derived for a declared configuration, purpose, scope, and time under `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §§3.4 and 3.11. A frozen historical input remains frozen even after it is no longer current.

## 6. Configuration Binding

Every input must identify the Managed Configuration/version to which it applies.

The system should detect when:

- Value and Risk Inputs refer to different configuration versions;
- a configuration materially changes after an input is frozen;
- an input is being reused outside its boundary;
- an input has become refresh-required.

A common case title is not sufficient configuration binding.

## 7. Finding

The Finding should state the analytical conclusion supported by the contributing analysis.

A strong Finding should:

- identify what is supported;
- avoid overstating evidence maturity;
- preserve important qualifications;
- remain understandable without reading the entire underlying analysis.

The Finding should not contain the final PAIM management judgment.

## 8. Boundary

The Boundary defines where the contributing Finding applies.

Possible dimensions include:

- activity/task;
- assignment/use class;
- user/customer population;
- information/data conditions;
- AI authority;
- human authority;
- controls;
- model/provider;
- operating conditions;
- capacity;
- geography;
- time/context;
- explicit exclusions.

The contributing Boundary is not the final Integrated Operating Boundary.

## 9. Uncertainty

The contributing input should preserve material uncertainty rather than resolving it through PAIM language prematurely.

The input may identify:

- unknowns;
- estimates/counterfactual dependence;
- evidence persistence;
- operating-condition uncertainty;
- control-effectiveness uncertainty;
- external consequence uncertainty;
- authority gaps where relevant.

PAIM later classifies uncertainty relative to the management decision as Accepted or Decision-Limiting.

The contributing analytical capability may use its own uncertainty taxonomy internally.

## 10. Implication

The Implication states what the contributing analytical capability alone supports now.

Examples:

- continue;
- target;
- constrain;
- experiment;
- do not expand;
- institutionalize within boundary;
- suspend;
- redesign;
- obtain authority/evidence before stronger action.

The Implication must remain independent of the other analytical leg.

It should not be rewritten after seeing the other input merely to create agreement.

## 11. Provenance

Provenance should link the compact input to the evidence and analytical record supporting it.

At minimum:

- underlying analysis/case record;
- material Evidence Records;
- relevant configuration;
- analytical owner/source;
- date/version.

Provenance may identify evidence as observed, inferred, estimated, assumed, or unknown where useful.

## 12. Analytical Independence

The system should preserve analytical independence through process and record design.

At minimum:

- Value Input may be constructed without knowing the desired Risk conclusion;
- Risk Input may be constructed without knowing the desired Value conclusion;
- one input cannot overwrite the other;
- integration occurs after contributing conclusions are available;
- disagreements remain visible.

Literal separate evaluators are desirable where appropriate but are not required by this specification for every organization.

## 13. Freeze

A contributing input becomes **frozen** when it is accepted as the analytical conclusion used for a particular PAIM integration/decision.

Freeze means:

- the five-part content is immutable for that decision;
- later evidence does not silently modify it;
- integration may quote, interpret, and compare it but not rewrite it;
- corrections require a traceable corrected/successor input;
- refreshed analysis creates a new version.

Freeze is an analytical-history rule, not a claim that the conclusion is permanently true.

Freeze is the finalization boundary for the selected Input version under `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §3.4. Later status changes never reopen its five-part content.

## 14. Frozen-Implication Fidelity

IET 004 exposed paraphrase drift during integration.

The system should therefore preserve and prominently display the frozen Implications verbatim during PAIM Integration.

Recommended system behavior:

```text
Frozen Value Implication:
[verbatim text]

Frozen Risk Implication:
[verbatim text]
```

Interaction analysis then occurs beneath or beside those immutable statements.

This reduces accidental reinterpretation.

## 15. Input Versioning

Example:

```text
VALUE-001 v1 — frozen for Decision D1
       |
       | new evidence / reassessment
       v
VALUE-001 v2 — frozen for Decision D2
```

Both remain available.

The same applies to Risk Inputs.

## 16. Refresh Required

An input may become `refresh required` when:

- configuration changes materially;
- evidence becomes stale;
- new conflicting evidence appears;
- material control changes;
- provider/model changes;
- operating conditions change;
- authority changes;
- reassessment requires a stronger/broader decision.

Refresh-required status does not itself rewrite the historical input.

## 17. Supersession

A new input supersedes an older input for current analysis only when explicitly established.

The older input remains the authoritative historical input for the decision that used it.

The system must distinguish:

- current input;
- historical frozen input;
- superseding input.

## 18. Corrections

If an input contains an error:

- preserve the original;
- create a correction or successor version;
- identify reason;
- identify decisions potentially affected;
- trigger reassessment where material.

Do not silently edit a historical frozen input.

## 19. Evidence Linkage

Each input should support linkage from its five fields to underlying evidence where useful.

For example:

```text
Finding
  +-- Evidence E1
  +-- Evidence E2

Boundary
  +-- Evidence E3

Uncertainty
  +-- Evidence E4
  +-- Unknown U1

Implication
  +-- derived from Finding + Boundary + Uncertainty
```

The platform need not force field-by-field citation where it creates unreasonable burden, but traceability must be available.

## 20. Authority Linkage

An input may reference established authority or unresolved authority where relevant to the analytical conclusion.

However, the Value or Risk analytical leg should not invent authority.

If authority is missing:

> **AUTHORITY UNRESOLVED**

The final PAIM Integration determines the management significance relative to the decision.

## 21. Interface Sufficiency

The interface is intended to be compact enough for integration while preserving the essential analytical structure.

It should contain enough information to answer:

- What does this analytical leg conclude?
- Where does the conclusion apply?
- What remains uncertain?
- What action does this leg support?
- What evidence supports it?

If PAIM Integration repeatedly requires reopening full analytical workpapers, that is evidence that the interface may be insufficient and should be investigated.

## 22. Interface Limitation Handling

If an integrator determines that a needed fact is absent:

- do not invent it;
- record the missing information;
- determine whether integration can proceed;
- request analytical clarification or refreshed input where necessary.

The integrator may not silently reconstruct the contributing analysis.

## 23. Value/Risk Agreement

Agreement should be preserved as independent reinforcement, not collapsed into a single conclusion.

Example:

```text
Value Implication: TARGET + CONTINUE
Risk Implication: TARGET + CONSTRAIN + CONTINUE

PAIM interaction: reinforcement on targeted continuation;
Risk adds conditions to the final operating boundary.
```

## 24. Value/Risk Conflict

Conflict must remain explicit.

Example:

```text
Value prefers Configuration A.
Risk does not support A.
Risk supports Configuration B.
B materially changes Value.
Configuration C may reconcile the conflict but is unvalidated.
```

PAIM then generates alternatives and management judgment.

The system should never rewrite the Value Finding to make B appear valuable or weaken the Risk Finding to preserve A.

## 25. Control Dependencies Across Inputs

The interface should preserve controls that materially affect either analytical conclusion.

PAIM Integration then determines:

- which controls affect both;
- whether control burden changes Value;
- whether control removal invalidates Risk;
- whether the control must be present in the Integrated Operating Boundary.

## 26. Boundary Comparison

The system should be able to compare:

```text
Value Boundary
vs.
Risk Boundary
vs.
Proposed Managed Configuration
```

Possible relationships:

- substantially aligned;
- Value narrower;
- Risk narrower;
- partially overlapping;
- materially conflicting;
- unclear.

This comparison supports, but does not replace, PAIM judgment.

## 27. Uncertainty Transfer to PAIM

Contributing uncertainty enters PAIM Integration without automatic classification.

PAIM then asks:

### Accepted

What remains unknown but does not prevent the current decision?

### Decision-Limiting

What remains unknown that prevents a stronger, broader, or different decision?

The system should preserve the contributing source of each uncertainty.

## 28. Input Construction from Fuller Evidence

IET 004 demonstrated a useful staged pattern:

```text
Fuller evidence
   |
   v
Construct Value Input
   |
FREEZE
   |
Construct Risk Input independently
   |
FREEZE
   |
PAIM Integration
```

The platform may support this workflow when analytical inputs are not already available.

The system should not require practitioners to expose or navigate development Markdown files; evidence should be surfaced through the system.

## 29. External Analytical Capabilities

PAIM should remain capable of consuming inputs from:

- AIVM;
- internal Risk Management;
- model-risk processes;
- safety/security assessments;
- vendor assessments;
- other compatible analytical capabilities.

Compatibility depends on producing the required five-part PAIM-facing interface, not on using one internal methodology.

## 30. Minimum Value/Risk Interface Record

### Identity
- Input ID
- Input Version ID
- type
- Case ID
- Configuration ID/version
- version
- status
- owner/source
- date
- recorded time and effective time/interval
- predecessor/successor
- freeze status

### Analytical content
- Finding
- Boundary
- Uncertainty
- Implication
- Provenance

### Relationships
- Evidence Records
- Authority Records/Gaps
- PAIM Integration Record(s)
- Management Decision(s)
- Reassessment(s)

### Applicability
- current/refresh-required/superseded
- configuration applicability
- known limitations

## 31. Interface Integrity Checks

The system should surface:

- missing one of the five required fields;
- input not bound to a configuration;
- Value and Risk Inputs bound to different configuration versions;
- frozen input modified after integration;
- superseded input used as current without explicit justification;
- implication paraphrased as though it were the original frozen text;
- provenance missing;
- material boundary absent;
- unresolved uncertainty omitted from integration;
- input used outside its applicability.

These checks support process integrity rather than automated substantive approval.

## 32. Human Judgment Points

Human/accountable judgment remains necessary for:

- constructing the analytical conclusion;
- defining the Boundary;
- deciding what uncertainty is material;
- selecting the contributing Implication;
- determining whether an input is ready to freeze;
- deciding whether new evidence requires refresh;
- interpreting differences between Value and Risk.

## 33. Platform Implications

A future platform will likely require:

- Value Input editor/view;
- Risk Input editor/view;
- status/freeze controls;
- configuration binding;
- evidence/provenance linkage;
- version history;
- side-by-side comparison;
- verbatim frozen Implication display;
- refresh-required indicator;
- supersession history;
- integration handoff.

This specification does not prescribe UI.

## 34. Behavioral Test Candidates

Future tests should include:

1. Freeze a Value Input, add new evidence, and confirm the historical input does not change.
2. Bind Value and Risk Inputs to different configuration versions and block/flag integration readiness.
3. Paraphrase a frozen Implication inaccurately and ensure the original remains visible.
4. Refresh Risk after a control change while retaining historical Risk for the prior decision.
5. Create Value/Risk conflict and verify neither input is rewritten.
6. Omit Boundary and confirm the interface is incomplete.
7. Attempt integration with a superseded input.
8. Use an input outside its applicability.
9. Resolve a contributing uncertainty and create a successor input.
10. Construct inputs from fuller evidence without exposing the other leg during analysis.

## 35. Open Questions

Deferred to later system/platform work:

- whether freeze requires explicit approval/signature;
- exact input status vocabulary;
- field-level evidence-linking requirements;
- machine-readable Boundary representation;
- structured vs. narrative Uncertainty;
- whether external systems can submit signed/frozen inputs;
- how to handle multiple simultaneous Value or Risk analyses;
- formal input acceptance/rejection workflow.

## 36. Completion Impact

This specification substantially advances the Value/Risk Interface capability in the system gap map.

The first five foundational system areas now have increasing definition:

- case lifecycle;
- managed configuration;
- evidence/authority;
- Value/Risk interface;
- PAIM Integration/Decision remains next.

## 37. Next Specification

Create:

`PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md`

It should formalize:

- integration identity/status;
- readiness;
- frozen-input handling;
- constraints/authority;
- Control Dependency;
- uncertainty classification;
- Integrated Operating Boundary;
- alternatives;
- interaction analysis;
- operating state;
- management judgment;
- authorization;
- immutable decision history;
- successor decisions.

## 38. Repository Placement

```text
400. Practical AI Management/
└── system/
    └── specifications/
        ├── PAIM_CASE_LIFECYCLE_SPEC_v0.1.md
        ├── PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md
        ├── PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md
        └── PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md
```

## 39. Conclusion

The Value/Risk Interface specification establishes the formal analytical handoff into PAIM.

Its central design rule is:

> **Preserve analytical independence in compact, configuration-bound, evidence-traceable, versioned inputs—and integrate them without rewriting them.**

This allows PAIM to remain compatible with different analytical capabilities while maintaining a stable management architecture.
