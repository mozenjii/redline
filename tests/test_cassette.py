"""Tests for cassettes: record once, replay exactly, and refuse to improvise or trust a bad file."""

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pytest

from redline.core.chat import ChatRequest, ChatResponse, Message, Role, ToolRequest
from redline.models.cassette import (
    Cassette,
    CassetteFormatError,
    CassetteMissError,
    Recorder,
    Replayer,
    request_key,
)


@dataclass
class CountingModel:
    """A live-model double that counts its calls and echoes the last message."""

    calls: list[ChatRequest] = field(default_factory=list[ChatRequest])

    def chat(self, request: ChatRequest) -> ChatResponse:
        """Record the call and echo the last message, asking for one tool."""
        self.calls.append(request)
        return ChatResponse(
            f"echo: {request.messages[-1].content}",
            (ToolRequest("t1", "read_file", {"path": "q3.txt"}),),
        )


def _request(text: str = "What was Q3 revenue? Café") -> ChatRequest:
    return ChatRequest("model-a", (Message(Role.SYSTEM, "Be brief."), Message(Role.USER, text)))


def test_the_recorder_calls_the_live_model_once_per_distinct_request() -> None:
    live, cassette = CountingModel(), Cassette()
    recorder = Recorder(live, cassette)
    first = recorder.chat(_request())
    again = recorder.chat(_request())
    recorder.chat(_request("Something else"))
    assert first == again
    assert len(live.calls) == 2
    assert len(cassette) == 2


def test_replay_returns_exactly_what_was_recorded_after_a_round_trip_through_a_file(
    tmp_path: Path,
) -> None:
    cassette = Cassette()
    recorded = Recorder(CountingModel(), cassette).chat(_request())
    path = tmp_path / "nested" / "demo.json"
    cassette.save(path)
    assert Replayer(Cassette.load(path)).chat(_request()) == recorded


def test_saving_is_deterministic_and_leaves_no_temporary_file(tmp_path: Path) -> None:
    cassette = Cassette()
    Recorder(CountingModel(), cassette).chat(_request())
    first, second = tmp_path / "a.json", tmp_path / "b.json"
    cassette.save(first)
    Cassette.load(first).save(second)
    assert first.read_bytes() == second.read_bytes()
    assert sorted(p.name for p in tmp_path.iterdir()) == ["a.json", "b.json"]


def test_replay_never_improvises_an_unrecorded_request() -> None:
    cassette = Cassette()
    Recorder(CountingModel(), cassette).chat(_request())
    with pytest.raises(CassetteMissError, match="no recording for a model-a request"):
        Replayer(cassette).chat(_request("A changed prompt"))


def test_the_key_covers_every_field_and_ignores_nothing() -> None:
    base = _request()
    changed = ChatRequest(base.model, base.messages, temperature=0.5)
    assert request_key(base) != request_key(changed)
    assert len(request_key(base)) == 64


def _saved(tmp_path: Path) -> tuple[Path, dict[str, Any]]:
    cassette = Cassette()
    Recorder(CountingModel(), cassette).chat(_request())
    path = tmp_path / "c.json"
    cassette.save(path)
    return path, json.loads(path.read_text(encoding="utf-8"))


def test_an_entry_edited_by_hand_is_refused(tmp_path: Path) -> None:
    path, data = _saved(tmp_path)
    data["entries"][0]["request"]["temperature"] = 0.9
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CassetteFormatError, match="key does not match"):
        Cassette.load(path)


Mutation = Callable[[dict[str, Any]], object]
MALFORMED: list[tuple[Mutation, str]] = [
    (lambda d: d.update(version=2), "is not a redline-cassette v1"),
    (lambda d: d.update(format="other"), "is not a redline-cassette v1"),
    (lambda d: d.update(entries={}), "no entry list"),
    (lambda d: d.update(entries=["x"]), "must be a JSON object"),
    (lambda d: d["entries"][0].update(response={"content": 1}), "content must be a string"),
]


@pytest.mark.parametrize(
    ("mutate", "message"),
    MALFORMED,
    ids=["version", "format", "entries-not-list", "entry-not-object", "bad-response"],
)
def test_a_malformed_cassette_is_refused(tmp_path: Path, mutate: Mutation, message: str) -> None:
    path, data = _saved(tmp_path)
    mutate(data)
    path.write_text(json.dumps(data), encoding="utf-8")
    with pytest.raises(CassetteFormatError, match=message):
        Cassette.load(path)


def test_a_file_that_is_not_json_is_refused(tmp_path: Path) -> None:
    path = tmp_path / "broken.json"
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(CassetteFormatError, match="is not JSON"):
        Cassette.load(path)


def test_a_cassette_that_is_not_an_object_is_refused() -> None:
    with pytest.raises(CassetteFormatError, match="must be a JSON object"):
        Cassette.from_json([])
