# PAIM UI M1A Foundation Dependency and Security Evidence v0.1

**Status:** Issue #94 implementation evidence

**Date:** 2026-08-21

**Scope:** Post-v0.1.0 browser foundation only

## Decision

M1A uses the smallest server-rendered dependency set authorized by the accepted implementation
architecture. The locked environment resolves:

| Purpose | Locked package | License |
|---|---:|---|
| Web application boundary | FastAPI 0.141.1 | MIT |
| ASGI/runtime integration | Starlette 1.6.0 | BSD-3-Clause |
| Server-rendered templates | Jinja2 3.1.6 | BSD-3-Clause |
| Loopback ASGI server | Uvicorn 0.52.4 | BSD-3-Clause |
| Bounded form parsing | python-multipart 0.0.32 | Apache-2.0 |
| TestClient transport (development only) | HTTPX2 2.9.1 | BSD-3-Clause |
| Browser automation (development only) | Playwright 1.62.0 | Apache-2.0 |
| Pytest browser integration (development only) | pytest-playwright 0.8.0 | Apache-2.0 |

All selected packages support CPython 3.12 and their licenses are compatible with PAIM's MIT
license. The locked Playwright release supplies Windows x86-64 Chromium/Chrome-for-Testing support.
No Node.js, npm, frontend build chain, CDN, HTMX, client framework, external session store, or
accessibility package was required for this gate.

## Compatibility and advisory verification

The upstream/PyPI compatibility and license metadata were checked immediately before locking.
FastAPI 0.141.1 resolves with Starlette 1.6.0; the focused TestClient and live Uvicorn/Chromium
tests exercise that exact pair. Starlette 1.6.0 now prefers HTTPX2, so the development dependency
uses HTTPX2 rather than retaining the deprecated HTTPX compatibility path.

The reviewed high-severity
[`python-multipart` unbounded-part-header advisory](https://github.com/advisories/GHSA-pp6c-gr5w-3c5g)
affects versions before 0.0.27. M1A locks 0.0.32. The implementation exposes no upload route and
also applies an 8 KiB request-body boundary plus form field/part limits.

The dependency set is frozen by `uv.lock`; `uv lock --check` is a release gate. Dependency review
does not convert upstream behavior into PAIM semantics. A `pip-audit` scan of the exact locked
environment on 2026-08-21 reported no known dependency vulnerabilities; the unpublished local
`paim` package was the sole expected unaudited package.

## Browser form origin constraint

M1A intentionally sends `Referrer-Policy: no-referrer`. Under the browser Fetch rules, a basic HTML
form POST under that policy serializes `Origin` as `null`; accepting only the literal configured
origin would therefore break the required no-JavaScript path. PAIM accepts a null Origin only when
all of the following are simultaneously true:

- trusted-host middleware has accepted exact `127.0.0.1`;
- browser Fetch Metadata reports `Sec-Fetch-Site: same-origin` and navigation mode; and
- the submitted synchronizer token matches the exact server-side session in constant time.

Cross-origin values, unproven null origins, missing Origin without an exact same-origin Referer,
and invalid CSRF tokens fail closed. Browser and HTTP hard-oracle tests cover both the accepted and
rejected paths.

## Bounded conclusion

The set is compatible with the accepted localhost-only, one-worker, server-rendered M1A
architecture. This evidence authorizes no remote topology and makes no change to the immutable
`v0.1.0` release claim.
