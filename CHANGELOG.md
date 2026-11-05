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
