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

Every candidate or selected Value or Risk Management Input is an authoritative PAIM record with a durable identity. Candidate status does not make the Input selected for an Integration use, and selection does not create a different analytical lane or combined Value/Risk record.

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
- disposition history for each bounded use

Value and Risk Input identities and histories remain separate. Analytical workpapers or external submissions may be provenance sources, but a PAIM-facing candidate Input contains the complete five-part lane conclusion and exact Configuration binding required by this specification.

## 5. Input Status

Input content/lifecycle statuses include:

- draft;
- in progress;
- ready;
- frozen;
- refresh required;
- superseded;
- withdrawn.

A draft input must not be represented as a frozen contributing conclusion.

`ready`, `frozen`, `accepted`, `selected`, `reused`, `rejected for use`, `withdrawn`, `superseded`, and `refresh required` are distinct facts:

- `ready` is an attributed analytical-readiness event stating that the producer regards a candidate Input as complete enough for accountable acceptance review;
- `frozen` means the exact Input Version's five-part content has crossed the immutable finalization boundary;
- `accepted` and `selected` are use-specific results recorded by the lane-specific Input Acceptance/Selection relationship in §13;
- `reused` means an already frozen Input Version has a new acceptance for another bounded use;
- `rejected for use` is a use-specific disposition and does not erase or globally invalidate the Input;
- `withdrawn` ends prospective reliance for its declared scope/time without rewriting prior use;
- `superseded` identifies a prospective successor for a declared scope/time; and
- `refresh required` is prospective attention/status and does not reopen frozen content.

Freeze and currentness are distinct. Freeze is global to one immutable Input Version. Current selected eligibility is derived for a declared lane, Configuration Version, bounded use/purpose, effective time, and optional knowledge cutoff under `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §§3.4 and 3.11. A frozen historical Input remains frozen after it is no longer eligible for a new use.

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

A candidate Input becomes **frozen** at its first valid lane-specific acceptance for a bounded Integration use. Analytical readiness is separate and does not freeze or select the Input.

Freeze means:

- the five-part content is immutable for that decision;
- later evidence does not silently modify it;
- integration may quote, interpret, and compare it but not rewrite it;
- corrections require a traceable corrected/successor input;
- refreshed analysis creates a new version.

Freeze is an analytical-history rule, not a claim that the conclusion is permanently true.

Freeze is global finalization of the exact Input Version under `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, §3.4. The first valid acceptance/selection semantic commit atomically:

1. finalizes and freezes that exact Input Version if it is not already frozen; and
2. records the exact bounded acceptance/selection described below.

Later status changes never reopen its five-part content. Later use of the same frozen Input Version creates a new acceptance/reuse record and does not refreeze or copy the Input content.

### 13.1 Input Acceptance/Selection identity

Value Input Acceptance/Selection and Risk Input Acceptance/Selection are separate authoritative relationship families. Every acceptance/selection supports:

- stable Acceptance/Selection Record ID;
- immutable Acceptance/Selection Version ID;
- exact lane: Value or Risk;
- exact Input ID and Input Version ID;
- exact owning Case and Managed Configuration ID/Version;
- bounded use or Integration-path identity and purpose;
- outcome/disposition;
- rationale, including reuse/fitness rationale where applicable;
- effective time/interval and recorded time;
- exact accountable Role Assignment version or explicitly governed accountable mechanism;
- predecessor, correction, supersession, or withdrawal relationship and reason; and
- exact material Evidence Applicability versions and lane-level fitness determination relied upon.

A mutable `selected` flag on the Input is not an Acceptance/Selection record.

### 13.2 Lane-specific selection

For one explicit Value or Risk lane, Configuration Version, bounded use/purpose, effective time, and optional knowledge cutoff, current selection returns exactly one of:

- one eligible accepted frozen Input Version and its exact Acceptance/Selection Version;
- `INPUT SELECTION NOT ESTABLISHED`; or
- `INPUT SELECTION CONFLICT — UNRESOLVED` with every incompatible candidate and reason.

The platform must not choose by newest/latest date, owner, readiness/status label, row order, specificity, directory hierarchy, or convenience. Value and Risk selection are evaluated independently. No shared acceptance shortcut or combined score may satisfy both lanes.

Zero eligible Acceptance/Selection Versions returns `INPUT SELECTION NOT ESTABLISHED`, regardless of how many co-current `ready` candidate Inputs exist. Two or more ready candidates remain preserved candidate alternatives and do not create authoritative selection conflict merely by being ready. Selection conflict arises only when two or more incompatible co-current eligible Acceptance/Selection Versions compete for the same explicit lane, exact Configuration Version, bounded use/purpose, effective time, and optional knowledge cutoff. An acceptance semantic commit that establishes one eligible selection must identify the accepted Input and record explicit non-selected/dissenting/rejected-for-use dispositions or supersession for every competing candidate material to that use. The resulting found selection is exactly one accepted/frozen Input and its exact Acceptance/Selection Version.

### 13.3 Acceptance accountability

Analytical production/readiness and acceptance accountability are distinct facts. Each lane acceptance must resolve for the exact lane, Configuration, bounded use, and effective time to:

- exactly one applicable accountable Role Assignment or one explicitly governed accountable mechanism;
- explicit vacancy/not established; or
- explicit incompatible-accountability conflict.

One actor may produce/declare readiness and accept only when separately applicable assignments/mechanisms establish both functions. Authorship, integrator participation, Evidence ownership, software permission, technical-principal identity, or a generic role label does not establish acceptance accountability. Broad and narrow assignments have no implicit precedence. Input acceptance never creates Decision Authority.

### 13.4 Candidate dispositions and history

Candidate Inputs and their exact content remain preserved whether selected, non-selected, dissenting, rejected for a use, withdrawn, corrected, or superseded. A use-specific disposition records the Input Version, bounded use, disposition, actor/accountable basis where required, rationale, effective/recorded time, and predecessor/history.

`dissenting` preserves a materially competing conclusion; it is not synonymous with invalid. `rejected for use` makes the Input ineligible for that bounded use but does not delete it or automatically reject it for every future use.

### 13.5 Reuse

An already frozen Input Version may support more than one Integration only when every later use has a new explicit Acceptance/Selection Version. The reuse acceptance binds the exact current governing Configuration Version, bounded use/purpose, material Evidence Applicability basis, lane-level fitness judgment, accountability, rationale, and time.

Historical frozen status or absence of `refresh required` is not sufficient for reuse. Prior acceptance is provenance only for the later fitness judgment.

### 13.6 Material-Evidence fitness gate

Every Evidence item declared material to a new acceptance/use must have a current Evidence Applicability result for its exact target context.

- Applicability absence, unresolved conflict, `NOT_APPLICABLE`, or unresolved `REFRESH REQUIRED` blocks acceptance when the Evidence is required to support the Input's Finding, Boundary, or Implication.
- `CONDITIONALLY_APPLICABLE` and `PARTIALLY_APPLICABLE` may support only within their recorded scope, conditions, and limitations; they cannot justify a broader Input Boundary.
- `INDETERMINATE` remains indeterminate. A separate accountable lane-level fitness determination records whether the bounded Input remains supportable for that exact use and why. It blocks when the unresolved matter is decision-limiting to that analytical Input/use. General management-level Decision-Limiting Uncertainty classification remains governed by Integration/Decision.
- Evidence linked as limitation, dissent, or conflict need not become favorable support, but its role and provenance remain explicit.

The platform may verify presence, exact references, scope containment, and conflict. It must not compute a universal evidence-sufficiency or confidence score or replace the accountable fitness judgment.

### 13.7 Withdrawal, rejection, and later change

Withdrawal or rejection of a selected Input before Integration readiness makes that acceptance/selection ineligible and blocks the affected handoff. Correction creates a new Input Version and identifies affected uses. Supersession changes prospective eligibility only for its declared scope/time.

Withdrawal, correction, supersession, staleness, or Evidence change after a historical Integration/Decision never rewrites the frozen Input or historical basis. It creates prospective attention, refresh, successor-analysis, or reassessment consequences where material.

### 13.8 Normative selection examples

1. Two co-current ready Value Inputs for the same Configuration/use do not produce a winner. Until an accountable acceptance/supersession establishes one eligible result, Value selection is conflict and the handoff is blocked.
2. One accepted Value Input and one accepted Risk Input, each bound to the same exact governing Configuration Version and each with an eligible Acceptance/Selection Version, satisfy the input-cardinality portion of the handoff.
3. Reusing a frozen Risk Input for a later use creates a new Risk Acceptance/Selection Version referencing the same immutable Risk Input Version.
4. A selected Input withdrawn before Integration readiness becomes ineligible. The same withdrawal after a historical Decision preserves the historical basis and creates only prospective attention/reassessment where material.
5. An accountable acceptance assignment valid only for unrelated Configuration B cannot accept an Input for Configuration A. Applicable broad and narrow competing accountable assignments produce conflict absent explicit supersession or delegation.

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

An unresolved `refresh required` status makes a new acceptance/reuse ineligible when the affected Evidence or analytical conclusion is material to that use. It does not retroactively invalidate a historical acceptance.

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

Every Evidence item declared material to an acceptance/use must additionally link to the exact current Evidence Applicability Version used by the §13.6 fitness gate.

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
- exact material Evidence Applicability Versions and their roles
- Authority Records/Gaps
- Input Acceptance/Selection Versions and use-specific dispositions
- PAIM Integration Record(s)
- Management Decision(s)
- Reassessment(s)

### Applicability
- prospective status such as refresh-required, superseded, or withdrawn
- selected current use only through exact Acceptance/Selection Version
- configuration applicability
- known limitations

### Minimum Input Acceptance/Selection record
- Acceptance/Selection Record ID and Version ID
- lane
- exact Input and Configuration Versions
- bounded use/Integration-path identity and purpose
- outcome/disposition and rationale
- effective/recorded time
- accountable assignment/mechanism
- exact material Evidence Applicability Versions
- lane-level fitness determination
- predecessor/correction/supersession/withdrawal history

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
- ready Input treated as accepted or frozen without an eligible Acceptance/Selection Version;
- more than one incompatible accepted Input for one lane/use;
- selected Value and Risk Inputs or their acceptances bound to different Configuration Versions;
- reuse without a new use-specific acceptance/fitness judgment;
- acceptance with vacant, conflicting, unrelated-scope, or permission-derived accountability;
- rejected/withdrawn Input still treated as eligible before Integration;
- material Evidence applicability absent, conflicting, not applicable, refresh-required, or broader than its recorded conditional/partial scope;
- `INDETERMINATE` treated as globally permitted or prohibited without the lane-level fitness determination;
- non-selected or dissenting Input erased or rewritten.

These checks support process integrity rather than automated substantive approval.

## 32. Human Judgment Points

Human/accountable judgment remains necessary for:

- constructing the analytical conclusion;
- defining the Boundary;
- deciding what uncertainty is material;
- selecting the contributing Implication;
- declaring whether an input is analytically ready;
- accepting/selecting the exact Input for a bounded use under applicable accountability;
- determining lane-level material-Evidence fitness, including treatment of `INDETERMINATE`;
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

1. First-accept a Value Input and confirm that freeze and bounded selection commit atomically while later Evidence does not change the Input.
2. Bind Value and Risk Inputs to different configuration versions and block/flag integration readiness.
3. Paraphrase a frozen Implication inaccurately and ensure the original remains visible.
4. Refresh Risk after a control change while retaining historical Risk for the prior decision.
5. Create Value/Risk conflict and verify neither input is rewritten.
6. Omit Boundary and confirm the interface is incomplete.
7. Attempt integration with a superseded input.
8. Use an input outside its applicability.
9. Resolve a contributing uncertainty and create a successor input.
10. Construct inputs from fuller evidence without exposing the other leg during analysis.
11. Create two ready Value candidates for one use and confirm `INPUT SELECTION NOT ESTABLISHED` while no eligible Acceptance/Selection Version exists; create two incompatible co-current eligible acceptances and confirm `INPUT SELECTION CONFLICT — UNRESOLVED`; then retain one accountable eligible acceptance with explicit competitor dispositions and confirm the one accepted/frozen Input and exact Acceptance/Selection Version are found.
12. Reuse one frozen Input for a later use and confirm a new acceptance references the same Input Version.
13. Withdraw a selected Input before readiness and block; withdraw it after a historical Decision and preserve history.
14. Reject an unrelated-scope acceptance assignment and expose broad/narrow accountable conflict without implicit precedence.
15. Reject conditional/partial Evidence as support for a broader Input Boundary.
16. Exercise both supportable and blocked `INDETERMINATE` cases through explicit lane-level fitness determinations.

## 35. Open Questions

Deferred to later system/platform work:

- approval/signature technology used to evidence an accepted accountable event;
- field-level evidence-linking requirements;
- machine-readable Boundary representation;
- structured vs. narrative Uncertainty;
- how an external signed candidate assertion maps into PAIM provenance and accountable acceptance without writing finalized state directly;
- external transport/signature protocol for submitting candidate Inputs.

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
