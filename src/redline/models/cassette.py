"""Record-once, replay-everywhere storage for model calls.

Owned by decision 0005. A cassette maps the hash of a request's canonical JSON to the reply it got.
Recording wraps a live model and stores each new reply; replay answers from the cassette alone and
treats a missing reply as an error, never as a reason to call a model. Tests, CI and the explorer
run on replay, so they need no model and cost nothing.

A cassette is a file in the repository and therefore input: loading it checks the format, every
reply's fields, and that each stored key really is the hash of the request stored beside it, so a
hand-edited or stale entry is refused rather than replayed.
"""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final, cast

from redline.core.chat import ChatRequest, ChatResponse
from redline.core.trace import JsonValue
from redline.models.base import Model

FORMAT: Final = "redline-cassette"
VERSION: Final = 1
_KEY_SALT: Final = f"{FORMAT}-v{VERSION}\n"


class CassetteMissError(LookupError):
    """Replay met a request that was never recorded, so the code or a prompt has changed."""


class CassetteFormatError(ValueError):
    """A cassette file is not in the recording format, or an entry does not match its key."""


def request_key(request: ChatRequest) -> str:
    """Return the SHA-256 key of a request's canonical JSON."""
    return _key_of(request.canonical())


def _key_of(canonical: str) -> str:
    return hashlib.sha256((_KEY_SALT + canonical).encode()).hexdigest()


@dataclass(frozen=True, slots=True)
class _Entry:
    request: Mapping[str, JsonValue]
    response: ChatResponse


@dataclass(slots=True)
class Cassette:
    """An ordered set of recorded calls, in the order they were first made."""

    _entries: dict[str, _Entry] = field(default_factory=dict[str, _Entry])

    def __len__(self) -> int:
        """Return how many calls are recorded."""
        return len(self._entries)

    def get(self, request: ChatRequest) -> ChatResponse | None:
        """Return the recorded reply to a request, or None if it was never recorded."""
        entry = self._entries.get(request_key(request))
        return None if entry is None else entry.response

    def put(self, request: ChatRequest, response: ChatResponse) -> None:
        """Record a reply. Recording the same request twice keeps the first reply."""
        self._entries.setdefault(request_key(request), _Entry(request.to_json(), response))

    def to_json(self) -> dict[str, JsonValue]:
        """Return the file form: a header and the entries in recording order."""
        return {
            "format": FORMAT,
            "version": VERSION,
            "entries": [
                {"key": key, "request": dict(entry.request), "response": entry.response.to_json()}
                for key, entry in self._entries.items()
            ],
        }

    def save(self, path: Path) -> None:
        """Write the cassette, replacing the file in one step so a crash leaves no half-file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        text = json.dumps(self.to_json(), indent=2, ensure_ascii=False) + "\n"
        temporary = path.with_name(path.name + ".tmp")
        temporary.write_text(text, encoding="utf-8")
        temporary.replace(path)

    @classmethod
    def load(cls, path: Path) -> "Cassette":
        """Read a cassette file.

        Raises:
            CassetteFormatError: If the file is not a valid cassette.
        """
        try:
            data: object = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise CassetteFormatError(f"{path} is not JSON: {error}") from error
        return cls.from_json(data, source=str(path))

    @classmethod
    def from_json(cls, data: object, *, source: str = "cassette") -> "Cassette":
        """Read a cassette from its parsed JSON form, checking every entry.

        Raises:
            CassetteFormatError: If the data is not a valid cassette.
        """
        header = _mapping(data, source)
        if header.get("format") != FORMAT or header.get("version") != VERSION:
            raise CassetteFormatError(f"{source} is not a {FORMAT} v{VERSION} file")
        entries = header.get("entries")
        if not isinstance(entries, list):
            raise CassetteFormatError(f"{source} has no entry list")
        cassette = cls()
        for index, raw in enumerate(cast("list[object]", entries)):
            where = f"{source} entry {index}"
            entry = _mapping(raw, where)
            key, request = entry.get("key"), _mapping(entry.get("request"), where)
            canonical = json.dumps(
                request, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
            if not isinstance(key, str) or key != _key_of(canonical):
                raise CassetteFormatError(f"{where}: key does not match its request")
            try:
                response = ChatResponse.from_json(entry.get("response"))
            except ValueError as error:
                raise CassetteFormatError(f"{where}: {error}") from error
            cassette._entries[key] = _Entry(cast("dict[str, JsonValue]", request), response)
        return cassette


def _mapping(data: object, where: str) -> dict[str, object]:
    if not isinstance(data, dict):
        raise CassetteFormatError(f"{where} must be a JSON object")
    return cast("dict[str, object]", data)


@dataclass(frozen=True, slots=True)
class Recorder:
    """A model that answers from the cassette when it can, and records the live model when not.

    Attributes:
        live: The model to call for anything not yet recorded.
        cassette: Where replies are stored.
    """

    live: Model
    cassette: Cassette

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Return the recorded reply, or call the live model once and record its reply."""
        recorded = self.cassette.get(request)
        if recorded is not None:
            return recorded
        response = self.live.chat(request)
        self.cassette.put(request, response)
        return response


@dataclass(frozen=True, slots=True)
class Replayer:
    """A model that answers only from a cassette, and fails rather than improvise.

    Attributes:
        cassette: The recorded calls.
    """

    cassette: Cassette

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Return the recorded reply.

        Raises:
            CassetteMissError: If this exact request was never recorded.
        """
        recorded = self.cassette.get(request)
        if recorded is None:
            raise CassetteMissError(
                f"no recording for a {request.model} request (key {request_key(request)[:12]}); "
                "re-record if a prompt, a tool or the model changed"
            )
        return recorded
