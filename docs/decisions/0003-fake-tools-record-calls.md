# 0003: Tools are fakes that record calls; the harness has no network surface

**Status:** accepted · **Date:** 2026-11-01

## Context

To see whether an attack exfiltrated data, the harness has to observe the attempt: an email sent, a URL
fetched with the secret in it. The first plan used a local HTTP capture server that the test assistant's
`http_get` would actually call.

## Decision

`send_email`, `http_get` and `shortlist` are fakes. They return a plausible response and record the call,
with its arguments, into the trial's trace. `read_file` reads only from the trial's own document sandbox.
The oracles inspect the recorded calls. Nothing in the tools opens a socket; the model layer is the only
module that may, and only to allowlisted hosts.

## Alternatives

- **A local capture server.** It proves the same thing, but it adds a listening port, a process to manage
  and a real network path that a bug could point somewhere else.
- **Real tools in a sandbox.** Closest to reality, and the most ways to cause harm by accident. Not needed
  to answer the question redline asks.

## Consequences

Exfiltration is measured as intent, the call the model tried to make. That is the right measure here:
whether the request would then succeed depends on network controls outside the model, which is not what
redline studies.

## Revisit when

A defense being measured depends on a real network effect, for example an egress proxy. It would then be
tested against a fake proxy first.
