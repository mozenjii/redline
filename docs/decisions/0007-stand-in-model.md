# 0007: Build the pipeline against a scripted stand-in before attaching a model

**Status:** accepted · **Date:** 2026-11-08

## Context

Every part of a trial except the model can be built and tested without one: the fake tools, the
recordings, the test assistants, the oracles and the command line. The development laptop has no GPU
and little free memory, so a local model is impractical there, and the choice of hosted model is still
open.

## Decision

Until a model is attached, the pipeline runs against a **stand-in**: a short, deterministic program
behind the same interface a model client has. It reads every document it is offered, obeys any line
addressed to the assistant that asks it to email someone, and otherwise answers with the document line
that best matches the question. That makes it a credulous assistant by construction, so a demo run shows
an exfiltration end to end.

The stand-in's replies are written by code, not generated. Its runs are labelled as stand-in runs
everywhere they appear, and they are never reported as measurements: no attack success rate or utility
figure in the README or the results explorer may come from it.

## Alternatives

- **Wait for a model.** Blocks everything that does not need one.
- **Hand-written fixed replies.** Simpler, but a fixed reply cannot contain the trial's canary, which is
  derived per run, so the exfiltration path could not be exercised.
- **A small local model.** Real, but too slow and too heavy for the development machine.

## Consequences

The recording, replay, tool and oracle code is proven on real traces before any model cost is spent.
When a model is attached it plugs in behind the same interface, and the demo is re-recorded against it.

## Revisit when

A model is attached. The stand-in then stays only as a test double.
