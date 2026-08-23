# Task-Oriented UX Semantic Review and Implementation Plan

## Status

This is a decomposition proposal, not authorization to implement. Each increment requires its own
bounded issue, branch, tests, practitioner review, and independent semantic acceptance. M1D remains
out of scope.

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

Scope:

- concise, Configuration-stable Case title using the existing persisted title contract;
- current-process/proposed-setup comparison;
- plain-language current position with separate prerequisites, available work, and unresolved
  conditions;
- non-disruptive source/history and technical-inspection shells; and
- no new write behavior.

Gate: read composition is deterministic, access-filtered, non-ranking, does not fabricate a durable
management question, and does not misstate governing currentness, authorization, or operation.

### UX-2 — Task-oriented “What we know” surface

Scope:

- separate available information, missing/unknown information, and requirements/authority;
- contextual source and limitations view;
- existing Evidence/Authority/Authority Gap creation translated into task language; and
- explicit Applicability review with carried context.

Gate: no inferred Applicability, no conversion of absence into favorable Evidence, and exact current
target revalidation at commit.

### UX-3 — Independent Value and Risk work surfaces

Scope:

- separate full-width lane workflows;
- natural-language analytical prompts;
- contextual source material limited to explicit visible relationships;
- three explicit checkpoints for Input, Fitness, and Selection; and
- persisted interaction intents that are not authoritative records.

Gate: lane independence, non-favorable outcomes, stale/tampered context, material evidence basis, and
non-selected history have hard-oracle tests.

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
- practitioner-visible wording reviewed against the provisional classification; and
- a documented statement of what the increment does not implement.

## Explicit exclusions

This plan does not implement M1D, later Harborlight scenarios, Reassessment, Management Register,
first-class Observation, telemetry, a generalized workflow engine, new domain semantics, or a release
change.
