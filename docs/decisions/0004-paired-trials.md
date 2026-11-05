# 0004: Measure usefulness on the same tasks, with and without an attack

**Status:** accepted · **Date:** 2026-11-01

## Context

A defense that blocks attacks by also breaking normal use is not a defense, so every configuration needs a
usefulness number beside its attack success rate. The first plan used a separate set of benign tasks.

## Decision

A trial pairs a **user task** with an **injection task** and an attack variant, following
[AgentDojo](https://github.com/ethz-spylab/agentdojo) (MIT licence). Each user task runs both without and with
the attack, which gives benign utility, utility under attack and attack success rate from one design. The
same trials run under every defense configuration, so comparisons are paired and use McNemar's exact test.
Because variants of one template are correlated, intervals on differences come from a bootstrap that
resamples whole attack families.

## Alternatives

- **A separate benign set.** Measures usefulness on different tasks from the ones attacked, so the two
  numbers don't line up, and it costs extra trials.
- **Inventing a new task format.** No advantage over a published one, and it would make results harder to
  compare with other work. AgentDojo is credited; its code is not copied.
- **Running AgentDojo's own suites directly.** Worth adding later as an external comparison. Its suites
  assume larger models than this project runs locally.

## Consequences

Each user task needs a deterministic utility check as well as each injection task needing a success check.
That is more authoring work up front, and it is what makes the usefulness number trustworthy.

## Revisit when

Results need to be compared directly with published AgentDojo numbers, at which point its suites run as an
additional target.
