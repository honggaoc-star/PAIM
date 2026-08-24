# PAIM Product Design Foundation

## Status and authority

This document is PAIM's product-level governing design reference. It explains why PAIM exists,
what practitioner value it should create, and the principles that should govern later product
design. It sits above the accepted
[Practitioner Operating Model](PAIM_PRACTITIONER_OPERATING_MODEL.md), which explains how people,
roles, responsibility, authority, and work should operate, and below the authoritative
[system specifications](../../system/specifications/), which define exact implementation
contracts.

This foundation is not a system specification, schema decision, UI specification, release claim,
or authorization to implement Responsibility, Case Work, UX-4, M1D, organization-local
deployment, analytics, or another Harborlight scenario. When a product proposal cannot preserve
an existing contract, it requires explicit semantic review rather than reinterpretation here.

## Product proposition

> PAIM helps organizations make, carry out, continuously review, and learn from AI-related
> business decisions while maintaining the information, reasoning, responsibility, authority,
> actions, outcomes, and history behind them.

PAIM's central value is **management continuity of an AI-related business decision over time**.
It is not primarily an assessment form, approval workflow, risk register, document generator, or
dashboard. It helps practitioners keep a legitimate management position coherent as information,
conditions, responsibilities, operation, outcomes, and organizational knowledge change.

The recurring management problem is broader than whether an AI system is approved. At any point,
the organization may need to answer:

- What use are we considering or operating, and within what exact Configuration?
- What Value do we expect, and what Value is actually being realized?
- What Risks, controls, constraints, alternatives, and uncertainties matter?
- What information is available, missing, changed, or no longer applicable?
- Who is responsible for the work, and whose substantive authority is required?
- What is the current Decision, why was it made, and under what conditions?
- What actions followed, what happened, and what remains unresolved?
- What should we watch, learn, reconsider, continue, adjust, pause, or stop?

The product should let practitioners answer those questions without asking them to reconstruct
PAIM's persistence model or repeat context PAIM already legitimately knows.

## The continuing management promise

A point-in-time Value-Risk assessment is not adequate for a use whose evidence, context,
operation, and consequences continue to develop. PAIM therefore supports a continuing cycle:

**Consider -> Assess Value & Risk -> Decide -> Act -> Observe -> Learn/Review -> Continue / Adjust /
Stop -> Observe ...**

This is a practitioner model, not a universal automated lifecycle. It does not imply that PAIM
currently has first-class Observation records, continuous telemetry, automatic review triggers,
or a workflow engine. The detailed model and its current semantic boundaries are in the
[Continuing Value-Risk & Decision Lifecycle](PAIM_CONTINUING_VALUE_RISK_DECISION_LIFECYCLE.md).

For an existing Case, legitimate continuing management should normally carry forward the exact
state that remains current, focus attention on what changed, and review only the affected basis.
It must not force a mechanical full reassessment or silently treat old evidence as current. Both
events and elapsed time may prompt review; neither determines the outcome.

Realized Value receives the same management attention as emerging Risk. The two remain
analytically independent and are never collapsed into a universal score, net rating, or automated
recommendation.

## Current management position

The ordinary product experience should compose a clear **current management position** from
authoritative PAIM state. It should answer, as applicable:

- the current bounded use and Configuration;
- current independent Value and Risk positions;
- the current authorized Decision and its reasoning;
- conditions, boundaries, controls, and required actions;
- unresolved information, responsibility, authority, or uncertainty;
- what the organization is watching or trying to learn;
- the next review basis or expected review point; and
- what presently needs attention.

For now this is a product/read composition, not a new domain record, Case status, score, or
materialized truth. Every statement must remain traceable to exact authoritative records and
access-filtered context. Composition must preserve conflict, absence, historical state, and
effective-time and knowledge-time meaning. Presentation does not choose a winner or create
priority, responsibility, authority, applicability, satisfaction, or closure.

## Decision record as a product outcome

A reconstructable Decision record should arise as a by-product of legitimate management work,
not as paperwork completed after the real decision. PAIM should preserve enough exact context to
answer:

> What was known, believed, unresolved, decided, and authorized when this Decision was made?

The product direction includes a conceptual **View Case as it stood when the Decision was made**.
That view would reconstruct the applicable information, Value and Risk inputs, boundary,
alternatives, rationale, accountability, authority, conditions, and action basis at the relevant
effective and knowledge times. It is not authorization for a new screen or record in this issue.
The [Decision Record, Audit & Learning Model](PAIM_DECISION_RECORD_AUDIT_AND_LEARNING_MODEL.md)
defines the distinction between decision quality and outcome quality and the levels at which PAIM
can support learning.

## Product concepts

PAIM should organize practitioner understanding around eight product concepts:

- **Case** — the continuing management context for a bounded AI-related business question.
- **Information** — what is known, missing, uncertain, applicable, or authoritative for the work.
- **Assessment** — independent Value and Risk judgments and their bounded support.
- **Work** — the legitimate tasks, responsibilities, prerequisites, and handoffs needed to move
  the Case forward.
- **Decision** — the accountable, authorized management position and the reasoning and conditions
  that support it.
- **Action** — what must be carried out, accepted, constrained, monitored, or changed after a
  Decision.
- **Learning** — what later information and experience mean for this Case, this Decision, or
  future organizational judgment.
- **History** — the reconstructable sequence of exact states, acts, bases, and changes.

These are product concepts, not a new record taxonomy, mandatory navigation labels, or authority
sources. Existing domain records retain their exact meanings.

## Practitioner-centered design principles

The accepted operating model establishes two linked expectations:

> The engineering model must be rigorous enough to protect the management process. The
> practitioner experience should be as simple as that rigor allows.

> PAIM should expose the minimum information and interaction necessary for legitimate management
> work.

Product design must therefore:

1. preserve rigorous identity, scope, time, history, access, accountability, and authority while
   presenting ordinary work in practitioner language;
2. expose the practitioner's genuine judgment or action and absorb safe system operations;
3. show state as management meaning, not as unexplained internal status;
4. let information grow with the task rather than with internal model complexity;
5. preserve history automatically as work proceeds;
6. avoid asking for context PAIM already legitimately knows;
7. avoid asking users to perform system operations;
8. avoid exposing an internal concept merely because persistence requires it;
9. keep technical inspection separate from ordinary work; and
10. remove content when it contributes no legitimate understanding, judgment, or consequence.

Four short rules make those expectations testable:

> **Expose the user's action; absorb the system operation.**

> **Show state as meaning, not status.**

> **The amount of information shown should grow with the practitioner's task, not with the
> complexity of PAIM's underlying state.**

> **Preserve history so practitioners can learn from it; never make them maintain history as a
> separate task.**

In particular, PAIM must not ask a practitioner to reconstruct already established Case, setup,
Evidence, assessment, or return-path context.

The minimum-content test remains:

> If removing this content would not impair understanding of the situation, a legitimate
> judgment, or the consequence of an action, why is it on the screen?

Sometimes the correct replacement is nothing.

## Product attention hierarchy

The product should guide attention at three levels:

- **Home — What needs me?** Cross-Case work, changes, waits, and attention that the participant is
  legitimately entitled to see, without universal ranking.
- **Case — What is happening here?** The current management position, people and responsibility,
  unresolved conditions, work, Decision, action, learning, and history for one Case.
- **Task — Help me accomplish this piece of work.** The minimum relevant context, genuine
  practitioner input, consequence, authority boundary, and return path for one bounded action.

This hierarchy is a direction for product composition, not a frozen navigation scheme, a queue
priority rule, or an authorization to fabricate assigned work.
Navigation should follow changing attention from organization to Case to task, rather than asking
the practitioner to navigate from capability to record type to command.

## Value hierarchy and virtuous cycle

PAIM's product value should be evaluated in this order:

1. help practitioners make a good, bounded, accountable Decision;
2. preserve why that Decision was made;
3. help the organization observe what follows;
4. support legitimate reconsideration when the basis changes; and
5. make learning available to the current Case and future judgment.

Case quality comes before dashboard breadth. The desired cycle is:

**better situated work -> clearer Decision -> faithful action -> useful observation -> disciplined
review -> reusable learning -> better situated work**

The cycle does not prove that PAIM causes better outcomes. It defines the practitioner value the
product should seek and the evidence future empirical work should examine.

## Operating-model relationship

This foundation defines the product's purpose, value, continuing lifecycle, design principles,
scope, and learning ambition. The
[Practitioner Operating Model](PAIM_PRACTITIONER_OPERATING_MODEL.md) defines how a small-to-medium
organization can staff and coordinate that work: a Case Coordinator, an Assessor, an optional
Reviewer, granular responsibilities, separately established authority, directly assigned
post-Decision actions, and administration outside Case staffing. One participant may hold several
responsibilities without collapsing their records or meanings.

`Local` continues to mean organization-controlled deployment as product direction. Current
support remains one loopback, single-workstation application until a separate deployment gate is
accepted. This foundation does not reopen those decisions.

Later normative Responsibility and Case Work specifications may define exact contracts. Later UI
work may express accepted product and operating-model decisions. Engineering supplies the
machinery. None of those layers may silently redefine the layer above it.

## Product ownership boundary

PAIM owns continuity across:

- the Case and bounded AI-enabled use;
- relevant information and missing information;
- independent Value and Risk assessment;
- responsibility and Case work;
- Decision, accountability, and substantive authority;
- conditions, actions, implementation, and outcomes;
- observation, learning, and continuing review; and
- reconstructable effective-time and knowledge-time history.

PAIM should link or integrate with adjacent systems where appropriate rather than duplicate them.
Its exclusions and adjacent-system boundaries are defined in the
[Product Scope Boundary](PAIM_PRODUCT_SCOPE_BOUNDARY.md).

## Gates after this foundation

Acceptance of this foundation establishes a product-design reference only. It does not begin the
next increment. Any follow-on must be separately bounded and must state whether it concerns:

- normative Responsibility or Case Work contracts;
- read composition for the current management position;
- continuing review or learning semantics;
- deployment architecture;
- a prototype or practitioner study;
- a UI increment; or
- empirical research.

UX-4, M1D, organization-local deployment, Harborlight Scenarios B-F, first-class Observation,
analytics, universal workflow, and domain or schema changes remain unauthorized here.
