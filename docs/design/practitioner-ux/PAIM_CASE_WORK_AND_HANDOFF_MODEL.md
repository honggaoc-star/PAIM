# PAIM Case Work & Handoff Model

## Purpose and boundary

This document defines the smallest Case-work and handoff model needed to coordinate PAIM management
work. It does not define a generic workflow engine, scheduler, messaging product, progress score, or
new domain record. Implementation requires the gates in the
[Architecture Feasibility & Gap Assessment](PAIM_PRACTITIONER_OPERATING_MODEL_ARCHITECTURE_GAP_ASSESSMENT.md).
The current [Roles and Accountability](../../system/specifications/PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md)
and [Integrity](../../system/specifications/PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md)
contracts remain controlling.

## Work model

PAIM should use two forms of work representation:

1. **Derived work** — a deterministic, current read of an authoritative PAIM condition, such as a
   ready Input missing one exact Applicability relationship. It is not persisted as task state.
2. **Durable Case Work Item** — an authoritative coordination record only when assignment, request,
   handoff, due time, return path, or completion history must survive sessions and participants.

The application must not persist a Work Item merely to mirror a domain status. Conversely, a
cross-practitioner assignment cannot be represented safely only as transient read composition.

## Minimal durable Work Item

A future Work Item should preserve:

| Field | Purpose and constraint |
|---|---|
| Work identity and Version | Stable, append-only coordination history; no overwrite on reassignment or cancellation. |
| Case | Exactly one owning Case. Cross-Case portfolio work requires an explicitly different contract. |
| Practitioner-readable task and obligation kind | Says what legitimate work is required without relying on a free-form title as semantic authority. |
| Context basis | Exact relevant Configuration, Evidence, Authority, Input, Fitness, Decision, Intervention, Trigger, Reassessment, or other Versions as required. |
| Responsible participant/responsibility | Exact accountable assignment or explicit vacancy/conflict; not inferred from access or authorship. |
| Requested/created by | Attributable Actor and legitimate assignment source. |
| Reason/prerequisite | Exact originating work or governed condition that made the work necessary. |
| State | Only justified coordination states: `ready`, `waiting`, `completed`, `cancelled`, plus explicit conflict/vacancy where needed. No percentage complete. |
| Time | Created/assigned/completed and optional due time; due time is not priority or authority. |
| Result link | Exact governed result Version(s), or an explicitly permitted unresolved coordination outcome. |
| Return relationship | The originating work/context to reconstruct when the prerequisite is satisfied. |
| History | Assignment, delegation, return, cancellation, and completion attribution with effective/recorded time. |

The exact names and schema are intentionally undecided. They require normative specification before
implementation.

## State and sequencing rules

### Ready

Work is ready only when its authoritative prerequisites are satisfied for the exact current context
and the responsible participant can legitimately attempt it. `Ready` is not permission, authority,
or a guarantee that the command will succeed; commit revalidates every guard.

### Waiting

Work is waiting when a named prerequisite, responsibility vacancy/conflict, inaccessible required
context, or another Work Item prevents it. PAIM must say what it is waiting for and must not choose
among independent prerequisites by rank or display order.

### Waiting on another participant

This is waiting plus an exact active responsibility/handoff. It should name the person and work in
authorized practitioner language without leaking hidden context. A notification is not proof that
the handoff exists.

### Completed

Completion requires the governed result specified by the obligation. Marking a Work Item complete
cannot create Applicability, Fitness, Selection, Authority, Decision, Intervention Completion
Acceptance, or any other substantive result. The Work Item links the committed result and returns
the originating context to current-state evaluation.

An explicit vacancy, conflict, or unresolved answer may complete only a coordination request whose
legitimate result is to establish that condition. It cannot satisfy a substantive prerequisite that
requires a judgment.

### Cancelled or stale

When authoritative context is superseded, access changes, the originating need disappears, or the
work is explicitly withdrawn, PAIM appends cancellation/supersession history. It never silently
retargets the Work Item to a newer Version. A replacement is a new or successor work Version with
an exact relationship.

## Turning prerequisites into work

For every blocked practitioner action PAIM should:

1. identify the exact authoritative prerequisite without ranking unrelated work;
2. determine whether it is already represented by derived work or needs durable assignment;
3. carry the exact Case/setup/assessment/information/purpose/return context;
4. show the responsible participant, or explicit vacancy/conflict;
5. allow an authorized assignment action only through the future responsibility contract;
6. render the receiving participant's work from the same authoritative context;
7. commit the required governed result through the owning domain command; and
8. reconstruct the originating work, which becomes ready only if all independent prerequisites are
   now satisfied.

Independent prerequisites remain independent. Completing one information Applicability judgment
does not complete another, does not establish Fitness, and does not select an Input.

## Harborlight prerequisite sequence

The live design test is:

```text
Value assessment recorded
  -> assessor declares exact Input ready
  -> support review identifies two exact missing information-to-Input judgments
  -> first judgment has no established responsibility
  -> originating support work waits; it is not failed or completed
  -> an authorized participant assigns the exact Applicability responsibility
  -> receiving participant sees the Case, proposed use, setup, Input, Evidence, purpose,
     requested judgment, requester, and return destination
  -> one governed Applicability result is committed
  -> the second independent prerequisite remains
  -> after both exact results exist, support review is reconstructed as ready
```

No participant reselects known Evidence, assessment, Configuration, or return route. No governance
phrase is typed into existence. Assignment does not decide the Applicability outcome.

## Handoff packet

The receiving practitioner should see, subject to access:

- **What is needed:** the ordinary-language judgment or work;
- **Why:** the exact originating prerequisite;
- **Where:** Case and proposed use/setup;
- **Relevant context:** only the Evidence, assessment, requirement, or other sources necessary for
  legitimate work;
- **From and responsible person:** attributable requester and assignment;
- **When:** due time only when legitimately established; and
- **Completion:** the governed result or explicit outcome that returns the work.

Raw Record/Version IDs, selection algorithms, compatibility keys, command names, and persistence
details stay in authorized history/technical inspection unless needed to understand a conflict or
consequential action.

## Notes and communication

PAIM is not general chat. A short bounded note may clarify a request, limitation, or return, but:

- the note is subordinate to the Work Item;
- it cannot alter context, responsibility, authority, or the substantive result;
- a conversation cannot be parsed into a governed decision automatically;
- important substantive content must be committed through the appropriate PAIM record; and
- access, retention, attribution, and history apply to notes as coordination records.

The initial model should omit conversation threads unless a demonstrated coordination need cannot
be met by structured reason, result, and return fields.

## Notifications

Notifications are derived delivery intents over Work Item changes. Candidate events are assignment,
material context change, return, block, completion, or cancellation. The authoritative state remains
the Work Item and governed records.

An in-app `Your work` surface may read current assigned work directly. Future email or Teams delivery
may carry a non-sensitive summary and deep link, but delivery success/failure cannot mutate Case
state. Duplicate delivery does not duplicate assignment; deleting a notification does not cancel
work.

## Conflict, access, and authority

- No responsible assignment produces explicit vacancy.
- Incompatible assignments produce explicit conflict; PAIM does not choose by specificity,
  recency, hierarchy, workload, or queue order.
- Access determines what can be seen/attempted, not who is responsible.
- Reassignment and delegation preserve exact predecessor/source history.
- Work assignment never creates Decision Authority or another separately governed authority.
- Hidden context is filtered before counts, labels, notifications, and summaries are composed.

## What PAIM should derive and what it should persist

| Need | Preferred representation |
|---|---|
| Current unmet domain prerequisite with no coordination history | Derived work from authoritative records |
| Current available independent Value/Risk work | Derived, unranked work |
| Cross-person request/assignment and return | Durable Work Item |
| Responsibility vacancy/conflict | Authoritative Responsibility resolution plus derived explanation; durable Work Item only if routing is requested |
| Substantive judgment/result | Existing owning-domain record, never Work Item content |
| Notification delivery | Non-authoritative delivery intent/event |
| Generic progress percentage or flowchart | Not supported |

## Acceptance rules for future implementation

A future implementation must prove exact context carry-forward, no hidden leakage, independent
prerequisite completion, stale/superseded cancellation, assignment vacancy/conflict, reassignment
history, governed-result linkage, return reconstruction, notification non-authority, and zero
creation of substantive results through task completion alone.
