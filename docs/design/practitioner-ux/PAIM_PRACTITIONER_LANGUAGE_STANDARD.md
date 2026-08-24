# PAIM Practitioner-Language Standard

## Status and authority

This standard governs practitioner-facing language in PAIM interaction design, browser copy,
operator guidance intended for practitioners, and reference-case content presented in a
practitioner workflow. It is an editorial and interaction-design standard over the existing PAIM
contracts; it does not rename domain records, change system specifications, or authorize new
semantics.

The system specifications under [`docs/system/`](../../system/) remain authoritative. When simpler
wording cannot preserve a governing distinction, the distinction wins and the formal term is
introduced where the practitioner needs it.

## Governing principle

> Practitioner UI communicates management meaning and useful action first. Formal PAIM terminology
> appears only when the distinction genuinely matters, and engineering implementation language
> normally remains outside the practitioner workflow.

Related rule:

> Describe what the practitioner can understand or do, not what PAIM intentionally does not infer,
> expose, or implement.

Clear language is not semantic relaxation. Exact identity, dual-time history, access, accountability,
authority, Applicability, independent Value/Risk, and proposal/authorization boundaries continue to
be enforced underneath.

## Audience and disclosure layers

Language follows the task and audience rather than a global word ban.

### 1. Practitioner work

Use the management question, concrete facts, choices, limits, and available action. Navigation,
headings, cards, helper text, and empty states must be understandable without prior PAIM ontology
training. Raw identifiers, persistence mechanics, and command vocabulary do not belong here.

### 2. Consequential review and confirmation

State what will be established, the context it applies to, who is acting, and any material limits.
Introduce a formal term only when it prevents a consequential misunderstanding—for example, that a
proposal is not authorization, or that software permission is not authority to make a Decision.

### 3. Source, governance trace, history, and reconstruction

Use formal concepts when they explain why a result applies, what changed, or what was known at a
time. `Configuration`, `Applicability`, `Fitness`, `Selection`, effective time, known time, and prior
Version may be appropriate here when introduced in context. Prefer readable names and dates before
technical identity.

### 4. Technical inspection and administration

Record/Version IDs, UUIDs, payloads, enum values, command/audit references, checksums, resolver
outputs, and storage/runtime details belong here and remain separately access-enforced. Technical
language may be precise because the task is technical.

### 5. Reference cases, examples, and fixtures

Content shown to a practitioner is practitioner-facing even when it originated in a fixture or
example. Author it to the same standard while preserving source discipline. A UI must not silently
rewrite governed source content; content revisions require their own authorized reference-case
change.

## Language principles

### 1. Lead with management meaning

Name the actual proposal, information, requirement, uncertainty, or action before the PAIM object
that represents it. Prefer `Proposed setup under review`, `Review how information applies`, and the
authority question itself over `Governing Configuration`, `Evidence Applicability`, or `Authority
Gap` as primary task labels.

### 2. Use concrete facts before abstract qualifiers

State known users, purpose, duration, amount limit, controls, verification, and exclusions before
using `bounded`. State the particular setup or reviewed version before using `exact`. Concrete
wording helps the practitioner understand the limit; the formal qualifier remains available in
confirmation and trace where it matters.

### 3. Keep satisfied controls quiet

Do not repeatedly defend invariants that the page structure and state already communicate. Identity,
visibility, access, accountability, and authority remain separate checks even when their successful
machinery is not narrated. Explain a failed check when it prevents an intended action.

### 4. Keep only consequential safeguards

A safeguard sentence is warranted when omitting it could reasonably cause a competent practitioner
to take or understand a consequential action incorrectly. Use the shortest positive statement that
preserves the boundary, placed at the decision point.

Keep safeguards such as:

- `This proposal still requires authorization` beside proposal confirmation;
- `Software access allows this attempt; the responsible role and authority are checked separately`
  when an authority failure must be explained; and
- `Value and Risk remain separate assessments` where an integration action could look like a merged
  score.

Remove or consolidate safeguards when the same distinction is already evident and no action depends
on repeating it. Do not add a disclaimer merely to document an implementation invariant.

### 5. Explain the page's positive purpose

Say `This page shows what was recorded, when it applied, and what was known at the time`, not `This
page does not expose machine identifiers or raw payloads`. Say what qualifies for a section, not how
the read-side classifier works. Implementation and persistence limitations belong in design or
technical documentation.

### 6. Introduce formal terminology just in time

Use the ordinary question first. Introduce the formal name when it helps review, confirmation,
history, reconstruction, or dispute resolution. The glossary supports the workflow; it is not a
prerequisite for understanding navigation or basic instructions.

### 7. Avoid redundant category labels

Do not repeat `Recorded information` or `Explicitly unavailable` on every card when the section
already establishes that category. If classification differentiates the material usefully, show the
governed classification in ordinary language—`Observed information`, `Estimate`, `Assumption`, or
`Explicitly unknown`—without implying quality, truth, sufficiency, or relevance.

### 8. Ask questions and name actions as practitioner work

Prefer:

- `What do we know?`
- `What do we still need to know?`
- `What requirements apply?`
- `What needs review?`
- `What potential Value could this create?`
- `What Risks and uncertainties should we consider?`
- `What does this mean for the proposed use?`

Actions use a verb plus the management object or judgment: `Add information`, `Review how
information applies`, `Assess potential Value`, `Review operating limits`, and `Submit the proposal
for authorization`. Command and record-family names may appear later in trace.

### 9. Match exception language to actual effect

Use `blocks` only when a stated intended action cannot proceed. Otherwise use `Why this matters`,
`What can resolve it`, or `What still needs review`. A failure message names:

1. the action that cannot proceed;
2. the absent, stale, inaccessible, or conflicting condition;
3. why it matters for that action; and
4. the legitimate action or responsible role that can resolve it.

Never present an implicit winner or instruct the practitioner to bypass a control.

### 10. Preserve authored-source boundaries

UI translation may simplify labels around a governed statement but must not silently paraphrase the
statement into a different claim. Quote or display authored source content faithfully where its exact
meaning matters. Raise awkward fixture wording as a separately governed content finding.

## Vocabulary treatment

| Term | Ordinary practitioner treatment | Where the formal term remains useful |
|---|---|---|
| `exact` | Name the particular setup, assessment, source, or version being reviewed. | Confirmation, stale/conflict explanation, governance trace, reconstruction, technical inspection. |
| `bounded` | State the actual scope, users, duration, controls, and exclusions. | Formal scope statement or confirmation after the concrete boundary is visible. |
| `governing` | `setup used for this assessment` or `setup for this Decision`. | Configuration designation trace and formal history. Never use it to imply authorization or operation. |
| `owning` | Name the task or responsible role directly. | Organizational responsibility or capability routing when ownership is itself the subject. |
| `accountable mechanism` | `Responsible for this judgment`. Show the established actor and function, or state that accountability is not established/conflicting. Never invite free text as a substitute. | Consequential confirmation, accountability conflict, governance trace, and audit. |
| `substantive authority` | `authority to make this Decision` or the specific governed act. | Explaining why identity, visibility, role label, or software permission is insufficient. |
| `authoritative evidence` | Name the source and what it supports; use `required source` only when the authority is established. | Source-discipline or audit discussion. Do not imply truth, sufficiency, or Applicability. |
| `substantive answer` | State the actual question and whether an answer is established. | Design or audit discussion distinguishing real content from placeholder/transport state. |
| `provenance` | `where this came from`, `source and history`, or `source, date, and limitations`. | Governance trace and technical inspection. |
| `Record` | Name the management object: Case, information item, requirement, assessment, proposal. | Technical inspection and formal data-contract documentation. |
| `Version` | `version reviewed`, `prior version`, or `history` when the distinction matters. | Confirmation, history, reconstruction, conflict/stale explanation, and technical inspection. |
| `UUID` | Do not show in ordinary work. | Separately authorized technical inspection and diagnostics. |
| `repository silence` | State positively that the section contains needs that were recorded as unavailable. | Design documentation explaining the non-inference rule. |
| `machine identifiers` / `raw payloads` | Do not explain their omission in ordinary copy; describe what the page provides. | Technical-inspection authorization, operator, security, and engineering documentation. |
| `current assessment basis` | `setup used for this assessment`; qualify `current` with the actual object and context. | Confirmation and governance trace where currentness is consequential. |
| `comparison option` | Prefer the concrete alternative, such as `manual-process comparison`, when governed content supports it. | Neutral fallback when the alternative's nature is not established. |
| `Proposal setup` | Use only when the surface is truly limited to a proposal. `Setup & scope` is a later test candidate, not an automatic rename. | Existing UX-1/UX-2 navigation until separately reviewed. |
| `recorded information` | Use as section helper text when needed, not a mechanical label on every card. Prefer the actual statement or governed classification. | Evidence/history trace where the distinction from inference matters. |
| `explicitly unavailable` | Prefer `not yet available`, `not observed`, or the recorded absence itself. | Design/trace language when explaining deterministic classification. |
| `Evidence` | `information` in ordinary source review; `Evidence` where the governed evidentiary role matters. | Applicability, Fitness, confirmation, governance trace, and specifications. |
| `Applicability` | `how this information applies` or `what this information bears on and under what limits`. | Confirmation, governance trace, history, and disputes about the exact judgment. |
| `Authority Gap` | Lead with the unresolved requirement or authority question. | Governance trace, history, and specifications. |
| Legacy `Fitness` | Preserve `Fitness` and its original outcome wording in historical/governance trace. Do not paraphrase it as favorable support for the AI use. | Current v0.1 saved determination, confirmation, and history until a coordinated prospective cutover. |
| Prospective assessment adequacy | `Is this assessment adequate for use in the management decision?` Explain material limitations and any reason it should not be used. | Future neutral review after the coordinated specification gate; not current runtime vocabulary. |
| Legacy `Selection` / prospective reliance | `Which assessment will management use?` when alternatives exist; otherwise explain that completing the review designates the exact adequate assessment for Case reliance. | Saved reliance/selection, confirmation, governance trace, and history. Never imply an automatic winner. |

This table is contextual guidance, not a blacklist. Review each occurrence according to audience,
task, and consequence.

## Component rules

### Headings and navigation

- Use a question or recognizable management task.
- Keep labels short and stable enough for orientation.
- Do not encode an unestablished workflow status or intended action in navigation.
- Do not rename `Proposal setup` to `Setup & scope` until a separately authorized scenario review
  establishes that the broader label remains truthful across the lifecycle.

### Action labels

- Begin with a verb and the judgment or object the practitioner recognizes.
- Do not expose command names, record families, or unexplained governance mechanisms.
- Do not imply that review equals commit, proposal equals authorization, or access equals authority.
- Preserve an explicit review/confirmation boundary for consequential governed acts.

### Cards and lists

- Lead with the concrete statement, requirement, question, setup, or assessment.
- Show source, timing, classification, and limitations as secondary context when useful.
- Avoid repeating a category already supplied by the section heading.
- Do not use visual order, emphasis, or completion styling to imply ranking, sufficiency, relevance,
  recommendation, authorization, or a preferred Value/Risk lane.

### Helper text

- Explain what the section contains and what the practitioner can do next.
- Use one consequential safeguard at the point of possible misunderstanding rather than repeating
  semantic-defense copy across the page.
- Do not narrate classifiers, persistence, hidden technical data, or deferred implementation.

### Empty states

- Name what is not visible or not established in the current context.
- Offer a legitimate next action only when access and workflow context support it.
- Do not turn absence into a favorable finding, completeness claim, readiness claim, or generic gap.

### Exceptions and unresolved conditions

- Reserve `blocked` for an intended action that actually cannot proceed.
- Distinguish absence, access denial, staleness, vacancy, and conflict.
- Avoid framework phrases such as `owning work area`; name the responsible action or role.
- Preserve fail-closed behavior and do not disclose protected identities or counts.

### Confirmation and history

- Show the management meaning first, then the formal governed effect where needed.
- Carry and revalidate current context rather than asking the practitioner to assemble identifiers.
- Name the action being attested to and its consequence; do not use an internal command name or
  generic enforcement narration as the heading, explanation, or primary button.
- Keep command names, Record/Version identifiers, and technical revalidation detail in secondary
  authorized record detail. Practitioner-friendly copy never replaces server-side revalidation.
- Preserve exact identity, effective time, known time, and append-only history underneath.
- Keep prior/non-selected records available in authorized history without crowding ordinary work.
- Distinguish `You / assessor` from `Responsible for this judgment`. The same person may appear in
  both only when a separately current applicable Role Assignment establishes accountability.
- For vacancy, say `Accountability for this judgment has not been established.` For incompatible
  plurality, say `More than one accountability assignment applies and the conflict must be
  resolved.` Neither state may offer an unrestricted text field as a way through the control.

## Before-and-after examples from UX-1 and UX-2 review

| Before or observed pattern | Preferred treatment | Reason |
|---|---|---|
| `Current Governing Configuration` | `Setup used for this assessment` | Communicates management role without implying authorization or operation. |
| `Review designation as governing` | `Use this setup for the assessment` | Names the practitioner's action while the confirmation preserves the governed designation. |
| `These tasks are peers. Their display order is not a ranking, recommendation, or priority.` | `Choose the task that fits the work you are doing now.` | Gives positive direction; equal treatment and layout already carry the non-ranking rule. |
| `Evidence recorded` on every card | Lead with the information statement; show classification in source detail if useful. | Removes redundant category language without changing Evidence semantics. |
| `Repository silence does not create a gap.` | `This section shows information recorded as not yet available.` | Describes the section rather than the classifier/non-inference implementation. |
| `Explicitly unavailable` on every missing-information card | Lead with the recorded absence itself. | The section heading already supplies the category. |
| `No exact Applicability determination is established.` | `Review what this information bears on, its scope and limits, and why.` | Names the practitioner judgment; Applicability remains explicit underneath. |
| `These are explicit judgments or questions that remain separate from the information and sources above.` | `Review unresolved questions and decide how visible information bears on this work.` | Explains the task rather than defending the ontology. |
| `This view does not expose machine identifiers or raw payloads.` | `This page shows what was recorded, when it applied, and what was known at the time.` | States the page's positive purpose. |
| `Record an Authority Gap` | `Record an unresolved requirement or authority question` | Foregrounds the question while preserving the Authority Gap command and history. |
| `Accountable mechanism` | `Responsible role or governance process` | Uses professional language; formal accountability remains in confirmation and trace. |

## Reference-case and example-content guidance

- Use realistic professional language at the practitioner's altitude.
- State concrete users, uses, time horizon, controls, thresholds, alternatives, and exclusions.
- Distinguish source fact, constructed illustration, and constructed PAIM extension explicitly.
- Do not imply that a reference case empirically validates PAIM, RWR, or another analytical method.
- Do not pre-author practitioner judgments that an exercise is intended to elicit.
- Apply the same terminology review to fixture titles, descriptions, information statements,
  authority questions, and helper content that will appear in the UI.
- Preserve accepted source text. Revise awkward governed content only through a separately reviewed
  reference-case/content issue.

The preserved Harborlight Scenario-A fixture remains unchanged by Issue #115. Future authorized
reference-case review should examine fixture-authored phrases including `exact bounded C1 pilot`,
`authoritative evidence`, and `substantive answer`, along with other uses of `exact` and `bounded`.
Those observations are content findings, not permission for the UI to rewrite the stored records.

## Known owner-review findings retained for later work

- Home still uses the long persisted Case title because PAIM has no separate durable management-
  question field. Copy tricks must not fabricate one.
- `Comparison option` is truthful but abstract; `manual-process comparison` is preferable only when
  governed content supports that meaning.
- `Proposal setup` may be too narrow as enduring navigation. `Setup & scope` is a scenario-test
  candidate, not an Issue #115 rename.
- The C0 action `Review using this setup for assessment` exposes a permitted governance operation
  without an obvious practitioner task. Preserve it for later workflow review.
- Source & history is readable but record-centric. A management-history narrative requires later
  design and is not a copy-only change.
- Reference-case wording can carry engineering vocabulary even when templates are clear; address it
  through separately governed content revision.

## Semantic hard constraints

Language changes must never:

- change domain/schema/specification semantics or add persistence/read-side state;
- weaken Record/Version binding, currentness, dual-time reconstruction, or append-only history;
- infer missing information from absence in the repository;
- infer Applicability, sufficiency, truth, materiality, Value/Risk relevance, or Decision support;
- merge, rank, score, prioritize, or recommend between Value and Risk;
- make Fitness, Selection, Integration, Boundary, proposal, or authorization implicit;
- infer accountability or authority from identity, visibility, software access, role label, document
  title, proximity, or presentation order;
- hide vacancy, conflict, staleness, inaccessibility, or historical/non-selected material;
- call a proposal authorized, an authorization operating, or a comparison baseline current operation
  without the separately established governed state; or
- disclose protected facts, identities, relationships, or global counts.

If clear practitioner wording would require a new field, relationship, status, classifier, workflow,
or substantive interpretation, stop and return the question to design/domain authority.

## Non-goals

This standard does not implement UX-3 or later UX increments, redesign Value/Risk, Integration,
Boundary, Decision, or Source & history, add M1D, mutate Harborlight, expose Scenario B–F, change a
system specification, or alter the immutable v0.1.0 release/tag.

## Practitioner-language PR checklist

Before a practitioner-UX PR is handed off, verify:

- [ ] Headings and navigation name recognizable management tasks.
- [ ] Actions use practitioner verbs while preserving the exact production capability and
      review/confirmation boundary.
- [ ] Concrete scope, users, duration, controls, and exclusions replace abstract qualifiers where
      governed facts support them.
- [ ] Formal PAIM terms appear only where the distinction is needed and are explained in context.
- [ ] Helper text states positive purpose or next action rather than hidden implementation details.
- [ ] Repeated category labels and semantic-defense copy have been removed unless they prevent a
      consequentially wrong inference.
- [ ] Empty states and exceptions describe only the exact visible/established condition.
- [ ] `Blocked` is used only for a specific intended action that cannot proceed.
- [ ] No wording implies unestablished Applicability, sufficiency, Value/Risk relevance,
      accountability, authority, authorization, operation, priority, ranking, or recommendation.
- [ ] Practitioner cards and details do not expose technical identities or payloads.
- [ ] Reference-case/example content shown in the flow has received the same language review without
      silent rewriting of governed source material.
- [ ] Access filtering, currentness revalidation, append-only history, and all formal semantic
      boundaries remain covered by hard-oracle tests.
- [ ] UX scope and deferred language/content findings are documented.
- [ ] Documentation links, focused runtime/browser tests when copy changed, normal repository gates,
      fixture-integrity checks, and `git diff --check` pass.
