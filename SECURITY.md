# Security policy — pmcp-conformance

The default policy for this organization lives in
[`pmcp-spec/SECURITY.md`](https://github.com/physicalcontextprotocol/pmcp-spec/blob/main/SECURITY.md)
and applies here in full. This file records what is specific to the
conformance suite.

## Reporting

Use **private vulnerability reporting**:
**Security → Report a vulnerability** on this repository, or
[open an org-level advisory](https://github.com/physicalcontextprotocol/security/advisories/new).

Do not open a public issue.

## Why this repository matters for security

The conformance suite is the thing that decides whether an
implementation is allowed to call itself P-MCP-compliant. A defect
*here* is therefore a security-relevant defect everywhere else: a gate
test that passes when it should fail, or an error-code test that
accepts a malformed E-Stop response, would let a non-conforming server
be waved through.

## In scope here

- A test that passes for the wrong reason — for example, an assertion
  that never executes, a fixture that silently swallows an error, or an
  assertion on a hardcoded literal instead of the response.
- A missing case in the E-Stop, Lease, or gate-ordering sections that
  lets a server bypass a gate and still pass.
- An error-code test that accepts a code outside the defined P-MCP
  range (`-33999`..`-33000`).
- Leaked secrets or credentials in this repository.

## Out of scope here

- The in-process mock in `conftest.py` not being production-grade. It
  is a test double, and the README says the suite does not yet exercise
  a third-party implementation.
- Coverage of protocol features the suite does not claim to cover. Open
  an issue.
- Defects in an implementation under test. Report those against that
  implementation's repository.

## Supported

`v0.5` line, best-effort.
