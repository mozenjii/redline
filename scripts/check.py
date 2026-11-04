"""Run the local quality gates in order, cheapest first, stopping at the first failure.

CI runs this same script, so a green run here and a green run in CI mean the same thing. Run it as

    uv run --locked python scripts/check.py

`--locked` matters: plain `uv run` quietly rewrites uv.lock to match pyproject.toml before this script
starts, so a stale lockfile would never be caught. Pass gate names to run a subset, for example
`uv run --locked python scripts/check.py lint types`.
"""

import subprocess
import sys
import tempfile
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import NamedTuple

PYTHON = sys.executable


def _run(*command: str) -> int:
    """Run one command with its output streamed to the terminal and return its exit code."""
    return subprocess.run(command, check=False).returncode


def _audit() -> int:
    """Audit exactly the locked dependency set, not whatever happens to be installed locally."""
    with tempfile.TemporaryDirectory() as tmp:
        requirements = Path(tmp) / "requirements.txt"
        exported = _run(
            "uv",
            "export",
            "--frozen",
            "--no-emit-project",
            "--all-groups",
            "--format",
            "requirements-txt",
            "--quiet",
            "--output-file",
            str(requirements),
        )
        if exported != 0:
            return exported
        return _run(
            PYTHON,
            "-m",
            "pip_audit",
            "--requirement",
            str(requirements),
            "--disable-pip",
            "--no-deps",
            "--strict",
            "--progress-spinner",
            "off",
        )


class Gate(NamedTuple):
    """One quality gate: the name it is selected by, why it exists, and how to run it."""

    name: str
    why: str
    run: Callable[[], int]


GATES: tuple[Gate, ...] = (
    Gate("lock", "the lockfile matches pyproject.toml", lambda: _run("uv", "lock", "--check")),
    Gate(
        "format",
        "one formatting, so a diff shows only real changes",
        lambda: _run(PYTHON, "-m", "ruff", "format", "--check", "."),
    ),
    Gate(
        "lint",
        "likely bugs, security smells, missing docstrings",
        lambda: _run(PYTHON, "-m", "ruff", "check", "."),
    ),
    Gate(
        "types",
        "strict static types over src, tests and scripts",
        lambda: _run(PYTHON, "-m", "pyright"),
    ),
    Gate(
        "tests",
        "tests pass and branch coverage stays at or above the floor",
        lambda: _run(PYTHON, "-m", "pytest", "--cov"),
    ),
    Gate("audit", "no known vulnerability in any locked dependency", _audit),
)
"""Every gate, in the order they run. Cheap and fast first, network-bound last."""


def main(argv: Sequence[str]) -> int:
    """Run the named gates, or all of them, and return 0 only if every one passed."""
    names = [gate.name for gate in GATES]
    unknown = [name for name in argv if name not in names]
    if unknown:
        print(
            f"unknown gate: {', '.join(unknown)} (choose from {', '.join(names)})", file=sys.stderr
        )
        return 2
    selected = [gate for gate in GATES if not argv or gate.name in argv]
    for gate in selected:
        print(f"\n== {gate.name}: {gate.why}", flush=True)
        started = time.perf_counter()
        code = gate.run()
        elapsed = time.perf_counter() - started
        if code != 0:
            print(f"== FAILED {gate.name} (exit {code}, {elapsed:.1f}s)", file=sys.stderr)
            return 1
        print(f"== passed {gate.name} ({elapsed:.1f}s)", flush=True)
    print(f"\nall {len(selected)} gates passed")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
