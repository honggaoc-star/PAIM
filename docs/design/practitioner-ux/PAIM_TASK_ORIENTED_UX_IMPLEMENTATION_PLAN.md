# Task-Oriented UX Semantic Review and Implementation Plan

## Status

This is the bounded implementation sequence. UX-1 is implemented as a read-only orientation and
vocabulary shell, and UX-2 is implemented as the task-oriented `What we know` workspace. Every
later increment still requires its own issue, branch, tests, practitioner review, and independent
semantic acceptance. M1D remains out of scope.

Issue #115 establishes the durable
[practitioner-language standard](PAIM_PRACTITIONER_LANGUAGE_STANDARD.md). UX-3 and every later
practitioner-facing increment must apply its audience layers, vocabulary treatment, safeguard rules,
reference-content guidance, and PR checklist. The standard improves communication; it does not
authorize a workflow or semantic change.

## Questions requiring semantic or domain review

The interaction design must not answer these by convenience:

1. **Case naming:** The current production Case contract persists one title and not a separate
   durable management question. UX-1 may use a concise persisted title and a clearly
   non-authoritative derived summary; a durable second field requires separately authorized domain
   work.
2. **Configuration labels:** Governing currentness, maturity/history, purpose, authorization, and
   operating state are separate. “Proposed setup used for assessment” is permitted only as a
   truthful read label and cannot imply authorization or operation.
3. **C0 comparison:** Comparison-baseline wording is presentation over visible C0 content, not a new
   Configuration purpose or relationship. It becomes “current operating process” only when that
   operating context is separately established.
4. **Missing evidence:** Which absences belong only in UI/read composition, which may be explicit
   unknown Evidence, and which qualify as Authority Gaps? No generic “gap” record should be invented.
5. **Evidence presentation:** What explicit relationships may support contextual grouping without
   implying Applicability? Neutral source grouping must be distinguished from recommendation.
6. **Accountability entry:** Existing browser forms accept free-text accountable mechanisms. When may
   the UI resolve an established mechanism/assignment, and when must the practitioner supply or route
   to a governance action?
7. **Assessment orchestration:** Can one interaction intent safely span the existing Input, readiness,
   Fitness, and Selection checkpoints without creating new authoritative draft semantics?
8. **Fitness wording:** Does “sufficiently supported for this proposed use” cover the full production
   Fitness contract, including material Evidence basis and decision-limiting treatment?
9. **Single eligible Selection:** Must explicit Selection always remain a separate confirmation when
   exactly one supportable Input exists? This design says yes unless the governing contract is changed.
10. **Boundary prefill:** Which Configuration conditions may be presented as proposed operating-limit
    inputs without implying they are already Boundary clauses?
11. **Authority binding:** May the adapter pre-bind one uniquely resolved eligible assignment/source,
    or must the current domain service expose a dedicated resolver contract for browser use?
12. **Lifecycle orientation:** Which deterministic read composition separately identifies unique
    required prerequisites, unranked available work, and unresolved conditions without a new
    workflow status?
13. **Technical inspection authorization:** Which users may inspect raw payloads and audit references,
    and how is access enforced without leaking hidden context?
14. **Temporal editing:** What is the practitioner interaction when effective-time and knowledge-time
    reconstruction reveals a newer Version during a multi-checkpoint task?

Any question that requires a new domain concept, status, relationship, or persistence field must stop
the UI increment and return to semantic design authority.

## Proposed bounded implementation sequence

### UX-1 — Read-only orientation and vocabulary shell

Implementation status: implemented by Issue #111. The Case Overview now uses the persisted Case
title, distinguishes unranked available work from unresolved conditions, and separates
Configuration assessment basis from authorization and operation. The
workspace navigation uses practitioner task language, while Source & history provides readable
governance trace. Raw identifiers and payloads are omitted from the browser because a separately
enforceable Technical inspection permission does not yet exist; authorized production CLI and audit
paths remain available.

Passive Case orientation does not infer an intended downstream action. A lone unfinished Value or
Risk lane therefore remains available work; it becomes a required prerequisite only in the context
of a separately established attempt to perform an action that requires both lane selections.

Scope:

- concise, Configuration-stable Case title using the existing persisted title contract;
- current-process/proposed-setup comparison;
- plain-language current position with separate prerequisites, available work, and unresolved
  conditions;
- non-disruptive source/history and technical-inspection shells; and
- no new write behavior.

Gate: read composition is deterministic, access-filtered, non-ranking, does not fabricate a durable
management question, and does not misstate governing currentness, authorization, or operation.

This increment does not redesign Evidence/Authority tasks, Value/Risk analytical checkpoints,
Integration/Boundary work, Decision proposal or authorization, or any later lifecycle surface. It
adds no persisted task, attention, ranking, priority, readiness, authorization, or operating state.

### UX-2 — Task-oriented “What we know” surface

Implementation status: implemented by Issue #113. The read composition groups Evidence as
explicitly unavailable only when governed content carries all three deterministic facts:
`classification = unknown`, `unknown = true`, and `not_a_positive_finding = true`. An unknown
classification without that complete basis remains neutral recorded information, and repository
silence creates no missing-information item. This intentionally narrow rule avoids free-text
classification and records the present model limitation for later semantic review.

The browser presents available information, explicitly unavailable information,
requirements/authority sources, and unresolved Applicability/Authority questions as separate
practitioner tasks. Contextual labels invoke the unchanged Evidence, Authority, Authority Gap, and
Applicability review/commit paths. Display creates no Applicability, Value/Risk relevance,
accountability, authority, or Decision support. Ordinary cards omit technical identities and raw
payloads; access-filtered read composition remains controlling.

Scope:

- separate available information, missing/unknown information, and requirements/authority;
- contextual source and limitations view;
- existing Evidence/Authority/Authority Gap creation translated into task language; and
- explicit Applicability review with carried context.

Gate: no inferred Applicability, no conversion of absence into favorable Evidence, and exact current
target revalidation at commit.

UX-2 does not redesign Value/Risk analysis, Fitness, Selection, Integration, management judgment,
Boundary/operating limits, proposal, authorization, or the broader Source & history narrative. It
does not implement UX-3+, M1D, or a new missing-information status.

### UX-3 — Independent Value and Risk work surfaces

Implementation status: implemented by Issue #117. The browser derives presentation stages from
authoritative Input status events and exact Input-to-Applicability, Fitness, and Acceptance/Selection
relations. Those stages are not persisted workflow state. Compact peer summaries preserve parity;
substantive lane work uses full-width forms and lets Value and Risk progress independently.

The interaction leads with the analytical and management questions and introduces formal
Applicability, Fitness, Acceptance/Selection, accountability, and identity detail only where each
becomes consequential. The Issue #115 practitioner-language standard remains governing editorial
guidance.

Scope:

- separate full-width lane workflows;
- natural-language analytical prompts;
- contextual source material limited to explicit visible relationships;
- four explicit checkpoints for Input development, readiness, Fitness, and Selection; and
- persisted interaction intents that are not authoritative records.

Gate: lane independence, non-favorable outcomes, stale/tampered context, material evidence basis, and
non-selected history have hard-oracle tests; practitioner copy passes the Issue #115 language
standard without concealing any formal checkpoint or semantic boundary.

UX-3 does not redesign `What we know` beyond contextual reuse, Integration or management judgment,
Boundary/operating limits, proposal or authorization, the global Source & history narrative,
reference-case fixture content, or M1D. It adds no universal score, inferred relevance/sufficiency,
combined lane state, automatic choice, or new domain command.

### UX-4 — Management judgment and operating limits

Scope:

- current-basis Integration surface;
- operating-limit/condition surface over existing Boundary capabilities; and
- carried exact selected bases without UUID assembly.

Gate: no synthesis/ranking, no stale Integration chain, Boundary remains distinct from Decision, and
all historical records remain visible.

### UX-5 — Proposal and separate authorization

Scope:

- task-language proposal review;
- “not yet authorized” state;
- unique authority resolution and display;
- zero/conflict/stale/out-of-scope stops; and
- separate authorization confirmation.

Gate: proposal/authorization separation and all five layers—identity, software access, governed
visibility, accountability, substantive authority—have hard-oracle coverage.

### UX-6 — Scenario-A practitioner confirmation

Scope:

- fresh Scenario-A exercise using only authoritative Scenario-A facts;
- no pre-seeded practitioner judgments;
- observed usability and conformance recorded separately; and
- comparison with the baseline stopping point without claiming causal improvement.

Gate: independent review determines whether follow-on refinement, M1C-R implementation closure, or a
semantic blocker is appropriate. It does not automatically authorize M1D.

## Required checks for every implementation increment

- production capabilities only; no test helper or browser-only semantic state;
- exact current basis revalidated at review and commit;
- no hidden-context leakage through counts, labels, errors, search, or detail routes;
- Value/Risk independence and non-ranking presentation;
- vacancy/conflict/stale/tampered hard oracles with zero mutation;
- append-only history and effective/knowledge-time reconstruction;
- keyboard, focus, responsive layout, and reversible-detail checks;
- practitioner-visible wording reviewed against the provisional classification;
- practitioner-visible and reference/example wording reviewed against the practitioner-language
  standard and its PR checklist; and
- a documented statement of what the increment does not implement.

## Explicit exclusions

This plan does not implement M1D, later Harborlight scenarios, Reassessment, Management Register,
first-class Observation, telemetry, a generalized workflow engine, new domain semantics, or a release
change.
