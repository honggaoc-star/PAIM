# PAIM v0.1 Practitioner Pathways

## 1. Purpose and boundary

This is the production-only operating guide for the three supported PAIM v0.1 practitioner
pathways:

1. Case to authorized bounded operation and Learning;
2. external occurrence to completed Reassessment; and
3. multi-Case Management Register to an exact owning-domain action.

It explains prerequisites, sequencing, exact-identity discipline, and the next owning action. It
does not change PAIM semantics, replace an organization's authority model, or turn software access
into substantive authority. The detailed local setup, intake, export, delivery, recovery, health,
and unsupported-capability rules remain in
`PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md`.

PAIM is a local governed application. On current post-v0.1 development `main`, its integrated
prospective practitioner browser uses the same production services as the typed gateway and keeps
technical/legacy surfaces outside the ordinary Home → Case → contextual Task → History journey.
The tagged v0.1.0 release boundary remains unchanged. There is deliberately no generic approve,
resolve, override, or Register “mark resolved” command.

## 2. Non-negotiable execution rules

Use these rules for every pathway and stop when any precondition is not established.

1. Run from the PAIM repository with the accepted CPython 3.12 environment:

   ```powershell
   uv --version
   uv lock --check
   uv run --locked python --version
   uv run --locked paim-local --help
   ```

2. Use `uv run --locked paim-local ...` for CLI commands and `uv run --locked python
   <production-script.py>` for typed-gateway scripts. A production script may import only `paim.*`
   and Python standard-library modules. Never import `tests.*` or a test fixture/helper.
3. Keep only the credential in an environment variable. Do not rely on PowerShell variables for
   identity or continuity between stages.
4. Persist each successful stage's downstream-required identities in a UTF-8, BOM-free JSON
   artifact. A later stage reads the configuration and that artifact afresh and verifies the
   referenced database records before acting.
5. Use exact persisted Record and Version identities. A label, title, question text,
   `question_id`, source name, “latest” query, or semantic similarity is not a substitute for an
   exact Version ID.
6. Use enum values supplied by production `paim.*` types. Do not invent capitalization or compare
   an enum's display representation when its production value is required.
7. Generate JSON with a UTF-8 encoder that emits no BOM. For exact punctuation in verification,
   compare Unicode code points or construct the expected value with `chr(...)`; do not depend on
   console encoding.
8. Inspect current access facts before appending a grant. Append only a missing exact
   principal/permission/action/scope fact. Access facts are historical evidence and must not be
   deleted or silently repeated.
9. Stop after an unexpected denial or failed postcondition. Preserve the command output, audit
   evidence, database, and stage artifact; diagnose before retrying.

## 3. Self-contained stage contract

Every substantive stage follows the same five-part contract:

1. **Read-only preflight:** read the configuration and prior result artifact; authenticate; verify
   exact referenced records, Versions, currentness, expected counts, and current access facts.
2. **Exact operations:** append only missing software access and invoke only the bounded production
   command(s) for the stage.
3. **Persist:** after the commands and semantic postconditions succeed, write one result artifact
   containing exact Record IDs, Version IDs, command/audit IDs, access context, and checksums needed
   later.
4. **Verify:** reopen the artifact and database, compare JSON arrays as arrays, and verify exact
   bindings and negative postconditions.
5. **Stop:** report the checkpoint before starting the next lifecycle boundary.

Use a stable artifact shape such as:

```json
{
  "status": "STAGE_POSTCONDITIONS_VERIFIED",
  "case_id": "<exact-record-id>",
  "configuration_id": "<exact-record-id>",
  "configuration_version_id": "<exact-version-id>",
  "source_version_ids": ["<exact-version-id>"],
  "command_id": "<exact-command-id>",
  "audit_id": "<exact-audit-id>"
}
```

Do not write the artifact before the postconditions pass. Do not repair an artifact by overwriting
it after a partial failure; preserve it and create an explicitly authorized successor artifact.

## 4. Access, accountability, and authority are separate

A command can proceed only when all applicable layers are established:

| Layer | What it establishes | What it does not establish |
|---|---|---|
| Authentication | The principal and its current mapped Actor | Command permission or substantive authority |
| `COMMAND` permission | Permission to attempt one action at an exact scope | Case/Configuration visibility, accountability, or authority |
| `CASE_READ` / `CONFIGURATION_READ` | Visibility of the exact governed context needed by the command | Permission to mutate it or authority to decide |
| Current Role Assignment | Accountable Actor for the typed target and obligation | Software permission or Decision Authority |
| Authority/Authorization Basis | Substantive permission for the exact governed act | General software access or an implicit winner among conflicts |

Before a Configuration-bound command, verify all three software-access prerequisites when they
apply:

- `COMMAND` / exact action at the required Case or Configuration scope;
- `CASE_READ` / `read` for the owning Case; and
- `CONFIGURATION_READ` / `read` for the exact Configuration.

Then verify the command's current Role Assignment and authority basis. A Case-scoped accountable
assignment may be applicable to a Configuration-bound obligation without becoming a Configuration-
scoped assignment. Zero eligible assignments is a vacancy; incompatible co-current assignments are
a conflict. Specificity, breadth, recency, role hierarchy, and software permission choose no
implicit winner.

An `AccessDenied` immediately after a successful command grant commonly means exact Case or
Configuration visibility is missing. Inspect all required layers; do not repeat the successful
grant or broaden its scope as a shortcut.

## 5. Pathway 1 — Case to authorized bounded operation and Learning

| Boundary | Required established input | Practitioner action | Successful output / next action |
|---|---|---|---|
| Identity and scope | Authenticated mapped Actor; `case.create` permission | Create the Case | Exact Case ID → establish Case read and Configuration-create access |
| Managed Configuration | Exact owning Case and finalized candidate content | Create Configuration | Exact Configuration and Version IDs → establish exact read access and governing designation |
| Accountability | Required typed Role Assignments at applicable Case/Configuration targets | Record assignments | Exactly one eligible accountable assignment per obligation → assemble Evidence and authority |
| Evidence and authority | Exact Evidence Versions, Applicability judgments, authority facts/gaps | Resolve applicability and preserve gaps/conflicts | Exact applicable Evidence and authority basis → prepare independent Value and Risk inputs |
| Value and Risk | Independent selected and frozen Value/Risk Versions | Freeze each analytical lane separately | Exact Value and Risk Version IDs → integrate without collapsing them |
| Integration and Boundary | Exact Configuration, Value, Risk, Evidence/authority basis | Commit Integration and Boundary snapshot | Exact Integration and Boundary Versions → propose Decision |
| Decision | Proposed Decision plus exact accountable/authority basis | Authorize Decision | Authorized Decision Version → define Intervention |
| Intervention | Authorized Decision and exact prerequisites | Commit Intervention, completion evidence, and accountable acceptance | Accepted completion with satisfied prerequisites → activation review |
| Activation | Exact accepted completion and activation authority | Authorize Activation | Bounded authorized operation → record Learning against exact history |
| Learning | Exact intervention/operation/Decision basis | Commit Learning | Learning record only; no automatic Decision change → Reassessment if a Trigger requires it |

At each boundary, preserve frozen-input history and the exact authorized Decision. Learning does not
amend a Decision automatically. A later Decision requires its own successor/amendment command and
authority.

## 6. Pathway 2 — External occurrence to completed Reassessment

| Boundary | Required established input | Practitioner action | Successful output / next action |
|---|---|---|---|
| External occurrence | Exact Case/Configuration visibility, `intake.external_trigger`, provenance envelope | Submit intake | `PROPOSED` intake with checksum; no Trigger or Observation → explicit promotion decision |
| Trigger | Exact proposed intake and accountable Trigger authority | Promote the exact intake | Trigger and Trigger Version IDs preserving provenance → Trigger Determination |
| Determination | Exact Trigger Version and current Trigger Determiner assignment | Record determination | Exact determination; if `REASSESSMENT_REQUIRED`, no automatic Reassessment → create it explicitly |
| Reassessment | Exact determination, Trigger Set, Decision and Configuration Versions | Establish Reassessment | Exact Reassessment Version → assess overlap/concurrency |
| Coordination | Exact current overlapping Reassessment Versions and accountable coordinator | Record grouping/coexistence/supersession/cancellation determination | Explicit coordinated state; no implicit winner → interim disposition if required |
| Interim operation | Exact affected scopes and active Reassessment Versions | Commit dispositions | Restrictive exact-scope intersection; indeterminate combined effect suspends only affected scope |
| Completion | Exact current Reassessment, reviewed basis, owner/authority assignment | Advance and confirm or create successor Decision | Completion outcome and satisfied Trigger coverage; full history retained |

Exact replay identity returns the existing intake. A similar but genuinely distinct occurrence is
not semantically deduplicated. Intake never auto-promotes to Trigger and no v0.1 Observation is
created or approximated.

When Reassessment overlap exists, evaluate the exact current Versions prospectively again after a
successor Version is created. Do not reuse a determination made against predecessor Versions.
Operating-state values are unordered identities: do not infer strongest, severity, priority,
ranking, or escalation.

## 7. Pathway 3 — Multi-Case Register to owning-domain action

| Boundary | Required established input | Practitioner action | Successful output / next action |
|---|---|---|---|
| Source population | Exact eligible source Versions and requested Case population | Derive Register | Deterministic current/conflict/informational/historical entries → inspect lifecycle state |
| Shared Dependency | Exact Candidate Set plus accountable current `EQUIVALENT` determination | Derive grouped view | Group only exact members under exact Shared Dependency → no similarity inference |
| Access filtering | Exact Case/Configuration read policy for the principal | Derive filtered view | `access_filtered=true`; protected IDs, facts, and global counts absent |
| Temporal view | Exact effective time, knowledge cutoff, and source Version identities | Reconstruct view | Exact historical view; staleness explicit against watermark |
| Output | Exact retained Register manifest and trusted access context | Export JSON/CSV; generate/deliver intent | Same manifest checksum/access context → select contextual action |
| Contextual action | Exact selected concern, source Versions, and owning family | Launch `ASSIGN_OWNER` or another supported contextual action | Return exact owning-domain command contract; no source mutation or authority transfer |

Lifecycle labels describe source state; they do not rank concerns. Shared Dependency requires exact
Candidate Set membership and an accountable `EQUIVALENT` determination. Similar text or subject
matter creates no governing relationship.

`ASSIGN_OWNER` is a contextual launch, not an assignment performed by the Register. The
practitioner must complete the returned owning-domain Role Assignment command with its normal access,
accountability, and authority checks. Generic Register resolution is unsupported.

## 8. Temporal and identity verification

For effective-time or knowledge-time reconstruction:

1. read the exact Version IDs from the prior successful artifact;
2. verify each Version's Record ID, effective interval, recorded time, status, and predecessor/
   successor relationships in persisted state;
3. derive cutoffs from those exact Versions, not from a broad semantic-key query;
4. invoke the production selection/read path with the explicit effective/known context;
5. compare the returned exact Version set with the expected persisted set; and
6. verify historical rows and semantic digests remain unchanged.

If a governed identifier such as an Authority Gap `question_id` defines scope, every successor must
retain it unless the domain contract explicitly creates a different governed question. Changing a
display or semantic key can change scope; it is not a harmless verifier convenience.

## 9. Failure and next-action checklist

When a stage stops, record the failed command and answer in order:

1. Did the locked runtime and production `paim-local` entrypoint preflight pass?
2. Was the configuration UTF-8 without a BOM, and is the credential environment variable present?
3. Do the exact Record/Version IDs in the last successful artifact still match persisted state?
4. Are `COMMAND`, exact Case read, and exact Configuration read all established where required?
5. Is exactly one eligible accountable assignment established across the applicable typed targets?
6. Is the exact substantive authority/authorization basis current and applicable?
7. Is the command using production enum values and exact predecessor/current Versions?
8. Did the command commit but a shell/verifier step fail? If so, reconstruct read-only before any
   retry; never repeat a successful append-only operation.

The answer identifies the next action: repair only procedure/runtime configuration, append only a
missing access fact, resolve an explicit accountability/authority vacancy or conflict in its owning
domain, or correct an exact command input. Do not bypass a failed guard.

## 10. v0.1 residual limitations

The current post-v0.1 development browser covers the accepted prospective Home, Cases, Case,
contextual Task, independent Value/Risk, adequacy, bounded Reliance choice, Decision,
continuing/focused review, and History & decisions experience. It is not a workflow engine or an
automatic substantive next-step engine. This guide does not add first-class Observation,
telemetry automation,
operating-state ranking, semantic dependency matching, generic Register resolution, background
scheduling, notifications, or networked multi-user deployment. These limitations remain visible
and do not authorize approximations.
