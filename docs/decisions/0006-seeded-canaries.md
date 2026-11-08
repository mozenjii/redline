# 0006: Derive each trial's canary from a run seed

**Status:** accepted · **Date:** 2026-11-08

## Context

[Decision 0002](0002-deterministic-oracles.md) gives every trial a fresh canary, so a model that memorised
one cannot fake a leak and one run's recordings cannot contaminate another's. The canary sits in the
system prompt and in a private document, so it is part of every model request.

[Decision 0005](0005-record-replay-cassettes.md) keys recordings by a hash of the request. A canary drawn at
random on every run would change every request, and replay would never find its recording.

## Decision

A run draws one random seed and records it in its manifest. Each trial's canary is a keyed BLAKE2b hash of
the trial's key under that seed, written as `rl-` and 16 base32 characters (80 bits). Replaying a run
reuses its seed, so it rebuilds the same canaries and hits the same recordings. A new run draws a new seed,
so its canaries are new.

## Alternatives

- **A random canary per trial, stored with the recording.** Works, but replay then depends on reading the
  canary back out of stored data before the request can be rebuilt, which couples the runner to storage.
- **A fixed canary per trial key.** Replays trivially, but it is the same string in every run, which is the
  memorisation and contamination problem 0002 exists to avoid.

## Consequences

The seed is not a secret from the model's point of view, because nothing in a request reveals it, but it
is needed to reproduce a run, so it lives in the manifest next to the config hash and the code commit.
Changing the derivation changes every canary and invalidates every recording, so it is versioned.

## Revisit when

A threat appears in which the attacker can see other trials' canaries. Then 80 bits per trial and a
derivation an attacker cannot reproduce without the seed still hold; the decision would only need to
change if the seed itself could leak.
