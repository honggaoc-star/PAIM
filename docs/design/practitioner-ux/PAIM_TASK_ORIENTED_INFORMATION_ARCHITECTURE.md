# PAIM Task-Oriented Information Architecture

## Design intent

The information architecture follows practitioner goals while retaining separate domain semantics.
It does not assume the current capability-shaped tabs must remain, and it does not collapse records
merely to reduce page count.

## Application-level navigation

```text
Home
Cases
Administration
Help
```

- **Home** identifies visible Cases needing understandable action without scoring or hidden counts.
- **Cases** supports discovery and entry using concise titles and current management position.
- **Administration** separates identity, software access, role/accountability, substantive authority
  sources, and local health. It is not the ordinary path for Case work.
- **Help** provides short concept explanations and a practitioner glossary, not a prerequisite course.

Future Reassessment and Management Register areas remain outside this Scenario-A design.

## Case workspace navigation

```text
Overview
Proposal setup
What we know
Value
Risk
Management judgment
Action and authorization
History
```

### Overview

Answers: What is this Case, what is being considered, where does it stand, and what is the earliest
meaningful next action?

### Proposal setup

Compares current process and proposed setup in concrete terms. Configuration creation/versioning and
governing designation operate underneath, with governance trace available.

### What we know

Combines task-oriented views of available evidence, missing/unknown evidence, requirements, authority,
and explicit relevance judgments. It does not merge their records or infer relationships.

### Value and Risk

Equal-status destinations with separate full-width working surfaces and independent saved state.
Each orchestrates assessment, support/Fitness, and explicit management Selection.

### Management judgment

Relates the two selected assessments and defines operating limits. Integration and Boundary remain
separate review/commit checkpoints.

### Action and authorization

Creates a proposal and, in a separate authorized session/action, records authorization. The page
must keep “proposed,” “authorized,” and “operating” states distinct.

### History

Reconstructs the Case across effective and knowledge time. It includes non-selected, superseded,
withdrawn, conflicted, and prior material without turning ordinary work into a history browser.

## Three-layer disclosure model

| Layer | Audience and task | Content | Interaction |
|---|---|---|---|
| Management workspace | Practitioner completing current work | Plain-language proposal, facts, unknowns, assessments, limits, decisions, and next actions | Primary pages and focused task flows |
| Source/history/governance trace | Practitioner, reviewer, governance or audit user asking “why?” | Sources, limitations, explicit Applicability, prior versions, accountability, authority, effective/known context | Side panel or dedicated detail route; stable return to task |
| Technical/audit/diagnostic inspection | Engineer, advanced auditor, support user troubleshooting identity or machine state | Full Record/Version IDs, raw payload, internal statuses, timestamps, relationships, command/audit references | Separate inspection route; copy/download where authorized; never inline page expansion |

Governance/audit information is not hidden; it is located where its meaning can be understood.

## Context behavior

### Carry forward

Carry Case, current proposed Configuration, Actor, assessment purpose/use context, source choices,
explicit Applicability, and prior checkpoint identities. Show them in review summaries rather than
editable hidden assumptions.

### Ask again

Ask when there is a real choice among eligible current records, when the practitioner changes scope,
or when a stale/conflict condition prevents safe reuse.

### Fail closed

At review and commit, revalidate exact current identity/version, visible context, accountability, and
authority. A stale surface returns the practitioner to a comparison of what changed; it never rebases
silently.

## Attention and routing

Attention items use management tasks:

- Review missing or unresolved information.
- Complete the Value assessment.
- Complete the Risk assessment.
- Confirm whether an assessment is sufficiently supported.
- Choose the assessment management will use.
- Record the management judgment.
- Define operating limits.
- Submit or review the proposal.

Ordering is pathway order, not priority or severity. Show only the earliest unmet task by default;
“See later steps” may explain the rest without repeating every dependency on every page.

## Help and glossary

Help is contextual:

- one-sentence explanations adjacent to the first meaningful use of a concept;
- examples drawn only from the current Case context;
- a provisional glossary grouped by practitioner task; and
- links to governance trace for formal meaning.

The glossary must not compensate for schema-led forms or internal labels.

## Responsive and non-disruptive detail

- Full-width substantive work avoids half-width form compression.
- Comparison summaries may use balanced columns where space permits.
- Detail panels preserve scroll position and unsaved work.
- Long payloads use a separate technical view with wrapping, copy controls, and a return link.
- Opening and closing detail never changes authoritative state.

## Accessibility and language checks

- Status is expressed in text, not color alone.
- Buttons name the practitioner outcome, not the command.
- Every unavailable action has a concise reason and next legitimate step.
- Confirmation distinguishes what will be established from what remains unestablished.
- Focus returns to the task result or first actionable error.
- Labels remain accurate without relying on tooltips or glossary lookup.
