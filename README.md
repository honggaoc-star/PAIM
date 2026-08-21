# Practical AI Management (PAIM)

**PAIM v0.1 is released under the bounded validated claim.**

Practical AI Management (PAIM) is a practitioner-oriented management system for making,
implementing, evaluating, and revising decisions about organizational uses of artificial
intelligence. The released v0.1 application is a local governed CLI and typed Python gateway.

PAIM addresses a recurring management question:

> Given the evidence available now, what should we do about this AI-enabled use, why, what should
> happen next, and what would cause us to reconsider?

PAIM is designed for continuing management rather than one-time approval, classification, or a
universal AI score.

## What PAIM manages

PAIM manages a bounded AI-enabled configuration: the AI capability together with its complementary
inputs, process or use context, and operating environment. Outcomes are not automatically
attributed to the AI component independently of that configuration.

The method keeps Value and Risk analytically independent. It brings their evidence together with
organizational context, constraints, alternatives, uncertainty, and accountable authority to
support a revisable management Decision. Missing evidence is not favorable evidence, software
permission is not substantive authority, and presentation does not create priority or governing
meaning.

## The management cycle

**Define → Establish → Assemble → Constrain → Generate Alternatives → Compare → Decide →
Intervene → Observe → Learn → Reassess**

This is a management cycle, not a claim that v0.1 implements first-class Observation records or
continuous telemetry. In v0.1, reassessment begins through exact supported manual or external-event
provenance and an explicit owning-domain Trigger action.

The released application was validated through three practitioner pathways:

1. **Case to authorized bounded operation and Learning** — establish the governed Case and
   Configuration, preserve independent Value/Risk inputs, authorize a Decision, satisfy
   Intervention and Activation prerequisites, operate, and retain Learning without silently
   changing the Decision.
2. **External occurrence to completed Reassessment** — preserve intake provenance, explicitly
   promote a Trigger, determine and coordinate Reassessment, apply restrictive interim operation,
   and complete through accountable confirmation without losing history.
3. **Multi-Case Management Register to owning-domain action** — derive source-traceable Register
   views, preserve access filtering and exact Shared Dependency identity, and return contextual
   actions to the authoritative owning domain without transferring authority or closing concerns.

The detailed production sequence is in the
[PAIM v0.1 Practitioner Pathways](docs/operations/PAIM_V0_1_PRACTITIONER_PATHWAYS_v0.1.md).

## What released v0.1 supports

PAIM v0.1 provides:

- authenticated local operation with explicit software-access checks;
- Case, Managed Configuration, lifecycle, and typed Role/accountability records;
- Evidence, Authority, Authority Gap, and exact Applicability history;
- independent Value and Risk intake, selection, acceptance, freeze, and reconstruction;
- Integration, Boundary, Decision, and exact Authorization Basis;
- Intervention, Completion Acceptance, Activation Authorization, and Learning;
- exact Trigger/Reassessment identity, coverage, concurrency, coordination, completion, and
  restrictive Interim Operating Disposition;
- source-traceable Management Register derivation, filtered outputs, exports, notification intent,
  and contextual owning-domain actions;
- SQLite persistence, immutable history, dual-time reconstruction, audit, backup/restore, health,
  and explicit degraded behavior.

## Try or operate PAIM

PAIM v0.1 supports CPython `>=3.12,<3.13`; CPython `3.12.13` is the exact reproducible reference
interpreter. Dependencies are locked in `uv.lock`, and the accepted `uv` version is pinned in
`pyproject.toml`.

From the repository root, the baseline environment commands are:

```powershell
uv sync --locked
uv run --locked paim-local --help
```

The interpreter and its native components must be permitted by local Application Control or
security policy. For configuration, bootstrap, administration, intake, export, recovery, and
health, use the
[Local Operational Application guide](docs/operations/PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md).
A shorter Quick Start is planned for documentation Pass B.

## Documentation

Start with the [PAIM Documentation Map](docs/PAIM_DOCUMENTATION_MAP_v0.1.md), which distinguishes
reader guidance, current technical contracts, validation evidence, and engineering history.

| Reader intent | Start here |
|---|---|
| New to PAIM | This README; a fuller Conceptual Guide is planned for Pass B |
| Want to try it | [Local Operational Application](docs/operations/PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md); a concise Quick Start is planned for Pass B |
| Follow practitioner workflows | [PAIM v0.1 Practitioner Pathways](docs/operations/PAIM_V0_1_PRACTITIONER_PATHWAYS_v0.1.md) |
| Operate or administer locally | [Local Operational Application](docs/operations/PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md) |
| Implement or review contracts | [System Architecture](docs/system/architecture/PAIM_SYSTEM_ARCHITECTURE_v0.1.md) and [system specifications](docs/system/specifications/) |
| Review validation and release evidence | [Increment 9 Validation Results](docs/system/testing/PAIM_INCREMENT_9_V0_1_VALIDATION_RESULTS_v0.1.md) and [v0.1 Release Gate Decision](docs/engineering/PAIM_V0_1_RELEASE_GATE_DECISION_v0.1.md) |
| Study design and development rationale | [Engineering documentation](docs/engineering/) |

## Method before software

PAIM was developed method-first: management semantics and observable practitioner behavior were
defined before platform implementation. The released application implements the bounded management
model; software remains subordinate to the governing PAIM architecture and specifications. Future
software convenience must not silently change PAIM meaning.

Core principles include managing the whole bounded Configuration, keeping conclusions within their
Evidence boundary, preserving missing evidence and uncertainty, applying constraints before
trade-offs, considering realistic alternatives, retaining accountable judgment, binding Decisions
to their evidence and context in time, and using Learning to support—but not automatically replace—
future management Decisions.

AI Value Management (AIVM) is an upstream analytical capability that can provide the Value leg of
PAIM. Risk is a separate analytical leg. PAIM operates within organizational governance; it does not
replace organizational authority, accountability, policy, or mandatory controls.

## Bounded v0.1 exclusions

The release does **not** imply or provide:

- a browser UI or polished self-service workflow;
- first-class Observation persistence or continuous telemetry automation;
- operating-state strength, breadth, ranking, priority, or state-derived escalation;
- semantic dependency matching or generic Management Register resolution;
- cloud, distributed, multi-tenant, or enterprise production deployment;
- live provider integrations; or
- any other post-v0.1 capability.

IRR-009 remains `OPEN — SEMANTICS UNDESIGNED` and
`CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM`. IRR-014 remains
`OPEN — SEMANTICS UNDESIGNED` and `CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM`. Their unsupported
behaviors remain explicit and fail closed; the v0.1 release does not design either semantic family.

## Release evidence

The bounded claim, automated validation, three human practitioner pathways, usability remediation,
and final release decision are recorded in:

- [Increment 9 v0.1 Validation Results](docs/system/testing/PAIM_INCREMENT_9_V0_1_VALIDATION_RESULTS_v0.1.md);
- [Practitioner Findings Cross-Pathway Review](docs/engineering/PAIM_INCREMENT_9_PRACTITIONER_FINDINGS_CROSS_PATHWAY_REVIEW_v0.1.md); and
- [PAIM v0.1 Release Gate Decision](docs/engineering/PAIM_V0_1_RELEASE_GATE_DECISION_v0.1.md).

The effective release checkpoint is merge commit
`b5e68ee3387571ca1db027099aa44272f03f06d5`.
