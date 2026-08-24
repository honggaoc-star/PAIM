# Scenario-A Provisional Practitioner Vocabulary Classification

## Status

This revises the provisional vocabulary in response to one Scenario-A usability checkpoint. It is not
a final glossary and does not rename domain records, API contracts, or specifications.

The later [PAIM Practitioner-Language Standard](PAIM_PRACTITIONER_LANGUAGE_STANDARD.md) is the
durable cross-cutting editorial standard. This Scenario-A classification remains source context and
concrete vocabulary input; use the durable standard as the UX-3 and PR-handoff gate.

## Classification key

1. **Ordinary practitioner UI term** — usable as a primary label when phrased in context.
2. **Practitioner concept needing contextual explanation** — meaningful, but introduce after the
   underlying question and explain just in time.
3. **Governance/audit term for progressive disclosure** — available in trace, review, and history;
   not usually a primary action label.
4. **Engineering/internal term not normally shown** — reserved for technical inspection and
   diagnostics.

## Candidate terms

| Candidate PAIM term | Class | Recommended practitioner wording or treatment |
|---|---:|---|
| Case | 2 | Lead with a concise, Configuration-stable Case title. Show a separate full management question only when an authoritative production field supplies it; explain once that the Case preserves the continuing concern across changes. |
| Configuration | 2 | Prefer **manual process / comparison baseline**, **proposed setup**, or **setup being assessed**. Use **current operating process** only when separately established. Introduce Configuration in source/history trace when versioned context matters. |
| Evidence | 1 | Use **information** or **evidence** according to professional context. Separate available material from missing/unknown evidence. |
| Applicability | 2 | Ask **Does this information bear on this proposal and question?** Show “Applicability determination” in governance trace. |
| Authority | 2 | Use **requirements and decision authority**; distinguish a source that governs the action from a person/role permitted to decide. |
| Authority Gap | 2 | Use **unresolved requirement or authority question**. Preserve the formal term in trace/history. |
| Value assessment | 1 | Use **Potential Value** for navigation and **Value assessment** for the saved judgment. |
| Risk assessment | 1 | Use **Risk and controls** for navigation and **Risk assessment** for the saved judgment. |
| Integration | 2 | Ask **Considering Value and Risk together, what is your management judgment?** Explain that the judgment relates independent assessments without merging them. |
| Boundary | 2 | Prefer **operating limits and conditions**. Show “Boundary” in confirmation and governance trace. |
| Decision proposal | 1 | Prefer **proposed action** or **proposal awaiting authorization**; keep proposal visibly distinct from authorization. |
| Decision Authority | 2 | Use **who can authorize this action** and show the responsible role/source. Do not use it as a synonym for software approver. |
| Fitness | 2 | Ask **Is this assessment sufficiently supported for this proposed use?** Show “Fitness determination” in governance trace. |
| Selection | 2 | Ask **Which assessment is management using for this Decision?** Use “selected assessment” in summaries after explicit confirmation. |
| exact | 3 | Replace with the concrete object or “the version reviewed here” in ordinary work. Use exact identity language in confirmation, trace, and conflict/stale explanations. |
| bounded | 3 | State the actual users, scope, duration, controls, and exclusions. Retain “bounded” in formal governance explanations when useful. |
| governing | 3 | Prefer **setup used for this assessment/Decision**. Keep “governing Configuration” in trace and formal history. |
| current | 2 | Always qualify: current selected assessment, current proposed setup, or currently authorized action, with a short reason available. Never use “current” to imply operating. |
| owning | 3 | Replace “owning work area/action/capability” with a direct task or responsible role. Use ownership only when organizational responsibility is the subject. |
| accountable mechanism | 3 | Show the responsible role or established governance process. The formal mechanism and identity belong in trace/review. Never ask for an unexplained free-text mechanism if the system can resolve it. |
| substantive authority | 3 | In ordinary work use **authority to make this Decision**. Use the formal distinction when explaining why software permission is insufficient. |
| Record | 4 | Do not use as a primary label. Technical inspection may show Record ID with the management object name. |
| Version | 3/4 | Use **version reviewed**, **prior version**, or **history** in governance trace. Raw Version ID is technical inspection. |
| effective time | 3 | Use **applies from / applied at** in history and reconstruction. |
| known time | 3 | Use **information recorded by / what was known by** in reconstruction. |
| provenance | 3 | Prefer **source and history**. Formal provenance fields belong in governance trace; raw payload fields belong in technical inspection. |

## Additional internal vocabulary

The following remain engineering/internal unless a diagnostic task requires them: command, gateway,
adapter, record family, UUID, foreign key, enum value, idempotency key, projection, payload checksum,
schema status, and resolver output.

## Wording patterns

| Avoid in ordinary workflow | Prefer |
|---|---|
| Open owning work area | Review what is known and unresolved |
| Review designation as governing | Use this setup for the assessment |
| No exact Applicability determination | You have not yet decided whether this information bears on the proposed pilot |
| Value selection not established | Choose which sufficiently supported Value assessment management will use |
| Integration not established | Complete the Value and Risk selections before recording the management judgment |
| Accountable mechanism | Responsible role or governance process, resolved where uniquely established |
| Current governing Configuration | Proposed pilot setup used for this assessment |
| Identity and provenance | Practitioner workspace; Source, history, and governance basis; Technical inspection |

## Review rule

Classification is audience- and task-dependent. A formal term may be appropriate in a confirmation,
conflict explanation, audit review, or reconstruction even when it is inappropriate as the ordinary
navigation label. Implementation review must assess each occurrence, not apply a global word ban.
