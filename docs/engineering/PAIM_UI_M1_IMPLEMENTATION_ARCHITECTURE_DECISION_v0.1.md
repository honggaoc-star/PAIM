# PAIM UI M1 Implementation Architecture Decision v0.1

Status: **PROPOSED — READY FOR INDEPENDENT REVIEW**

Decision date: 2026-08-21

Proposed implementation gate: **READY FOR BOUNDED M1 FOUNDATION IMPLEMENTATION**

This artifact decides how to implement the accepted
[PAIM Practitioner Experience Architecture M1](../design/PAIM_PRACTITIONER_EXPERIENCE_ARCHITECTURE_M1_v0.1.md).
It does not implement a browser application, add dependencies, change PAIM semantics, or alter the
immutable v0.1.0 release. The current
[System Architecture](../system/architecture/PAIM_SYSTEM_ARCHITECTURE_v0.1.md),
[Platform Architecture](PAIM_PLATFORM_ARCHITECTURE_v0.1.md), and
[system specifications](../system/specifications/) remain controlling.

## 1. Decision

PAIM M1 will use **server-rendered FastAPI + Jinja2 with standard HTML forms and modest,
repository-owned JavaScript enhancement** (Option A).

The server owns authentication, sessions, CSRF verification, access filtering, read composition,
exact currentness, command adaptation, error translation, and HTML rendering. JavaScript may
improve disclosure, focus, confirmation, and duplicate-submit prevention, but every essential read
and action must work through server routes and ordinary HTML semantics.

M1 will not add HTMX or a dedicated client application. Either can be reconsidered when a later
milestone demonstrates an interaction need that standard server rendering cannot satisfy without
weakening accessibility or usability. No such need is established for M1.

## 2. Current baseline and constraints

The implementation baseline is a Python 3.12 package with:

- a modular authoritative core under `paim.application`, `paim.domain`, and `paim.integrity`;
- SQLite persistence under `paim.persistence.sqlite`;
- an authenticated local operational gateway in `paim.operational.application`;
- a `paim-local` command-line entry point;
- exact Record/Version identity, dual-time history, idempotent command identity, access filtering,
  audit, and domain hard-oracle tests; and
- no web framework, template engine, JavaScript framework, CSS framework, browser session store,
  or browser test dependency.

The browser is a new replaceable adapter. It must not become an alternate domain service, make a
projection authoritative, or use client state as evidence of currentness, accountability, or
authority.

M1 implements only the I9-P1 Case-to-bounded-operation pathway. Trigger/Reassessment, Management
Register interaction, Observation automation, IRR-009/IRR-014 extensions, remote deployment, and
multi-user topology remain outside the milestone.

## 3. Requirements distilled from the experience architecture

The implementation must support:

- Home and Cases views filtered before aggregation or disclosure;
- a persistent Case Workspace with Overview, Evidence & Assessment, Decision, Implementation &
  Operation, Learning & Reassessment handoff, and History;
- equal, independent Value and Risk views;
- visible separation of proposal, Decision Authorization, Completion Result, accountable
  Completion Acceptance, prerequisite evaluation, Activation Authorization, and operation;
- `State → Why? → What can legitimately change it?` explanations;
- five separately reported action layers: identity, software access, exact governed-context
  visibility, accountability, and substantive authority;
- exact source Versions, effective time, optional knowledge cutoff, provenance, and reconstruction;
- accessible confirmations, stale/conflict/denial explanations, and fail-closed degraded behavior;
  and
- the full I9-P1-derived browser acceptance pathway after local initialization and administration,
  without hidden CLI repair.

The UI may simplify navigation and data entry. It may not simplify management meaning.

## 4. A/B/C comparison

The matrix records qualitative fit, not a product score or a PAIM management ranking.

| Criterion | A. FastAPI + Jinja2 + modest JS | B. FastAPI + server-driven partial interaction | C. FastAPI/API + dedicated client |
|---|---|---|---|
| Semantic integrity | Strongest default: requests reconstruct server state and templates consume finished view models. Low temptation to copy selectors into a client. Exact hidden preconditions plus command-time server validation fit naturally. | Server can remain authoritative, but partial-target logic, out-of-band swaps, and multiple fragment states increase stale-context and error-routing complexity. Still materially safer than a client-owned domain model. | Highest duplication risk: API schemas, client models, eligibility logic, caches, and optimistic updates can drift from the authoritative core. Requires strict generated/hand-maintained contracts and more denial/staleness surfaces. |
| M1 interaction fit | Full pages, anchors, forms, `<details>`, peer Value/Risk panels, confirmation pages, and Post/Redirect/Get cover M1. Small JS can manage focus and disclosure. | Excellent for in-place explanations, filters, and workspace panels, but M1 does not require those interactions to be asynchronous. | Excellent visual/interactivity ceiling, but M1 value does not justify the additional application boundary. |
| Read/query composition | Server routes call one reusable application read boundary and render DTOs. No presentation persistence is needed. | Same server read boundary is possible; fragment/full-page variants add rendering contracts. | Same read boundary is still required, plus a public browser API and serialization/versioning contract. Client caching adds another freshness problem. |
| Security and sessions | Same-origin pages, standard forms, server-side opaque sessions, synchronizer CSRF tokens, strict cookies, no CORS, and small script surface. | Same posture is possible, but every partial request must carry CSRF/origin/session handling and safe target semantics. | Larger attack surface: API authorization, CORS or same-origin BFF policy, token/session handling, client storage temptations, and more XSS-sensitive state. |
| Concurrency and integrity UX | Confirmation page binds expected Versions; server revalidates on POST; PRG reconstructs authority after commit. Unknown outcomes stay on the server evidence path. | Can do the same, but simultaneous fragments and out-of-order responses require additional sequencing and focus/error reconciliation. | Optimistic client state and parallel requests make exact currentness harder; robust conflict recovery needs significant client architecture. |
| Accessibility | Semantic HTML and progressive enhancement are the default. Keyboard/focus behavior is predictable and works without JS. | Feasible, but fragment swaps require deliberate focus, live-region, history, title, and error-summary handling. | Feasible with discipline, but semantics, focus routing, and no-JS resilience require more custom engineering. |
| Testing | Existing pytest stack extends to query, route, and template tests; Playwright covers real browser paths. Domain hard-oracle tests remain unchanged. | Adds fragment-response and swap-behavior permutations to the same stack. | Adds API contract and client unit/component/build tests, plus end-to-end tests across two applications. |
| Local packaging and launch | One Python environment, one ASGI process, package-owned templates/static files, no Node build, and a new `paim-web` entry point. | Similar if HTMX is vendored as a static asset; still adds a third-party browser runtime and fragment conventions. | Usually adds Node/package-manager/build artifacts or a prebuilt client bundle, duplicated release steps, and greater Windows-local friction. |
| Maintainability | Smallest new surface and closest to current contributor skills. Debugging follows request → read/command adapter → existing service. | Moderate complexity and a new interaction idiom; still bounded if used sparingly. | Highest complexity, model/type duplication, dependency churn, and coordinated upgrades. |
| Future extensibility | M2/M3 can add selected partial interactions or replace the web adapter while retaining query/command boundaries. Full-page rendering is sufficient for initial scale. | Good path for future Reassessment/Register filtering without adopting a client framework. Could be introduced later behind the same routes/DTOs. | Highest rich-client ceiling for complex visualization and long-lived interaction, but remote/multi-user deployment remains a separate architecture problem. |

## 5. Recommendation and alternatives

### Why Option A is selected

Option A gives M1 the shortest dependency path from authoritative PAIM services to an accessible
practitioner experience. Standard requests naturally reconstruct exact context. Templates receive
presentation-only data and cannot become a second source of selection or authority. Standard forms
also make CSRF, confirmation, PRG, validation, and no-JavaScript behavior explicit.

FastAPI is selected rather than raw Starlette because it supplies a typed, well-supported ASGI
application/route/testing ecosystem while retaining direct access to Starlette templates,
middleware, requests, and responses. Jinja2 is selected for package-owned server templates with
autoescaping and `StrictUndefined` configuration.

### Why Option B is not selected for M1

HTMX 2.x is viable and does not require a Node build. It supports progressive enhancement and
server-rendered fragments. M1, however, has no interaction that requires partial replacement.
Adding it now would expand CSRF, stale-response, focus, live-region, and dual-render-path testing
before those costs buy a demonstrated practitioner benefit. It remains a reversible enhancement.

### Why Option C is not selected for M1

A dedicated client would create a second application boundary and likely a second toolchain. It
would require browser API versioning, duplicated data models, client cache discipline, additional
security policy, and a separate accessibility/component test layer. Those costs are justified only
if later interaction or visualization requirements cannot be met by server rendering. M1 does not
establish that condition.

No PAE or APRM technology choice influenced this selection.

## 6. Selected logical architecture

```text
Browser
  |
  | same-origin HTTP, opaque session cookie, CSRF token
  v
paim.web
  - application factory / middleware
  - resource routes and form parsers
  - Jinja templates / repository-owned CSS / modest JS
  - browser session and CSRF adapter
  |
  +-------------------------------+
  |                               |
  v                               v
BrowserCommandAdapter       AuthenticatedPractitionerQueries
  |                               |
  | typed command requests        | access-filtered view DTOs
  v                               v
paim.operational.application / paim.application
  - authentication and current principal/Actor checks
  - software access and exact visibility
  - existing selectors/resolvers and domain commands
  |
  v
paim.domain / paim.integrity / paim.persistence.sqlite
  - authoritative semantics, commits, history, audit
```

Dependency direction is inward:

- `paim.web` may depend on operational/application public interfaces and browser DTOs;
- practitioner query orchestration may depend on application ports and immutable domain/integrity
  types, never templates;
- persistence adapters implement read ports but do not import the web layer;
- templates and JavaScript receive view models and URLs only; and
- no domain, integrity, application, operational, or persistence module imports from `paim.web`.

The browser process uses the same application factory/configuration and SQLite authority as
`paim-local`. It does not create a second database or synchronize copies.

## 7. Practitioner read/composition boundary

### Conceptual location

Create a browser-independent application read boundary conceptually under
`paim.application.practitioner` (exact file layout deferred to M1A):

- immutable presentation DTOs and basis structures;
- query requests containing exact subject, purpose, `effective_at`, optional `known_at`, and
  trusted access context;
- a `PractitionerQueryService` that calls existing selectors/resolvers and read ports; and
- explicit results for established, absent, conflict, indeterminate, stale, and inaccessible
  conditions.

SQLite-specific read implementations belong under `paim.persistence.sqlite`. An authenticated
facade in `paim.operational.application` must establish the current session, principal/Actor
mapping, accessible Case set, and accessible Configuration set before query composition. A browser
request cannot supply or widen that access population.

### Required view models

At minimum, M1 needs:

- `HomeView` and `CaseListView` with access-filtered attention facts;
- `CaseWorkspaceView` and area-specific views;
- `CurrentManagementPositionView` as a composition, not a new lifecycle status;
- `ActionEligibilityView` with five independent layers and command-time-revalidation warning;
- `ExplanationView` for state, reasons, exact basis, and legitimate owning action;
- peer `AnalyticalLaneView` values for Value and Risk;
- Decision, Intervention, Completion, prerequisite, activation, and operation basis views; and
- `ManagementHistoryView` plus read-only `ExactProvenanceView`.

Every material DTO carries:

- exact source Record and Version IDs;
- effective time, optional knowledge cutoff, and reconstruction time;
- explicit selection/resolution rule or existing resolver basis where applicable;
- absence/conflict/indeterminate detail rather than a chosen fallback;
- access-filtered status without hidden identities or global counts; and
- a source high-water/watermark if a projection is ever used.

`ActionEligibilityView` explains whether an attempt appears available from current facts. It is not
authorization and cannot guarantee command success; the command path revalidates every guard.

### Persistence and caching

M1 composes views on request and may use only request-local memoization. It persists no Home,
workspace, explanation, or eligibility state. If later performance evidence justifies a derived
cache, that cache must be rebuildable, source-Version/watermark-bound, partitioned or filtered
before disclosure, visibly stale when currency is unproven, and never used as command authority.

## 8. Browser command adapter

`BrowserCommandAdapter` is a thin server-side adapter from one explicit form route to one existing
production capability. It must:

1. validate session, origin, CSRF token, body size, field shape, and exact visible target;
2. parse typed IDs, enums, times, and bounded content without semantic defaults;
3. require the exact expected Record/Version/precondition set shown on the confirmation page;
4. allocate or reuse one server-generated idempotency identity for the exact action intent;
5. invoke `OperationalApplication` and the owning existing typed application command;
6. let existing access, currentness, accountability, authority, lifecycle, and integrity guards
   decide the outcome;
7. translate typed errors into practitioner states while retaining correlation, command, audit,
   and idempotency identities; and
8. discard the submitted state as authority and reconstruct the resulting page through
   `PractitionerQueryService`.

There is no generic `/approve`, `/resolve`, `/transition`, or `/command` browser endpoint. Each
consequential route names its domain action and typed target.

For two-step confirmation, the server creates a short-lived action intent containing action type,
target, expected source Versions, normalized non-secret form digest, idempotency key, creator
session, and expiry. The confirmation page displays the exact basis. The final POST refers to the
opaque intent and CSRF token; it cannot alter the bound content. An intent is single-outcome but
remains available for unknown-outcome inspection.

If an existing command cannot prove the required exact precondition/currentness atomically, that
browser action remains read-only until a separately bounded application-contract change is
authorized and tested. JavaScript or a pre-query cannot fill such a gap.

## 9. Browser authentication and session posture

### Local exposure boundary

- Default bind: `127.0.0.1` only, one Uvicorn worker, no reload.
- Default URL: `http://127.0.0.1:<configured-port>`.
- Accepted hosts: exact loopback hosts only; use trusted-host validation.
- No CORS and no remote/private-network access.
- Remote binding, TLS termination, reverse proxies, and multiple workers are unsupported in M1.

### Login and credential handling

The login form submits principal ID and the protected credential to the local server. The server
calls existing `OperationalApplication.authenticate`, then exchanges the credential for a
server-side browser session.

`GET /login` creates a short-lived anonymous server session solely for login CSRF protection;
successful authentication invalidates it and rotates to a new authenticated session. Login uses a
generic failure response, bounded per-process attempt throttling/backoff, and non-secret audit so it
does not disclose whether a principal or credential component was wrong.

The credential exists only in the bounded login request and authentication call. It is not stored
in the session, cookie, template, browser storage, configuration, application log, operational
audit detail, or redirect. Request/exception logging must redact the login body. The login response
uses `Cache-Control: no-store` and clears form data by redirecting after success.

### Server-side session

M1 uses an in-process server-side session registry because the supported topology is one local
process and one worker. A cryptographically random opaque session identifier (at least 256 bits) is
stored in a host-only cookie; the server registry stores its digest and:

- principal ID and resolved Actor ID;
- authenticated time, last-active time, and expiry;
- CSRF secret;
- current correlation context; and
- bounded pending action intents/flash messages, never credentials or authoritative records.

Restart invalidates every browser session. This is deliberate and avoids a new database/migration
for M1. An inactivity timeout of 30 minutes and an absolute timeout of 8 hours are the initial
bounded defaults; both are server-enforced and should be configurable only within documented safe
bounds. Login and logout rotate/invalidate the session ID. The registry enforces a bounded session
count and expires entries independently of browser cooperation.

For default loopback HTTP, the cookie is `HttpOnly`, `SameSite=Strict`, host-only (no `Domain`), and
`Path=/`; it cannot use `Secure` because browsers send a Secure cookie only over HTTPS. If a later
explicit local-HTTPS mode is supported, `Secure` becomes mandatory and the cookie uses a `__Host-`
name. Session IDs never use `localStorage`, `sessionStorage`, or JavaScript-readable cookies.

Starlette's signed cookie `SessionMiddleware` is not the selected session store because its session
payload is client-held/readable. Its cookie controls remain useful reference behavior, but PAIM M1
requires an opaque cookie and server-held session state.

### CSRF and request policy

Use the synchronizer-token pattern: one unpredictable token bound to the server session, rendered
as a hidden field on every state-changing form, and compared in constant time. The token never
appears in a URL or log. All state changes use POST; GET/HEAD are read-only. State-changing
requests must also carry an exact same-origin `Origin`, or a same-origin `Referer` only where the
browser omits `Origin`; otherwise they fail closed. `SameSite=Strict` is defense in depth, not the
CSRF mechanism.

Response policy includes a self-only Content Security Policy with no inline script requirement,
`frame-ancestors 'none'`, `form-action 'self'`, `base-uri 'none'`, and `object-src 'none'`, plus
`X-Content-Type-Options: nosniff`, `Referrer-Policy: no-referrer`, and no-store caching for
authenticated or sensitive pages. Jinja autoescaping is mandatory; templates never apply `safe`
to practitioner-controlled content.

### Principal revalidation

Every protected request verifies that the current principal remains enabled and its Actor mapping
matches the server session. Every consequential command also passes through existing operational
session validation and current access checks. Access, visibility, accountability, and substantive
authority are recomputed from authoritative state.

If principal status or Actor mapping changes, the server invalidates the browser session and asks
for a new login. If only permissions, assignments, or authority change, the next read reconstructs
the new position and the next command revalidates it. A stale shell never preserves eligibility.

## 10. URL, navigation, and rendering model

Routes are stable resource locators, not semantic authority. Representative M1 routes are:

```text
GET  /login
POST /session
POST /session/logout
GET  /
GET  /cases
GET  /cases/new
POST /cases
GET  /cases/{case_id}
GET  /cases/{case_id}/overview
GET  /cases/{case_id}/evidence-assessment
GET  /cases/{case_id}/decision
GET  /cases/{case_id}/implementation-operation
GET  /cases/{case_id}/learning
GET  /cases/{case_id}/history?effective_at=...&known_at=...
POST /cases/{case_id}/configurations
POST /cases/{case_id}/governing-designations
POST /cases/{case_id}/decision-proposals
POST /cases/{case_id}/decisions/{decision_id}/authorizations
POST /cases/{case_id}/interventions
POST /cases/{case_id}/completion-results
POST /cases/{case_id}/completion-acceptances
POST /cases/{case_id}/activation-authorizations
GET  /administration/...
```

The exact route inventory is finalized incrementally, but the rules are fixed:

- the server parses every path ID and verifies access before disclosing existence;
- a query reconstructs exact current Case/Configuration/Version context from authoritative state;
- forms carry expected Version identities and an opaque server action-intent ID;
- successful POSTs use HTTP 303 Post/Redirect/Get to a newly reconstructed GET;
- stale tabs receive a 409-style practitioner page showing visible changed Versions and a safe
  reconstruction link, not silent rebinding; and
- URLs may select an effective/knowledge context but cannot assert that the result is current.

## 11. Client-side state rule

JavaScript may own only transient presentation state:

- open/closed disclosure state;
- tabs where equivalent server links remain available;
- focus movement and live-region announcement after a server response;
- client-side hints that supplement, but never replace, server validation;
- a submit-in-progress lock for accidental double clicks; and
- confirmation-dialog enhancement where the server confirmation page remains controlling.

JavaScript must not own or compute:

- current Record/Version identity;
- access or visibility;
- accountability or authority;
- action eligibility, lifecycle guards, selection, applicability, or conflict resolution;
- Value/Risk conclusions or combined interpretations;
- idempotency outcome; or
- an optimistic authoritative result.

No service worker, offline command queue, client data store, frontend router, or automatic retry is
used in M1. Essential navigation and forms remain functional when JavaScript is unavailable.

## 12. Concurrency, idempotency, and failure UX

Before showing a consequential confirmation, the server reconstructs the exact source set. The
confirmation intent freezes expected Versions, not authoritative records. On final POST the
adapter and existing command service revalidate currentness and all guards.

The submit button is disabled while a request is in flight, but server idempotency is controlling.
Refreshing or resubmitting the same exact intent uses the same idempotency key. A different input,
target, or expected Version requires a new intent and key.

If the browser loses the response, it does not automatically retry. The result page first queries
the server by the retained action-intent/idempotency/correlation evidence. It either shows the
committed result, a known rejection, or `OUTCOME NOT YET ESTABLISHED` with a deliberate same-intent
retry only where the production contract proves idempotency.

Errors remain distinct:

- authentication/session loss → reauthenticate and reconstruct;
- software access denial → exact permission/action/scope explanation;
- exact visibility denial → bounded non-leaking response;
- accountability vacancy/conflict → owning assignment path, no implicit winner;
- authority vacancy/conflict/invalid basis → substantive owning path, no admin override;
- stale expected Version → compare and deliberately rebuild;
- `DEGRADED` → no new consequential command; and
- unexpected domain failure → preserved correlation/command/audit evidence and no workaround.

## 13. Styling, static assets, and accessibility

M1 uses lightweight repository-owned CSS, semantic HTML components, and a small repository-owned
JavaScript file. It does not adopt Bootstrap, Tailwind, a large design system, an icon package, a
CDN, or a frontend build tool. Templates and static assets are package resources included in the
Python wheel and served at same-origin versioned paths.

Component vocabulary is intentionally small: application shell, breadcrumbs, Case summary,
attention group, state/explanation card, peer analytical lane, data table, error summary,
confirmation basis, provenance disclosure, and accessible status banner. Component behavior is
documented in templates/CSS and tested; it carries no domain logic.

WCAG 2.2 AA is an M1 acceptance target. Architecture requirements include semantic landmarks and
headings, keyboard operation, visible focus, skip link, non-color state cues, correctly associated
labels/descriptions/errors, focus on error summaries and changed content, polite/assertive live
regions as appropriate, reduced motion, zoom/reflow, and exact Value/Risk peer treatment. Standard
HTML is the resilient baseline; automated checks do not replace manual keyboard and assistive-
technology review.

## 14. Local packaging and launch

Add a separate `paim-web` console entry point in M1A. The intended launch shape is:

```powershell
uv run --locked paim-web --config C:\secure\paim-local.json
```

The entry point loads the same validated `LocalConfiguration`, runs schema/health checks, starts one
Uvicorn worker on `127.0.0.1`, and prints the exact URL. Browser auto-open is opt-in through an
explicit flag such as `--open-browser`; it is not the default. Startup fails closed for invalid
configuration, blocked runtime components, incompatible schema, non-loopback bind, or unavailable
secure session/CSRF randomness.

`paim-local` remains supported for bootstrap, recovery, and existing operation. Both entry points
use the same authoritative database and services. Concurrent cross-process writes are not claimed
as a supported M1 workflow until M1A tests SQLite locking, idempotency, currentness, and web-session
revalidation against a concurrent CLI change. A supported operator may stop one interface and use
the other without migration or synchronization.

Expected later dependency impact is:

- runtime: FastAPI, its compatible Starlette version, Jinja2, Uvicorn, and the bounded form-parser
  dependency required by the selected framework path;
- development/test: pytest-playwright and pinned Playwright browser binaries; and
- no Node.js, npm, client framework, HTMX, CSS framework, external session service, Redis, OAuth,
  OIDC, or cloud dependency.

Exact constraints and lock changes belong to M1A after a compatibility/security spike. This issue
changes neither `pyproject.toml` nor `uv.lock`.

## 15. Test architecture

### Existing tests

All current domain, integrity, migration, operational, and I9 hard-oracle tests remain unchanged and
must continue to pass. Browser tests supplement them; HTML does not become a new semantic oracle.

### New layers

1. **Practitioner query unit tests** — exact source Version sets, dual time, explicit
   absence/conflict, five-layer explanations, Value/Risk independence, and access-before-aggregate
   non-leakage.
2. **Command adapter tests** — exact typed mapping, stale preconditions, idempotency reuse,
   unknown-outcome inspection, and lossless error/audit translation.
3. **Session/security tests** — login redaction, session fixation/expiry/logout, principal remap,
   CSRF/origin/referrer, host-header, cookie flags, CSP/headers, no CORS, body limits, and protected
   error non-leakage.
4. **Route/HTTP tests** — FastAPI/Starlette test client with injected clock, session registry,
   configuration, and existing application services.
5. **Template/component tests** — `StrictUndefined`, autoescape, stable semantic landmarks,
   required accessible names, error-summary links, and no domain branching in templates. Prefer
   targeted DOM assertions over broad fragile HTML snapshots.
6. **Browser end-to-end tests** — Python Playwright pytest plugin, role/label locators, web-first
   assertions, JavaScript-enabled and essential no-JavaScript paths, stale tabs, duplicate submit,
   denials, vacancy/conflict, `DEGRADED`, and the complete I9-P1-derived path.
7. **Accessibility tests** — Playwright ARIA snapshots/role assertions plus an axe-core scan adapter
   selected in M1A, followed by manual keyboard, zoom/reflow, contrast, screen-reader, and
   consequential-confirmation checks.
8. **Windows-local launch tests** — locked CPython 3.12 environment, packaged templates/assets,
   loopback bind, printed URL, optional browser open, clean shutdown, and Edge/Chromium smoke.

### Browser technology decision

Use the Python Playwright pytest plugin for M1 browser testing. Compared with Selenium, Playwright
provides built-in isolated browser contexts, auto-waiting/web-first assertions, traces, role/label
locators, and pinned Chromium/Firefox/WebKit binaries under one Python pytest integration. Selenium
is mature and standards-based but requires more explicit driver/wait management for this bounded
repository. Playwright is a development/test dependency only and its downloaded browser footprint
must be documented.

Automated browser accessibility checks cannot prove WCAG conformance. Current Playwright guidance
directs full accessibility-rule scans to tools such as axe; the exact Python integration is deferred
to the M1A dependency spike while ARIA/role assertions and manual checks remain mandatory.

## 16. Technology status and freshness verification

Verified 2026-08-21 against authoritative upstream documentation. Versions below are research
snapshots for dependency planning, not dependency changes or automatic pins.

| Technology | Verified status | Architectural use |
|---|---|---|
| FastAPI | [Release notes](https://fastapi.tiangolo.com/release-notes/) list 0.141.1 (2026-07-29). [Version guidance](https://fastapi.tiangolo.com/deployment/versions/) recommends pinning a tested minor range and allowing FastAPI to select compatible Starlette. | Selected ASGI web/route layer; exact compatible constraint chosen and locked in M1A. |
| FastAPI/Starlette templates | [FastAPI template guidance](https://fastapi.tiangolo.com/advanced/templates/) documents `Jinja2Templates`, template responses, and static files. | Selected server-rendering integration. |
| Jinja2 | [Official changes](https://jinja.palletsprojects.com/en/stable/changes/) list 3.1.6 (2025-03-05), including a sandbox security correction. | Selected template engine; M1A must use a current patched 3.1.x release, autoescape, and `StrictUndefined`. |
| Starlette | [Release notes](https://www.starlette.io/release-notes/) list 1.6.0 (2026-08-08). [Middleware docs](https://www.starlette.io/middleware/) document session cookie controls and trusted-host behavior. | Transitive FastAPI foundation; do not independently pin across FastAPI compatibility. Built-in signed cookie sessions are not selected as PAIM's server-side store. |
| Uvicorn | [Release notes](https://www.uvicorn.org/release-notes/) list 0.46.0 (2026-04-23). | Selected local ASGI server; exact tested range chosen in M1A. |
| python-multipart | [Official releases](https://github.com/Kludex/python-multipart/releases) list 0.0.32 (2026-06-04); multiple 2026 parser advisories affect older releases. | Expected bounded form-parser dependency. M1A must select a current patched release, limit request bodies/fields, and reject file upload where a route does not require it. |
| HTMX | [Official docs](https://htmx.org/docs/) identify 2.x as current and show 2.0.10 assets, progressive enhancement, and CSRF-header support. | Compared but not selected for M1; no dependency added. |
| Playwright Python | [Official releases](https://github.com/microsoft/playwright-python/releases) list 1.62.0 (2026-07-31). [Python installation guidance](https://playwright.dev/python/docs/intro) recommends the pytest plugin and documents supported browser engines/platforms. | Selected browser-test stack for M1A; dependency and browser binaries are pinned together. |
| Selenium Python | [Official Python API docs](https://www.selenium.dev/selenium/docs/api/py/) show 4.47.0 and Python 3.10+ support. | Viable comparison, not selected. |
| Session/CSRF guidance | [OWASP Session Management](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html) and [CSRF Prevention](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html) describe opaque server sessions, cookie controls, expiry, synchronizer tokens, and origin checks. | Basis for the bounded local posture; PAIM still tests its own implementation. |

M1A must recheck all versions, compatibility, security advisories, Python 3.12 support, license
compatibility, Windows behavior, transitive dependencies, and lock reproducibility on the day it
changes dependencies. “Latest” is not itself a selection criterion.

## 17. Reversibility and future extension

The choice is reversible because:

- browser routes depend on application query/command boundaries, not on persistence internals;
- view DTOs are browser-independent and can later serialize to a dedicated API;
- standard forms and full-page templates remain valid if selected routes later return partials;
- repository CSS/components do not bind PAIM to a third-party design system;
- no domain rule, schema, authoritative record, or historical fact depends on Jinja or FastAPI; and
- session state is operational and ephemeral.

M2 Trigger/Reassessment and M3 Management Register should first extend the same server read and
command boundaries. HTMX-style partials may be reconsidered for large Register filters, concurrent
Reassessment panels, or in-place explanations only after accessibility, stale-response, and CSRF
contracts are specified. Rich visualization can be a bounded island fed by immutable DTOs; it does
not require a full client application.

A future remote/multi-user architecture would require HTTPS, durable/distributed sessions,
explicit proxy/host/origin policy, concurrency/load analysis, deployment security, and likely a
versioned external API. M1 does not pretend to satisfy those requirements.

## 18. Bounded implementation increments and gates

### M1A — web foundation, read model, and security shell

Deliver:

- dependency/security/license spike and locked compatible versions;
- `paim-web` factory/entry point, loopback launch, package assets, health/degraded shell;
- server-side session registry, login/logout, principal revalidation, CSRF/origin/host/header policy;
- practitioner read ports, DTOs, access-filtered query service, and Home/Cases read-only views;
- base semantic HTML/CSS components and Playwright harness.

Gate: no domain changes; login secret never persists; access filtering precedes aggregation; views
carry exact basis/time; no-JS navigation works; existing full tests and new security/browser tests
pass.

### M1B — Case/Configuration and Evidence/Value/Risk Workspace

Deliver explicit Case and Configuration commands/designation, Overview, Evidence/Authority/
Applicability, and independent Value/Risk views/actions.

Gate: every form maps to one existing capability; exact preconditions and idempotency proven;
missing/conflicting Evidence remains explicit; lanes remain independent; no hidden CLI repair in
the bounded path.

### M1C — Integration/Boundary and Decision

Deliver integration, uncertainty, alternatives, Boundary, Decision proposal, Decision
Authorization, and `Why?/What can change it?` explanations.

Gate: proposal/authorization separation is hard-oracle tested; complete authority basis and stale
Version checks remain server-authoritative; no generic approval or administrator override exists.

### M1D — Intervention, Completion, Activation, Learning, and History

Deliver Intervention/obligations, Completion Result, accountable Completion Acceptance,
prerequisite evaluation, Activation Authorization, bounded operation, Learning, management history,
and exact provenance.

Gate: every authoritative distinction remains visible; target operation cannot appear before exact
Activation Authorization; dual-time history reconstructs without mutation.

### M1E — full browser acceptance and practitioner usability

Deliver complete I9-P1 browser automation, denial/vacancy/conflict/degraded/stale/unknown-outcome
oracles, accessibility automation/manual evidence, Windows-local operation, and a bounded human
confirmation of the accepted experience architecture.

Gate: independent review accepts semantic, security, accessibility, and practitioner evidence.
M2/M3 do not start automatically.

Each increment uses one issue, one bounded branch, one draft PR, independent review, merge,
cleanup, and clean-main checkpoint.

## 19. Risks and mitigations

| Risk | Mitigation / gate |
|---|---|
| Query composition reimplements domain selection | Query service calls existing selectors/resolvers; exact source-set tests compare authoritative results; no template selection logic. |
| Access leakage through Home counts or errors | Calculate trusted visible scope before reads/aggregation; test hidden IDs, facts, match counts, timing-insensitive error shapes, and same-Case Configuration denial. |
| Templates accumulate business rules | Templates receive finished enums/labels/explanations and use only presentation branching; template review and tests reject selector/authority logic. |
| Localhost is mistaken for no security boundary | Exact loopback bind, trusted hosts, same-origin policy, CSRF, strict cookies, CSP, no CORS, redaction, and explicit remote-use rejection. |
| HTTP cannot use a Secure cookie | Document the loopback-only exception; use HttpOnly/SameSite Strict/host-only; require Secure + `__Host-` for any future HTTPS or non-loopback mode. |
| In-memory sessions disappear or do not scale | Treat restart logout as M1 behavior; one worker only; durable/distributed session architecture is a future gate. |
| Stale tabs submit obsolete Versions | Server-bound confirmation intent, exact expected Versions, command-time guards, 409 reconstruction, and no silent rebind. |
| Double submit or lost response creates duplicate effects | Stable server idempotency key per action intent, submit lock as enhancement, outcome inspection, and no automatic retry. |
| Concurrent CLI/web changes surprise the session | Revalidate principal mapping and authoritative command guards; explicitly test or withhold concurrent-write support. |
| Jinja/XSS or unsafe static dependencies | Autoescape, `StrictUndefined`, no unsafe `safe`, CSP/no inline scripts, no CDN, patched versions, and malicious-content tests. |
| Playwright adds large binaries | Development-only dependency, pin browser/package together, document cache/install, and use a bounded CI browser matrix. |
| Automated accessibility produces false confidence | Manual keyboard, zoom, contrast, and screen-reader checks remain required; human acceptance closes M1E. |
| Later partial/rich interactions force a rewrite | Keep query DTOs and command adapter browser-independent; enhance or replace only `paim.web`. |

## 20. Explicitly deferred choices

M1A may decide exact details within this architecture:

- tested FastAPI/Jinja2/Uvicorn/form-parser versions and dependency ranges;
- precise module filenames and public port names;
- default local port and safe configurable range;
- exact template inheritance and CSS token names;
- whether the action-intent registry shares the in-memory session store implementation;
- exact axe-core Python/Playwright integration; and
- the bounded cross-browser CI matrix.

The following require separate architecture authority and are not M1A choices:

- HTMX adoption, dedicated client/API, Node build, or third-party design system;
- durable/distributed sessions or multi-worker operation;
- HTTPS certificate lifecycle, reverse proxy, non-loopback/remote exposure, or multi-user hosting;
- OAuth, OIDC, enterprise identity, or new credentials;
- domain/specification/schema changes or new workflow/authority semantics;
- M2 Trigger/Reassessment, M3 Register interaction, IRR-009/IRR-014 extensions; and
- PAE/APRM technology or semantic reuse.

## 21. Capability trace and hard boundaries

| M1 browser work | Existing production owner or new read-only composition |
|---|---|
| Case and Configuration create/designate | Existing Increment 2 commands and governing selector. |
| Roles/accountability | Existing Role Assignment commands and accountability resolvers. |
| Evidence/Authority/Applicability | Existing Increment 3 commands and selectors. |
| Independent Value/Risk Inputs and selection | Existing lane-specific Increment 3 commands/selectors, invoked independently. |
| Integration/Boundary/Decision | Existing Increment 4 commands, authorization guards, and current Decision selector. |
| Intervention/Completion/Acceptance/prerequisites/activation/Learning | Existing Increment 5 commands/evaluators and Case transition guards. |
| Home, Case Workspace, explanation, and history | New access-filtered application read composition over existing authoritative records, selectors, resolvers, dual-time history, and audit; no new governing facts. |
| Browser identity/access | Existing operational authentication/current-session/access behavior behind a new ephemeral browser session adapter. |

Every implementation increment must preserve:

- authoritative server-side exact identity/currentness and immutable history;
- Value/Risk independence and Evidence applicability scope;
- identity → software access → exact visibility → accountability → substantive authority;
- proposed Decision → Decision Authorization → prerequisites → Activation Authorization;
- dual-time reconstruction, provenance, audit, and access-filtered non-leakage;
- IRR-009/IRR-014 exclusions;
- no generic approval/resolution/workflow engine;
- no priority, risk, readiness, severity, strength, or state rank;
- no semantic matching as authority; and
- no client-side domain authority.

## 22. Final gate recommendation

The architecture decision is complete enough to open a separately bounded M1A implementation
issue. Option A meets the accepted M1 experience without weakening semantic integrity, creates a
clear server-side read and command boundary, establishes a concrete local security/session model,
keeps dependency and toolchain growth bounded, and remains reversible.

**Gate recommendation: READY FOR BOUNDED M1 FOUNDATION IMPLEMENTATION.**

This recommendation does not authorize implementation in this issue or automatic follow-on work.
