# 0001: Python with uv, ruff, pyright and pytest

**Status:** accepted, built · **Date:** 2026-11-04

## Context

Every number redline publishes rests on checks that run unattended, so the toolchain had to exist, and be
proven to fail on bad input, before any product code.

## Decision

- Python 3.11 pinned in `.python-version`; CI also runs 3.13.
- uv for the environment, the lockfile and the build backend.
- ruff for format and lint, with a broad rule set that includes bugbear, bandit and docstrings on every
  public symbol.
- pyright in strict mode over `src`, `tests` and `scripts`.
- pytest with strict configuration; branch coverage with an 80% floor and nothing excluded to reach it.
- pip-audit over the exported lockfile, so the audit covers what is locked rather than what happens to be
  installed.
- One stdlib script, `scripts/check.py`, runs all of it cheapest first, locally and in CI.

## Alternatives

- **TypeScript.** A good fit for the web parts, a poor one for the attack, model and statistics libraries,
  which are Python-first.
- **mypy instead of pyright.** Both are fine. pyright is faster and its strict mode is stricter by default.
- **A task runner (make, nox, poe) instead of a script.** make is awkward on Windows; nox and poe add a
  dependency to do what forty lines of standard library already do.
- **pip and requirements files instead of uv.** No real lockfile for the whole dependency graph, and slower.

## Consequences

Strict types make early work slower and refactors cheaper. Breaking each gate on purpose showed that plain
`uv run` re-locks before a command starts, so a stale lockfile can only be caught with
`uv run --locked`. The documented command and CI both use it.

## Revisit when

The full check takes more than ninety seconds, or a library this project needs drops the pinned Python.
