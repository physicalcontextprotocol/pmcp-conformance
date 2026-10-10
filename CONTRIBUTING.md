# Contributing to pcp-conformance

The conformance suite: 42 tests that an implementation must pass to call
itself PCP-compliant.

The organization-wide contributor policy lives in
[`physicalcontextprotocol/.github`](https://github.com/physicalcontextprotocol/.github/blob/main/CONTRIBUTING.md).
This file covers what is specific to this repository.

## Running the checks

```bash
python -m pip install -e .
pytest -v
```

All 42 tests must pass. They run against a self-contained mock robot
server in `conftest.py`, so no SDK and no network are needed.

## Writing a test

The suite is organised by protocol section, one file per section:
`test_01_initialization.py` through `test_06_error_codes.py`. Keep new
tests in the file for their section.

Three rules that matter more than they look:

1. **A test that passes for the wrong reason is worse than a missing
   test.** This suite is what decides whether an implementation is
   allowed to claim compliance, so a test whose assertion never
   actually executes gives false assurance to everyone downstream. If
   you write a test, check that it fails when you break the thing it
   claims to check.
2. **Assert on the response, not on a literal.** Assert that
   `response["result"]["leaseState"] == "ACTIVE"`, not that your own
   fixture constant equals itself.
3. **Never let a fixture swallow an error.** The mock is a test
   double; if it starts returning something unexpected, the test should
   fail loudly.

These three are exactly the class of defect that was found by executing
code rather than reading it elsewhere in this project.

## Testing a real implementation

The suite currently only round-trips against its own in-process mock,
so it verifies that the tests and the mock agree — not that a
third-party implementation is compliant. That limitation is stated in
the README.

Closing it is the highest-value contribution here. The shape of the
work: make the `mock_robot_server` fixture accept a base URL from an
environment variable, and document a driver contract for external
implementations.

## Releasing

Bump `version` in `pyproject.toml` and add a `CHANGELOG.md` entry in
the same PR. This suite is versioned in lockstep with the protocol
version it tests — a conformance suite for v0.5 must not be published
as v0.6.
