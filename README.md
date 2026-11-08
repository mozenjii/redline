# redline

[![ci](https://github.com/mozenjii/redline/actions/workflows/ci.yml/badge.svg)](https://github.com/mozenjii/redline/actions/workflows/ci.yml)

A harness that attacks AI assistants with prompt injection, measures how often the attacks work, and keeps score as defenses are added.

> **Scope:** the targets are the deliberately vulnerable test assistants in this repo, or an endpoint of your own that you explicitly allow. The harness refuses any other host.
>
> **Status:** early. The toolchain, quality gates and the mechanical success checks are in place; no attack has been run against a model yet. The results table below stays empty until a script in this repo produces the numbers.

## The problem

Assistants that read documents, résumés or web pages can be taken over by instructions hidden in that content. Defenses tend to get announced without before-and-after numbers, and static attack lists go stale as soon as someone tunes against them.

## What it will do

- Ship two test assistants, a document Q&A bot with tools and a résumé screener, with adjustable levels of protection, plus an adapter for testing your own assistant.
- Run a corpus of attacks that vary in goal, delivery (visible text, hidden text, metadata, tool output) and encoding, and score success with deterministic checks such as canary tokens instead of another model's opinion.
- Layer defenses (input cleaning, spotlighting, privilege separation, output and tool-call policy, a classifier) and measure each one's effect and its cost to normal use.
- Search for new attacks adaptively, because a defense that only beats a fixed list hasn't proved much.
- Turn every exploit that worked into a permanent regression test.
- Publish every trial, its trace and its verdict in a static results explorer.

## How I plan to know it works

| Measurement | How | Result |
|---|---|---|
| Attack success rate before and after each defense, with intervals | Attack corpus against the test assistants | not measured |
| Cost of each defense to normal tasks | The same tasks run without an attack | not measured |
| Residual success rate after all defenses | Attacks held out from defense tuning | not measured |
| Exploits turned into regression tests | Count | not measured |

## Design notes

**Oracles from canaries.** Each attack has a goal I can check mechanically: a secret token shows up in the output, a forbidden tool call happens, a score moves, a tool is asked to fetch a URL carrying the secret. The tools are fakes that record the attempt, so nothing actually leaves the machine. That avoids grading attacks with a model that can be fooled by the same tricks.

**Test against an adaptive attacker.** Fixed attack lists flatter defenses. I'll run a budgeted search that mutates attacks (rephrasing, encoding, position, wrappers) against each defense configuration and report both the static and the adaptive numbers.

**Report what's left.** No defense is complete. The write-up reports the residual success rate with intervals and which layers actually contributed, using leave-one-out ablations.

**Defenses cost something.** A filter that blocks every attack and half the legitimate documents isn't a defense. Every configuration is also scored on the same tasks with no attack present.

## Roadmap

- [x] Toolchain, quality gates and CI
- [x] Mechanical success checks, with independently written expected results
- [ ] Test assistants and attack corpus format
- [ ] Layered defenses and their ablations
- [ ] Adaptive attacker
- [ ] Regression suite and write-up

## Documentation

- [Design](docs/design.md): what redline produces, how a trial is measured, the architecture and what is built so far
- [Oracles](docs/oracles.md): exactly what counts as a leak, a tool misuse, a hijacked answer or a moved score
- [Threat model](docs/threat-model.md): the attacker redline measures, and the risks of running redline itself
- [Decision records](docs/decisions/): the choices that would be expensive to reverse, and the alternatives they beat
- [Changelog](CHANGELOG.md), [contributing](CONTRIBUTING.md), [security policy](SECURITY.md)

## Development

Needs [uv](https://docs.astral.sh/uv/). It installs the pinned Python for you.

```bash
uv sync
uv run --locked python scripts/check.py
```

That one command runs every gate CI runs, cheapest first: lockfile, format, lint, strict types,
tests with an 80% branch-coverage floor, and a vulnerability audit of the locked dependencies. Keep
`--locked`; without it uv silently rewrites a stale lockfile and that gate can't fail.

## Related projects

Part of a set of six projects about building LLM systems you can trust:
[evalgate](https://github.com/mozenjii/evalgate),
[policylens](https://github.com/mozenjii/policylens),
[docproof](https://github.com/mozenjii/docproof),
[tollgate](https://github.com/mozenjii/tollgate),
[redline](https://github.com/mozenjii/redline),
[casefile](https://github.com/mozenjii/casefile).

Built by Mohib Ahmad. Licensed under [Apache-2.0](LICENSE).
