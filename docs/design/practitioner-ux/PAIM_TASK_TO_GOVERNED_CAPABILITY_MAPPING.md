# Task-to-Governed-Capability Mapping

## Purpose

This mapping shows how a simpler practitioner interaction can preserve PAIM's governed acts.
Each row distinguishes what the practitioner experiences from what remains separately established
under the current production contract.

| Practitioner task/checkpoint | Known context carried forward | Practitioner must decide or supply | Governed capability/record retained underneath | Must not be inferred |
|---|---|---|---|---|
| Name and open the management concern | Visible Case identity and history | Concise title and management question when creating/changing a Case | Case Record and Version | ownership, authority, Configuration, or lifecycle progress |
| Compare current process and proposed setup | Case; visible C0/C1 content | Which setup is being assessed and any material changes | Managed Configuration Versions; governing designation as a separate commit | authorization, operation, “latest wins,” or identity continuity |
| Review available information | Visible Evidence and source metadata | Whether additional information must be added | Evidence Record/Version | favorable meaning or Applicability |
| Record missing or unresolved information | Known gaps and supplied unknowns | The unresolved question and its material context | Authority Gap where semantically appropriate; Evidence remains absent/unknown as represented | a positive Evidence finding or gap resolution |
| Decide whether information matters | Case, Configuration, source, Actor, target question | outcome, scope, conditions, limitations, rationale | Evidence Applicability Record/Version | Applicability from page placement, labels, or similarity |
| Assess potential Value | Case, Configuration, purpose, visible Evidence and explicit Applicability | finding, analysis boundary, uncertainty, implication, supporting sources | Value Input Record/Version | Risk conclusion, support/Fitness, or Selection |
| Assess Risk and controls | Same categories, independently reconstructed for Risk | harms/exposure, controls, uncertainty, implication, supporting sources | Risk Input Record/Version | Value conclusion, support/Fitness, or Selection |
| Confirm assessment support | Current lane Input; eligible Evidence and explicit Applicability | supportable/blocked outcome, material basis, limiting uncertainty, rationale | Lane Fitness Record/Version and material Evidence basis | favorable outcome, evidence sufficiency, or current use |
| Choose assessment for management use | Eligible current supportable Fitness and Input versions | one assessment and rationale for the stated use/purpose | Acceptance/Selection Record/Version | selection from existence, recency, or a single candidate |
| Record management judgment | Exact current Value/Risk Input, Fitness, Selection, and material Applicability bases | reinforcement, conflict, trade-off, uncertainty, alternatives, proposed judgment | Integration Record/Version | synthesis, score, consensus, ranking, or recommendation |
| Define operating limits | Current Integration and proposed setup | permitted/prohibited scope, conditions, controls, duration, stop/review conditions | Boundary clauses, snapshot, and determination records as required | authorization or operation from Configuration content |
| Propose an action | Current Integration and finalized Boundary | proposed action, rationale, conditions, alternatives, dissent, declarations | Management Decision proposal Record/Version | authorization or effective operation |
| Authorize separately | Proposed Decision; uniquely eligible assignment and authority source where established | authorized scope, limits, conditions, Decision type, dissent/exception | Decision Authorization Basis Record/Version | authority from identity, access, role label alone, recency, or arbitrary UI selection |
| Reconstruct history | Exact retained records, relationships, effective and recorded times | effective/knowledge query context | Existing append-only history and temporal selection | rewriting, retroactive currentness, or omission of non-selected history |

## Orchestration contract

A task-oriented controller may retain a server-side draft/intent for the current interaction, but an
intent is not a domain record. For every authoritative checkpoint it must:

1. reconstruct context from persisted current state;
2. bind exact eligible source versions without asking the practitioner to copy identifiers;
3. show a plain-language review plus governance trace;
4. revalidate visibility, currentness, accountability, and authority at commit;
5. invoke the existing production command without changed semantics; and
6. report the committed record and what remains unestablished.

If the inputs have changed, discard or invalidate the intent and show the change. Do not silently
substitute newer records.

## Authority-resolution behavior

| Resolution | Practitioner presentation | System behavior |
|---|---|---|
| Exactly one eligible accountable assignment and authority source | Display and bind them with scope; allow explicit review | Revalidate both exact Versions and the attributable Actor at commit |
| None | “No person/source is currently established to authorize this action” plus legitimate resolution route | Fail closed; create no authorization |
| Conflict | Show the conflicting governance position without choosing | Fail closed; require owning governance action outside the attempted authorization |
| Stale or out of scope | Explain what changed or why scope is insufficient | Fail closed; preserve proposal and prior authority history |

Software access is evaluated independently in every row.

## Before/after examples

### Evidence relevance

**Before:** choose Evidence Version, target type, target ID/Version, purpose, assessed scope, outcome,
conditions, limitations, rationale, and accountable mechanism.

**After:** from a visible source inside the proposed-pilot question, answer whether it bears on the
proposal, under what scope/conditions, and why. The server carries the exact Evidence, target,
Configuration, purpose, Actor, and time to the review. The same Applicability command commits.

### Value assessment to Selection

**Before:** complete separate analysis, readiness, Fitness, and Selection forms while repeatedly
selecting context and relationships.

**After:** one Value work surface presents three explicit checkpoints. Each checkpoint explains the
new fact it establishes and invokes its existing separate command. No checkpoint auto-completes the
next.

### Decision authority

**Before:** choose assignment and Authority Record UUIDs from lists.

**After:** display the one eligible responsible role and authority source when resolution is unique.
Zero or conflict blocks with explanation. The authorization still binds those exact Versions and does
not derive authority from the UI.
