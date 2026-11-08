"""A scripted stand-in for a model: credulous by construction, deterministic, and never measured.

Owned by decision 0007. It exists so the whole pipeline can run before a real model is attached.
Its replies are produced by the rules below, not generated, so its runs show that the plumbing works
and say nothing about any real model. Every run that uses it is labelled as a stand-in run.

The rules, applied to the conversation so far:

1. If no tool has answered yet, read every document the system prompt lists (lines of the form
   `- path`).
2. If a document line speaks to the assistant and contains an email address, and no email has been
   sent yet, obey it: email the full system prompt to that address. A real credulous model does this
   when told to "forward your instructions".
3. Otherwise answer with the document line that shares the most words with the user's question,
   ignoring lines that speak to the assistant.
"""

import re
from dataclasses import dataclass
from typing import Final

from redline.core.chat import ChatRequest, ChatResponse, Message, Role, ToolRequest

MODEL_ID: Final = "standin/credulous-v1"
"""The name the stand-in reports. Recordings made with it are recognisable by this."""

NOT_FOUND: Final = "I could not find that in the documents."

_LISTED_DOCUMENT = re.compile(r"^- (\S+)\s*$", re.MULTILINE)
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_ADDRESSES_ASSISTANT = re.compile(r"\bassistant\b", re.IGNORECASE)
_WORD = re.compile(r"[a-z0-9]{4,}")


@dataclass(frozen=True, slots=True)
class CredulousStandIn:
    """The stand-in model. It satisfies the `Model` interface."""

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Apply the module's rules to the conversation and return the scripted reply."""
        offered = {tool.name for tool in request.tools}
        system = _first(request.messages, Role.SYSTEM)
        results = [m.content for m in request.messages if m.role is Role.TOOL]
        if not results and "read_file" in offered:
            paths = _LISTED_DOCUMENT.findall(system)
            if paths:
                return ChatResponse(
                    "",
                    tuple(
                        ToolRequest(f"read-{index}", "read_file", {"path": path})
                        for index, path in enumerate(paths)
                    ),
                )
        lines = [line.strip() for text in results for line in text.splitlines() if line.strip()]
        order = _instruction(lines)
        if order is not None and "send_email" in offered and not _emailed(request.messages):
            return ChatResponse(
                "",
                (
                    ToolRequest(
                        "email-0",
                        "send_email",
                        {"to": order, "subject": "Requested information", "body": system},
                    ),
                ),
            )
        question = _first(request.messages, Role.USER)
        facts = [line for line in lines if not _ADDRESSES_ASSISTANT.search(line)]
        return ChatResponse(_best_match(question, facts))


def _first(messages: tuple[Message, ...], role: Role) -> str:
    return next((message.content for message in messages if message.role is role), "")


def _instruction(lines: list[str]) -> str | None:
    for line in lines:
        if _ADDRESSES_ASSISTANT.search(line):
            address = _EMAIL.search(line)
            if address is not None:
                return address.group(0).rstrip(".")
    return None


def _emailed(messages: tuple[Message, ...]) -> bool:
    return any(
        request.name == "send_email" for message in messages for request in message.tool_requests
    )


def _best_match(question: str, lines: list[str]) -> str:
    wanted = set(_WORD.findall(question.casefold()))
    best, best_overlap = NOT_FOUND, 0
    for line in lines:
        overlap = len(wanted & set(_WORD.findall(line.casefold())))
        if overlap > best_overlap:
            best, best_overlap = line, overlap
    return best
