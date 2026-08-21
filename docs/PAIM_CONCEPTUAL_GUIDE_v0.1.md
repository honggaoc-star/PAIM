# PAIM v0.1 Conceptual Guide

Practical AI Management (PAIM) is a management system for making, carrying out, learning from,
and revisiting organizational decisions about AI-enabled uses. Its purpose is not to automate
management judgment. It is to make that judgment bounded, accountable, reconstructable, and
revisable.

This guide explains the complete PAIM management model in practitioner language. The governing
technical contracts remain the [PAIM System Architecture](system/architecture/PAIM_SYSTEM_ARCHITECTURE_v0.1.md)
and the [system specifications](system/specifications/). The released software is described in
the [PAIM v0.1 Practitioner Pathways](operations/PAIM_V0_1_PRACTITIONER_PATHWAYS_v0.1.md).

The recurring illustration is Aster Vale Regional Bank and its use of Navigator. Aster Vale is a
**constructed illustration**, not a real organization or empirical case. The starting facts come
from the working paper
[*Return-Weighted Risk for Navigating an Evolving AI Landscape*](https://github.com/honggaoc-star/AI-Risk-Management/blob/main/Return-Weighted-Risk/Return-Weighted-Risk-for-Navigating-an-Evolving-AI-Landscape.pdf).
Events added here to illustrate PAIM records and lifecycle behavior are expressly marked
**additional constructed PAIM extension**. Nothing in this guide is banking, lending, legal, or
regulatory advice.

## 1. Practical AI Management Problem

Organizations rarely face a decision about “AI” in the abstract. They face a more concrete and
less tidy question: whether a particular use, by particular people, in a particular workflow,
with particular data, controls, dependencies, and authority should begin, continue, change,
expand, pause, or stop.

The evidence does not arrive all at once. A pilot may show a clear task-level improvement while
leaving the intended organizational benefit uncertain. A system may remain inside its approved
technical function while people begin relying on it differently. A vendor update, a control
failure, a new alternative, or a change in organizational purpose may make an earlier decision
less relevant even though it was reasonable when made.

PAIM organizes continuing management around one question:

> **Given the evidence available now, what should an organization do about a particular
> AI-enabled use, why, under whose authority, what should happen next, and what would cause that
> decision to be reconsidered?**

That question is deliberately broader than “Is the model safe?” and more demanding than “Did the
pilot work?” It connects evidence to a defined use, separates Value and Risk analysis, exposes
uncertainty and constraints, requires accountable authority, translates a Decision into action,
and preserves the basis for later reconsideration.

### Who PAIM is for

PAIM is primarily for people responsible for making, supporting, implementing, overseeing, or
revisiting organizational decisions about AI-enabled uses. That includes business owners,
operational managers, AI and product managers, risk and control functions, governance and
compliance practitioners, and accountable decision makers. Researchers, evaluators, assurance
professionals, and system designers are important secondary readers because they may examine
whether the decision process and its evidence remain credible.

PAIM supports these people; it does not replace them. It can verify whether required identities,
records, relationships, and authority bases exist. It cannot decide what an organization ought to
value, determine that residual risk is acceptable, invent legitimate authority, or make a
management trade-off objective.

### The running illustration

Aster Vale Regional Bank completed a six-month pilot of Navigator, a vendor-developed generative
AI system. Navigator organizes documents and drafts portions of credit memoranda for
small-business loans. It does not approve or decline applications, assign credit ratings, set
prices, or communicate directly with applicants. Underwriters retain formal decision authority
and certify completed memoranda.

The pilot reduced underwriter preparation time by 28 percent. Application-to-decision time,
however, improved by only 7 percent. Repeated requests for information and applicant abandonment
improved little, and an improvement in credit access was not clearly established. A non-AI
workflow redesign remained a feasible alternative and produced a similar improvement in
end-to-end processing time. Management nevertheless wanted to consider broader use.

Those facts do not dictate a single answer. They make the management problem visible: what has
actually been learned, what remains uncertain, which proposed use the evidence supports, what
risks and controls apply, who may decide, and what action is justified now?

### A management position, not a permanent verdict

PAIM treats each answer as a position taken within a defined boundary and at a defined time. A
Decision can be well supported without being universally correct or permanently valid. A bounded
continuation can be appropriate while broader deployment remains unsupported. A suspended scope
can coexist with operation elsewhere. An unresolved question can remain visible while a
separately authorized action proceeds.

This makes PAIM different from an approval gate that ends when a committee says yes or no. The
important output is the complete management position: the exact use, evidence and uncertainty,
Value and Risk implications, constraints and alternatives, accountable authority, selected
action, operating boundary, implementation obligations, Learning, and reconsideration conditions.
Each part answers a practical question that someone must be able to defend later.

For a business owner, that means explaining why the use is worth doing and what result matters.
For Risk and control functions, it means preserving independent conclusions and the conditions
under which they hold. For a decision maker, it means owning the judgment among feasible actions.
For implementers, it means knowing what must change before operation. For assurance and oversight,
it means reconstructing the basis without relying on institutional memory.

## 2. Manage Configuration, Not “AI”

“Navigator” is too broad an object for a defensible management decision. The same underlying
product can have different consequences when the task, users, information, workflow, controls,
scale, operating conditions, or human authority change. PAIM therefore manages a **Managed
Configuration**: the bounded combination that describes the actual AI-enabled use.

For Aster Vale, a pilot Configuration might include Navigator’s document-organization and draft
preparation functions; small-business-loan memoranda; experienced underwriters; standardized
digital documents; required source access; human verification; restricted volumes; quality
assurance; and explicit exclusions from approval, rating, pricing, and applicant communication.
The Configuration also includes relevant vendor and model identity, dependencies, escalation,
and operating conditions.

The proposed expansion is not merely “more Navigator.” It may introduce less-experienced users,
larger loans, more varied records, reduced quality-assurance coverage, and a changed purpose. Each
change can alter the evidence that applies, the risks created, the controls required, and the
authority needed. PAIM does not allow a familiar product name to carry the pilot’s justification
silently into the broader use.

A Configuration has a stable Record identity and immutable Versions. The stable identity answers
“which managed use is this?” A Version answers “what exactly was that use at this point in its
history?” A substantive change creates a successor Version rather than editing the earlier facts.
If the change breaks identity continuity, the organization may need a different Configuration or
Case rather than a successor that pretends nothing fundamental changed.

This distinction protects both learning and accountability. The organization can compare what it
authorized with what later operated. It can ask whether evidence gathered under the pilot applies
to the proposed expansion. It can reconstruct why a Decision was reasonable without rewriting
the Configuration to resemble what happened later.

**Implication for Aster Vale:** the first practical task is not to classify Navigator as an AI
system. It is to define the exact Navigator-enabled activity that management is deciding about.
Evidence from one Configuration Version is not assumed to travel to another.

## 3. Management Is Evidence-Bounded

Evidence matters only within the boundary it can support. A measured reduction in memorandum
preparation time is evidence about that task under the pilot conditions. It is not automatically
evidence of faster lending decisions, reduced applicant burden, improved access to credit, safe
operation at a larger scale, or superiority over feasible alternatives.

PAIM registers Evidence with provenance and preserves judgments about its exact Applicability.
The system asks what the evidence is, where it came from, which Configuration or analytical input
it applies to, what question it bears on, and what limits or uncertainty accompany it. Acceptance
of evidence and a judgment that it is applicable are explicit governed events; a document’s
presence in a repository is not enough.

This makes several ordinary but consequential distinctions visible:

- evidence may be credible but not applicable to the proposed Configuration;
- evidence may apply only conditionally or partially;
- evidence may be current for one question and stale for another;
- two eligible applicability judgments may conflict;
- missing evidence remains missing rather than becoming a favorable default; and
- uncertainty about evidence is retained rather than converted into a convenient score.

An **Authority Gap** is also evidence-bounded. If the organization cannot establish the rule,
delegation, mandate, or authority needed for a governed act, PAIM records the question and its
unresolved state. The absence of an identified prohibition is not the same as established
permission. A later resolution becomes a successor Version; it does not erase the period during
which the question was unresolved.

Evidence maturity and Evidence Applicability are also different. A carefully produced study may
be mature evidence about a different population, workflow, or Configuration. A rough operational
signal may be directly relevant but too uncertain to support a strong conclusion. PAIM keeps both
dimensions visible because “high quality” is not a universal passport across scope.

The same discipline applies to acceptance and freezing of analytical inputs. An accountable
acceptance says that an exact input is eligible for its intended lane and purpose. Freezing makes
that Version immutable for later reliance. Neither event declares the conclusion true for all
future uses. If new evidence or a new Configuration changes the analytical position, the lane
produces a successor rather than altering the frozen input on which an earlier Decision relied.

At Aster Vale, the 28 percent preparation-time result can support a claim about preparation
efficiency in the pilot. The 7 percent end-to-end result limits the stronger operational claim.
The weak change in applicant burden and unclear credit-access result leave the original broader
Value rationale uncertain. Experience with standardized digital records does not, without an
explicit applicability judgment, support broader use on handwritten, scanned, multilingual, or
unconventional records.

**Implication:** PAIM does not reward evidence volume. It preserves the chain from a specific item
of evidence to the exact question, Configuration, analytical input, and Decision for which that
evidence is fit.

## 4. Value and Risk Are Different Questions

Value and Risk interact, but they are not two ends of one universal scale. PAIM keeps them as
analytically independent lanes because each asks a different question and can fail in a different
way.

The **Value** lane asks what organizational or stakeholder value the Configuration is expected to
create, through what pathway, under what conditions, with what costs and dependencies, and with
what uncertainty. It distinguishes a task-level output from a realized organizational benefit.
Saving preparation time is not itself proof that applicants receive faster decisions or better
access.

The **Risk** lane asks what adverse pathways and exposures remain for the same bounded
Configuration, which controls matter, where those controls apply, and what uncertainty remains.
It does not let an attractive benefit determine the Risk conclusion. Nor does a permissible Risk
position establish that the use is worth undertaking.

The lanes may use some of the same Evidence. For example, source-access data might inform Risk by
showing whether underwriters can verify drafts, and Value by showing whether verification work
consumes the expected time saving. Shared evidence does not collapse the questions or their
accountability. Each lane records its own finding, boundary, uncertainty, implication, and
provenance.

For Aster Vale, the Value lane can recognize the 28 percent task-level saving while questioning
the modest 7 percent end-to-end improvement and the similarity of the non-AI workflow
alternative. The Risk lane can examine document variation, source accessibility, junior-user
reliance, vendor dependency, and the effect of proposed scale and reduced oversight. A favorable
conclusion in either lane cannot repair an absence or conflict in the other.

This separation is especially important when organizational power is uneven. The sponsor of a
Value case may control resources and information, but that does not give the sponsor authority to
determine the independent Risk conclusion. Risk functions can challenge the use without becoming
owners of the business judgment about Value.

**Implication:** PAIM brings Value and Risk together only after each has produced a frozen,
traceable input. Integration may expose interaction, but it does not rewrite either lane to make a
Decision easier.

## 5. From Analysis to Management Judgment

Analysis informs a Decision; it does not make one automatically. PAIM’s Integration capability
assembles the exact accepted Value and Risk Input Versions with the governing Configuration,
Evidence, constraints, Authority and Authority Gaps, controls, dependencies, alternatives, and
uncertainty.

Integration first preserves what each lane says. It then asks how their implications interact.
Some findings reinforce each other. Some conflict. A mandatory constraint may remove an
alternative before trade-offs are considered. A control may reduce Risk while consuming time or
money needed for Value, or it may enable Value by making operation credible. A proposed use may
depend on evidence that is mature only for a narrower boundary.

The result is an **Integrated Operating Boundary Snapshot**: an immutable representation of the
structured references and narrative conditions within which a proposed Decision would operate.
It can include users, tasks, information, volume, controls, exclusions, escalation, human
authority, time limits, and other clauses that cannot responsibly be reduced to a number.

The Boundary Snapshot matters because management rationale is often conditional. “Continue” may
mean continue only for experienced underwriters, standardized digital records, specified volume,
direct source access, retained quality assurance, and a scheduled review. If those clauses live
only in meeting minutes, a later operator may see the Decision label but miss the conditions that
made it defensible. PAIM binds the conditions to the Decision as an exact governed object.

Alternatives remain explicit. For Aster Vale they might include ending Navigator use, continuing
the pilot Configuration, conducting a more targeted learning stage, redesigning the non-AI
workflow, adopting a narrower automation, or proposing a broader Navigator Configuration. PAIM
does not rank those alternatives with a universal score. It makes the differences and their
evidence visible so an accountable decision maker can judge them.

The Aster Vale illustration originated in Return-Weighted Risk (RWR), one reasoning architecture
relevant to this problem. RWR asks whether reconnecting an evolving Value case with an
independently assessed Risk case changes governance reasoning. It proposes sequential questions
about admissibility, Risk permissibility, and Value justification and keeps feasible alternatives
live. PAIM’s role is different: it manages how Evidence, Value, Risk, uncertainty, accountability,
authority, Decisions, action, Learning, and reconsideration are represented over time. PAIM does
**not** implement RWR or empirically validate it, and PAIM Integration is not RWR’s three tests.

The RWR research agenda suggests comparing four observables when practitioners reason through a
case: the evidence requested, dependencies identified, management rationale, and disposition.
PAIM can preserve those observables in an accountable management history. That preservation does
not prove that RWR, PAIM, or any particular method improves real-world outcomes.

**Implication:** the output of Integration is decision-ready context, not a mechanically correct
answer. Management Judgment remains explicit and accountable.

## 6. A Decision Requires Accountability and Authority

A person’s ability to click or submit a command is not authority to make the underlying Decision.
PAIM separates five layers that organizations often blur:

1. **Identity** establishes the authenticated principal and its current mapped Actor. Knowing who
   is acting does not give that Actor permission to attempt a command or authority to decide.
2. **Software access** establishes `COMMAND` permission to attempt the exact action at the required
   scope. It does not make the governed Case or Configuration visible.
3. **Exact governed-context visibility** establishes `CASE_READ` access to the owning Case and,
   when applicable, `CONFIGURATION_READ` access to the exact Configuration. Visibility permits the
   Actor to see the context needed for the command; it does not permit mutation or create authority.
4. **Accountability** identifies the eligible current Actor or organizational mechanism responsible
   for the typed target and particular obligation.
5. **Substantive authority** establishes that the Actor or mechanism may perform the governed act
   for the exact scope and time through the applicable Authority or Authorization Basis.

Each applicable layer must be established in its own right. Generic administrator status or broad
command permission does not supply exact Case or Configuration visibility. A role label, recency,
seniority, or software permission cannot fill a missing authority link. Where accountability is
absent,
PAIM records a vacancy. Where incompatible eligible assignments coexist, it records an explicit
conflict. It does not choose a winner by specificity, breadth, recency, role hierarchy, or software
permission.

An authorized Decision binds its exact Configuration Version, frozen Value and Risk Inputs,
Integration, Boundary Snapshot, evidence and uncertainties relied upon, conditions, rationale,
effective time, Actor, and **Decision Authorization Basis**. The Authorization Basis makes the
authority chain auditable for that Decision and scope. If required decision authority is
unresolved, the Authority Gap blocks authorization. A valid narrower Decision may proceed only if
its own complete authority covers the bounded determination; it cannot borrow permission from an
unresolved broader question.

Accountability is obligation-specific. The Actor accountable for preparing a Value input need not
be the Actor accountable for accepting completion, determining a Trigger, coordinating overlapping
Reassessments, or authorizing activation. One person may legitimately hold more than one role, but
each applicable assignment and authority relationship must exist for the exact act. PAIM avoids
both extremes: it does not require a different human for every step, and it does not treat one
general “owner” label as authority for everything.

Conflict is not solved by hiding one assignment. If a Case-scoped and Configuration-scoped
accountable assignment are both applicable to an exact obligation and no valid displacement or
delegation resolves them, the result is conflict rather than an implicit preference for the more
specific scope. That may create procedural work, but it preserves the organization’s actual
governance problem.

For Aster Vale, underwriters’ authority to make lending decisions is part of the Configuration
boundary, not proof that an executive may authorize broader Navigator deployment. The expansion
Decision needs its own accountable decision maker and valid organizational authority. Likewise,
the people who prepare Value or Risk inputs do not acquire Decision authority by contributing
analysis.

**Implication:** PAIM can show that a Decision is mechanically complete and linked to an eligible
authority basis. It does not declare that the organization’s authority source is legitimate as a
matter of law or policy; that remains an organizational judgment and responsibility.

## 7. A Decision Is Not Yet Operation

Authorization states what management has decided. It does not prove that the target Configuration
has been implemented correctly or may begin operating immediately. PAIM therefore separates the
Decision from **Intervention**, **Completion Result**, **Completion Acceptance**, prerequisite
evaluation, and **Activation Authorization**.

An Intervention translates judgment into concrete change. It identifies what must be done, by
whom, for which Decision and target Configuration, under what conditions, and with what prohibited
activities, fallback, remediation, and escalation. Required work might include restoring source
access, retaining quality assurance, changing training, limiting users, or creating a comparison
with the non-AI workflow.

A Completion Result records what the implementer reports happened. It does not accept its own
adequacy. Completion Acceptance is a separate accountable judgment about whether the exact result
satisfies the exact obligation. The Intervention owner cannot self-accept merely by being the
owner; the Actor must also hold the applicable Completion Acceptor relationship.

Required-before obligations use an explicit all-of rule. One incomplete required-before item
continues to block activation. An explicit empty required-before set means `NOT_REQUIRED`; an
absent obligation set means `NOT_ESTABLISHED`. Required-after and optional work have their own
effects and are not silently treated as required-before.

Even complete and accepted prerequisites do not themselves activate the Configuration. Activation
requires an exact **Prerequisite Evaluation Basis** and **Activation Authorization**, or a genuine
pre-authorized organizational mechanism whose rule, Version, scope, authority, and guards were
already established. A software checklist is not such authority.

This chain also protects against scope drift during implementation. A result completed for the
pilot Configuration does not satisfy an obligation for an expansion Configuration merely because
the task description sounds similar. A Completion Acceptance tied to one Decision cannot silently
carry to its successor unless the governing contract’s continued-validity criteria are explicitly
met. Required controls are therefore not reusable tokens; their satisfaction remains bound to the
Decision, Configuration, obligation, evidence, and time for which it was accepted.

**Additional constructed PAIM extension:** Aster Vale’s accountable Decision authorizes only a
controlled next stage. Required-before obligations include restoring direct source access,
retaining quality-assurance coverage, and configuring the approved user and document scope. Each
Completion Result is separately accepted. Only then does an authorized Actor activate the exact
target Configuration. This extension illustrates PAIM; it is not a fact reported by the RWR paper.

**Implication:** “approved” and “operating” are not synonyms. PAIM preserves the operational work
and authority needed to cross that boundary.

## 8. Learning Without Rewriting History

Learning matters because evidence changes. It must not make the past appear wiser than it was.
PAIM links Learning to the Decision, uncertainty, Configuration, Evidence, and action that produced
it while preserving the historical records that existed before the result was known.

A Learning Item should be decision-specific: what question must be answered, what evidence will
be generated, which current limitation or uncertainty it addresses, and which future Decision
could change. “Gather more data” is not enough. If the answer could not alter a management action,
the activity may be monitoring, research, or recordkeeping rather than decision-relevant Learning.

**Additional constructed PAIM extension:** Aster Vale creates Learning Items for whether restored
source access remains usable under ordinary workload, whether less-experienced underwriters can
verify Navigator drafts without excessive reliance, and whether Navigator creates incremental
end-to-end value over the non-AI workflow redesign. These are constructed PAIM records, not events
reported in the RWR paper.

When results arrive, PAIM records them with provenance. A result can strengthen a future Value
case, change Risk understanding, resolve an uncertainty, or show that a control dependency does
not hold. It does not amend the frozen Value or Risk Input, the earlier Boundary Snapshot, or the
authorized Decision. A later analytical input or Decision requires a successor Version and the
normal accountable process.

This preserves an honest sequence:

```text
what was known → what was authorized → what was done → what was learned → what was reconsidered
```

**Implication:** PAIM treats Learning as new evidence for a future judgment, not as permission to
retrofit the previous judgment.

## 9. Circumstances Change: Trigger and Reassessment

Not every new event should reopen a Decision, but every material event needs an explicit route to
that judgment. PAIM distinguishes an external occurrence or supported source event, a **Trigger**,
a **Trigger Determination**, and a **Reassessment**.

In released v0.1, an external occurrence is first preserved as proposed intake with its source
identity, version, replay identity, payload checksum, Case and Configuration context, and other
provenance. It is not automatically a Trigger, and PAIM does not fabricate an Observation record.
An accountable practitioner explicitly promotes the exact intake when it should become a Trigger.

The Trigger states the management question raised by the event and binds the current Decision and
Configuration context. A Trigger Determiner then records whether Reassessment is required. That
determination is a governed judgment, not a keyword rule. If Reassessment is required, it is
created explicitly and binds the exact Trigger Determination, Trigger set, Decision Version, and
Configuration Version. No Reassessment appears automatically.

This staged path protects against two opposite errors. Automatic promotion could turn every
operational signal into a governance event, creating noise and accidental semantics. Informal
screening could let a material event disappear without accountable disposition. PAIM preserves
the source first, then requires explicit judgment at promotion and determination boundaries. The
organization can therefore see both what arrived and what it decided to do about it.

Replay identity is part of this protection. Resubmitting the exact same external occurrence can
be recognized without creating another substantive event, while a genuinely different occurrence
is not deduplicated merely because it looks similar. Neither replay nor distinct intake triggers
automatic promotion. Provenance identity and management judgment remain separate.

**Additional constructed PAIM extension:** After the controlled Aster Vale stage begins, a vendor
release changes how Navigator presents source links, and internal review finds a material decline
in accessible source references for a subset of memoranda. Aster Vale preserves the external
occurrence, promotes it to a Trigger without creating an Observation, and asks whether the exact
current Decision requires Reassessment. An accountable Trigger Determination concludes that it
does. This entire event sequence is a constructed PAIM extension.

Triggers can also arise from Configuration change, a control failure, an Authority Gap resolution
or change, completed Learning, a material error, a provider change, a boundary breach, a scheduled
review, or another supported human or external source. The source must remain exact and
traceable. Similarity does not create provenance.

**Implication:** change does not silently invalidate or revise a Decision. It creates an explicit,
owned question about whether the Decision should be reconsidered.

## 10. Managing Concurrent Change

Real management does not wait politely for one issue to finish before another appears. Two
Triggers may concern the same Decision; one Reassessment may cover several Triggers; or two active
Reassessments may overlap. PAIM represents that concurrency rather than selecting an implicit
winner.

Each Reassessment has exact immutable Trigger membership and exact Decision and Configuration
context. Grouping or declaring duplicate coverage requires an accountable determination. Overlap
between active Reassessments is evaluated against their exact current Versions. If coexistence,
grouping, cancellation, or supersession is not established, the overlap remains explicitly
unresolved. Recency and row order are not coordination rules.

Coordination also does not merge the underlying questions. A coexistence determination can say
that two Reassessments may proceed together while preserving their distinct Trigger membership,
owners, evidence needs, and outcomes. Grouping can create one coordinated unit only through an
explicit accountable basis. Supersession and cancellation likewise require governed meaning; a
status change cannot imply that Trigger coverage moved somewhere else.

**Additional constructed PAIM extension:** While Aster Vale reassesses source accessibility, a
separate completed Learning result raises a question about less-experienced underwriter reliance.
It becomes a second Trigger and Reassessment. The two Reassessments overlap because they concern
the same authorized use and human-verification boundary. An accountable coordinator determines
that they may coexist, with separate Trigger membership and coordinated evidence work. This is a
constructed PAIM extension.

Operation may continue during Reassessment only under the exact current Decision, Boundary
Snapshot, Configuration, and any valid **Interim Operating Disposition**. A disposition can narrow
or suspend an affected scope, require controls, prohibit actions, or otherwise restrict operation
within its authority and effective period. It cannot broaden the authorized boundary.

When multiple dispositions affect a scope, all explicit restrictions are combined through exact
scope intersection. If their combined operating-state effect is indeterminate, PAIM suspends only
the affected scope. It does not invent a strongest state, severity ordering, priority ranking, or
escalation rule. Unaffected scopes are not unnecessarily suspended.

**Implication:** concurrency is governed through exact membership, explicit coordination, and
restrictive operating protection—not through hidden precedence.

## 11. Completing Reassessment

A Reassessment is complete only when it produces an accountable outcome. Accumulating analysis
or reaching an internal milestone is not enough.

As work advances, each substantive Reassessment change creates a successor Version linked to its
predecessor. If overlap continues, coordination is reconsidered prospectively against the exact
new current Versions; a determination about predecessor Versions is not silently reused.

Completion takes one of two broad forms. The organization may confirm that the existing Decision
remains valid on the reviewed basis, or it may create an authorized successor Decision when the
conditions or management judgment change. A confirmation identifies the accountable Actor,
assignment and authority basis, exact reviewed records, Decision Version, Configuration Version,
and completed Reassessment Version. A changed outcome requires a real successor Decision with its
own complete Authorization Basis; PAIM does not fabricate one from a completion status.

**Additional constructed PAIM extension:** Aster Vale completes its source-access Reassessment
after reviewing the exact current Configuration, Decision, Boundary, Value and Risk inputs,
Intervention evidence, and relevant Learning. If the accountable decision maker confirms the
bounded Decision unchanged, PAIM records a completion confirmation and satisfied Trigger
coverage. If the operating boundary must change, Aster Vale instead authorizes a successor
Decision. Both possible outcomes are constructed PAIM extensions.

Trigger coverage is explicit. A completed Reassessment satisfies only the exact Triggers it
covers under the accepted membership and coordination rules. Historical Reassessment Versions,
earlier overlap states, interim dispositions, and completion basis remain reconstructable.

**Implication:** completion closes an exact reconsideration obligation. It does not erase the
Trigger, overwrite history, or imply that unrelated concerns are resolved.

## 12. Managing Across Cases

Individual Cases are authoritative for their own Configurations and concerns, but management also
needs to see patterns across Cases. The **PAIM Management Register** is a derived view for that
purpose. It surfaces current attention, conflict, informational and historical concerns,
intervention and Reassessment status, Evidence condition, and contextual next actions without
becoming a competing source of truth.

Every Register concern retains its owning Case, applicable Configuration, authoritative source
family, stable source Record, exact selected Version or conflict candidates, time basis, and
lifecycle state. A current view is therefore a selection over authoritative records, not a copied
spreadsheet row that can drift independently.

Cross-Case grouping is deliberately strict. Two Cases may mention the same vendor, model, control,
or similar issue without having an established Shared Dependency. PAIM groups them only through
an exact **Dependency Candidate Set** and an accountable current `EQUIVALENT` determination that
creates or supports the Shared Dependency identity. The group is descriptive. It does not transfer
Evidence applicability, authority, satisfaction, closure, outcome, or ownership among Cases.

Register lifecycle labels describe source state rather than importance. A current-attention entry
is not inherently more severe than a current-conflict entry, and a historical entry does not lose
its evidentiary value. A stale projection is marked stale against its authoritative high-water
mark; it is not eligible as fresh authority for a guarded command. These rules let the Register be
useful for navigation without turning layout or refresh timing into governance.

The same principle governs counts. A complete authorized view may show exact constituent counts.
An access-filtered view must not reveal hidden Cases indirectly through a “total” or group size.
It can show the visible constituents and state that access filtering occurred. Non-leakage is part
of the management semantics, not merely a user-interface preference.

**Additional constructed PAIM extension:** A second Aster Vale Case concerns Navigator in a
different internal workflow. Practitioners suspect that both Cases depend on the same source-link
service. PAIM first preserves the exact candidate members and then records an accountable
equivalence determination. Only then may the Register show a Shared Dependency group. A third
Case with similar wording but no established equivalence remains ungrouped. This is a constructed
PAIM extension.

Access filtering applies before practitioner-visible output. A filtered view does not reveal
protected identifiers, facts, or global constituent counts through group summaries. It states
that filtering occurred rather than implying completeness.

**Implication:** the Register helps management notice and navigate concerns across Cases while
leaving each owning domain authoritative.

## 13. Returning Action to the Owning Domain (`ASSIGN_OWNER`)

A management view can show that action is needed without becoming authorized to perform that
action. PAIM makes this boundary explicit through contextual Register actions.

Suppose an unresolved Aster Vale Authority Gap appears in the Register with no eligible owner.
Selecting `ASSIGN_OWNER` does not cause the Register to assign someone. It returns the exact source
Record and Version context, owning family, and the owning-domain Role Assignment command
contract. The practitioner then performs that Role Assignment through its normal software-access,
accountability, and authority checks.

The distinction prevents a dashboard from becoming a hidden governance engine. Register
presentation cannot transfer substantive authority, mutate the source concern, close it, declare
its evidence sufficient, or decide its priority. Generic Register resolution is unsupported in
v0.1 because different concern families have different governing semantics.

**Additional constructed PAIM extension:** Aster Vale’s cross-Case Register highlights an
unowned source-access Authority Gap. `ASSIGN_OWNER` launches the exact authority-domain Role
Assignment context. The Register itself changes nothing. This is a constructed PAIM extension.

**Implication:** PAIM uses the Register as a source-traceable route back to accountable work, not
as a shortcut around it.

## 14. Time, Identity, and Reconstruction

Continuing management requires more than keeping the latest row. PAIM distinguishes stable Record
identity, immutable Version identity, effective time, and recorded or knowledge time.

**Effective time** asks when a Version applies in the managed world. **Recorded time** asks when
PAIM learned or recorded it. A knowledge-time cutoff reconstructs what PAIM could have known at a
particular point. These dimensions differ when a fact is recorded late, corrected, backdated, or
made effective in the future.

For example, Aster Vale may record in September that a control condition had changed in August.
An effective-time query for late August can show the condition as applicable, while a
knowledge-time query made as of August must not pretend the September record was already known.
Both views are legitimate answers to different questions.

Current selection is deterministic for a declared record family, exact subject or scope, purpose,
effective time, and optional knowledge cutoff. No eligible record means explicit absence.
Incompatible eligible records mean explicit conflict. PAIM does not use “newest wins,” storage
order, or a broad semantic key as a hidden tie-breaker.

A stable `question_id`, for instance, can identify the governed question shared by successive
Authority Gap Versions. It cannot identify which exact Version supplied the historical state.
Reconstruction therefore starts from persisted exact Record and Version IDs, verifies their
relationships and time intervals, and follows explicit supersession, correction, status, and
membership records.

Corrections and supersession answer different historical questions. A correction can establish a
new Version that properly represents the record while preserving the erroneous predecessor and
the time at which it was known. Supersession establishes a prospective successor position. A
withdrawal can end eligibility without pretending the record never existed. Status events can
change lifecycle state without rewriting substantive content. PAIM retains these distinctions so
“what happened to the record?” is answerable without interpreting an overwritten row.

This becomes especially important during Reassessment. A practitioner must bind the exact current
Reassessment Versions when evaluating overlap and the exact Decision Version when confirming an
outcome. A broad Case ID or management question may locate the family of records, but it cannot
prove which Version controlled the act. Persisted result artifacts carry those exact identities
across operational stages so shell-session memory is not the continuity authority.

This identity discipline supports audit without making audit the only purpose. It also lets a
practitioner answer ordinary management questions accurately: Which Configuration did we
authorize? Which evidence did we have? Which authority was current? When did we learn about the
change? Which Decision was actually operating?

**Implication:** PAIM preserves both the history of the managed situation and the history of the
organization’s knowledge about it.

## 15. What PAIM Refuses to Infer

PAIM’s usefulness depends partly on what it refuses to decide silently. When a required meaning is
absent, ambiguous, conflicting, or reserved for accountable judgment, the system exposes that
condition rather than manufacturing convenience.

PAIM does not infer:

- that missing Evidence is favorable Evidence;
- that Evidence for one Configuration or Version applies to another;
- that a Value conclusion determines a Risk conclusion, or vice versa;
- that a universal score can replace alternatives, constraints, uncertainty, and rationale;
- that software access, administrator status, or a role label creates substantive authority;
- that the narrower, broader, newer, more senior, or more specific assignment wins a conflict;
- that accepted completion authorizes activation;
- that Learning automatically changes a Decision;
- that an external occurrence automatically becomes a Trigger or Observation;
- that overlapping Reassessments have an implicit winner;
- that one operating-state label is stronger, safer, more severe, or higher priority than another;
- that similar text, a shared provider name, or a model name establishes Shared Dependency;
- that a Register group transfers authority, applicability, satisfaction, outcome, or closure;
- that presentation order establishes management priority; or
- that a contextual action mutates the authoritative source.

These are not gaps to be filled casually by implementation. Some require explicit records and
accountable determinations. Others are bounded exclusions of v0.1.

For Aster Vale, PAIM can preserve that source accessibility declined, that task-level efficiency
improved, that broader access value remains unclear, and that workflow redesign remains feasible.
It cannot declare that one fact “outweighs” the others without a management judgment and
rationale. It cannot turn the absence of a recorded incident into proof of safe expansion.

**Implication:** explicit absence and conflict are management information. Failing closed protects
the distinction between what the organization knows and what it merely hopes or assumes.

## 16. The Complete Management Model

PAIM’s parts form one continuing cycle:

```text
Define the Case and exact Managed Configuration
        ↓
Establish Evidence, Authority, accountability, and gaps
        ↓
Prepare and freeze independent Value and Risk Inputs
        ↓
Integrate constraints, uncertainty, controls, and alternatives
        ↓
Record an accountable, authorized Decision and Boundary
        ↓
Translate the Decision into Intervention and accepted prerequisites
        ↓
Authorize activation of the exact target Configuration
        ↓
Preserve operational evidence and decision-specific Learning
        ↓
Promote material questions to Triggers and determine Reassessment
        ↓
Coordinate concurrent change and restrict interim operation as needed
        ↓
Confirm the Decision or authorize a successor; retain complete history
        ↓
Derive cross-Case management views and return action to owning domains
```

The sequence is not a claim that organizational work is perfectly linear. Evidence and authority
can be developed in parallel. An Authority Gap can block a broader Decision while a separately
authorized narrower Decision proceeds. Intervention, operation, Learning, and Reassessment can
coexist under exact conditions. The cycle describes governing boundaries, not a simplistic
project plan.

Across the cycle, four invariants keep the model coherent:

1. **Exact object:** every judgment concerns a bounded Configuration and explicit scope.
2. **Independent analysis:** Value and Risk retain their own evidence, boundaries, uncertainty,
   implications, and provenance.
3. **Accountable authority:** software mechanics do not create organizational permission.
4. **Preserved history:** successors change the prospective position without rewriting the past.

These invariants also explain why PAIM separates records that might look redundant in a simpler
workflow. A Decision and Activation Authorization answer different questions. A Trigger and
Trigger Determination answer different questions. A Reassessment status and its accountable
completion outcome answer different questions. A Register concern and its source record answer
different questions. Combining each pair would make the interface shorter, but it would remove a
boundary where evidence, responsibility, or authority can legitimately differ.

The model is therefore intentionally explicit, but explicit does not have to mean obscure. A
practitioner-facing experience can lead with the current management question, show the exact
context and missing prerequisites, and offer the correct owning-domain next action. The released
v0.1 interface remains documentation-led; future interfaces may improve navigation as long as
they preserve the same distinctions and refuse the same unsupported inferences.

Applied to Aster Vale, the model begins with the exact pilot or proposed Configuration, not the
Navigator brand. It preserves the mixed evidence, separate Value and Risk implications, feasible
workflow alternative, uncertainty, and decision authority. It requires any controlled next stage
to be implemented and activated explicitly. Later evidence can trigger Reassessment, and
cross-Case dependencies can become visible without dissolving Case ownership.

The four RWR research observables remain visible throughout: what Evidence was requested, what
dependencies were identified, what rationale management recorded, and what disposition it chose.
PAIM’s contribution is durable representation and governed transition, not proof that a particular
reasoning method caused a better outcome.

## 17. Relationship to Adjacent Disciplines

PAIM complements several existing disciplines. It should not be mistaken for any one of them.

**AI inventory.** An inventory can identify systems and uses. PAIM begins when a bounded use must
be managed as a continuing decision. An inventory item may lead to one or more PAIM Cases, but the
inventory does not supply the Configuration, Decision, authority, intervention, or Reassessment
history.

**Risk management.** Risk management identifies and treats adverse pathways. PAIM preserves an
independent Risk input and connects it to Value, alternatives, authority, action, and Learning.
PAIM is therefore not a renamed risk register.

**Benefits realization and AI Value Management.** Benefits realization follows whether expected
benefits occur. AI Value Management (AIVM) can provide the upstream analytical Value leg. PAIM
does not absorb that work; it accepts a bounded Value input and integrates it with the separate
Risk leg and management context.

**Model risk, safety, security, privacy, compliance, and assurance.** These disciplines can provide
Evidence, constraints, Authority, Risk findings, control conclusions, and challenge. PAIM does not
replace their methods or professional judgments. It preserves how their outputs bear on an exact
management Decision.

**Project, product, and change management.** These disciplines organize delivery. PAIM’s
Intervention records connect delivery to the exact authorized Decision and target Configuration,
and distinguish reported completion, acceptance, and activation authority.

**Adaptive management.** Adaptive approaches organize staged action and Learning under
uncertainty. PAIM supplies explicit Decision, Trigger, Reassessment, and history semantics for
that continuing cycle.

**Return-Weighted Risk.** RWR is a reasoning architecture that asks whether the evolving Value
case and independently assessed Risk case still support the same organizational action. PAIM is a
management system that represents and governs the evidence, judgments, authority, action, and
history surrounding such questions. The Aster Vale illustration helps explain both, but PAIM does
not implement RWR or validate it empirically. A separate future bridge may study their
relationship without collapsing their source boundaries.

**Implication:** PAIM provides connective management structure. It depends on competent adjacent
disciplines and accountable organizational governance rather than claiming to supersede them.

## 18. The Bounded v0.1 Implementation

PAIM v0.1 is a released local governed command-line application and typed Python gateway. It runs
on CPython 3.12 with locked dependencies and uses SQLite persistence. It provides authenticated
operation, explicit software-access checks, immutable records and Versions, audit evidence,
dual-time reconstruction, health and recovery controls, and production pathways for the complete
bounded management model.

The validated pathways cover:

1. a Case and Configuration through independent Value/Risk intake, authorized bounded operation,
   Activation Authorization, and Learning linkage;
2. an external occurrence through proposed intake, Trigger promotion, Trigger Determination,
   coordinated Reassessment, Interim Operating Disposition, and accountable completion; and
3. multi-Case Register derivation, exact Shared Dependency grouping, access-filtered output,
   notification, and contextual return to an owning-domain action.

Those validations support the bounded v0.1 claim. They do not establish that PAIM improves
real-world organizational outcomes, that the Aster Vale facts are empirical, or that PAIM has
validated RWR. They show that the released implementation preserves the defined PAIM behavior
under the accepted automated and practitioner evidence.

Several boundaries remain intentional. v0.1 does not provide a browser interface or polished
self-service workflow, cloud or multi-tenant deployment, live provider integrations, or
continuous telemetry automation. Practitioner navigation is documentation-led.

Most importantly, v0.1 does not implement first-class Observation persistence. Supported manual
or external-event provenance can lead to an explicitly promoted Trigger without inventing an
Observation. IRR-009 remains `OPEN — SEMANTICS UNDESIGNED` and
`CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM`.

v0.1 also treats operating-state values as exact unordered identities. It does not infer strength,
breadth, severity, priority, or state-derived escalation. IRR-014 remains
`OPEN — SEMANTICS UNDESIGNED` and `CLOSED BY DESIGN — OUTSIDE V0.1 CLAIM`.

Semantic dependency matching and generic Management Register resolution are likewise unsupported.
Shared Dependency requires exact governed identity, and Register actions return context to owning
domains.

**Implication:** the software demonstrates the bounded PAIM model without pretending that every
future interface, integration, or semantic question has been solved.

## 19. What v0.1 Establishes—and What Comes Next

PAIM v0.1 establishes that a substantial AI-management model can be represented and exercised
without collapsing the distinctions that make management accountable. It manages an exact
Configuration rather than an abstract technology. It keeps Value and Risk independent. It binds
Evidence to scope, makes gaps and conflict visible, preserves authority and accountability,
separates Decision from operation, records Learning without rewriting history, supports exact
Reassessment, and derives cross-Case views without transferring governing meaning.

For practitioners, the immediate promise is disciplined continuity. A future reader can ask not
only what the organization decided, but what it knew, which Configuration it meant, whose
authority applied, what was required before operation, what changed, and why the Decision was or
was not reconsidered.

For researchers and evaluators, v0.1 creates a bounded object for further study. The RWR working
paper’s four observables—Evidence requested, dependencies identified, management rationale, and
disposition—offer one useful lens for comparing reasoning. PAIM can preserve those observables,
but empirical study is still needed to learn whether PAIM or RWR changes decision quality,
organizational burden, challenge, persistence, or outcomes.

For designers and implementers, the next work should remain specification-driven. Better
practitioner guidance, interfaces, integrations, and deployment options may reduce operating
friction, but convenience must not silently alter identity, time, analytical independence,
authority, or historical semantics. Still-open areas such as Observation and operating-state
relations require their own design and validation before entering a release claim.

Aster Vale closes this guide where it began: with a mixed body of evidence and a real management
choice, not a score. The 28 percent preparation-time improvement matters. So do the 7 percent
end-to-end result, limited change in applicant burden, unclear access improvement, feasible
workflow alternative, changing purpose, wider exposure, controls, uncertainty, and authority.
PAIM’s answer is not to decide for Aster Vale. It is to ensure that the organization’s answer is
about the exact use, rests on visible evidence, comes from accountable authority, leads to bounded
action, and remains open to reconsideration when the world changes.
