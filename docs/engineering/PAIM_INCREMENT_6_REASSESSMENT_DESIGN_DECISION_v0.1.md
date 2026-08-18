# PAIM Increment 6 Reassessment Design Decision v0.1

## Status and purpose

This artifact resolves the human design questions needed to close IRR-011 for a bounded Increment 6 implementation. It is a design-analysis proposal for independent PAIM design-authority review. It is not a governing specification and does not authorize implementation.

The analysis preserves the accepted Increments 1–5 contracts, the one-governing-Configuration-per-Case model, immutable/versioned history, exact Decision and Configuration binding, authority-first action, Value/Risk independence, dual-time reconstruction, and explicit absence/conflict behavior.

Increment 6 remains bounded as follows:

- no first-class Observation record or automated Observation-to-Trigger conversion (IRR-009);
- no Management Register population, shared-dependency equivalence, or cross-Case aggregation (IRR-012);
- no operating-state strength/breadth/rank inference (IRR-014);
- no generic event bus, workflow engine, scheduler, notification system, or distributed-concurrency design; and
- no code, schema, migration, API, UI, projection, or executable-test design in this artifact.

## Governing basis reviewed

The following current repository contracts were reviewed as the authority for this analysis:

- `PAIM_PLATFORM_ARCHITECTURE_v0.1.md`, especially §§6.3–6.4, 7, 12, 16, 18, 20, and 23;
- `PAIM_IMPLEMENTATION_SEQUENCE_AND_P1_GATES_v0.1.md`, especially §§5–8 and 10.4–10.6;
- `PAIM_CODEX_IMPLEMENTATION_READINESS_REVIEW_v0.1.md`, including IRR-011;
- `PAIM_REASSESSMENT_SPEC_v0.1.md`, especially §§3–10 and 19–38;
- `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`, especially §§12–18 and 20–23;
- `PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md`, especially §§20–30;
- `PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md`, including its Reassessment handoff and deferred-P1 boundary;
- `PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md`, especially §§2–3, 21–22, 26–28, and 32;
- `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`, especially §§3, 5.7, 6, 7, and 8; and
- `PAIM_SYSTEM_BEHAVIORAL_VALIDATION_STRATEGY_v0.1.md`, especially §§25 and 28.

Current governing specifications control if this analysis is later found inconsistent with them.

## Fixed invariants carried into the decision

1. Trigger, Reassessment, membership/coordination determination, Interim Operating Disposition, and outcome facts that become authoritative use stable record identity, immutable version identity, effective time, recorded time, provenance, and exact relationship history.
2. A finalized fact is never edited in place. Correction, amendment, supersession, withdrawal, cancellation, and status changes preserve predecessor content and recorded knowledge.
3. Current selection returns one eligible version, explicit absence/not established, or explicit incompatible-current conflict. Time, row order, recency, severity, hierarchy, specificity, breadth, and software permission do not select a winner.
4. A Case has at most one governing Configuration at an effective time. Independent concurrent governing Configurations require separately linked Cases.
5. Opening Reassessment neither changes nor extends operation. Operation remains governed by the exact current Decision and Boundary plus every applicable current authorized Interim Operating Disposition.
6. Current Interim Operating Dispositions combine only under the already-governing restrictive-overlay rule: apply the determinable intersection; suspend affected scope if the intersection is indeterminate. No state ranking is used.
7. Every completed Reassessment atomically produces exactly one path: immutable unchanged-Decision Confirmation or an authorized successor/amendment Decision with its own Boundary Snapshot and Decision Authorization Basis.
8. Trigger materiality, grouping, duplicate disposition, coordination, supersession, cancellation, completion, and any operating effect are accountable determinations, not queue behavior or software convenience.
9. A Trigger and every relationship to it remain historically retrievable after correction, withdrawal, cancellation, supersession, or Reassessment completion.
10. Value and Risk remain separate through any refreshed inputs and Reassessment Integration.

## Topic classification and recommended disposition

Each required topic has exactly one classification.

| # | Topic | Classification | Recommended disposition |
|---:|---|---|---|
| 1 | Trigger identity and source | `HUMAN PAIM DESIGN DECISION REQUIRED` | Adopt the bounded authoritative Trigger contract and identity rule in D1. |
| 2 | Trigger-to-Reassessment cardinality | `HUMAN PAIM DESIGN DECISION REQUIRED` | Permit many-to-many relationships; freeze each Reassessment Version's exact Trigger Set under D2. |
| 3 | Reassessment identity and scope | `HUMAN PAIM DESIGN DECISION REQUIRED` | Bind one stable Reassessment to one Case, initiating Decision Version, target Configuration Version, purpose/scope, owner, and versioned Trigger Set under D2. |
| 4 | Trigger compatibility and grouping | `HUMAN PAIM DESIGN DECISION REQUIRED` | Prohibit automatic semantic grouping; require an accountable exact-context grouping determination under D3. |
| 5 | Duplicate Trigger semantics | `HUMAN PAIM DESIGN DECISION REQUIRED` | Deduplicate only exact identity/idempotent replay; never infer semantic duplication under D1. |
| 6 | Concurrent Reassessments in one Case | `HUMAN PAIM DESIGN DECISION REQUIRED` | Permit concurrency only for explicitly non-overlapping scope; otherwise expose conflict under D4. |
| 7 | Overlap/conflict detection | `HUMAN PAIM DESIGN DECISION REQUIRED` | Use exact scope comparison plus accountable compatibility determination; never a priority winner, under D4. |
| 8 | Merge semantics | `HUMAN PAIM DESIGN DECISION REQUIRED` | Do not support Reassessment merge in v0.1; use explicit coordination/supersession under D5. |
| 9 | Supersession and cancellation | `HUMAN PAIM DESIGN DECISION REQUIRED` | Require explicit, authorized, history-preserving action; no event automatically closes Reassessment under D6. |
| 10 | Trigger ownership during merge/supersession | `FIXED BY GOVERNING SPEC` | Preserve all Trigger relationships; derive prospective coverage from eligible current relationships and determinations. |
| 11 | No-lost-trigger invariant | `HUMAN PAIM DESIGN DECISION REQUIRED` | Adopt the exact coverage-state vocabulary and invariant in D6. |
| 12 | Reassessment lifecycle/status vocabulary | `HUMAN PAIM DESIGN DECISION REQUIRED` | Adopt the minimal non-Case-lifecycle vocabulary in D7. |
| 13 | Interim Operating Disposition interaction | `FIXED BY GOVERNING SPEC` | Multiple Reassessments may each support a disposition; all independently valid current dispositions restrict through intersection, or affected scope suspends if indeterminate. |
| 14 | Reassessment completion outcome cardinality | `FIXED BY GOVERNING SPEC` | Exactly one unchanged-Decision Confirmation or one authorized successor/amendment Decision; blocked/unresolved is not completion. |
| 15 | Same-Decision concurrent completion | `HUMAN PAIM DESIGN DECISION REQUIRED` | Require prospective revalidation and explicit coordination; never auto-close the other Reassessment, under D8. |
| 16 | Successor Decision effect on open Reassessments | `HUMAN PAIM DESIGN DECISION REQUIRED` | Preserve historical analysis but require explicit supersession and a new/rebased Reassessment identity before current completion under D8. |
| 17 | Cross-Case trigger propagation | `HUMAN PAIM DESIGN DECISION REQUIRED` | Create distinct Case-scoped Triggers sharing exact source provenance; never cross-Case merge under D9. |
| 18 | Accountability | `HUMAN PAIM DESIGN DECISION REQUIRED` | Establish substantive Trigger Determiner, Reassessment Owner, and Reassessment Coordination Authority functions under D10; Decision Authority remains separate. |
| 19 | Effective-time and knowledge-time semantics | `FIXED BY GOVERNING SPEC` | Reuse the integrity kernel's dual-time, current-selection, expected-version, idempotency, and immutable-history rules exactly. |
| 20 | IRR-014 boundary for Increment 6 | `DEFERRED LATER P1 / OUT OF SCOPE` | Carry exact explicit state values and authorized applicability only; perform no stronger/broader/rank inference. |
| 21 | IRR-009 boundary for Increment 6 | `DEFERRED LATER P1 / OUT OF SCOPE` | Accept explicit human/external provenance and exact existing-record sources; persist no Observation and automate no Observation conversion. |
| 22 | IRR-012 boundary | `DEFERRED LATER P1 / OUT OF SCOPE` | Require no Register, shared-dependency equivalence, concentration aggregation, or register-driven workflow for Case-scoped Reassessment. |

## Human design decisions

### D1. Trigger identity, source, materiality, and exact duplication

**Ambiguity.** The current specifications name Trigger fields and source families but do not establish the continuing subject of a Trigger, exact replay identity, how source updates relate, or whether competing materiality judgments create duplicate Triggers.

**Why engineering cannot decide.** Choosing event identity, Case impact, or materiality changes which management obligations exist. Hashing similar prose, collapsing source updates, or accepting the newest judgment would erase accountable meaning for software convenience.

**Viable options.**

1. One Trigger per received message or record version. This is simple and lossless but creates meaningless duplicates and makes retries authoritative events.
2. One Trigger per source event globally. This reduces duplicates but improperly combines independent Case contexts and decisions.
3. One Trigger per established source occurrence, affected Case, and declared management question, with immutable versions and identity-only replay protection.

**Tradeoffs.** Option 1 preserves raw history but weakens longitudinal management identity. Option 2 damages bounded-Case accountability and cross-Case independence. Option 3 best preserves source history, Case-specific authority, non-destructive correction, and explicit management judgment, at the cost of requiring a declared source identity and management question.

**Recommended v0.1 choice.** Adopt option 3. A Trigger has at minimum:

- stable Trigger ID and immutable Trigger Version ID;
- exactly one affected/owning Case;
- exact initiating/current Decision Version and governing Configuration Version when established, or explicit `NOT ESTABLISHED`/conflict references rather than invented IDs;
- trigger type/category and declared affected management question/scope;
- exact source family, source Record ID and Version ID for an existing PAIM record, or explicit external/human source system, event identity, actor/provenance, and received/knowledge time;
- description/rationale and affected boundary/control/evidence/authority references where known;
- effective time, recorded time, source knowledge cutoff/provenance;
- predecessor/correction/supersession/withdrawal relationships; and
- one current accountable Trigger Determination outcome: `INFORMATIONAL`, `MONITOR`, `ANALYTICAL_REFRESH`, `REASSESSMENT_REQUIRED`, or `IMMEDIATE_DISPOSITION_AND_REASSESSMENT`.

Exact replay identity is the same source occurrence identity + exact affected Case + declared management question + command idempotency identity. Replay returns the original outcome or payload mismatch. A materially updated version of the same established source occurrence creates a successor Trigger Version. The same event affecting a distinct management question may create a distinct Trigger only through an accountable determination. Competing co-current determinations for the same Trigger/context are explicit conflict, not separate hidden winners.

**Normative wording later required.** Harden Reassessment §§3, 7–8, 34–35 and Integrity §§2.1, 3.11–3.13 with the minimum contract, exact identity key, materiality outcomes, one/absence/conflict selection, and source-update rule. Add Trigger Determiner accountability to Roles §§21–22 and 26–28.

**Hard-oracle examples.**

- Retrying the same Evidence Version → Case A → management-question command returns the same Trigger ID/Version; no second Trigger exists.
- A corrected Evidence Version for the same evidence occurrence and Case A creates a successor Trigger Version and preserves the first.
- Similar descriptions from unrelated events are distinct; text similarity cannot deduplicate them.
- Two incompatible current materiality determinations produce `TRIGGER DETERMINATION CONFLICT — UNRESOLVED`; recency cannot select one.

### D2. Many-to-many cardinality, membership, and Reassessment identity

**Ambiguity.** The Reassessment specification uses singular `trigger ID/type`, while architecture reserves many-to-many links. It does not say whether later membership changes the Reassessment identity, a version, or only a relationship.

**Why engineering cannot decide.** Grouping changes analytical scope, accountability, outcome coverage, and the historical basis of a Decision Confirmation or successor Decision. A storage-friendly join table or mutable list cannot decide that meaning.

**Viable options.**

1. Enforce one Trigger ↔ one Reassessment. This is simple but duplicates analysis and contradicts the reserved many-to-many seam.
2. Allow mutable many-to-many membership. This is flexible but rewrites the basis of in-progress and completed analysis.
3. Allow many-to-many relationships while every finalized Reassessment Version binds one immutable exact Trigger Set; adding/removing membership creates a successor Reassessment Version and immutable relationship history.

**Tradeoffs.** Option 1 weakens coordination and source-event reuse. Option 2 breaks exact historical reconstruction. Option 3 preserves bounded scope and exact outcome basis while supporting legitimate reuse, but requires explicit versioning when membership changes.

**Recommended v0.1 choice.** Adopt option 3.

- One Trigger may relate to multiple Reassessments only for explicitly distinguishable scopes/purposes or explicit successor coordination.
- One Reassessment may contain multiple exact Trigger Versions.
- One source event affecting multiple Cases produces separate Case-scoped Triggers, not one cross-Case Trigger.
- Every finalized Reassessment Version binds one complete immutable Trigger Set of exact Trigger Versions plus membership relationship Versions.
- Adding a compatible Trigger to an open Reassessment atomically creates a successor Reassessment Version with a new exact Trigger Set. It does not mutate the prior version.
- Analytical input refresh that does not alter Case, initiating Decision, target Configuration, purpose/scope, or Trigger Set remains the same Reassessment identity but creates the required successor Reassessment/content/basis versions.
- Changing Case, initiating Decision, target Configuration, or substantive purpose/scope requires a new/successor Reassessment identity, not merely a version.

Minimum Reassessment identity binds one owning Case, one initiating governing Decision Version, one target governing Configuration Version, one explicit purpose/scope, one Reassessment Owner accountability relationship, and lifecycle/version history. If Decision or Configuration is absent/conflicting, initiation may be recorded only as blocked/not established and cannot pretend to have an exact governing context.

**Normative wording later required.** Replace singular-trigger assumptions in Reassessment §§3, 24–25 and define stable identity versus new-version versus new-identity rules, exact Trigger Set, membership relationships, and relationship history. Align Integrity §3.12 and architecture §§6.3 and 12.6.

**Hard-oracle examples.**

- R1 v1 binds T1. Adding T2 creates R1 v2 binding T1+T2; R1 v1 remains retrievable.
- T1 supports a narrow control reassessment and later a separately scoped authority reassessment only through two explicit relationships; both remain visible.
- Changing from Decision D1 to D2 does not silently revise R1; a successor Reassessment identity is required.

### D3. Trigger compatibility and grouping

**Ambiguity.** Current contracts do not define when two Triggers are compatible enough to share one Reassessment.

**Why engineering cannot decide.** Compatibility is a judgment about management scope and analytical consequence. Time proximity, common source, category, severity, or matching labels do not prove that one review/outcome can responsibly cover both.

**Viable options.**

1. Automatically group by Case and time window.
2. Automatically group by exact Case, Decision, Configuration, and category.
3. Never infer grouping; require an accountable determination after exact-context mechanical guards pass.

**Tradeoffs.** Option 1 is efficient but risks silent consumption and unrelated scope. Option 2 is safer mechanically but category equality still does not prove compatible purpose. Option 3 best protects longitudinal integrity and authority-first scope, while adding explicit triage work.

**Recommended v0.1 choice.** Adopt option 3. Software may establish only prerequisite facts: exact same Case, initiating Decision Version, target Configuration Version, and structurally declared scope references. It may propose candidates but cannot group them. A current accountable grouping determination must state compatibility, rationale, exact Trigger Versions, target Reassessment, effective/recorded time, and relied-upon assignment/mechanism. Different Decision Versions, Configurations, Cases, or unrelated purposes are mechanically incompatible for one Reassessment identity. Same exact context remains only potentially compatible.

**Normative wording later required.** Harden Reassessment §§7, 10, 25, and 35 with grouping eligibility, the accountable determination, explicit absence/conflict results, and prohibited heuristic winners.

**Hard-oracle examples.**

- Two same-Case/same-D1/same-C1 control-failure Triggers are not grouped until one eligible determination says they share scope.
- Two Triggers received minutes apart for unrelated authority and capacity questions do not auto-group.
- Same Case but D1 and D2 Trigger contexts are incompatible for one Reassessment identity.

### D4. Concurrent Reassessments and overlap/conflict

**Ambiguity.** Simultaneous Reassessments are deferred, and neither allowed concurrency nor overlap behavior is defined.

**Why engineering cannot decide.** A one-open-row constraint can suppress legitimate independent review, while unlimited concurrency can create competing outcomes and dispositions. Database locks, creation order, severity, or owner hierarchy cannot define management compatibility.

**Viable options.**

1. Permit only one open Reassessment per Case.
2. Permit multiple only for explicit non-overlapping scope under one exact Case/Decision/Configuration context; overlap is conflict requiring accountable coordination.
3. Permit general concurrency with eventual conflict resolution.

**Tradeoffs.** Option 1 is deterministic but bottlenecks unrelated work and encourages overbroad scope. Option 3 maximizes flexibility but weakens outcome integrity and no-lost-trigger guarantees. Option 2 supports bounded parallelism while preserving exact conflict and history.

**Recommended v0.1 choice.** Adopt option 2. Two open Reassessments may coexist only when they bind the same Case and either (a) have mechanically disjoint declared affected-component/scope references, or (b) have one current accountable compatibility determination establishing coexistence without competing outcome coverage. Different current Decision/Configuration contexts do not make them silently compatible; they require explicit successor/rebase handling. Any shared Trigger, affected exact record/scope, proposed Decision consequence, or indeterminate scope is `REASSESSMENT OVERLAP CONFLICT — UNRESOLVED` absent an explicit coordination determination. Conflict blocks completion and scope-changing disposition action for the affected overlap, but does not erase either analysis.

No implicit winner exists by creation time, recency, severity, owner, hierarchy, scope breadth, or software priority.

**Normative wording later required.** Add current open-Reassessment selection and overlap outcomes to Reassessment §§4, 10, 34, and 38; align Case Lifecycle §§12–13 and Integrity §§3.11 and 5.7.

**Hard-oracle examples.**

- One evidence-applicability refresh and one unrelated authority-domain review may coexist only when exact declared scopes are disjoint or accountable compatibility is established.
- Two Reassessments both proposing consequences for D1's same boundary clause produce conflict; neither completes first by timestamp.
- Missing scope is indeterminate and cannot be treated as non-overlap.

### D5. Merge semantics

**Ambiguity.** IRR-011 reserves merge behavior but does not define whether merge creates a successor, absorption, or shared membership.

**Why engineering cannot decide.** Merge determines identity, ownership, trigger coverage, analytical basis, and which outcome governs. A convenience operation could destructively collapse two accountable histories.

**Viable options.**

1. Create a new successor Reassessment preserving both predecessors and all Triggers.
2. Allow one Reassessment to absorb another through an authorized relationship.
3. Do not support merge in v0.1; use explicit coexistence, cancellation, or supersession with Trigger coverage preserved.

**Tradeoffs.** Option 1 is integrity-preserving but adds identity, completion, ownership, and migration semantics before needed. Option 2 risks a disguised winner/overwrite rule. Option 3 is the narrowest deterministic increment and avoids premature workflow complexity, but may require explicit coordination steps.

**Recommended v0.1 choice.** Adopt option 3. `MERGED` is not a v0.1 Reassessment status or action. Operators must either establish non-overlapping coexistence or explicitly supersede/cancel one Reassessment and establish prospective Trigger coverage under D6. A future merge capability, if accepted, must use a new successor Reassessment preserving all predecessor identities, Versions, Trigger relationships, actors/authority, rationale, and time; absorption is rejected.

**Normative wording later required.** State in Reassessment §§4, 25, and 38 that v0.1 has no merge action and define the coordination alternative. Keep future merge outside the Increment 6 contract.

**Hard-oracle examples.**

- A request to merge R1 and R2 is rejected as unsupported; no rows or Trigger links change.
- An accountable actor may instead supersede R2 with named successor R1 only if every unresolved Trigger receives explicit prospective coverage and the action passes D6 authority.

### D6. Supersession, cancellation, Trigger coverage, and the no-lost-trigger invariant

**Ambiguity.** The specifications list cancellation/supersession statuses but do not say what causes them, whether they close another Reassessment's work, or how unresolved Trigger coverage survives.

**Why engineering cannot decide.** A newer Decision, Configuration, source correction, or duplicate claim may affect eligibility but does not establish management intent or authority to abandon work. Automatic closure can lose material Triggers.

**Viable options.**

1. Auto-close on newer Decision/Configuration/Reassessment.
2. Permit free cancellation while retaining history.
3. Require explicit accountable cancellation/supersession and an atomic disposition of every unresolved Trigger relationship.

**Tradeoffs.** Option 1 violates authority-first and historical meaning. Option 2 preserves rows but can orphan obligations. Option 3 makes abandonment and transfer visible and reconstructable, with additional accountable coordination.

**Recommended v0.1 choice.** Adopt option 3.

- `CANCELLED` ends planned work without naming a successor. It requires rationale, exact scope, accountable authority, effective/recorded time, and a separate valid disposition for every Trigger not already satisfied.
- `SUPERSEDED` names one exact successor Reassessment identity/version and replacement scope. It does not mean the predecessor was invalid historically.
- A successor Decision, withdrawn/expired Decision, superseded Configuration, corrected/withdrawn Trigger, duplicate discovery, or later broader Reassessment creates a prospective eligibility/attention condition only. None automatically closes work.
- One Reassessment cannot close another. Only its own authorized cancellation/supersession action changes its status.
- All historical Trigger ↔ Reassessment relationships remain. Prospective current coverage is derived from eligible membership, disposition, completion, and supersession facts.

For every current eligible Trigger whose current determination requires reassessment, exactly one **Trigger Coverage State** must be derivable at an effective time and knowledge cutoff:

1. `REASSESSMENT_REQUIRED_UNASSIGNED` — explicitly visible and awaiting accountable assignment;
2. `LINKED_ACTIVE` — linked to at least one eligible active Reassessment, with multiple links allowed only for distinguishable scope or explicit coordination;
3. `BLOCKED_CONFLICT` — assignment, grouping, overlap, authority, or currentness conflict prevents valid active coverage;
4. `SATISFIED_BY_COMPLETED_REASSESSMENT` — exact completed Reassessment outcome explicitly covers the Trigger Version; or
5. `DUPLICATE_DISPOSITIONED` — an accountable identity-level duplicate determination names the canonical Trigger and coverage basis.

A corrected, withdrawn, or superseded Trigger Version is prospectively ineligible rather than assigned a coverage state, but its historical coverage remains reconstructable. No Trigger is deleted or hidden. More than one incompatible coverage state is explicit `TRIGGER COVERAGE CONFLICT — UNRESOLVED`.

**Normative wording later required.** Harden Reassessment §§4, 7, 25, 34, and 38 with cancellation/supersession actions, the exact coverage vocabulary, one/absence/conflict derivation, and atomic unresolved-Trigger handling. Align Integrity §§3.5–3.13.

**Hard-oracle examples.**

- Cancelling R1 while T1 is unresolved fails unless T1 atomically becomes unassigned, duplicate-dispositioned, or validly linked elsewhere.
- D2 becoming effective marks D1-bound R1 as requiring coordination; it does not auto-supersede R1.
- A withdrawn T1 remains in R1's completed historical basis but is not prospectively eligible for new coverage.

### D7. Reassessment lifecycle vocabulary

**Ambiguity.** The current vocabulary is illustrative and does not distinguish blocked/conflict, awaiting authority, or the two terminal completion paths.

**Why engineering cannot decide.** Status controls eligibility, concurrency, completion, and Trigger coverage. UI labels or implementation workflow states cannot determine substantive terminal meaning.

**Viable options.**

1. Use only `OPEN`, `COMPLETED`, `CANCELLED`, `SUPERSEDED`.
2. Adopt a large configurable workflow vocabulary.
3. Adopt a small normative v0.1 vocabulary that distinguishes preparation, analysis, authority wait, conflict, and the two completion outcomes.

**Tradeoffs.** Option 1 hides material blocking and outcome distinctions. Option 2 creates a generic workflow engine and organization-dependent semantics. Option 3 provides deterministic guards while leaving UI and subtask presentation flexible.

**Recommended v0.1 choice.** Adopt option 3:

- `PROPOSED` — identity/scope exists but opening guards or accountability are not yet established;
- `OPEN` — valid scope, owner, and Trigger Set established;
- `ANALYSIS_IN_PROGRESS` — accountable review has begun;
- `AWAITING_DECISION_AUTHORITY` — analysis is ready but confirmation/successor authority path is not established;
- `BLOCKED_CONFLICT` — explicit Trigger, membership, scope, concurrency, authority, or currentness conflict;
- `COMPLETED_CONFIRMED` — atomic immutable unchanged-Decision Confirmation path;
- `COMPLETED_SUCCESSOR_DECISION` — atomic authorized successor/amendment Decision path;
- `CANCELLED` — authorized termination without completion; and
- `SUPERSEDED` — authorized prospective replacement by a named Reassessment.

`REASSESSMENT_DUE` and `REOPENED` remain Case lifecycle states, not Reassessment statuses. `UNASSIGNED` remains a Trigger coverage state. Blocked/unresolved is never completion.

**Normative wording later required.** Replace illustrative status text in Reassessment §4, define transitions/guards/status-event versus new-version behavior, and align Case Lifecycle §§12–13 without collapsing the two state dimensions.

**Hard-oracle examples.**

- Missing Reassessment Owner leaves a record `PROPOSED`; it cannot become `OPEN`.
- Outcome conflict yields `BLOCKED_CONFLICT`, not `COMPLETED`.
- A completed record can be exactly classified as confirmed or successor-Decision; generic completed without one path is rejected.

### D8. Same-Decision concurrency, completion, and successor-Decision effect

**Ambiguity.** If concurrent Reassessments concern the same Decision, the specifications do not say how the first completion affects the second or whether an open Reassessment may complete after a successor Decision changes current governance.

**Why engineering cannot decide.** Auto-closing by first completion loses independent triggers; allowing stale completion can create competing current Decisions. Last-writer-wins changes management authority.

**Viable options.**

1. First completion automatically supersedes all other same-Decision Reassessments.
2. Each completes independently against its historical initiating Decision, even after governance changes.
3. Do not auto-close; require every completion to revalidate current Decision/Configuration, overlap, Trigger coverage, and authority, with explicit coordination/rebase when governance changed.

**Tradeoffs.** Option 1 loses work and Trigger ownership. Option 2 preserves analysis but can authorize stale or competing current outcomes. Option 3 preserves both histories and prevents stale authority, at the cost of an explicit rebase/supersession decision.

**Recommended v0.1 choice.** Adopt option 3.

- If R1 confirms D1 unchanged, R2 remains open. R2 may later complete against D1 only if D1 and its Configuration remain exact current governance at R2's completion effective time and no unresolved overlap/coverage/authority conflict exists.
- If R1 creates effective successor D2, any open D1-bound R2 may continue only as preserved historical analysis. It cannot issue a current Confirmation for D1 or a competing successor from stale context.
- Continuing R2 prospectively requires an explicit coordination determination, a new successor Reassessment identity bound to D2/current Configuration, explicit carried Trigger relationships, and supersession/cancellation of R2 as appropriate.
- A future-effective D2 does not affect R2 before D2's effective time; dual-time selection applies.
- No action automatically closes R2, and a second successor Decision can arise only through the ordinary Decision currentness/authorization rules; incompatible candidates surface Decision conflict, never a winner.

**Normative wording later required.** Add prospective completion guards and rebase/successor-Reassessment rules to Reassessment §§3, 22–25, 33–34; align Integration/Decision §§24–29, Integrity §§3.11 and 7.5–7.6, and Case Lifecycle §13.

**Hard-oracle examples.**

- R1 confirms D1; R2 remains `ANALYSIS_IN_PROGRESS` and later revalidates D1 rather than auto-closing.
- R1 creates D2 effective today; R2's attempted D1 Confirmation today is rejected as stale current context.
- D2 is recorded today but effective next month; a historically effective R2 action before next month uses the correct effective/knowledge-time basis.

### D9. Cross-Case source-event propagation

**Ambiguity.** A shared provider/control/external event may affect many Cases, but IRR-009 and IRR-012 are deferred and the current Trigger cardinality is undefined.

**Why engineering cannot decide.** Matching provider names or control descriptions cannot establish Case impact, source-event sameness, or authority. A global Reassessment would collapse independent Configurations and Decisions.

**Viable options.**

1. One global Trigger and one cross-Case Reassessment.
2. Clone event data into unrelated Case records without shared provenance.
3. Retain one exact external/existing-record provenance identity and create separately accountable Case-scoped Trigger identities; no cross-Case Reassessment merge.

**Tradeoffs.** Option 1 violates bounded-Case governance. Option 2 preserves Case scope but loses source traceability. Option 3 preserves both exact provenance and independent Case accountability without needing Register aggregation.

**Recommended v0.1 choice.** Adopt option 3. Each affected Case gets a distinct Trigger ID, exact affected Decision/Configuration context, and independent materiality determination. Each Trigger references the same established source event/provenance identity where applicable. No automatic propagation, grouping, merge, shared outcome, or authority transfer occurs. An external caller may submit separate idempotent Case-scoped commands; deciding that a Case is affected remains accountable.

**Normative wording later required.** Add the cross-Case identity/provenance rule to Reassessment §§7, 29, and 38 and clarify in Roles §§29–30 that shared dependency coordination does not replace Case/Reassessment ownership or Decision Authority.

**Hard-oracle examples.**

- Provider event E1 affects Cases A and B: TA and TB are distinct, both cite E1, and their Reassessments/outcomes remain independent.
- A provider-name match alone creates no Trigger for Case C.
- Closing Case A's Reassessment does not satisfy TB.

### D10. Substantive accountability functions

**Ambiguity.** Existing specs identify Reassessment Owner generally but do not establish who accepts raw-event materiality, grouping/duplicate/coordination actions, cancellation/supersession, or unchanged-Decision confirmation.

**Why engineering cannot decide.** Software permission, Case ownership, authorship, or queue assignment does not establish substantive management authority. These actions alter obligations and coverage.

**Viable options.**

1. Treat Case Owner or administrator permission as sufficient for every action.
2. Require Decision Authority for all Trigger and Reassessment actions.
3. Establish distinct substantive functions using existing typed-target accountability semantics, while reserving Decision authority for actual Decision/required confirmation authorization.

**Tradeoffs.** Option 1 violates authority separation. Option 2 is safe but unnecessarily centralizes analytical coordination and confuses management judgment with workflow accountability. Option 3 preserves function separation and allows one actor to hold multiple functions only through separately established assignments/mechanisms.

**Recommended v0.1 choice.** Adopt option 3:

- **Trigger Determiner** accepts the raw/existing-record source as a Trigger for an exact Case context and owns the materiality outcome.
- **Reassessment Owner** owns exact Trigger Set, declared scope, review coordination, status progression, and completion package preparation.
- **Reassessment Coordination Authority** owns grouping, duplicate disposition, compatibility, overlap resolution, cancellation, supersession, and Trigger transfer/coverage actions.
- **Decision Authority** authorizes any successor/amendment Decision and any Interim Operating Disposition under the existing Authorization Basis rules. It approves an unchanged-Decision Confirmation only where required by the current Decision or legitimate organizational authority mechanism; the Confirmation must always retain the accountable Reassessment Owner/confirmer.

For v0.1 these obligations use the existing applicable typed target set: exact Decision, exact target Configuration, and owning Case; Intervention may additionally be applicable when it is the exact Trigger source/scope. Each assignment retains its own target type. Exactly one eligible accountable assignment or governed mechanism is required; zero is not established and incompatible plurality is conflict. No implicit scope precedence applies. Every action binds the exact actor, assignment/mechanism, delegation chain, rule/version/scope/source where a mechanism is used, effective time, recorded time, and rationale. Later routine role expiry does not rewrite a historically valid action; withdrawal, revocation, expiry, or supersession is prospective for future actions.

No new software permission or technical principal is a substantive function. If later hardening finds exact Trigger/Reassessment role targets necessary, they must be explicit additions to Roles §26 rather than synthetic scope strings.

**Normative wording later required.** Add these functions and obligation-target rules to Roles §§4, 21–22, 26–28, and 32; add action-specific accountability to Reassessment §§7–8, 24–25, and 34–35; align Confirmation authority language in Integrity §7.5.

**Hard-oracle examples.**

- An administrator with write permission but no applicable Trigger Determiner accountability cannot classify an event as reassessment-required.
- Case- and Configuration-scoped Coordination Authority assignments overlapping for the same obligation produce explicit conflict absent valid supersession/delegation.
- A fabricated mechanism string is rejected; a governed mechanism must retain exact identity, rule/version, scope, authority source, actor, and time.
- Routine later Owner-role expiry preserves a completed historical determination; a revoked assignment cannot authorize tomorrow's cancellation.

## Fixed effective-time, knowledge-time, and command behavior

No new temporal model is needed. Increment 6 must use the common integrity kernel:

- `effective_at` determines what governed the management subject;
- optional `known_at` limits facts to those recorded by that cutoff;
- later backdating, correction, withdrawal, or supersession never rewrites an earlier knowledge-time result;
- current Trigger Determination, Trigger Coverage, Reassessment Version/status, membership, coordination determination, accountability, Interim Operating Disposition, and outcome selection each return one, explicit absence/not established, or explicit conflict;
- commands depending on current state carry expected-version/current-selection preconditions and reject stale inputs rather than silently rebase;
- exact idempotency replay returns the original result or explicit payload mismatch; and
- projections/queues cannot authorize or substitute for authoritative selection.

Historical completed Reassessment retrieval retains the exact Trigger Set, memberships, analytical inputs, Evidence/Authority, Value/Risk refreshes, Decision/Configuration/Boundary, accountability, Interim Dispositions, effective/knowledge context, and exactly one outcome basis used at completion.

## Interim Operating Disposition concurrency

The governing specs already resolve this behavior; no new human choice is recommended:

1. Each Reassessment may have zero or more historical dispositions and at most the current eligible disposition results allowed by exact scope/current-selection rules.
2. Multiple independently valid current dispositions from concurrent Reassessments may coexist.
3. Effective operation is the exact current Decision/Boundary intersected with every applicable independently valid restrictive disposition.
4. If the restrictive intersection is mechanically determinable, operation cannot exceed it while any conflict is escalated.
5. If intersection is indeterminate, affected operation is suspended pending authorized determination.
6. No strongest-state, severity, newest, or ordinal ranking is performed.
7. Expiry is prospective; an expired disposition remains historical and cannot continue silently.

## Hard-oracle scenario matrix

| # | Scenario | Deterministic recommended outcome |
|---:|---|---|
| 1 | One Trigger → one Reassessment | One exact Case-scoped Trigger, one eligible determination, one `OPEN` Reassessment Version, and one immutable membership; coverage is `LINKED_ACTIVE`. |
| 2 | Two compatible Triggers arrive before start | No automatic grouping. One accountable grouping determination may create one Reassessment whose first finalized Version binds both exact Trigger Versions; otherwise each remains explicitly unassigned/separate. |
| 3 | Second compatible Trigger arrives after open | Accountable grouping plus a successor Reassessment Version binds the expanded exact Trigger Set; prior Version remains unchanged. Without it, the Trigger stays unassigned/separate. |
| 4 | Exact replay of same Trigger source | Idempotency returns the original Trigger outcome; no second Trigger. Payload mismatch is explicit error. |
| 5 | Materially changed source Version | Same established source occurrence/Case/question creates a successor Trigger Version; a distinct question requires an accountable new Trigger identity. Prior Version remains. |
| 6 | Same provider event affects two Cases | Two Case-scoped Triggers cite one source provenance identity; no cross-Case Reassessment or merge. |
| 7 | Two unrelated Triggers in same Case | They do not group by recency, category, or source similarity; independent/unassigned until accountable scope handling. |
| 8 | Two open non-overlapping Reassessments | They coexist only with exact disjoint scopes or current accountable compatibility; both remain visible. |
| 9 | Two overlapping open Reassessments | `REASSESSMENT OVERLAP CONFLICT — UNRESOLVED`; no last-writer completion or disposition winner. |
| 10 | One Reassessment consumes another's Trigger | Rejected absent explicit membership Version, coordination determination, successor Reassessment Version, and preserved original relationship. |
| 11 | Merge requested | Unsupported in v0.1. No identity/history changes. Coordination must use coexistence, cancellation, or explicit supersession with coverage preservation. |
| 12 | Cancellation/supersession | Historical Reassessment and Trigger relationships remain; every unresolved Trigger atomically receives a valid prospective coverage/disposition state. |
| 13 | Trigger corrected/withdrawn after completion | Historical completed basis is unchanged; the Version is prospectively ineligible and correction/withdrawal may create new attention/Trigger. |
| 14 | Eligible requiring Trigger has no assignment | Coverage is explicitly `REASSESSMENT_REQUIRED_UNASSIGNED`; it cannot disappear from authoritative queries. |
| 15 | Reassessment completion | Exactly one atomic `COMPLETED_CONFIRMED` + Confirmation or `COMPLETED_SUCCESSOR_DECISION` + authorized successor path; zero/both are rejected. |
| 16 | First same-Decision Reassessment completes | Second does not auto-close. It prospectively revalidates D1/current context and coordinates before completion. |
| 17 | Successor Decision becomes effective while another is open | Open predecessor-bound work remains historical but cannot complete as current; explicit successor Reassessment/rebase and Trigger carry-forward are required. |
| 18 | Conflicting interim dispositions | Apply determinable restrictive intersection; if indeterminate, suspend affected scope. No operating-state ranking. |
| 19 | Explicit state value carried | Exact authorized state identity/value may be compared for equality/applicability; stronger/broader/priority inference is unavailable. |
| 20 | Trigger from existing/external source without Observation | Exact Evidence, Authority Gap, Intervention/Learning, Configuration, or external/human provenance may source a Trigger; no Observation record is created. |
| 21 | Queue priority/timestamp/severity suggests merge | It has no authoritative effect; merge is unsupported and coordination remains accountable. |
| 22 | Later role expiry or withdrawal | Routine later expiry does not rewrite valid historical action; withdrawal/supersession/revocation is prospective and blocks future reliance. |
| 23 | Duplicate/coordination action lacks authority | Action is blocked as accountability not established or conflict; software permission cannot substitute. |
| 24 | Management Register absent | Case-scoped Trigger selection, coverage, Reassessment concurrency, disposition, and completion remain deterministic from authoritative source records. |

## IRR dependency boundaries

### IRR-014

Increment 6 may store, carry, display, and validate equality/identity and exact authorized applicability of an operating-state value already present in a Decision or Interim Operating Disposition. It may accept an explicitly proposed state value for accountable analysis. It must not infer `stronger`, `broader`, `more restrictive`, escalation rank, automatic Trigger materiality, automatic grouping, or an automatic target state from labels, ordinals, configuration, or history. Any changed state is explicit and requires the governing successor/amendment Decision path.

### IRR-009

Allowed Trigger sources without Observation persistence are exact existing PAIM Evidence, Authority/Authority Gap, Configuration/version/currentness, Decision/Boundary, Intervention/Completion/Learning, correction/withdrawal, and explicit scheduled-review records, plus explicit human/external events with retained source identity/provenance and knowledge time. This artifact does not define Observation identity, versions, retention, cardinality, or automated conversion. IRR-009 remains deferred and is not required for a coherent explicit Trigger path.

### IRR-012

No Management Register entry, shared-dependency identity/equivalence, portfolio aggregation, concentration rule, cross-Case priority, or Register-driven workflow is required. Cross-Case Triggers share exact source provenance only; Case accountability and outcomes remain independent. IRR-012 remains deferred to Increment 7.

## Recommendation summary

### 1. Numbered human decisions and recommended v0.1 choices

1. **D1 — Trigger identity/source/duplication:** authoritative Case-scoped Trigger keyed to an established source occurrence and management question; exact replay only is deduplicated; updated source creates a successor Version.
2. **D2 — Cardinality/identity:** many-to-many relationships; every Reassessment Version binds an immutable exact Trigger Set; changed Decision/Configuration/substantive scope creates a successor Reassessment identity.
3. **D3 — Grouping:** no automatic semantic grouping; accountable exact-context grouping determination required.
4. **D4 — Concurrency/overlap:** allow explicitly non-overlapping concurrency; overlap or indeterminate scope is explicit conflict requiring accountable coordination.
5. **D5 — Merge:** no Reassessment merge in v0.1; use explicit coexistence/cancellation/supersession. Any future merge must create a history-preserving successor, never absorption.
6. **D6 — Supersession/cancellation/coverage:** no automatic closure; every action is accountable and atomically preserves/dispositions unresolved Triggers under the five-state coverage vocabulary.
7. **D7 — Status vocabulary:** adopt the nine statuses separating proposal, active analysis, authority wait, conflict, two completion paths, cancellation, and supersession.
8. **D8 — Concurrent completion/successor effect:** no auto-close; prospectively revalidate current context; stale-context work requires explicit successor Reassessment/rebase.
9. **D9 — Cross-Case propagation:** distinct Case-scoped Triggers sharing exact source provenance; independent Reassessments and outcomes.
10. **D10 — Accountability:** distinct Trigger Determiner, Reassessment Owner, and Reassessment Coordination Authority functions using fail-closed typed-target assignment/mechanism semantics; Decision Authority remains separately governed.

### 2. Rationale and rejected alternatives

The recommendations choose the narrowest v0.1 behavior that is deterministic, history-preserving, authority-first, and compatible with one governing Configuration per Case. Rejected alternatives are: mutable Trigger membership; semantic/text/time-window deduplication; automatic grouping; one-open-Reassessment bottlenecks; unrestricted concurrency; recency/severity winners; destructive absorption merge; automatic closure on a newer Decision/Configuration/row; global cross-Case Reassessments; administrator/Case-Owner permission shortcuts; and stale-context completion.

### 3. Dependency map

| Recommendation | IRR-009 dependency | IRR-012 dependency | IRR-014 dependency |
|---|---|---|---|
| D1 explicit Trigger intake | None; explicit PAIM/external provenance is sufficient | None | None; materiality is accountable, not ranked |
| D2–D8 Case-scoped Reassessment | None | None | None while state values remain explicit |
| D9 cross-Case source provenance | None; no Observation | None; no aggregation/equivalence | None |
| D10 accountability | None | None | None |
| Automated Observation ingestion | Deferred/blocked by IRR-009 | None | Conditional |
| Register-driven cross-Case workflow | Optional source only after IRR-009 if Observation projected | Deferred/blocked by IRR-012 | Conditional if prioritized by state |
| Stronger/broader-state automation | Optional source path only | Optional projection only | Deferred/blocked by IRR-014 |

No recommendation unexpectedly requires IRR-009, IRR-012, or IRR-014.

### 4. Governing files requiring later hardening

Primary owners:

1. `docs/system/specifications/PAIM_REASSESSMENT_SPEC_v0.1.md` — Trigger/Reassessment identities, many-to-many membership and Trigger Set, determinations, grouping, scope/concurrency, coverage, statuses, cancellation/supersession, completion revalidation, cross-Case source rule.
2. `docs/system/specifications/PAIM_CASE_LIFECYCLE_SPEC_v0.1.md` — relationship between multiple Reassessments and the single Case lifecycle, entry/exit guards, and no automatic closure.
3. `docs/system/specifications/PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md` — Trigger Determiner, Reassessment Owner, Coordination Authority, exact applicable typed-target sets, delegation, vacancy/conflict, and mechanism rules.

Conforming cross-specification updates only where needed:

4. `docs/system/specifications/PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md` — exact Trigger Set/membership history, current/coverage selection, semantic commit bundles, prospective completion guard.
5. `docs/system/specifications/PAIM_INTEGRATION_AND_DECISION_SPEC_v0.1.md` — effect of same-Decision concurrency and an effective successor Decision on open Reassessments.
6. `docs/system/specifications/PAIM_INTERVENTION_AND_LEARNING_SPEC_v0.1.md` — exact source handoff only; no redesign of accepted Increment 5 semantics.
7. `docs/system/testing/PAIM_SYSTEM_BEHAVIORAL_VALIDATION_STRATEGY_v0.1.md` — hard-oracle scenarios for cardinality, replay, grouping, coverage, concurrency, conflict, cancellation/supersession, and stale completion.
8. `docs/engineering/PAIM_PLATFORM_ARCHITECTURE_v0.1.md` and `docs/engineering/PAIM_IMPLEMENTATION_SEQUENCE_AND_P1_GATES_v0.1.md` — traceability/gate status after governing hardening is accepted, without duplicating normative semantics.

`PAIM_MANAGEMENT_REGISTER_SPEC_v0.1.md` does not need modification to close IRR-011 and remains under IRR-012.

### 5. Proposed Increment 6 gate sequence

1. PAIM design authority reviews and accepts/revises D1–D10.
2. A bounded specification-hardening issue updates the three primary owner specs and only necessary conforming contracts.
3. Add the 24 scenarios and negative/metamorphic dual-time cases to the behavioral validation contract.
4. Conduct an independent focused implementation-readiness re-review proving IRR-011 closed and IRR-009/012/014 boundaries preserved.
5. Reach a clean merged-main checkpoint.
6. Open a bounded Increment 6 implementation issue covering explicit Trigger intake, Reassessment identity/membership/status/concurrency, restrictive Interim Dispositions, Confirmation/successor outcome, persistence, and hard-oracle tests.
7. Exclude Observation persistence/automation, Register aggregation, operating-state ranking, generic workflow infrastructure, and follow-on increments.

## Gate conclusion

IRR-011 can be closed without resolving IRR-009, IRR-012, or IRR-014 if PAIM adopts the recommended Case-scoped Trigger identity, immutable many-to-many membership/versioning, accountable no-auto-grouping rule, bounded non-overlapping concurrency, explicit conflict and coordination, no v0.1 merge, no-lost-trigger coverage invariant, prospective completion revalidation, and distinct accountability functions.

The shortest safe path is design acceptance → governing-spec hardening → focused gate re-review → bounded Increment 6 implementation. No implementation should begin from this analysis artifact alone.
