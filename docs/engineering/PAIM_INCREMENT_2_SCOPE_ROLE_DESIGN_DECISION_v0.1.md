# PAIM Increment 2 Scope and Role Design Decision v0.1

## Status

**PROPOSED — HUMAN DECISION REQUIRED**

This artifact resolves the design analysis required by IRR-007 and IRR-013/CON-002 sufficiently to expose the remaining PAIM semantic choices. It does not make those choices, amend a governing specification, authorize Increment 2 implementation, or define a physical schema, API, UI, identity provider, or permission engine.

## 1. Purpose and baseline

The purpose of this artifact is to prepare one coordinated human decision on the minimum scope, cardinality, role-assignment, accountability, and authority semantics required before PAIM Platform Architecture §23 Increment 2 may begin.

The engineering baseline is PAIM `main` at merge commit `c4e7602f91bbe593020ee7108bb8a50c4b93c2b3`, after accepted Increment 1A. The Increment 1A kernel supplies only domain-neutral identity, version, history, currentness, audit, and point-in-time mechanisms. It supplies no answer to IRR-007 or IRR-013/CON-002.

Governing sources are:

- `PAIM_IMPLEMENTATION_SEQUENCE_AND_P1_GATES_v0.1.md`;
- `PAIM_PLATFORM_ARCHITECTURE_v0.1.md`;
- `PAIM_CODEX_IMPLEMENTATION_READINESS_REVIEW_v0.1.md`;
- `PAIM_CASE_LIFECYCLE_SPEC_v0.1.md`;
- `PAIM_MANAGED_CONFIGURATION_SPEC_v0.1.md`;
- `PAIM_ROLES_AND_ACCOUNTABILITY_SPEC_v0.1.md`; and
- `PAIM_SYSTEM_RECORD_AND_DECISION_INTEGRITY_SPEC_v0.1.md`.

The governing system specifications control observable PAIM behavior. This artifact distinguishes constraints already fixed by those contracts from choices that still require PAIM design authority.

## 2. Governing constraints already fixed

The following are not open implementation choices.

### 2.1 Record identity, version, and currentness

- A stable Record ID identifies one continuing management subject; every durable content version has a distinct immutable Record Version ID.
- Finalized content is never edited in place. Corrections, amendments, supersessions, withdrawals, and status events preserve exact history.
- Currentness is derived for explicit subject, scope, purpose, effective time, and optional knowledge cutoff.
- Current selection returns exactly one eligible record, explicit absence/not established, or explicit incompatible-current conflict.
- Recency, breadth, row order, convenience, or permissiveness cannot silently select a winner.
- Multiple current records are permitted only in recorded, distinguishable, non-competing scopes.

These constraints are governed principally by Integrity §§3.1–3.12 and 8.

### 2.2 Configuration meaning

- A Managed Configuration is the bounded AI-enabled system of work, not an abstract model.
- A Case is a durable decision-centered management container, not merely an inventory row.
- A Case may compare multiple separately identifiable alternatives, including current, proposed, experimental, and fallback configurations.
- Configuration currentness, proposal/experimental/fallback purpose, Case lifecycle state, and AI operating state are distinct dimensions.
- AI operating state belongs to an authorized Decision, not inherently to Configuration identity.
- Every substantive finalized Configuration-content change creates an immutable version even when judged non-material to one Decision.
- A materiality judgment determines impact and routing; it does not authorize historical mutation.
- Evidence, frozen inputs, Decisions, Interventions, and Reassessments remain bound to exact Configuration versions.

These constraints are governed principally by Managed Configuration §§1–7, 11–12, 17–25 and Case Lifecycle §§1–3, 5–7, 13, and 18–23.

### 2.3 Identity, role, accountability, and authority separation

- An authenticated technical principal is not automatically a PAIM actor.
- A PAIM actor performing an action must remain attributable separately from the technical principal used to access the software.
- A Role Assignment describes a PAIM responsibility for a declared scope and effective period; it is not identical to software permission.
- Accountability for analysis, management judgment, execution, evidence, authority resolution, review, and technical administration remains functionally distinguishable even when one person holds several roles.
- System Administrator status does not confer substantive PAIM authority.
- Decision Authority must be established by legitimate organizational governance, delegation, policy, role, committee charter, or another legitimate mechanism.
- Every authorized Decision version requires exactly one complete logical Decision Authorization Basis binding the exact Decision, actor/mechanism, assignment and/or authority mechanism, delegation chain where used, scope, limits, effective period, and authorization event.
- Passing authentication and software access checks never proves Decision Authority.
- Missing, expired, revoked, out-of-scope, or conflicting authority blocks authorization and remains explicit.

These constraints are governed principally by Roles §§2–19, 23–27, and 35–39; Integrity §§5.2 and 6; and Platform Architecture §§5.1, 5.9, 5.13, 10, and 14.

### 2.4 Human judgment boundary

PAIM already requires accountable human or established-authority judgment for configuration materiality, same-identity/new-identity continuity, substantive role/authority legitimacy, and management authorization. The platform may validate completeness, scope, time, overlap, and conflict; it may not manufacture those judgments from technical access or schema defaults.

## 3. IRR-007 unresolved semantics

### 3.1 What remains genuinely unspecified

IRR-007 is not a gap in immutable version mechanics. It is a gap in the management scope against which those mechanics select a Configuration.

The specifications do not yet state:

1. whether every Configuration identity has exactly one owning Case, may be jointly owned by Cases, or exists independently and is related to Cases;
2. whether one Case may have only one governing Configuration at an effective time or may have several governing Configurations in distinguishable sub-scopes;
3. what the minimum sub-scope vocabulary is if several governing Configurations may coexist;
4. whether same-scope plural current Configurations are ever valid and, if so, what makes them compatible;
5. which authoritative relationship designates the Configuration relevant to Case lifecycle guards before and after a Decision;
6. which Configuration dimensions are authoritative currentness versus purpose labels such as proposed, experimental, alternative, or fallback;
7. which accountable role or mechanism makes and records materiality and same-identity/new-identity determinations; and
8. how disagreement or overlap in those determinations becomes explicit conflict rather than an implicit winner.

Cross-case shared provider, model, control, or dependency identity is not the same question as shared Configuration ownership and remains deferred with IRR-012 unless the human choice here requires otherwise.

### 3.2 Behaviors blocked by IRR-007

Until the questions above are resolved, implementation cannot safely:

- enforce the Case-to-Configuration relationship or its uniqueness;
- answer “the current Configuration for this Case” without an explicit purpose/scope;
- evaluate lifecycle guards that require a current/relevant Configuration;
- distinguish legitimate parallel configurations from incompatible current records;
- assign evidence, input, Decision, Intervention, or Reassessment routing to a Configuration by default;
- decide whether a change creates a new version, new Configuration identity, successor Case, or unresolved determination;
- build Register population or row-unit assumptions; or
- create indexes, constraints, or workflow defaults that embody one of those choices.

## 4. IRR-013/CON-002 unresolved semantics

### 4.1 The contradiction

Roles §3 includes Case ID in every Role Assignment identity, while Roles §26 permits assignments scoped to a configuration, decision, intervention, authority domain, business unit, or organization-wide function. An organization-wide assignment cannot truthfully carry a mandatory Case ID. Case ID must therefore be conditional on a typed scope, or broad assignments must be represented through a different explicit mechanism.

### 4.2 What remains genuinely unspecified

The specifications do not yet state:

1. the closed minimum set of Role Assignment target types required for Increment 2;
2. which target identifiers are required for each type;
3. whether a role may have one holder or several compatible holders for one scope/time;
4. whether every governed scope must identify exactly one accountable holder even when several people are responsible contributors;
5. whether broad and narrow assignments combine additively, use specific-over-general precedence, use explicit organizational policy, or remain an unresolved conflict;
6. how an assignment that is temporary, delegated, overlapping, vacant, expired, revoked, or superseded affects role resolution;
7. whether role resolution returns one assignment, several compatible assignments, absence, or conflict for each requested function;
8. who may assign or transfer accountability for materiality and identity determinations; and
9. how software permissions may be derived from resolved Role Assignments without implying Decision Authority.

Committee quorum, emergency authority, organization-wide RBAC templates, directory synchronization, and detailed segregation-of-duties policy remain organization/platform concerns unless later governing semantics require them.

### 4.3 Behaviors blocked by IRR-013/CON-002

Until the questions above are resolved, implementation cannot safely:

- represent organization-wide or business-unit assignments without fictitious Case IDs;
- resolve a role for a Case, Configuration, or Decision across simultaneous scopes;
- determine whether plural assignments are compatible or conflicting;
- identify the accountable holder for Configuration materiality/identity judgments;
- derive general role-based software access without hidden precedence;
- transfer open obligations deterministically when an assignment ends; or
- validate role-resolution examples beyond the exact Decision Authorization Basis rules already fixed.

## 5. Why the findings are coupled

Role scope cannot be typed until Configuration and Case scope are typed. Configuration materiality and identity continuity cannot be finalized until an accountable actor or mechanism is selected for the relevant scope.

The coupling is bidirectional:

```text
Case–Configuration ownership/cardinality
        ↓ defines targets
typed Role Assignment scope
        ↓ defines accountable holder/conflict
materiality and identity determination ownership
        ↓ governs
Configuration version/new-identity/successor-Case routing
```

Resolving only IRR-007 could leave materiality judgments unowned or accidentally assign them to the Case Owner by implementation convenience. Resolving only IRR-013 could define configuration-scoped roles against an unknown Configuration scope and introduce precedence that later selects a Configuration indirectly. Both findings must use the same scope vocabulary, time model, absence/conflict outcomes, and exact-version history.

## 6. Scope/cardinality alternatives

All alternatives below preserve one stable Configuration ID across immutable versions and preserve exact-version binding. They differ in Case ownership and in the scope at which one governing Configuration may be selected.

### 6.1 Alternative S1 — one governing Configuration per Case at an effective time

Model:

- each Configuration identity has exactly one owning Case;
- one Case may own several separately identifiable Configuration alternatives;
- exactly one Configuration is designated as the Case's governing/current Configuration at an effective time;
- proposed, experimental, alternative, and fallback configurations are purpose-designated but do not become a second governing current Configuration;
- independent simultaneous operation requiring different governing Configurations requires separate linked Cases.

Assessment:

| Criterion | Assessment |
|---|---|
| Semantic clarity | Highest. “Current Configuration for Case” has one answer or explicit absence/conflict. |
| Stable ID/version fit | Strong. The designation selects a Configuration identity/version without changing its content history. |
| Point-in-time/current selection | Simple Case-level designation history; overlap is conflict. |
| Later-layer effect | Value/Risk, Evidence, Decision, Reassessment, and Register receive one Case-level governing Configuration, while alternatives retain exact links. |
| Conflict behavior | Two effective governing designations for one Case/time are incompatible and block guarded use. |
| Migration/extensibility | A later move to sub-scopes requires introducing scope and possibly splitting historical Cases/designations. |
| Over-specification risk | Low technically, but it may over-constrain a real PAIM Case that legitimately manages concurrent bounded operating segments. |

This alternative is defensible only if PAIM v0.1 intends a Case to represent one governing configuration at a time and uses linked Cases for independent parallel operation.

### 6.2 Alternative S2 — one governing Configuration per Case plus explicit typed sub-scope

Model:

- each Configuration identity has exactly one owning Case;
- one Case may own several Configuration identities and alternatives;
- a governing designation is unique for `(Case, typed sub-scope, purpose, effective time)`;
- the minimum sub-scope is an explicit, stable Case-local managed segment; an unsegmented Case uses one distinguished whole-Case scope;
- configurations in different sub-scopes may be simultaneously governing; overlap within the same sub-scope/purpose is conflict;
- proposed, experimental, alternative, and fallback remain purpose dimensions and do not imply authorization or operation.

Assessment:

| Criterion | Assessment |
|---|---|
| Semantic clarity | Strong if the sub-scope identity and non-overlap rule are normative; weak if scope is free text. |
| Stable ID/version fit | Strong. Configuration identities and designation histories remain separate and exact. |
| Point-in-time/current selection | Deterministic for explicit Case + sub-scope + purpose; a scope-free “current” query is invalid or returns the complete partition, not one winner. |
| Later-layer effect | Supports exact segment binding for inputs, evidence, decisions, interventions, reassessments, and Register projections without making those layers multi-valued by accident. |
| Conflict behavior | Same-scope overlap is conflict; cross-scope coexistence is valid only when scopes are explicitly distinguishable. |
| Migration/extensibility | Moderate initial cost; easier future support for concurrent operating segments and later portfolio projections. |
| Over-specification risk | Moderate. Defining enterprise hierarchies or arbitrary nesting would exceed v0.1; one flat Case-local segment type avoids that. |

This alternative is the minimum extensible option if PAIM must support more than one governing Configuration within one Case.

### 6.3 Alternative S3 — plural concurrent governing Configurations in the same scope

Model:

- a Case may own or relate to multiple Configuration identities;
- several Configurations may be current for the same Case/scope/time;
- every downstream action supplies an explicit selected Configuration set or compatibility rule;
- coexistence is valid only when an explicit incompatibility/current-selection policy says so; otherwise the result is conflict.

Assessment:

| Criterion | Assessment |
|---|---|
| Semantic clarity | Lowest. “Current” becomes a set and every consumer needs selection/compatibility semantics. |
| Stable ID/version fit | Mechanically compatible, but family-specific eligibility becomes substantially more complex. |
| Point-in-time/current selection | Returns a permitted set only under a new substantive rule; otherwise Integrity §3.11 requires conflict. |
| Later-layer effect | Forces set cardinality and selection rules into Value/Risk, Evidence, Decision, Reassessment, and Register earlier than their own P1 resolutions permit. |
| Conflict behavior | High risk of hidden precedence or partial winners; explicit incompatibility explanations are mandatory. |
| Migration/extensibility | Most flexible but highest implementation and data-migration burden. |
| Over-specification risk | High. It anticipates enterprise portfolio/variant management not demonstrated as necessary for PAIM v0.1. |

This alternative is incompatible with Increment 2 unless the human decision also supplies complete set-selection and downstream compatibility semantics. It is not a safe permissive default.

### 6.4 Cross-case ownership variation

Any of S1–S3 could theoretically make Configuration identities independent of Cases or jointly owned. That variation is not recommended for v0.1. The current Managed Configuration record requires Case ID, Case is the decision-centered container, lifecycle guards are Case-scoped, and cross-case shared configurations remain explicitly open. A one-owning-Case rule with explicit related/successor Case relationships preserves current contracts while deferring shared dependency/equivalence to IRR-012.

## 7. Role/accountability/authority alternatives

### 7.1 Required conceptual separation

| Concept | Minimum meaning | Must not imply |
|---|---|---|
| Technical principal | Authenticated software/session identity that attempted an action. | PAIM role, accountability, or Decision Authority. |
| PAIM actor | Attributable person, committee, team, external party, or authorized mechanism performing a PAIM action. | Software access merely because an actor record exists. |
| Role Assignment | Versioned relationship assigning a named PAIM function to an actor for a typed target, effective interval, status, source, and optional delegation. | Substantive authorization outside the role's declared responsibility and scope. |
| Accountability | Explicit obligation to own a governed record, determination, or unresolved item for a scope/time. | Sole performance of every contributing task or Decision Authority. |
| Decision Authority | Legitimate power to authorize an exact management Decision within scope and time. | Validity from role label, directory group, platform permission, or approval click alone. |

### 7.2 Alternative R1 — single-holder Role Assignment for every role and scope

Model:

- each role type has at most one active assignment for one typed target/time;
- that holder is both the role performer and accountable holder;
- overlap is always conflict;
- temporary assignment replaces or suspends the ordinary assignment for the effective interval.

Assessment:

- **Clarity:** high; vacancy, one holder, and conflict are deterministic.
- **Small-organization fit:** simple, but the same actor may still hold multiple distinct roles.
- **Large/team fit:** poor for Value/Risk contributors, committees, shared owners, and co-owners.
- **Delegation:** simple replacement semantics but risks erasing the distinction between retained accountability and delegated performance.
- **Authority boundary:** compliant only if a Decision Authority role remains merely an input to the exact Authorization Basis; the role alone cannot authorize.
- **Over-specification risk:** low implementation complexity but high semantic rigidity.

### 7.3 Alternative R2 — plural role performers with exactly one accountable assignment where accountability is required

Model:

- a typed role/scope may have multiple compatible performer assignments;
- record families and determinations that require accountability designate exactly one accountable assignment for that obligation/scope/time;
- contributor or reviewer roles may be plural without a single designated accountable holder when the governing record does not require one;
- multiple eligible accountable designations for the same obligation/scope/time are conflict, not co-accountability by default;
- vacancy is explicit absence; temporary and delegated assignments are time-bounded versions/relationships;
- Decision Authority still requires exact per-Decision Authorization Basis validation.

Assessment:

- **Clarity:** strong if performer assignment and accountable designation are separate concepts.
- **Small-organization fit:** strong; one actor may carry several assignments and be the accountable holder.
- **Large/team fit:** strong; team contribution does not obscure who owns the obligation.
- **Delegation:** can state whether performance is delegated while accountability is retained or transferred, without inventing workflow steps.
- **Authority boundary:** fully consistent with the prohibition on equating access, role, or accountability with Decision Authority.
- **Over-specification risk:** moderate but bounded; it adds only the distinction needed to avoid ambiguous plural ownership.

### 7.4 Alternative R3 — plural peer holders with resolution by a role mechanism

Model:

- several active assignments may jointly hold one role/accountability scope;
- a separately identified mechanism—committee, quorum, consensus, named lead, or organization-specific rule—produces a determination;
- no single accountable holder is required when the mechanism is valid;
- absent or conflicting mechanism evidence produces unresolved conflict.

Assessment:

- **Clarity:** variable and mechanism-dependent.
- **Organizational fit:** supports committees and collective accountability.
- **Delegation/temporary assignment:** requires more rules about membership, quorum, replacement, and time.
- **Authority boundary:** compliant only when the exact mechanism and its legitimate authority are validated in the Decision Authorization Basis; peer role labels alone are insufficient.
- **Over-specification risk:** high for Increment 2 if generalized beyond the already accepted committee/organizational authority extension point.

R3 should remain an explicit authority-mechanism path for Decisions, not the default for all PAIM accountability.

### 7.5 Scope-resolution policy alternatives

Plural scope levels create a separate choice from holder cardinality.

| Policy | Rule | Consequence |
|---|---|---|
| P1 — no implicit precedence | All applicable assignments are returned. Compatible additive performer assignments coexist; competing accountability/authority assignments produce conflict until explicitly resolved. | Safest and most explicit; more conflicts require human resolution. |
| P2 — specific overrides general | The most specific applicable target suppresses broader assignments for the same role/function. Equal-specificity overlaps conflict. | Familiar, deterministic, but silently removes broad accountability unless that consequence is normatively intended. |
| P3 — explicit per-role organizational policy | A versioned policy declares additive, overriding, retained-accountability, or conflict behavior for each role/target relation. Missing policy yields conflict. | Most flexible; introduces governance configuration and testing beyond the minimum v0.1 need. |

No policy may make a broad software or Role Assignment automatically override the exact Decision Authorization Basis.

### 7.6 Vacancy, overlap, delegation, and temporary assignment

Every viable posture should represent these conditions without adding later workflow semantics:

- **Vacancy:** no eligible assignment/accountable designation for the requested role, target, and time; return `NOT ESTABLISHED` and surface orphaned obligations.
- **Compatible overlap:** multiple performer assignments are allowed only when the role/function is declared additive and no unique accountability is being selected.
- **Incompatible overlap:** more than one eligible accountable designation, contradictory delegation chain, or unsupported scope overlap returns explicit conflict with all candidates.
- **Delegation:** immutable relationship from delegating assignment/authority to delegated assignment, with scope, limits, effective interval, source, and retained-versus-transferred accountability stated.
- **Temporary assignment:** ordinary Role Assignment with a bounded effective interval and explicit relationship to the assignment it covers or supplements; expiry never silently extends.
- **Revocation/supersession:** prospective status event/history; prior actions remain attributable to the assignment effective when performed.

## 8. Coupled compatibility matrix

Legend: `Compatible` means a coherent contract can be stated without hidden selection. `Conditional` requires the named additional rule. `Incompatible for v0.1` means the combination would leave Increment 2 behavior ambiguous or require broader semantics not otherwise justified.

| Scope alternative | R1 single holder | R2 plural performers + one accountable | R3 plural peer mechanism |
|---|---|---|---|
| S1 one governing Configuration per Case | Compatible; simplest but rigid. | Compatible; clear Case-level accountability and team contribution. | Conditional on an explicit mechanism for Case-level accountability; otherwise hidden collective precedence. |
| S2 one governing Configuration per typed sub-scope | Compatible but creates many single-holder assignments and transfer burden. | **Compatible and coherent** when role targets use the same typed sub-scope and unique accountability is enforced per obligation. | Conditional on mechanism identity and time for every affected sub-scope; likely excessive for v0.1. |
| S3 plural same-scope governing Configurations | Incompatible for v0.1: one holder does not resolve which Configuration governs. | Conditional on explicit assignment-to-Configuration-set compatibility and downstream selection rules; otherwise unsafe. | Incompatible for v0.1 without both Configuration-set and collective-decision mechanisms, creating hidden precedence and ambiguous current selection. |

Additional incompatibilities:

- S2 with free-text or overlapping sub-scopes is not deterministic; scope identity and overlap behavior must be explicit.
- Any scope alternative combined with specific-over-general precedence is unsafe for Decision Authority unless the exact Authorization Basis independently proves coverage.
- R2 without an explicit accountable designation converts plural responsibility into hidden co-accountability.
- R3 without a versioned mechanism converts a group label into authority.
- Any combination that treats proposed/experimental/fallback purpose as currentness can create multiple incompatible current Configurations and is non-conformant.

## 9. Human decision points

### Decision 1 — What is the minimum governing Configuration scope within a Case?

**Question in plain language:** May one Case have more than one governing Configuration at the same time, and if so, how are they kept non-competing?

Options:

1. **S1:** one governing Configuration per Case; use linked Cases for independent concurrent operation.
2. **S2:** one governing Configuration per explicit Case-local sub-scope; same-scope overlap is conflict.
3. **S3:** plural governing Configurations in the same scope with explicit set-selection/compatibility rules.

Trade-offs: S1 is smallest and clearest but may split one management question artificially. S2 adds one typed scope seam while preserving deterministic selection. S3 is maximally flexible but propagates unresolved plural-selection semantics into every later layer.

**Codex recommendation:** select S2 only if PAIM v0.1 has a demonstrated need for concurrent governed segments within one Case; otherwise select S1. Do not select S3 for v0.1.

Sections requiring amendment: Managed Configuration §§2, 18, 24, 25, and 30; Case Lifecycle §§5, 7, 18, 19, 22, and 26; Roles §§3 and 26; Integrity §§3.11–3.12 and 11 if a new cross-cutting scope invariant is required.

### Decision 2 — How is Configuration ownership represented across Cases?

**Question in plain language:** Does one Case own each Configuration identity, or may a Configuration be jointly owned or independent?

Options:

1. exactly one owning Case, with explicit related/successor Case links;
2. independent Configuration identity related many-to-many to Cases;
3. joint Case ownership.

Trade-offs: one owner matches the current Case-centered lifecycle and minimizes ambiguity. Independent or joint ownership may reduce duplication but requires authority, lifecycle, materiality, and conflict rules across Cases and overlaps IRR-012.

**Codex recommendation:** exactly one owning Case for v0.1; defer shared dependency/equivalence and cross-case reuse to explicit relationships and IRR-012.

Sections requiring amendment: Managed Configuration §§2, 12, 22, 24, and 30; Case Lifecycle §§18–19; Roles §§22 and 26.

### Decision 3 — May one role have multiple holders in one scope?

**Question in plain language:** Can several actors perform the same PAIM role for the same target and time?

Options:

1. R1 single holder for every role/scope;
2. R2 plural compatible performers, with one accountable designation where the record or determination requires accountability;
3. R3 plural peer holders governed by a separately identified collective mechanism.

Trade-offs: R1 is deterministic but too rigid for teams. R2 preserves team participation and individual accountability. R3 supports committees but requires substantially more governance mechanics.

**Codex recommendation:** R2, with R3 retained only through the already accepted committee/organizational mechanism path where specifically configured.

Sections requiring amendment: Roles §§3, 4, 9, 14, 22–28, 34–35, and 39–41; Integrity §§3.11–3.12, 6.1–6.2, and 11.

### Decision 4 — Must accountable ownership be singular?

**Question in plain language:** When PAIM says a record or judgment has an owner, must one assignment be accountable for it?

Options:

1. one accountable assignment per required obligation/scope/time, while contributors may be plural;
2. plural co-accountable assignments, all equally accountable;
3. one accountable mechanism, which may be an individual role or explicitly governed committee/team mechanism.

Trade-offs: option 1 is clearest but may not match collective governance. Option 2 obscures who must act when holders disagree or leave. Option 3 is flexible but requires mechanism identity and validity.

**Codex recommendation:** option 3, implemented minimally as exactly one accountable assignment **or one explicit accountable mechanism**, never an unqualified set of peers.

Sections requiring amendment: Roles §§2–5, 11, 14–17, 21–22, 28, 31–34, and 39; Case Lifecycle §§4, 20, and 23.

### Decision 5 — How do broad and narrow Role Assignments interact?

**Question in plain language:** If an organization-wide assignment and a Case- or Configuration-specific assignment both apply, does either take precedence?

Options:

1. P1 no implicit precedence; compatible performers combine, competing accountable/authority assignments conflict;
2. P2 specific assignment overrides general assignment for the same role/function;
3. P3 a versioned organizational policy declares the interaction for each role/target relation.

Trade-offs: P1 is safest and exposes ambiguity. P2 is simple but may silently displace broad accountability. P3 is extensible but adds governance configuration and a new authoritative policy dependency.

**Codex recommendation:** P1 for v0.1. Add explicit supersession or delegation when an organization intends displacement. Consider P3 later if operational evidence shows recurring valid combinations; do not default to P2.

Sections requiring amendment: Roles §§26–28, 35, 39, and 41; Integrity §§3.11, 6.2, and 11; Platform Architecture §§5.13 and 20 only for conformance wording.

### Decision 6 — Who owns Configuration materiality and identity-continuity judgments?

**Question in plain language:** Who is accountable for deciding whether a change is material and whether it remains the same Configuration identity?

Options:

1. Case Owner by default, with explicit delegation;
2. designated Configuration Owner accountable for both judgments;
3. a separately assigned determination owner/mechanism per Configuration scope, with Case Owner coordinating workflow.

Trade-offs: option 1 is smallest but expands Case Owner meaning beyond current coordination duties. Option 2 creates clear specialist ownership but adds a role. Option 3 is most flexible and explicit but requires a determination-assignment relationship.

**Codex recommendation:** option 3 expressed through the R2/R3 accountability model, with a configurable default to Case Owner or designated Configuration Owner rather than hard-coding one universal role. The recorded determination must identify the accountable assignment/mechanism, rationale, scope, and review history.

Sections requiring amendment: Managed Configuration §§7, 9–12, 24, 27, and 30; Case Lifecycle §§2.4, 13, 18, 20, and 23; Roles §§5, 22, 26, 28, and 39.

### Decision 7 — How is Decision Authority related to Role Assignment?

**Question in plain language:** Does assigning the label “Decision Authority” itself grant power to authorize a Decision?

Options considered:

1. derive authority directly from the Role Assignment;
2. maintain a separate authority assignment that independently grants power; or
3. allow a Role Assignment or legitimate organizational mechanism to identify the candidate authority, but require the exact Decision Authorization Basis to prove authority, scope, time, limits, and authorization event for each Decision.

This is **not genuinely open**. Governing Integrity §6 and Roles §§11–14 already require option 3. Options 1 and 2 are non-conformant if they bypass the complete Authorization Basis.

**Codex recommendation:** record this as a conformance clarification, not a new semantic decision.

Sections likely requiring explanatory amendment: Roles §§3, 11, 13, 26, and 35; no normative weakening or duplication of Integrity §6.

## 10. Proposed minimal v0.1 posture — HUMAN DECISION REQUIRED

The following posture is coherent and minimal, but every item marked `PROPOSED` remains subject to explicit PAIM design-authority acceptance:

1. **PROPOSED — one owning Case per Configuration identity.** A Case may own multiple separately identifiable Configurations and their immutable versions. Cross-case relationships are explicit; shared dependency/equivalence remains deferred.
2. **PROPOSED — S2 with one flat typed Case-local sub-scope only if concurrent governed segments are required; otherwise S1.** There is no same-scope plural governing Configuration in v0.1.
3. **PROPOSED — orthogonal Configuration dimensions.** Immutable content/version identity and status events follow Integrity; governing currentness is derived for explicit scope/time; purpose is separately recorded as governing, proposed alternative, experimental, or fallback; authorization and AI operating state remain Decision-derived.
4. **PROPOSED — typed Role Assignment targets.** Increment 2 supports at least organization, business unit, Case, Case-local Configuration sub-scope/Configuration, and specific Decision targets. Case ID is required only for Case-derived targets. Intervention and authority-domain targets may remain typed extension points until their increments.
5. **PROPOSED — R2 accountability.** Multiple compatible performers may hold a role, but a governed record/determination requiring accountability resolves to exactly one accountable assignment or one explicit accountable mechanism. More than one incompatible result is conflict; none is vacancy/not established.
6. **PROPOSED — no implicit scope precedence.** Broad and narrow assignments coexist only when additive/compatible. Competing accountability or authority assignments remain conflict until explicit supersession, delegation, or an accepted policy resolves them.
7. **PROPOSED — explicit materiality/identity determination accountability.** Each determination records exact Configuration scope/version, accountable assignment or mechanism, rationale, effective/recorded time, and outcome. A configurable organizational default may nominate the Case Owner or Configuration Owner; software must not infer ownership from edit access.
8. **FIXED — Decision Authority is never derived from software access or role label alone.** An exact Decision Authorization Basis remains mandatory for every authorized Decision.
9. **FIXED — deterministic outcomes.** Every Configuration designation and required Role/accountability resolution returns one eligible result, explicit absence/vacancy, or explicit conflict with candidates and reasons.

This posture deliberately excludes arbitrary nested scope hierarchies, same-scope Configuration sets, universal RBAC, automatic specific-over-general precedence, generalized quorum engines, and shared cross-Case Configuration identity.

## 11. Specification-hardening plan

No amendment should be made until the decisions in §9 are explicitly recorded. The selected posture then requires one coordinated normative hardening change with explanatory conformance updates.

### 11.1 Amendments required under any selected posture

| Specification | Normative amendments | Explanatory amendments |
|---|---|---|
| Case Lifecycle | State which Configuration designation/scope satisfies `CONFIGURATION_DEFINED`, readiness, routing, reopen/new-Case, and lifecycle integrity guards; assign materiality/identity determination accountability. | Examples showing alternatives, vacancy/conflict, and current operation versus proposed/target Configuration. |
| Managed Configuration | Define Case ownership cardinality; separate purpose from currentness/status/operating state; define designation scope, compatibility, materiality/identity determination record, and conflict behavior. | Replace ambiguous `current/proposed/experimental` examples; show point-in-time selection and change examples. |
| Roles and Accountability | Replace mandatory Case ID with typed target; define target identifiers, holder cardinality, accountability designation/mechanism, scope resolution, vacancy, overlap, delegation, temporary assignment, and conflict. | Clarify principal/actor/assignment/accountability/authority distinctions and provide small/large-organization examples. |
| System Record and Decision Integrity | Amend only if the selected scope/accountability semantics require a cross-cutting selection invariant beyond §§3.11, 6, and 8; remove the corresponding reservations from §11 when closed. | Add conformance examples referencing the substantive owners; do not duplicate their domain meaning. |
| Platform Architecture | No semantic redesign. Update §20 P1 reservation and any §5.4/§5.13 wording only after governing specifications control the answer. | Reflect the accepted module ownership/query scope and mark the findings closed. |
| Sequencing roadmap | No change to increment order. Update the gate record only after independent re-review closes both findings. | Link accepted amendments and review evidence. |

### 11.2 If S1 is selected

Normatively define one effective governing designation per Case and make every overlap conflict. State that independently concurrent governing operation uses linked Cases. Add lifecycle examples for alternatives and successor Cases. No sub-scope hierarchy is introduced.

### 11.3 If S2 is selected

Normatively define the Case-local sub-scope identity, whole-Case scope, non-overlap/compatibility rule, and uniqueness per scope/purpose/time. Require every dependent query and Role Assignment to state the sub-scope. Add negative examples for free-text, missing, and overlapping sub-scopes.

### 11.4 If S3 is selected

Before hardening can be accepted, specify Configuration-set identity or exact selection, compatibility/incompatibility rules, downstream cardinalities, lifecycle guard aggregation, point-in-time behavior, and conflict resolution across every affected record family. This likely requires reopening Value/Risk, Evidence, Decision, Reassessment, and Register semantics and is not a minimal Increment 2 posture.

### 11.5 If R1 is selected

Normatively prohibit overlapping active assignments for the same role/target/time, define temporary replacement and vacancy, and clarify how teams/committees are represented as one actor or separate authority mechanism. Do not let the single role holder bypass Decision Authorization Basis.

### 11.6 If R2 is selected

Normatively distinguish performer assignment from accountable designation, declare which record families/determinations require one accountable result, define additive compatibility, and make plural accountable candidates conflict. Define retained-versus-transferred accountability on delegation.

### 11.7 If R3 is selected

Normatively define accountable mechanism identity, membership/effective-time relationship, validity evidence, and absence/conflict outcomes. Committee/quorum detail may remain organization-configured, but an unvalidated group label cannot be treated as a valid mechanism.

### 11.8 If P1, P2, or P3 scope resolution is selected

- **P1 no implicit precedence:** define additive-compatible role functions and explicit conflict for all competing accountability/authority assignments.
- **P2 specific-over-general:** define a closed specificity order, exact suppression behavior, equal-specificity conflict, historical reconstruction, and roles for which override is prohibited. Decision authorization still uses Integrity §6 independently.
- **P3 explicit policy:** define the policy as a versioned authoritative input with target relation, effective interval, rule vocabulary, provenance, absence, and conflict behavior; bind historical role resolution to the exact policy version.

## 12. Increment 2 gate evidence

The Increment 2 implementation gate remains **CLOSED — P1 GATE**. Case, Managed Configuration, lifecycle, and Roles/Accountability implementation may begin only after all evidence below exists on merged clean `main`:

1. an explicit human decision record selecting every genuine choice in §9;
2. accepted normative amendments to Case Lifecycle, Managed Configuration, and Roles/Accountability;
3. any strictly necessary cross-cutting Integrity amendment, with no duplicate or weakened invariant;
4. exact typed Case–Configuration and Role Assignment scope models;
5. orthogonal Configuration currentness, purpose, lifecycle, authorization, and operating-state semantics;
6. explicit one/absence/conflict behavior for governing Configuration designation, role resolution, accountable designation, delegation, and overlap;
7. materiality and same-identity/new-identity determination ownership, rationale, time, and history;
8. corrected organization/business-unit Role Assignment identity without fictitious Case ID;
9. examples covering normal, multiple-alternative, concurrent-scope if selected, vacancy, compatible overlap, incompatible overlap, delegation, temporary assignment, correction, supersession, and point-in-time reconstruction;
10. negative behavioral test oracles for conflicting current Configurations, ambiguous/missing scope, overlapping accountable assignments, invalid delegation, and software-permission/Decision-Authority confusion;
11. cross-specification conformance check across Case Lifecycle, Managed Configuration, Roles, Integrity, Management Register references, and Decision Authorization Basis;
12. confirmation that Value/Risk independence, exact Configuration binding, authority gaps, frozen-input history, authorized-decision history, and reassessment semantics remain unchanged;
13. independent focused implementation-readiness re-review explicitly concluding that IRR-007 and IRR-013/CON-002 are closed for Increment 2; and
14. a separate bounded implementation issue created only after the accepted re-review and clean-main checkpoint.

Merge of this design artifact alone does not open the gate.

## 13. Explicit non-decisions and deferred semantics

This artifact does not decide or design:

- physical tables, foreign keys, indexes, ORM models, APIs, commands, or UI;
- identity-provider, directory, authentication, session, or credential mechanics;
- a general organization-wide RBAC/IAM system;
- exact software permission matrices;
- committee quorum, voting, dissent, or emergency-authority workflows;
- arbitrary nested organizational or Configuration scope hierarchies;
- cross-Case shared Configuration ownership or shared-dependency equivalence;
- Evidence Applicability (IRR-008);
- Value/Risk selection and freeze ownership (IRR-006);
- Observation (IRR-009);
- Intervention prerequisite/acceptance semantics (IRR-010);
- Trigger/Reassessment concurrency (IRR-011);
- Register population/aggregation and shared identity (IRR-012);
- operating-state stronger/broader relations (IRR-014);
- workflow convenience, notification, escalation timing, or role-request/approval presentation;
- Case/Configuration/Role code, migrations, tests, or permissions; or
- changes to Increment 1A.

References to later layers identify consequences and required compatibility only. They do not resolve those layers' open P1 findings.

## 14. Final recommendation to ChatGPT/user

Record one coordinated human decision using the seven questions in §9, with Decision 7 acknowledged as already fixed rather than re-decided.

The recommended minimal coherent posture is:

- one owning Case per Configuration identity;
- S1 unless one Case demonstrably needs concurrent governed segments, otherwise the flat typed-sub-scope S2;
- no same-scope plural governing Configurations in v0.1;
- typed Role Assignment targets with Case ID conditional on target type;
- R2 plural compatible performers plus exactly one accountable assignment or one explicit accountable mechanism where accountability is required;
- no implicit broad/narrow precedence;
- explicit, attributable materiality and identity determinations with a configurable accountable default; and
- unchanged mandatory per-Decision Authorization Basis.

This recommendation favors semantic explicitness, deterministic conflict behavior, minimum necessary cardinality, preserved human accountability and authority boundaries, and future extension without speculative enterprise complexity. It remains **PROPOSED — HUMAN DECISION REQUIRED** until accepted by PAIM design authority and incorporated into governing specifications.
