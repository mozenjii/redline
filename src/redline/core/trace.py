"""The record of what one trial produced: the final answer, the tool calls and an optional score.

Owned by the oracle contract in `docs/oracles.md`. A trace is the only thing an oracle reads, so
it carries exactly what a verdict may depend on and nothing about how it was produced. Tool
arguments are frozen on construction because a verdict over a trace that can still change proves
nothing.
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from types import MappingProxyType
from typing import TypeAlias

JsonValue: TypeAlias = (
    "str | int | float | bool | Sequence[JsonValue] | Mapping[str, JsonValue] | None"
)
"""A JSON value. Once frozen, sequences are tuples and mappings are read-only views."""


def freeze_json(value: JsonValue) -> JsonValue:
    """Return a deep, read-only copy of a JSON value.

    Lists become tuples and dicts become read-only mapping views over a private copy, so the caller
    keeps no handle that could change the frozen value.
    """
    if value is None or isinstance(value, str | bool | int | float):
        return value
    if isinstance(value, Mapping):
        return freeze_object(value)
    return tuple(freeze_json(item) for item in value)


def freeze_object(value: Mapping[str, JsonValue]) -> Mapping[str, JsonValue]:
    """Return a deep, read-only copy of a JSON object."""
    return MappingProxyType({key: freeze_json(item) for key, item in value.items()})


@dataclass(frozen=True, slots=True)
class ToolCall:
    """One tool call the assistant made.

    Attributes:
        name: The tool's name, compared exactly.
        arguments: The arguments the assistant wrote. These are attacker-reachable output.
        result: What the tool returned. This is input to the assistant, never evidence of a leak.
    """

    name: str
    arguments: Mapping[str, JsonValue]
    result: str | None = None

    def __post_init__(self) -> None:
        """Reject a nameless call and freeze the arguments."""
        if not self.name:
            raise ValueError("a tool call needs a name")
        object.__setattr__(self, "arguments", freeze_object(self.arguments))


@dataclass(frozen=True, slots=True)
class Trace:
    """What one trial produced.

    Attributes:
        output: The assistant's final answer.
        tool_calls: Every tool call, in the order the assistant made them.
        score: The number the assistant produced, for tasks that ask for one; otherwise None.
    """

    output: str
    tool_calls: tuple[ToolCall, ...] = ()
    score: float | None = None
