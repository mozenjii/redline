"""The outcome of judging a trace: achieved, not achieved, or undetermined, with evidence.

Owned by the "Attack goals" section of `docs/oracles.md`. Undetermined is a third outcome rather
than a quiet "no", because a trace missing what a predicate needs is not evidence that an attack
failed; folding it into either side would bias the attack success rate.
"""

from dataclasses import dataclass
from enum import Enum


class Outcome(Enum):
    """Whether an attacker's goal was reached."""

    ACHIEVED = "achieved"
    NOT_ACHIEVED = "not_achieved"
    UNDETERMINED = "undetermined"


@dataclass(frozen=True, slots=True)
class Verdict:
    """An attack verdict and the reasons for it.

    Attributes:
        outcome: The verdict.
        evidence: Human-readable notes on where the goal was met, or why it could not be judged.
            Shown in reports and the explorer; empty when nothing was found.
    """

    outcome: Outcome
    evidence: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class UtilityResult:
    """Whether the user's task was solved, and which checks failed if not.

    Attributes:
        solved: True when every check passed.
        failures: One note per failed check.
    """

    solved: bool
    failures: tuple[str, ...] = ()
