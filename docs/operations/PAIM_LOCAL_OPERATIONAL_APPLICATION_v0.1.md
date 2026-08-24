# PAIM Local Operational Application v0.1

This guide covers the bounded Increment 8 local application. It is an implementation-facing
operator guide, not a change to PAIM system semantics or the v0.1 release claim.

PAIM v0.1 is released under the bounded validated claim. The Increment 9 automated and human
pathways, practitioner-findings remediation, and bounded human confirmation are complete. The
Observation and operating-state limitations in §10 are intentional bounded v0.1 product
boundaries, not silent placeholders or evidence that their substantive semantics have been
designed.

## 1. Boundary

The application is a synchronous local CLI and typed Python gateway over the existing Increment
1–7 services. It uses the same durable SQLite database and Alembic lineage. The gateway performs
authentication and software-access checks before it invokes an existing semantic command.

Software permission only permits an attempted command. It is not a PAIM Role Assignment,
accountability determination, Evidence Applicability judgment, Decision Authority, Completion
Acceptance, or Activation Authorization. An operational administrator receives no substantive PAIM
authority through administration permission.

### Runtime prerequisite

PAIM v0.1 supports CPython `>=3.12,<3.13`; CPython `3.12.13` is the exact reproducible reference
interpreter. The interpreter, its SQLite extension, and installed native wheels must be permitted by
the workstation's Application Control/security policy. Do not disable or bypass that policy. A
downloaded or repository-local runtime is not supported merely because its version matches.

Before setup, identify an organization-approved CPython 3.12.13 executable and verify it directly.
In this example, replace the assigned path with the actual approved installation path:

```powershell
$PaimPython = 'C:\approved\Python312\python.exe'
& $PaimPython -c "import sys, sqlite3; print(sys.version); print(sqlite3.sqlite_version)"
uv sync --locked --python $PaimPython
uv run --locked --python $PaimPython python -c "import paim; print(paim.__file__)"
```

The preflight must report Python 3.12.x, import SQLite without a policy error, complete locked sync,
and import PAIM. Stop and obtain an approved runtime if any native component is blocked. Do not
change `.python-version`, `pyproject.toml`, or `uv.lock` as a workstation workaround.

## 2. Configuration

Create a local JSON file outside source control. The file contains paths and the name of an
environment-based credential source; it contains no credential value.

```json
{
  "database_path": "C:/paim-local/state/paim.sqlite3",
  "credential_env": "PAIM_LOCAL_TOKEN",
  "intake_directory": "C:/paim-local/intake",
  "spool_directory": "C:/paim-local/spool",
  "export_directory": "C:/paim-local/export",
  "backup_directory": "C:/paim-local/backup",
  "event_log_path": "C:/paim-local/events/operational.jsonl"
}
```

All fields are required. The four operational directories must be distinct. Startup fails closed if
the configuration is absent, unreadable, incomplete, or if the configured credential environment
variable is empty. Paths are created as needed. Never put a password/token in the JSON file,
repository, fixture payload, PAIM record, command line, or ordinary log.

Set the credential from an external protected source in the current process. For example, on
Windows PowerShell, a protected local file can be read without placing the token in command
history:

```powershell
$env:PAIM_LOCAL_TOKEN = (Get-Content -Raw C:\secure\paim-owner.token).Trim()
```

The application stores only a per-version random salt and a PBKDF2-HMAC-SHA256 verifier with
600,000 iterations. There is no default principal, shared administrator, or default credential.

## 3. Initial bootstrap

The first bootstrap is allowed only when the principal registry is empty. Explicit flags choose
the initial software permissions. `--admin` grants only the bounded operational actions needed to
manage principals/access, inspect counters, and perform backup/restore. It does not authorize any
PAIM Decision.

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json bootstrap `
  --principal principal:local-owner `
  --admin `
  --allow-command actor.create
```

Create the first PAIM Actor through the authenticated gateway:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json actor-create `
  --principal principal:local-owner `
  --display-name "Local PAIM Owner" `
  --effective-at 2026-08-19T00:00:00+00:00
```

Retain the returned `actor_id`, then append a new principal version mapping the principal to that
exact Actor. The subject credential is read from the named environment source and is never echoed:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json principal-update `
  --principal principal:local-owner `
  --subject-principal principal:local-owner `
  --subject-token-env PAIM_LOCAL_TOKEN `
  --actor-id <returned-actor-id> `
  --status ENABLED
```

An enabled but unmapped principal may use explicitly permitted non-substantive bootstrap behavior;
all substantive commands fail closed until one current actor mapping is established. `DISABLED` or
`REVOKED` principal versions fail authentication.

## 4. Software access

Access facts are append-only. Append a later `ALLOW` or `DENY` fact for the exact
principal/permission/action/scope tuple to change current software access.

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json access-grant `
  --principal principal:local-owner `
  --subject-principal principal:practitioner-1 `
  --permission CASE_READ `
  --action read `
  --scope-type CASE `
  --scope-id <case-id> `
  --effect ALLOW
```

Permissions are `LOGIN`, `CASE_READ`, `CONFIGURATION_READ`, `COMMAND`, `EXPORT`, `DELIVERY`, and
`OPERATIONAL_ADMIN`. Scopes are `GLOBAL`, `CASE`, and `CONFIGURATION`. Case/Configuration access is
computed from trusted stored policy, never from a caller-supplied `accessible_case_ids` value.

The Register keeps the requested global population separate from visible Case scope so a partially
hidden Shared Dependency reports `access_filtered=true` and no global constituent count. Hidden
Case/Configuration IDs, exact protected facts, payloads, and counts are removed from returned filter
metadata, exports, notifications, errors, and operational audit details. If a visible Case contains
a requested Configuration without Configuration access, the local v0.1 boundary hides the Case
for that query rather than risk same-Case leakage.

## 5. Practitioner gateway

The CLI provides concrete local commands for bootstrap, Actor creation, principal/access
administration, Case/Configuration creation, intake, delivery, export, backup/restore, health,
counters, and unsupported-capability checks. Use `paim-local --help` and each subcommand's `--help`
for exact arguments.

The Python `OperationalApplication.run_command` method is the typed gateway for the remaining
Increment 1–7 commands. It establishes `CommandMeta` from the authenticated session and retains the
principal, resolved Actor, command ID, idempotency scope/key, correlation ID, causation ID, and
operational allow/deny evidence. It calls the existing `Increment7ApplicationService`; it does not
copy or weaken domain rules.

Sensitive actions such as Decision Authorization, Completion Acceptance, Activation
Authorization, Reassessment confirmation/successor, and Shared Dependency determination require
an exact claimed Actor matching the authenticated principal's actor mapping. The existing PAIM Role,
authority, currentness, Boundary, accountability, and other guards then remain controlling.

The application intentionally has no generic `approve`, `resolve`, `override`, `admin authorize`,
or Register “mark resolved” command.

For the production-only sequence, prerequisites, exact-identity discipline, and next owning action
for each of the three v0.1 lifecycle pathways, use
`PAIM_V0_1_PRACTITIONER_PATHWAYS_v0.1.md`. That guide standardizes self-contained stages and
persisted reconstruction; historical Increment 9 walkthrough transcripts are evidence, not reusable
operator instructions.

## 6. Manual intake envelope

`intake` accepts a bounded JSON object plus explicit envelope fields:

- adapter type (`VALUE`, `RISK`, `EVIDENCE`, `AUTHORITY`, or `EXTERNAL_TRIGGER`);
- source system/provider, source object ID, and source Version;
- source effective/observed time and application ingest time;
- exact replay identity and payload SHA-256 checksum;
- mapper rule ID/Version;
- exact target Case/Configuration and management context where required;
- payload reference, bounded retained payload, and unmapped material; and
- quarantine reason or predecessor intake ID for a source successor.

Example payload file:

```json
{"finding":"bounded source material","source_quality":"declared"}
```

Example Value intake:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json intake `
  --principal principal:practitioner-1 `
  --type VALUE `
  --source-system fixture:aivm `
  --source-object-id value-case-001 `
  --source-version v3 `
  --source-effective-at 2026-08-18T00:00:00+00:00 `
  --replay-id aivm-value-case-001-v3 `
  --mapper-rule-id value-fixture `
  --mapper-rule-version v0.1 `
  --case-id <case-id> `
  --configuration-id <configuration-id> `
  --file C:\paim-local\intake\value-case-001-v3.json
```

Value and Risk use distinct logical adapter types and intake rows even if their parser/transport is
shared. Arrival produces `PROPOSED`, never accepted/frozen/current input. Evidence arrival never
establishes applicability or fitness. Authority arrival never establishes permission, prohibition,
or Decision Authority. External Trigger events require an exact Case and management question and
create no Observation.

An absent/mismatched target, missing provenance, oversized payload, exact replay-key payload
mismatch, or same-source-Version payload mismatch produces `QUARANTINED`. Exact replay returns the
existing intake idempotently. A materially changed source uses a new source Version and replay ID;
its proposed intake points to the predecessor. Correct and resubmit as a new explicit source
version—there is no quarantine override that finalizes a PAIM record.

## 7. Notification delivery and exports

`deliver` consumes an exact Increment 7 notification intent and writes one deterministic local
spool JSON file. Each attempt has append-only `PENDING` then `DELIVERED` or `FAILED` technical
events. Retrying with the same attempt ID is idempotent; retrying a failed delivery uses a new
attempt ID. Delivery never mutates the source concern, Decision, or Reassessment.

`export --format json|csv` requires an exact retained Register manifest whose trusted access
context matches the current principal. JSON carries the full visible manifest basis. CSV repeats
manifest ID/checksum, effective/known context, rule Version, high-water/watermark, consistency, and
access context on each flattened entry/group row. Conflicts and absence remain explicit JSON basis;
CSV never selects a winner.

## 8. Backup and restore

Create an application-consistent SQLite backup:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json backup `
  --principal principal:local-owner `
  --label before-change-001
```

SQLite's online backup API creates the snapshot. Its sidecar manifest records application/schema
Version, UTC time, non-secret source filename, checksum/size, source high-water, all table counts,
derived-output inclusion, operator principal, and the initiating audit fact.

Restore always targets a new path:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json restore `
  --principal principal:local-owner `
  --backup C:\paim-local\backup\before-change-001.sqlite3 `
  --manifest C:\paim-local\backup\before-change-001.manifest.json `
  --target C:\paim-local\recovery\verified.sqlite3
```

Before publishing the separate target, verification checks checksum/size, application and Alembic
compatibility, SQLite integrity, foreign keys, required append-only triggers, every table count,
record high-water, and every retained Register manifest checksum/reconstruction basis. Corrupted,
tampered, incomplete, wrong-schema, incompatible, or already-existing targets are rejected. The
active database is never replaced or modified by restore verification.

Replication, failover, point-in-time recovery, and distributed recovery are not implemented.

## 9. Health and observability

`health` distinguishes process-alive from readiness. `READY` requires database reachability,
Increment 8 schema compatibility, SQLite integrity, foreign-key integrity, usable configured
directories/spool, and internally consistent Register manifests. Otherwise it returns `DEGRADED`
with bounded reason codes. Health does not claim that PAIM substantive evidence or a Decision is
valid.

`counters` aggregates append-only operational audit facts by category/outcome. Facts cover
authentication and actor resolution, access allow/deny, command outcome, administrative changes,
intake/replay/quarantine, delivery, export, backup/restore, integrity, configuration, and projection
state. Correlation/causation IDs are preserved where available. Audit details reject keys that
could carry credentials, secrets, payload bodies, or content. Operational events and counters are
not Evidence or Observation.

Degraded behavior fails closed: unavailable authentication/access or database integrity blocks a
new semantic command; intake failure creates no PAIM record; delivery failure leaves intent and
sources unchanged; stale/inconsistent Register views cannot launch action; backup failure leaves
the active database unchanged; and restore failure publishes no target. Previously authorized
operation remains governed by its exact existing Decision, Boundary, and effective Interim
Operating Dispositions.

## 10. Explicitly unsupported in v0.1

The application explicitly rejects and fails closed for:

- first-class Observation persistence, continuous monitoring, and Observation/telemetry
  automation;
- automatic telemetry/log/metric/alert/intake conversion to Evidence, Trigger, or Register
  attention;
- operating-state strength, breadth, restrictiveness, severity, rank, score, priority, or escalation
  inference, including inference from labels, enum/numeric order, color, recency, queue order, or
  notification frequency;
- semantic/AI dependency matching as authority;
- live Value/Risk/directory/document/authority/messaging/BI/task/incident integrations;
- a generic workflow engine or scheduler;
- cross-Case authority transfer or generic Register resolution; and
- distributed production topology.

Manual/external intake is provenance-preserving and remains `PROPOSED` or `QUARANTINED`; it is
non-authoritative until an explicit owning-domain command succeeds. An exact accepted external
source occurrence can support the existing Trigger path without creating Observation identity, and
no provider/text similarity performs semantic deduplication. The application preserves exact
operating-state identity and supports exact-scope restrictive Interim Operating Disposition
intersection; an indeterminate combined effect suspends only the affected scope.

Use `unsupported --principal <principal> <CAPABILITY>` to exercise the negative boundary. IRR-009
and IRR-014 each remain `OPEN — SEMANTICS UNDESIGNED` while each bounded-v0.1 product gate is
`CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM`. Separate post-v0.1 human design authority,
specification, implementation, and validation are required before either extension may be enabled,
and no extension may reinterpret v0.1 historical records. Increment 9 practitioner evidence is
retained in `../system/testing/PAIM_INCREMENT_9_V0_1_VALIDATION_RESULTS_v0.1.md`, and the findings
review is retained in
`../engineering/PAIM_INCREMENT_9_PRACTITIONER_FINDINGS_CROSS_PATHWAY_REVIEW_v0.1.md`. The effective
release verdict is recorded in `../engineering/PAIM_V0_1_RELEASE_GATE_DECISION_v0.1.md`; it does
not authorize post-v0.1 work.

## 11. Post-v0.1 M1 browser development

The M1 browser is an **under-development post-v0.1.0 application**. It is not part of the
immutable PAIM v0.1.0 release claim and is not broadly ready for external practitioners. M1A
provides secure local sign-in plus access-filtered Home and Cases views. M1B adds browser Case
creation and the first substantive Case Workspace: exact Configuration creation/successors and
governing designation, Evidence, Authority and Authority Gaps, Configuration-bound Evidence
Applicability, and equal independent Value and Risk input/readiness/fitness/selection lanes.
M1C adds exact current-basis Integration, finalized Boundary, and separate Decision proposal and
authorization interactions. UX-1 adds a read-only task-oriented orientation shell: persisted Case
title, plain current position, unranked available work, and separately disclosed unresolved
conditions. Passive Case orientation does not infer an intended downstream action or promote the
last incomplete lane to a required next task. It does not persist or infer a generic
task, attention, rank, priority, readiness, authority, or operating status.

UX-2 changes the `What we know` browser organization without changing the production write
contracts. It separates recorded information available for consideration, explicitly unavailable
information, requirements/authority sources, and review work. Information is placed in the
unavailable section only when its governed content establishes `unknown = true` and
`not_a_positive_finding = true` under the `unknown` Evidence classification. Other unknown records
remain neutral, and repository silence creates no inferred gap. Applicability and unresolved Authority
questions remain explicit governed judgments; displaying a source establishes no Value/Risk
relevance, sufficiency, accountability, substantive authority, or Decision support.

UX-3 changes the `Value & Risk` browser organization without changing the production analytical
commands. Each lane presents four separate practitioner acts: develop an assessment, confirm it is
ready for review, judge whether it is sufficiently supported for an intended use, and explicitly
choose a supportable assessment for that use. The page reconstructs those stages from authoritative
status events and exact relations; it creates no persisted task or progress state. Value and Risk
remain independent peers, can be at different stages, and are never combined into a score or
automatic choice. Selecting information for an assessment does not create Applicability; an
Applicability judgment does not create Fitness; Fitness does not select an assessment; and selection
does not create Integration or a Decision.

UX-3A preserves task context when that separate Applicability prerequisite crosses from `Value &
Risk` to `What we know`. For a ready assessment, PAIM lists only the current visible Evidence
Versions explicitly linked to that Input and identifies each missing information-to-assessment
judgment separately. Follow `Continue information review`, record scope, outcome, conditions,
limitations, rationale, and responsible governance process for one item, and confirm the
practitioner consequence. PAIM then returns to the next unresolved item or the originating lane's
support review. The count is reconstructed from governed records; it is not saved task state.

Entering `What we know` through ordinary navigation remains a general Case information workspace.
Leaving a contextual review changes no record. If the Case, setup, assessment, linked information,
visibility, or currentness changes, the handoff fails closed and must be reconstructed from `Value &
Risk`. Confirmation pages lead with the practitioner action and consequence; command and identity
detail is secondary, while the production command still revalidates all security and governance
prerequisites before commit.

UX-3A intentionally leaves three later interaction questions open: the long page can show both
development forms, the native multi-select control uses browser-specific Ctrl/Cmd interaction, and
the wording/interaction for information used as limitation, uncertainty, comparison, or
counterevidence requires separate analytical-input UX review.

The workspace is divided into Overview, Proposal setup, What we know, Value & Risk, Management
judgment, and Source & history. Governing assessment basis remains distinct from authorization and
operation. Routine pages use practitioner language; raw identifiers and payloads are omitted because
the browser does not yet have a separately enforceable Technical inspection permission. Authorized
operators retain the production CLI and audit paths for exact inspection and reconstruction.

The browser still stops before Intervention, Completion, Activation, Trigger/Reassessment, and
Management Register work. UX-3 does not redesign `What we know` beyond contextual reuse,
Integration/management judgment, Boundary/operating limits, proposal or authorization, the broader
Source & history narrative, reference-case fixture content, or M1D. UX-4 and later work remain
separate bounded implementation gates.

Use the same validated configuration and database as `paim-local`. The configured credential
environment source must remain available for the existing configuration preflight, but browser
credentials are entered at sign-in and are never read from that environment variable, persisted,
placed in a cookie, or rendered back to the browser.

```powershell
uv run --locked paim-web --config C:\secure\paim-local.json
```

After required schema, health, integrity, resource, and secure-randomness checks pass, the command
prints the exact local URL and binds only to `127.0.0.1` with one worker and no reload. Non-loopback
binds and failed required startup checks are rejected. M1 does not claim concurrent CLI/web write
support; use one managed application process for the authoritative domain write boundary.

Browser sessions are opaque, server-side, and process-local. Inactivity expires a session after 30
minutes; absolute expiry is eight hours; restart signs out every browser. The loopback HTTP cookie
is host-only, `HttpOnly`, `SameSite=Strict`, and `Path=/`. It cannot use `Secure` under the
intentionally HTTP-only M1 posture; any future HTTPS or non-loopback architecture must use a
`Secure` `__Host-` cookie and requires a new decision. Every protected request revalidates current
principal status, Actor mapping, and current visible access.

For browser development, install the browser binary matched to the locked Playwright package, then
run the bounded browser gate:

```powershell
uv run --locked playwright install chromium
uv run --locked pytest tests/browser --browser chromium
```

Templates and static assets are repository-owned package resources. Essential sign-in, Home,
Cases, the M1B Case Workspace and forms, confirmations, and sign-out work without JavaScript. Each
consequential form creates a bounded server-held action intent, confirms its exact source-Version
basis, invokes one named production capability, and reconstructs authoritative state through PRG.
Where a finite visible set exists, the server renders practitioner-labelled choices, binds the
selected option to its exact Record/Version identity, and revalidates visibility and currency again
at confirmation. A disappeared, hidden, or superseded choice fails closed before mutation.
The small same-origin script only adds submit locking; it owns no PAIM meaning or state.
