"""Per-trial canaries: unique secrets whose appearance in a channel proves a leak.

Owned by `docs/oracles.md` and decision 0006. A canary is derived from a run seed and a trial key,
so it is fresh for every trial and every run yet rebuilt exactly when a recorded run is replayed.
Drawing the seed is the runner's job; this module never draws randomness itself.
"""

import base64
import hashlib
import re
from dataclasses import dataclass
from typing import Final

PREFIX: Final = "rl-"
"""Marks a canary in a trace. Not part of what identifies it."""

ALPHABET: Final = "abcdefghijklmnopqrstuvwxyz234567"
"""Lower-case RFC 4648 base32, chosen because it has no characters that look alike."""

BODY_LENGTH: Final = 16
"""Characters in a canary's body: 80 bits, so an accidental match is not a realistic event."""

DERIVATION: Final = b"rl-canary-v1"
"""Personalises the hash. Changing it changes every canary and invalidates every recording."""

MIN_SEED_BYTES: Final = 16
MAX_SEED_BYTES: Final = 64
"""BLAKE2b accepts keys up to 64 bytes; below 16 the seed could be guessed."""

_CANARY = re.compile(rf"{re.escape(PREFIX)}[{ALPHABET}]{{{BODY_LENGTH}}}")


@dataclass(frozen=True, slots=True)
class Canary:
    """A trial's secret, in the form `rl-` followed by 16 base32 characters.

    Attributes:
        value: The full canary, prefix included.
    """

    value: str

    def __post_init__(self) -> None:
        """Reject anything that is not a well-formed canary."""
        if not _CANARY.fullmatch(self.value):
            raise ValueError(f"not a canary: {self.value!r}")

    @property
    def body(self) -> str:
        """The 16 characters that identify the canary. A leak is this body appearing."""
        return self.value[len(PREFIX) :]

    def __str__(self) -> str:
        """Return the canary as it is placed in a prompt or document."""
        return self.value


def derive_canary(run_seed: bytes, trial_key: str) -> Canary:
    """Return the canary for one trial of one run.

    The same seed and key always give the same canary; a different seed or key gives an unrelated
    one. Without the seed, one trial's canary says nothing about another's.

    Args:
        run_seed: The run's random seed, 16 to 64 bytes, recorded in the run's manifest.
        trial_key: A string that identifies the trial uniquely within the run.

    Raises:
        ValueError: If the seed is the wrong length or the trial key is empty.
    """
    if not MIN_SEED_BYTES <= len(run_seed) <= MAX_SEED_BYTES:
        raise ValueError(
            f"run seed must be {MIN_SEED_BYTES} to {MAX_SEED_BYTES} bytes, got {len(run_seed)}"
        )
    if not trial_key:
        raise ValueError("trial key must not be empty")
    digest = hashlib.blake2b(
        trial_key.encode(), key=run_seed, person=DERIVATION, digest_size=BODY_LENGTH * 5 // 8
    ).digest()
    body = base64.b32encode(digest).decode("ascii").lower()
    return Canary(PREFIX + body)
