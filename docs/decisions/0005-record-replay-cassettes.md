# 0005: Record every model call once and replay it everywhere else

**Status:** accepted · **Date:** 2026-11-01

## Context

The target models run locally on a CPU at a few tokens per second. A full run is hours of compute. Tests,
CI, the regression suite and the results explorer all need model outputs, and none of them can wait hours
or depend on a model being installed.

## Decision

The model layer records each request and response to a cassette keyed by a hash of the request: model
digest, messages, tools and sampling parameters. In replay mode a missing cassette is an error, never a
silent live call. Live mode is used only to produce new measurements.

## Alternatives

- **Mock responses written by hand.** Fast, but they test the code against what I expect a model to say
  rather than what it said.
- **Always call the model.** Honest, and too slow and too machine-dependent for CI.
- **Cache results instead of raw calls.** Loses the ability to re-run the oracles or the statistics over
  the same outputs after the code changes.

## Consequences

Cassettes make every published number reproducible from a clean checkout without a model. They also mean a
recording can go stale when a prompt changes; the request hash catches that, because a changed prompt
misses the cassette and fails loudly in replay mode.

## Revisit when

Cassettes grow too large for the repository, at which point they move to release assets with checksums in
the repository.
