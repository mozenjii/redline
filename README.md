# redline

A harness that attacks AI assistants with prompt injection, measures how often the attacks work, and keeps score as defenses are added.

> **Scope:** the targets are the deliberately vulnerable test assistants in this repo, and the harness will refuse to run against anything else.
>
> **Status:** early. I'm at the design stage and there is no released code yet. The results table below stays empty until a script in this repo produces the numbers.

## The problem

Assistants that read documents, résumés or web pages can be taken over by instructions hidden in that content. Defenses tend to get announced without before-and-after numbers, and static attack lists go stale as soon as someone tunes against them.

## What it will do

- Ship two test assistants, a document Q&A bot with tools and a résumé screener, with adjustable levels of protection.
- Run a corpus of attacks that vary in goal, delivery (visible text, hidden text, metadata, tool output) and encoding, and score success with deterministic checks such as canary tokens instead of another model's opinion.
- Layer defenses (input cleaning, spotlighting, privilege separation, output and tool-call policy, a classifier) and measure each one's effect and its cost to normal use.
- Search for new attacks adaptively, because a defense that only beats a fixed list hasn't proved much.
- Turn every exploit that worked into a permanent regression test.

## How I plan to know it works

| Measurement | How | Result |
|---|---|---|
| Attack success rate before and after each defense, with intervals | Attack corpus against the test assistants | not measured |
| Cost of each defense to normal tasks | Benign task set | not measured |
| Residual success rate after all defenses | Attacks held out from defense tuning | not measured |
| Exploits turned into regression tests | Count | not measured |

## Design notes

**Oracles from canaries.** Each attack has a goal I can check mechanically: a secret token shows up in the output, a forbidden tool call happens, a score moves, a request reaches a URL I control. That avoids grading attacks with a model that can be fooled by the same tricks.

**Test against an adaptive attacker.** Fixed attack lists flatter defenses. I'll run a budgeted search that mutates attacks (rephrasing, encoding, position, wrappers) against each defense configuration and report both the static and the adaptive numbers.

**Report what's left.** No defense is complete. The write-up reports the residual success rate with intervals and which layers actually contributed, using leave-one-out ablations.

**Defenses cost something.** A filter that blocks every attack and half the legitimate documents isn't a defense. Every configuration is scored on the benign task set too.

## Roadmap

- [ ] Test assistants and attack corpus format
- [ ] Mechanical success checks
- [ ] Layered defenses and their ablations
- [ ] Adaptive attacker
- [ ] Regression suite and write-up

## Related projects

Part of a set of six projects about building LLM systems you can trust:
[evalgate](https://github.com/mozenjii/evalgate),
[policylens](https://github.com/mozenjii/policylens),
[docproof](https://github.com/mozenjii/docproof),
[tollgate](https://github.com/mozenjii/tollgate),
[redline](https://github.com/mozenjii/redline),
[casefile](https://github.com/mozenjii/casefile).

Built by Mohib Ahmad.
