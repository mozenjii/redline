# Contributing

Thanks for looking. redline is early, so the most useful contributions right now are issues: an attack
family the [threat model](docs/threat-model.md) misses, a flaw in the measurement method in the
[design](docs/design.md), or a defense worth measuring.

## Ground rules

- **Synthetic data only.** No real person's documents, résumés or personal details, in code, fixtures or
  issues.
- **Test assistants and allowlisted hosts only.** Don't add code that points redline at a system it has no
  permission to attack, and don't use it that way.
- **Hijacking, not harmful content.** Attacks here try to take over an assistant's task, steal a canary,
  misuse a tool or move a score. Jailbreaks aimed at getting a model to produce harmful content are out of
  scope and won't be merged.
- **Security problems in redline itself** go through [SECURITY.md](SECURITY.md), not a public issue.

## Setting up

You need [uv](https://docs.astral.sh/uv/); it installs the pinned Python for you.

```bash
uv sync
uv run --locked python scripts/check.py
```

The second command runs every gate CI runs. A pull request needs it green. Keep `--locked`: without it uv
quietly rewrites a stale lockfile and that gate can't fail.

## Making a change

- Write the failing test first, then the change.
- Every module starts with a docstring saying what it is for and what it deliberately does not do. Every
  public function, class and constant has a docstring.
- Keep the core free of I/O. Anything with an external effect goes behind an interface that has a fake.
- Don't lower a threshold, skip a test, delete an assertion or add a suppression comment to get to green.
  If a rule is wrong for a case, say why in the pull request and change the rule's scope in
  `pyproject.toml`.
- One idea per commit, with a message that says what changed and why.
- A change that would be expensive to reverse gets a short record in [docs/decisions](docs/decisions/).
- User-visible changes get a line in [CHANGELOG.md](CHANGELOG.md) under *Unreleased*.

## Numbers

A result appears in the README or the docs only if a committed script produced it from a committed
configuration, with its interval. Please don't hand-edit a results table.
