# PAIM Task-Oriented Practitioner UX Principles

## Design objective

Help a competent practitioner complete the management task without prior PAIM ontology training,
while the application continues to preserve every governing distinction required by PAIM.

## Interaction principles

### 1. Start with the task

Every page, panel, action, and field must answer: **What practitioner task does this help
accomplish?** Record families may determine storage and validation, but they do not automatically
determine navigation or form boundaries.

### 2. Carry known context

Case, proposed Configuration, purpose, use context, Actor identity, visible source material, and
prior reviewed choices should be bound from current authoritative state. Ask again only when:

- more than one eligible current choice exists;
- the practitioner is intentionally changing the context;
- the prior choice became stale or conflicted; or
- confirmation of a consequential governed act is required.

Display carried context before commit and revalidate it at commit. Never silently update a stale
working context.

### 3. Ask for judgment, not schema assembly

Prompts should elicit management reasoning. The adapter may structure that answer into existing
domain inputs, but it must not supply missing substantive content, infer Applicability, or choose an
assessment or authority source.

### 4. Orchestrate distinct acts

One task surface may coordinate several governed acts when their order is understandable. Each act
still has:

- an explicit practitioner checkpoint;
- a review representation of what will be established;
- current-context, accountability, and authority revalidation;
- an atomic production command; and
- a durable audit and history result.

A completed earlier step can populate context for the next step; it cannot satisfy the next step.

### 5. Distinguish prerequisites, available work, and unresolved conditions

Show a unique required prerequisite only when it blocks the practitioner's stated intended action.
Otherwise show the set of independent work available now and keep unresolved absence, staleness,
vacancy, or conflict distinct. Value and Risk are unranked peer work; neither becomes the default
next task merely because it appears first in a pathway description. This is deterministic read
composition, not a persisted task status, attention score, or recommendation.

### 6. Make passed controls quiet and failed controls explanatory

Identity, software access, exact governed-context visibility, accountability, and substantive
authority remain separate checks. Keep satisfied machinery quiet unless it is management-significant.
At a consequential review or commit, still show the action, Actor/role, authority source, scope,
limits, and conditions. When a check fails, state:

1. what intended action cannot proceed;
2. what is absent, stale, or conflicting;
3. why that matters; and
4. the legitimate action or responsible role that can resolve it.

Never offer an implicit winner for a conflict.

### 7. Present evidence in the question's context

Show available source material and known gaps beside the assessment prompt. “Suggested for review”
may be based only on explicit current relationships or neutral scenario grouping; it must not imply
Applicability. The practitioner still determines whether each source bears on the question.

Available evidence and missing/unknown evidence must look different. Missing live outcomes are not
positive Evidence cards.

### 8. Preserve analytical independence through behavior

Value and Risk receive equal status, separate work sessions, sources, assessments, support checks,
and selections. Their summaries may be compared, but no common score, automatic consensus,
priority, or recommendation is produced. Full-width work is compatible with peer status.

### 9. Disclose meaning before machinery

Use three progressive layers:

1. **Practitioner workspace** — proposal, facts, unknowns, judgment, limits, responsible person, and
   available or required action; no raw identifiers or payloads.
2. **Source, history, and governance basis** — sources, limitations, prior versions, applicability
   basis, accountable role, authority basis, and effective/knowledge context.
3. **Technical inspection** — full identifiers, machine timestamps, status codes, relationships,
   command/audit references, and payload for separately authorized inspection.

Opening a deeper layer must be reversible and must not replace or stretch the working page.

### 10. Use concrete conditions

Prefer “two senior-underwriter teams, standardized digital records, eight weeks, 100% quality
assurance” over “bounded.” Prefer “the C1 setup described here” over repeated “exact Configuration”
when no ambiguity exists. Formal language remains available in trace and confirmation.

### 11. Separate consideration, proposal, authorization, and operation

Labels must make clear whether a setup is:

- a comparison baseline;
- under consideration;
- proposed for authorization;
- authorized under stated limits; or
- currently operating.

No visual completion state may collapse these positions.

Formal governing-currentness language belongs primarily in governance trace. It must remain
distinct from maturity/history, purpose, authorization, and operating state.

## Non-negotiable semantic constraints

The practitioner UX must not:

- weaken Record/Version binding or currentness checks;
- infer Evidence Applicability from proximity, labels, or similarity;
- merge Value and Risk or calculate a shared score;
- make Fitness or Selection implicit;
- make Integration automatic;
- treat operating limits as a Decision;
- treat a proposal as authorization;
- infer accountability or authority from identity, visibility, or software permission;
- choose among conflicting assessments, assignments, or authority sources;
- rewrite history or hide non-selected and historical material; or
- pre-decide the Harborlight outcome.

## Evaluation criteria

A future implementation should be tested for both conformance and usability:

- Can a practitioner state what is being considered and what is missing before learning PAIM terms?
- Can they complete each judgment without re-entering known context?
- Can they explain what PAIM established at every checkpoint?
- Can they find source and governance trace without disrupting their work?
- Can they inspect technical identity when needed?
- Does the system stop clearly on stale context, vacancy, or conflict?
- Are Value/Risk independence and proposal/authorization separation evident from behavior?
- Can the practitioner reach a non-favorable or no-action conclusion without interface resistance?
