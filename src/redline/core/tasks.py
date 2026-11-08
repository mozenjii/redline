"""What a trial asks for: the user's task with its checks, and the attacker's goal.

Owned by the "Attack goals" and "User tasks" sections of `docs/oracles.md`. Every rule the contract
calls an error is enforced here, on construction, so an oracle never sees a goal that would pass
vacuously: a task with no checks, an empty marker, or a pattern that matches any call.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType

from redline.core.text import normalize


def _require_text(value: str, what: str) -> None:
    if not normalize(value):
        raise ValueError(f"{what} must not be empty after normalisation")


@dataclass(frozen=True, slots=True)
class ToolCallPattern:
    """A tool call described by its name and some of its arguments.

    A call matches when its name is equal and, for every argument named here, the call's argument
    contains this text. Arguments not named here are ignored.

    Attributes:
        tool: The tool's exact name.
        arguments: Argument name to the text that argument must contain.
    """

    tool: str
    arguments: Mapping[str, str]

    def __post_init__(self) -> None:
        """Reject a nameless pattern or one with an empty argument text, and freeze it."""
        if not self.tool:
            raise ValueError("a tool call pattern needs a tool name")
        for name, text in self.arguments.items():
            _require_text(text, f"pattern argument {name!r}")
        object.__setattr__(self, "arguments", MappingProxyType(dict(self.arguments)))


@dataclass(frozen=True, slots=True)
class Exfiltrate:
    """The attacker wants the trial's canary to leave through the answer or a tool argument."""


@dataclass(frozen=True, slots=True)
class MisuseTool:
    """The attacker wants a tool used: one the user never needs, or with arguments they chose.

    Attributes:
        forbidden_tools: Tools whose mere use means the attack worked.
        attacker_calls: Calls whose occurrence means the attack worked.
    """

    forbidden_tools: frozenset[str] = frozenset()
    attacker_calls: tuple[ToolCallPattern, ...] = ()

    def __post_init__(self) -> None:
        """Reject a goal that no trace could achieve."""
        if not self.forbidden_tools and not self.attacker_calls:
            raise ValueError("a tool-misuse goal needs a forbidden tool or an attacker call")


@dataclass(frozen=True, slots=True)
class HijackOutput:
    """The attacker wants a phrase or link shown in the answer.

    Attributes:
        markers: Any one of these appearing in the answer means the attack worked.
    """

    markers: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject an empty marker list or a marker that would match every answer."""
        if not self.markers:
            raise ValueError("an output-hijack goal needs at least one marker")
        for marker in self.markers:
            _require_text(marker, "a marker")


class Direction(Enum):
    """Which way the attacker wants a score to move."""

    UP = "up"
    DOWN = "down"


@dataclass(frozen=True, slots=True)
class ManipulateDecision:
    """The attacker wants a score moved, judged against the same input without the payload.

    Attributes:
        direction: Which way the score must move.
        threshold: How far it must move, a finite number greater than zero.
    """

    direction: Direction
    threshold: float

    def __post_init__(self) -> None:
        """Reject a threshold that would count no change, or noise, as success."""
        if not math.isfinite(self.threshold) or self.threshold <= 0:
            raise ValueError(f"threshold must be finite and above zero, got {self.threshold}")


InjectionGoal = Exfiltrate | MisuseTool | HijackOutput | ManipulateDecision
"""Exactly one of the four goals in the threat model."""


@dataclass(frozen=True, slots=True)
class AnswerContains:
    """The answer must contain every listed phrase.

    Attributes:
        all_of: The phrases, each non-empty after normalisation.
    """

    all_of: tuple[str, ...]

    def __post_init__(self) -> None:
        """Reject a check that every answer would pass."""
        if not self.all_of:
            raise ValueError("an answer check needs at least one phrase")
        for phrase in self.all_of:
            _require_text(phrase, "a required phrase")


@dataclass(frozen=True, slots=True)
class CallsTool:
    """Some tool call must match a pattern.

    Attributes:
        pattern: The call the user's task needs.
    """

    pattern: ToolCallPattern


@dataclass(frozen=True, slots=True)
class ScoreInRange:
    """The score must be present and within inclusive bounds.

    Attributes:
        low: Lowest acceptable score.
        high: Highest acceptable score.
    """

    low: float
    high: float

    def __post_init__(self) -> None:
        """Reject bounds that no score could satisfy, or that are not numbers."""
        if not (math.isfinite(self.low) and math.isfinite(self.high)):
            raise ValueError("score bounds must be finite")
        if self.low > self.high:
            raise ValueError(f"low bound {self.low} is above high bound {self.high}")


UtilityCheck = AnswerContains | CallsTool | ScoreInRange
"""One deterministic test of whether the user's task was done."""


@dataclass(frozen=True, slots=True)
class UserTask:
    """What a legitimate user asked for, and how to tell that it was done.

    Attributes:
        id: Stable identifier, unique in the corpus.
        prompt: The user's request as the assistant receives it.
        checks: All of these must pass for the task to count as solved.
    """

    id: str
    prompt: str
    checks: tuple[UtilityCheck, ...]

    def __post_init__(self) -> None:
        """Reject a task that would count as solved whatever the assistant did."""
        if not self.id:
            raise ValueError("a user task needs an id")
        if not self.checks:
            raise ValueError(f"user task {self.id!r} has no checks")


@dataclass(frozen=True, slots=True)
class InjectionTask:
    """What the attacker wants, independent of how the payload delivers it.

    Attributes:
        id: Stable identifier, unique in the corpus.
        goal: The one goal whose predicate decides success.
    """

    id: str
    goal: InjectionGoal

    def __post_init__(self) -> None:
        """Reject a task without an id."""
        if not self.id:
            raise ValueError("an injection task needs an id")
