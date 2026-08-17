# PAIM Management Register Specification v0.1

## Status

Implementation-independent system specification for the **PAIM Management Register and Portfolio View**.

This specification derives from the PAIM system architecture and the completed single-case specifications for lifecycle, configuration, evidence/authority, Value/Risk interfaces, integration/decision, intervention/learning, and reassessment.

It defines how management should see and manage multiple AI configurations and PAIM cases together.

It does not prescribe dashboards, database technology, visualization libraries, reporting software, or UI layout.

## 1. Purpose

Individual PAIM cases support individual management judgments.

The Management Register provides the organizational view across those cases.

It must help management answer:

> **What AI-enabled configurations are currently operating or proposed?**

> **What has management authorized for each one?**

> **Which configurations require attention now?**

> **Where are authority, evidence, control, intervention, or reassessment gaps accumulating?**

> **Where do multiple cases share dependencies such as providers, models, controls, reviewers, or capacity?**

The register is not merely an AI inventory. It is an active management view.

## 2. Register Principle

Conceptually:

```text
PAIM Case 001 ----+
PAIM Case 002 ----+
PAIM Case 003 ----+----> PAIM Management Register
PAIM Case 004 ----+              |
...                |              v
                                 Management Attention
                                 Portfolio Decisions
                                 Prioritization
                                 Reassessment
```

The register summarizes authoritative case records without replacing them.

## 3. Register Unit

The primary register unit should normally be the **managed AI configuration under a current PAIM decision**.

A single case may contain multiple historical configuration versions and decisions, but the register should make the current management position clear.

Where multiple configurations are simultaneously active under one case, each may require a distinct register entry.

## 4. Register Entry Identity

Minimum identity fields:

- Register Entry ID
- Case ID
- current Configuration ID/version
- configuration title
- business/process area
- case owner
- decision authority
- current Decision ID/version
- current status
- last material update
- next required management action where applicable

## 5. Current Management Position

Each active entry should make visible:

- case lifecycle state;
- configuration status;
- AI operating state;
- current Integrated Operating Boundary;
- decision date;
- decision authority;
- current intervention status;
- reassessment status.

These states must not be collapsed into one generic traffic-light status.

## 6. Operating State View

The register should support visibility across operating states such as:

- experiment;
- bounded continuation;
- targeted scale;
- institutionalized use;
- broader deployment;
- controlled transition/redesign;
- suspended;
- discontinued.

Organizations may define additional states, but their meaning should remain explicit.

## 7. Boundary View

Management should be able to identify:

- what is currently authorized;
- major exclusions;
- required controls;
- capacity/operating conditions;
- material boundary changes;
- boundary breaches.

The register need not reproduce the full Integrated Operating Boundary in every row, but it should provide a concise summary and access to the authoritative boundary.

## 8. Value Position

The register may summarize the current Value position using fields such as:

- Value Input status;
- Value implication;
- Value Boundary;
- realized vs. expected value where relevant;
- material Value uncertainty;
- refresh-required status.

The register should not reduce Value to a single score unless a domain-specific measure is separately justified.

## 9. Risk Position

The register may summarize:

- Risk Input status;
- Risk implication;
- Risk Boundary;
- material residual pathways;
- required controls;
- material Risk uncertainty;
- refresh-required status.

The register should not reduce Risk to one generic score as the sole management representation.

## 10. Authority View

The register should make visible:

- established material authority;
- `AUTHORITY UNRESOLVED`;
- decision affected;
- authority owner;
- resolution status;
- whether the current bounded decision may proceed.

Unresolved authority requiring management attention should be discoverable across the portfolio.

## 11. Uncertainty View

The register should distinguish:

### Accepted Uncertainty

Unknowns compatible with current operation.

### Decision-Limiting Uncertainty

Unknowns blocking a stronger, broader, or different decision.

Management should be able to identify configurations with material Decision-Limiting Uncertainty and the decisions currently blocked.

## 12. Intervention View

The register should surface:

- interventions required;
- owner;
- status;
- blocked interventions;
- failed interventions;
- overdue interventions;
- target configuration;
- operational consequence of non-completion.

A decision should not appear fully implemented merely because it has been authorized.

## 13. Learning View

Management should be able to see:

- active Learning Items;
- decision/uncertainty addressed;
- owner;
- status;
- evidence-generation progress;
- decisions potentially unlocked;
- inconclusive/overdue learning.

This supports management of evidence generation rather than generic monitoring.

## 14. Reassessment View

The register should identify:

- reassessment due;
- trigger;
- date;
- interim operating disposition;
- analytical refresh required;
- decision pending;
- overdue reassessment;
- completed reassessment awaiting intervention.

The register should support a management reassessment queue.

## 15. Boundary Breach View

Material boundary breaches should be visible across the portfolio.

Minimum summary:

- configuration;
- breach;
- date;
- affected decision/boundary;
- immediate disposition;
- intervention;
- reassessment status.

Boundary breaches should not be hidden inside case notes.

## 16. Evidence Status View

The register may summarize:

- current Value/Risk input status;
- evidence refresh required;
- stale evidence;
- conflicting evidence;
- major learning evidence pending;
- configuration/evidence mismatch.

This is an evidence-management view, not a universal evidence-quality score.

## 17. Provider / Model Dependency View

Where provider/model dependency is material, the register should support cross-case identification of:

- shared provider;
- shared model/service;
- affected configurations;
- material dependency;
- current incidents/changes;
- reassessment exposure.

This allows management to see concentration that individual cases may not reveal.

## 18. Shared Control Dependency View

Multiple configurations may depend on the same:

- review team;
- specialist capacity;
- reference source;
- external provider;
- escalation function;
- human adjudication process;
- monitoring capability.

The register should eventually support identification of shared control dependencies where operationally useful.

## 19. Capacity View

Where capacity is part of a supported boundary, management should be able to identify:

- configurations dependent on constrained human capacity;
- current capacity condition;
- competing demand;
- cases near or beyond supported capacity;
- reassessment exposure.

This is particularly important where a control remains effective only within a bounded workload.

## 20. Management Attention

The register should support explicit management-attention conditions.

Examples:

- unresolved authority blocking current or proposed action;
- Decision-Limiting Uncertainty;
- required intervention blocked/failed/overdue;
- reassessment due;
- boundary breach;
- configuration changed without completed review;
- Value/Risk input refresh required;
- required control unavailable;
- provider/model change affecting multiple cases;
- proposed stronger operating state;
- case with no decision authority.

The exact prioritization method is deferred.

## 21. No Universal Portfolio Score

The Management Register should not require one aggregate AI risk/value score.

Management may use counts, financial measures, domain-specific metrics, or prioritization indicators.

However, the register must preserve the underlying management reasons for attention.

A high-level indicator should never replace the authoritative case record.

## 22. Portfolio Filters

A future platform should be able to filter or group entries by dimensions such as:

- business/process area;
- case owner;
- decision authority;
- operating state;
- lifecycle state;
- provider/model;
- unresolved authority;
- Decision-Limiting Uncertainty;
- reassessment due;
- intervention status;
- boundary breach;
- Value/Risk refresh status.

This is a system requirement for discoverability, not a prescribed UI.

## 23. Portfolio History

The register should support historical questions such as:

- How many configurations moved from experiment to continuation?
- Which configurations were suspended or discontinued?
- What decisions changed after reassessment?
- Which authority gaps recur?
- Which controls repeatedly become bottlenecks?
- Where did Value fail to persist?
- Which provider/model changes affected multiple cases?

Historical portfolio analysis should derive from preserved case records rather than rewritten summaries.

## 24. Management Register Entry

Minimum content:

### Identity
- Register Entry ID
- Case ID
- Configuration ID/version
- title/business area
- owner
- decision authority

### Current position
- case lifecycle state
- configuration status
- operating state
- Decision ID/version/date
- boundary summary

### Analytical status
- Value Input status/implication
- Risk Input status/implication
- evidence refresh status

### Management attention
- unresolved authority
- Accepted Uncertainty summary
- Decision-Limiting Uncertainty
- intervention status
- learning status
- reassessment status
- boundary breach
- next management action

### Dependencies
- provider/model
- material shared controls/capacity where relevant

## 25. Register Source of Truth

The register is a **derived management view**.

Authoritative detail remains in:

- Managed Configuration Record;
- Value/Risk Inputs;
- Authority Records/Gaps;
- Integration Record;
- Management Decision Record;
- Intervention Record;
- Learning Items;
- Reassessment Record.

The register must not become an independent competing source of truth.

## 26. Update Behavior

A register entry should reflect authoritative changes when:

- configuration changes;
- new decision is authorized;
- intervention status changes;
- authority resolves/changes;
- uncertainty changes;
- learning completes;
- reassessment is triggered/completed;
- boundary breach occurs;
- case closes/supersedes.

Detailed technical synchronization is deferred to platform architecture.

## 27. Closed / Historical Cases

Closed or superseded cases should remain discoverable but distinguishable from active management entries.

The default management view may focus on active configurations, while history remains accessible.

## 28. Multi-Configuration Cases

If one PAIM case governs multiple simultaneously active configurations, the register should avoid hiding material differences.

Possible approach:

```text
Case C1
  |
  +-- Configuration A — bounded continuation
  +-- Configuration B — experiment
```

Each active configuration may have its own entry linked to the common case.

## 29. Portfolio-Level Management Action

The register may reveal issues requiring action above any single case.

Examples:

- shared review capacity overloaded;
- one provider change affects many configurations;
- repeated authority gaps;
- common control weakness;
- systemic boundary drift;
- concentration in one model/provider.

A portfolio-level issue may create:

- new PAIM case;
- cross-case intervention;
- policy/authority review;
- system-level reassessment program.

Detailed portfolio governance is deferred.

## 30. Relationship to Organizational AI Inventory

An organization may already maintain an AI inventory.

PAIM Management Register is not necessarily a replacement.

Possible relationship:

```text
AI Inventory
   |
   +--> identifies AI systems/use cases
             |
             v
      PAIM-managed configurations
             |
             v
      Management Register
```

The platform may later integrate with an external inventory.

## 31. Relationship to Risk Register

PAIM is not simply a risk register.

A PAIM entry includes:

- Value;
- Risk;
- operating boundary;
- decision;
- intervention;
- learning;
- reassessment.

Risk-register integration may be useful but should not collapse PAIM into risk-only governance.

## 32. Relationship to Value Portfolio

Likewise, PAIM should not become a benefits-tracking dashboard only.

Value is one contributing management leg.

The register should preserve Value and Risk as distinct but integrated dimensions.

## 33. Management Reporting

Minimum future reports may include:

### Active PAIM portfolio

Current configurations and operating states.

### Management attention report

Items requiring decision/intervention/reassessment.

### Authority-gap report

Unresolved authority across configurations.

### Reassessment report

Due/overdue reassessments and triggers.

### Intervention report

Incomplete/failed/blocked interventions.

### Learning report

Decision-specific evidence generation.

### Historical decision report

Decision changes over time.

Exact formats are deferred.

## 34. Register Integrity Checks

The system should surface:

- active configuration with no current decision;
- current decision linked to superseded configuration;
- case marked operating while required intervention incomplete;
- unresolved authority omitted from register;
- Decision-Limiting Uncertainty omitted;
- reassessment due but not surfaced;
- boundary breach not reflected;
- closed case shown as active;
- register summary inconsistent with authoritative decision;
- provider/model change affecting multiple entries but not linked where known.

## 35. Human Judgment Points

Human/accountable judgment remains necessary for:

- determining what requires management attention;
- prioritizing competing cases;
- interpreting concentration/dependency;
- deciding portfolio-level action;
- allocating review/capacity;
- determining whether recurring issues warrant policy/system change.

The register should inform management rather than automate executive judgment.

## 36. Platform Implications

A future platform will likely require:

- management dashboard/register;
- filters/search;
- attention queue;
- drill-down to case/configuration;
- reassessment queue;
- intervention queue;
- authority-gap view;
- dependency/concentration view;
- historical reporting;
- portfolio exports.

This specification does not prescribe visual layout.

## 37. Behavioral Test Candidates

Future tests should include:

1. New decision updates current operating state in register.
2. Reassessment becomes due and appears in attention queue.
3. Authority gap resolves and register updates without deleting history.
4. Intervention fails and management attention is raised.
5. Boundary breach appears across portfolio.
6. Shared provider changes and all affected configurations become discoverable.
7. Closed case leaves active view but remains historically accessible.
8. One case has two active configurations with different states.
9. Register summary conflicts with authoritative decision; integrity check detects it.
10. Capacity dependency affects several cases and becomes visible as a cross-case issue.

## 38. Open Questions

Deferred to later system/platform work:

- exact management-attention prioritization;
- portfolio hierarchy;
- business-unit structure;
- AI-inventory integration;
- risk-register integration;
- value-portfolio integration;
- provider/model normalization;
- portfolio analytics;
- reporting cadence;
- cross-case intervention objects;
- organization-wide policy escalation.

## 39. Completion Impact

This specification adds the first formal cross-case management layer to PAIM.

The system now has specifications for:

- single-case lifecycle;
- configuration;
- evidence/authority;
- Value/Risk inputs;
- integration/decision;
- intervention/learning;
- reassessment;
- portfolio/register view.

The principal remaining implementation-independent system specifications are:

- Roles and Accountability;
- System Behavioral Validation Strategy.

## 40. Next Specification

Create:

`PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md`

It should define:

- case owner;
- Value evaluator;
- Risk evaluator;
- decision authority;
- intervention owner;
- evidence/authority owner;
- reviewer/auditor;
- system administrator;
- separation-of-role principles;
- delegated authority;
- accountability relationships;
- role conflicts;
- platform permission implications.

## 41. Repository Placement

```text
400. Practical AI Management/
└── system/
    └── specifications/
        ├── PAIM_CASE_LIFECYCLE_SPEC_v0.1.md
        ├── PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md
        ├── PAIM_EVIDENCE_AND_AUTHORITY_SPEC_v0.1.md
        ├── PAIM_VALUE_RISK_INTERFACE_SPEC_v0.1.md
        ├── PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md
        ├── PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md
        ├── PAIM_REASSESSMENT_SPEC_v0.1.md
        └── PAIM_MANAGEMENT_REGISTER_SPEC_v0.1.md
```

## 42. Conclusion

The PAIM Management Register turns a collection of individual management cases into an organizational AI-management capability.

Its central principle is:

> **The register should show management where attention is required without collapsing the underlying Value, Risk, authority, boundary, decision, intervention, and learning records into a single score.**

This provides the portfolio layer needed for a practical PAIM platform.
