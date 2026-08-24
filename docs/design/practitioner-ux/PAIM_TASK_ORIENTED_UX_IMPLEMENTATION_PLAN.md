# Task-Oriented UX Semantic Review and Implementation Plan

## Status

This was the bounded task-oriented implementation sequence through UX-3B. Issue #123 now pauses all
further practitioner-UI implementation pending independent owner review of the
[Practitioner Operating Model](PAIM_PRACTITIONER_OPERATING_MODEL.md) package. UX-4 is not the
automatic next increment. Any normative Responsibility/Case Work changes identified by that review
must be designed, accepted, and implemented through separate gates before dependent UI work.

UX-1 through UX-3B remain implemented historical increments. M1D remains out of scope.

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
6. **Accountability entry:** Resolved by UX-3B for Evidence Applicability, lane Fitness, and
   Acceptance/Selection. New browser finalization uses exact current accountable Role Assignments;
   arbitrary mechanism text is not an accountability source.
7. **Assessment orchestration:** Current UX-3 preserves Input, readiness, Fitness, and Selection.
   Issue #127 prospectively recommends one natural **Complete Value/Risk review** interaction only
   where separate adequacy and reliance facts can commit atomically without semantic loss.
8. **Neutral review wording:** Issue #127 rejects “sufficiently supported” as advocacy-prone for the
   future contract and proposes neutral assessment adequacy for decision use. Legacy Fitness names
   and semantics remain unchanged until coordinated specification and implementation gates pass.
9. **Single eligible candidate:** Issue #127 preserves a separate authoritative reliance fact but
   permits one confirmation to record adequacy and reliance when exactly one adequate candidate,
   dual Responsibilities, and all fail-closed guards are established. Uniqueness never auto-selects.
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

### UX-3A — Cross-workspace prerequisite context and practitioner confirmation

Implementation status: implemented by Issue #119. When a ready Value or Risk assessment has
explicitly linked current visible information but lacks one or more exact information-to-Input
Applicability relationships, the assessment page now identifies only that exact prerequisite set.
Each relationship remains an independent judgment. The contextual `What we know` handoff binds the
information and target assessment, retains the practitioner's genuine scope, outcome, conditions,
limitations, rationale, and governance-process decisions, and re-resolves the authoritative Case,
setup, Input, Evidence, and relationship at review and commit.

Completion returns to the next unresolved information item or to the originating lane's support
review. The displayed count is derived each time and is not persisted workflow state. Ordinary
`What we know` navigation remains general. Shared confirmations retain review-before-commit and
server-side revalidation while leading with the action, reviewed content, and practitioner
consequence; command names and identifiers are secondary record detail.

Gate: exact linked-source selection, multiple-item independence, tamper/stale/access failure with
zero mutation, deterministic return continuity, generic-workspace isolation, action-specific copy,
and unchanged Value/Risk/Fitness/Selection boundaries have focused integration and Chromium tests.

UX-3A does not solve the long dual-form page, replace the browser-native multi-select control, or
redesign the analytical role of linked information. Those observed issues remain deferred. It does
not implement UX-4, M1D, or a domain/schema change.

### UX-3B — Accountability before finalizing practitioner judgments

Implementation status: implemented by Issue #121. Evidence Applicability resolves only the current
explicit `Applicability Owner` function over the exact Configuration and its owning Case. Value and
Risk Fitness and Acceptance/Selection resolve their respective accountable evaluator functions
independently. One assignment is carried into practitioner-readable confirmation and revalidated at
commit. Vacancy, broad/narrow overlap, plural current assignments, revocation, supersession, stale
identity, or client-carried alternatives fail closed with zero judgment mutation.

The authenticated assessor remains separately attributable. Identity, software access, authorship,
Evidence ownership, Case ownership, and role labels do not create accountability. The ordinary form
therefore contains no free-text accountability escape hatch and cannot create a Role Assignment.

The persistence contract still permits legacy `accountable_mechanism` strings, but PAIM has no
general authoritative accountable-mechanism identity/version/current-selection model for these
covered obligations. UX-3B does not pretend otherwise: new browser finalization uses Role
Assignments only. Supporting another governed function for Applicability, or a genuine governed
mechanism, requires separate domain work that can represent its exact obligation, purpose/scope,
effective interval, and currentness. Existing historical mechanism-backed records remain history.

Gate: exact-one, vacancy, incompatible overlap, unrelated-function, tampered identity, and
review-to-commit change have hard-oracle coverage; the two analytical lanes remain independent; the
preserved Harborlight exercise receives no invented assignment. UX-3B does not implement UX-4,
M1D, Role Assignment administration, or a new schema concept.

### Practitioner Operating Model checkpoint — Issue #123

Implementation status: accepted documentation/design checkpoint. The package defines
organization-controlled `local`, separates Participant, practical Role, Responsibility, and
Authority, limits standing Case roles to Case Coordinator and Assessor plus optional Reviewer,
proposes bounded contextual Case Work/handoffs, and assesses current architecture honestly.

The checkpoint finds that current read composition can explain some ready/waiting work, while
durable responsibility assignment and cross-practitioner handoff require normative/domain/
persistence work. Organization-local concurrent use requires a separate deployment architecture.
`Applicability Owner` is not adopted as a practical role, and the Harborlight live vacancy is not
repaired.

Gate: owner acceptance of the operating model and explicit selection of the next bounded issue.
This section authorizes no UI, specification, schema, networking, Role Assignment, Work Item,
notification, UX-4, or M1D implementation.

### Product Design Foundation checkpoint — Issue #125

Implementation status: accepted documentation/design foundation. The
[Product Design Foundation](PAIM_PRODUCT_DESIGN_FOUNDATION.md) is the product-level governing
reference above the accepted Practitioner Operating Model. It establishes PAIM's central value as
management continuity of an AI-related business Decision over time, the continuing Value-Risk and
Decision lifecycle, reconstructable Decision and learning model, practitioner-centered product
principles, product scope boundary, and illustrative Harborlight journey.

The hierarchy for follow-on work is:

1. Product Design Foundation — why PAIM exists, what value it creates, and what it owns;
2. Practitioner Operating Model — how participants, roles, granular responsibilities, separate
   authority, Case Work, and deployment direction support that value;
3. normative Responsibility and Case Work specifications — exact contracts, only after a separate
   accepted issue;
4. practitioner UI design and implementation — expression of accepted product and normative
   decisions; and
5. engineering machinery — persistence, security, reconstruction, deployment, and verification.

Status: paused after the documentation checkpoint. No normative Responsibility/Case Work work, UI
redesign, UX-4, M1D, first-class Observation, analytics, organization-local deployment, or
Harborlight Scenario B-F work is authorized. The next issue must be explicitly selected and
bounded after independent review.

### Normative Model Redesign checkpoint — Issue #127

Implementation status: documentation/semantic-design checkpoint. The
[Normative Model Redesign package](../normative-model/) evaluates the smallest integrated target
for continuing Case identity/status, Case practical-role relationships, exact Responsibility,
derived and durable Case Work, planned/required review timing, optional rigorous quantitative
Value/Risk, analytical readiness, neutral assessment adequacy, exact reliance, historical
reconstruction, and legacy compatibility.

The proposal keeps current specifications controlling. It adds no records or runtime behavior.
Its [Downstream Specification Plan](../normative-model/PAIM_DOWNSTREAM_SPECIFICATION_PLAN.md)
requires separate coordinated gates for Integrity, Roles/Accountability, Case/Configuration,
Responsibility/Case Work, continuing review/timing, and Value/Risk
readiness/adequacy/reliance before any domain or UI implementation.

Status: checkpoint ready for independent review; subsequent work remains paused. No specification
revision, Responsibility/Work implementation, review scheduler, UI redesign, UX-4, M1D,
organization-local deployment, analytics, or Harborlight Scenario B-F work begins automatically.

### UX-4 — Management judgment and operating limits

Status: paused. Re-evaluate scope and sequencing only after the Practitioner Operating Model gate
and any required Responsibility/Case Work contracts are accepted. The earlier outline below is
retained as historical planning, not current authorization.

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
