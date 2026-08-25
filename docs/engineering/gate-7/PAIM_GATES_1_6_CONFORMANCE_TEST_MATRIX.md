# PAIM Gates 1–6 Conformance Test Matrix

## Rule

Every hard oracle in the accepted Behavioral Validation Strategy remains controlling. This matrix
allocates those oracles to implementation layers and slice exits; it does not replace or weaken
them. “No mutation” means no authoritative Version, relationship, event, audit success,
idempotency success, or family row is appended.

## Test layers

- **U** — pure domain/unit;
- **P** — persistence, constraint, migration, and adapter contract;
- **T** — transaction, concurrency, idempotency, and replay;
- **A** — access and non-disclosure;
- **Q** — selector/query/dual-time composition;
- **C** — application command integration;
- **B** — browser/practitioner flow; and
- **H** — separately authorized human Harborlight validation after implementation.

## Common integrity and semantic era — Gate 1

| Oracle | Layers | Required proof | Slice |
|---|---|---|---|
| Prospective Version envelope complete | U/P/C | contract ID/version, exact context, dual time, attribution, command/audit all present or no mutation | A |
| Legacy row remains legacy | P/Q | no semantic metadata backfill; exact legacy digest and reconstruction unchanged | A–G |
| Canonical exact context | U/P | member permutation yields same canonical digest; duplicate/invalid member rejected | A |
| Context is not authority/equivalence | U/C | matching digest creates no access, Responsibility, Applicability, adequacy, reliance, or Decision | A |
| Selector one/absence/conflict | U/P/Q | no recency, role, specificity, presentation, or insertion-order winner | every family |
| Dual-time boundary | U/P/Q | effective-at and known-at vary independently; later recorded fact cannot contaminate earlier knowledge | A–G |
| Natural multi-fact atomicity | T/C | each constituent guard failure produces zero mutation; success emits all facts and one coherent audit basis | A–E |
| Exact replay and mismatch | T/C | same key+digest returns original outcome; changed contract/context/payload rejects | A–E |
| Stale write/concurrency | T/C | expected-Version change fails; two writers cannot both commit incompatible successors | A–E |
| Access before composition | A/Q/B | hidden fact cannot affect count, conflict, attention, label, relationship, timing, or source manifest | B–G |
| No silent legacy fallback | P/Q/C | absent prospective basis returns not established unless named adapter/consumer contract exists | A–G |
| Cross-era conflict | U/Q/C | incompatible declared sources return explicit conflict, never merge or winner | A–G |

## Responsibility and Case Work — accelerated Gates 2/4

| Oracle | Layers | Required proof | Slice |
|---|---|---|---|
| Responsibility exact signature | U/P/Q | obligation kind plus exact context distinguishes materially different duties | A |
| One/vacancy/conflict | U/P/Q/B | exact eligible assignment, none, and incompatible co-current assignments remain distinct | A |
| Access/role/authority separation | U/A/C/B | principal, visibility, practical role, Responsibility, and substantive authority never substitute | A–D |
| Same Actor, distinct Responsibilities | U/C/B | one participant may act naturally while each basis and result remains separate | A/C |
| Assignment history | P/Q | reassignment, delegation, withdrawal, expiry, correction, supersession reconstruct exactly | A |
| Assignment is not result | U/C | assignment creates no Applicability, assessment, acceptance, Decision, or completion fact | A |
| Derived versus durable work | U/Q/C | deterministic attention needs no Work; durable coordination keeps request/assignee/history | A |
| Result/link/return atomicity | T/C | governed result and required Work links commit together; Work never substitutes for result | A |
| Stale Work no-retarget | U/T/C | changed source/context rejects old Work; no silent new target | A |
| Handoff restart continuity | P/C/B | new session reconstructs exact source/question/return from persisted state | A/H |
| Work non-disclosure | A/Q/B | hidden source/Case does not leak through Work labels, counts, return path, or errors | A |

## Continuing Case and Configuration — Gate 3

| Oracle | Layers | Required proof | Slice |
|---|---|---|---|
| Three statuses only | U/P | prospective continuity uses `OPEN`, `CLOSED`, `SUPERSEDED`; subordinate state does not invent a phase | B |
| Case opens prospectively | T/C/B | natural create/open action atomically establishes exact Case, Configuration context, and `OPEN` | B |
| Same Case versus new Case | U/C | material use difference requires accountable determination/new identity; no silent retarget | B |
| Governing Configuration | U/Q | one/absence/conflict by exact context/time; alternative never becomes governing by display | B |
| Closure guards | U/T/C | operation stopped with Work/obligation/review/learning/authority remaining stays `OPEN` with no mutation | B |
| Reopen | U/T/Q | eligible determination restores `OPEN` prospectively and preserves closure history | B |
| Superseded terminal | U/P/C/B | named successor linked; predecessor accepts no new substantive Work/Decision | B |
| Legacy phase isolation | P/Q/B | old lifecycle events remain exact and do not imply target continuity status | B |
| Decision-bound reconstruction | Q/A | continuity view at Decision time uses exact then-current Case/Configuration and access | B/G |

## Continuing review and timing — Gate 5

| Oracle | Layers | Required proof | Slice |
|---|---|---|---|
| Planned point one/absence/conflict | U/P/Q | exact Case/Decision/Configuration/purpose/time selector with no cadence default | E |
| Required constraint source/Applicability | U/P/C | source presence alone creates no constraint; every constraint retains exact source and limits | E |
| Constraint intersection | U/Q | compatible `BY`/`NOT_BEFORE`/`WINDOW` intersection retains all sources; empty/indeterminate is conflict | E |
| Plan authority boundary | U/C | planning Responsibility cannot amend Decision condition or waive a governing constraint | E |
| Arrival is attention only | U/Q/B | due/missed date creates no Trigger significance, staleness, Reassessment, invalidity, priority, or suspension | E |
| Event before plan | U/C/Q | exact event provenance and accountable determination proceed; future point retained/cancelled/superseded explicitly | E |
| Focused one-lane refresh | U/C/Q | affected lane changes; other exact lane continues only under its own guards | E |
| No periodic copying | P/Q | unchanged state reuses exact Version; no successor created merely by review/cadence | E |
| Review completion outcome | T/C | exact Confirmation or successor path; zero/both invalid; optional next point separately valid and atomic | E |
| Expected/observed comparability | U/Q | all exact guards pass before comparison; non-comparable claims remain separate | F |
| No outcome inference | U/Q/B | delta creates no causality, materiality, priority, Decision error, or management outcome | F |

## Value/Risk assessment, adequacy, reliance, and quantitative claims — Gate 6

| Oracle | Layers | Required proof | Slice |
|---|---|---|---|
| Finish assessment | T/C/B | exact candidate finalization and Readiness commit together; no separate system click | C |
| Successor-on-edit | U/P/Q | material edit creates successor not ready; predecessor and readiness remain historical | C |
| Neutral adequacy | U/C/B | favorable, unfavorable, and uncertain conclusions can be `ADEQUATE` on quality grounds | C |
| Adverse adequacy | U/C | exaggeration, incompleteness, hidden uncertainty, unsupported generalization, false precision yield valid `NOT_ADEQUATE`/`INDETERMINATE` paths | C/F |
| Applicability distinct | U/C | adequate cannot repair missing/conflicting information Applicability | C |
| Adequacy not desirability | U/Q/B | result creates no Case support, acceptable Risk, reliance, Integration, or Decision | C |
| One candidate combined review | T/C/B | same Actor with both Responsibilities commits distinct adequacy+reliance facts through one action | C |
| Different Actors | U/C/B | separate attributable actions; neither Actor attests for the other | C |
| Multiple candidates | U/Q/C/B | explicit choice/dispositions; uniqueness never auto-selects and presentation never wins | C |
| Lane independence | U/P/Q/C | Value and Risk identities, sources, Responsibility, adequacy, reliance, refresh, and history remain separate | C–F |
| Legacy Fitness/Selection isolation | P/Q/C | Fitness is not adequacy; Acceptance/Selection is not reliance; adapter provenance explicit | C/D |
| Exact prospective Integration basis | U/Q/C | one relied chain per lane with Input/Readiness/Adequacy/Reliance/information basis | D |
| Changed lane invalidates chain | T/C | old Integration/Boundary/proposal/authorization cannot proceed; old records remain historical | D |
| Six quantitative types | U/P/Q | controlled types remain distinct with stable identity/version/history | F |
| Qualitative legitimacy | U/C/B | no defensible number is a valid bounded result, not automatic incompleteness | C/F |
| Material context and false precision | U/C | only material fields required; missing material context explicit; system does not invent values | F |
| No universal calculation | U/Q/B | no ROI, net Value, probability×impact, common score, ranking, recommendation, or cross-lane offset | F |
| Estimate/observation separation | P/Q | 20–35% expectation and later 24% result remain different Versions/types/knowledge times | F/G |
| Observation boundary | U/P/Q | `OBSERVED_RESULT` creates no first-class Observation, telemetry, Trigger, or causality semantics | F |

## Cross-cutting practitioner and Harborlight acceptance

| Oracle | Layers | Required proof | Slice |
|---|---|---|---|
| Natural language boundary | B/H | no default task requires semantic era, context set, readiness event, adequacy ID, reliance designation, Work link, selector, dual-time control, or transaction term | H |
| Progressive disclosure | A/Q/B/H | ordinary view shows meaning/consequence; authorized provenance shows exact basis without new authority | B–H |
| Fail-closed explanation | C/B/H | visible vacancy/conflict/stale/missing authority explains why and legitimate next action without leakage | A–H |
| Management record emerges | P/Q/B/H | ordinary acts create reconstructable exact history; no duplicate narrative task | G/H |
| Then versus now | Q/A/B/H | exact Decision-time basis and current knowledge stay separate; decision quality and outcome quality not collapsed | G/H |
| Harborlight full journey | C/B/H | fresh disposable prospective fixture passes the accepted 15-step simulation and burden review | H only |
| Historical Harborlight unchanged | P/Q | existing fixture/reference/live semantic digest unchanged across upgrade and H validation | every migration/H |

## Required execution gates

Every implementation PR runs, at minimum:

- `uv lock --check` under the accepted CPython 3.12 runtime;
- full pytest, plus focused slice tests and browser tests where applicable;
- Ruff format check and lint;
- strict mypy on `src/paim`;
- empty database to head and every supported prior revision to head;
- programmatic schema/constraint/index/trigger/foreign-key verification;
- transaction/replay/contention suite;
- access/non-disclosure and dual-time suites;
- legacy semantic digest and adapter suites; and
- `git diff --check` and tracked-source secret scan.

Human Harborlight validation is deferred to Slice H and must record actual practitioner observations
without inference. Automated completion never substitutes for that evidence.
