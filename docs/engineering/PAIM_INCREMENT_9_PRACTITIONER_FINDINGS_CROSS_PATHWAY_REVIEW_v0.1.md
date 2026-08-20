# PAIM Increment 9 Practitioner Findings Cross-Pathway Review v0.1

## 1. Evidence basis

This review implements GitHub Issue #76. Its controlling practitioner-study evidence is draft PR
#70 at commit `ffc4882be05952ce5453e6a45db719b84fb7be57`, especially:

- `docs/system/testing/PAIM_INCREMENT_9_V0_1_VALIDATION_RESULTS_v0.1.md`;
- `docs/engineering/PAIM_V0_1_RELEASE_GATE_DECISION_v0.1.md`;
- the frozen Increment 9 validation plan at commit `90fc285`;
- retained I9-P1, I9-P2, and I9-P3 artifacts and exact practitioner statements; and
- the accepted CPython 3.12 runtime and migration evidence on `main`.

All three human pathways and automated gates are complete in PR #70. The practitioner recorded
eight findings, all classified `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT`, and observed no
release-blocking semantic or operational/security failure. This review preserves those
classifications. It does not rewrite historical failed attempts or issue a release verdict.

## 2. Original findings

| Finding | Practitioner classification | Practitioner disposition |
|---|---|---|
| I9-P1-F1 — workflow not sufficiently self-guiding | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Explain action sequence, authority prerequisites, and next steps |
| I9-P1-F2 — procedure/environment assumptions caused interruptions | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Harden runtime, PowerShell, encoding, quoting, verifier, and state guidance |
| I9-P2-F1 — tooling too fragile and shell-dependent | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Use self-contained persisted reconstruction, locked runtime, production modules/enums, stable comparisons |
| I9-P2-F2 — access prerequisites not discoverable | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Separate command permission from exact Case/Configuration visibility |
| I9-P2-F3 — outputs weak at next-action guidance | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Explain required next actions, prerequisites, and authority dependencies |
| I9-P3-F1 — Register semantics not sufficiently self-explanatory | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Explain lifecycle, exact grouping, access filtering, and contextual action |
| I9-P3-F2 — verifier used broad semantic keys | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Require exact persisted Version identity for temporal reconstruction |
| I9-P3-F3 — self-contained persisted reconstruction improved execution | `NON-BLOCKING USABILITY/DOCUMENTATION DEFECT` | Make that pattern standard and avoid ephemeral shell state |

## 3. Consolidated themes

The evidence supports four themes without erasing the eight original findings:

1. **Workflow and next-action discoverability:** I9-P1-F1, I9-P2-F3, and I9-P3-F1.
2. **Procedure fragility and ephemeral shell state:** I9-P1-F2, I9-P2-F1, and I9-P3-F3.
3. **Access-prerequisite discoverability:** I9-P2-F2.
4. **Exact persisted identity/version discipline:** I9-P3-F2.

Themes 1 and 2 recur across all pathways. Themes 3 and 4 are distinct because confusing access
layers can cause an otherwise valid command to fail, while broad identity selection can produce an
incorrect historical conclusion even when access is valid.

## 4. Root-cause distinction

The completed pathways demonstrated correct governed behavior: Value and Risk remained separate;
authority was not inferred from software permission; exact provenance, histories, and access
boundaries were preserved; Register grouping required exact governed relationships; and excluded
IRR-009/IRR-014 behavior failed closed.

The recurring causes were practitioner procedure, tooling assumptions, and documentation:

- state was carried in ephemeral PowerShell variables instead of durable artifacts;
- some scripts invoked a bare interpreter or imported test helpers;
- PowerShell version, BOM, quoting, and console encoding assumptions were unsafe;
- successful append-only grants or domain commits were followed by verifier failures;
- access guidance omitted exact Case/Configuration visibility prerequisites;
- a temporal verifier selected by broad `question_id` rather than exact Version IDs; and
- exact outputs exposed audit state but did not explain the next owning action.

No evidence supports changing domain semantics, schemas, the access resolver, authority rules, or
the CLI command model for v0.1. A generic workflow engine or inferred next-step engine would exceed
the accepted product boundary.

## 5. Per-finding disposition and traceability

| Finding | Consolidated disposition | Implemented location | Closure state |
|---|---|---|---|
| I9-P1-F1 | Document all three next-action sequences and authority boundaries | Practitioner guide §§4–7, 9 | Remediated in documentation; human confirmation pending |
| I9-P1-F2 | Standardize locked runtime, BOM-free artifacts, stable encoding, stop/reconstruct rules | Practitioner guide §§2–3, 8–9 | Remediated in documentation; human confirmation pending |
| I9-P2-F1 | Require self-contained stages, persisted reconstruction, production-only imports/enums | Practitioner guide §§2–3 | Remediated in documentation; human confirmation pending |
| I9-P2-F2 | Make command/read/accountability/authority layers explicit | Practitioner guide §4 | Remediated in documentation; human confirmation pending |
| I9-P2-F3 | Supply boundary-by-boundary prerequisites and next actions | Practitioner guide §§5–7, 9 | Remediated in documentation; human confirmation pending |
| I9-P3-F1 | Explain lifecycle, exact grouping, filtering, and contextual action | Practitioner guide §7 | Remediated in documentation; human confirmation pending |
| I9-P3-F2 | Mandate exact persisted Version selection and temporal verification | Practitioner guide §§2, 8 | Remediated in documentation; human confirmation pending |
| I9-P3-F3 | Adopt persisted artifacts as continuity authority | Practitioner guide §§2–3 | Remediated in documentation; human confirmation pending |

No original finding is declared closed by this engineering review. Closure requires the bounded
human confirmation in §9 and independent acceptance.

## 6. Remediation implemented and deferred

Implemented in this issue:

1. `docs/operations/PAIM_V0_1_PRACTITIONER_PATHWAYS_v0.1.md`, a durable production-only guide for
   all three pathways;
2. explicit `uv run --locked`, `paim.*`-only, production-enum, UTF-8/BOM, and encoding-stable rules;
3. a self-contained five-part stage contract using persisted configuration/artifacts/database;
4. an access/accountability/authority matrix and exact visibility prerequisites;
5. next-action tables for every major lifecycle boundary and Management Register contextual action;
6. exact persisted identity and temporal reconstruction rules; and
7. links from the existing operator guide and repository README.

Deferred beyond bounded v0.1 remediation:

- browser or richer interactive UI;
- generic workflow/next-step engine;
- new CLI commands solely to duplicate existing typed production commands;
- inferred remediation, authority, ranking, priority, or semantic matching;
- first-class Observation or operating-state relation design; and
- rewriting historical walkthrough transcripts.

No Python source, database migration, governing specification, or executable behavior changes.

## 7. Release-blocking assessment

The practitioner classified every finding as non-blocking and completed all three governed
objectives. Automated and human evidence found no release-blocking semantic or operational/security
failure. The defects materially affected efficiency, discoverability, and independence from expert
guidance, but corrections did not require a semantic or product-behavior change.

Documentation remediation is therefore proportionate before v0.1 release. This assessment does not
close findings or authorize release: the practitioner must confirm that the consolidated guide
actually improves the five targeted experience properties.

## 8. Regression evidence

The change set is documentation-only. Required engineering validation is:

- `git diff --check`;
- all changed-document relative paths resolve;
- all eight finding IDs occur in this review and map to a disposition;
- the three pathway headings and four consolidated themes are present;
- examples use `uv run --locked` and do not import `tests.*`;
- repository search confirms no Python, migration, or specification change; and
- Markdown structure/link inspection passes.

Executable regression, Ruff, and mypy are not required because executable behavior does not change.

## 9. Minimum human revalidation

Use one short practitioner confirmation, targeted at 10–15 minutes. Do not repeat I9-P1, I9-P2,
or I9-P3.

Preparation may reuse a safe existing study database or a disposable fixture. The facilitator
provides only:

- a configuration path;
- the credential environment-variable name and protected value source; and
- one BOM-free JSON context artifact containing exact Case, Configuration, source Record, source
  Version, and current owning-action identities.

The practitioner then uses only the new guide to:

1. run the locked-runtime/import preflight;
2. reopen the configuration and context artifact without restoring cross-stage shell variables;
3. identify the exact `COMMAND`, `CASE_READ`, and `CONFIGURATION_READ` prerequisites for the stated
   action and distinguish them from accountability and substantive authority;
4. identify which exact Version IDs, not broad semantic keys, control a supplied historical query;
5. follow the relevant pathway table to name the correct next owning action and explain what PAIM
   must not infer or mutate; and
6. run one read-only production health/reconstruction check appropriate to the fixture.

Record only the practitioner's actual actions and answers. Confirmation passes only if the
practitioner reports that the runtime invocation, access prerequisites, persisted reconstruction,
exact identity discipline, and next-action/authority guidance are clear enough to complete without
an undisclosed corrective instruction. Any failure remains evidence and is classified separately.

## 10. Residual v0.1 limitations

Even after confirmation, PAIM v0.1 remains a local CLI and typed-gateway application with
documentation-led navigation. It does not provide a polished self-service interface or automatic
workflow guidance. Operators must understand exact Record/Version identity and organizational Role/
authority prerequisites. Unsupported Observation, telemetry automation, operating-state ranking,
semantic dependency matching, and generic Register resolution remain explicit fail-closed
boundaries.

These limitations must appear in release wording. The guide reduces avoidable procedure fragility;
it does not claim to remove every usability cost identified by the practitioner.

## 11. PR #70 and release-gate implications

PR #70 remains draft and unmerged while Issue #76 is reviewed and the minimum human confirmation
is outstanding. This remediation belongs to a separate bounded branch and PR. It does not modify
PR #70 evidence, retroactively alter practitioner statements, or issue a `PAIM V0.1 RELEASED`
verdict.

After independent review and merge of this remediation, conduct only §9's bounded human
confirmation. If accepted, record the actual confirmation evidence and update PR #70 for final
independent release review. Until then, all eight findings remain open and the release decision
remains pending.
