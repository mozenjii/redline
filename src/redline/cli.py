"""Command-line entry point for redline.

Parsing only: each subcommand hands off to a library function, so everything the CLI can do is also
reachable from Python and testable without spawning a process.
"""

import argparse
from collections.abc import Sequence

from redline import __version__

STAND_IN_NOTICE = (
    "Note: the model is a scripted stand-in (decision 0007), not a real model. This run shows the\n"
    "pipeline working end to end; it is not a measurement of any model."
)


def build_parser() -> argparse.ArgumentParser:
    """Return the top-level argument parser."""
    parser = argparse.ArgumentParser(
        prog="redline",
        description="Measure how often prompt injection hijacks an AI assistant.",
    )
    parser.add_argument("--version", action="version", version=f"redline {__version__}")
    commands = parser.add_subparsers(dest="command")
    demo = commands.add_parser(
        "demo", help="run one exfiltration attack on DocQA, replayed from a recording"
    )
    demo.add_argument(
        "--live",
        action="store_true",
        help="run the stand-in model directly instead of replaying the recording",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return a process exit code.

    With no subcommand it prints usage and exits 0: an empty invocation is a request for help
    rather than an error.
    """
    parser = build_parser()
    arguments = parser.parse_args(argv)
    if arguments.command == "demo":
        return _demo(live=arguments.live)
    parser.print_help()
    return 0


def _demo(*, live: bool) -> int:
    from redline.demo import RECORDING, format_report, run_demo
    from redline.models.base import Model
    from redline.models.cassette import Cassette, Replayer
    from redline.models.standin import MODEL_ID, CredulousStandIn

    model: Model = CredulousStandIn() if live else Replayer(Cassette.load(RECORDING))
    source = f"{MODEL_ID}, {'live' if live else 'replayed from the committed recording'}"
    print(format_report(run_demo(model, MODEL_ID), source=source))
    print()
    print(STAND_IN_NOTICE)
    return 0
