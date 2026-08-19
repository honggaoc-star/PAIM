# PAIM Increment 7 Management Register Design Decision v0.1

## 1. Purpose and baseline

This artifact proposes the bounded human design package required to resolve IRR-012 before Increment 7 implementation. It is a design-analysis proposal for independent PAIM design-authority review. It is not a governing specification and does not authorize implementation.

The analysis starts from accepted Increments 1–6 at merge commit `5a4ab92e12270f8bc9df83cab862119d2f337c20`. It preserves authoritative source-family ownership, exact version binding, dual-time reconstruction, explicit absence/conflict, Case independence, Value/Risk independence, and authority-first action.

The following current repository contracts were reviewed:

- `PAIM_CODEX_IMPLEMENTATION_READINESS_REVIEW_v0.1.md`, especially IRR-012 and INV-012/INV-015;
- `PAIM_PLATFORM_ARCHITECTURE_v0.1.md`, especially §§5.12, 7.6–7.7, 13, 16, 18, 20, and 23;
- `PAIM_IMPLEMENTATION_SEQUENCE_AND_P1_GATES_v0.1.md`, especially the Increment 7 gate;
- `PAIM_MANAGEMENT_REGISTER_SPEC_v0.1.md` in full;
- the current System Record and Decision Integrity, Case Lifecycle, Managed Configuration, Roles and Accountability, Evidence and Authority, Value/Risk Interface, Integration and Decision, Intervention and Learning, and Reassessment specifications;
- `PAIM_SYSTEM_BEHAVIORAL_VALIDATION_STRATEGY_v0.1.md`, especially §§25–30; and
- the Increment 1–6 implementation only to confirm which authoritative source facts currently exist.

Current governing specifications control if this proposal conflicts with them.

This artifact creates no Observation contract, operating-state ordering, code, schema, migration, API, projection, UI, or executable test.

## 2. Original IRR-012 ambiguity

The Management Register is declared derived, but the specifications do not yet determine:

- which exact source facts create current management attention;
- how multiple facts in one or several families become distinct entries rather than one lossy summary;
- whether proposed or decisionless Configurations appear;
- what stable identity makes providers, models, controls, capacity, or other dependencies the same across Cases;
- what cross-Case aggregation means without transferring authority, resolution, or satisfaction;
- how conflicts, stale projections, correction, supersession, and historical views behave; or
- whether a dashboard action edits a row, invokes an existing authoritative command, or creates a new substantive determination.

Without these decisions, software could choose the newest fact, merge similar names, hide competing facts behind one status, treat a count as risk, dismiss unresolved work, or let a queue become an unauthorized workflow.

## 3. Fixed upstream invariants from Increments 1–6

1. Authoritative records retain stable Record IDs, immutable Version IDs, exact relationships, effective time, recorded time, provenance, and correction/supersession/withdrawal history.
2. Current selection is always for explicit family, subject, scope, purpose, effective time, and optional knowledge cutoff. It returns one eligible version, explicit absence/not established, or explicit conflict with all candidates.
3. No newest, broadest, most specific, highest severity, row order, role hierarchy, queue order, owner, or software permission may select an authoritative winner unless a governing rule expressly authorizes it.
4. The Register, projections, dashboards, queues, reports, exports, attention indicators, and notification intents are derived. They never override or replace authoritative source records.
5. Every derived fact retains exact source Version IDs, effective and knowledge time, projection rule/version, watermark, and absence/conflict/indeterminate state.
6. A Case has at most one governing Configuration at an effective time. A Configuration identity has exactly one owning Case. Proposed, experimental, alternative, or fallback purpose is not governing currentness or authorization.
7. Independent concurrent governing Configurations use separate linked Cases. A Case link does not transfer evidence, authority, ownership, satisfaction, or dependency identity.
8. Value and Risk remain separately attributable and independently current, accepted, frozen, refreshed, conflicted, and displayed.
9. Evidence Applicability is target/version specific. Similar Evidence, attachment, provider name, or prior applicability does not establish current applicability.
10. Authority Gaps and Decision Authority Gaps remain explicit and never imply permission.
11. Decision conditions, uncertainty, Boundary, Authorization Basis, Intervention obligations, Completion Acceptance, activation, Learning, Triggers, Reassessments, Trigger Coverage, Interim Operating Dispositions, Confirmation, and successor Decisions retain their accepted independent meanings.
12. Required-before aggregation, Reassessment coverage, and restrictive Interim Disposition overlay already have their own authoritative derivation rules. The Register reports those results and does not recompute them under a different rule.
13. One Case resolving, completing, or closing does not resolve another Case, even where provenance or a dependency is shared.
14. Software access, report authorship, dashboard ownership, queue administration, and technical principal identity do not create substantive PAIM accountability or authority.
15. Historical views must be reconstructable for effective time and recorded-knowledge cutoff without later facts rewriting what was known.

### Topic classification

| Area | Classification | v0.1 disposition |
|---|---|---|
| Non-authoritative Register boundary | Fixed upstream | Preserve exactly. |
| Current selection, dual time, and conflict | Fixed upstream | Reuse authoritative family queries; do not invent projection selection. |
| Value/Risk independence | Fixed upstream | Project as separate concern dimensions and entries. |
| Concern-entry identity and population | Human design choice | Resolve in D2–D4. |
| Shared-dependency identity and cross-Case grouping | Human design choice | Resolve in D5–D7 and D12. |
| Attention ordering and closure | Human design choice | Resolve in D8–D11. |
| Physical projection/cache technology | Non-blocking engineering choice | Defer under §9. |
| Observation persistence/conversion | IRR-009 deferred | Exclude under D15. |
| Operating-state strength/rank | IRR-014 deferred | Exclude under D16. |

## 4. Genuine human decisions D1–D16

### D1. Register authority model

**Decision question.** Is the Register itself authoritative, partly authoritative, or entirely derived while substantive actions remain in owning domains?

**Viable alternatives.** (1) Authoritative Register rows; (2) hybrid rows with editable dispositions; (3) a purely rebuildable Register whose actions invoke separately authoritative domain commands or determinations.

**Recommendation.** Adopt alternative 3. A Register row, attention state, group, count, acknowledgement, filter, sort, report, or notification has no substantive authority. New shared-dependency/equivalence determinations required by D5 are authoritative domain facts, not authoritative Register rows.

**Rationale.** Authoritative summaries duplicate and can diverge from source-family truth. The architecture already prohibits substantive Register edits and requires exact-source rebuildability.

**Audit/history/currentness/conflict implications.** Register outputs retain source manifests, query time, rule version, and watermark. Authoritative actions retain their own domain audit. Rebuild must reproduce the same output from the same basis. Source conflict remains conflict in the view.

**Software convenience must not decide.** A writable grid, cached status, dismissal button, or queue transition cannot create authority, resolve a source fact, or become the durable management record.

### D2. Register entry identity and granularity

**Decision question.** What is one stable Register entry when a Case/Configuration can have multiple simultaneous concerns?

**Viable alternatives.** (1) one row per Case or Configuration; (2) one row per exact source Version; (3) one stable concern entry per Case + Configuration context + concern kind + authoritative source Record identity; (4) one mutable entry per free-text management question.

**Recommendation.** Adopt alternative 3. A base **Register Concern Entry** key is:

`owning Case ID + applicable Configuration ID (or explicit absence) + concern kind + source family + source Record ID`.

The selected source Version changes over time without changing the concern-entry identity. A materially different source Record or concern kind creates another entry. Where an authoritative aggregate already has stable identity—such as an Obligation Set result or Trigger Coverage result—the aggregate subject Record ID is the source identity and all contributing versions remain linked. Configuration-summary rows and shared-dependency groups are presentation groupings over concern entries, not entry identities.

Decisionless/proposed work is not omitted: a finalized non-governing Configuration may appear when an eligible authoritative source fact creates attention, with governing Configuration/Decision explicitly `NOT ESTABLISHED` where applicable. A mere draft or inventory mention creates no authoritative entry.

**Rationale.** One row per Configuration collapses plurality; one row per Version creates churn; the recommended key preserves the continuing management subject while exact Versions preserve history.

**Audit/history/currentness/conflict implications.** Each rendering names the selected source Version(s). Correction or supersession changes prospective rendering but preserves earlier views. Co-current incompatible Versions make the concern entry `CONFLICT`; they do not create an arbitrary winner.

**Software convenience must not decide.** Table row IDs, hashes of display text, titles, provider names, and UI grouping cannot establish concern identity.

### D3. Population eligibility

**Decision question.** Which authoritative facts create current attention or current informational entries?

**Viable alternatives.** (1) every source row; (2) a hard-coded “worst status” per family; (3) explicit family-specific eligibility rules over authoritative current-selection results.

**Recommendation.** Adopt alternative 3. The v0.1 eligibility matrix is:

| Source family/result | Current Register treatment |
|---|---|
| Governing Configuration / current Decision / Boundary / Authorization Basis | Configuration position; absence or conflict is attention. |
| Finalized non-governing proposed/experimental Configuration | Show only when linked eligible work or an explicit attention fact exists; label non-governing and not authorized. |
| Authority Gap or Decision Authority Gap | Open/unresolved/conflicted gap is attention; resolved gap is historical. |
| Value Input selection/fitness | Keep Value separate; absence, conflict, rejected/withdrawn current eligibility, or explicit refresh-required affecting current/proposed use is attention. Competing non-selected history remains drill-down, not silently “worst.” |
| Risk Input selection/fitness | Same independent rule for Risk. Never combine with Value. |
| Evidence Applicability | Missing required applicability, current conflict, `NOT_APPLICABLE`, material unresolved `INDETERMINATE`, or explicit `REFRESH REQUIRED` is attention for the exact target/use; conditional/partial facts display exact limitations. |
| Decision uncertainty and conditions | Display exact accepted uncertainty and conditions informationally; explicit Decision-Limiting, blocked, due, breached, or conflicted facts create attention. Do not infer stronger-state blockage. |
| Intervention Obligation / aggregate | `INCOMPLETE`, `BLOCKED`, `CONFLICT`, or `NOT_ESTABLISHED` creates attention according to the exact requirement type; `SATISFIED`/`NOT_REQUIRED` remains current position/history. Completion without eligible Acceptance remains attention. |
| Learning Item | Active, blocked, failed, inconclusive, overdue, or required incomplete commitment creates attention; completion does not change Decision automatically. |
| Trigger Determination/Coverage | `REASSESSMENT_REQUIRED_UNASSIGNED`, `BLOCKED_CONFLICT`, coverage conflict, or determination conflict creates attention. Informational/monitor outcomes display only where the source explicitly requires current attention. |
| Reassessment | Eligible active, overdue, owner-vacant/conflicted, overlap-conflicted, or outcome-blocked Reassessment creates attention; completed/cancelled/superseded is historical unless another current concern cites it. |
| Interim Operating Disposition | Each current exact-scope partition is visible; suspension, conflict, or approaching explicit expiry may be attention only from exact source facts/configured date rules. No state rank. |
| Lifecycle/currentness/integrity | Illegal, absent, stale, or conflicting current governance and explicit Boundary breach/integrity facts create attention when an accepted source family records them. |
| Role/accountability | Vacancy/conflict creates attention only for an identified current obligation; a role assignment by itself is not a concern. |

Other source families may be added only by a versioned projection rule accepted against their governing specification. Raw telemetry, drafts, text similarity, and unsupported inferred conditions are ineligible.

**Rationale.** Eligibility follows management meaning already established upstream and preserves multi-valued facts.

**Audit/history/currentness/conflict implications.** Each family adapter records the rule version and exact input versions. Ineligibility is prospective and never deletes history. Conflicts remain first-class entries.

**Software convenience must not decide.** Null checks, enum ordering, one generic traffic light, “latest status,” or whichever table is easiest to query cannot define attention.

### D4. Population timing and currentness

**Decision question.** Is population query-derived, asynchronous, or governed by explicit refresh?

**Viable alternatives.** (1) derive every view directly; (2) asynchronous materialized projection; (3) manually governed refresh; (4) semantic authority from direct derivation with either direct or materialized delivery.

**Recommendation.** Adopt alternative 4. The authoritative answer is the deterministic derivation for declared `effective_at`, optional `known_at`, and projection-rule version. Increment 7 may materialize it asynchronously for performance. A materialized view is claimable as current only when its watermark proves processing through the relevant authoritative recorded-time high-water mark under the active rule version. Otherwise it is visibly `STALE` or rebuilt before “current” is claimed.

**Rationale.** This separates PAIM semantics from delivery technology while preventing stale cache from masquerading as truth.

**Audit/history/currentness/conflict implications.** Every response exposes calculation time, effective time, known-at cutoff, watermark, rule version, and inconsistency marker. Guarded commands re-evaluate authoritative facts rather than trusting projection state.

**Software convenience must not decide.** Poll frequency, event arrival order, cache TTL, refresh button use, or last-write timestamp cannot define authoritative currentness.

### D5. Shared-dependency identity and equivalence

**Decision question.** What proves that facts or Cases share one provider/model/control/capacity dependency?

**Viable alternatives.** (1) normalized names; (2) semantic/AI matching; (3) exact same authoritative dependency Record identity only; (4) exact identity plus an accountable equivalence determination into one stable Shared Dependency identity.

**Recommendation.** Adopt alternative 4. Sharing exists only through:

1. citation of the same exact stable authoritative dependency Record ID; or
2. one eligible authoritative **Shared Dependency Equivalence Determination** that binds exact candidate dependency references to one stable Shared Dependency ID, typed dependency kind, explicit equivalence scope, rationale, accountable provenance, effective/recorded time, and immutable history.

The same Evidence source, provider string, model label, control description, organization owner, URL, or external event provenance is not itself a shared dependency unless it is the exact dependency identity or an eligible determination establishes equivalence. Equivalence may be scope-limited; it does not rewrite candidate identities.

**Rationale.** Equivalence creates substantive portfolio meaning. Exact identity is mechanically safe; broader equivalence requires accountable judgment.

**Audit/history/currentness/conflict implications.** Current selection of determinations returns one eligible equivalence, `NOT ESTABLISHED`, or explicit conflict. Correction/supersession is prospective. Every group retains candidates and determination Version.

**Software convenience must not decide.** Case folding, aliases, fuzzy matching, embeddings, vendor normalization, URLs, ownership, or co-occurrence cannot merge dependencies or select a canonical identity.

### D6. Cross-Case aggregation

**Decision question.** When may Case-scoped concerns appear together, and what remains independent?

**Viable alternatives.** (1) group by any common label/owner/domain; (2) prohibit all cross-Case grouping; (3) descriptively group only by exact Shared Dependency identity while preserving Case-local facts.

**Recommendation.** Adopt alternative 3. A grouped view may collect concern entries from different Cases only when D5 establishes the same Shared Dependency ID and the view declares the concern/dependency dimensions. Every constituent retains its Case, Configuration, source Versions, owners, authorities, status, and outcome.

Common provider provenance, organizational owner, Value/Risk domain, or text may be used as a filter but does not establish shared identity. Grouping never transfers authority, evidence applicability, Decision effect, Intervention satisfaction, Trigger coverage, Reassessment outcome, closure, or accountability.

**Rationale.** Management gains portfolio visibility without constructing a cross-Case authority model.

**Audit/history/currentness/conflict implications.** Group membership is reproducible from exact entry bases and equivalence determinations. A Case joining/leaving changes the prospective group view only. Conflicted constituents stay identified.

**Software convenience must not decide.** SQL grouping columns, shared owner, business unit, provider name, or dashboard filters cannot create substantive sameness.

### D7. Aggregation semantics and concentration

**Decision question.** Which cross-entry summaries are safe, and when does a count become a substantive concentration judgment?

**Viable alternatives.** (1) derived universal risk/severity score; (2) exact descriptive aggregates only; (3) descriptive aggregates plus separately accountable concentration classification.

**Recommendation.** Adopt alternative 3, with no mandatory concentration classification in v0.1. Safe derived fields are exact counts and sets: affected Case/Configuration IDs and counts, concern counts by exact kind/state, unresolved/conflict counts, exact obligation counts, explicit due-date ranges, age from recorded dates, current blocker-presence flags, exact source materiality labels, and exact dependency exposure sets.

“Concentration” without qualification means only a descriptive exposure count/set for one established Shared Dependency identity. Any label such as `MATERIAL CONCENTRATION`, threshold, escalation, or management consequence is a separate accountable **Concentration Determination** (or an accepted versioned organizational mechanism) with scope, inputs, rationale, time, and history.

**Rationale.** Exact counting is reproducible; interpreting whether the count matters is human management judgment.

**Audit/history/currentness/conflict implications.** Aggregates retain constituent manifests and rule version. Conflict counts conflict; it does not resolve it. A later classification does not rewrite earlier descriptive views.

**Software convenience must not decide.** A chart threshold, color scale, percentile, average, maximum enum, or count cannot silently become risk, severity, priority, or authority.

### D8. Priority and attention ordering

**Decision question.** What ordering is presentation, and what ordering changes substantive priority?

**Viable alternatives.** (1) universal derived priority score; (2) chronological queue only; (3) user-selected sorting and explicit-source ordering, with substantive priority only from authoritative facts/determination.

**Recommendation.** Adopt alternative 3. Safe presentation sorts include exact authoritative due date, effective/recorded date, age, Case/Configuration/dependency identity, exact lifecycle/blocker category, and user-selected fields. Explicit authoritative materiality or priority labels may be displayed and sorted as source identities. Sorting changes no source status or authority.

No cross-family “worst,” severity rank, state rank, or weighted score exists. If management needs substantive prioritization beyond exact source facts, it requires a separately accepted accountable prioritization determination or versioned policy outside this Increment 7 v0.1 package.

**Rationale.** Discoverability can be deterministic without claiming that presentation order is management judgment.

**Audit/history/currentness/conflict implications.** Reports/exports retain filter and sort basis. Interactive sorts need not be authoritative but must be visible. Ties may use stable IDs solely for deterministic presentation.

**Software convenience must not decide.** Default UI order, timestamp, severity string, color, drag-and-drop, row position, or notification frequency cannot establish substantive priority.

### D9. Conflict and ambiguity

**Decision question.** How does the Register treat upstream conflict, absence, indeterminacy, staleness, supersession, or withdrawal?

**Viable alternatives.** (1) choose newest/majority; (2) omit unresolved facts; (3) preserve exact states and candidates, aggregating only facts that do not require a winner.

**Recommendation.** Adopt alternative 3. `CONFLICT`, `NOT ESTABLISHED`, `INDETERMINATE`, `STALE`, and `PROJECTION INCONSISTENCY` are visible states with exact candidates/reasons. A conflict may be grouped descriptively and counted, but fields requiring a single winner remain unset/conflicted. Superseded/withdrawn/ineligible facts leave the prospective current view and remain historical.

**Rationale.** The Register must expose management uncertainty, not repair it.

**Audit/history/currentness/conflict implications.** Conflict entries preserve all candidates and selection context. Projection inconsistency triggers quarantine/rebuild and authoritative evaluation for commands.

**Software convenience must not decide.** Newest, majority, non-null, shortest path, one database row, or aggregation function cannot resolve ambiguity.

### D10. Register lifecycle and closure semantics

**Decision question.** When is a concern open, resolved, superseded, withdrawn, historical, or conflicted?

**Viable alternatives.** (1) editable Register lifecycle; (2) derived lifecycle from source eligibility/currentness; (3) hybrid operator dismissal plus source state.

**Recommendation.** Adopt alternative 2. Derived categories are:

- `CURRENT_ATTENTION` — eligible current source result requires attention;
- `CURRENT_CONFLICT` — eligible current selection/aggregate is conflicted;
- `CURRENT_INFORMATIONAL` — current fact is intentionally visible but not itself unresolved work;
- `RESOLVED_HISTORICAL` — source authoritatively resolved/satisfied/completed and no current attention rule applies;
- `SUPERSEDED_HISTORICAL` — source subject has an eligible successor;
- `WITHDRAWN_OR_INELIGIBLE_HISTORICAL` — prospective reliance ended; and
- `PROJECTION_STALE_OR_INCONSISTENT` — delivery state, never source resolution.

Entries do not close independently. They cease current attention only when authoritative source selection and the versioned population rule produce that result. A dependency group remains partially unresolved while any constituent is current attention/conflict; when all cease, it leaves current attention and remains reconstructable.

**Rationale.** Independent closure would let the summary override obligations.

**Audit/history/currentness/conflict implications.** Historical category is derived as-of time. Dismissal or personal read state can be non-authoritative preference only and cannot suppress required organizational views.

**Software convenience must not decide.** Checkbox, archive, acknowledgement, snooze, notification read, or row deletion cannot resolve a concern.

### D11. Human management actions in Register context

**Decision question.** Which actions are permitted from the Register and where do their authoritative effects live?

**Viable alternatives.** (1) generic editable actions on Register rows; (2) read-only Register; (3) contextual launch of explicit domain commands plus narrowly defined non-authoritative UI preferences.

**Recommendation.** Adopt alternative 3:

| User intent | v0.1 treatment |
|---|---|
| Assign owner | Invoke existing/new typed Role Assignment command for the exact owning domain target; never edit the row. |
| Acknowledge/read/snooze notification | Non-authoritative user preference only; cannot hide organizational current attention or change due/state. |
| Defer | Invoke an existing authoritative source-family command only if its specification permits deferral; otherwise unavailable. |
| Accept residual concern | Invoke Decision/uncertainty/authority command with its complete authorization basis; no generic Register acceptance. |
| Link shared dependency | Create D5 Equivalence Determination under D12 accountability. |
| Link duplicate | Invoke the owning family’s accepted duplicate/identity command; never generic text deduplication. |
| Create Trigger/Reassessment | Invoke existing Increment 6 commands and all accountability/current-governance guards. |
| Create/modify Decision or Intervention | Invoke the owning Increment 4/5 commands and guards. |
| Mark resolved | Unavailable generically; resolve through the authoritative source family. |

**Rationale.** The Register can be an effective work surface without becoming a competing command model.

**Audit/history/currentness/conflict implications.** Each command audit links launch context optionally but the owning authoritative record is the effect. Failed commands leave no source or Register resolution.

**Software convenience must not decide.** Button placement, permission to edit a dashboard, or bulk selection cannot bypass domain accountability, authority, completion acceptance, or conflict guards.

### D12. Accountability for dependency and aggregation determinations

**Decision question.** Who may establish equivalence or substantive concentration meaning?

**Viable alternatives.** (1) System Administrator/Register Curator by permission; (2) existing Case Owner or Decision Authority implicitly; (3) a new substantive Shared Dependency Determiner function, with separate dependency ownership where used.

**Recommendation.** Adopt alternative 3. Add a **Shared Dependency Determiner** accountable function for Equivalence Determinations and optional Concentration Determinations. A general Management Register Curator is unnecessary because projection rules are governed system design, not case-by-case judgment.

Typed applicable targets are:

- `DEPENDENCY_CANDIDATE_SET`: exact typed candidate Record/Version references plus declared equivalence scope; and
- `SHARED_DEPENDENCY`: exact stable Shared Dependency ID for correction, supersession, or concentration classification.

Resolution returns exactly one eligible accountable assignment/mechanism, explicit vacancy/not established, or explicit accountability conflict. Broad/narrow assignments have no implicit precedence. A Shared Dependency Owner may coordinate work after identity is established but does not replace Case Owners, source owners, Reassessment functions, Completion Acceptors, or Decision Authorities.

**Rationale.** Equivalence and material concentration are substantive cross-Case judgments not owned by any one Case merely because it appears first.

**Audit/history/currentness/conflict implications.** Determinations retain exact target set, outcome, rationale, actor, assignment/mechanism Version, delegation, effective/recorded time, and immutable history. Incompatible co-current determinations are explicit conflict and do not group authoritatively.

**Software convenience must not decide.** Dashboard ownership, report authorship, directory group, queue administrator, System Administrator, source owner, majority of Case Owners, or software permission does not establish equivalence.

### D13. Historical reconstruction

**Decision question.** What basis must be retained to reconstruct a past Register view?

**Viable alternatives.** (1) retain rendered rows only; (2) rebuild only from latest source history; (3) retain/reconstruct exact query and aggregation basis.

**Recommendation.** Adopt alternative 3. A reconstructable view/export manifest contains:

- requested scope, `effective_at`, `known_at`, and requesting access context where relevant;
- projection/population/aggregation rule IDs and Versions;
- every selected source Record and Version ID and explicit absent/conflict candidates;
- Shared Dependency and Equivalence/Concentration Determination IDs/Versions;
- constituent concern-entry keys and group membership;
- calculation time, source recorded-time high-water mark, projection watermark, and inconsistency state; and
- visible filter, grouping, and ordering basis.

Rendered snapshots may be retained for evidence/performance, but exact source reconstruction is controlling.

**Rationale.** Latest-only rebuild cannot reproduce knowledge-time views after backdated correction.

**Audit/history/currentness/conflict implications.** Later corrections or rule changes create different views under different basis Versions without rewriting the old basis.

**Software convenience must not decide.** Export file order, cache snapshot, current rule code, or latest source version cannot substitute for the historical manifest.

### D14. Reports, queues, and notification hooks boundary

**Decision question.** Can an Increment 7 output change source state?

**Viable alternatives.** (1) outputs directly mutate state; (2) all outputs are non-authoritative and may only link to/invoke commands; (3) reports authoritative, dashboards derived.

**Recommendation.** Adopt alternative 2. Dashboards, queues, reports, export snapshots, drill-down views, search indexes, attention indicators, schedules, and notification intents are filtered/rendered projections. Delivery receipt is a technical fact. None resolves, prioritizes, authorizes, satisfies, closes, or changes a source record. Contextual actions invoke D11 commands.

**Rationale.** Delivery channel must not change PAIM semantics.

**Audit/history/currentness/conflict implications.** Outputs expose basis, watermark, generation time, staleness, and conflict. Notification retries/delivery do not duplicate or change source facts.

**Software convenience must not decide.** Queue dequeue, report sign-off, email click, export edit, webhook success, or notification acknowledgement cannot be a substantive transition.

### D15. IRR-009 boundary

**Decision question.** Does Increment 7 define Observation identity or automatic Observation population?

**Viable alternatives.** (1) add Observation now; (2) treat telemetry as Register facts; (3) exclude Observation authority and accept only existing authoritative source families.

**Recommendation.** Adopt alternative 3. No first-class Observation persistence, monitoring-record identity/version/cardinality, retention policy, or Observation-to-Register conversion is decided. External monitoring may appear only after entering an accepted existing source family with retained provenance, or as clearly non-authoritative UI context outside Register authority.

**Rationale.** Otherwise Increment 7 would silently resolve IRR-009.

**Audit/history/currentness/conflict implications.** No authoritative concern entry cites an unaccepted telemetry object as its source.

**Software convenience must not decide.** Available logs, metrics, alerts, monitoring IDs, or adapter payloads cannot create Register truth.

### D16. IRR-014 boundary

**Decision question.** May Register aggregation or ordering infer operating-state strength, breadth, restriction, severity, or escalation rank?

**Viable alternatives.** (1) rank labels lexically/configurationally now; (2) display exact identities only; (3) infer from apparent workflow order.

**Recommendation.** Adopt alternative 2. Exact operating-state values and exact authorized applicability may be displayed, filtered, counted, and grouped by identity only. No `stronger`, `broader`, `more restrictive`, severity, escalation, target-state, or priority relation is inferred.

**Rationale.** Those semantic relations remain IRR-014.

**Audit/history/currentness/conflict implications.** Views preserve exact source values and do not map them to an ordinal. Distinct values remain distinct, not conflicting merely because they differ across Cases.

**Software convenience must not decide.** Enum order, label wording, color, workflow sequence, numeric code, frequency, or product convention cannot establish rank.

## 5. Recommended v0.1 design package

Accept D1–D16 as one coordinated package:

1. The Management Register is a purely derived, rebuildable portfolio read model.
2. Its base unit is a stable Case/Configuration-scoped concern entry keyed to one authoritative source Record identity and concern kind; source Versions remain exact and plural conflict is preserved.
3. Population uses the explicit family eligibility matrix in D3, including finalized proposed/decisionless work only when authoritative attention exists.
4. Semantic currentness comes from authoritative dual-time derivation; materialization is allowed only with visible watermark/staleness.
5. Shared identity requires the same exact dependency Record ID or one accountable Equivalence Determination into a stable Shared Dependency identity.
6. Cross-Case grouping is descriptive and never transfers authority, satisfaction, outcome, closure, or ownership.
7. Exact counts/sets are safe; substantive concentration requires a separate accountable determination or accepted mechanism.
8. Sorting is presentation unless an explicit authoritative source fact or later accepted determination establishes priority.
9. Conflict/absence/indeterminacy/staleness remain visible; no winner is selected.
10. Entry lifecycle and closure derive from source currentness; operator dismissal has no authoritative effect.
11. Register actions invoke owning authoritative commands. Shared dependency meaning is governed by a new Shared Dependency Determiner function.
12. Historical views retain exact source, determination, rule, time, watermark, filter, group, and ordering basis.
13. Reports, queues, exports, and notifications remain non-authoritative.
14. IRR-009 and IRR-014 remain explicitly deferred.

## 6. Thirty hard-oracle scenario analyses

| # | Scenario | Deterministic recommended outcome |
|---:|---|---|
| 1 | One unresolved Authority Gap | One `CURRENT_ATTENTION` concern cites the exact Gap Version, Case/Configuration/Decision context, and unresolved state. |
| 2 | Gap later resolves | It leaves current unresolved attention and becomes `RESOLVED_HISTORICAL`; past effective/knowledge views still show the unresolved Version. |
| 3 | Two Cases cite same provider Evidence source with different applicability | Separate Case/target concern entries and outcomes remain independent. Evidence-source equality does not itself establish a Shared Dependency. |
| 4 | Two Cases share one exact dependency identity | A descriptive dependency group may show both exact constituent entries and counts; no authority, applicability, or closure transfers. |
| 5 | Similar provider names without equivalence | No shared group is created. Name similarity may be a search result only. |
| 6 | Intervention obligation is `BLOCKED` | Current attention cites exact Obligation, Intervention, aggregate result, requirement type, and operational consequence. |
| 7 | Required-before satisfied; required-after incomplete | Activation history remains unchanged. Required-before is satisfied; the required-after commitment remains a separate current attention item when its exact rule says incomplete attention. |
| 8 | Trigger is `REASSESSMENT_REQUIRED_UNASSIGNED` | Current attention is visible with exact Trigger Version and coverage result. |
| 9 | Trigger Coverage conflict | `CURRENT_CONFLICT` displays every incompatible coverage candidate/reason; no winner or disappearance. |
| 10 | Active and completed Reassessments share provenance | Active Reassessment is current attention as applicable; completed one is historical. Provenance does not merge identities or outcomes. |
| 11 | Two Cases share provider name only | No dependency identity or aggregation is inferred. |
| 12 | Shared dependency, different owning authorities | Group is allowed descriptively, but each Case’s authority/accountability remains visible and independently effective. |
| 13 | Upstream record prospectively superseded | Current concern selects successor truth; predecessor becomes `SUPERSEDED_HISTORICAL`; earlier views remain exact. |
| 14 | Upstream current selection conflict | Concern is `CURRENT_CONFLICT` with all candidates; newest is not selected. |
| 15 | Projection behind authoritative recorded time | UI shows `STALE` and watermark, or rebuilds before claiming current; guarded commands use authoritative evaluation. |
| 16 | User dismisses unresolved row | Only optional personal presentation state changes. Organizational current attention and authoritative source remain visible/unresolved. |
| 17 | User sorts by age | Display order changes; no substantive priority, state, authority, or notification obligation changes. |
| 18 | User sorts by explicit due date | Display orders by the exact source due-date values and retains the sort basis; no new priority meaning is created. |
| 19 | Similar semantic text, no exact dependency | No automatic grouping or identity. Semantic similarity is ineligible. |
| 20 | Accountable equivalence groups two items | Group cites stable Shared Dependency ID, exact candidates, Equivalence Determination Version, rationale, actor/accountability, and dual time. |
| 21 | Incompatible equivalence determinations | Explicit equivalence conflict; no canonical dependency winner and no authoritative combined group. Candidate concerns remain visible independently. |
| 22 | Group shows affected-Case count | Count is exact and descriptive, with constituent set; it is not risk, severity, materiality, or priority. |
| 23 | One shared-dependency Case resolves locally | That constituent becomes historical/resolved; group remains partially unresolved while the other Case remains current. No cross-Case satisfaction. |
| 24 | All constituents resolve | Group leaves current attention/derives resolved according to D10; exact historical group membership and source basis remain reconstructable. |
| 25 | Register action opens Reassessment | It invokes Increment 6 commands and must pass Trigger Determiner/Reassessment Owner/coordination/current-governance rules; Register permission adds nothing. |
| 26 | Attempt to mark blocked Intervention resolved without Acceptance | Rejected or has no authoritative effect. Blocked attention remains until exact Completion Result and eligible Completion Acceptance satisfy governing rules. |
| 27 | Two Cases show different operating-state values | Values display/group only as identities; no rank, strength, severity, or winner is inferred. |
| 28 | External Observation-like data not in accepted source family | No authoritative Register concern is created. It may be labeled non-authoritative UI context only. |
| 29 | Notification intent from unresolved work | Intent cites exact concern basis and is non-authoritative. Generation/delivery/retry does not change source or attention state. |
| 30 | Historical as-of view | Reconstruct exact source Versions, conflicts, equivalence determinations, rule version, effective time, knowledge cutoff, watermark/basis, grouping, filter, and ordering visible then. |

## 7. Cross-spec implications

If accepted, later specification hardening should be coordinated and bounded:

- **Management Register specification:** replace “normally one Configuration under a current Decision” ambiguity with concern-entry identity, proposed/decisionless eligibility, D3 population matrix, derived lifecycle, exact aggregation, conflict/staleness, and action boundaries.
- **System Record and Decision Integrity specification:** add Shared Dependency and Equivalence/Concentration Determination identity/history/current-selection invariants, Register reconstruction manifest, and no-cross-Case-transfer rules.
- **Roles and Accountability specification:** add Shared Dependency Determiner, typed targets, one/vacancy/conflict behavior, and clarify that dependency ownership is coordination rather than Case/Decision authority.
- **Managed Configuration specification:** permit explicit dependency references without changing one-Case ownership or governing cardinality.
- **Evidence/Authority, Value/Risk, Integration/Decision, Intervention/Learning, and Reassessment specifications:** add only conformance references to the D3 projection treatment; do not change their authoritative semantics.
- **Behavioral Validation Strategy:** add the 30 hard oracles, rebuild equivalence, watermark/inconsistency, conflict-display, exact-source, and no-authority-transfer tests.
- **Platform Architecture and implementation sequence:** mark IRR-012 normatively hardened only after coordinated specification acceptance and require independent gate-closure re-review before Increment 7 code.

This design does not itself modify any governing contract.

## 8. Explicit IRR-009 and IRR-014 deferrals

### IRR-009 remains open

No Observation Record, identity/version/cardinality, monitoring retention, automated monitoring intake, or Observation-to-Evidence/Trigger/Register conversion is defined. Existing authoritative PAIM source families and explicit accepted provenance remain the only authoritative population basis.

### IRR-014 remains open

No universal or organization-specific stronger/broader/restrictiveness relation, state severity, escalation rank, or state-derived priority is defined. Operating-state values remain exact identities only.

Neither deferral blocks the exact-source, non-ranked Increment 7 design in this artifact.

## 9. Non-blocking engineering choices

The following may be decided during bounded Increment 7 implementation without changing PAIM semantics:

- direct query versus asynchronous materialization, provided D4 currentness is preserved;
- relational views, projection tables, document indexes, or equivalent physical read-model storage;
- projector transaction/batch size, retry mechanism, checkpoint format, and rebuild scheduling;
- API protocol, pagination, stable cursor encoding, and response shape;
- dashboard layout, columns, visualizations, drill-down navigation, and saved-view implementation;
- search engine and exact-string alias support that is clearly non-authoritative;
- export format and notification channel;
- watermark encoding and operational lag thresholds, provided stale state is visible;
- performance indexes, partitioning, retention of disposable caches, and report rendering technology; and
- whether interactive filters/sorts are persisted as user preferences.

Engineering must still prove exact-source traceability, deterministic derivation, conflict preservation, rebuild equivalence, historical reconstruction, access filtering, and no derived-state use as unverified command authority.

## 10. Risks and tradeoffs

1. Concern-level entries create more rows than one-row-per-Configuration, but avoid hidden plurality and lossy “worst status” logic.
2. Accountable dependency equivalence adds curation effort, but prevents false portfolio meaning from names or AI matching.
3. Purely descriptive concentration may feel less decisive, but avoids inventing universal risk and leaves substantive interpretation attributable.
4. Visible staleness can make operational lag apparent, but is safer than false currentness.
5. Source-derived closure prevents convenient dismissal, but protects unresolved obligations and audit integrity.
6. A new Shared Dependency Determiner function requires Roles/specification hardening, but existing Case roles do not legitimately own cross-Case equivalence by default.
7. Historical manifests add storage and query complexity, but are necessary for exact knowledge-time reconstruction and rule-version changes.
8. Excluding semantic matching may miss candidate dependencies; software may suggest candidates as non-authoritative context, but only accountable determination establishes equivalence.

## 11. Questions requiring human acceptance

Independent design authority should explicitly accept or reject each point:

1. D1: Is the Register purely derived, with all substantive actions outside Register rows?
2. D2: Is the stable concern key Case + Configuration context + concern kind + source family/Record ID?
3. D3: Is the population matrix complete and appropriately bounded for v0.1?
4. D4: Is authoritative dual-time derivation controlling while asynchronous materialization remains allowed with visible watermark?
5. D5: Is exact dependency identity or accountable equivalence the exclusive sharing basis?
6. D6: Is cross-Case grouping descriptive only, with no transfer of authority/outcome/satisfaction?
7. D7: Are exact counts/sets safe while substantive concentration requires accountable determination?
8. D8: Is user/source sorting presentation only absent a separately governed prioritization decision?
9. D9: Must all conflict/absence/indeterminate/stale states remain visible with no winner?
10. D10: Is concern lifecycle derived exclusively from authoritative sources and rule versions?
11. D11: May Register context only invoke owning domain commands, never resolve generically?
12. D12: Should PAIM add the Shared Dependency Determiner function and typed targets proposed here?
13. D13: Is the historical reconstruction manifest sufficient?
14. D14: Are all reports, queues, exports, and notification intents non-authoritative?
15. D15: Is IRR-009 explicitly untouched?
16. D16: Is IRR-014 explicitly untouched?

Acceptance should be coordinated as one package because changing identity, authority, population, or closure affects every aggregation and historical oracle.

## 12. Recommended next step

If this design package is accepted, open one bounded specification-hardening issue to update the Management Register, System Record and Decision Integrity, Roles and Accountability, relevant conforming specifications, Platform Architecture/P1 gate status, and Behavioral Validation Strategy. Then conduct an independent focused IRR-012 gate-closure review. Do not implement Increment 7 until that review explicitly opens the gate.

