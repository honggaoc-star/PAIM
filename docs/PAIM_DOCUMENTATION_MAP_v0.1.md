# PAIM v0.1 Documentation Map

PAIM v0.1 is released under a bounded validated claim. This map routes readers to the right level
of documentation without treating development history or validation evidence as new product
semantics.

## Choose a starting point

| Reader intent | Start here | Then continue to |
|---|---|---|
| New to PAIM / conceptual understanding | [Repository README](../README.md) | [PAIM v0.1 Conceptual Guide](PAIM_CONCEPTUAL_GUIDE_v0.1.md) |
| Want to try PAIM | [PAIM v0.1 Quick Start](operations/PAIM_QUICK_START_v0.1.md) | [Local Operational Application](operations/PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md) for full operation and recovery |
| Follow the practitioner pathways | [PAIM v0.1 Practitioner Pathways](operations/PAIM_V0_1_PRACTITIONER_PATHWAYS_v0.1.md) | Validation evidence for the three pathways below |
| Operate or administer a local instance | [Local Operational Application](operations/PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md) | Runtime decisions and recovery evidence under engineering documentation if deeper rationale is needed |
| Implement or review PAIM contracts | [System Architecture](system/architecture/PAIM_SYSTEM_ARCHITECTURE_v0.1.md) | [Current system specifications](system/specifications/) and [behavioral validation strategy](system/testing/PAIM_SYSTEM_BEHAVIORAL_VALIDATION_STRATEGY_v0.1.md) |
| Plan or review the bounded practitioner browser experience | [Practitioner Experience Architecture M1](design/PAIM_PRACTITIONER_EXPERIENCE_ARCHITECTURE_M1_v0.1.md) | Current system architecture and specifications remain controlling implementation contracts |
| Review the selected M1 browser implementation architecture | [UI M1 Implementation Architecture Decision](engineering/PAIM_UI_M1_IMPLEMENTATION_ARCHITECTURE_DECISION_v0.1.md) | Practitioner Experience Architecture M1 defines the required experience; implementation remains separately gated |
| License or cite PAIM | [Apache License 2.0](../LICENSE) and [NOTICE](../NOTICE) | [`CITATION.cff`](../CITATION.cff) |
| Review validation and release evidence | [Increment 9 v0.1 Validation Results](system/testing/PAIM_INCREMENT_9_V0_1_VALIDATION_RESULTS_v0.1.md) | [v0.1 Release Gate Decision](engineering/PAIM_V0_1_RELEASE_GATE_DECISION_v0.1.md) and the frozen validation plan |
| Review or test PAIM and report findings | [Focused feedback](../FEEDBACK.md) | [v0.1 GitHub Release Notes source](release/PAIM_V0_1_GITHUB_RELEASE_NOTES.md) |
| Plan or review empirical PAIM research | [PAIM Empirical Research Agenda](research/PAIM_EMPIRICAL_RESEARCH_AGENDA_v0.1.md) | Current concepts and bounded validation evidence as sources, not empirical proof |
| Study design rationale or development history | [Engineering documentation](engineering/) | Increment decisions, readiness assessments, runtime decisions, sequencing, and practitioner-findings review |

## Practitioner and operator guidance

The three current operational guides serve different purposes:

- [PAIM v0.1 Quick Start](operations/PAIM_QUICK_START_v0.1.md) provides the shortest supported
  path from a clean checkout to a healthy local instance and first Case/Configuration context.
- [PAIM v0.1 Practitioner Pathways](operations/PAIM_V0_1_PRACTITIONER_PATHWAYS_v0.1.md)
  explains the production-only management pathways, exact prerequisites, persisted-state
  continuity, authority boundaries, and contextual next actions.
- [PAIM Local Operational Application](operations/PAIM_LOCAL_OPERATIONAL_APPLICATION_v0.1.md)
  covers local configuration, bootstrap, authentication and access, intake, exports,
  notifications, backup/restore, health, and explicit unsupported boundaries.

## Current architecture and technical contracts

Use these documents when implementing, reviewing, or testing PAIM behavior:

- [PAIM System Architecture](system/architecture/PAIM_SYSTEM_ARCHITECTURE_v0.1.md);
- [PAIM Platform Architecture](engineering/PAIM_PLATFORM_ARCHITECTURE_v0.1.md), the engineering
  implementation-architecture decision for the released platform;
- [system specifications](system/specifications/), including Case Lifecycle, Managed
  Configuration, Evidence and Authority, Value/Risk Interface, Integration and Decision,
  Intervention and Learning, Reassessment, Management Register, Roles and Accountability, and
  System Record and Decision Integrity; and
- [PAIM System Behavioral Validation Strategy](system/testing/PAIM_SYSTEM_BEHAVIORAL_VALIDATION_STRATEGY_v0.1.md).

The architecture and specifications preserve the bounded v0.1 semantics. In particular, Value and
Risk remain analytically independent; software permission does not create substantive authority;
and exact Record/Version identity, configuration binding, frozen inputs, authorized Decisions,
Authority Gaps, and Reassessment history remain explicit.

## Validation and release evidence

Use evidence documents to understand what was tested and accepted, not to invent additional
semantics:

- [Increment 9 Integrated Validation Plan](system/testing/PAIM_INCREMENT_9_V0_1_INTEGRATED_VALIDATION_PLAN_v0.1.md)
  is the frozen campaign plan.
- [Increment 9 v0.1 Validation Results](system/testing/PAIM_INCREMENT_9_V0_1_VALIDATION_RESULTS_v0.1.md)
  records automated and human pathway evidence.
- [Practitioner Findings Cross-Pathway Review](engineering/PAIM_INCREMENT_9_PRACTITIONER_FINDINGS_CROSS_PATHWAY_REVIEW_v0.1.md)
  records the bounded usability/documentation remediation and confirmation.
- [PAIM v0.1 Release Gate Decision](engineering/PAIM_V0_1_RELEASE_GATE_DECISION_v0.1.md)
  records the effective bounded release verdict.
- Other files under [system testing](system/testing/) retain implementation-readiness reviews,
  focused gate closures, test contracts, and historical validation evidence.

Testing and release evidence demonstrates conformance to defined behavior. It must not be rewritten
or interpreted as authority to expand product semantics.

## Empirical research

The [PAIM Empirical Research Agenda](research/PAIM_EMPIRICAL_RESEARCH_AGENDA_v0.1.md) identifies
revisable questions about PAIM, alternatives to it, and emergent practitioner behavior. It is a
research-planning artifact, not a product specification, literature review, experimental protocol,
or validation claim.

## Engineering decisions and development history

Files under [engineering](engineering/) record design rationale, implementation sequencing,
technology/runtime choices, readiness assessments, increment-specific decisions, practitioner
findings, and release history. They are valuable for understanding why the repository reached its
current design.

Engineering documents are historical or explanatory unless a document explicitly declares a
controlling role. When engineering history describes an earlier pending gate, branch, or PR state,
read it as evidence of that checkpoint rather than as the current product status.

## Documentation authority

- `docs/system/**` contains the current/normative technical architecture, specifications, and test
  contracts or evidence, as applicable to each document.
- `docs/operations/**` contains practitioner and local operator guidance. It explains how to use
  the released application without changing governing semantics.
- `docs/research/**` contains empirical research-planning artifacts. Research questions and
  hypotheses do not amend product semantics or constitute validation evidence.
- `docs/engineering/**` contains design rationale, implementation decisions, assessments, and
  development/release history unless a document explicitly declares a controlling role.
- Testing and release artifacts remain evidence. They do not silently amend PAIM architecture,
  specifications, authority, or product scope.

If documents appear to conflict, first distinguish current normative contracts from operational
guidance and historical evidence. Do not resolve an apparent conflict by choosing newer, broader,
more convenient, or more permissive behavior.

## Bounded release reminder

PAIM v0.1 is a local governed CLI and typed Python gateway. It does not imply a browser UI,
polished self-service workflow, first-class Observation or continuous telemetry semantics,
operating-state ranking, semantic dependency matching, generic Register resolution, live provider
integrations, or cloud/distributed/multi-tenant deployment.

IRR-009 remains `OPEN — SEMANTICS UNDESIGNED` and
`CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM`. IRR-014 remains
`OPEN — SEMANTICS UNDESIGNED` and `CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM`.
