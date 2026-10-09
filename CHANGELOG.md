# Changelog — pmcp-conformance

All notable changes to the P-MCP conformance suite. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

This suite is versioned in lockstep with the protocol version it tests.
A conformance suite for v0.5 must not be published as v0.6 — which is also
why it is not 1.0.0. An earlier revision of this file headed the first
public release `[1.0.0]`; that was the version scheme it was meant to
replace, not the version of the suite, and it contradicted both this
preamble and the `0.5.0` in `pyproject.toml`.

## [0.5.0] — 2026-09-28

First tagged public release: 42 tests across six sections — initialization,
actuations, sensors, leases, metrics/ping, and error codes — written against
protocol v0.5.

### Fixed

- **`pip install -e .` failed outright, so CI could never have run.**
  `pyproject.toml` declared no package configuration, and setuptools'
  automatic flat-layout discovery aborted the build: this project ships
  a test *suite* — `conftest.py` plus seven `test_*.py` files collected
  from the repository root — and there is no importable package for
  discovery to find. Declaring `py-modules = []` states that intent and
  makes the install succeed. Verified: install clean, **42 passed**.
- **Stale `tests.conformance.conftest` imports** in `test_02` through
  `test_06` caused pytest to ERROR at collection. The hyphen-broken
  package `__init__.py` was removed and the imports switched to
  `from conftest import rpc_call`. All 42 tests now collect and pass.

### Added

- `pyproject.toml` dependencies (`pytest`, `pytest-asyncio`, `aiohttp`)
  so the suite is installable and runnable out of the box.
- `SECURITY.md`, documenting why a defect in *this* repository is a
  security defect everywhere else.

### Known limitations (documented, not fixed)

- The suite only round-trips against its own in-process mock robot
  server. It therefore verifies that the tests and the mock agree — it
  does not yet exercise a third-party implementation. Making the base
  URL configurable and defining a driver contract for external
  implementations is the highest-value open work here.
- The per-method JSON-RPC schema registry is still missing from
  `pmcp-spec/schema/`, so response shapes are asserted inline in the
  tests rather than generated from the schema.
