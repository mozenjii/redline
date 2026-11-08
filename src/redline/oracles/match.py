"""Turning tool arguments into text, and matching a tool call against a pattern.

Owned by the "Text normalisation" and "Misuse a tool" sections of `docs/oracles.md`. Shared by the
attack and utility oracles so that "this call matches" means the same thing to both.
"""

from collections.abc import Mapping

from redline.core.tasks import ToolCallPattern
from redline.core.text import contains
from redline.core.trace import JsonValue, ToolCall


def argument_text(value: JsonValue) -> str:
    """Return every string, number and key inside a JSON value, joined by single spaces.

    Booleans and nulls contribute nothing: they cannot carry a canary or a chosen recipient.
    """
    return " ".join(_text_parts(value))


def _text_parts(value: JsonValue) -> list[str]:
    if value is None or isinstance(value, bool):
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, int | float):
        return [str(value)]
    if isinstance(value, Mapping):
        parts: list[str] = []
        for key, item in value.items():
            parts.append(key)
            parts.extend(_text_parts(item))
        return parts
    return [part for item in value for part in _text_parts(item)]


def matches(call: ToolCall, pattern: ToolCallPattern) -> bool:
    """Return whether a tool call matches a pattern.

    The names must be equal exactly. Every argument the pattern names must be present in the call
    and contain the pattern's text; arguments the pattern does not name are ignored.
    """
    if call.name != pattern.tool:
        return False
    for name, needle in pattern.arguments.items():
        if name not in call.arguments:
            return False
        if not contains(argument_text(call.arguments[name]), needle):
            return False
    return True
