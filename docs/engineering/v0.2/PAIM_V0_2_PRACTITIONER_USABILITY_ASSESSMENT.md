# PAIM v0.2 practitioner usability assessment

## Assessment outcome

**Pre-polish recommendation: READY FOR TARGETED POLISH**

The integrated application preserves the accepted PAIM semantics and provides a
coherent route through the ordinary management cycle. No blocker was found in
this assessment. A reasonably experienced business practitioner can start and
reopen a Case, follow assigned work, keep Value and Risk separate, prepare and
authorize a Decision, establish continuing review, respond to material change,
and revisit the history.

The application is not yet ready for closure without a bounded presentation
pass. Several ordinary surfaces still expose architecture language, ask for
information PAIM already carries, or add confirmation friction without enough
practitioner value. These are finish-before-v0.2 defects, not reasons to weaken
the domain model or add new capabilities.

This assessment was conducted from clean `main` at
`4c4ef522744b206d094e3c9642d939dbc4dbea1d`. It is an assessment artifact only;
no product behavior or governing specification was changed.

## Evidence and method

The assessment combined three forms of evidence:

1. A fresh isolated practitioner session was opened in the actual browser
   application. Home, Cases, New Case, Case-start review, and ordinary
   navigation were inspected without relying on architecture documentation.
2. Every ordinary Slice-H template, action form, confirmation surface, and
   History surface was reviewed against the frozen Practitioner UI Contract,
   Product Design Foundation, Practitioner Operating Model, and Practitioner
   Language Standard.
3. The focused production-route and browser proof was rerun:
   `tests/integration/test_gate8_slice_h_ui.py` and
   `tests/browser/test_slice_h_browser.py` — **10 passed**. The proof includes
   the integrated Harborlight Decision journey, quiet Home, durable Work to
   action, restart continuity, source-hidden and stale/tampered failure,
   independent Value/Risk work, single- and multiple-candidate Reliance,
   focused review, History reconstruction, and real Chromium/no-JavaScript
   Case initiation.

The manual session used disposable local state. It was not a substitute for
the production-route proof and did not alter historical Harborlight or
Increment 9 evidence.

## Representative journeys assessed

| Journey | Evidence | Practitioner assessment |
| --- | --- | --- |
| Fresh sign-in -> quiet Home -> Cases | Live browser | Home is calm and understandable. “Nothing currently needs your attention” is useful. Sign-in still assumes a provisioned principal and protected credential. |
| Cases -> New Case -> review | Live browser plus production browser proof | The four starting facts are defensible, but the distinction among AI use, management question, and setup/scope needs examples. Review protects a consequential Case start, although its copy is architecture-heavy. |
| Home -> durable Task -> exact action -> restart | Production-route proof and source review | Routing and continuity work. Task reaches the permitted action, but ordinary copy still describes exact/governed mechanics more than the business judgment. |
| Finish Value and Risk -> adequacy -> Reliance | Production-route proof and source review | Value and Risk remain independent. One eligible candidate is carried without a standalone Reliance click; multiple candidates require an explicit choice. The two finishing forms nevertheless feel like copies of one generic record form. |
| Consider Value and Risk -> propose -> authorize/confirm Decision | Production-route proof and source review | The governed acts remain separate and current-basis revalidation fails closed. The authorization form unnecessarily asks the practitioner to restate an authority identity already carried by PAIM. |
| Plan review -> quiet period -> event attention -> focused review -> unchanged-Decision confirmation | Production-route proof and source review | PAIM remains quiet during legitimate no-action periods. Event attention does not assert a conclusion, focused review stays bounded, and unchanged-Decision confirmation preserves the existing Decision. |
| History & decisions: why, what was known, what changed | Production-route proof and source review | Exact dual-time reconstruction and non-disclosure work. Ordinary History still foregrounds timestamp mechanics and record language instead of the manager’s question. |

## Friction inventory

The counts below describe one representative complete path. They are diagnostic,
not optimization targets; separately governed acts must remain separate.

| Measure | Representative count | Assessment |
| --- | ---: | --- |
| Distinct ordinary surface types | 9 | Home, Cases, New Case, Case, Task, action form, confirmation, History, and bounded error/recovery. |
| Forms | 12 | Case start; two assessment finishes; two adequacy judgments; Integration; proposal; authorization; review plan; focused-review start; unchanged-Decision confirmation; review completion. |
| Confirmation steps | 12 | Every form receives a separate generic review/commit step. Consequential acts warrant confirmation, but the repeated generic layer is often ceremonial. |
| Required entries | 33 | Includes six required entries in each generic Value/Risk finish form and one authority-identity entry that PAIM already carries. |
| Optional entries | 14 | Mostly limitations, material reasons, tensions, alternatives, authority conditions, and dissent. |
| Common-path transitions | about 39–40 | Route-derived estimate including navigation, form, review, commit, durable Task, and History transitions. It is not a universal click count. |

### Re-entry and unnecessary ceremony

- Decision authorization asks “What exact authority are you exercising?” even
  though the exact authority source is already part of the governed context.
- Value and Risk finish forms ask for boundary and provenance in generic text
  even when PAIM already carries the exact Case, Configuration, and information
  basis. A practitioner may need to state a substantive limitation or source
  judgment, but the form does not explain that distinction.
- Generic confirmation screens mechanically repeat the submitted payload. They
  do not consistently explain the consequence specific to the action.

### Natural combinations and necessary separation

- Proposal and authorization must remain separate; combining them would erase
  an accepted authority boundary.
- Value and Risk facts must remain independent even when one practitioner can
  perform both acts.
- One-candidate Reliance is already carried automatically. Multiple legitimate
  candidates correctly remain an accountable choice.
- A combined adequacy presentation could reduce navigation when the same Actor
  is legitimately responsible for both lanes, while still committing separate
  authoritative facts. This is presentation polish, not a new domain act.

### Where ordinary tools would currently feel easier

- A short memo or structured email gives a practitioner more natural freedom
  than two identical six-field Value/Risk forms with generic confirmation.
- Asking “show what we knew when this Decision was made” is easier than entering
  raw effective-time and known-time timestamps.
- Case-start questions are compact, but a Word template would more readily show
  examples distinguishing the AI use, management question, and initial scope.

## Six burden tests

Legend: **PASS** means the ordinary surface satisfies the test; **FRICTION** is
usable but burdensome; **DEFECT** is concrete pre-v0.2 correction work.

| Ordinary surface | 1. PAIM already knows? | 2. Needed now? | 3. Click creates value? | 4. Easier in office tools? | 5. Natural combination? | 6. Useful or quiet? |
| --- | --- | --- | --- | --- | --- | --- |
| Home | PASS — no fact re-entry | PASS — attention and open Cases | PASS — direct destination | PASS — better than manual tracking | PASS — attention is composed without collapsing facts | PASS — quiet when no action exists |
| Cases | PASS | PASS — find or start work | PASS | PASS | PASS | FRICTION — empty-state “prospective workspaces” is internal language |
| New Case | PASS — four new starting facts | FRICTION — distinctions need examples | PASS — Case start is consequential | FRICTION — a template may be clearer | PASS — one coherent start | DEFECT — “bounded” and production-contract copy distract from purpose |
| Case orientation | PASS | FRICTION — repeated “not established” states add clutter | PASS | PASS — useful shared orientation | PASS | DEFECT — architecture defenses compete with management meaning |
| Durable Task | PASS — context is carried | PASS | PASS — reaches the exact action | PASS | PASS | FRICTION — default authority/context wording is technical |
| Finish Value | FRICTION — boundary/provenance may already be carried | FRICTION — six generic required prompts | FRICTION — separate review is repetitive | DEFECT — a memo is more natural today | PASS — remains a separate fact | DEFECT — generic form does not guide the Value judgment |
| Finish Risk | FRICTION — boundary/provenance may already be carried | FRICTION — six generic required prompts | FRICTION — separate review is repetitive | DEFECT — a memo is more natural today | PASS — remains a separate fact | DEFECT — generic form feels like a copy of Value |
| Adequacy | PASS | PASS — suitability for this Decision matters | FRICTION — Value/Risk navigation repeats | FRICTION | FRICTION — one presentation could commit separate facts | PASS — does not imply Case endorsement |
| Reliance | PASS | PASS when choice exists | PASS — zero click for one; accountable click for many | PASS | PASS | PASS — hidden when no substantive choice exists |
| Consider Value and Risk | PASS — exact selected lanes carried | PASS | PASS — prepares a Decision | PASS | PASS — synthesis does not net the lanes | FRICTION — some “governed synthesis” language remains |
| Decision proposal | PASS | PASS | PASS — creates a distinct proposal | PASS | PASS — remains separate from authorization | PASS |
| Decision authorization | DEFECT — authority identity is already carried | PASS — authority judgment is necessary | PASS for the act; FRICTION for the field | FRICTION | PASS — must remain separate | DEFECT — asks for technical authority identity rather than the practitioner judgment |
| Generic confirmation | FRICTION — repeats submitted content | FRICTION — needed for consequential acts, not uniformly | DEFECT — often satisfies ceremony more than judgment | DEFECT | PASS — does not merge acts | FRICTION — consequence copy is not action-specific |
| Continuing review | PASS | PASS | PASS — creates a real review obligation | PASS | PASS | PASS — quiet between legitimate review points |
| Focused review | PASS — event context carried | PASS | PASS — bounded response to change | PASS | PASS — avoids unnecessary full reassessment | PASS — no substantive conclusion is inferred |
| History & decisions | PASS — source basis reconstructed | FRICTION — raw cutoff controls are not ordinary needs | FRICTION — manual dual-time entry is audit work | DEFECT — ordinary question is easier to ask outside PAIM | PASS — chronology composes facts without rewriting them | DEFECT — record mechanics obscure “why, what we knew, what changed” |

## Findings by severity

### Blocker

None observed. The focused proof found no inability to complete the core cycle,
semantic collapse, unauthorized mutation, stale-context acceptance, or
source-level disclosure failure.

### Finish-before-v0.2

**U-01 — Ordinary surfaces still leak architecture vocabulary.** Cases uses
“prospective workspaces”; New Case and action copy repeatedly use “bounded,”
“exact,” “governed,” “governing setup,” and production-command language. Case
orientation exposes repeated “not established” states and architecture defenses
at Level 1. The terms are sometimes precise, but their current density makes a
business practitioner translate the architecture before acting.

**U-02 — Value and Risk finish forms are generic duplicates.** Each requires
finding, boundary, uncertainty, implication, provenance, and rationale in the
same form shape. The application preserves analytical independence, but it does
not yet ask lane-specific practitioner questions or show the expected level of
detail. Boundary and provenance prompts also risk re-entry of context PAIM
already carries.

**U-03 — Decision authorization re-asks a known authority identity.** The exact
authority source is already bound and revalidated. Asking the practitioner to
type it again adds burden and creates avoidable inconsistency without granting
or proving authority.

**U-04 — Confirmation is too generic and repetitive.** The same “Record this
judgment?” pattern and mechanical field replay is applied across ordinary acts.
Consequential confirmation should remain, but it should explain the specific
effect and omit repetition that does not improve the practitioner’s decision.

**U-05 — History foregrounds audit mechanics.** Raw effective/known timestamp
controls, source/version language, and “exact visible basis” wording appear too
prominently. The underlying dual-time and provenance behavior is correct and
must remain unchanged; ordinary History should lead with why the Decision was
made, what was known then, and what changed, with exact reconstruction controls
under advanced/audit disclosure.

**U-06 — Case-start concepts need examples and clearer differentiation.** The AI
use, management question, and initial setup/scope are all substantively useful,
but their current labels do not give enough help to a first-time practitioner.

### Acceptable v0.2 limitations

- Local sign-in assumes an already provisioned principal and protected
  credential. That is acceptable for the bounded single-workstation v0.2
  application, although it is not an organization-local identity experience.
- Proposal, authorization, Decision confirmation, and focused-review completion
  remain separate clicks because they are separately governed acts.
- Exact IDs and provenance remain available in collapsed audit disclosures.
- Multiple legitimate Reliance candidates require explicit accountable choice.
- The current application is a local practitioner product, not a notification,
  scheduling, analytics, or network-deployment platform.

### Post-v0.2 ideas

- Organization-local identity and credential administration.
- Notifications, scheduling automation, analytics, and network deployment.
- Empirical study of whether real organizations find PAIM useful or improve
  Decision quality with it.

These are outside the v0.2 finishing line and are not part of the recommended
polish issue.

## Bounded finishing recommendation

Open **one** follow-up v0.2 practitioner-presentation polish issue covering only:

1. action-specific plain-language copy and empty/status-state cleanup on Home,
   Cases, New Case, Case, Task, and confirmations;
2. lane-specific Value and Risk prompts that do not re-ask safely carried
   context and do not change assessment semantics;
3. removal of the practitioner-entered authority-identity field while retaining
   exact server-side authority binding and revalidation;
4. proportionate, action-specific confirmation presentation, preserving every
   separately governed commit; and
5. a manager-first History presentation with dual-time/provenance controls moved
   to progressive advanced/audit disclosure.

The issue should include browser or route-level oracles proving that all exact
context, authority, Value/Risk independence, transaction, stale/tampered
failure, and source-level non-disclosure behavior remains unchanged. It should
not add capabilities, new semantic families, workflow automation, scoring, or
post-v0.2 scope.

After that bounded polish and an owner browser check, PAIM can be reassessed for
`READY FOR CLOSURE`.

## Issue #165 post-polish reassessment

**Recommendation: READY FOR OWNER BROWSER CHECK**

The bounded presentation pass resolves U-01 through U-06 without changing a
governed act, source-selection rule, authority boundary, or separately
committed fact. The application now asks lane-specific business questions,
derives the authorization identity from the exact current authority source,
uses action-specific review screens, and leads History with the management
story. Exact IDs, time reconstruction, and provenance remain available under
advanced or audit disclosure.

The refreshed friction measurements for the same representative path are:

| Measure | Post-polish count | Change and disposition |
| --- | ---: | --- |
| Distinct ordinary surface types | 9 | Unchanged; no new workflow or surface was introduced. |
| Forms | 12 | Unchanged; separately governed acts remain separate. |
| Confirmation steps | 12 | Unchanged; each is now action-specific and states both effect and non-effect. |
| Required entries | 32 | Reduced by one: the known Decision-authority identity is no longer re-entered. |
| Optional entries | 14 | Unchanged; optional limits, tensions, alternatives, and dissent remain available. |
| Common-path transitions | about 39–40 | Unchanged; this pass improves presentation rather than weakening commit boundaries. |

Re-entry was reduced without hiding a genuine practitioner judgment. PAIM now
carries the Case, Configuration, exact information basis, Responsibility,
Assignment, and authority identity. The Value and Risk forms ask for the
practitioner's substantive benefit/limitation or concern/control judgment, not
for those carried identities. Proposal, authorization, confirmation, and
focused-review completion deliberately remain distinct clicks because each
creates a different governed fact.

### Finding disposition and burden-test result

| Finding | Disposition | Six-burden-test result on the corrected surface |
| --- | --- | --- |
| U-01 architecture vocabulary | Resolved for ordinary Level-1 Home, Cases, New Case, Case, Task, and action surfaces; exact technical material remains under audit disclosure. | PASS — ordinary copy now leads with the practitioner's purpose and stays quiet about absent facts. |
| U-02 generic Value/Risk forms | Resolved with distinct Value-benefit and Risk-concern/control prompts while retaining independent records and commits. | PASS — each prompt asks for a material lane judgment needed now; carried context is not re-entered. |
| U-03 authority identity re-entry | Resolved by deriving identity from the one exact current substantive-authority source and revalidating at commit. | PASS — the authorization click creates value; the known identity does not become another input. |
| U-04 generic confirmation | Resolved with a compact action-specific consequence, non-effect, and confirmation label. | PASS — confirmation remains only at the accepted semantic boundary and explains why it matters. |
| U-05 audit-first History | Resolved with a manager-first timeline and “what was known then” presentation; exact cutoffs and source identities are progressively disclosed. | PASS — ordinary History answers the management question first while preserving full reconstruction. |
| U-06 unclear Case start | Resolved with natural labels, examples, and explicit differentiation of AI use, management question, and starting scope/setup. | PASS — all requested facts are new and necessary to start the Case, and their purpose is visible. |

Hard-oracle coverage confirms that browser authorization cannot supply or
retarget authority identity, selectively hidden authority fails closed, a
superseded authority source invalidates an already reviewed intent without
mutation, Value and Risk remain independent, and manager-first History retains
dual-time and source-level non-disclosure. A real Chromium/no-JavaScript proof
also crosses the revised Value action and its action-specific review boundary.
The focused Slice-H/browser proof passed **13 tests**, and the complete
repository regression gate passed **384 tests**. No schema or migration change
was made; the complete gate includes the existing migration/schema regression.
Lock verification, Ruff format/lint, strict mypy, tracked-source secret scan,
and diff checks also passed.

This recommendation is bounded. It supports the planned owner browser check;
it is not a release verdict, an empirical usefulness claim, or permission to
add post-v0.2 capabilities.

## Human-judgment boundary

This assessment establishes structural browser usability evidence and identifies
concrete friction in the integrated product. It does **not** establish that real
organizations find PAIM useful, that practitioners will understand it without
facilitation in every setting, or that PAIM improves Decision quality. Those are
human and empirical validation questions beyond automated/browser simulation.
