# PAIM v0.1 Python 3.12 Runtime Migration Evidence

## 1. Accepted decision and starting checkpoint

GitHub Issue #73 implements the runtime-only decision accepted through Issue #71 and merged PR #72:

**STANDARDIZE PAIM V0.1 ON CPYTHON 3.12**

| Identity | Value |
|---|---|
| Starting clean-main commit | `963c2b9b7a5121ab4ad1bd7a5c635eee4bbfeb04` |
| Migration branch | `runtime/python-3-12-v0-1` |
| Validated implementation commit | `8a0b9088505aca945f51831ec063aeccee041012` |
| Validation date | 2026-08-19 |
| Controlling decision | `PAIM_V0_1_PYTHON_RUNTIME_BASELINE_DECISION_v0.1.md` |
| Alembic schema head | `0008_increment_8` |

This migration changes only the supported runtime/toolchain contract and the minimum compatible
source, dependency, tests, and setup documentation. No governing specification under
`docs/system/specifications/` changed. No database revision, PAIM record family, management
semantic, product capability, or authoritative-output meaning changed.

PR #70 remained draft and unmodified. Human practitioner validation did not resume.

## 2. Selected exact reference Python patch and provenance

The supported package/runtime line is CPython `>=3.12,<3.13`. The exact reproducible reference patch
is CPython `3.12.13`, recorded in `.python-version`.

Validation used the Issue #73-authorized, locally policy-permitted interpreter at:

`C:\Users\gaohe\miniforge3\envs\llm312\python.exe`

The locked repository `.venv` was recreated from that interpreter by:

```text
uv sync --locked --python C:\Users\gaohe\miniforge3\envs\llm312\python.exe
```

Observed runtime identity:

| Component | Exact observed value |
|---|---|
| Python | `3.12.13`, packaged by conda-forge, build date 2026-03-05, MSC v.1944 64-bit AMD64 |
| Repository interpreter | `C:\Users\gaohe\Documents\GitHub\PAIM\.venv\Scripts\python.exe` |
| SQLite | `3.53.1` |
| uv | `0.12.5` (`210d1f678`, x86_64-pc-windows-msvc) |

Windows Application Control permitted the interpreter, `_sqlite3`, the locked native wheels, the
test suite, and the built-wheel smoke environment to execute. `Get-AuthenticodeSignature` reported
the source interpreter executable as `NotSigned`. This does not invalidate the Issue #73-authorized
policy-permitted evidence, but it prevents any inference that publisher signing establishes trust or
that the same distribution is automatically allowed on another workstation. Every deployment still
requires explicit local security-policy approval; matching `3.12.13` alone is insufficient.

## 3. UUIDv7 provider selection and rationale

PAIM now uses `uuid6==2025.0.1`, constrained in `pyproject.toml` as
`uuid6>=2025.0.1,<2026` and resolved exactly in `uv.lock`.

The provider satisfies the Issue #73 criteria:

- it returns standard-library `uuid.UUID` values;
- its UUIDv7 values carry version 7 and the RFC variant;
- it implements local RFC 9562 UUIDv7 generation without a network/runtime service;
- it is pure Python and supports CPython 3.12;
- package metadata declares the MIT license;
- the package has no transitive dependencies of its own;
- the resolved wheel and source archive are hash-locked; and
- the implementation is compact and reviewable.

The resolved wheel SHA-256 is
`80530ce4d02a93cdf82e7122ca0da3ebbbc269790ec1cb902481fa3e9cc9ff99`; the source archive SHA-256 is
`cd0af94fa428675a44e32c5319ec5a3485225ba2179eefcf4c3f205ae30a81bd`.

No stored identity format changed. PAIM continues to accept and persist canonical UUID text, parse it
through `uuid.UUID`, reject non-version-7 identity values, and treat every identity as opaque. The
provider's time-local generation behavior is not currentness, precedence, rank, tie-break, or
authority. Existing conflict selection still returns all eligible incompatible candidates.

## 4. Repository, runtime, and lock changes

The implementation commit makes these bounded changes:

1. `.python-version` now records `3.12.13`.
2. `pyproject.toml` supports `>=3.12,<3.13`, targets Ruff `py312` and mypy `3.12`, retains uv
   `==0.12.5`, and adds the narrow UUIDv7 dependency.
3. `uv.lock` was regenerated on CPython 3.12.13. Every pre-existing package version was retained;
   only CPython-specific wheel sets changed and `uuid6==2025.0.1` was added.
4. `paim.integrity.ids` imports UUIDv7 generation from the locked provider while retaining
   standard-library `UUID` values and all nominal identity wrappers.
5. The one Python-3.14-only multiple-exception clause is parenthesized with unchanged behavior.
6. Targeted tests prove UUID version/variant, uniqueness, parse/text round-trip, persisted text
   compatibility, no identifier-order winner, and both intended recovery exception types.
7. README, the Increment 1 technology foundation decision, and the local operator guide now state
   the 3.12 contract, exact reference patch, locked workflow, and Application Control prerequisite.

Locked top-level identities:

| Package | Version |
|---|---|
| PAIM | `0.1.0` |
| Alembic | `1.19.1` |
| SQLAlchemy | `2.0.52` |
| uuid6 | `2025.0.1` |
| pytest | `9.1.1` |
| mypy | `1.20.2` |
| Ruff | `0.16.3` |

`uv lock --check` resolved 19 packages without mutation. The final `uv.lock` SHA-256 is
`C9A7FCF3906EF775AD797FED0239562E5A6FA564DD0973B3300733D2182D383C`.

No database migration or historical-record rewrite was required.

## 5. Compatibility-test evidence

The targeted migration oracles passed under the locked CPython 3.12.13 environment:

| Oracle | Evidence |
|---|---|
| Generated identity version | 10,000 generated identities were all UUID version 7 |
| RFC variant | all 10,000 generated identities reported the RFC variant |
| Representative uniqueness | 10,000 generated values produced 10,000 distinct UUIDs |
| Text parse/round-trip | fixed historical-compatible UUIDv7 text parsed and returned byte-for-byte identical canonical text |
| Persisted value compatibility | fixed Record/Version UUIDv7 text persisted in SQLite unchanged and reloaded through the public history API |
| Non-ordering authority | equal-time candidates remained an explicit conflict containing every candidate, independent of input/UUID order |
| Recovery syntax behavior | both `OSError` and `sqlite3.DatabaseError` produced explicit `DATABASE_UNAVAILABLE` degraded readiness |

The final targeted runs were:

- identity, time/selection, and recovery: 16 passed in 6.32s;
- fixed persisted UUIDv7 contract: 1 passed in 2.04s.

A source scan found four UUID/identifier sorting sites. Each is non-authoritative: deterministic
conflict text, deterministic exact-scope partition presentation, or deterministic Register output
ordering. None selects a winner, establishes currentness, resolves conflict, ranks a management
state, or grants authority. Their existing hard-oracle coverage passed unchanged.

## 6. Full regression, schema, recovery, and static evidence

### 6.1 Locked full regression

`uv run --locked pytest` passed **246/246** tests in 758.73s (12m38s).

The population includes all accepted Increment 1–8 behavior, migration/schema coverage, transaction
and idempotency behavior, exact history, Value/Risk independence, authorization, intervention,
reassessment, Management Register, security/access, recovery, degraded operation, and the five new
runtime-migration oracles.

### 6.2 Independently focused Increment gates

| Gate | Result |
|---|---|
| Increment 1 integrity/identity/time/transaction | PASS — 25 passed in 28.91s |
| Increment 2 Case/Configuration/lifecycle/Roles | PASS — 17 passed in 54.08s |
| Increment 3 Evidence/Authority/Value/Risk | PASS — 12 passed in 40.81s |
| Increment 4 Integration/Boundary/Decision | PASS — 19 passed in 64.03s |
| Increment 5 Intervention/Acceptance/Activation/Learning | PASS — 21 passed in 89.42s |
| Increment 6 Trigger/Reassessment/interim disposition | PASS — 47 passed in 181.89s |
| Increment 7 Management Register/shared dependency | PASS — 64 passed in 144.37s |
| Increment 8 local operational/configuration | PASS — 24 passed in 89.70s |

PR #70's four Increment 9 automated tests are not present on accepted `main`. They were not copied,
cherry-picked, or executed here because doing so would modify or prematurely reconcile PR #70.
They remain mandatory regression evidence after PR #70 is separately reconciled onto an accepted
3.12 clean-main baseline; they do not substitute for human I9-P1/P2/P3 evidence.

### 6.3 Migration and schema

The independently focused migration/schema file passed 16/16 tests in 44.63s. It covers empty and
supported prior revisions, constraints, indexes, append-only triggers, and foreign keys.

Additional direct checks reported:

| Check | Result |
|---|---|
| Alembic head | `0008_increment_8` |
| Empty SQLite database to head | PASS — `0008_increment_8` |
| Prior `0007_increment_7` to head | PASS — `0008_increment_8` |
| Head schema inventory | 136 tables, 97 check constraints, 429 foreign keys, 58 indexes, 268 triggers |
| Runtime FK enforcement | `PRAGMA foreign_keys = 1` |
| SQLite integrity | `PRAGMA quick_check = ok` |

The Python runtime change required no Alembic revision and did not alter schema identity.

### 6.4 Recovery, degraded operation, and security

An independent eight-test assurance gate passed in 28.45s. It directly covered:

- online backup, checksum/manifest/table evidence, separate restore, restart, authentication, and
  authoritative-history reconstruction;
- tampered-backup and incompatible-schema rejection;
- explicit degraded readiness for missing spool and both database failure classes;
- bad, disabled, and unmapped credential behavior;
- hidden Case/Configuration identifier, fact, and count non-leakage; and
- configuration failure without external credentials plus CLI secret hygiene.

A tracked-file high-confidence private-key/cloud/GitHub/API credential scan found no matches.

### 6.5 Build, sync, and static checks

| Check | Result |
|---|---|
| `uv lock --check` | PASS — 19 packages |
| locked environment sync | PASS — repository `.venv` recreated on CPython 3.12.13; 19 packages installed |
| source distribution build | PASS — `paim-0.1.0.tar.gz` |
| wheel build | PASS — `paim-0.1.0-py3-none-any.whl` |
| isolated wheel install | PASS — PAIM and all declared application dependencies installed |
| isolated import/identity smoke | PASS — PAIM imported; generated value was UUID version 7 with RFC variant |
| Ruff format check | PASS — all 69 tracked Python files formatted |
| Ruff lint | PASS — all 69 tracked Python files |
| strict mypy | PASS — 43 source files |
| `git diff --check` at implementation commit | PASS |

## 7. Deviations and residual risks

No technical or semantic migration defect remains. The following validation-harness events were
classified and corrected without changing PAIM behavior:

1. A first focused-gate command used nested pytest `--basetemp` paths without creating their parent.
   Pytest produced setup `FileNotFoundError` results before database fixtures ran. The parent was
   created and every Increment 1–8 gate then passed independently.
2. A repository-wide Ruff format traversal encountered older inaccessible ignored pytest directories
   and panicked before format judgment. The authoritative rerun enumerated every tracked Python file:
   all 69 passed format and lint. No source file was omitted.
3. One inline schema-inventory command was initially misquoted by PowerShell and did not execute.
   The corrected command upgraded a fresh database and produced the inventory in §6.3.
4. During pre-commit test authoring, the new persistence oracle initially treated the public
   `RecordHistory.versions` frozenset as an indexed object. The oracle was corrected before the
   validated implementation commit; product code was unchanged.

Residual risks and controls:

- CPython 3.12 has a shorter remaining upstream support horizon than 3.14. A new runtime decision is
  required before 3.12 end of life or an incompatible maintenance horizon.
- The reference conda-forge interpreter is not Authenticode-signed. Current Application Control
  permitted it, but each target workstation must separately approve its runtime provenance and
  native components.
- `uuid6` is a new supply-chain dependency. Its tested release line is narrowly constrained, exact
  artifacts are hash-locked, it has no dependencies/runtime service, and future upgrades require a
  bounded full-regression change.
- UUIDv7 contains time-derived bits. PAIM continues to prohibit identity order from becoming
  currentness, precedence, ranking, tie-break, or authority.

## 8. PR #70 and Increment 9 implications

This migration does not make PR #70 ready and does not validate I9-P1, I9-P2, or I9-P3.

After this migration is independently accepted and merged:

1. establish a clean synchronized 3.12 `main` checkpoint;
2. separately reconcile/rebase PR #70 onto that accepted runtime baseline;
3. rerun the complete release regression, including PR #70's Increment 9 automated tests, with exact
   Python/SQLite/uv/lock/source identities;
4. restart human practitioner validation from I9-P1, followed by I9-P2 and I9-P3 one at a time; and
5. replace all inferred practitioner claims with exact human actions and observations before PR #70
   can return ready for independent review.

PR #70 must remain draft and unmerged until that separate sequence is complete.

## 9. Final migration verdict

The CPython 3.12 migration preserves PAIM semantics, identity and serialized value contracts,
database/schema identity, historical reconstruction, authoritative outputs, security boundaries,
and all accepted Increment 1–8 behavior. The supported/runtime and reproducibility contracts are
internally consistent and fully validated at the recorded implementation commit.

**PAIM V0.1 CPYTHON 3.12 RUNTIME MIGRATION ACCEPTED**
