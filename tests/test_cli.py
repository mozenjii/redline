"""Tests for the command-line entry point, driven through `main` rather than a subprocess."""

import pytest

from redline import __version__
from redline.cli import main


def test_version_flag_prints_the_package_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--version"])
    assert exit_info.value.code == 0
    assert capsys.readouterr().out.strip() == f"redline {__version__}"


def test_no_arguments_prints_usage_and_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert capsys.readouterr().out.startswith("usage: redline")


def test_unknown_option_is_rejected() -> None:
    with pytest.raises(SystemExit) as exit_info:
        main(["--no-such-option"])
    assert exit_info.value.code == 2
