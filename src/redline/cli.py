"""Command-line entry point for redline.

Parsing only: each subcommand hands off to a library function, so everything the CLI can do is also
reachable from Python and testable without spawning a process.
"""

import argparse
from collections.abc import Sequence

from redline import __version__


def build_parser() -> argparse.ArgumentParser:
    """Return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="redline",
        description="Measure how often prompt injection hijacks an AI assistant.",
    )
    parser.add_argument("--version", action="version", version=f"redline {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code.

    With no subcommand it prints usage and exits 0; there is nothing to run yet, and an empty
    invocation is a request for help rather than an error.
    """
    parser = build_parser()
    parser.parse_args(argv)
    parser.print_help()
    return 0
