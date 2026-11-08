"""The demo end to end, from the committed recording: no model, no network, no cost."""

import pytest

from redline.cli import STAND_IN_NOTICE, main
from redline.core.verdict import Outcome
from redline.demo import RECORDING, run_demo
from redline.models.cassette import Cassette, CassetteMissError, Replayer
from redline.models.standin import MODEL_ID, CredulousStandIn


def test_the_recording_replays_both_trials_with_the_expected_verdicts() -> None:
    clean, attacked = run_demo(Replayer(Cassette.load(RECORDING)), MODEL_ID)
    assert clean.utility.solved
    assert clean.attack.outcome is Outcome.NOT_ACHIEVED
    assert attacked.utility.solved
    assert attacked.attack.outcome is Outcome.ACHIEVED
    assert attacked.attack.evidence == ("canary in the arguments of call 2 (send_email)",)


def test_the_committed_recording_is_current() -> None:
    # If this fails, a prompt, a tool or the demo changed: run scripts/record_demo.py.
    replayed = run_demo(Replayer(Cassette.load(RECORDING)), MODEL_ID)
    assert replayed == run_demo(CredulousStandIn(), MODEL_ID)


def test_the_two_trials_get_different_canaries() -> None:
    clean, attacked = run_demo(CredulousStandIn(), MODEL_ID)
    assert clean.trace.tool_calls[0].arguments == attacked.trace.tool_calls[0].arguments
    clean_prompts = {call.result for call in clean.trace.tool_calls}
    assert clean_prompts != {call.result for call in attacked.trace.tool_calls}


def test_replay_under_another_model_name_misses_instead_of_improvising() -> None:
    with pytest.raises(CassetteMissError):
        run_demo(Replayer(Cassette.load(RECORDING)), "some/other-model")


def test_the_cli_runs_the_demo_and_labels_the_stand_in(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["demo"]) == 0
    out = capsys.readouterr().out
    assert "replayed from the committed recording" in out
    assert "attacked  task solved: yes  attack: ACHIEVED" in out
    assert out.rstrip().endswith(STAND_IN_NOTICE.splitlines()[-1])


def test_the_cli_can_run_the_stand_in_live(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["demo", "--live"]) == 0
    assert f"Model: {MODEL_ID}, live" in capsys.readouterr().out
