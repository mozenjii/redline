# Changelog

All notable changes are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Python package with a `redline` command that prints its version.
- One command, `uv run --locked python scripts/check.py`, that runs every quality gate: lockfile, format,
  lint, strict types, tests with an 80% branch-coverage floor, and a vulnerability audit of the locked
  dependencies.
- CI running the same gates on Python 3.11 and 3.13.
- Design, threat model and the first five decision records under `docs/`.
- Apache-2.0 licence, security policy and contributing guide.
- Core types for traces, tasks, attack goals and verdicts, and per-trial canaries derived from a run
  seed so replays rebuild them.
- Deterministic oracles for all four attack goals and for user-task checks, with the contract in
  `docs/oracles.md` and 162 expected results written from that contract alone.
- An egress allowlist that refuses any host not listed, checked before a connection exists.
