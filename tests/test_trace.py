"""Tests for the trace types: a judged trace must not be editable afterwards."""

from collections.abc import Mapping
from types import MappingProxyType

import pytest

from redline.core.trace import JsonValue, ToolCall, Trace, freeze_json


def test_tool_call_arguments_do_not_follow_later_edits_to_the_input() -> None:
    recipients: list[JsonValue] = ["alice@example.test"]
    arguments: dict[str, JsonValue] = {"to": recipients, "body": "hi"}
    call = ToolCall("send_email", arguments)

    recipients.append("attacker@evil.test")
    arguments["body"] = "changed"

    assert call.arguments["to"] == ("alice@example.test",)
    assert call.arguments["body"] == "hi"


def test_tool_call_arguments_are_a_read_only_view() -> None:
    call = ToolCall("send_email", {"to": "alice@example.test"})
    assert isinstance(call.arguments, MappingProxyType)


def test_nested_values_are_frozen_all_the_way_down() -> None:
    frozen = freeze_json({"a": [{"b": [1, 2]}]})
    assert isinstance(frozen, Mapping)
    outer = frozen["a"]
    assert isinstance(outer, tuple)
    inner = outer[0]
    assert isinstance(inner, Mapping)
    assert inner["b"] == (1, 2)


@pytest.mark.parametrize("scalar", ["text", 3, 2.5, True, None])
def test_scalars_freeze_to_themselves(scalar: JsonValue) -> None:
    assert freeze_json(scalar) == scalar


def test_a_tool_call_needs_a_name() -> None:
    with pytest.raises(ValueError, match="name"):
        ToolCall("", {})


def test_a_trace_defaults_to_no_calls_and_no_score() -> None:
    trace = Trace("answer")
    assert trace.tool_calls == ()
    assert trace.score is None
