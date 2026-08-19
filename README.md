# Practical AI Management (PAIM)

## Overview

Practical AI Management (PAIM) is a practitioner-oriented management
system for making, implementing, evaluating, and revising decisions
about the use of artificial intelligence in organizations.

PAIM addresses a practical management question:

> Given what is known about the value, risks, uncertainties,
> alternatives, and organizational context of an AI use, what should
> management do?

PAIM is intended to support continuing management of AI-enabled
activities rather than one-time approval or classification.

The project is being developed method-first. Software, including a
possible PAIM Workbench, is expected to support the management method
rather than define it.

## Purpose

PAIM integrates distinct value-management and risk-management evidence
into practical, accountable, revisable management decisions. It does not
assume that value and risk can always be reduced to a single score.

Its four broad functional capabilities are:

1.  **Value Management** --- determine what value an AI-enabled
    configuration is producing and what the evidence supports.
2.  **Risk Management** --- identify and evaluate relevant risks,
    consequences, uncertainties, and controls.
3.  **Decision Integration** --- combine value evidence, risk evidence,
    context, constraints, alternatives, and uncertainty into an
    accountable management judgment.
4.  **Management Learning** --- observe what happens after intervention
    and use new evidence to reassess prior decisions.

## Management Object

PAIM manages a bounded AI-enabled use or configuration rather than "AI"
in the abstract.

Conceptually:

\[ M = (AI, X, P, E) \]

where (AI) is the relevant AI capability or system, (X) represents
complementary inputs, (P) represents the process or use context, and (E)
represents the operating environment.

Observed outcomes should not automatically be attributed to the AI
component independently of the surrounding configuration.

## Decision Integration

Conceptually:

\[ D = g(V, R, C, A, U) \]

where (V) is value evidence, (R) is risk evidence, (C) is organizational
context and constraints, (A) is the set of available alternatives, (U)
is relevant uncertainty, and (D) is the management decision.

This notation identifies decision inputs; it does not prescribe a
universal numerical optimization function.

## PAIM Management Cycle

**Define → Establish → Assemble → Constrain → Generate Alternatives →
Compare → Decide → Intervene → Observe → Learn → Reassess**

The cycle treats management decisions as evidence-bounded judgments made
under a particular evidence state and context. Decisions may therefore
require reassessment as evidence, technology, costs, risks, workflows,
policies, or alternatives change.

## Core Principles

-   **Configuration Principle** --- manage the bounded AI-enabled
    configuration rather than AI abstractly.
-   **Evidence-Boundary Principle** --- management conclusions should
    not exceed the evidence supporting them.
-   **Missing-Evidence Principle** --- absence of evidence should not be
    converted into favorable evidence.
-   **Constraint-Before-Trade-off Principle** --- impermissible
    alternatives should be removed before comparative judgment.
-   **Alternative-Configuration Principle** --- consider realistic
    alternative configurations rather than only AI-versus-no-AI choices.
-   **Judgment Principle** --- structured evidence supports accountable
    management judgment; it does not eliminate judgment.
-   **Temporal-Decision Principle** --- decisions are made against an
    evidence state and context and may require reassessment.
-   **Learning-Intervention Principle** --- generating decision-relevant
    evidence can itself be an appropriate management intervention.

## Relationship to AIVM

AI Value Management (AIVM) provides the value-management leg of PAIM.
Its practitioner process is:

**Discover → Establish → Decide → Learn → Reassess → Rediscover**

AIVM findings become inputs to PAIM decision integration. PAIM preserves
their evidentiary boundaries rather than converting intermediate
benefits into unsupported downstream value claims.

## Relationship to AI Risk Management

Risk management provides a separate analytical leg. Value and risk are
related but are not mathematical inverses. Low risk does not imply high
value, and high value does not imply acceptable risk. Controls may also
alter value, cost, or operating characteristics.

PAIM integrates decision-relevant risk evidence without requiring a
universal risk score.

## Relationship to Governance

PAIM does not replace organizational AI governance. Governance
establishes authority, accountability, policy, mandatory controls,
escalation requirements, and organizational boundaries. PAIM operates
within those structures to manage actual AI-enabled uses.

## Method Before Software

The intended progression is:

\[ `\text{PAIM Method}`{=tex}
`\rightarrow`{=tex}`\text{PAIM Operating Model}`{=tex}
`\rightarrow`{=tex}`\text{PAIM Workbench}`{=tex} \]

Workbench requirements should be derived from a sufficiently stable
practitioner method rather than used to determine that method
prematurely.

## Current Development Status

**PAIM v0.1 scope is complete; validation and release are not complete.**

PAIM v0.1 is a complete functional local governed PAIM application for
the implemented management lifecycle. It supports authenticated local
operation, provenance-preserving manual/external intake, access
segmentation, recovery, and explicit degraded behavior. The lifecycle
includes Case and Configuration governance; Evidence and Authority;
independent Value and Risk inputs; Integration, Boundary, Decision, and
Authorization; Intervention, Activation, and Learning; explicit-event
Reassessment and restrictive interim operation; and source-traceable
Management Register outputs.

PAIM v0.1 does not provide first-class Observation persistence or
continuous telemetry automation, and it does not infer operating-state
strength, breadth, severity, ranking, priority, or escalation. Those
capabilities remain semantically undesigned post-v0.1 extensions. Their
unsupported boundaries are explicit and fail closed. The supported v0.1
paths use exact manual/external Trigger provenance and exact-state,
exact-scope restrictive intersection or affected-scope suspension.

The current estimate is **approximately 92% complete against the bounded
complete-functional-v0.1 denominator after Increment 8 and the accepted
release-scope decision**. This is a functional-completion estimate, not a
release declaration. Remaining work is principally this consistency
reconciliation, separately authorized Increment 9 integrated/practitioner
validation, and final traceability and release evidence.

The current product is a local governed application. Enterprise/cloud
deployment, live provider integrations, distributed infrastructure, and
generic workflow scope are not part of the v0.1 claim.

## Development Direction

Increment 9 remains a separate gate and has not begun. It may be
authorized only after the accepted scope-consistency package is
independently reviewed and merged and a bounded issue freezes the exact
claim, three practitioner pathways, hard boundary oracles, regression and
operational evidence, practitioner study, final traceability, and release
verdict. Passing that campaign—not scope completion alone—is required
before PAIM v0.1 may be declared released.

## Project Objective

The long-term objective is a practical system that helps organizations
answer, repeatedly and defensibly:

> **Given the evidence available now, what should we do about this
> AI-enabled use, why, what should happen next, and what would cause us
> to reconsider?**
