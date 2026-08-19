# PAIM v0.1 Release-Scope Decision — IRR-009 and IRR-014

**Status:** Proposed human design-authority decision

**Decision scope:** PAIM v0.1 product/release scope only

**Governing checkpoint:** `main` at
`ede0950269c26200f2284b9b92a8defddc5346e5` (merged PR #64)

**Decision effect:** This record recommends a bounded release claim. It does not design or
substantively close IRR-009 or IRR-014, amend a governing specification or roadmap, authorize
Increment 9, or implement either deferred capability.

## 1. Purpose and checkpoint

This record answers the release question left open by the post-Increment-7 readiness assessment:

> Can PAIM v0.1 be truthfully described as a complete functional application while explicitly
> excluding first-class Observation automation and operating-state ranking?

**Recommended answer: yes, for a precisely bounded local governed-application claim.** The answer
is not yes for a continuous monitoring platform, an automated telemetry interpretation service, or
an operating-state ranking/escalation engine.

The assessment basis is:

- the accepted system and Platform Architecture contracts;
- the current Evidence/Authority, Intervention/Learning, Reassessment, Management Register, Case
  Lifecycle, Roles/Accountability, and System Record/Decision Integrity specifications;
- the implementation-readiness review and P1 sequencing record;
- merged Increment 6–8 implementation and test evidence; and
- the current local-application operator guide.

At the checkpoint, Increment 8 reports 241 passing tests and supplies the authenticated,
restartable local operational boundary that the earlier 75% readiness estimate lacked. The
following decision therefore evaluates the implemented application, not the pre-Increment-8 gap.

## 2. Current functional baseline

### 2.1 Implemented management capability

The current application implements the complete bounded management loop for its declared scope:

| Capability | Current functional behavior |
|---|---|
| Case, Configuration, lifecycle, and Roles | Stable/versioned Cases and Configurations, governing-Configuration selection, lifecycle guards and transition history, typed Role Assignments, accountability vacancy/conflict, and software-permission/substantive-authority separation. |
| Evidence and Authority | Versioned Evidence, Authority, Authority Gaps, exact provenance, first-class target-specific Evidence Applicability, conflict/currentness, and exact historical reconstruction. |
| Value and Risk | Separate Value and Risk lanes, independent provenance and refresh, exact Configuration binding, material-evidence fitness, accountable acceptance/selection, freeze, reuse, and preserved disagreement. |
| Integration, Boundary, Decision, and Authorization | Exact frozen-input Integration, alternatives and uncertainty, immutable hybrid Boundary Snapshots/Clauses, determinations, Decision versions, exact Authorization Basis, bounded-proceed controls, and authorized-decision history. |
| Intervention, Completion, Activation, and Learning | Exact obligation sets and prerequisite types, Completion Results distinct from accountable Acceptance, aggregate activation guards, governed Activation Authorization, replacement/reuse, and decision-specific Learning. |
| Trigger, Reassessment, and interim operation | Explicit existing-record or human/external Trigger provenance, materiality Determination, immutable Trigger Sets, bounded concurrency/coverage, restrictive Interim Operating Dispositions, exact intersection or suspension, Confirmation or authorized successor, and longitudinal history. |
| Shared Dependency and Management Register | Deterministic exact-source concern population, immutable Candidate Sets, accountable equivalence/concentration determinations, descriptive non-transferring aggregation, watermarks/staleness, historical manifests, reports, exports, notification intents, and contextual owning-domain actions. |
| Local operational application | Authenticated principal-to-actor resolution, prospectively current sessions, stored software-access policy, Case/Configuration segmentation, non-leaking Register queries/exports, security audit, typed gateway/CLI, durable SQLite state, and restart. |
| Manual integration boundary | Common provenance-preserving intake with separate Value/Risk lanes and Evidence, Authority, and explicit external Trigger-event types; exact replay/source succession; quarantine; and no direct authoritative finalization. |
| Operational readiness | Deterministic local delivery spool, exact-manifest JSON/CSV export, SQLite-safe backup, separately located verified restore, deterministic Register rebuild, health/readiness, structured counters/events, and fail-closed degraded behavior. |

### 2.2 What a practitioner can do today

Through the authenticated local gateway, a suitably authorized practitioner can:

- create and govern Cases, Configurations, actors, roles, and lifecycle transitions;
- establish and assess Evidence/Authority and preserve unresolved gaps;
- maintain independent Value and Risk inputs through selection and freeze;
- integrate alternatives and authorize an exact Decision and Boundary under a valid authority
  chain;
- govern Intervention obligations, completion acceptance, activation, and Learning;
- record an explicit existing-record or human/external event as a Trigger, conduct Reassessment,
  impose exact restrictive interim effects, and complete through Confirmation or successor
  Decision;
- derive access-filtered Register views, retain exact manifests, export them, deliver local
  notifications, and launch only the owning authoritative action;
- import bounded manual/external candidate material with provenance and quarantine; and
- operate, inspect, back up, verify, restore, and diagnose the local application without treating
  operational telemetry as substantive PAIM truth.

Some domain commands use the typed Python gateway rather than a bespoke CLI subcommand. That is a
local practitioner-entrypoint limitation to be exercised in Increment 9, not a missing domain
semantic.

### 2.3 What a practitioner cannot do today

The current v0.1 boundary does not:

- persist a first-class Observation family or continuously monitor an operating system;
- automatically convert a log, metric, alert, incident, or other telemetry into Evidence, a
  Trigger, or Register attention;
- infer that one operating-state value is stronger, broader, more restrictive, more severe, more
  escalated, or higher priority than another;
- infer materiality, authority, applicability, grouping, or Decision change from source type,
  labels, similarity, recency, color, enum position, or software permission;
- provide live provider adapters, a polished browser/mobile interface, a generic workflow engine,
  or distributed production infrastructure; or
- replace accountable practitioner judgment with automation.

These absences are explicit. `OperationalApplication.require_supported` rejects the relevant
capabilities; the operator guide names them; Increment 6–8 tests prove the explicit external-event
path, absence of an Observation table/family, rejection of Observation as a Register source, and
absence of operating-state rank.

## 3. IRR-009 release-scope analysis

### 3.1 Four distinct meanings

| Level | Meaning | PAIM v0.1 position |
|---|---|---|
| 1 | Observing or monitoring information exists in the real world. | True and unavoidable. PAIM does not claim otherwise. |
| 2 | PAIM can receive manual/external information with exact provenance. | Supported through bounded Evidence, Authority, and explicit external Trigger-event intake. Arrival remains proposed/quarantined until an owning-domain action succeeds. |
| 3 | PAIM has an authoritative first-class Observation record family. | Not supported. No Observation identity, version, status, retention, currentness, scope, or correction contract is implemented. |
| 4 | PAIM automatically converts monitoring/telemetry into Evidence, Trigger, or Register attention. | Not supported. No automatic conversion, materiality, applicability, or projection-population rule exists. |

Levels 3 and 4 are not necessary for the fixed v0.1 goal. The implemented lifecycle requires that
material operational change can enter governed Reassessment; it does not require PAIM itself to
continuously discover that change. Exact existing PAIM records and explicit human/external source
occurrences already reach Trigger Determination with identity, source/effective/recorded/knowledge
context, Case, management question, replay behavior, and accountable materiality judgment.

The boundary preserves truth rather than concealing a substitute. An external event does not
become an Observation-like authoritative object. Intake alone does not make it Evidence or a
Trigger. A practitioner must invoke the existing owning-domain command, and the domain's
provenance, scope, accountability, currentness, and authority guards remain controlling.

The Case lifecycle label `OPERATING_OBSERVING` describes an operating management phase and its
visibility obligations. It does not establish a first-class Observation record family. The
Evidence/Authority specification reserves Observation only as a future typed extension category,
and the Reassessment contract explicitly permits exact existing records and human/external events
without that extension.

### 3.2 Exact supported v0.1 boundary

If the recommendation is accepted:

- manual/external monitoring information may enter only through an accepted
  provenance-preserving intake type;
- the information becomes substantive only through an existing authoritative Evidence, Trigger,
  or other owning-domain command;
- no telemetry, log, metric, alert, incident, source label, or delivery event is automatically
  Evidence, a Trigger, or a Register concern;
- Observation-like unaccepted objects are ineligible for Register population;
- no claim of continuous monitoring, automated breach detection, automated evidence generation,
  or automated telemetry conversion is made; and
- operator and release documentation must present the limitation as a product boundary, not as a
  temporarily successful placeholder.

### 3.3 Classification and later work

**Recommended IRR-009 disposition:** exclude the capability from v0.1 and defer its design to a
later release. The exact required classification appears once in §11.

IRR-009 remains semantically open. Post-v0.1 work is required before first-class Observation or
automation can be claimed. The smallest coherent later human design package must define:

- stable Observation identity and immutable Version identity;
- source provenance, Configuration/Boundary/scope binding, effective/recorded/knowledge time;
- status, correction, supersession, retention, currentness, and conflict;
- the distinction between technical telemetry, proposed intake, authoritative Observation, and
  Evidence;
- accountable conversion/linkage determinations to Evidence and Trigger, including absence and
  conflict;
- Evidence Applicability, Register eligibility, confidentiality, and historical reconstruction;
- adapter replay/quarantine/failure behavior; and
- negative, longitudinal, recovery, and human-judgment oracles.

No current implementation is evidence that those semantics have been resolved.

## 4. IRR-014 release-scope analysis

### 4.1 Sufficiency of exact-state semantics

The current application treats an operating-state value as an exact identity bound to an
authorized Decision or disposition. It does not compare state names or codes. This is sufficient
for the fixed v0.1 management loop because:

- every substantive operating-state change requires an authorized successor/amendment Decision;
- an Interim Operating Disposition may only restrict exact current operation;
- independently valid dispositions combine through exact structured-scope intersection;
- a determinable intersection applies all explicit restrictions;
- an indeterminate intersection suspends the affected scope rather than selecting a supposedly
  strongest state; and
- the Register can display/filter/count exact identities and exact source facts without turning
  presentation order into authority or priority.

Increment 6 proves that two different state values remain a set and suspend when their combined
effect is indeterminate. Increment 7 proves no `rank` exists on the Register entry. The
specifications prohibit recency, severity, enum order, color, breadth, queue priority, or product
convention from choosing a winner.

The phrase “stronger-state request” may still be retained as human/source narrative or a declared
management question. PAIM v0.1 does not mechanically establish that relation. The practitioner
must identify the exact proposed target state and use the existing Trigger/Decision path; no
automated stronger/broader oracle is claimed.

### 4.2 Exact supported v0.1 boundary

If the recommendation is accepted:

- displays, filters, counts, grouping, reports, and exports use exact operating-state identities
  only;
- current operation applies exact restrictive Interim Operating Disposition intersections by
  exact scope;
- indeterminate intersection suspends the affected scope pending authorized determination;
- PAIM does not infer relative strength, severity, breadth, restrictiveness, escalation,
  materiality, priority, or target-state ordering;
- enum order, labels, colors, numeric codes, workflow position, queue placement, notification
  frequency, and presentation sorting are non-semantic; and
- no release, operator, report, export, UI, or validation claim depends on ranked operating
  states.

### 4.3 Classification and later work

**Recommended IRR-014 disposition:** exclude the capability from v0.1 and defer its design to a
later release. The exact required classification appears once in §11.

IRR-014 remains semantically open. The smallest coherent later human design package must define:

- minimum versioned operating-state traits, including operational activity, scope, duration or
  transition character, evidence expectation, observation obligation, and active/inactive/terminal
  effect;
- an explicit organization-configured relation, preferably able to represent partial order and
  incomparable/indeterminate pairs rather than assuming a universal linear rank;
- identity, version, authority, scope, effective time, correction, and conflict for the configured
  relation;
- the exact effect, if any, on Trigger materiality, Reassessment, Intervention burden, Evidence,
  Decision eligibility, and Register presentation;
- the rule that relation results never authorize a Decision automatically; and
- hard, metamorphic, negative, historical, and organization-specific conformance oracles.

Exact-state behavior does not substantively resolve that future relation.

## 5. Complete-functional-application test

`PASS` below means the capability can be excluded without making the bounded v0.1 claim false. It
does not mean the deferred semantic problem has been designed.

| Criterion | IRR-009 exclusion | IRR-014 exclusion |
|---|---|---|
| 1. Every core practitioner path remains executable end-to-end. | **PASS.** Case-to-operation uses Evidence/Authority and manual intake; Trigger-to-Reassessment accepts exact existing records and explicit human/external events; Register derives only accepted source families. None requires an Observation family. | **PASS.** Decisions bind exact state identity; Reassessment applies exact restrictive scope intersection/suspension; Register displays exact identities. No core commit requires rank. |
| 2. Absence produces an explicit unsupported/manual boundary, not silent approximation. | **PASS.** Observation record/automation and telemetry conversions are enumerated unsupported capabilities; manual intake and practitioner promotion are explicit. | **PASS.** state ranking/strength inference is enumerated unsupported; indeterminate intersections suspend and Register entries have no rank. |
| 3. Existing semantics remain truthful and deterministic. | **PASS.** exact provenance, replay, Determination, scope, dual time, and owning-domain commands are deterministic; no source type silently becomes substantive. | **PASS.** exact identity equality, explicit structured restrictions, intersection, conflict, and suspension are deterministic; no implicit order selects a winner. |
| 4. No current release claim implies the missing capability. | **PASS, conditional on adopting §7 claim language.** The current operator guide already disclaims both Observation and conversion automation. README/release notes must use the bounded claim. | **PASS, conditional on adopting §7 claim language.** The operator guide disclaims rank/strength inference. No future display or report may imply it. |
| 5. Final practitioner validation can test the boundary directly. | **PASS.** Increment 9 can exercise explicit unsupported requests, manual event intake, promotion to Trigger, no Observation persistence, and no automated Register population. | **PASS.** Increment 9 can exercise exact state display, conflicting values, scope intersection/suspension, no rank attribute, and invariance to labels/colors/order. |
| 6. Deferral creates no hidden authority, safety, or reconstruction gap in implemented workflows. | **PASS.** accountable materiality and owning-domain commands remain required; missing automation cannot fabricate authority or erase source history. Operational detection outside PAIM remains an explicit organizational dependency. | **PASS.** every state change still requires Decision authority; conservative suspension handles indeterminate combined restrictions; exact versions and rationale remain reconstructable. |

Both exclusions pass all six criteria. The combined release claim is therefore supportable only with
the named boundaries and Increment 9 evidence in §8.

## 6. Roadmap/P1 interpretation

The current roadmap's broad “all nine P1 findings” language was written for a complete unqualified
PAIM validation claim. It must not be silently reinterpreted. Human acceptance of this record would
establish a narrower but complete v0.1 product claim and the following three-part status for each
finding:

| Finding | Semantic problem status | v0.1 product-scope gate status | Future status |
|---|---|---|---|
| IRR-009 | `OPEN — SEMANTICS UNDESIGNED` | `CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM` | Deferred post-v0.1 design before authoritative Observation or automated conversion. |
| IRR-014 | `OPEN — SEMANTICS UNDESIGNED` | `CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM` | Deferred post-v0.1 design before state relations, ranking, or automated escalation. |

`CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM` closes only the applicability of the finding to the bounded
v0.1 release gate. It is not substantive resolution and must never appear as `RESOLVED` in a
semantic findings register.

After human acceptance, a separate bounded consistency issue should update, at minimum:

- Implementation Sequence §§2, 3.2, 4.10, 7, and 10.7 so Increment 9 closes against the named
  bounded v0.1 P1 matrix rather than the prior unqualified all-nine rule;
- Platform Architecture §§20 and 23 to record the accepted v0.1 exclusion while preserving the
  extension gates;
- the implementation-readiness/P1 status and validation traceability matrices so semantic-open and
  product-gate-closed are distinct fields;
- Behavioral Validation scenarios that previously assume a mechanically “stronger” state or
  longitudinal Observation family, replacing them for v0.1 with the boundary oracles in §8; and
- README/release-note and operator-facing limitation wording using §7.

That later issue must not invent Observation or operating-state relations. This issue changes none
of those files.

## 7. Proposed v0.1 release claim

### 7.1 Claim if both exclusions are accepted

> **PAIM v0.1 is a complete functional local governed PAIM application for the implemented
> management lifecycle: Case and Configuration governance; Evidence, Authority, independent Value
> and Risk; Decision, Boundary, and Authorization; Intervention, Activation, and Learning;
> explicit-event Reassessment and restrictive interim operation; and source-traceable Management
> Register outputs. It supports authenticated local operation, provenance-preserving manual/external
> intake, access segmentation, recovery, and explicit degraded behavior. PAIM v0.1 is not a
> continuous monitoring or telemetry-automation platform and does not provide a first-class
> Observation record or automatic telemetry-to-Evidence/Trigger/Register conversion. It is not an
> operating-state ranking or escalation engine: operating states are exact identities, and interim
> restrictions use exact-scope intersection or suspension without inferred strength, breadth,
> severity, or priority.**

Short release-note form:

> **PAIM v0.1 delivers the complete bounded local governed management lifecycle using manual,
> provenance-preserving external intake and exact-state semantics. Continuous Observation
> automation and operating-state ranking/escalation are explicitly outside the v0.1 claim and are
> deferred to post-v0.1 design.**

### 7.2 Alternative claim if either finding is included

If design authority instead requires either finding's capability in v0.1, PAIM must not claim
v0.1 scope completion. The accurate interim wording would be:

> **PAIM is a functional local release candidate for the currently implemented governed lifecycle,
> but the v0.1 scope is incomplete pending accepted design, specification hardening,
> implementation, and validation of [first-class Observation and conversion semantics] and/or
> [operating-state relation and escalation semantics]. No release claim is made for those
> capabilities until their separate gates close.**

## 8. Increment 9 implications

### 8.1 Entry conditions under the recommended exclusions

Increment 9 may be separately authorized only after:

1. human design authority accepts both independent classifications and the combined verdict;
2. the bounded roadmap/validation consistency updates identified in §6 are accepted and merged;
3. the clean-main checkpoint and exact v0.1 claim under test are recorded; and
4. a separate bounded Increment 9 issue freezes scenarios, expected evidence, failure
   classification, and practitioner-study boundaries.

Acceptance of this record does not start Increment 9 automatically.

### 8.2 Required Increment 9 validation

Increment 9 must validate at minimum:

- all three practitioner paths through the authenticated operational gateway:
  Case-to-authorized-operation, Trigger-to-Reassessment-completion, and multi-Case
  Register-to-contextual-owning-domain-action;
- explicit/fail-closed rejection of Observation records, Observation automation, and every
  telemetry-to-Evidence/Trigger/Register conversion request;
- exact manual/external source occurrence → proposed intake → explicit practitioner promotion →
  Trigger behavior without Observation identity or semantic deduplication;
- exact operating-state identity and exact-scope Interim Operating Disposition intersection,
  including determinable restriction, indeterminate suspension, expiry, conflict, and successor
  Decision requirements without rank;
- UI/CLI/report/export/notification invariance: label, enum order, numeric code, color, queue order,
  frequency, and presentation must not imply state rank or substantive priority;
- operator and release documentation comprehension of both exclusions;
- full locked regression, migration/schema/foreign-key integrity, access/non-leakage, security,
  quarantine/replay, delivery, degraded-operation, backup/restore/rebuild, exact history,
  knowledge-time reconstruction, and longitudinal behavior; and
- practitioner usability and understandability, preserving usability findings separately from
  semantic verdicts.

### 8.3 Exit conditions

Increment 9 closes the bounded v0.1 gate only if:

- every in-scope hard oracle passes and all failures are classified;
- practitioners can execute and explain the three paths and both limitations;
- no interface or durable output claims either deferred capability;
- the traceability record maps every v0.1 claim to specification, implementation, tests, and named
  exclusions;
- recovery and historical reconstruction reproduce the exact authoritative basis; and
- the final release verdict uses the accepted bounded claim, while IRR-009/014 remain visibly open
  for post-v0.1 design.

### 8.4 Alternative sequence if either finding blocks v0.1

If either finding is made a v0.1 blocker, the smallest sequence before Increment 9 is:

1. one bounded human design package using the applicable minimum contents in §3.3 or §4.3;
2. coordinated governing-specification hardening and roadmap/validation updates;
3. independent focused implementation-readiness re-review;
4. one bounded implementation increment with migration/adapters/UI only as required by the
   accepted design;
5. full regression and a focused closure review; and only then
6. a separately authorized Increment 9 campaign expanded with the new semantic scenarios.

## 9. Updated completion estimate

### 9.1 Fixed denominator

The denominator is the **complete functional v0.1 application under the proposed bounded claim**,
not total PAIM ambition, post-v0.1 integrations, PR count, lines of code, or calendar effort. It is
fixed at 100 points and separates the dimensions required by this decision:

| Completion dimension | Weight | Earned at this proposed-decision checkpoint | Basis |
|---|---:|---:|---|
| Domain/spec semantics for the bounded v0.1 claim | 25 | 24 | All implemented lifecycle semantics are accepted and executable. One point remains because the release-boundary interpretation is not yet human accepted or reconciled into the controlling roadmap/validation wording. IRR-009/014 substantive semantics are outside this denominator only if the recommendation is accepted. |
| Executable management core | 40 | 40 | Increments 1–7 implement the authoritative/derived management loop with exact history, authority, conflict, and Value/Risk independence. |
| Operational application and readiness | 20 | 20 | Increment 8 supplies the authenticated restartable gateway, manual adapters, access segmentation, audit, delivery/export, recovery/rebuild, health/observability, degraded behavior, and explicit unsupported boundaries. |
| Release-scope decision | 5 | 2 | The decision package and exact claim are drafted, but human acceptance and later consistency updates are outstanding. |
| Integrated/practitioner validation | 10 | 6 | The 241-test suite includes extensive integrated, security, adapter, recovery, and boundary evidence. Formal frozen Increment 9 scenarios, practitioner evidence, final traceability, and release verdict remain. |
| **Total** | **100** | **92** | **Estimated complete functional v0.1 application completion: 92%.** |

### 9.2 Change from the prior 75% estimate

The prior estimate was made before Increment 8 and awarded only 5 of 20 operational points. The
merged local application closes the substantive authentication, access, adapter, export/delivery,
recovery, observability, and degraded-operation gap, adding 15 points. This artifact adds two
provisional release-decision points because the alternatives, claim, and gates are now explicit but
not accepted. To preserve the fixed 100-point denominator while showing the newly explicit
release-decision dimension, five points formerly embedded in the 45-point executable-core category
are split out: the core is now 40/40, three already-earned test-evidence points move to integrated
validation (from the former 3/10 to 6/10), and the new release-decision category earns 2/5. Thus the
prior checkpoint still normalizes to 75 points, and the only net increase is 15 delivered
operational points plus 2 proposed-decision points. The resulting movement from 75% to 92% reflects
delivered capability and evidence, not repository activity.

If design authority accepts the recommendation and the §6 wording updates merge, the release-scope
and semantic-reconciliation holdbacks may be earned. The remaining work is then principally
Increment 9 integrated/practitioner validation and the final release evidence—not implementation of
the two excluded semantic families.

## 10. Human decisions required

PAIM design authority must explicitly accept or reject each item; engineering cannot infer these
decisions from the existing unsupported implementation:

1. The IRR-009 v0.1 classification recorded in §11.
2. The IRR-014 v0.1 classification recorded in §11.
3. The combined verdict recorded in §11.
4. The exact claim language and limitations in §7.1.
5. The three-part finding treatment in §6: semantic-open, v0.1-gate-closed-by-design, future
   post-v0.1 work.
6. A later bounded consistency-update issue before Increment 9 entry.
7. A separate future design sequence before either excluded capability is enabled or claimed.

Rejecting either exclusion selects that finding's required inclusion classification and the
pre-Increment-9 sequence in §8.4. It does not authorize implementation automatically.

## 11. Final classifications and recommendation

| Decision | Classification |
|---|---|
| IRR-009 — first-class Observation and automated conversion | **`EXCLUDE FROM V0.1 — DEFER POST-V0.1`** |
| IRR-014 — operating-state relations/ranking/escalation | **`EXCLUDE FROM V0.1 — DEFER POST-V0.1`** |
| Combined PAIM v0.1 release scope | **V0.1 SCOPE COMPLETE — PROCEED TO INCREMENT 9 VALIDATION** |

The recommendation is to accept the two exclusions as explicit v0.1 product boundaries, preserve
both findings as semantically open post-v0.1 design work, reconcile the roadmap and validation
wording in a separate bounded issue, and then separately authorize Increment 9 validation against
the exact claim in §7.1.
