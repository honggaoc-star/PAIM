# PAIM v0.1 Python Runtime Baseline Decision

## 1. Purpose and trigger

This artifact answers GitHub Issue #71. It reviews the PAIM v0.1 Python runtime contract before
Increment 9 practitioner validation resumes and before draft PR #70 can be considered for merge.

The trigger was environmental, not a PAIM command result. The first I9-P1 bootstrap attempt stopped
while CPython imported `_sqlite3`; Windows Application Control blocked a native file under the
repository-local uv-managed CPython 3.14.6 runtime. PAIM bootstrap did not execute. A discovered
`python3.14.exe` was an unsigned uv trampoline and was also unable to launch its child runtime. The
event is therefore not practitioner evidence against PAIM semantics or application behavior, but it
is direct evidence that the current runtime contract is not operable on the intended workstation
without additional runtime approval or provisioning.

This is an analysis and recommendation only. It does not change the runtime, PAIM specifications,
PR #70, or practitioner evidence.

## 2. Current runtime contract

The accepted `main` baseline at `62c5d807c2cfec4d13c0f4c9d4f15280511327db` states:

| Contract surface | Current value |
|---|---|
| `.python-version` | `3.14.6` |
| `pyproject.toml` package requirement | `requires-python = "==3.14.6"` |
| Ruff language target | `py314` |
| mypy language target | `3.14` |
| uv tool contract | `==0.12.5` |
| `uv.lock` Python requirement | `==3.14.6` |

`PAIM_INCREMENT_1_TECHNOLOGY_FOUNDATION_DECISION_v0.1.md` selected CPython 3.14.x primarily for a
typed synchronous Python implementation, the mature Python SQL/testing ecosystem, timezone-aware
standard types, and standard-library UUIDv7. It made the exact patch a reproducibility policy: the
latest accepted 3.14 patch was to be pinned at bootstrap, patch upgrades were to receive bounded full
regression, and minor-version changes were to require a new decision.

That earlier decision is the only accepted PAIM architecture or engineering artifact that requires
3.14 specifically. No governing artifact under `docs/system/specifications/` requires CPython,
Python 3.14, `uuid.uuid7()`, unparenthesized exception syntax, or any other 3.14 facility.

## 3. Evidence inventory

The review used two source checkpoints without modifying PR #70:

- accepted pre-Increment-9 baseline: `62c5d807c2cfec4d13c0f4c9d4f15280511327db`;
- current PR #70 analysis checkpoint: `2dcf1e44c621d2464916caa5d1a7417df45ff93c`.

The following evidence was inspected or executed:

1. `.python-version`, `pyproject.toml`, `uv.lock`, package/build metadata, README, operator guide,
   Increment 1 technology decision, platform architecture, system specifications, and PR #70
   validation/release artifacts;
2. every Python file under `src/paim`, `tests`, and `migrations`, including syntax compilation and
   searches for version-specific syntax, standard-library APIs, typing features, SQLite use, and
   UUID generation;
3. current SQLAlchemy Core, Alembic, SQLite, pytest, Ruff, and mypy paths, migrations, fixtures,
   recovery tests, deterministic serialization, and exact-history tests;
4. an isolated, policy-permitted CPython 3.12.13 process from
   `C:\Users\gaohe\miniforge3\envs\llm312\python.exe`, with SQLite 3.53.1;
5. a temporary copy of PR #70 checkpoint `2dcf1e4`, never used to alter either PAIM branch;
6. installation of the exact locked application/dev versions on CPython 3.12: Alembic 1.19.1,
   SQLAlchemy 2.0.52, pytest 9.1.1, mypy 1.20.2, and Ruff 0.16.3, plus Hatchling 1.32.0;
7. a temporary Python 3.12 candidate lock and environment resolved by uv 0.12.5; and
8. official CPython lifecycle, UUID, and syntax documentation.

The Python development guide currently classifies 3.14 as receiving bug fixes through its normal
lifecycle and 3.12 as receiving security fixes through October 2028. Thus 3.14 has the longer
upstream support horizon, while 3.12 is the older, mature line. See the official
[Python version status](https://devguide.python.org/versions/).

## 4. Python-3.14-only dependency and code analysis

The scan found exactly two material source-level incompatibilities with Python 3.12:

| Location | Current construct | Classification | Python 3.12-compatible equivalent |
|---|---|---|---|
| `src/paim/integrity/ids.py` | `from uuid import uuid7` | `REQUIRED BY IMPLEMENTATION` under the current implementation choice | use a reviewed, locked RFC 9562 UUIDv7 provider while retaining `UUID` values and version-7 validation |
| `src/paim/operational/recovery.py` | `except OSError, sqlite3.DatabaseError:` | `INCIDENTAL CURRENT CONFIGURATION` / syntax choice | `except (OSError, sqlite3.DatabaseError):` |

The standard-library `uuid.uuid7()` function was added in Python 3.14. The standard representation
remains a `uuid.UUID`; the present PAIM identity wrappers reject any UUID whose `version` is not 7.
Official behavior is documented in the
[Python 3.14 UUID documentation](https://docs.python.org/3.14/library/uuid.html#uuid.uuid7).

The unparenthesized multiple-exception form is Python 3.14 syntax from
[PEP 758](https://peps.python.org/pep-0758/). Adding parentheses preserves exactly the same exception
handling behavior and is valid on both 3.12 and 3.14.

Other observed language features are available in Python 3.12:

- PEP 695 `type` aliases;
- `Self`, `Protocol`, union types, generic built-ins, frozen/slotted dataclasses, and `StrEnum`;
- `datetime.UTC`, aware datetime arithmetic, `pathlib`, JSON, hashing, and SQLite APIs used here.

No use was found of another Python-3.13/3.14-only syntax form, typing primitive, standard-library
API, interpreter behavior, packaging feature, or serialization facility. After the two temporary
compatibility edits, Python 3.12 `compileall` succeeded for all source and tests.

The requirement categories are therefore:

| Category | Finding |
|---|---|
| `REQUIRED BY PAIM SEMANTICS` | No Python minor or exact patch. PAIM requires stable opaque identity, immutable history, dual time, deterministic selection, and preserved authoritative outputs; these are runtime-independent contracts. |
| `REQUIRED BY IMPLEMENTATION` | Python 3.12 or newer for the current PEP 695 type-alias syntax; an RFC 9562 UUIDv7 generator; synchronous Python/SQLite behavior already exercised by the suite. |
| `REQUIRED BY DEPENDENCY/TOOLCHAIN` | A supported Python line for SQLAlchemy, Alembic, pytest, mypy, Ruff, Hatchling, and uv. The current versions installed and resolved successfully on 3.12. |
| `REPRODUCIBILITY POLICY CHOICE` | Exact local interpreter patch, exact uv version, committed lock, hashes, and bounded patch-upgrade regression. |
| `INCIDENTAL CURRENT CONFIGURATION` | Exact package requirement `==3.14.6`, Ruff/mypy 3.14 targets, one optional 3.14 syntax form, and use of stdlib rather than a locked UUIDv7 provider. |

## 5. Candidate A — retain exact CPython 3.14.6

**Classification: `SUPPORTED — NOT RECOMMENDED`.**

Candidate A is technically supported by existing automated evidence: PR #70 records 245 passing
tests, focused gates, static checks, migrations, schema checks, and recovery checks on 3.14.6. It
also retains the standard-library UUIDv7 implementation, the current lock, and the longer CPython
support horizon.

It is not technically necessary for PAIM semantics. The only functional benefit used by PAIM is
stdlib UUIDv7, and the only other dependency is optional syntax whose parenthesized equivalent is
semantically identical. Exact `==3.14.6` package metadata also conflates a reproducible tested
toolchain with the entire supported-runtime contract: it rejects later security/bugfix patches until
the repository is changed even when PAIM has no patch-specific dependency.

Operationally, Candidate A currently requires IT to approve/provision the interpreter and its native
extensions on the practitioner workstation. That is a legitimate deployment prerequisite if
explicitly accepted, but it blocks the local v0.1 walkthrough today. A repository-local downloaded
runtime is not made trusted merely by an exact version or lockfile. Exact versioning verifies
identity; Application Control governs provenance and execution permission.

Candidate A would minimize source/config change, but it preserves an avoidable deployment gate for
features that do not materially require 3.14.

## 6. Candidate B — standardize PAIM v0.1 on CPython 3.12

**Classification: `SUPPORTED — RECOMMENDED`.**

Candidate B supports the implemented code after two bounded non-semantic compatibility edits:

1. parenthesize the one multiple-exception clause; and
2. replace stdlib-only UUIDv7 generation with a reviewed and locked RFC 9562 UUIDv7 provider while
   preserving `uuid.UUID`, version-7 validation, UUID text representation, and opaque identity use.

The current technology decision explicitly states that semantic ordering never uses UUID order.
The database stores UUIDs through their existing textual/value contracts, and existing identities
are parsed rather than regenerated. A generator substitution therefore does not migrate or rewrite
stored identities. The migration issue must nevertheless add hard oracles for version 7, RFC variant,
parse/round-trip, uniqueness, and the rule that UUID order is never authoritative.

All current application and development dependency versions have Python 3.12 distributions or
otherwise installed successfully. uv 0.12.5 resolved 19 packages for a temporary
`>=3.12,<3.13` candidate, adding only `uuid6==2025.0.1` for the tested UUIDv7 compatibility path;
`uv lock --check`, `uv sync --locked`, package build, and PAIM import succeeded in the isolated
study copy. Selection of the final UUIDv7 provider remains a bounded implementation-review choice;
the temporary provider is evidence of viability, not an authorization to add it in this issue.

The recommended support posture is:

- package/runtime contract: CPython `>=3.12,<3.13` (one supported minor line);
- reproducible development/release reference: an exact, organization-approved 3.12 patch in
  `.python-version`, initially the accepted patch chosen by the migration issue;
- uv remains exactly pinned and dependencies remain hash-locked;
- each reference-patch update is a bounded dependency change with the complete regression suite;
- support never includes an interpreter or native extension blocked by organizational policy.

This separates compatibility policy from environment reproduction. It allows a security-patched
3.12 release to be evaluated without falsely claiming that PAIM correctness depends on one patch,
while retaining an exact tested reference environment.

## 7. Candidate C — another mature runtime

No Candidate C is introduced. Python 3.12 is sufficient, installed dependency evidence is complete,
and the full regression passes. Python 3.13 would add another unsupported migration choice without
eliminating the UUIDv7 compatibility work or providing a demonstrated PAIM-specific benefit.

## 8. Reproducibility and security/operations analysis

| Consideration | Exact 3.14.6 | Bounded 3.12 line plus exact reference patch |
|---|---|---|
| PAIM semantic fidelity | Preserved | Preserved with hard-oracle UUIDv7 compatibility tests |
| Existing source/config churn | None | Two source compatibility edits plus bounded config/lock/docs changes |
| Dependency evidence | Existing lock and passing suite | Current exact versions installed; candidate lock/sync/import and full suite passed |
| Upstream lifecycle | Longer | Security-supported through October 2028; adequate for bounded v0.1 but requires later runtime review |
| Current practitioner workstation | Blocked by Application Control | CPython 3.12.13 and SQLite executed without that block during this study; formal deployment provenance still must be approved |
| Reproducibility | Exact interpreter, uv, and lock | Exact reference interpreter, uv, and lock; package compatibility expressed at minor-line level |
| Patch security updates | Repository change required before any patch change | Reference patch still changes through a bounded regression issue, without misrepresenting package-level compatibility |
| Native-code exposure | CPython/SQLite plus dependency wheels | Same classes of native components; all remain subject to provenance, signature, hash, and Application Control policy |

Neither candidate should bypass Application Control. A correct operational baseline requires an
approved interpreter distribution and approved native modules. uv lock hashes, runtime provenance,
and organizational allowlisting solve different problems and all remain relevant.

Python 3.12's shorter remaining support horizon is an explicit residual risk. PAIM must conduct a
new runtime decision before 3.12 end of life or before any post-v0.1 release whose maintenance period
would exceed that horizon.

## 9. Regression and compatibility evidence

### 9.1 Unmodified Python 3.12 attempt

On PR #70 checkpoint `2dcf1e4`, Python 3.12 compilation/import identified exactly:

- `SyntaxError` at the unparenthesized multiple-exception clause; and
- `ImportError` for `uuid.uuid7`.

Test collection otherwise reached the expected 245-test population once dependencies were present.
An initial pytest setup error came from an inaccessible stale `pytest-of-gaohe` directory; using a
new isolated `--basetemp` removed that environmental error.

### 9.2 Temporary compatibility candidate

Only the two changes in §6 were applied to the temporary copy. No PAIM specification, schema,
migration, test, fixture, expected output, or governing behavior was edited.

| Check under CPython 3.12.13 | Result |
|---|---|
| SQLite import/version | PASS — SQLite 3.53.1 |
| Exact application/dev dependency installation | PASS |
| Python compilation of all source/tests | PASS |
| Full PR #70 pytest population | PASS — 245 passed in 878.38s |
| Ruff check with `py312` | PASS |
| Ruff format check with `py312` | PASS — 70 files already formatted after formatting the two temporary edits |
| strict mypy with Python 3.12 target | PASS — 43 source files |
| uv 0.12.5 candidate resolution | PASS — 19 packages |
| `uv lock --check` | PASS |
| `uv sync --locked` and package build/install | PASS |
| PAIM import through locked uv environment | PASS |

The 245 tests include migration from empty and supported prior SQLite revisions, schema constraints,
foreign keys, append-only enforcement, transaction/idempotency behavior, exact dual-time history,
deterministic serialization/output, authentication/access, recovery, degraded operation, and the
Increment 9 automated gateways. No migration, SQLite, SQLAlchemy/Alembic, CLI, typing, historical
reconstruction, Value/Risk independence, or authoritative-output difference was observed.

The temporary study was not practitioner validation and does not repair the human-evidence problem
in PR #70.

## 10. Recommended runtime baseline

Standardize PAIM v0.1 on the CPython 3.12 minor line, expressed as `>=3.12,<3.13`, with one exact
organization-approved reference patch, exact uv 0.12.5, and a regenerated committed lock. The
migration issue should select and record the exact 3.12 reference patch available and approved at
that checkpoint.

The recommendation is based on PAIM's own code, governing contracts, current dependencies, full
regression, and local operational evidence. It is not based on another project.

## 11. Required repository changes if accepted

A separate bounded implementation issue and PR must:

1. change `pyproject.toml` `requires-python` to `>=3.12,<3.13`;
2. set Ruff to `py312` and mypy to `3.12`;
3. set `.python-version` to the exact accepted, organization-approved 3.12 reference patch;
4. select, justify, constrain, and lock an RFC 9562 UUIDv7 provider (or a separately reviewed local
   implementation), then retain the existing UUID value/version checks;
5. parenthesize the one multiple-exception clause;
6. regenerate `uv.lock` under the accepted Python 3.12 reference runtime without opportunistic
   unrelated dependency upgrades unless separately justified;
7. update the Increment 1 technology decision and local operator/setup documentation to identify
   this accepted decision as superseding the 3.14 baseline and to state the Application Control /
   approved-runtime prerequisite;
8. add targeted UUIDv7 compatibility and persistence round-trip oracles;
9. run the complete regression, focused Increment gates, migrations from empty and supported prior
   revisions, programmatic schema/constraint/trigger/index/FK checks, recovery/degraded-operation
   checks, Ruff, strict mypy, lock verification, build/install, secret scan, and diff checks; and
10. record the exact runtime distribution/provenance, Python/SQLite/uv/dependency identities, and
    validation commit.

No governing PAIM system specification, database migration, serialized record contract, or
authoritative historical record should change.

## 12. Increment 9 and PR #70 implications

PR #70 remains draft, unmodified, and unmergeable while this decision and any accepted runtime
migration are outstanding. Its automated evidence remains useful evidence for the 3.14 checkpoint,
including the already-corrected F-I9-001, but it does not establish human practitioner walkthroughs.

If this recommendation is accepted:

1. complete and merge the separate runtime migration issue/PR;
2. rebase or reconcile PR #70 onto that accepted clean-main runtime baseline;
3. rerun the complete release regression under the accepted 3.12 environment because runtime,
   SQLite build, dependency artifacts, and UUID generator provenance change materially;
4. discard the stopped I9-P1 attempt as practitioner evidence; and
5. restart guided practitioner validation from I9-P1, then I9-P2 and I9-P3 one at a time.

No current PR #70 claim of completed practitioner observation can be accepted until those human
walkthroughs are actually executed and recorded without inference or embellishment.

## 13. Human decision required

ChatGPT, as PAIM system/platform design authority and release-state owner, must independently accept,
reject, or request changes to this recommendation. Codex must not implement the runtime migration,
resume practitioner validation, mark PR #70 ready, or merge either PR based only on this artifact.

Acceptance should authorize a new bounded migration issue. It should not authorize changes inside
this analysis PR beyond review corrections to this artifact.

## 14. Final recommendation

**STANDARDIZE PAIM V0.1 ON CPYTHON 3.12**
