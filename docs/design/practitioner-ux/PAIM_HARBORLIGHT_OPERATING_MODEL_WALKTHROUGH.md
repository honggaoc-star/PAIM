# Harborlight Practitioner Operating-Model Walkthrough

## Purpose and evidence boundary

This walkthrough tests the proposed operating model against Harborlight Scenario A and
representative staffing arrangements. It does not mutate, repair, reset, or extend the preserved
Harborlight fixture. It records design expectations, not empirical validation or completed PAIM
judgments.

The design evidence is bounded by the recorded
[Scenario-A findings](PAIM_HARBORLIGHT_SCENARIO_A_UX_FINDINGS.md) and
[task flow](PAIM_HARBORLIGHT_SCENARIO_A_TASK_FLOW.md). Later Harborlight scenarios are not used.
The A–E labels below are Issue #123 operating-model acceptance paths, not Harborlight Scenarios B–E.

The current live stopping point remains:

- one Value assessment is recorded and ready;
- Value support review needs two independent information-to-Input Applicability judgments;
- the first contextual judgment has no eligible accountable assignment;
- the judgment remains unfinalized;
- Risk remains undeveloped; and
- no Role Assignment is invented to make the exercise continue.

## Scenario A — one-person small organization

### Staffing

Alex is the attributable participant and is practically the Case Coordinator and Assessor. The
organization separately establishes who may authorize the eventual Decision.

### Experience

1. Alex opens Harborlight and sees where the proposal stands, current unranked work, and unresolved
   conditions.
2. PAIM shows `Assess Value` and `Assess Risk` as independent responsibilities assigned to Alex,
   without requiring Alex to switch identities or impersonate two job roles.
3. Alex completes each analytical record separately. PAIM preserves independent sources,
   uncertainty, readiness, Fitness, Selection, timestamps, and attribution.
4. When an Applicability judgment is required, PAIM checks the exact responsibility. If Alex is
   legitimately assigned it, the confirmation shows Alex as responsible for that judgment. If not,
   the work remains vacant even though Alex authored the Value Input and can access the command.
5. The eventual authorization action resolves the separate Decision Authority basis. Alex's Case
   coordination and assessment work do not create it.

### Safeguards

Same-person staffing is visible, not treated as automatic independence or automatic conflict.
Value and Risk never share a record, score, Fitness, Selection, or acceptance shortcut.

## Scenario B — small team

### Staffing

- Morgan — Case Coordinator
- Priya — Assessor responsible for Value
- Luis — Assessor responsible for Risk
- Sam — security specialist participant for a contextual vendor-security review
- Dana — participant expected to decide, with separately governed Decision Authority

### Experience

1. Morgan sees Case coordination work and which analytical responsibilities are assigned, waiting,
   vacant, or conflicted.
2. Priya sees the Value task with the proposed pilot, setup, relevant supplied information, purpose,
   and legitimate completion checkpoints. Luis receives equivalent Risk context independently.
3. Priya reaches a vendor-security prerequisite and requests/assigns the exact contextual review to
   Sam through an authorized responsibility action.
4. Sam receives work that says what is needed, why, the Harborlight proposed use, relevant vendor
   information, the requesting participant, and what governed result completes the work. Sam does
   not receive an abstract `question 2` message.
5. Sam commits the appropriate governed result. The Work Item links it and returns Priya to the
   reconstructed Value support task.
6. Morgan can see coordination status but cannot change Sam's judgment. Dana acts only at the later
   Decision authorization checkpoint and only under the exact Authorization Basis.

### Safeguards

Notification delivery does not complete work. Morgan's coordinator role does not become authority.
Sam's specialist participation does not create a permanent specialist role or decide Value/Risk.

## Scenario C — current live stopping point

### Authoritative condition

The current Value assessor is ready to judge the first linked information item, but accountability
for that exact Applicability obligation is not established. UX-3B correctly fails closed.

### Desired operating-model path

```text
Value support review
  -> waiting for two independent information judgments
  -> first judgment: responsibility not established
  -> authorized Case participant selects Assign this work
  -> PAIM carries Case + proposed setup + Value Input + Evidence + purpose + assessed context
  -> responsibility is established through a governed, versioned action
  -> assigned participant sees contextual work
  -> participant makes and confirms the substantive Applicability judgment
  -> governed Applicability Version is authoritative
  -> Work Item completes by linking that Version
  -> PAIM reconstructs the originating Value support task
  -> second missing judgment remains independently waiting
```

At the current checkpoint only the conceptual path is approved for evaluation. PAIM has no accepted
Responsibility/Work contract or assignment UI, so the live Case must remain blocked. The existing
`Applicability Owner` resolver label is not promoted into a practical role.

### What must not happen

- the assessor must not type a governance phrase;
- Case Owner, Configuration Owner, Evidence Owner, Decision Authority, access, or authorship must
  not be treated as the missing responsibility;
- PAIM must not auto-assign the signed-in participant;
- completing one judgment must not complete the second or create Fitness/Selection; and
- the practitioner must not reconstruct Evidence, target Input, purpose, Configuration, or return
  destination that PAIM already knows.

## Scenario D — same participant, multiple responsibilities

Taylor is assigned both `Assess Value` and `Assess Risk`. PAIM presents one participant identity and
two clear pieces of work. Each has its own exact context and substantive confirmations.

The Case history shows Taylor's attribution and the separately established responsibility for each
lane. The organization can add an optional Reviewer or compensating review without pretending two
analyses were produced by different people. A later conflict-of-interest policy may be stricter,
but PAIM does not infer that policy.

The same pattern applies when a Case Coordinator is also an Assessor: practical-role consolidation
does not erase responsibility boundaries.

## Scenario E — vacancy and conflict

### Vacancy

PAIM says:

> This review needs someone responsible before it can be recorded.

An authorized coordination action may offer `Assign this work`. If no participant can establish
the responsibility, the work remains waiting with an explicit route outside the form. Software
access remains separate.

### Conflict

If two incompatible current responsibilities apply, PAIM says that responsibility is conflicting
and shows the legitimate resolution route. It does not select by narrowness, recency, job title,
seniority, display order, workload, or who is signed in. The substantive judgment remains
uncommitted.

### Authority conflict

A responsibility conflict and Decision Authority conflict remain different conditions. Resolving
who performs a review does not resolve who may authorize the Decision.

## Opening-the-Case acceptance test

Across these scenarios, a participant opening Harborlight should be able to answer quickly:

- What is being considered?
- Where does the Case stand?
- What work is mine and what is available independently?
- What is waiting, on whom, and why?
- Which information and requirements matter to the selected work?
- What will happen when I complete it?
- What remains for another participant or for authority?

The ordinary surface should not require knowledge of Record/Version IDs, command contracts,
compatibility keys, internal selectors, or the complete PAIM role taxonomy. Authorized history and
technical inspection still preserve that detail.

## Owner-review questions

1. Is the compact role vocabulary understandable for both one-person and small-team organizations?
2. Is the distinction between practical role, responsibility, and authority clear in each path?
3. Does the contextual handoff carry enough information without becoming a chat thread?
4. Does `waiting` explain the current Harborlight stop without ranking other available work?
5. Is an authorized `Assign this work` route the right practitioner concept before normative design
   defines its exact mechanics?
6. Which scenario, if any, requires a stronger separation-of-duties policy than PAIM's default?
