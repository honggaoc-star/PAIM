# Pre-UX-1 Semantic Decisions

## Status and authority

This document is the semantic-design checkpoint required before UX-1. It reconciles the
[Harborlight Scenario-A findings](PAIM_HARBORLIGHT_SCENARIO_A_UX_FINDINGS.md) and the
[task-oriented UX design](README.md) with the authoritative PAIM system specifications. It does
not amend those specifications, authorize implementation, create a workflow status, or establish
new Harborlight facts.

The controlling sources are:

- [Managed Configuration Specification](../../system/specifications/PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md),
  especially §§4 and 18;
- [Case Lifecycle Specification](../../system/specifications/PAIM_CASE_LIFECYCLE_SPEC_v0.1.md),
  especially §§2 and 4–5;
- [System Record and Decision Integrity Specification](../../system/specifications/PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md),
  especially §§2–3, 5, and 6; and
- [Roles and Accountability Specification](../../system/specifications/PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md),
  especially §§2–3 and 11.

If an implementation cannot satisfy these decisions with existing production capabilities, it must
stop for separately authorized semantic or domain work. The UI must not manufacture the missing
meaning.

## 1. Governing Configuration and practitioner state language

### Decision

The formal governing relationship remains the one exact finalized Configuration Version governing
the Case at an effective time. It is current-basis identity, not authorization and not operation.
The UI must preserve five distinct questions:

1. What is the Configuration's maturity and history state?
2. Is this the governing Configuration for this Case and effective time?
3. What is its purpose?
4. Has an applicable Decision authorized an action?
5. What operating state, if any, has that Decision established?

Practitioner language may describe a Configuration as **current operating process** only when that
operating context is actually established; otherwise it must use a narrower truthful label such as
**comparison baseline**. Other permissible management labels include **proposed setup**, **pilot
under review**, **authorized**, and **operating**, but only when the exact corresponding state is
established. **Current Governing Configuration** is generally governance-trace language rather than
the primary practitioner label.

### Specification basis

The Managed Configuration Specification §4 makes record maturity, governing currentness, purpose,
authorization, and operating state orthogonal. Section 18 defines governing currentness for the
owning Case and effective time and prohibits choosing a winner by purpose, recency, authorization
date, or convenience. The Case Lifecycle Specification §§2.2 and 5 likewise separates lifecycle and
operating state and rejects a proposed or alternative Configuration as a substitute for the
governing Configuration.

### Harborlight rationale and required UX change

Scenario A compares C0, the manual-process comparison, with C1, the proposed eight-week pilot under
review. The primary view should therefore say **Manual process / comparison baseline** and
**Proposed eight-week pilot under review**. It may call C0 the **current operating process** only if
the read basis establishes that fact. C1's governing-currentness trace does not make the pilot
authorized, approved, deployed, or operating.

This revises the earlier shorthand in the findings and task flow without adding a baseline status.
The labels are read compositions over exact existing records and relationships.

### What does not change

No new Configuration purpose, status, currentness rule, Decision state, or operating-state inference
is introduced. The UI cannot repair governing absence or conflict by selecting C0 or C1.

### UX-1 checks and blockers

- Reconstruct the exact governing result for the Case and effective time: one Version, absence, or
  explicit conflict.
- Derive each practitioner label from established maturity, purpose, governing, authorization, and
  operating facts; never from the Configuration title alone.
- Keep the formal governing identity and reconstruction time in governance trace.
- Stop if production reads cannot distinguish the five dimensions without inference.

## 2. Case title and management question

### Decision

A Case title is a concise, stable navigation label for the continuing management subject. A
management question is the fuller question being managed and may be refined while Case continuity
is preserved. Configuration-specific duration, status, or outcome language does not belong in the
stable title.

For Harborlight, the proposed title is **Harborlight Assist — SBL Memo Preparation**. The fuller
management question remains: **Whether and how Harborlight should use AI assistance in
small-business credit-memorandum preparation.** The eight-week pilot belongs to the proposed C1
Configuration and task context, not the Case title.

### Specification basis

The Case Lifecycle Specification §4 lists Case title and provisional management question as
separate minimum entry information and permits refinement of the management question. The System
Record and Decision Integrity Specification §3 preserves stable Record identity across immutable
Versions and prohibits silently substituting a convenient semantic key for exact identity.

### Harborlight rationale and required UX change

The Scenario-A exercise showed that a sentence-length question is poor repeated navigation, while
the earlier proposed title was itself tied to one candidate pilot. Separating the concise Case label
from the question keeps navigation stable as C0, C1, or later Configuration history changes.

### What does not change

Display naming does not create a second Case identity, change the Case question, or make a
Configuration current. A title is not a substitute for exact Record/Version identity.

### UX-1 checks and blockers

The current production Case write contract and practitioner read model persist and expose one Case
`title`; they do not currently provide a separate durable Case management-question field. UX-1
therefore must:

- verify this limitation against the then-current production contract;
- use the persisted Case title as the authoritative navigation label;
- if helpful, derive a clearly labelled **non-authoritative display summary** only from visible
  existing content, without persisting or presenting it as the management question; and
- stop for an authorized domain change if UX-1 requires a separately durable or editable management
  question.

UX-1 must not silently split one persisted string into two authoritative fields or place the C1
eight-week duration into the durable Case title.

## 3. Required prerequisites, available work, and unresolved conditions

### Decision

The application does not persist or infer one generic `NEXT_TASK`. Its orientation is a deterministic,
access-filtered read composition with three distinct outputs:

- **Required prerequisite** — the unique unmet condition that blocks the practitioner's stated
  intended downstream action, when such a unique condition is established.
- **Available work** — the set of independent tasks the practitioner can legitimately undertake now.
- **Unresolved condition** — an absence, vacancy, stale basis, or conflict requiring attention, not
  itself a task completion or priority.

If Value and Risk work are both available, show both as unranked peer work. Do not route to Value
merely because it appears first in a lifecycle description. An attention count must not collapse
different task, prerequisite, and unresolved-condition meanings.

### Specification basis

The Case Lifecycle Specification preserves explicit guarded transitions, separate Value and Risk
inputs, and explicit absence/conflict. The System Record and Decision Integrity Specification §§2.2,
2.3, and 3 requires exact selection and no silent fallback; it does not authorize a UI workflow
status or priority. The Roles and Accountability Specification preserves Value/Risk independence
and requires vacancy and incompatible accountability to remain explicit.

### Harborlight rationale and required UX change

At the Scenario-A stopping point, reviewing known/unknown material, Value assessment, and Risk
assessment can be available concurrently. The earlier universal **earliest next task** wording hid
that parallelism and could imply that Value outranks Risk. The revised header and orientation show
available work as a set, then show a unique prerequisite only in the context of a blocked intended
action—for example, Integration requires both exact current lane selections.

### What does not change

No new workflow engine, task record, priority, readiness state, recommendation, attention score, or
automatic transition is created. Visiting a page never satisfies a task.

### UX-1 checks and blockers

- For every orientation item, identify the exact existing facts and deterministic rule supporting
  its category.
- Apply access filtering before composition and do not leak hidden work through labels or counts.
- Hard-test parallel Value/Risk availability, a unique downstream prerequisite, and unresolved
  vacancy/conflict as different outputs.
- Stop if the read model would need ranking, arbitrary tie-breaking, or a new persisted task status.

## 4. Disclosure and access boundaries

### Decision

The UX uses three disclosure layers:

1. **Practitioner workspace** — management meaning and ordinary task content; no raw Record/Version
   IDs, payloads, internal statuses, command references, or machine timestamps.
2. **Source, history, and governance basis** — understandable sources, limitations, prior versions,
   exact-basis categories, accountability, authority, and effective/knowledge context.
3. **Technical inspection** — machine identifiers, raw payloads, timestamps, relationships, and
   audit/command details for an authorized diagnostic or audit purpose.

Moving to a deeper layer must be explicit, reversible, and non-disruptive to the working task.
Disclosure depth never broadens software access or exact governed-context visibility.

### Specification basis

The System Record and Decision Integrity Specification §§3.1–3.2 requires exact Record and Version
identity and reconstructable history; it does not require raw machinery in the ordinary work view.
The Roles and Accountability Specification §3 separates technical principal, PAIM Actor, Role
Assignment, accountability, and Decision Authority. Visibility of a technical detail cannot create
any of those governed relationships.

### Harborlight rationale and required UX change

The Scenario-A exercise found that inline UUIDs and payloads displaced the practitioner task. The
revised layers retain full traceability for authorized users while keeping the management workspace
readable. **Source and history**, **Governance basis**, and **Technical inspection** replace the
ambiguous use of disclosure labels that implied one expansion exposed everything.

### What does not change

No identifier, source fact, global count, payload, or audit relation becomes visible merely because
the presentation has a deeper layer. Technical inspection remains separately access-enforced and
must fail closed without leaking existence.

### UX-1 checks and blockers

- Define access checks for every route and read before exposing counts, labels, links, or errors.
- Verify protected context is absent from all three layers when access is denied.
- Verify opening and closing detail preserves task state and causes no domain mutation.
- Stop if a shared read payload would expose technical or hidden context before authorization.

## 5. Quiet success and explanatory exceptions

### Decision

Satisfied machinery should be quiet when it is not management-significant. Ordinary pages need not
repeat successful authentication, software-access, exact-visibility, exact-binding, raw Actor-ID,
or command-ownership checks. They remain enforced and auditable.

At a consequential review or commit—especially authorization—the practitioner must see the
management meaning of the act: what will be established, who is acting, the responsible role, the
authority source, applicable scope, limits, conditions, and what remains unestablished.

An exception must explain:

1. which intended action is blocked;
2. what required fact is missing, stale, ineligible, or conflicting;
3. why the condition matters; and
4. which legitimate owning action or responsible role can resolve it.

### Specification basis

The Roles and Accountability Specification §§2–3 and 11 separates authenticated identity, software
permission, accountable Role Assignment, and substantive Decision Authority. A successful lower
layer cannot establish a higher one. The System Record and Decision Integrity Specification §§2.3
and 6 requires gaps/conflicts and complete authorization basis to remain explicit.

### Harborlight rationale and required UX change

Scenario A was dominated by successful control machinery before an intended action was attempted.
Quiet success restores task focus. Conversely, the separate Harborlight authorization checkpoint
must still name the Actor, Decision Authority role, fictional authority source, and its scope and
limits because those facts are part of the management judgment, not technical clutter.

### What does not change

Controls are not removed, weakened, or treated as implicitly satisfied. The UI never chooses a
winner for conflict or infers accountability or authority from identity, visibility, software
access, Case ownership, recency, or role hierarchy.

### UX-1 checks and blockers

- Demonstrate that quiet passed controls are still executed and reconstructable.
- Hard-test identity success with accountability vacancy, access success with authority conflict,
  and stale exact basis with zero mutation.
- Verify consequential confirmation retains action, Actor/role, authority source, scope, limits,
  and conditions in practitioner language.
- Stop if simplifying an exception would require choosing a resolution or hiding an exact conflict.

## UX-1 semantic gate

UX-1 may proceed only as a read-only orientation and vocabulary increment. It must demonstrate:

- truthful, separately derived Configuration maturity, governing, purpose, authorization, and
  operating language;
- stable Case-title behavior without fabricating a durable management-question field;
- deterministic separation of required prerequisites, available peer work, and unresolved
  conditions;
- three-layer disclosure with unchanged access boundaries; and
- quiet successful machinery together with management-complete consequential confirmation and
  explanatory exceptions.

These decisions narrow presentation choices; they do not weaken any hard constraint in the merged
task-oriented UX design.
