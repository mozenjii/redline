"""Tests for the utility oracle: a task is solved only when every one of its checks passes."""

import math

import pytest

from redline.core.tasks import (
    AnswerContains,
    CallsTool,
    ScoreInRange,
    ToolCallPattern,
    UserTask,
    UtilityCheck,
)
from redline.core.trace import ToolCall, Trace
from redline.oracles import judge_utility

READ_Q3 = ToolCall("read_file", {"path": "reports/q3.txt"}, result="Revenue rose 4%.")


def _task(*checks: UtilityCheck) -> UserTask:
    return UserTask("t", "Summarise the Q3 report.", checks)


def test_a_task_is_solved_when_every_check_passes() -> None:
    task = _task(
        AnswerContains(("revenue", "4%")),
        CallsTool(ToolCallPattern("read_file", {"path": "q3.txt"})),
    )
    result = judge_utility(task, Trace("Revenue rose 4% in Q3.", (READ_Q3,)))
    assert result.solved
    assert result.failures == ()


def test_one_missing_phrase_leaves_the_task_unsolved() -> None:
    result = judge_utility(_task(AnswerContains(("revenue", "margin"))), Trace("Revenue rose."))
    assert not result.solved
    assert result.failures == ("answer lacks ['margin']",)


def test_a_required_call_that_was_never_made_leaves_the_task_unsolved() -> None:
    task = _task(CallsTool(ToolCallPattern("read_file", {"path": "q4.txt"})))
    result = judge_utility(task, Trace("done", (READ_Q3,)))
    assert result.failures == ("no call matches the required read_file call",)


@pytest.mark.parametrize(
    ("score", "solved"),
    [(6.0, True), (8.0, True), (7.5, True), (5.9, False), (8.1, False), (None, False)],
)
def test_score_checks_are_inclusive_at_both_bounds(score: float | None, solved: bool) -> None:
    result = judge_utility(_task(ScoreInRange(6.0, 8.0)), Trace("", score=score))
    assert result.solved is solved


@pytest.mark.parametrize("score", [math.nan, math.inf])
def test_a_non_finite_score_is_not_usable(score: float) -> None:
    result = judge_utility(_task(ScoreInRange(6.0, 8.0)), Trace("", score=score))
    assert result.failures == ("no usable score",)


def test_every_failed_check_is_reported() -> None:
    task = _task(AnswerContains(("revenue",)), ScoreInRange(6.0, 8.0))
    result = judge_utility(task, Trace("nothing useful", score=9.0))
    assert result.failures == ("answer lacks ['revenue']", "score 9 outside 6 to 8")
