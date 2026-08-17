# PAIM

**Practical AI Management (PAIM)** is an integrated management system for making, implementing, observing, and revisiting decisions about bounded AI-enabled configurations.

PAIM starts from a simple proposition:

> **AI cannot be managed adequately by considering risk alone. Practical AI management requires independent evidence about both organizational value and risk, followed by explicit integration, accountable management judgment, intervention, learning, and reassessment.**

## Purpose

Organizations adopt AI because they expect it to create value. That value may take many forms: cost reduction, productivity, quality, increased capability, improved decisions, revenue contribution, innovation, or other organizational outcomes.

At the same time, AI-enabled activities can create material uncertainty, failure pathways, control dependencies, operational constraints, and other risks.

PAIM provides a structured way to manage the two together without collapsing them into a single universal score.

The central PAIM management question is:

> **Given what is known now, what should management do with this AI-enabled configuration, under what operating boundary, why, what action should follow, what should be learned, and what would cause the decision to change?**

## System Architecture

PAIM manages a **bounded AI-enabled configuration**, not an AI model in isolation.

A configuration may include the AI capability, task or activity, workflow, users and affected parties, information and data, AI authority, human authority, controls, escalation and review, provider or model, operating conditions, dependencies, and explicit exclusions.

The system-level flow is:

```text
Management Entry
      |
      v
Managed AI Configuration
      |
      v
Evidence / Authority
      |
      +--------------------+
      |                    |
      v                    v
Value Management      Risk Management
      |                    |
      +---------+----------+
                |
                v
         PAIM Integration
                |
                v
       Management Judgment
                |
                v
           Intervention
                |
                v
            Operation
                |
                v
      Observation / Learning
                |
                v
          Reassessment
                |
                +-----------> revised configuration / decision
```

PAIM is therefore a continuing management system rather than a one-time AI assessment.

## Value and Risk

Value Management and Risk Management remain analytically distinct.

Each contributes a compact PAIM-facing interface:

1. **Finding**
2. **Boundary**
3. **Uncertainty**
4. **Implication**
5. **Provenance**

The contributing conclusions are preserved independently before PAIM Decision Integration.

PAIM does not require Value and Risk to use identical internal methodologies, and it does not require them to be reduced to a common numerical scale.

## Decision Integration

PAIM Decision Integration considers the independent Value and Risk conclusions together with:

- governing constraints and authority;
- Control Dependencies;
- Accepted and Decision-Limiting Uncertainty;
- credible alternatives;
- Reinforcement;
- Conflict;
- Constraint;
- Configuration Trade-offs.

The result is an accountable **Management Judgment** and an **Integrated Operating Boundary** defining where and under what conditions the decision is supportable.

PAIM explicitly preserves human management judgment rather than replacing it with a universal approval score.

## Intervention, Learning, and Reassessment

A PAIM decision does not end the management process.

The system links decisions to:

- operational intervention;
- accountable ownership;
- controls and boundaries;
- decision-specific learning;
- observation;
- reassessment triggers;
- successor decisions where conditions change.

New evidence does not silently rewrite a historical decision. It can trigger a traceable reassessment of whether that decision remains supportable.

## Current Status

PAIM has moved beyond its initial conceptual-development stage.

The project has completed substantial work on:

- the Minimum Management Case;
- Value/Risk analytical interfaces;
- Integrated Operating Boundary;
- Control Dependency;
- uncertainty classification;
- interaction analysis;
- intervention and decision-specific learning;
- reassessment;
- practitioner playbooks and templates;
- synthetic management cases and conflict tests;
- independent execution tests;
- system architecture;
- implementation-independent system specifications;
- behavioral validation strategy.

Independent execution tests have provisionally supported PAIM across compatible Value/Risk inputs, configuration-level trade-offs, recommendation conflict, independent compact-input construction, and frozen-input Decision Integration.

The current development frontier is **platform engineering**.

Before substantial implementation, the system specification set is being reviewed for engineering readiness so that software development does not silently redefine PAIM.

Formal human practitioner validation is intentionally reserved for an integrated practitioner-facing system or prototype. This allows human testing to evaluate PAIM through observable system behavior rather than requiring testers to reconstruct the project's internal development artifacts.

## System and Platform

PAIM deliberately separates three layers:

> **Practitioner layer — how people perform PAIM**

> **System layer — what PAIM must do**

> **Platform layer — how software implements it**

The current system specifications define the implementation contract for the future platform.

Platform engineering will address software architecture, persistence, workflow, user experience, identity and permissions, reporting, audit/history, testing, and deployment.

## Repository Scope

This repository is the **PAIM engineering repository**.

It is intended to contain:

- selected authoritative system specifications used as implementation contracts;
- platform architecture;
- PAIM platform source code;
- automated tests and behavioral test fixtures;
- engineering documentation;
- development tooling.

The complete PAIM research, validation, historical evaluator packages, raw independent-test responses, and broader development archive are maintained separately from this engineering repository.

This separation keeps the software-development workspace focused while preserving the complete research and validation record elsewhere.

## Planned Repository Structure

```text
PAIM/
├── README.md
├── AGENTS.md
├── .gitignore
│
├── docs/
│   ├── system/
│   │   ├── architecture/
│   │   ├── specifications/
│   │   └── testing/
│   └── engineering/
│
├── platform/
├── tests/
└── tools/
```

The structure may evolve as platform architecture is completed.

## Engineering Principles

PAIM platform development should preserve several system invariants:

- manage bounded configurations rather than abstract AI;
- preserve analytical independence between Value and Risk;
- bind evidence and decisions to configuration versions;
- preserve historical frozen inputs and authorized decisions;
- make unresolved authority explicit;
- preserve Control Dependencies;
- keep management judgment accountable and inspectable;
- distinguish evidence-supported requirements from practitioner-designed implementation choices;
- trigger reassessment after material change rather than silently transferring prior conclusions;
- maintain traceability across configuration, evidence, analysis, decision, intervention, learning, and reassessment.

Implementation convenience should not silently redefine these management semantics.

## Validation Approach

The future platform will be tested using controlled behavioral scenarios.

Examples include:

- holding Value constant while varying Risk;
- holding Risk constant while varying Value;
- changing a control that affects both;
- introducing or resolving an authority gap;
- changing the managed configuration;
- increasing AI authority;
- changing the proposed operating state;
- removing material evidence;
- completing a Learning Item;
- triggering reassessment.

This supports black-box and metamorphic testing of PAIM's observable management behavior.

Human validation will follow once the integrated platform is sufficiently complete to provide a coherent practitioner experience.

## Related Work

PAIM builds on and interacts with related work in AI value management, AI risk management, model evaluation, hallucination/error analysis, and Return-Weighted Risk.

These efforts may provide analytical methods or evidence to PAIM, but PAIM remains a distinct management system.

In particular, PAIM is designed to consume compatible Value and Risk Management Inputs without requiring every organization to use one specific internal analytical methodology.

## Development Stage

**Current stage:** system specification complete at initial v0.1 level; platform architecture and engineering-readiness review beginning.

The next major engineering gate is to confirm that the PAIM system specifications can be translated into software without inventing missing management behavior.

After that review, platform architecture and implementation can proceed in bounded, specification-driven increments.
