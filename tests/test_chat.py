"""Tests for the chat types: role rules, the canonical form, and reading replies back safely."""

import json

import pytest

from redline.core.chat import (
    ChatRequest,
    ChatResponse,
    Message,
    Role,
    ToolRequest,
    ToolSpec,
)
from redline.core.trace import thaw_json

READ = ToolSpec("read_file", "Read a document.", {"type": "object", "properties": {}})
REQUEST = ToolRequest("call-1", "read_file", {"path": "q3.txt", "lines": [1, 2]})


def test_only_an_assistant_message_can_request_tools() -> None:
    Message(Role.ASSISTANT, "", (REQUEST,))
    with pytest.raises(ValueError, match="only an assistant"):
        Message(Role.USER, "hi", (REQUEST,))


@pytest.mark.parametrize(
    ("role", "tool_call_id"),
    [(Role.TOOL, None), (Role.USER, "call-1"), (Role.ASSISTANT, "call-1")],
)
def test_tool_call_ids_belong_to_tool_messages_only(role: Role, tool_call_id: str | None) -> None:
    with pytest.raises(ValueError, match="tool_call_id"):
        Message(role, "text", tool_call_id=tool_call_id)


def test_the_canonical_form_is_stable_compact_and_sorted() -> None:
    request = ChatRequest(
        "standin",
        (Message(Role.SYSTEM, "Café rules."), Message(Role.ASSISTANT, "", (REQUEST,))),
        (READ,),
    )
    text = request.canonical()
    assert text == ChatRequest(request.model, request.messages, request.tools).canonical()
    assert " " not in text.replace("Café rules.", "").replace("Read a document.", "")
    assert "Café" in text
    assert list(json.loads(text)) == sorted(json.loads(text))


def test_any_change_to_a_request_changes_its_canonical_form() -> None:
    base = ChatRequest("standin", (Message(Role.USER, "hi"),))
    variants = [
        ChatRequest("other", base.messages),
        ChatRequest("standin", (Message(Role.USER, "hi!"),)),
        ChatRequest("standin", base.messages, (READ,)),
        ChatRequest("standin", base.messages, temperature=0.7),
        ChatRequest("standin", base.messages, seed=1),
    ]
    assert len({base.canonical(), *(variant.canonical() for variant in variants)}) == 6


def test_a_reply_survives_a_round_trip_through_json() -> None:
    reply = ChatResponse("Reading it now.", (REQUEST,))
    assert ChatResponse.from_json(json.loads(json.dumps(reply.to_json()))) == reply


def test_frozen_arguments_thaw_back_to_plain_json() -> None:
    assert thaw_json(REQUEST.arguments) == {"path": "q3.txt", "lines": [1, 2]}


MALFORMED: list[object] = [
    [],
    {"tool_requests": []},
    {"content": 3},
    {"content": "", "tool_requests": {}},
    {"content": "", "tool_requests": ["x"]},
    {"content": "", "tool_requests": [{"id": 1, "name": "x", "arguments": {}}]},
    {"content": "", "tool_requests": [{"id": "1", "name": "x", "arguments": []}]},
]


@pytest.mark.parametrize(
    "data",
    MALFORMED,
    ids=[
        "not-object",
        "no-content",
        "content-not-text",
        "requests-not-list",
        "request-not-object",
        "id-not-text",
        "arguments-not-object",
    ],
)
def test_a_malformed_reply_in_a_recording_is_refused(data: object) -> None:
    with pytest.raises(ValueError, match="must be"):
        ChatResponse.from_json(data)
