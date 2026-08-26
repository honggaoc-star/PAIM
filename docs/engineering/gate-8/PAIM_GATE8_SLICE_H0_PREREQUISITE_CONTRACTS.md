# Gate 8 Slice H0 — Production prerequisite contracts

## Implemented boundary

Slice H0 resolves the two production seams identified at Slice-H entry. It adds no practitioner
screen, route, workflow, scheduler, deployment capability, telemetry, analytics, or Harborlight
mutation.

## Pre-Case Case initiation

`case-initiation-authority` is a distinct pre-Case authoritative family. An operationally
authorized recorder captures an external organizational mandate and its provenance; recorder
permission is not the mandate. Active Versions bind one authorized Actor, local/organizational
scope, `CREATE_OPEN_CASE`, optional management-use prefixes, effective/recorded time, and immutable
succession/withdrawal history.

`CaseContinuityService.initiate_case` accepts the ordinary material request and generates every
PAIM identity and exact Case context internally. It selects and revalidates exactly one matching
pre-Case mandate, then uses the existing outer semantic transaction to create the Case, governing
Configuration/designation, `OPEN` status, and the initial continuity Responsibility, Assignment
Basis, and assignment. Exact replay preserves the first identities. The mandate cannot authorize
any post-Case substantive act.

The prior exact Case-bound `open_case` path remains available for compatibility and retains its
existing hard oracles. No legacy or prospective fact is backfilled or reinterpreted.

## Exact-source visibility

`source_access_grants` stores append-only exact-source software-disclosure facts. Each fact binds a
principal, read purpose, Case, optional Configuration, exact source Version and family, `ALLOW` or
`DENY` effect, effective interval, recorded time, and deterministic sequence. Resolution is dual
time and fail-closed. Case navigation access is still required, but never overrides an absent or
denied exact-source decision.

`OperationalSliceAAccessPolicy` now consumes the source Version/family supplied by the accepted
prospective services. Non-source navigation and write behavior retain the existing bounded
GLOBAL/CASE/CONFIGURATION model. Exact-source administration records software visibility only and
cannot grant PAIM Responsibility or authority.

## Persistence and compatibility

Migration `0017_gate8_slice_h0_prerequisites` is additive from
`0016_gate8_reconstruction_support`. It adds only:

- `case_initiation_authority_versions`;
- `source_access_grants`;
- exact foreign keys, selection/resolution indexes; and
- append-only update/delete triggers.

There is no authority or access backfill. Existing installations therefore disclose prospective
source content only after explicit exact-source grants are appended; legacy read behavior remains
under its original contract. Downgrade is permitted only while both new tables are empty.

## Vertical proof

The production-adapter oracle records a disposable pre-Case mandate, opens a fresh prospective
Case through the minimal natural command, verifies its exact initial Responsibility/Assignment
basis, grants navigation access, allows one exact source, denies another exact source in the same
Case, composes the Case without disclosing the denied source, and reconstructs the same result
after application restart. It uses no selective access test double and changes no historical
Harborlight environment.

Slice H may re-enter only with these contracts present. Practitioner UI Contract v1.0 and accepted
Slices A–G remain unchanged.

## Validation evidence

- locked dependency graph: PASS (`uv lock --check`);
- focused Slice-H0 hard oracles: PASS (8 tests);
- accepted Slices A–G plus Slice H0: PASS (66 tests);
- operational, recovery, practitioner-query, Increment-9, and migration assurance: PASS (56 tests);
- complete repository suite: PASS (365 tests);
- Ruff format and lint: PASS;
- strict mypy over `src/paim`: PASS (81 source files);
- additive migration from an empty database and exact prior revision `0016`: PASS;
- tracked-source high-confidence credential scan: PASS; and
- `git diff --check`: PASS.
