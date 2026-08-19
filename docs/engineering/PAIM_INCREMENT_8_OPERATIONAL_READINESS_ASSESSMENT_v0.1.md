# PAIM Increment 8 Operational Readiness Assessment v0.1

**Status:** Implementation-readiness assessment

**Assessment scope:** Increment 8 operational/integration readiness and remaining PAIM v0.1 gates

**Governing baseline:** `main` at `b479472eb8a9252976f283d9810bac5a4dfbc7e6`

**Decision effect:** Review only. This artifact does not amend a PAIM specification, select a
production topology, authorize an external provider, or implement Increment 8.

## 1. Executive conclusion

PAIM has an unusually complete executable semantic core for a pre-operational system. Increments
1–7 implement the common integrity kernel, Case/Configuration/Role foundation, Evidence and
Authority, independent Value/Risk intake, Integration/Boundary/Decision, Intervention and
Activation, Reassessment and interim disposition, and the derived Management Register. Seven
Alembic revisions and 179 collected test functions (217 pytest cases at the starting checkpoint)
exercise those capabilities through the in-process application services and SQLite adapter.

That baseline is not yet a functional practitioner application. The package deliberately has no
HTTP API, product CLI, UI, authentication mechanism, principal-to-actor adapter, external intake or
delivery adapter, backup/restore workflow, health surface, or operational telemetry. A caller can
construct `CommandMeta` and invoke services directly; the software does not yet establish that the
caller is entitled to do so. Register access filtering consumes caller-supplied accessible Case IDs
but does not determine them.

The minimum coherent Increment 8 is therefore a **bounded local operational application**, not a
production integration estate. It should add an authenticated application boundary, enforce
Case/Configuration confidentiality and action access before existing semantic services are called,
provide deterministic manual/file adapters for the required inbound and outbound seams, and prove
backup/recovery, projection rebuild, observability, and degraded behavior. Provider-specific live
integrations, first-class Observation, state-strength inference, distributed deployment, and a
polished UI are not required for functional PAIM v0.1.

IRR-009 and IRR-014 do not block that bounded Increment 8 because their dependent capabilities can
remain explicitly unavailable. They do expose a roadmap/release-gate mismatch: Roadmap §4.10 and
§10.7 require all nine P1 findings to close Increment 9, while a coherent narrow v0.1 can validate
the already-specified explicit Trigger path and exact-state behavior without Observation automation
or state ranking. PAIM design authority must decide the release claim before Increment 9 can close;
engineering must not silently reinterpret the gate.

## 2. Assessment basis and limits

The assessment reconciles:

- the system specifications under `docs/system/` as implementation contracts;
- Platform Architecture §§14–19, 20, and 23;
- the implementation sequence, especially §§4.9, 4.10, 10.5, and 10.7;
- the accepted Increment 1–7 design and P1 closure artifacts;
- Behavioral Validation Strategy §§23–44; and
- the executable package, migrations, and tests present at the governing baseline.

This review treats the specifications as authoritative and code as evidence of the current
implementation. It does not infer completeness merely from a table or class name, and it does not
require every integration or deployment capability imagined by the technology-independent
architecture.

## 3. Implemented baseline after Increment 7

| Capability | Executable evidence | Assessment |
|---|---|---|
| Integrity and history | `application/service.py`; integrity models; audit facts; SQLite semantic transactions; migration `0001` | Implemented with immutable versions, dual time, idempotency, explicit currentness/conflict, audit attribution, rollback, and point-in-time reads. |
| Case, Configuration, lifecycle, Roles | `application/increment2.py`; migration `0002` | Implemented, including typed scope, accountability absence/conflict, governing Configuration, determinations, and lifecycle guards. |
| Evidence, Authority, Value/Risk | `application/increment3.py`; migration `0003` | Implemented with separate Value/Risk lanes, exact version binding, Evidence Applicability, Authority Gaps, selection/freeze, and readiness. |
| Integration, Boundary, Decision | `application/increment4.py`; migration `0004` | Implemented with exact frozen inputs, uncertainty, Boundary snapshots/determinations, proposals, authority basis, authorization, and authorized-decision history. |
| Intervention, Completion, Activation, Learning | `application/increment5.py`; migration `0005` | Implemented with all-of prerequisites, accountable Completion Acceptance, activation authority, replacement/reuse, and Learning Items. |
| Trigger, Reassessment, interim disposition | `application/increment6.py`; migration `0006` | Implemented with explicit provenance, immutable Trigger Sets, bounded concurrency, overlap/coverage conflict, confirmation/successor completion, and restrictive overlays. |
| Register, shared dependencies, outputs | `application/increment7.py`; migration `0007` | Implemented as deterministic derivation plus manifests, notification intents, contextual actions, and source-traceable historical outputs. |
| Persistence and verification | SQLite/SQLAlchemy Core, seven Alembic revisions, contract/integration/scenario/unit suites | Adequate for a local functional v0.1; not evidence of production scale or operational recovery. |

The roadmap's older phrases such as “pending independent closure review” are historical checkpoint
language for IRR-010, IRR-011, and IRR-012. Their later gate-closure artifacts and merged
implementations are the current evidence. Updating that historical roadmap wording is unnecessary
for Increment 8 and would obscure provenance; this assessment supplies the reconciliation.

## 4. Minimum functional PAIM v0.1 goal

A functional v0.1 is a local, restartable PAIM application in which authorized practitioners can
execute and inspect the three governing pathways in §6 against durable data, with exact actor,
scope, version, time, authority, and source history. It must fail closed when identity, access,
authority, applicability, currentness, or adapter provenance is absent or conflicting. An operator
must be able to distinguish accepted authoritative records, proposed adapter material, derived
views, delivery state, and operational telemetry.

### 4.1 Must-have functional boundary

The minimum boundary may be a typed local CLI or a small local API; a browser UI is not required.
Whichever transport is selected must expose one application gateway rather than bypassing the
existing services. It must authenticate a principal, resolve the principal to the explicit PAIM
actor (or preserve unresolved/not-applicable status), calculate accessible scopes and allowed
actions, invoke the existing semantic transaction, and record allow/deny and administrative audit
facts. Software permission must never manufacture Role Assignment, Evidence Applicability,
substantive Authority, Decision Authority, Completion Acceptance, or Activation Authorization.

The functional fixture path must support deliberate operator entry/import of Cases,
Configurations, actors/roles, Evidence/Authority, separate Value/Risk inputs, and explicit external
Trigger events. Inbound material remains proposed/unaccepted until an authorized PAIM command
establishes the corresponding authoritative record. Deterministic local notification and export
delivery are sufficient to exercise outbound contracts.

### 4.2 Deferrable and out-of-scope capability

Provider-specific APIs, enterprise directory synchronization, document extraction, email/chat
delivery, BI connectors, external task/incident synchronization, first-class Observation or
telemetry conversion, state-strength/breadth inference, distributed workers, cloud deployment,
PostgreSQL, multi-tenancy, high availability, and polished visual design can be deferred. Their
absence must be explicit in the operator surface and validation claim; placeholders must not report
success or create authoritative data.

## 5. External adapter seam disposition

The adapter contract in Platform Architecture §15 remains controlling: retain source identity,
object/version, source and ingest time, provenance/integrity, scope, replay identity, unmapped
material, and quarantine reason; never finalize or authorize directly.

| Logical seam | Minimum v0.1 disposition | Governing boundary | Remaining-item IDs |
|---|---|---|---|
| Value intake | Manual/versioned fixture adapter required; maintain a distinct Value mapper and source lane. Live AIVM integration deferred. | Proposed intake only; authorized selection/freeze remains PAIM behavior. | R4, R15 |
| Risk intake | Manual/versioned fixture adapter required; maintain a distinct Risk mapper and source lane even if transport is shared. Live risk-system integration deferred. | No shared mutable Value/Risk record or score; selection/freeze remains PAIM behavior. | R4, R15 |
| Identity/directory | Explicit local principal-to-actor registry required. Enterprise directory synchronization deferred. | Directory membership cannot imply PAIM Role, accountability, or substantive authority. | R2, R3, R9 |
| Authority repository | Manual/versioned fixture adapter required. Live policy/authority repository deferred. | Source text cannot synthesize target identity or authority; ambiguity quarantines. | R5, R9, R15 |
| Evidence/document | Manual/versioned fixture adapter required. Document extraction/classification deferred. | Document presence cannot infer applicability, fitness, acceptance, or finality. | R5, R9, R15 |
| Notification | Deterministic local spool/delivery adapter required to consume notification intents. Email/chat/SMS providers deferred. | Delivery acknowledgement cannot mutate authoritative concern or decision state. | R6, R9, R15 |
| Report/export | Deterministic local JSON/CSV export required from an exact manifest. BI/document rendering deferred. | Preserve watermark, access context, source versions, conflict/absence, and derivation basis. | R6, R9, R15 |
| External task/incident | Not required for v0.1; defer. | Task completion is evidence, not Completion Acceptance; incident closure is not Trigger/Reassessment closure. | R9 |
| Observation/monitoring | Not enabled for v0.1; defer under IRR-009. Explicit external events may use the specified Trigger provenance path. | No Observation record and no automated Observation-to-Evidence/Trigger conversion. | R8, R9 |
| State-relation adapter | Not enabled for v0.1; defer under IRR-014. | Exact state identity only; no rank, stronger/broader inference, or state-derived priority. | R8, R9 |

## 6. End-to-end pathway trace

### 6.1 Case to authorized operation

| Step | Current executable state | Operational gap and disposition |
|---|---|---|
| Case → Configuration → roles | Domain commands and guards exist. | An authenticated practitioner entrypoint and access calculation are absent (R2, R3). |
| Evidence/Authority → Evidence Applicability | Exact records, gaps, typed applicability, accountability, and conflict exist. | Proposed fixture intake and quarantine are absent (R5). |
| independent Value/Risk → accepted frozen inputs | Separate lanes, fitness, acceptance, freeze, and readiness exist. | Proposed Value/Risk fixture intake is absent (R4). |
| Integration → Boundary → Decision → Authorization Basis | Full semantic command path and atomic authorization exist. | Transport serialization, access precheck, and security audit are absent (R2, R3). |
| Intervention → obligations/results/acceptance → Activation | Full prerequisite and authority path exists. | Operator workflow composition and visible blocked reasons are absent (R2, R13, R16). |
| Learning/history | Learning and exact history exist. | Practitioner inspection/export and recovery proof are absent (R6, R10, R13). |

No missing domain decision prevents this pathway. Increment 8 must compose existing commands without
weakening their preconditions or substituting a generic “approve” operation.

### 6.2 Trigger to Reassessment completion

| Step | Current executable state | Operational gap and disposition |
|---|---|---|
| Explicit event/existing record → Trigger | Exact source provenance and identity-only replay exist; no Observation is needed. | Manual external-event fixture intake and quarantine are absent (R5); Observation automation stays excluded (R8). |
| Trigger Determination/Set → Reassessment | Accountability, no-auto-grouping, immutable many-to-many membership, concurrency and conflict exist. | Authenticated composition and human-visible conflict resolution paths are absent (R2, R3, R13). |
| Interim Operating Disposition | Exact applicability, intersection/suspension, expiry, and current effect exist without rank. | Scheduling must not be invented; operator-driven expiry/recheck plus observable pending work is required (R11, R13). |
| Confirmation or authorized successor | Exactly one completion path, coverage, and prospective revalidation exist. | Integrated longitudinal and restart/recovery evidence is absent (R10, R13, R15). |

IRR-009 and IRR-014 are not hidden dependencies in this path. The functional claim is explicitly
limited to human/external provenance and exact state identity.

### 6.3 Multi-Case Register to contextual action

| Step | Current executable state | Operational gap and disposition |
|---|---|---|
| eligible Case concerns → Register | Exact concern population, conflicts, dual-time watermark, staleness, and access-filter labels exist. | The caller currently supplies accessible Case IDs; policy-derived access is absent (R3). |
| Candidate Set → Shared Dependency → Equivalence | Immutable candidates, accountable determinations, absence/conflict, and descriptive aggregation exist. | Operator entrypoint and access-safe fixture/report use are absent (R2, R3, R13). |
| Register context → action | Contextual Case action launch and notification intents exist without authority transfer. | Local delivery/export adapters are absent (R6); live providers remain deferred (R9). |
| rebuild/history | Derivation and exact manifests exist. | Rebuild tooling, equivalence verification, recovery drill, and lag/health reporting are absent (R10, R11, R15). |

## 7. Security and access readiness

The semantic core correctly distinguishes `principal_id`, attributable actor, PAIM Roles, and
substantive authority. It records command audit facts and tests that software permission cannot
authorize substantive outcomes. Those are necessary foundations, not a security perimeter.

Increment 8 must establish:

- authenticated principal acquisition and explicit principal-to-actor resolution;
- action authorization by record family, exact target/scope, active Role Assignment where
  applicable, and confidentiality segment;
- Case/Configuration/record/attachment-or-field-group segmentation where the selected v0.1 data
  shape needs it, with non-leaking counts and explicit protected-source indicators;
- a separate privileged-administration capability that cannot perform substantive PAIM actions by
  virtue of administration alone;
- security audit facts for authentication, allow/deny, administrative operations, exports,
  adapter quarantine/replay, and integrity/recovery actions; and
- safe configuration/credential handling with no secrets in source control, domain records,
  exports, or ordinary logs.

Authorization must be enforced at the common application boundary and again at access-sensitive
query/export composition. Passing an `accessible_case_ids` set from an untrusted caller is not
authorization. Redaction must preserve the fact that protected material affected a result when the
governing specification requires that context, without leaking the material.

## 8. Durability, recovery, and continuity readiness

SQLite is acceptable for the bounded local v0.1 selected by Increment 1: explicit `BEGIN
IMMEDIATE`, foreign-key enforcement, short semantic transactions, rollback, idempotency, and
contention behavior are already tested. It is not by itself a recovery plan.

Increment 8 needs an operator-controlled, application-consistent backup and restore workflow with:

1. a manifest identifying application version, schema revision, backup time, source database,
   checksums, and included projection/output state;
2. SQLite-consistent snapshot creation while semantic writes are safely bounded;
3. restore into a separate location, Alembic revision verification, foreign-key and integrity
   checks, and explicit refusal on mismatch/corruption;
4. preservation of record/version IDs, recorded/effective time, audit attribution, event order,
   authority history, and idempotency records;
5. deterministic Register/projection rebuild from authoritative records, compared to the captured
   manifest without treating the disposable projection as authority; and
6. a documented restart/degraded workflow covering busy database, partial adapter delivery,
   quarantined input, stale projection, and unavailable proof modules.

The v0.1 does not need point-in-time recovery, replication, automatic failover, or a production
database migration. It does need a repeatable restore drill proving that the local authoritative
history survives loss of the working database.

## 9. Observability and degraded operation

Minimum observability is semantic and operator-facing rather than a vendor platform. It must expose
structured events or counters for application availability, command success/rejection by reason,
writer contention, projection watermark/lag/rebuild, adapter accepted/replayed/quarantined/failed
states, delivery backlog, access denials, integrity check failures, and human-attention items. A
health/readiness command or endpoint must distinguish “process is running” from “database and
required proof paths are usable.” Correlation and causation IDs already present in command metadata
should connect the records.

Telemetry is never Evidence or Observation merely because it is collected. If an adapter is down,
PAIM retains proposed work or delivery intent and reports failure; it does not fabricate acceptance
or success. If a module needed to prove a new authorization/transition is unavailable, that new
semantic commit fails closed while already-authorized operation remains governed by its exact
Decision, Boundary, and any effective Interim Operating Disposition.

## 10. IRR-009 and IRR-014 disposition

### 10.1 IRR-009 — Observation

IRR-009 remains substantively open. The current implementation deliberately persists no
Observation and performs no automated telemetry-to-Evidence or Observation-to-Trigger conversion.
That does **not** block a functional v0.1: Reassessment already accepts exact existing PAIM sources
and explicit human/external events with source identity, provenance, and knowledge time. The
Increment 8 fixture adapter must use that path and label Observation/monitoring import unavailable.

Choosing whether Observation becomes an authoritative PAIM record remains PAIM design authority's
decision. It is required only before enabling a first-class monitoring adapter or claiming
Observation longitudinal validation.

### 10.2 IRR-014 — operating-state relations

IRR-014 remains substantively open. The current implementation stores and compares exact state
identity/applicability and prohibits inferred strength, breadth, severity, restrictiveness, rank,
or priority. Interim dispositions use only determinable explicit intersection and otherwise
suspend. Any changed operating state still requires an explicit authorized successor path.

That behavior is coherent for v0.1 and does not block Increment 8. IRR-014 is required before an
adapter or workflow infers stronger/broader state or before PAIM claims the complete escalation
oracle that depends on such a relation.

## 11. Increment 9 gate and v0.1 release claim

Roadmap §4.10 says that all nine P1 findings are prerequisites for a “complete PAIM validation
claim,” allows narrower validation only with named exclusions, and says that narrower validation
cannot close the full gate. Section 10.7 similarly requires all nine P1 findings before Increment 9
completion. By contrast, the accepted Increment 6 and 7 boundaries establish coherent explicit
Trigger and exact-state behavior while preserving IRR-009/014 as optional later extensions.

This is a scope/gate decision, not a reason to invent Observation or ranking during Increment 8.
Before Increment 9 can close, PAIM design authority must choose and record one of two paths:

1. retain the broad “complete PAIM” claim, resolve/harden/re-review IRR-009 and IRR-014, implement
   their required behaviors, and run the added scenarios; or
2. define the functional v0.1 validation/release claim as the accepted explicit-event/exact-state
   subset, amend the controlling roadmap and validation matrix so that named exclusions can close
   that bounded v0.1 gate, and leave IRR-009/014 visibly open for a later release.

The shortest coherent path is option 2. This assessment does not make or implement that design
authority decision. It also does not treat the decision as a prerequisite to starting bounded
Increment 8 work, because no proposed Increment 8 capability depends on either finding.

## 12. Canonical remaining-item register

This is the complete remaining-item inventory found by this assessment. Every item has exactly one
classification. Other sections refer to these IDs rather than creating additional unclassified
work.

| ID | Remaining item | Classification | Closure evidence |
|---|---|---|---|
| R1 | Decide the v0.1 validation/release claim and reconcile Roadmap §§4.10/10.7 with explicit IRR-009/014 exclusions, or expand scope to close both findings. | **BLOCKING HUMAN DESIGN DECISION** | Accepted design-authority record and conforming roadmap/validation changes, required before Increment 9 completion. |
| R2 | Add one authenticated local operator/application boundary that resolves principals/actors and composes existing services without semantic bypass. | **V0.1 MUST-HAVE** | Executable non-test entrypoint and contract tests for identity resolution, command dispatch, validation errors, and restart. |
| R3 | Enforce action/scope/confidentiality access, non-leaking queries/exports, separate privileged administration, and security audit while preserving software-permission/substantive-authority separation. | **V0.1 MUST-HAVE** | Allow/deny, segmentation, redaction, administrator non-authority, and audit hard oracles. |
| R4 | Add separate provenance-preserving manual fixture intake adapters for Value and Risk. | **V0.1 MUST-HAVE** | Adapter contracts prove lane independence, replay/idempotency, quarantine, unmapped retention, and no direct acceptance/freeze. |
| R5 | Add provenance-preserving manual fixture adapters for Evidence, Authority, and explicit external Trigger events. | **V0.1 MUST-HAVE** | Adapter contracts prove exact scope/time/source, unrelated-scope rejection, quarantine, no inferred applicability/authority, and no Observation creation. |
| R6 | Add local notification-spool and exact-manifest JSON/CSV export adapters. | **V0.1 MUST-HAVE** | Delivery/export contracts prove idempotency, access context, watermark/source retention, and no authoritative mutation from delivery. |
| R7 | Add configuration and credential hygiene for the selected local application boundary. | **V0.1 MUST-HAVE** | Startup validation and tests prove no default credential, secret logging, record leakage, or permissive fallback. |
| R8 | Keep first-class Observation/monitoring conversion and state-strength/breadth/ranking automation unavailable unless IRR-009/014 are later resolved. | **V0.1 MUST-HAVE** | Negative capability tests and operator documentation show explicit unsupported behavior and no hidden inference. |
| R9 | Implement provider-specific live adapters (AIVM/risk, directory, authority/document repository, messaging, BI, task/incident), Observation monitoring, and state-relation integration. | **DEFER POST-V0.1** | Separate future issues, each gated by its applicable accepted semantics and adapter contract. |
| R10 | Add application-consistent backup, separately located restore verification, migration/integrity checks, projection rebuild, and an operator recovery procedure. | **V0.1 MUST-HAVE** | Successful clean restore/rebuild plus corrupted, incomplete, and schema-mismatch refusal tests. |
| R11 | Add minimum health/readiness, structured operational events/counters, adapter/delivery status, projection lag/rebuild status, security/integrity signals, and explicit degraded behavior. | **V0.1 MUST-HAVE** | Observable failure injection proves fail-closed commits and no fabricated adapter/delivery success. |
| R12 | Add production database/topology, multi-tenancy, replication/failover, distributed workers, cloud infrastructure, and scale tuning. | **DEFER POST-V0.1** | Future deployment/scale decision and adapter conformance suite. |
| R13 | Execute automated integrated scenarios for all three §6 pathways, including absence/conflict, replay, stale input, knowledge-time reconstruction, and restart boundaries. | **V0.1 VALIDATION REQUIREMENT** | Versioned automated evidence against a fresh and upgraded database. |
| R14 | Run security, access, quarantine, degraded-operation, backup/restore, and projection-rebuild drills. | **V0.1 VALIDATION REQUIREMENT** | Versioned pass/fail evidence, failure classification, and retained recovery manifests. |
| R15 | Re-run the full locked quality/migration/schema/foreign-key suite plus all selected adapter contracts. | **V0.1 VALIDATION REQUIREMENT** | `uv lock --check`, full pytest, Ruff format/lint, strict mypy, empty/prior upgrades, schema verification, and `git diff --check`. |
| R16 | Conduct stable minimum practitioner workflow validation and preserve usability findings separately from behavioral verdicts. | **V0.1 VALIDATION REQUIREMENT** | Frozen scenario/instructions, observable results, practitioner evidence, and explicit verdict/failure classification. |
| R17 | Produce the bounded v0.1 traceability/release record for specifications → implementation → tests → exclusions → known limitations. | **V0.1 VALIDATION REQUIREMENT** | Accepted Increment 9 gate matrix consistent with the R1 decision. |
| R18 | Add a polished browser UI, mobile experience, rich dashboards, document rendering, or organization-wide workflow automation. | **DEFER POST-V0.1** | Future practitioner/product issue after minimum workflow evidence. |

## 13. Weighted completion estimate

The estimate uses a fixed 100-point denominator so that mature specifications and tests do not hide
the missing operational application:

| Completion dimension | Weight | Earned | Basis |
|---|---:|---:|---|
| Governing semantics and architecture | 25 | 24 | P0 and seven increment semantics are accepted; only the IRR-009/014 release-claim decision remains. |
| Executable authoritative core | 45 | 43 | Increments 1–7 and seven migrations cover the authoritative and derived loop; transport/operator composition is absent. |
| Operational application and integrations | 20 | 5 | Durable local transactions, audit, manifests, intents, and rebuildable design exist; access enforcement, adapters, recovery, and observability do not. |
| Integrated and human validation | 10 | 3 | Extensive hard-oracle automated tests exist; operational, recovery, security, end-to-end operator, and human evidence do not. |
| **Total** | **100** | **75** | **Estimated v0.1 completion: 75%.** |

This is a readiness estimate, not a claim that 75% of code lines or calendar effort is complete.
Remaining work is integration-heavy and security-sensitive, so its delivery risk is greater than its
point share.

## 14. Shortest remaining delivery sequence

The shortest sequence is four bounded packages:

1. **Increment 8A — local operational boundary and adapters:** R2–R8, with common adapter contracts,
   authenticated/access-controlled application gateway, explicit unsupported capabilities, and no
   provider-specific integrations.
2. **Increment 8B — recovery and operational hardening:** R10–R11, including restore/rebuild drills
   and observable degraded operation. This may be combined with 8A only if the issue remains
   reviewable and retains separate acceptance groups.
3. **v0.1 gate-scope decision:** R1, completed no later than the start of Increment 9. It may proceed
   in parallel with Increment 8 because it does not change the bounded Increment 8 behavior.
4. **Increment 9 — integrated/practitioner validation and release evidence:** R13–R17, judged under
   the accepted R1 claim. R9, R12, and R18 remain explicitly deferred.

No package should start automatically after its predecessor. Each remains subject to the PAIM
issue/branch/draft-PR/independent-review/merge/clean-main protocol.

## 15. Final recommendation

The existing semantics and executable core are sufficient to start a bounded Increment 8 that
excludes Observation automation, state ranking, live provider integrations, distributed production
infrastructure, and polished UI. The implementation issue must bind itself to R2–R8 and R10–R11,
with R13–R15 as its acceptance evidence, and must leave the Increment 9 release claim to the explicit
R1 design-authority decision.

**PROCEED TO BOUNDED INCREMENT 8 IMPLEMENTATION**
