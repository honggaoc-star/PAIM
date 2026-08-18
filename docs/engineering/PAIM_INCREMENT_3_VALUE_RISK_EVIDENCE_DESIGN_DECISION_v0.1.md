# PAIM Increment 3 Value/Risk and Evidence Design Decision v0.1

## Status

Design-analysis artifact for PAIM Issue #23. This artifact analyzes IRR-006 and IRR-008 and recommends a minimal v0.1 posture for human acceptance. It does not amend a governing specification, authorize implementation, or resolve a deferred P1 finding.

## 1. Purpose and baseline

This artifact reduces the remaining design choices that gate PAIM Platform Architecture v0.1 Increment 3:

- **IRR-006 — selection and freeze of authoritative Value/Risk inputs**; and
- **IRR-008 — Evidence Applicability semantics**.

The baseline is synchronized `main` at merge commit `b1ad5eb2bb3eaacf2b653abb89ca566753258db2`, after accepted Increment 2 Case, Configuration, lifecycle, and Roles semantics. Current PAIM specifications remain authoritative. This analysis does not infer a rule from the merged implementation and does not use APRM.

The principal governing sources are:

- `PAIM_IMPLEMENTATION_SEQUENCE_AND_P1_GATES_v0.1.md`, especially §§3–7 and 10;
- `PAIM_PLATFORM_ARCHITECTURE_v0.1.md`, especially §§3, 5.5–5.7, 6–7, 16, 20, and 23;
- `PAIM_CODEX_IMPLEMENTATION_READINESS_REVIEW_v0.1.md`, IRR-006 and IRR-008;
- `PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md`, especially §§4–6, 12–19, 30–35;
- `PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md`, especially §§3, 6–10, 19–29, and 32–36;
- `PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md`, especially §§3–6, 31, 33, and 35;
- `PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md`, especially §§13–16 and 22–25;
- `PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md`, especially §§2–9, 16–26, 35, and 39;
- `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`, especially §§2, 6–8, 16, and 22;
- `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, especially §§2–3, 8, 10, and 11; and
- accepted Increment 2 scope/role decisions for conformance only.

The objective is the smallest coherent posture that permits a later specification-hardening issue to close both P1 findings, after which an implementation issue may implement Increment 3. Recommendations in this artifact remain proposals until accepted by PAIM design authority and incorporated into the governing contracts.

## 2. Governing constraints already fixed

The following are not open design choices in this issue.

### 2.1 Record and history integrity

- Every continuing management subject has a stable Record ID; every finalized content version has an immutable Record Version ID.
- Freeze is a finalization boundary. Frozen Value and Risk content cannot be edited in place.
- Correction, amendment, supersession, withdrawal, and status changes preserve their predecessors and exact recorded/effective times.
- Historical Integrations and Decisions retain exact versions relied upon even after later correction, withdrawal, staleness, or supersession.
- Current selection is evaluated for explicit family, subject, scope, purpose, effective time, optional knowledge cutoff, and eligibility guards.
- Selection returns exactly one eligible version, explicit absence/not established, or explicit incompatible-current conflict. There is no latest/newest/owner/status/row-order fallback.

### 2.2 Configuration and analytical invariants

- Every Configuration identity has exactly one owning Case.
- A Case has at most one governing Configuration at an effective time; proposed, experimental, alternative, and fallback purpose does not satisfy governing currentness.
- Value and Risk are separate analytical lanes with separately attributable Finding, Boundary, Uncertainty, Implication, and Provenance.
- Every input binds to an exact Configuration identity/version.
- A finalized Integration binds exactly one frozen Value Input version and exactly one frozen Risk Input version for the relevant Configuration version.
- Additional analyses and disagreement must not be erased or used to rewrite either selected input.
- No combined score or confidence oracle replaces Value, Risk, evidence, uncertainty, boundary, rationale, or accountable judgment.

### 2.3 Accountability and authority invariants

- Technical principal, PAIM actor, Role Assignment, accountable assignment/mechanism, software permission, and Decision Authority remain distinct.
- Software permission authorizes an attempt; it cannot establish PAIM accountability or authority.
- Multiple compatible performers may coexist, but a governed obligation requiring accountability resolves to one accountable assignment/mechanism, explicit vacancy, or explicit conflict.
- Broad and narrow Role Assignments have no implicit precedence. Recency, breadth, specificity, directory hierarchy, and permission cannot choose a winner.
- Value Evaluator and Risk Evaluator functions remain distinct even when one person holds both assignments.
- Evidence ownership does not itself confer authority to decide what evidence means; Integration facilitation does not confer analytical acceptance or Decision Authority.

### 2.4 Evidence and lifecycle invariants

- Evidence is distinct from Findings, Authority, Value/Risk Inputs, Integration, and Decision.
- Evidence has durable identity, provenance, scope, limitations, version/history, effective time, and recorded time.
- Evidence may relate many-to-many to Configurations, findings, controls, uncertainty, authority questions, inputs, Integrations, Decisions, learning, and reassessment.
- A configuration change requires applicability review; prior evidence does not automatically transfer.
- Conflicting evidence remains explicit and is not resolved by newer-record selection.
- A Case cannot become ready merely because documents exist. Required inputs, exact Configuration binding, provenance, boundaries, uncertainty, and authority gaps must be represented.
- A stale or withdrawn input before authorization fails the affected readiness guard; after authorization it does not rewrite the historical Decision and may create reassessment attention.

## 3. Original IRR-006 gap

The specifications already require separate, frozen, exact Value and Risk Input versions in an Integration, but do not fully define the path from analysis to authoritative use.

The unresolved questions are:

1. how contributor-produced analyses differ from PAIM-facing Input records and authoritative selected versions;
2. which event declares analytical readiness, accepts the Input, freezes its content, and selects it for one Integration use;
3. which accountable assignment or mechanism may perform each act for each lane;
4. how competing eligible submissions produce one/absence/conflict without a hidden winner;
5. how rejection, withdrawal, dissent, correction, and supersession affect eligibility and history; and
6. whether one frozen Input version may be reused, and what new judgment is required for each later Integration.

Without resolution, an implementation could accidentally freeze any `ready` record, allow an integrator or technical administrator to choose a conclusion, treat the newest submission as authoritative, or silently carry a historically valid but currently unfit Input into a later Integration.

## 4. IRR-006 alternatives

### 4.1 Analytical submission versus authoritative input

#### Alternative A — submission and authoritative Input are the same record state machine

Each Value or Risk Input begins as a draft, may become `ready`, and is then frozen/selected. Competing analyses are separate Input identities or versions with dispositions.

Consequences:

- minimal record-family count and direct fit with the existing Input contract;
- every contributor draft enters the authoritative Input family, which may overstate immature work;
- a rejected or withdrawn analysis still needs a durable disposition and history; and
- parallel contributors can accidentally create ambiguous same-identity version histories unless continuity rules are explicit.

#### Alternative B — separate Analytical Submission and PAIM-facing Input families

Contributor work is recorded as a Value Analysis Submission or Risk Analysis Submission. Acceptance creates or references a distinct frozen PAIM-facing Input version.

Consequences:

- strongest distinction between contributed analysis and accepted conclusion;
- clean preservation of competing, dissenting, rejected, and withdrawn work;
- added identity, promotion, linkage, correction, and UI concepts before v0.1 needs them; and
- risk of duplicating the same five-part content at the promotion boundary.

#### Alternative C — one Input family with explicit candidate/disposition relationships

All PAIM-facing five-part conclusions are Input records, but authoritative use is established only by a separate acceptance/selection record. Candidate Inputs may be ready, non-selected, dissenting, rejected, withdrawn, superseded, or selected for a declared use without changing their historical content.

Consequences:

- preserves the current Input family and avoids a speculative analysis-workpaper model;
- makes “frozen content” distinct from “selected for this Integration”;
- preserves all competing Inputs and their dispositions; and
- requires a first-class acceptance/selection relationship rather than a mutable `selected` flag.

**Codex recommendation:** Alternative C for minimal v0.1. External or internal analytical workpapers remain provenance sources. A PAIM-facing Input is a compact five-part conclusion; an authoritative use exists only through an exact acceptance/selection record.

### 4.2 Selection cardinality

The cardinality itself is fixed: one Integration attempt/path selects exactly one eligible frozen Value Input version and exactly one eligible frozen Risk Input version.

Viable selection models are:

#### Model S1 — mutable selected/current flag on each Input

Reject. A flag cannot adequately identify use, scope, accountable selector, effective time, correction history, or simultaneous selection conflict. It invites last-write-wins behavior.

#### Model S2 — selection embedded in the Integration draft

The Integration draft references one Value and one Risk Input. Finalizing the Integration makes those references authoritative.

This is compact, but it gives the Integration owner de facto acceptance power unless a separate accountable validation exists. It also makes input acceptance unavailable before Integration construction, conflicting with readiness language.

#### Model S3 — first-class lane-specific acceptance/selection record

For each Integration use, one Value Input Acceptance/Selection and one Risk Input Acceptance/Selection identify the exact Input Version, exact Configuration Version, use/Integration identity or reserved Integration path, effective/recorded time, accountable assignment/mechanism, rationale, and predecessor/correction/supersession history.

Current selection for one lane/use returns:

- `FOUND` with one exact eligible acceptance/selection version;
- `NOT ESTABLISHED` when none qualifies; or
- `SELECTION CONFLICT — UNRESOLVED` with every incompatible candidate when more than one qualifies.

**Codex recommendation:** S3. The Integration later binds the exact selected Value and Risk Input versions and the acceptance/selection versions that established their eligibility.

### 4.3 Acceptance and freeze event

#### Model F1 — readiness, acceptance, freeze, and selection are one event

This is simple but collapses analytical readiness, accountable acceptance, content finalization, and use-specific choice. It makes reuse awkward because an already frozen version cannot sensibly be frozen again.

#### Model F2 — readiness, global freeze, and use selection are three independent events

An analytical owner declares ready; another event freezes content globally; a third selects it for an Integration. This is explicit but risks a frozen record with no declared authoritative purpose and adds workflow without a demonstrated need.

#### Model F3 — readiness is separate; first acceptance atomically freezes and selects; reuse creates a new use acceptance without refreezing

An analytical owner may declare a candidate ready. The first valid acceptance/selection semantic commit:

1. finalizes and freezes the exact Input Version if it is not already frozen;
2. records lane-specific acceptance for the exact Configuration/use;
3. records accountable provenance and rationale; and
4. establishes current one/absence/conflict selection for that lane/use.

If the Input Version is already frozen, a later Integration records a new acceptance/reuse selection. The content remains the same immutable version; the new record judges current fitness and applicability for the new use.

**Codex recommendation:** F3. Freeze is global immutability of one Input Version after first authoritative acceptance; selection/acceptance is scoped to each Integration use. One frozen version may support multiple Integrations only through separate explicit use-acceptance records.

### 4.4 Accountability alternatives

#### Alternative O1 — analytical owner self-acceptance by role label

The Value Evaluator accepts Value and the Risk Evaluator accepts Risk solely because they produced the inputs.

This preserves lane independence but conflates performance with accountable acceptance and fails when several performers or broad/narrow assignments coexist.

#### Alternative O2 — Integration owner accepts both lanes

This centralizes workflow but gives the integrator power to choose contributing conclusions, weakens analytical independence, and creates an unintended combined gatekeeper.

#### Alternative O3 — separately accountable acceptance assignment/mechanism per lane

Each lane/use resolves exactly one accountable acceptance assignment or governed mechanism applicable to the exact Configuration/use. The assigned actor may also be the analytical producer, but self-acceptance is valid only because the separate accountable relationship is established—not because the person authored the input.

#### Alternative O4 — hybrid readiness plus separately accountable acceptance

The producing analytical function declares readiness; a lane-specific accountable assignment/mechanism accepts/freezes/selects. An organization may assign both functions to one actor, but PAIM preserves both functions and conflict/vacancy behavior. The integrator coordinates and validates exact references but does not acquire acceptance authority by participation.

**Codex recommendation:** O4. It aligns with Increment 2 role semantics, supports small organizations, and preserves the distinction between performer, accountability, and Decision Authority. Software permission or technical principal identity never establishes acceptance authority.

### 4.5 Reuse, dissent, rejection, and historical validity

#### Reuse alternatives

- **Silent reuse:** any frozen/current Input may be reused. Reject because historical validity is not current fitness.
- **Reuse unless refresh-required:** reuse is automatic unless a negative status exists. Reject because absence of a flag is not an applicability judgment.
- **Explicit use acceptance:** every later Integration records a new acceptance/reuse judgment against the exact Configuration Version, purpose, current evidence/applicability basis, and time. Recommended.

#### Non-selected and dissenting analyses

Additional Inputs remain independently attributable and retrievable. A use-specific disposition may mark them `non-selected`, `dissenting`, `rejected for this use`, or `withdrawn by source`, with rationale and actor/mechanism. `Dissenting` is not synonymous with invalid; it preserves a materially competing analytical conclusion. A rejected Input is not eligible for that use but is not deleted or rewritten.

#### Correction, supersession, and withdrawal

- Correction creates a successor/corrected Input Version and identifies affected selections/Integrations. It never mutates a frozen version.
- Supersession changes prospective current eligibility for a declared scope/time but preserves prior uses.
- Withdrawal before Integration completion makes the affected selection ineligible and fails readiness.
- Withdrawal after authorization preserves the historical Decision basis and creates an integrity/reassessment condition where material.
- Stale-but-historically-valid means the version remains the true frozen basis for its historical use but needs a new current-use fitness judgment and possibly refreshed analysis before reuse.

## 5. IRR-006 decision matrix

| Design area | Minimal candidate | Stronger alternative | Conformance consequence | Implementation consequence | Recommendation |
|---|---|---|---|---|---|
| Candidate representation | One Input family plus dispositions | Separate Submission and Input families | Both can preserve independence/history | Stronger model adds promotion and duplicate identity | One Input family plus first-class disposition/selection |
| Selection | Embedded Integration references | Lane-specific acceptance/selection record | Both can bind exact versions; embedded selection risks implied integrator authority | Separate record adds one authoritative relationship family | Lane-specific record |
| First freeze | Freeze before acceptance | Atomic with first acceptance | Both can preserve immutability | Pre-freeze creates purposeless frozen states | Atomic first acceptance/freeze |
| Reuse | Global frozen/current status | New use-specific acceptance | Silent global reuse violates exact fitness judgment | New acceptance adds explicit linkage and time | New acceptance for every use |
| Acceptance owner | Producer or integrator by role label | Separate accountable lane mechanism | Role label alone conflicts with accepted accountability rules | Requires exact applicable assignment/mechanism validation | Hybrid readiness plus separate lane acceptance |
| Competing inputs | Mutable selected flag | One/absence/conflict selection | Only explicit selection conforms to no-silent-winner | Requires conflict query and resolution history | Explicit one/absence/conflict |
| Dissent/rejection | Status only | Use-specific disposition relationship | Both preserve record if immutable | Relationship distinguishes different uses | Use-specific disposition |

## 6. Original IRR-008 gap

The current specifications recognize Evidence scope, applicability, correction, supersession, conflict, staleness, and many possible targets. They do not yet define Evidence Applicability as an independently versioned accountable judgment.

The missing semantics are:

1. stable identity and immutable versions for one applicability subject;
2. exact Evidence Version and target identity/version binding;
3. minimum target types and many-to-many cardinality;
4. outcome vocabulary and assessed scope;
5. assessor/accountable provenance, rationale, and dual time;
6. correction, supersession, withdrawal, staleness, and reuse relationships; and
7. one/absence/conflict current selection when judgments coexist.

Without these rules, an implementation could overwrite applicability as Evidence metadata, infer applicability from folder attachment, silently generalize evidence to another Configuration, or choose the newest judgment when assessors disagree.

## 7. IRR-008 alternatives

### 7.1 Evidence Applicability as a first-class relationship

#### Alternative E1 — applicability fields on Evidence Version

An Evidence Version contains target IDs and status fields. This is simple but makes target-specific judgment changes look like Evidence-content changes, does not scale cleanly to many targets, and makes independent correction/provenance difficult.

#### Alternative E2 — target-owned evidence link

Each target record stores Evidence references and applicability. This makes Evidence reuse dependent on every target family and fragments history/currentness semantics.

#### Alternative E3 — versioned Evidence Applicability record/relationship

Evidence Applicability is an authoritative relationship family with its own identity, immutable versions, current selection, accountability, and history. It links one exact Evidence Version to one exact target subject and assessed scope. The same Evidence Version may have many applicability identities for different targets; one target may have many Evidence Applicability identities for different Evidence Versions.

**Codex recommendation:** E3.

### 7.2 Minimum candidate contract

Each Evidence Applicability record should support:

#### Identity and exact endpoints

- Evidence Applicability Record ID;
- Evidence Applicability Version ID;
- exact Evidence ID and Evidence Version ID;
- target type;
- target stable identity;
- exact target Version ID where the target is versioned and the judgment depends on content;
- Case ID and owning Configuration context where applicable, as context rather than a substitute target; and
- declared purpose/use if the same endpoints may be assessed for distinct analytical purposes.

#### Judgment

- applicability outcome;
- assessed scope, including relevant Configuration elements/conditions and exclusions;
- conditions/limitations;
- rationale;
- assessor PAIM actor; and
- exact accountable Role Assignment version or governed accountable mechanism.

#### Time, state, and history

- effective interval;
- recorded time;
- finalization/status;
- predecessor version;
- correction, supersession, or withdrawal relationship and reason;
- affected Inputs, Integrations, Decisions, or reassessment attention where material; and
- exact source/provenance for externally supplied judgments.

#### Current selection

For the explicit Evidence Version + target identity/version + purpose + assessed scope + effective time + optional knowledge cutoff, return:

- one eligible current applicability version;
- `APPLICABILITY NOT ESTABLISHED`; or
- `EVIDENCE APPLICABILITY CONFLICT — UNRESOLVED` with all incompatible candidates and provenance.

No mutable `current` flag, recency, target specificity, or software permission chooses a winner.

### 7.3 Target-type alternatives and cardinality

#### Target set T1 — Configuration Version only

This is too narrow. It can state that Evidence fits a Configuration but cannot preserve a distinct judgment about its use in a Value or Risk Input or authority question.

#### Target set T2 — every currently named and future PAIM object in Increment 3

This is expressive but prematurely designs findings, controls, uncertainty, Boundary clauses, Decisions, Interventions, Reassessments, and Observation persistence.

#### Target set T3 — bounded Increment 3 targets plus typed extension

Required first-class targets for Increment 3:

1. Managed Configuration Version;
2. Value Input Version;
3. Risk Input Version;
4. Authority Record Version; and
5. Authority Gap Version/question where Evidence bears on resolving the gap.

Reserved typed targets, activated in their owning increments:

- Integration Version and Decision Version in Increment 4;
- Finding, Uncertainty, Control, and Boundary Clause only if their owning specifications establish stable target identities;
- Intervention/Learning and Reassessment targets in later increments; and
- Observation only after IRR-009.

An Integration or Decision can still preserve exact Evidence Applicability versions relied upon through historical reference when Increment 4 is hardened, without making those not-yet-implemented targets part of Increment 3.

**Codex recommendation:** T3. Cardinality is explicitly many-to-many. No Evidence record “belongs” to only one target, and no target may infer applicability from attachment alone.

### 7.4 Applicability outcomes

#### Vocabulary V1 — binary applicable/not applicable

Too coarse for conditional, partial, and uncertain use already recognized by governing specifications.

#### Vocabulary V2 — compact five-outcome judgment

- `APPLICABLE`;
- `CONDITIONALLY_APPLICABLE`;
- `PARTIALLY_APPLICABLE`;
- `NOT_APPLICABLE`; and
- `INDETERMINATE`.

`REFRESH REQUIRED` is a prospective status/current-use condition, not a substantive applicability outcome. Staleness is a reason or condition that may lead to a new judgment or refresh requirement. `CONFLICT` is a deterministic selection result from incompatible co-current judgments, not a stored assessor conclusion.

#### Vocabulary V3 — configurable organization-specific outcome taxonomy

This is flexible but would make cross-module readiness behavior indeterminate without a normative mapping.

**Codex recommendation:** V2. Each non-binary outcome requires assessed scope, conditions, and rationale. PAIM does not assign a numerical confidence score.

### 7.5 Conflict and accountable resolution

Multiple applicability judgments may coexist when they have distinguishable targets, purposes, scopes, or effective intervals. They conflict only when they compete for the same explicit selection context and their outcomes cannot simultaneously govern.

Conflict alternatives:

- newest judgment wins — non-conformant;
- most specific target/scope wins — non-conformant under the no-implicit-precedence rule;
- all judgments remain a set and consumers decide — unsafe because each consumer may invent a winner; or
- selection returns conflict until an accountable successor/supersession resolution is recorded — recommended.

An accountable resolver may create a successor applicability judgment or explicit supersession relationship that states the governing outcome, scope, rationale, and displaced versions. The prior judgments and disagreement remain reconstructable. The resolver's assignment/mechanism must apply to the exact target obligation; broad/narrow conflicts remain conflict unless explicitly resolved.

### 7.6 Accountability alternatives

- **Evidence Owner always decides:** simple but violates the separation of evidence production and interpretation.
- **Target analytical owner always decides:** fits Value/Risk use but not Configuration or Authority targets.
- **Universal Evidence Applicability role:** consistent but adds a mandatory organization-wide role not currently required.
- **Target-context accountable assignment/mechanism:** one accountable assignment/mechanism is resolved for the exact target, scope, purpose, and time; Evidence Owner, Value Evaluator, Risk Evaluator, Authority Owner, or another governed mechanism may be eligible according to accepted organizational assignment. Recommended.

The assessor actor and accountable assignment/mechanism are both recorded. They may refer to the same person, but participation or edit access is not accountability.

### 7.7 Correction, staleness, supersession, and reuse

- **Evidence-content correction** creates a corrected Evidence Version and does not mutate the prior Evidence or its prior applicability judgments.
- **Applicability-judgment correction** creates a corrected Evidence Applicability Version against the same exact endpoints and identifies the error and affected uses.
- **Evidence supersession** changes prospective Evidence currentness but does not rewrite applicability or historical decisions that referenced the prior version.
- **Staleness** is contextual. Evidence may carry a broad attention/status event, but fitness for a particular target/version is expressed through Evidence Applicability and current-use assessment. There is no universal expiry period.
- **Reuse across Configurations or Input versions** requires a new Evidence Applicability judgment for the new exact target/version. Prior applicability may be provenance but is not silently transferred.
- **Refresh required** means prospective use needs review or replacement; it does not make historical evidence disappear.

## 8. IRR-008 decision matrix

| Design area | Alternative | Semantic consequence | Implementation consequence | Invariant fit | Recommendation |
|---|---|---|---|---|---|
| Location | Evidence metadata | Overwrites target-specific judgment | Simple row/field, poor many-to-many history | Weak | Reject |
| Location | Target-owned links | Fragments semantics by target family | Repeated implementations | Partial | Reject |
| Location | Versioned relationship | Independent identity/history/currentness | One shared relationship family | Strong | Select |
| Targets | Configuration only | Cannot express Input/Authority use | Small | Too narrow | Reject |
| Targets | All future objects now | Prematurely resolves later identity questions | Large speculative model | Risky | Reject |
| Targets | Increment 3 core plus typed extension | Bounded now, explicit later activation | Moderate and extensible | Strong | Select |
| Outcomes | Binary | Loses conditional/partial/unknown | Simple | Weak | Reject |
| Outcomes | Five outcomes; conflict derived | Preserves current concepts without score | Finite enum plus conditions/scope | Strong | Select |
| Conflict | Newest/specific wins | Hides disagreement | Easy | Non-conformant | Reject |
| Conflict | Explicit conflict then accountable successor | Preserves all judgments and rationale | Requires conflict selection/resolution | Strong | Select |
| Reuse | Carry forward | Treats historical applicability as universal | Easy | Non-conformant | Reject |
| Reuse | New target/version judgment | Exact fitness for every use | More explicit records | Strong | Select |

## 9. Coupled Value/Risk–Evidence analysis

### 9.1 Does selecting or reusing an Input require applicable Evidence?

A frozen Input must retain exact material Evidence and Evidence Applicability versions in its provenance. For a new acceptance/use, PAIM should evaluate current fitness of the material evidence basis for the exact Input Version and governing Configuration Version.

The minimum gate is not “every linked Evidence item must say `APPLICABLE`.” Evidence may be contextual, limiting, conflicting, or the basis for explicit uncertainty. Instead:

- each Evidence item declared material to the Input/use must have a current applicability result for its exact target context;
- `APPLICABILITY NOT ESTABLISHED`, unresolved applicability conflict, `NOT_APPLICABLE`, or unresolved `REFRESH REQUIRED` blocks acceptance when that Evidence is required to support the Input's Finding, Boundary, or Implication;
- `CONDITIONALLY_APPLICABLE` or `PARTIALLY_APPLICABLE` is eligible only within its recorded scope/conditions and must not support a broader Input Boundary;
- `INDETERMINATE` may be preserved as explicit uncertainty if an accountable lane acceptance determines that the bounded Input remains supportable; it blocks when the unresolved question is decision-limiting to that Input/use; and
- Evidence included only as limitation, dissent, or conflict need not become favorable support, but its role and provenance remain visible.

This is an accountable fitness gate, not an automated evidence-sufficiency score.

### 9.2 Independence of Applicability and Input acceptance

An Evidence Applicability judgment can be finalized before, during, or after analytical Input construction. It is independent of acceptance because applicability may be reused across analyses and can change without changing the Evidence content.

Input acceptance references the exact applicability versions relied upon and determines whether their combination is sufficient for that bounded lane/use. It does not rewrite those judgments.

### 9.3 Later Evidence change and historical freeze

An accepted frozen Value or Risk Input remains immutable and historically authoritative for the Integration/Decision that used it even when later Evidence becomes stale, corrected, superseded, conflicting, or inapplicable.

Later Evidence change may:

- end prospective eligibility of an acceptance/selection;
- mark the Input `refresh required`;
- require a corrected/successor Input;
- block a new Integration use; or
- create an integrity/reassessment condition for a current authorized Decision where material.

It never edits the historical Input, Integration, Decision, or applicability versions.

### 9.4 What blocks a new Integration

A new Integration is blocked when either analytical lane has:

- no eligible use-specific acceptance/selection;
- selection conflict;
- a selected Input bound to the wrong Configuration Version;
- withdrawn, rejected-for-use, or superseded-without-justified-reuse Input status;
- required material Evidence with applicability absent, conflicting, not applicable, or unresolved refresh requirement;
- a conditional/partial evidence scope narrower than the claimed Input Boundary; or
- missing accountable provenance for acceptance or applicability.

The following may remain documented gaps/uncertainties rather than automatic blockers when an accountable bounded-use judgment says the Input remains supportable:

- non-material Evidence with indeterminate applicability;
- Evidence intentionally linked as limitation or dissent;
- an Authority Gap that does not govern the bounded analytical acceptance; and
- stale Evidence that is not material to the bounded conclusion and whose treatment is explicit.

Whether an uncertainty limits a later management Decision remains an Increment 4 integration judgment. Issue #23 does not resolve uncertainty classification generally.

### 9.5 May the same mechanism accept an Input and assess applicability?

PAIM should permit but not require separation. The same actor may perform both functions only when exact applicable assignments/mechanisms establish both obligations. The record must show the role combination. Neither Evidence ownership, analytical authorship, Case ownership, Integration facilitation, nor software permission automatically establishes both.

Organizations may impose stronger segregation later. PAIM v0.1 should not mandate universal separation that small organizations cannot satisfy.

### 9.6 Case/Configuration scope and no implicit precedence

Every Input acceptance and Evidence Applicability judgment binds exact Configuration identity/version and use/target scope. A Case-scoped accountable assignment may apply to a Configuration obligation only through the accepted target-context rules. A Configuration-scoped and Case-scoped accountable assignment that both compete produce conflict; specificity does not win.

Cross-Case reuse requires a new target-specific judgment and does not imply shared Configuration ownership. Independent concurrent governing Configurations remain in linked Cases.

### 9.7 Deferred coupled questions

This issue does not decide:

- Observation identity/persistence or signal conversion (IRR-009);
- Intervention prerequisites or completion acceptance (IRR-010);
- Trigger/Reassessment cardinality, merge, or concurrency (IRR-011);
- Register population, aggregation, or shared dependency identity (IRR-012);
- stronger/broader operating-state relations (IRR-014);
- general uncertainty classification, Integrated Operating Boundary, Management Decision, or Decision Authorization Basis beyond the exact references Increment 3 must later expose;
- a universal evidence-sufficiency score, confidence score, or automated human-judgment replacement; or
- granular Finding/Control/Boundary target identity where the owning later contract has not established it.

## 10. Compatibility combinations

| IRR-006 posture | IRR-008 posture | Compatibility | Reason |
|---|---|---|---|
| Mutable selected flag | Evidence metadata fields | Incompatible with PAIM invariants | Both hide scope/time/provenance and invite latest-write behavior |
| Embedded Integration selection | Versioned Applicability | Conditional | Evidence history is sound, but selection still needs separate accountable acceptance before readiness |
| Use-specific lane acceptance | Evidence metadata fields | Incomplete | Input selection is explicit but evidence fitness can still be overwritten or generalized |
| Use-specific lane acceptance | Versioned Applicability for all future targets | Semantically possible, not bounded | Prematurely resolves later record identity and workflow questions |
| Use-specific lane acceptance | Versioned Applicability with Increment 3 targets and extensions | **Compatible and minimal** | Shares exact Configuration/version, target, purpose, dual-time, accountability, history, and conflict semantics |
| Silent Input reuse | New target-specific Applicability | Inconsistent | Evidence is reassessed but the analytical conclusion is silently accepted |
| New use acceptance | Silent applicability carry-forward | Inconsistent | Input use is explicit but its evidence basis is not |
| New use acceptance | New applicability/fitness judgment where target/version changes | **Compatible** | Both analytical conclusion and evidence basis are explicitly judged for the bounded use |

The coherent combination is therefore:

```text
Candidate Value Inputs                 Candidate Risk Inputs
          |                                      |
          v                                      v
one/absence/conflict Value acceptance   one/absence/conflict Risk acceptance
          |                                      |
          +------------------+-------------------+
                             |
              exact material Evidence Applicability versions
                             |
                             v
             eligible bounded Integration handoff
```

No arrow implies substantive approval by software. Each accountable judgment remains attributable and reconstructable.

## 11. Proposed minimal v0.1 posture

The following is the recommended combined posture, subject to human acceptance:

1. Keep one Value Input family and one Risk Input family; treat workpapers/submissions as provenance unless they produce a PAIM-facing five-part candidate Input.
2. Preserve candidate Inputs independently with explicit use dispositions; no candidate is deleted or rewritten because another is selected.
3. Introduce a first-class lane-specific Input Acceptance/Selection record for each Integration use.
4. Require exactly one selected frozen Value Input version and one selected frozen Risk Input version per Integration use, with explicit absence/conflict otherwise.
5. Separate analytical readiness from accountable acceptance. The first acceptance atomically freezes the Input Version and selects it for the bounded use.
6. Permit one frozen Input Version to support multiple Integrations only through a new explicit acceptance/reuse record for each use.
7. Resolve acceptance through one exact accountable assignment/mechanism per lane/use; permit the producer to hold that accountability but never infer it from authorship, access, or role label alone.
8. Make Evidence Applicability a first-class authoritative relationship with stable identity, immutable versions, exact Evidence/target versions, assessed scope, outcome, rationale, assessor, accountable provenance, dual time, and history.
9. Support Increment 3 targets for Configuration Version, Value Input Version, Risk Input Version, Authority Record Version, and Authority Gap Version/question; reserve typed later targets.
10. Use `APPLICABLE`, `CONDITIONALLY_APPLICABLE`, `PARTIALLY_APPLICABLE`, `NOT_APPLICABLE`, and `INDETERMINATE`; treat `REFRESH REQUIRED` as prospective status/attention and conflict as a derived selection result.
11. Select Evidence Applicability as one/absence/conflict for explicit endpoints, purpose, scope, effective time, and optional knowledge cutoff. Preserve all conflicting judgments until accountable supersession/resolution.
12. Require a new Applicability judgment for a new target/version and a new Input acceptance for a new Integration use; never silently carry forward either.
13. Preserve frozen historical Inputs and historical Applicability versions after later Evidence change; route material prospective impact to refresh, successor Input, blocked new use, or later reassessment.
14. Permit but do not require separation between Input accepter and Applicability assessor; exact accountable assignments/mechanisms must establish each obligation and visible role overlap.

This posture unlocks the semantic foundation of Increment 3 and supplies exact references needed by Increment 4 without designing Increment 4 itself.

## 12. Genuine human decision points

The decisions below require PAIM design authority. Fixed integrity behavior and ordinary storage/UI choices are intentionally excluded.

### Decision 1 — How are candidate analyses distinguished from authoritative Inputs?

- **Viable alternatives:** one Input state machine; separate Submission and Input families; one Input family plus first-class use dispositions/selection.
- **Semantic consequences:** separate families provide the strongest promotion boundary; one family plus dispositions preserves candidates without treating selection as content state.
- **Implementation consequences:** separate families require more identities, promotion links, correction paths, and workflows.
- **Invariant compatibility:** all are compatible only if selected authority is explicit and history is immutable.
- **Codex recommendation:** one Value Input family and one Risk Input family plus use-specific dispositions and acceptance/selection records.
- **Deferred:** a later external-analysis adapter may define signed Submission records without changing the core acceptance contract.

### Decision 2 — What event freezes and selects an Input?

- **Viable alternatives:** one combined readiness/freeze event; independent readiness/freeze/selection events; readiness followed by atomic first acceptance/freeze/selection and later reuse acceptance.
- **Semantic consequences:** the recommended alternative cleanly separates producer readiness from accountable authority while avoiding purposeless frozen records.
- **Implementation consequences:** requires a semantic commit that finalizes content and creates its first selection atomically.
- **Invariant compatibility:** must preserve immutable freeze and explicit exact-version selection.
- **Codex recommendation:** separate readiness; atomic first acceptance/freeze/selection; use-specific acceptance thereafter.
- **Deferred:** signature/approval technology and external signed-input protocol.

### Decision 3 — Who may accept each analytical lane?

- **Viable alternatives:** analytical owner by role; integrator for both; separate accountable acceptance mechanism; hybrid readiness plus lane-specific accountability.
- **Semantic consequences:** producer-only and integrator-only models conflate functions; separate accountability permits visible same-person combination without automatic authority.
- **Implementation consequences:** exact applicable assignment/mechanism resolution and conflict/vacancy validation.
- **Invariant compatibility:** only models that distinguish permission, performer, accountability, and Decision Authority conform fully.
- **Codex recommendation:** hybrid model with producer readiness and one lane-specific accountable acceptance assignment/mechanism.
- **Deferred:** organization-specific default assignments and stronger segregation-of-duties policy.

### Decision 4 — May a frozen Input be reused?

- **Viable alternatives:** never; silently while current; reuse through a new use-specific acceptance/fitness judgment.
- **Semantic consequences:** never-reuse duplicates unchanged content; silent reuse mistakes historical validity for current fitness; explicit reuse preserves both.
- **Implementation consequences:** new acceptance record per use, with exact Configuration, evidence basis, rationale, and time.
- **Invariant compatibility:** explicit reuse best preserves exact version binding and frozen history.
- **Codex recommendation:** allow reuse only through a new use-specific acceptance record.
- **Deferred:** automated suggestion of reusable candidates; software may suggest but never select.

### Decision 5 — Which Evidence Applicability targets are first-class in Increment 3?

- **Viable alternatives:** Configuration Version only; every named PAIM object; bounded Increment 3 targets plus typed extension.
- **Semantic consequences:** Configuration-only cannot express analytical/authority use; all-targets resolves later identities prematurely.
- **Implementation consequences:** bounded targets keep validation finite while requiring an extensible target discriminator/contract.
- **Invariant compatibility:** all endpoints must retain exact identity/version and many-to-many behavior.
- **Codex recommendation:** Configuration, Value Input, Risk Input, Authority Record, and Authority Gap versions/questions now; activate later targets in owning increments.
- **Deferred:** Integration/Decision, granular Finding/Uncertainty/Control/Boundary, Intervention/Learning, Reassessment, and Observation targets.

### Decision 6 — What is the minimum applicability outcome vocabulary?

- **Viable alternatives:** binary; five-outcome vocabulary; configurable taxonomy with normative mapping.
- **Semantic consequences:** binary loses conditional/partial use; configurable vocabulary weakens consistent guards without mapping.
- **Implementation consequences:** five outcomes require structured scope/conditions and finite eligibility rules.
- **Invariant compatibility:** conflict must remain derived, and no outcome may become a confidence score.
- **Codex recommendation:** applicable, conditionally applicable, partially applicable, not applicable, and indeterminate; refresh-required as status; conflict as selection outcome.
- **Deferred:** organization-specific finer labels mapped to the normative set.

### Decision 7 — Who assesses Evidence Applicability and resolves conflict?

- **Viable alternatives:** Evidence Owner; target analytical owner; universal applicability role; exact target-context accountable assignment/mechanism.
- **Semantic consequences:** fixed owner choices do not fit all targets; target-context accountability preserves role separation and small-organization flexibility.
- **Implementation consequences:** same one/vacancy/conflict and no-implicit-precedence resolution used by accepted Increment 2 semantics.
- **Invariant compatibility:** assessor and accountable provenance remain distinct from access and authorship.
- **Codex recommendation:** one target-context accountable assignment/mechanism; permit Evidence/Value/Risk/Authority roles according to explicit assignment.
- **Deferred:** organization-specific default policies or committees.

### Decision 8 — How does Evidence fitness gate Input acceptance?

- **Viable alternatives:** require every linked Evidence item to be applicable; require only existence of provenance; assess material Evidence fitness for the bounded use and preserve limitations/uncertainty.
- **Semantic consequences:** all-applicable is too rigid and hides limiting/conflicting evidence; provenance-only is too weak; material fitness is bounded and inspectable.
- **Implementation consequences:** acceptance references exact material applicability versions and records treatment of conditional/partial/indeterminate evidence.
- **Invariant compatibility:** preserves human judgment, exact Configuration binding, explicit gaps/conflict, and no sufficiency score.
- **Codex recommendation:** material Evidence fitness gate with explicit blocker rules and bounded accountable treatment of indeterminate evidence.
- **Deferred:** general Accepted versus Decision-Limiting Uncertainty classification to Increment 4.

## 13. Deferred P1 dependencies

The recommended posture intentionally leaves the following unchanged:

| Finding | Deferred question | Boundary preserved here |
|---|---|---|
| IRR-009 | Is Observation an authoritative record, and how does it become Evidence/Trigger? | No Observation target or persistence contract is created. |
| IRR-010 | Which Interventions are prerequisites and who accepts completion? | Evidence Applicability does not imply Intervention completion. |
| IRR-011 | Trigger/Reassessment cardinality and concurrency | Later evidence impact may raise attention; no merge/closure rules are chosen. |
| IRR-012 | Register unit, aggregation, and shared dependency identity | Cross-Case reuse uses explicit records; no equivalence or portfolio winner is inferred. |
| IRR-014 | Stronger/broader operating-state relation | No Evidence or Input status implies operating-state ranking. |

Also deferred are signature technology, general RBAC, external adapter finalization, universal evidence scoring, formal authority hierarchy, granular later-target identities, and general Integration/Decision semantics beyond exact handoff references.

## 14. Specification sections that would require hardening after decisions

No specification is modified in Issue #23. If the proposed posture is accepted, a separate bounded hardening issue should amend at least:

| Governing artifact | Sections | Required hardening |
|---|---|---|
| Value/Risk Interface | §§4–6, 12–19, 30–35 | Candidate/disposition semantics; lane-specific acceptance/selection identity; first freeze semantic commit; reuse, rejection, withdrawal, correction; exact accountability and one/absence/conflict. |
| Evidence and Authority | §§3, 6–10, 19–29, 32–36 | Evidence Applicability record contract, targets, outcomes, many-to-many cardinality, dual time, accountability, correction/supersession, staleness, reuse, conflict. |
| Integration and Decision | §§3–6, 31, 33, 35 | Exact acceptance/selection references, final readiness guards, Evidence Applicability basis, non-selected/dissenting Input treatment. |
| Managed Configuration | §§13–16, 24–25 | Exact target-version applicability and configuration-change review behavior. |
| Roles and Accountability | §§6–8, 16–26, 35, 39 | Lane acceptance and target-context applicability obligations; actor/accountability separation; vacancy/conflict and no implicit precedence examples. |
| Case Lifecycle | §§2.5, 6–8, 16.2, 21–22 | READY_FOR_INTEGRATION guards for exact selected frozen Inputs and required Evidence Applicability outcomes. |
| Record and Decision Integrity | §§3.4, 3.11–3.13, 8, 10–11 | Add cross-cutting conformance invariants and remove IRR-006/008 reservations only after substantive owners are hardened. |
| Platform Architecture | §§5.5–5.7, 7, 16, 20, 23 | Update P1 dependency state and reference accepted record/selection contracts without duplicating domain semantics. |

Hardening must use one shared vocabulary for exact Configuration Version, target/use purpose, accountable assignment/mechanism, effective/recorded time, predecessor/correction/supersession, and one/absence/conflict.

## 15. Increment 3 gate implications

Issue #23 alone does not open the implementation gate. If PAIM design authority accepts the decisions, the next gate steps are:

1. harden the governing specifications in a separate bounded issue;
2. perform a focused conformance review across the amended contracts;
3. confirm explicit behavioral oracles for competing Inputs, first freeze, reuse, withdrawal, dissent, unrelated Configuration use, applicability absence/conflict, conditional/partial scope, correction, and historical reconstruction;
4. confirm no IRR-009/010/011/012/014 semantics were imported;
5. merge at a clean-main checkpoint; and only then
6. authorize a separate Increment 3 implementation issue.

Acceptance evidence for gate closure should include:

- exact lane-specific acceptance/selection and freeze event contracts;
- exact accountable actor/mechanism rules and vacancy/conflict behavior;
- one/absence/conflict selection for each lane/use;
- immutable reuse/rejection/withdrawal/dissent examples;
- full Evidence Applicability identity, endpoint, outcome, scope, provenance, time, and history contract;
- many-to-many target examples and new-target reuse behavior;
- conflict-preserving resolution examples;
- coupled readiness behavior for material Evidence fitness; and
- confirmation that Value/Risk independence and historical Decision reconstruction remain intact.

## 16. Final recommendation

PAIM should adopt a paired explicit-judgment model for Increment 3:

1. **Input authority is use-specific.** Candidate Value and Risk Inputs remain independent records. For each Integration use, one lane-specific accountable acceptance/selection record identifies exactly one frozen Input Version or returns explicit absence/conflict.
2. **Freeze and reuse are distinct.** First acceptance freezes content atomically; later reuse never refreezes or rewrites it and always requires a new bounded acceptance/fitness judgment.
3. **Evidence Applicability is authoritative in its own right.** It is a versioned many-to-many relationship with exact Evidence/target versions, assessed scope, outcome, rationale, assessor, accountable provenance, dual time, history, and one/absence/conflict selection.
4. **Material Evidence fitness gates new use without rewriting history.** Historical Inputs and Decisions remain frozen; later evidence change affects prospective selection, refresh, successor analysis, or reassessment attention.
5. **Human accountability remains explicit.** Software validates identity, scope, time, eligibility, overlap, and conflict. It does not choose the substantive conclusion, infer authority from permission, collapse Value and Risk, or compute a universal sufficiency score.

This is the smallest v0.1 posture that closes the semantic gaps in IRR-006 and IRR-008 while preserving PAIM's accepted integrity, scope, role, authority, and analytical-independence invariants. It remains **PROPOSED — HUMAN DECISION REQUIRED** until accepted and incorporated into governing specifications.
