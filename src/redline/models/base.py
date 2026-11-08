"""The model interface: one method, a request in and a reply out.

Owned by the architecture in `docs/design.md`. A hosted client, the stand-in and the recorder all
satisfy it, so a test assistant never knows which one it is talking to, and attaching a real model
changes nothing above this line.
"""

from typing import Protocol

from redline.core.chat import ChatRequest, ChatResponse


class Model(Protocol):
    """Anything that answers a chat request."""

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Return the reply to one request."""
        ...
