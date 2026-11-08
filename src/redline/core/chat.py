"""The conversation between a test assistant and a model: messages, tool requests and replies.

Owned by the architecture in `docs/design.md`. These types are the model interface's vocabulary, so
a hosted client, the stand-in and the recorder all speak them. Their JSON form is what a recording
stores and what its key is computed from, so it is part of the recording format: changing a field
changes every key.
"""

import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from typing import cast

from redline.core.trace import JsonValue, freeze_object, thaw_json


class Role(Enum):
    """Who wrote a message."""

    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"


@dataclass(frozen=True, slots=True)
class ToolSpec:
    """A tool as it is offered to a model.

    Attributes:
        name: The tool's name.
        description: What the tool does, in the words the model reads.
        parameters: A JSON Schema object describing the arguments.
    """

    name: str
    description: str
    parameters: Mapping[str, JsonValue]

    def __post_init__(self) -> None:
        """Freeze the schema."""
        object.__setattr__(self, "parameters", freeze_object(self.parameters))

    def to_json(self) -> dict[str, JsonValue]:
        """Return the JSON form used in recordings."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": thaw_json(self.parameters),
        }


@dataclass(frozen=True, slots=True)
class ToolRequest:
    """A model asking for a tool to be run.

    Attributes:
        id: Pairs the request with the tool message that answers it.
        name: The tool asked for. It may not exist; the toolbox decides.
        arguments: The arguments the model wrote.
    """

    id: str
    name: str
    arguments: Mapping[str, JsonValue]

    def __post_init__(self) -> None:
        """Freeze the arguments."""
        object.__setattr__(self, "arguments", freeze_object(self.arguments))

    def to_json(self) -> dict[str, JsonValue]:
        """Return the JSON form used in recordings."""
        return {"id": self.id, "name": self.name, "arguments": thaw_json(self.arguments)}


@dataclass(frozen=True, slots=True)
class Message:
    """One message in a conversation.

    Attributes:
        role: Who wrote it.
        content: Its text.
        tool_requests: Tools the assistant asked for. Only an assistant message has these.
        tool_call_id: The request this answers. A tool message must have one; nothing else may.
    """

    role: Role
    content: str
    tool_requests: tuple[ToolRequest, ...] = ()
    tool_call_id: str | None = None

    def __post_init__(self) -> None:
        """Reject a message whose fields contradict its role."""
        if self.tool_requests and self.role is not Role.ASSISTANT:
            raise ValueError("only an assistant message can request tools")
        if (self.tool_call_id is None) == (self.role is Role.TOOL):
            raise ValueError("a tool message needs a tool_call_id, and no other message has one")

    def to_json(self) -> dict[str, JsonValue]:
        """Return the JSON form used in recordings. Empty optional fields are left out."""
        data: dict[str, JsonValue] = {"role": self.role.value, "content": self.content}
        if self.tool_requests:
            data["tool_requests"] = [request.to_json() for request in self.tool_requests]
        if self.tool_call_id is not None:
            data["tool_call_id"] = self.tool_call_id
        return data


@dataclass(frozen=True, slots=True)
class ChatRequest:
    """Everything a model call depends on. Two equal requests must get equal replies on replay.

    Attributes:
        model: Which model, as precisely as the provider allows (a digest beats a tag).
        messages: The conversation so far.
        tools: The tools on offer.
        temperature: Sampling temperature. Zero by default, for repeatability.
        seed: Sampling seed, for providers that honour one.
    """

    model: str
    messages: tuple[Message, ...]
    tools: tuple[ToolSpec, ...] = ()
    temperature: float = 0.0
    seed: int = 0

    def to_json(self) -> dict[str, JsonValue]:
        """Return the JSON form a recording stores and its key is computed from."""
        return {
            "model": self.model,
            "messages": [message.to_json() for message in self.messages],
            "tools": [tool.to_json() for tool in self.tools],
            "temperature": self.temperature,
            "seed": self.seed,
        }

    def canonical(self) -> str:
        """Return the request as canonical JSON: sorted keys, no spaces, non-ASCII kept as is."""
        return json.dumps(self.to_json(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class ChatResponse:
    """A model's reply: text, tool requests, or both.

    Attributes:
        content: The reply's text. Empty when the model only asked for tools.
        tool_requests: Tools the model asked for. None means the reply is a final answer.
    """

    content: str
    tool_requests: tuple[ToolRequest, ...] = ()

    def to_json(self) -> dict[str, JsonValue]:
        """Return the JSON form used in recordings."""
        return {
            "content": self.content,
            "tool_requests": [request.to_json() for request in self.tool_requests],
        }

    @classmethod
    def from_json(cls, data: object) -> "ChatResponse":
        """Read a reply back from a recording, checking every field's type.

        Recordings are files in the repository, so they are input like any other: a malformed one
        is refused rather than trusted.

        Raises:
            ValueError: If the data is not a reply in the recording format.
        """
        reply = _object(data, "reply")
        content = reply.get("content")
        if not isinstance(content, str):
            raise ValueError("reply content must be a string")
        requests = reply.get("tool_requests", [])
        if not isinstance(requests, list):
            raise ValueError("reply tool_requests must be a list")
        return cls(content, tuple(_tool_request(item) for item in cast("list[object]", requests)))


def _object(data: object, what: str) -> dict[str, object]:
    if not isinstance(data, dict):
        raise ValueError(f"{what} must be a JSON object")
    return cast("dict[str, object]", data)


def _tool_request(data: object) -> ToolRequest:
    request = _object(data, "tool request")
    request_id, name, arguments = (
        request.get("id"),
        request.get("name"),
        request.get("arguments"),
    )
    if not (isinstance(request_id, str) and isinstance(name, str)):
        raise ValueError("tool request id and name must be strings")
    return ToolRequest(request_id, name, cast("dict[str, JsonValue]", _object(arguments, "args")))
