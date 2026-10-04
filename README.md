# pmcp-conformance

Conformance tests for any P-MCP server implementation (Python, TypeScript,
Rust, or third-party). This is the suite an implementation must pass to
claim protocol compliance with `pmcp-spec` v0.5.

## What it verifies

- **Section 1 — Initialization** (7 tests): the JSON-RPC `initialize`
  handshake, protocol-version echo, capability advertising.
- **Section 2 — Actuations** (8 tests): `actuations/list`,
  `actuations/execute`, batch actuation atomicity, unknown-actuation
  error path.
- **Section 3 — Sensors** (7 tests): `sensors/list`, `sensors/read`,
  response schema, unknown-sensor error path.
- **Section 4 — Leases** (6 tests): acquire/release/re-acquire,
  double-acquire protection, expiry semantics.
- **Section 5 — Metrics + Ping** (7 tests): required fields on
  `pcp/metrics`, `pcp/ping`, and E-Stop engage/disengage semantics.
- **Section 6 — Error codes** (7 tests): P-MCP error range
  (-33999..-33000), JSON-RPC 2.0 standard codes, response
  well-formedness.

Total: **42 tests**.

## Install and run

```bash
pip install -e .
pytest -v
```

## Current scope and limits

The suite ships with a self-contained mock robot server (`conftest.py`)
that speaks the wire correctly. That mock is what the tests round-trip
against by default. The suite therefore verifies that the tests and the
mock agree — it does **not** yet exercise a third-party implementation.

To run against a real implementation:

1. Launch the implementation on `http://127.0.0.1:<PORT>/rpc`.
2. Override the `mock_robot_server` fixture (or provide an env var — see
   `conftest.py`) to point at that base URL instead of the in-process
   mock.
3. Re-run `pytest`.

A pluggable base-URL fixture and a driver contract for external
implementations are follow-up work.
