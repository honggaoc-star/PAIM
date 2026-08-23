# Harborlight Scenario-A Task Flow

## Purpose

This wireframe-level flow lets a competent practitioner work Scenario A without first learning the
PAIM object model. It uses only the supplied Scenario-A facts. It does not prescribe whether the
pilot should be authorized.

The flow is an orchestration proposal. Existing production commands, exact bindings, and separate
records remain controlling underneath, as detailed in the
[task-to-capability mapping](PAIM_TASK_TO_GOVERNED_CAPABILITY_MAPPING.md).

## Entry: Case orientation

### Header

```text
Harborlight Assist — Small-Business Lending Pilot
Harborlight Community Bank

Considering: an eight-week AI-assisted credit-memorandum pilot
Current position: evidence and independent assessments are not yet complete
Next: review what is known and unresolved
```

Secondary **Case context** reveals the full management question. **Governance trace** reveals Case
identity, C1 governing-basis details, lifecycle state, and reconstruction time. Neither is required to
understand the header.

### Orientation cards

```text
CURRENT PROCESS / COMPARISON BASELINE        PROPOSED PILOT UNDER REVIEW
Manual organization and drafting            Harborlight Assist document organization
Existing human review                        Two trained senior-underwriter teams
No generative-AI processing                  Standardized digital records
                                              Eight weeks; 100% QA
                                              No automated lending action

What needs attention
1. Review available information and known gaps
2. Assess potential Value
3. Assess Risk, uncertainty, and controls
```

The proposed pilot card must not say “current,” “approved,” “authorized,” or “operating.”

## Task 1: Understand what is being considered

The practitioner sees a concrete comparison grouped by:

- purpose and intended use;
- people and responsibilities;
- eligible applications and documents;
- duration and scale;
- required verification and quality assurance;
- prohibited actions and exclusions; and
- feasible comparison alternatives.

Action: **This is the setup I intend to assess**. If C1 is already uniquely established as the
Scenario-A basis, the action is shown as satisfied with “Change setup” available. The practitioner
does not reselect Case or Configuration IDs.

Confirmation language states that this identifies the setup for assessment; it does not authorize
the pilot.

## Task 2: Review what is known and unresolved

### What we know

Cards use management meaning, classification, and limitations:

- 46 of 50 standardized synthetic packages had materially complete source linkage;
- two unsupported draft statements were found and caught before memorandum completion;
- document-sorting time may fall by an estimated 20–35%; and
- a low-cost non-AI checklist alternative is immediately feasible.

Each card offers **Source and limitations**. That view shows the supplied-case source, whether the
item is observed or estimated, and its stated limitations. It does not initially expose UUIDs or raw
payload.

### What remains unknown

A visually distinct panel states:

- no live applicant outcome evidence;
- no end-to-end application-to-decision evidence; and
- two vendor-security control questions remain unresolved.

These are not styled as favorable evidence. The two security questions link to their unresolved
governance trace without inventing question content that the case does not supply.

### Requirements and decision authority

Plain-language cards show:

- autonomous lending action is prohibited;
- every material statement requires source verification;
- the named forum can authorize only the proposed pilot within the fictional charter; and
- individual lending decisions remain outside this management authorization.

The uniquely established fictional sources appear under **Why this applies**. Their technical
records remain under **Technical inspection**.

## Task 3: Decide what information matters here

The practitioner opens a source card in the context of **the proposed C1 pilot assessment** and
answers:

```text
Does this information bear on the proposed pilot?
( ) Yes
( ) Yes, under conditions or limits
( ) Only in part
( ) No
( ) I cannot determine this yet

What part of the proposal does it inform?
What conditions or limitations matter?
Why?
```

Known context—Case, C1 identity/version, source identity/version, Actor, and assessment time—is
carried and shown in the review step. The question does not preselect “Yes.” A list view then groups
explicit practitioner determinations by management question without implying that undetermined
sources are irrelevant.

## Task 4: Assess potential Value

Value opens in a full-width focused surface.

```text
Potential Value of the proposed pilot

What useful change could the pilot create?
For whom, and through what pathway?
Compared with the current process and the non-AI checklist, what could be different?
What evidence supports this view?
What remains uncertain or untested?
What does this mean for the proposed eight-week pilot?
```

The side panel contains available sources and explicit Applicability determinations. Adding a source
to the assessment does not create Applicability; if none is established, the UI asks Task 3 first.

Checkpoint A: **Review Value assessment** creates the analytical Input only.

Checkpoint B appears after an assessment exists:

```text
Is this assessment sufficiently supported for deciding about this proposed pilot?
Supportable / Blocked
What material evidence and limitations support that judgment?
Does unresolved uncertainty limit the Decision?
```

This preserves Fitness. It must allow a blocked conclusion.

Checkpoint C appears when one or more supportable assessments exist:

```text
Which Value assessment is management using for this Decision?
```

If only one supportable assessment exists, it is displayed as the candidate but still requires
explicit confirmation. If several exist, all eligible choices are shown neutrally. This preserves
Selection and non-selected history.

## Task 5: Assess Risk and controls

Risk is a separate full-width session with equal navigation status and independent state.

```text
Risk, uncertainty, and controls for the proposed pilot

What could go wrong, and who could be affected?
Which conditions or populations may behave differently?
What controls are proposed, and what do they actually address?
What evidence supports control adequacy?
What remains uncertain, including vendor-security questions?
What does this mean for the proposed eight-week pilot?
```

Risk uses the same three checkpoints—assessment, support/Fitness, and explicit Selection—but does
not inherit answers, readiness, or disposition from Value. Shared source material is presented as
available, not automatically Applicable.

## Task 6: Consider Value and Risk together

This task is unavailable until both lane selections are uniquely established and current. Until
then it says only, for example, **Select the Risk assessment management will use**, with a direct
link to that task.

When available:

```text
Management judgment

Selected Value assessment        Selected Risk assessment
[plain-language summary]          [plain-language summary]

Where do they reinforce one another?
Where do they conflict?
What trade-offs require judgment?
What uncertainty remains?
What alternatives remain credible?
Considering both independently developed assessments, what is your judgment?
```

The UI does not summarize into a score, recommendation, or automatic consensus. **Review management
judgment** commits Integration against the exact current selected bases.

## Task 7: Define operating limits and conditions

The surface asks what would have to be true if the proposed action proceeds:

- permitted use and users;
- eligible application/document scope;
- duration and review point;
- mandatory verification and quality assurance;
- prohibited actions;
- monitoring or evidence obligations; and
- conditions requiring stop or reconsideration.

The system may prefill concrete conditions already present in C1 as **proposal context**, but the
practitioner must review and explicitly establish the operating limits. Prefill does not convert the
Configuration into a Boundary. The resulting clauses and finalized Boundary remain separate records.

## Task 8: Propose an action

The proposal surface summarizes the current selected Value/Risk bases, management judgment, and
operating limits. It asks:

- What action is proposed?
- Why is it proposed now?
- What alternatives were considered?
- What conditions, dissent, or unresolved matters must remain visible?

Available outcomes include defer, request more evidence, decline, or propose an appropriately
limited action. The UI does not favor authorization. **Submit proposal for authorization** creates a
proposal only and labels it **Not yet authorized**.

## Task 9: Separate authorization

The authorization task appears only to an eligible Actor with visibility and software access. If one
current accountable Decision Authority assignment and one applicable authority source are uniquely
established, the UI binds and displays them:

```text
Who is acting: Harborlight Scenario-A practitioner
Responsible role: Decision Authority
Authority source: Fictional charter HCB-DA-03
Scope: management authorization of the proposed C1 pilot only
```

The Actor reviews the proposal and basis before choosing an authorized action. Zero eligible sources,
a vacancy, conflict, stale assignment, or insufficient scope stops the action and explains the
legitimate resolution path. The UI never offers arbitrary record selection to resolve ambiguity.

## Completion states

After each task, show what was established and what was not:

```text
Value assessment recorded.
Not yet established: evidence support for this use; management selection.
Next: confirm whether the assessment is sufficiently supported.
```

This wording prevents a progress indicator from becoming a readiness or authorization claim.

## Technical trace access

Every saved checkpoint has:

- **Source and history** — readable sources, limitations, author/Actor, and change history;
- **Governance trace** — exact basis categories, accountability, authority, effective and known time;
  and
- **Technical inspection** — full Record/Version identifiers and machine payload in a side panel or
  separate route with a clear return to the originating task.

No raw payload expands inline inside the primary assessment surface.
