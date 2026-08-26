# PAIM Practitioner UI Contract v1.0

## Status, authority, and interpretation

This document is the normative, implementation-independent practitioner UI contract for Gate 8
Slice H. It freezes the accepted product experience that Slice H must express over the
independently accepted Gate 8 Slices A–G.

The contract sits below the authoritative [system specifications](../../system/specifications/)
and the accepted prospective semantic contracts, and below the
[Product Design Foundation](PAIM_PRODUCT_DESIGN_FOUNDATION.md). It expresses those authorities
through the [Practitioner Operating Model](PAIM_PRACTITIONER_OPERATING_MODEL.md) and
[Practitioner-Language Standard](PAIM_PRACTITIONER_LANGUAGE_STANDARD.md). If a simpler UI would
conflict with an accepted semantic contract, the semantic contract wins and the conflict returns
to design authority. The UI must not reinterpret the contract for convenience.

In this document:

- **must** and **must not** state Slice-H requirements;
- **should** states the expected implementation unless evidence establishes a better conforming
  expression; and
- **may** identifies a permitted expression, never an inferred permission, Responsibility, or
  substantive authority.

This document authorizes no runtime change by itself. It does not begin Slice H, change Gates 1–6,
or modify an authoritative Harborlight environment.

## 1. Product-level UI contract

PAIM is a management tool for small and medium-sized organizations. Its visible structure is
organized around four practitioner questions:

1. **Home — What needs me?**
2. **Case — What is happening with this AI use?**
3. **Task — What do I need to do here?**
4. **History & decisions — What happened, what did we know, and why?**

Only **Home** and **Cases** are primary navigation. A Task is a contextual working state entered
from legitimate attention or Case work. History & decisions is inside one Case. The UI must not
create top-level navigation for Assessments, Value, Risk, Decisions, Reviews, Evidence,
Responsibilities, Work, Integration, Reliance, History, or Reports merely because those objects
exist underneath.

The governing interaction principle is:

> PAIM brings the right work, context, and evidence to the practitioner; the practitioner
> contributes judgment.

The governing value principle is:

> A structured paper trail, Decision auditability, and organizational memory arise largely as a
> by-product of useful management work, not as duplicate governance documentation.

There is no universal workflow dashboard, universal lifecycle phase, or authoritative persisted
master Case status. Technical and audit detail uses progressive disclosure rather than becoming
the default experience.

## 2. Home contract — What needs me?

Home is an access-filtered attention surface, not an activity dashboard. An ordinary attention
item contains only:

- the Case in recognizable language;
- what needs doing;
- why it needs attention;
- the natural action; and
- meaningful timing only when an exact visible fact justifies timing.

Home must not manufacture work, urgency, rank, priority, recommendation, or percentage complete.
Visual order must not imply any of those meanings. A date, event, vacancy, conflict, or changed
fact creates attention only under its accepted source contract; it does not create a substantive
Value, Risk, adequacy, Integration, or Decision conclusion.

When no exact visible source establishes legitimate attention, Home says:

> **Nothing currently needs your attention.**

This is a positive empty state, not a completeness or favorable-outcome claim. Home must remain
quiet rather than inventing setup work or generic improvement suggestions.

Level-1 Home must not expose internal Version IDs, Record families, semantic contracts or eras,
context digests, Assignment Basis, authority-source records, Reliance, Integration Records, Review
Episodes, selectors, source closure, transaction mechanics, or engineering diagnostics.

## 3. Case contract — What is happening here?

The Case is the central continuing management surface. Its ordinary composition should support,
when exact visible sources safely establish them:

- a concise purpose and description of the bounded AI use;
- **What needs attention**;
- **Current position**, with Value and Risk shown independently;
- the current Decision and its conditions or limitations;
- continuing review: last review, next planned review, and any visible governing requirement;
- **What has changed**;
- people and their responsibilities; and
- an entry point to **History & decisions**.

Current position is a derived, access-filtered presentation over authoritative facts. It is never
a newly persisted authoritative master status. It must preserve exact source identity, effective
time, knowledge time, absence, conflict, currentness, and append-only history underneath without
making those mechanics the ordinary page.

The Case must distinguish:

- **visible absence** — the authorized source population establishes that the fact is not
  established; and
- **status not safely available** — a required fact or its source closure is not safely visible or
  reconstructable.

A hidden fact must not become a false `missing`, `not started`, or `redo this work` instruction.
Hidden identities, relationships, counts, dates, conflicts, or successor existence must not leak
through labels, layout, action availability, or timing.

## 4. Task contract — Help me do this

Every ordinary practitioner task follows this shape:

1. **Why** — why the work is here and what management question it serves;
2. **What you need to know** — the minimum exact visible context and evidence needed for the act;
3. **Your judgment/action** — the genuine practitioner input or choice; and
4. **Finish** — a review of consequence, accountable/authority boundary where material, and the
   natural completion action.

Task context travels automatically from the authoritative Work/Case path. The practitioner must
not normally choose or enter Case, Configuration, assessment, or predecessor Version IDs;
semantic contracts; context digests; information-basis IDs; Responsibility, Assignment, Reliance,
or source-manifest IDs; or transaction members.

The UI must ask for confirmation only where confirmation is substantively required. It must
revalidate exact current context, access, Responsibility, accountability, and authority at review
and commit. A stale or tampered context fails closed without retargeting to a newer object.

Where accepted Work semantics already preserve a durable assignment, handoff, return path, or
restart, the task must support save-for-later and restart continuity from that persisted state. A
shell variable, browser-only identifier, or hidden route parameter is not continuity authority.

## 5. Progressive governance and just-in-time setup

PAIM asks for people, responsibilities, authority evidence, review timing, and other governance
information when that information becomes necessary for legitimate work. It must not impose a
large mandatory setup exercise merely because the data model can represent one.

Progressive setup does not weaken command-side requirements. Before an authority-bearing act, the
UI may help an authorized practitioner establish a missing legitimate input, such as an exact
Responsibility assignment or authority source. It must still:

- distinguish identity, software access, exact governed-context visibility, accountability, and
  substantive authority;
- expose vacancy or incompatible conflict rather than infer a winner;
- preserve source, scope, effective time, history, and any required independent actor boundary;
  and
- return to the original task from persisted Work/Case context.

The UI must not convert a practical role, Case coordination, authorship, seniority, proximity,
software permission, or visibility into accountability or substantive authority.

## 6. Independent Value and Risk contract

Value and Risk remain independent assessments, Responsibilities, judgments, histories, and
sources. Their visible experiences may share a consistent interaction pattern, but neither lane
may supply, rank, net, or choose the other.

An ordinary **Value** task asks:

- What improvement are we seeking?
- How could AI contribute?
- What information supports or limits that view?
- What measures or uncertainty are useful, if any?

An ordinary **Risk** task asks:

- What could go wrong or require attention?
- What conditions affect the Risk?
- What safeguards or controls matter?
- What information supports or limits that view?
- What measures or uncertainty are useful, if any?

Quantification is optional. The UI must not require a Value score, Risk score, universal composite
score, ranking, or Value-minus-Risk/net-benefit arithmetic. Quantitative claims appear
contextually inside the relevant assessment, continuing review, or history experience. They are
not a separate mandatory analytical module and do not determine adequacy, Reliance, Integration,
Decision, priority, causality, or success.

## 7. Adequacy contract

The practitioner question is:

> **Is this assessment adequate for the decision being made?**

Ordinary answers may be rendered as:

- **Yes** — mapped to the accepted `ADEQUATE` judgment;
- **No** — mapped to `NOT_ADEQUATE`; or
- **Needs revision** — mapped to `INDETERMINATE` where the accepted command contract applies.

The interaction includes comments, rationale, material limitations, and any required cause without
changing the governed outcome vocabulary underneath.

The UI must not ask whether the reviewer supports the Case, approves the Value or Risk, or finds
the Case sufficiently supported. Adequacy is the suitability of one exact assessment for one
bounded Decision use. It does not establish Reliance, Integration, Decision, or authority.

When one practitioner legitimately holds both independent review Responsibilities, the UI may
offer a combined review experience. The confirmation and transaction must still preserve two
separate lane judgments, exact sources, and failure behavior. A combined visible experience is not
a combined Value/Risk conclusion.

## 8. Reliance contract — expose choices, not mechanism

Reliance normally remains below Level 1. The UI must never present `Designate Reliance Version` as
ordinary practitioner work.

When exactly one eligible visible assessment can be carried into the next bounded action under the
accepted contract, PAIM should carry that exact assessment automatically. This is deterministic
context carriage, not an inferred substantive winner.

When multiple legitimate visible candidates require accountable choice, PAIM asks the business
question:

> **Which assessment should be used for this decision?**

The choice view shows the candidate assessments and their relevant visible bases and limitations,
requires rationale where the governing contract requires it, and records exact Reliance
underneath. It must not choose by recency, favorability, magnitude, owner, role, display order,
score, or convenience. Hidden candidates must not affect visible counts, labels, or conflict.

## 9. Integration contract

Integration has no standalone primary navigation item and normally no engineering-named screen.
The practitioner experience is:

> **Consider Value and Risk together for this decision.**

The experience presents the exact relied Value view and exact relied Risk view side by side,
preserves their independent conclusions and tensions, and asks for the bounded synthesis needed by
the Decision. The authoritative Integration fact remains separate, exact, current-basis-bound, and
historical underneath.

UI simplification must not collapse Integration into Decision. A lane change makes an old
Integration historical rather than silently current, and the UI must fail closed before proposal
or authorization if either relied lane basis changes.

## 10. Decision contract

The Decision surface is management-oriented and contains:

- what is being considered;
- a concise independent Value view;
- a concise independent Risk view;
- drill-down to exact visible assessments and evidence;
- Decision options in ordinary language;
- conditions and limitations;
- rationale; and
- the natural proposal, authorization, confirmation, or successor action that is legitimately
  available.

The UI must preserve proposal, authorization, unchanged-Decision confirmation, and successor
Decision as separate governed acts. Software permission to attempt an action is not the authority
to make it. Authorization revalidates the exact current Integration, Configuration, Responsibility,
Assignment, and substantive authority basis.

A Decision does not create a universal `approved Case`, `complete`, or operating state. Later
outcomes do not establish that the original Decision was right or wrong.

## 11. Continuing-review contract

After a Decision, the Case remains ongoing rather than finished. The Case may present:

- the last visible completed review;
- one practitioner-selected next Planned Review Point;
- separately visible governing Required Review Constraints; and
- exact visible event-based attention.

Common interval choices, a chosen date, or no planned date where permitted are convenience inputs,
not a universal cadence. A Planned Review Point is not a governing deadline. Required Review
Constraints remain separate and may intersect or conflict under their accepted contract.

Dates and accepted event facts create attention only. They never automatically create Value,
Risk, adequacy, Reliance, Integration, Decision, Trigger, Reassessment, or outcome conclusions.
When no legitimate attention exists, PAIM remains quiet.

## 12. Focused-review contract

Starting a continuing review shows:

- what changed or why review is occurring;
- relevant prior and current visible information;
- the areas that exact recorded facts indicate may need another look; and
- natural focused actions.

The UI must not force a full Value + Risk + Integration + Decision reassessment automatically.
Unaffected exact bases may remain current only under the accepted carry-forward and currentness
guards; they are not copied into new truth.

Mechanical attention must not become a substantive conclusion. For example:

> **Configuration changed; Risk review suggested.**

is permitted when exact recorded facts support that route. `Risk increased` is not permitted
without an independently governed Risk conclusion that establishes it.

Review Episode remains an internal governed concept unless Level-2 explanation or authorized
Level-3 audit disclosure needs the distinction.

## 13. History & decisions contract

History & decisions is organizational memory, not a raw audit database. Ordinary presentation
supports:

- a chronological narrative of Decisions, reviews, and material changes;
- each Decision and its rationale;
- **What we knew then**;
- **What changed since**;
- then-versus-now Value, Risk, Configuration, Integration, and Decision views;
- optional expected-versus-observed quantitative differences only when exact Slice-F
  comparability permits them; and
- drill-down to exact visible basis and provenance.

The experience must preserve effective-time and knowledge-time boundaries. A later-recorded fact
or successor must not appear at an earlier known-at cutoff. Every displayed historical claim and
successor must have complete visible source closure in the audit provenance. Hidden or
not-yet-knowable sources leave no identifier, count, label, conflict, date, or existence signal.

History must not infer hindsight error, Decision quality, causality, success, materiality,
priority, or that the original Decision was wrong. Expected-versus-observed arithmetic follows the
exact oriented Slice-F pair, compatible bases, current Comparability Version at the relevant
cutoff, and complete source-access contract.

## 14. Progressive disclosure levels

### Level 1 — ordinary use

Show business language and only the information required for the immediate practitioner judgment
or action. Prefer recognizable people, questions, evidence, choices, conditions, and dates.

### Level 2 — Why? / See basis

Show evidence and assessment detail, reviewer or accountable person, rationale, conditions,
meaningful dates, limitations, and what changed. Formal terms may be introduced when they prevent
a consequential misunderstanding.

### Level 3 — audit/provenance

For an authorized audit or diagnostic purpose, show exact visible Record and Version identities,
effective and known times, Responsibility, Assignment, Assignment Basis, authority source, source
manifest, and other technical provenance needed for reconstruction.

Access filtering applies independently at every level. A disclosure control is not authorization
to read a protected source. Level 1 must remain truthful when Level-2 or Level-3 sources are hidden.

> **Technical rigor must be available rather than inflicted.**

## 15. Practitioner-language contract

The following terms are prohibited from ordinary Level-1 UI unless the term is genuinely necessary
for the substantive judgment in front of the practitioner:

- Version;
- Record;
- semantic era;
- semantic contract;
- context digest;
- Assignment Basis;
- Reliance;
- Integration Record;
- Review Episode;
- projection;
- selector;
- currentness;
- source closure;
- transaction; and
- authority-source Version.

Prefer assessment, evidence or information, review, used for this decision, Decision, review date,
what changed, why, people, responsibility, history, and AI configuration or setup where those words
truthfully express the accepted source.

Formal vocabulary remains available at confirmation, history, dispute, and audit levels where its
distinction matters. Friendly wording must not rename an authoritative family, paraphrase authored
source content into a different claim, or weaken exact identity, access, accountability, authority,
dual-time, Value/Risk independence, or append-only history.

## 16. Slice-H burden acceptance tests

Every ordinary Slice-H screen and action must pass all six tests:

1. **Could PAIM already know this?** If yes, do not ask unless substantive confirmation is
   required.
2. **Does the practitioner need this for the judgment or action in front of them?** If no, hide it
   by default.
3. **Does this click create practitioner value or merely satisfy the data model?** Remove
   data-model clicks.
4. **Would a Word document, spreadsheet, or email be easier?** If yes, redesign until PAIM earns
   the burden.
5. **Can two independently governed actions be naturally combined for one legitimately authorized
   practitioner?** If yes, combine the visible experience while preserving separate authoritative
   facts.
6. **Does PAIM have anything useful to say?** If no, remain quiet.

Passing these tests never permits the UI to absorb a substantive judgment, choose an accountable
Actor, fabricate authority, or merge authoritative facts. The implementation must include
behavioral or human evidence appropriate to each ordinary screen/action.

## 17. Screen and interaction wire contracts

These wires define behavior and information burden, not pixels, component libraries, ordering
priority, or a new persisted state model.

### 17.1 Home with attention

```text
Home                                      Cases
What needs me?

Harborlight small-business lending
Review the updated Risk assessment
Why: the AI setup changed after the last Decision.
Review Risk

Harborlight small-business lending
Complete the required review by 12 Nov
Why: the governing review requirement has reached its attention window.
Start review
```

Timing appears only when justified. Card order does not rank the work.

### 17.2 Home empty state

```text
Home                                      Cases
What needs me?

Nothing currently needs your attention.
```

No generic setup, improvement, percentage, or `all clear` claim is added.

### 17.3 New Case minimal capture

```text
Start a Case

What AI use are you considering?
[Short purpose or management question]

What setup or scope should this Case begin with?
[Concise bounded description]

[Start Case]
```

PAIM establishes safe system facts through the accepted natural Case command. It does not ask for
IDs, contracts, digests, initial status, or a complete staffing/governance questionnaire.

### 17.4 Case current position

```text
Harborlight small-business lending
[What needs attention]

Current position
Value: Faster decisions may improve access; evidence and uncertainty available.
Risk: Fairness and verification limitations remain; safeguards available.

Current Decision
Proceed within the pilot limits
Conditions: human verification; lending cap; review date

Continuing review                 What changed
Last reviewed: 12 Aug             Configuration updated after Decision
Next planned review: 12 Nov

People & responsibilities         [History & decisions]
```

Every statement is derived from safely visible sources; this layout is not a master status.

### 17.5 Value assessment

```text
Assess potential Value

Why: management needs an independent Value view for this lending pilot.
What improvement are we seeking?       [text]
How could AI contribute?               [text]
What information supports this view?   [visible source choices / add information]
Measures or uncertainty (optional)     [contextual claim fields]

[Review and finish Value assessment]
```

### 17.6 Risk assessment

```text
Assess Risks and uncertainty

Why: management needs an independent Risk view for this lending pilot.
What could go wrong or need attention? [text]
What conditions affect the Risk?       [text]
What safeguards or controls matter?    [text]
What information supports this view?   [visible source choices / add information]
Measures or uncertainty (optional)     [contextual claim fields]

[Review and finish Risk assessment]
```

Neither lane displays a composite score or an implied conclusion from the other lane.

### 17.7 Combined adequacy review

```text
Review the assessments for this Decision

Value assessment
Is this assessment adequate for the decision being made?
( ) Yes   ( ) No   ( ) Needs revision
[Comments / material limitations]

Risk assessment
Is this assessment adequate for the decision being made?
( ) Yes   ( ) No   ( ) Needs revision
[Comments / material limitations]

[Review both judgments]  ->  [Confirm both judgments]
```

This wire applies only when the practitioner holds both exact Responsibilities. Two authoritative
judgments remain separate underneath and commit atomically only where the accepted contract allows.

### 17.8 Multiple-candidate business choice

```text
Which Value assessment should be used for this Decision?

( ) Assessment completed 10 Aug
    Expected improvement: ...
    Basis and limitations: ...
( ) Assessment completed 15 Aug
    Expected improvement: ...
    Basis and limitations: ...

Why this choice? [rationale]
[Use selected assessment]
```

The UI records exact Reliance but does not expose that mechanism or imply a preferred candidate.

### 17.9 Decision

```text
Decide how to proceed

What is being considered
[bounded AI use and setup]

Potential Value                  Risks and safeguards
[concise independent view]       [concise independent view]
[See assessment & evidence]      [See assessment & evidence]

Decision
( ) Proceed within stated limits
( ) Do not proceed
( ) Return for revision
Conditions and limitations [text]
Rationale [text]

[Review Decision proposal]
```

Proposal and authorization remain separate. The confirmation names the exact consequential act and
authority boundary in practitioner language.

### 17.10 Post-Decision review timing

```text
When should we review this Decision next?

( ) In 1 month   ( ) In 3 months   ( ) In 6 months
( ) Choose a date [date]
( ) No planned date [only when allowed]

Governing review requirement
Review by 12 Nov [See basis]

[Plan next review]
```

The chosen plan and governing constraint remain separate.

### 17.11 Event-triggered focused review

```text
Review a change to the AI setup

Why: the verification step changed after the current Decision.
What changed: [exact visible before/after description]
Suggested focus: Risk assessment

[Review Risk]  [See current Decision]  [Save for later]
```

The suggestion routes attention; it does not assert that Risk increased.

### 17.12 Scheduled review with optional observed result

```text
Review the lending pilot

Why: the planned review date has arrived.
What has changed since the Decision? [visible change summary]

Observed result (optional)
Metric and context [fields]
Value and period   [fields]
Source and uncertainty [fields]

[Continue focused review]
```

An observed claim is optional and establishes no comparison, causality, or outcome by itself.

### 17.13 History & decisions

```text
History & decisions

12 Aug — Decision authorized: proceed within pilot limits
          Why: [rationale]
          [What we knew then] [What changed since] [See basis]
20 Aug — AI setup changed
25 Aug — Focused review completed; Decision confirmed unchanged
          [See review and basis]
```

Chronology is access-filtered and dual-time-aware, not a raw table of Records.

### 17.14 What we knew then / What changed since

```text
Decision on 12 Aug                         Current position
Configuration: lending pilot C1            Configuration: lending pilot C2
Value: [then-bound view]                    Value: [current independent view]
Risk:  [then-bound view]                    Risk:  [current independent view]
Decision: proceed within limits             Decision: proceed within current limits
                                            Last review: no Decision change

What changed
- Configuration basis changed.
- Risk assessment basis changed.
- Expected 30%; observed 24% [only with exact visible comparability]

[See exact basis and provenance]
```

The view states mechanical, safely established differences only. It makes no hindsight, quality,
causality, or `wrong Decision` judgment.

## 18. Slice-H implementation boundary

Slice H must implement this practitioner experience against accepted Slices A–G. It may add
presentation, view-model, routing, template, and bounded integration support needed for the UI, but
it must not:

- weaken source-level non-disclosure or compose before access filtering;
- invent or persist an authoritative master Case status;
- collapse Value and Risk;
- collapse assessment, adequacy, Reliance, Integration, proposal, authorization, confirmation, or
  successor Decision;
- create identity, access, role, Responsibility, accountability, or authority shortcuts;
- invent workflow rank, priority, urgency, recommendation, or percentage complete;
- silently backfill or reinterpret legacy semantics;
- present hidden status as absent or ask a practitioner to repeat hidden completed work;
- expose technical mechanics to ordinary users merely because the internal command requires them;
  or
- add scheduler, notification, multi-user deployment, telemetry/Observation, analytics, mandatory
  quantification, universal scoring, or other post-Slice-H scope.

Slice H must carry authoritative context, use production commands and selectors, revalidate at
commit, preserve exact history, and fail closed with zero mutation on stale, inaccessible,
conflicting, vacant, or unauthorized context. Existing technical/audit detail remains available
only through separately authorized progressive disclosure.

## 19. Harborlight validation boundary

Harborlight Scenario A is the integrated runtime and usability validation Case for Slice H. Slice H
must use a fresh disposable prospective fixture authorized by its bounded issue and must preserve
all authoritative historical Harborlight facts and prior owner-review evidence.

The runtime study must exercise the accepted Gate-7 journey and Gates 1–6 conformance criteria over
the real Slices A–G production paths. It must include one-person and split-person paths where
authorized, restart/session-change continuity, stale/tampered-context failure, access and
non-disclosure, non-mutating legacy reconstruction, and the burden tests in §16. Human observations
must be recorded as observed without inference or embellishment.

Harborlight validation does not authorize destructive reinterpretation, fixture repair solely to
make the UI pass, a release verdict, organization-local deployment, or another Harborlight
scenario. Any blocker that would require changing accepted semantics returns to the issue/PR
handoff protocol before implementation continues.
