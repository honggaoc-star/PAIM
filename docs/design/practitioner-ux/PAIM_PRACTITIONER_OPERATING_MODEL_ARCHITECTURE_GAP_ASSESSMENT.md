# Practitioner Operating Model Architecture Feasibility & Gap Assessment

## Status and scope

This assessment compares the proposed
[Practitioner Operating Model](PAIM_PRACTITIONER_OPERATING_MODEL.md) with current PAIM architecture.
It authorizes no code, schema, specification, networking, or deployment change.

The technical basis is the current
[M1 implementation architecture](../../engineering/PAIM_UI_M1_IMPLEMENTATION_ARCHITECTURE_DECISION_v0.1.md),
[Platform Architecture](../../engineering/PAIM_PLATFORM_ARCHITECTURE_v0.1.md),
[local operational guide](../../operations/PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md),
[Roles and Accountability Specification](../../system/specifications/PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md),
and executable repository structure inspected at the Issue #123 clean-main checkpoint.

## Executive assessment

PAIM can improve read-side orientation immediately by composing authoritative state into clearer
`ready`, `waiting`, and unresolved explanations. It cannot safely implement durable responsibility
assignment, cross-practitioner handoff, or organization-local concurrent use as UI-only work.

Three distinct gates are required:

1. **Read-composition gate** — bounded derived work over current records, with no durable assignment.
2. **Normative work/responsibility gate** — specifications, authoritative records, migrations,
   commands, history, and hard oracles.
3. **Organization-local deployment gate** — remote security, durable sessions, concurrency,
   availability, and operational evidence.

## Current architecture fit

| Area | Current support | Fit and limitation |
|---|---|---|
| Actor model | Versioned PAIM Actor is separate from technical principal; actions retain attribution. | Suitable participant identity foundation. It lacks ordinary participant profile, Case involvement, contact/notification preference, and practical-role membership. Those should not be inferred from access. |
| Role Assignment | Versioned actor/function relationship; one typed target; Case context; accountable flag; compatibility key; effective interval; delegation; currentness/vacancy/conflict. | Preserves rigorous provenance but conflates practical role and granular responsibility. It lacks obligation kind/identity, purpose/use/assessed scope, multi-record context, requester/return, and work completion. `Applicability Owner` exposes this gap. |
| Decision Authority | Separate Decision Authorization Basis and fail-closed authority behavior. | Strong fit. Must remain outside the standing Case role model and separate from task assignment. The UI may identify the expected/authorized participant but must not create a `Decision Maker` role. |
| Access/permission | Authenticated principal maps to Actor; exact Case/Configuration access and command permission are checked separately from accountability/authority. | Strong semantic separation. Current administration is local/technical and not a future responsibility-assignment workflow. Organization-local identity lifecycle and delegated access administration remain undesigned. |
| Operational gateway | One authenticated gateway composes access checks and domain commands; idempotency and audit are retained. | Good future command boundary. No work/responsibility commands exist. Current CLI/browser concurrent-write use is not a supported product workflow. |
| SQLite persistence | Append-only/versioned domain records, foreign keys, `BEGIN IMMEDIATE` semantic writes, integrity checks, backup/restore. | Suitable current single-workstation authority. It serializes writers but has no demonstrated organization-local concurrency/load/availability claim. Database choice for a future server remains open pending evidence. |
| Browser sessions | Opaque, server-side, process-local sessions; one worker; restart logout; loopback-only host policy. | Secure bounded M1 fit, but incompatible with multi-worker/failover and inconvenient for shared organization deployment. Durable/revocable shared sessions and HTTPS posture require a new architecture decision. |
| Browser topology | FastAPI/Jinja, `127.0.0.1`, one Uvicorn worker, no CORS/non-loopback exposure. | Supports current single-workstation local mode only. `Local` cannot yet be advertised as organization-local multi-practitioner. |
| Practitioner read composition | Access-filtered Case workspace reconstructs authoritative current state, Value/Risk lanes, prerequisites, and explanations on request. | Strong basis for derived `ready/waiting` views. No durable work identity, assignee, due time, return, or cross-person state exists. Read composition must not manufacture them. |
| Action intents | Process-local, short-lived review-before-commit intents with exact preconditions/idempotency. | Suitable for one practitioner's bounded confirmation, not durable work assignment or handoff. Restart invalidates them by design. |
| Append-only history | Exact Records/Versions, effective/known time, status events, relationships, audit and reconstruction. | Strong foundation for future Work/Responsibility records. Existing history must not be reinterpreted or rewritten during migration. |
| Notifications | Derived notification intents/delivery exist for Management Register output. | Demonstrates non-authoritative delivery separation, not a general Case-work notification contract. Reuse requires explicit source/work context and access-safe delivery design. |
| Backup/availability | Operator-controlled SQLite backup/restore, integrity and health surfaces. | Adequate for bounded local v0.1. Organization-local service needs scheduled operations, recovery objectives, monitoring, upgrade/rollback, and availability ownership. |

## What can be done over current authoritative state

After owner acceptance, a separately bounded read-only design may:

- replace ontology-first summaries with `Where things stand`;
- derive unranked ready work and exact waiting reasons from current records;
- distinguish `Your current actions` only where the signed-in Actor's existing exact assignment is
  already authoritative;
- carry exact prerequisite context and return links within one browser session as UX-3A already
  does; and
- hide engineering details from routine pages while retaining authorized history/inspection.

It must not call a participant responsible when only software access, authorship, Case ownership,
or a broad role label exists. It cannot preserve cross-session assignment or handoff without a new
authoritative record.

## What requires normative specification revision

Design authority must specify:

- Participant and practical-role semantics, including whether either is authoritative Case state;
- Responsibility identity, Version, obligation taxonomy, context, effective interval, accountable
  selection, delegation, supersession, conflict, and history;
- the relation between Responsibility and existing Role Assignment;
- Work Item identity, allowed states, prerequisites, result/return relationships, cancellation, and
  non-duplication of domain lifecycle;
- which current named roles become responsibility kinds and which remain authority concepts;
- whether and how a responsibility can bind several exact record targets while Role Assignment has
  one typed target;
- legitimate unresolved completion outcomes;
- notification and bounded-note semantics; and
- historical/migration treatment for existing Role Assignments and legacy mechanism strings.

The Roles & Accountability, Integrity, relevant domain specifications, architecture, validation
strategy, and implementation sequence would then need coordinated hardening. This issue must not
edit them automatically.

## What requires new authoritative records and persistence

If the normative gate accepts durable coordination, likely additions include:

- Responsibility Record/Version or an explicitly revised Role Assignment contract;
- Work Item Record/Version with exact context, state, requester, assignee/responsibility, result,
  return, and predecessor/successor relationships;
- optional bounded Work Note records only if demonstrated necessary;
- operational notification intents sourced from exact Work Versions; and
- indexes/constraints for current assignment, Case/participant work, source/result relationships,
  idempotency, effective/known-time reconstruction, and conflict detection.

These require migrations and backward-compatible interpretation. Work state may never become a
second authoritative copy of Applicability, Fitness, Selection, Decision, Intervention,
Reassessment, or other lifecycle state.

## Organization-local multi-practitioner deployment gap

The recommended future direction is an organization-controlled service, but current M1 is not that
service. A later deployment decision must cover:

| Concern | Required decision/evidence |
|---|---|
| Network | Non-loopback bind, private-network boundary, HTTPS/TLS, reverse proxy, trusted hosts, origin/CSRF, firewall and update posture |
| Identity | Organization-managed login, principal/Actor lifecycle, account recovery, revocation, optional federation, no directory-to-authority inference |
| Sessions | Durable shared session store, secure `__Host-` cookie, rotation/revocation, multi-worker behavior, restart/failover semantics |
| Concurrency | Supported writer topology, optimistic/currentness conflicts, idempotency, contention/load tests, long-read behavior, CLI/admin coordination |
| Persistence | SQLite concurrency evidence or another database decision, migration/rollback, encrypted storage/backup policy, recovery objectives |
| Availability | Service supervision, health/readiness, backup schedule, restore drills, upgrades, monitoring, incident ownership |
| Privacy | access-before-aggregate, protected notifications, logging/redaction, retention, administrator boundaries, audit access |

One authoritative application service should own writes. Multiple browsers may submit work to that
service; multiple independent local processes writing the database directly should not become the
target architecture merely because SQLite can serialize some writes.

## Single-workstation mode implications

The current topology can later support sequential multi-practitioner handoffs on one workstation if:

- each practitioner signs in with a distinct principal mapped to an attributable Actor;
- logout/session expiry prevents identity carryover;
- durable Work/Responsibility records, not browser session variables, carry the handoff;
- only one managed application process owns the write boundary; and
- operator backup, workstation security, and availability expectations are explicit.

That support does not exist merely because multiple accounts can be configured. The work model must
be implemented and validated first.

## Proposed staged architecture gates

### Gate A — Operating-model acceptance

Owner reviews this design package. No code or normative change.

### Gate B — Normative Responsibility and Case Work design

Revise specifications and architecture; define exact records, selectors, commands, migration,
security, and hard oracles. Reconcile existing role assignments without rewriting history.

### Gate C — Domain/persistence implementation

Implement and validate authoritative Responsibility/Work capabilities through production services.
No broad UI redesign until these capabilities are stable.

### Gate D — Practitioner read and coordination UI

Build `Where things stand`, `Your work`, `Waiting on others`, participant/responsibility assignment,
contextual handoff, and return behavior over the accepted contracts. Keep work-centered
notifications secondary.

### Gate E — Organization-local deployment

Make and validate the separate remote/multi-practitioner architecture decision. It may follow or
overlap bounded UI work only after its security/concurrency assumptions are explicit.

## Risks if treated as UI-only work

- role labels would become false accountability;
- `Applicability Owner` could harden into an accidental organizational model;
- browser session state could masquerade as durable handoff;
- task completion could duplicate or override domain results;
- permission could be mistaken for responsibility or authority;
- concurrent users could rely on an unsupported topology; and
- notifications/chat could become a shadow Case record.

The correct response is to stop at the design gate, not to hide these gaps with copy or navigation.
