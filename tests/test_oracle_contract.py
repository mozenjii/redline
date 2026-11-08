"""Differential test: the oracles against expected results written independently from the contract.

`tests/fixtures/oracle_cases.json` was authored from `docs/oracles.md` alone, before the oracles
existed, by someone who never read them. A failure here is a disagreement to resolve by cause:
fix the code if it breaks the contract, or fix the contract and then the case if the contract was
unclear. Never edit a case just to make it agree with the code.
"""

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, cast

import pytest

from redline.core.canary import Canary
from redline.core.tasks import (
    AnswerContains,
    CallsTool,
    Direction,
    Exfiltrate,
    HijackOutput,
    InjectionGoal,
    ManipulateDecision,
    MisuseTool,
    ScoreInRange,
    ToolCallPattern,
    UserTask,
    UtilityCheck,
)
from redline.core.trace import JsonValue, ToolCall, Trace
from redline.oracles import judge_attack, judge_utility
from redline.oracles.match import argument_text

Case = Mapping[str, Any]

FIXTURES = Path(__file__).parent / "fixtures" / "oracle_cases.json"
CASES: Mapping[str, list[Case]] = json.loads(FIXTURES.read_text(encoding="utf-8"))


def _number(value: float | str | None) -> float | None:
    """Read a JSON number, or one of the strings "nan", "inf" and "-inf" that JSON cannot hold."""
    return None if value is None else float(value)


def _pattern(raw: Case) -> ToolCallPattern:
    arguments = cast("Mapping[str, JsonValue]", raw.get("arguments", {}))
    return ToolCallPattern(raw["tool"], {key: argument_text(v) for key, v in arguments.items()})


def _trace(raw: Case | None) -> Trace | None:
    if raw is None:
        return None
    calls = tuple(
        ToolCall(call["name"], call.get("arguments", {}), call.get("result"))
        for call in raw.get("tool_calls", [])
    )
    return Trace(raw["output"], calls, _number(raw.get("score")))


def _goal(raw: Case) -> InjectionGoal:
    kind = raw["kind"]
    if kind == "exfiltrate":
        return Exfiltrate()
    if kind == "misuse_tool":
        return MisuseTool(
            frozenset(raw.get("forbidden_tools", [])),
            tuple(_pattern(call) for call in raw.get("attacker_calls", [])),
        )
    if kind == "hijack_output":
        return HijackOutput(tuple(raw["markers"]))
    if kind == "manipulate_decision":
        threshold = _number(raw["threshold"])
        assert threshold is not None
        return ManipulateDecision(Direction(raw["direction"]), threshold)
    raise AssertionError(f"unknown goal kind {kind!r}")


def _check(raw: Case) -> UtilityCheck:
    kind = raw["kind"]
    if kind == "answer_contains":
        return AnswerContains(tuple(raw["all_of"]))
    if kind == "calls_tool":
        return CallsTool(_pattern(raw))
    if kind == "score_in_range":
        low, high = _number(raw["low"]), _number(raw["high"])
        assert low is not None
        assert high is not None
        return ScoreInRange(low, high)
    raise AssertionError(f"unknown check kind {kind!r}")


def _judge_attack_case(case: Case) -> str:
    goal = _goal(case["goal"])
    trace = _trace(case["trace"])
    assert trace is not None
    verdict = judge_attack(
        goal, trace, canary=Canary(case["canary"]), clean_trace=_trace(case["clean_trace"])
    )
    return verdict.outcome.value


def _judge_utility_case(case: Case) -> str:
    task = UserTask("fixture", "fixture", tuple(_check(check) for check in case["checks"]))
    trace = _trace(case["trace"])
    assert trace is not None
    return "solved" if judge_utility(task, trace).solved else "unsolved"


def _outcome(judge: Callable[[Case], str], case: Case) -> str:
    try:
        return judge(case)
    except ValueError:
        return "invalid"


def _ids(section: str) -> list[str]:
    return [case["id"] for case in CASES[section]]


def test_case_ids_are_unique() -> None:
    ids = [case["id"] for cases in CASES.values() for case in cases]
    assert len(ids) == len(set(ids))


@pytest.mark.parametrize("case", CASES["attack_cases"], ids=_ids("attack_cases"))
def test_attack_oracle_agrees_with_the_contract(case: Case) -> None:
    assert _outcome(_judge_attack_case, case) == case["expected"], case["why"]


@pytest.mark.parametrize("case", CASES["utility_cases"], ids=_ids("utility_cases"))
def test_utility_oracle_agrees_with_the_contract(case: Case) -> None:
    assert _outcome(_judge_utility_case, case) == case["expected"], case["why"]
