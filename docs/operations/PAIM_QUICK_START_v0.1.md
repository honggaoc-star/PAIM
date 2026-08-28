# PAIM v0.1 Quick Start

This guide takes a clean PAIM checkout to a healthy local instance and a first Case with a
finalized candidate Managed Configuration. It uses the released local commands; on current
post-v0.1 development `main`, it also describes the prospective Slice-H browser entry point. The
tagged v0.1.0 release boundary remains the CLI and typed gateway recorded in its release notes.
Neither path bypasses or replaces PAIM's governing semantics. Continue with the
[Practitioner Pathways](PAIM_V0_1_PRACTITIONER_PATHWAYS_v0.1.md) for governing designation and the
full management lifecycles.

## 1. Before you start

You need:

- a clean checkout of this repository and `uv` available on the command line;
- an organization-approved CPython `>=3.12,<3.13` installation (CPython `3.12.13` is the exact
  reproducible reference);
- permission under the workstation's Application Control or security policy to run that
  interpreter, its SQLite extension, and installed native wheels; and
- a protected external location for the local credential and a local configuration outside the
  repository.

Do not disable or bypass security policy. If Python, SQLite, or a native package is blocked, stop
and obtain an approved runtime. Do not modify `.python-version`, `pyproject.toml`, `uv.lock`, or
runtime files as a workstation workaround.

Run every command below from the repository root. Replace each example path, timestamp, and
angle-bracket placeholder with an exact value for your instance. Record returned Record and
Version IDs in a protected, UTF-8 BOM-free operator artifact outside the repository. Do not use a
shell variable as the continuity authority between stages.

## 2. Verify the locked runtime

For the initial preflight and synchronization only, point `$PaimPython` to the approved CPython
3.12 executable:

```powershell
$PaimPython = 'C:\approved\Python312\python.exe'
& $PaimPython -c "import sys, sqlite3; assert sys.version_info[:2] == (3, 12); print(sys.version); print(sqlite3.sqlite_version)"
uv --version
uv lock --check
uv sync --locked --python $PaimPython
uv run --locked --python $PaimPython python -c "import sys, paim; assert sys.version_info[:2] == (3, 12); print(sys.version); print(paim.__file__)"
uv run --locked --python $PaimPython paim-local --help
```

All commands must succeed. Thereafter, use `uv run --locked ...`; it selects the synchronized
project environment. Do not invoke an arbitrary Python executable for PAIM application commands.

## 3. Create the local configuration and protected credential

Create `C:\secure\paim-local.json` outside the repository. Adapt the paths for your workstation;
keep the four operational directories distinct:

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

The configuration names the credential environment variable; it must not contain the credential.
Never place the secret in this repository, a configuration file, PAIM record, fixture, command
line, or ordinary log.

Load the secret from an external protected source into the current PowerShell process:

```powershell
$env:PAIM_LOCAL_TOKEN = (Get-Content -Raw C:\secure\paim-owner.token).Trim()
if ([string]::IsNullOrWhiteSpace($env:PAIM_LOCAL_TOKEN)) { throw 'PAIM credential is unavailable. Stop.' }
```

The environment variable is intentionally session-local and is normally lost when a new shell is
opened. Reload it from the protected source; do not try to recover it from PAIM. PAIM stores only a
salted verifier and does not echo the credential.

## 4. Bootstrap identity and verify health

Bootstrap is permitted only when the principal registry is empty:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json bootstrap `
  --principal principal:local-owner `
  --admin `
  --allow-command actor.create
```

`--admin` grants bounded operational administration only. It does not create a Role Assignment,
Decision Authority, Completion Acceptance authority, Activation Authorization, or any other
substantive PAIM authority.

Create the first Actor:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json actor-create `
  --principal principal:local-owner `
  --display-name "Local PAIM Owner" `
  --effective-at 2026-08-21T00:00:00+00:00
```

Persist the returned exact `actor_id`, then replace the placeholder below with that literal value:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json principal-update `
  --principal principal:local-owner `
  --subject-principal principal:local-owner `
  --subject-token-env PAIM_LOCAL_TOKEN `
  --actor-id <returned-actor-id> `
  --status ENABLED
```

Verify the application:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json health `
  --principal principal:local-owner
```

Continue only when the result is `READY`. `READY` means the local process, schema, database
integrity, directories, spool, and projection path are usable. It does **not** mean that Evidence,
authority, Value, Risk, a governing Configuration, or a Decision is established or valid. If the
result is `DEGRADED`, stop and use the
[Local Operational Application guide](PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md) to diagnose it.

## 5. Create the first Case and candidate Configuration

First inspect the released command contracts:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json access-grant --help
uv run --locked paim-local --config C:\secure\paim-local.json case-create --help
uv run --locked paim-local --config C:\secure\paim-local.json configuration-create --help
```

Grant permission to attempt Case creation:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json access-grant `
  --principal principal:local-owner `
  --subject-principal principal:local-owner `
  --permission COMMAND `
  --action case.create `
  --scope-type GLOBAL `
  --effect ALLOW
```

Create the Case:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json case-create `
  --principal principal:local-owner `
  --title "My first governed AI context" `
  --effective-at 2026-08-21T00:00:00+00:00
```

Persist the returned exact `case_id`. Use that literal ID in both grants below. The first grants
visibility of the Case; the second permits an attempt to create a Configuration in it:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json access-grant `
  --principal principal:local-owner `
  --subject-principal principal:local-owner `
  --permission CASE_READ `
  --action read `
  --scope-type CASE `
  --scope-id <returned-case-id> `
  --effect ALLOW

uv run --locked paim-local --config C:\secure\paim-local.json access-grant `
  --principal principal:local-owner `
  --subject-principal principal:local-owner `
  --permission COMMAND `
  --action configuration.create `
  --scope-type CASE `
  --scope-id <returned-case-id> `
  --effect ALLOW
```

Create `C:\secure\first-configuration.json` as the bounded content for the actual AI context you
intend to manage. Describe the capability, intended use, users, workflow, operating conditions,
and exclusions precisely; do not copy a test fixture or inject database state. Then create a
finalized candidate Configuration:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json configuration-create `
  --principal principal:local-owner `
  --case-id <returned-case-id> `
  --maturity finalized `
  --purpose candidate `
  --effective-at 2026-08-21T00:00:00+00:00 `
  --content-file C:\secure\first-configuration.json
```

Persist the returned exact Configuration Record and Version identities. Grant visibility for the
exact Configuration Record:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json access-grant `
  --principal principal:local-owner `
  --subject-principal principal:local-owner `
  --permission CONFIGURATION_READ `
  --action read `
  --scope-type CONFIGURATION `
  --scope-id <returned-configuration-id> `
  --effect ALLOW
```

This is the Quick Start endpoint: an authenticated Actor, a healthy local instance, an exact Case,
and an exact finalized candidate Configuration with explicit visibility. The Configuration is not
silently designated as governing. Governing designation, accountability, Evidence and authority,
independent Value and Risk, Integration, Decision, Intervention, Activation, Learning,
Reassessment, and Register work continue through the production typed gateway as described in
[Practitioner Pathways](PAIM_V0_1_PRACTITIONER_PATHWAYS_v0.1.md).
Do not invent a convenience command or use `tests.*`, raw SQL, fixture helpers, or direct database
writes to cross that boundary.

## 6. Keep these boundaries visible

- Authentication identifies the mapped Actor.
- `COMMAND` access permits an operation to be attempted.
- `CASE_READ` and `CONFIGURATION_READ` establish visibility of the exact governed context.
- A current applicable Role Assignment establishes accountability.
- An exact Authority or Authorization Basis establishes substantive permission for a governed act.

These layers do not substitute for one another. Inspect current grants before appending access;
append only missing exact facts. Use exact Record and Version identities for all later temporal and
historical work. On any unexpected denial or failed postcondition, stop and preserve the output,
audit evidence, database, and operator artifacts before diagnosing the cause.

## 7. Open the practitioner browser on current development `main`

Before the ordinary browser can offer **Start a Case**, establish both the software permission to
attempt Case initiation and one externally grounded organizational mandate for the mapped Actor.
Neither fact grants downstream Decision authority or substitutes for a PAIM Responsibility:

```powershell
uv run --locked paim-local --config C:\secure\paim-local.json access-grant `
  --principal principal:local-owner `
  --subject-principal principal:local-owner `
  --permission COMMAND `
  --action case.create_open `
  --scope-type GLOBAL `
  --effect ALLOW

uv run --locked paim-local --config C:\secure\paim-local.json access-grant `
  --principal principal:local-owner `
  --subject-principal principal:local-owner `
  --permission OPERATIONAL_ADMIN `
  --action case.initiation-authority.record `
  --scope-type GLOBAL `
  --effect ALLOW

uv run --locked paim-local --config C:\secure\paim-local.json case-initiation-authority-record `
  --principal principal:local-owner `
  --authorized-actor-id <returned-actor-id> `
  --organization-scope "organization:local" `
  --authoritative-source "<approved organizational mandate>" `
  --source-version "<exact source version or date>" `
  --effective-at 2026-08-21T00:00:00+00:00 `
  --idempotency-key "local-owner-case-initiation-v1"
```

The `OPERATIONAL_ADMIN / case.initiation-authority.record / GLOBAL / ALLOW` fact is required for
an existing local environment before the operator can record the organizational mandate. It is
software permission to perform that administrative operation. It does not create the mandate,
grant substantive Case-initiation authority, or grant any downstream Decision authority.

An empty `--allowed-use-prefix` set permits the mandate's exact Actor and organization scope to be
considered for any entered AI-use text. Repeat that flag only when the authoritative mandate itself
limits initiation to explicit text prefixes. The browser checks this prerequisite before presenting
a usable form and revalidates the exact mandate at commit.

For ordinary Windows use, install the PAIM desktop shortcut once from the repository root. Supply
the same external configuration used by `paim-local`:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\windows\Install-PAIM-DesktopShortcut.ps1 `
  -ConfigurationPath C:\secure\paim-local.json
```

The shortcut stores only the repository and configuration paths in the current user's local
application-data folder. It does not store a credential. Before using the shortcut, make the
credential environment variable named by the external configuration available to the Windows user
or launching process. Never put its value in the shortcut, configuration, command arguments,
repository, or diagnostic log. The launcher prevents a second instance for the same configuration,
waits for the exact intended PAIM instance to report ready, and then opens the default browser.
Launch failures are shown in plain language; support detail remains available under
`%LOCALAPPDATA%\PAIM\logs`.

For an operator-controlled fallback, the existing terminal command remains supported:

```powershell
uv run --locked paim-web --config C:\secure\paim-local.json
```

Open the loopback URL printed at startup. Sign in with the provisioned principal ID and the
credential held in the environment variable named by the external configuration. The ordinary
primary navigation is **Home**, **Cases**, and **Learn**; **Account** remains in the signed-in header.
Home shows only exact visible work that legitimately needs the signed-in practitioner
and remains quiet when no such work exists. A Case carries recognizable purpose, independent
Value and Risk positions, the current Decision, continuing review, people/responsibilities, and
History & decisions when their complete exact source basis is visible.

Learn is the curated practitioner on-ramp. It explains Cases, AI versus AI use, factual AI
characteristics and dependencies, separate Value and Risk work, Decisions, Responsibility,
authority, continuing review, history, good practices, and common questions. It does not expose
operator commands or engineering documentation in the ordinary practitioner experience.

The browser carries exact context from durable Case, Responsibility, Assignment, Work, and source
facts; it does not ask the practitioner for Record or Version IDs. Technical source provenance is
available through progressive disclosure for an authorized audit purpose. Opening a disclosure
does not grant access, accountability, or substantive authority. A stale, tampered, or no-longer-
visible task fails closed without retargeting or partial mutation.

Starting a prospective Case in the browser requires an applicable pre-Case initiation mandate and
the separately configured software access to use it. Later actions appear only from exact current
Responsibility and Assignment facts and still revalidate software access, source visibility,
accountability, and substantive authority at commit. The browser does not infer missing governance
or turn visibility into authority.

Use **Sign out** to end only your browser session while leaving PAIM running. Use **Account → Stop
PAIM** when you intend to close the local application. PAIM asks for explicit confirmation, drains
the accepted request, and shuts down the owned server and operational resources in order. To resume,
ensure the configured credential environment variable is available and use the same desktop
shortcut (or the fallback command) against the same external configuration. Sign in again; the
database and external configuration, rather than browser, launcher, or PowerShell-session state,
preserve the governed Case history.

Back up and recover the external database and configured operational directories according to the
[Local Operational Application guide](PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md). Do not treat a
browser export or copied page as a database backup, and do not place credentials in configuration,
backup, or repository files.

For the conceptual model, read the [PAIM v0.1 Conceptual Guide](../PAIM_CONCEPTUAL_GUIDE_v0.1.md).
For complete operation and recovery, use the
[Local Operational Application guide](PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md). For the three
released management sequences, use the
[Practitioner Pathways](PAIM_V0_1_PRACTITIONER_PATHWAYS_v0.1.md). For planned empirical evaluation
rather than product proof, see the [PAIM Empirical Research Agenda](../research/PAIM_EMPIRICAL_RESEARCH_AGENDA_v0.1.md).
