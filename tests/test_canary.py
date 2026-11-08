"""Tests for canary derivation: fresh per trial and per run, identical on replay."""

import pytest

from redline.core.canary import BODY_LENGTH, PREFIX, Canary, derive_canary

SEED = bytes(range(32))


def test_the_same_seed_and_key_give_the_same_canary() -> None:
    assert derive_canary(SEED, "trial-1") == derive_canary(SEED, "trial-1")


def test_every_trial_in_a_run_gets_its_own_canary() -> None:
    canaries = {derive_canary(SEED, f"trial-{index}") for index in range(1000)}
    assert len(canaries) == 1000


def test_a_new_run_seed_changes_the_canary() -> None:
    other_seed = bytes(reversed(SEED))
    assert derive_canary(SEED, "trial-1") != derive_canary(other_seed, "trial-1")


def test_a_derived_canary_is_well_formed() -> None:
    canary = derive_canary(SEED, "trial-1")
    assert canary.value.startswith(PREFIX)
    assert len(canary.body) == BODY_LENGTH
    assert str(canary) == canary.value
    assert canary.value == PREFIX + canary.body


def test_derivation_is_pinned() -> None:
    # Recordings depend on canaries, so a silent change to the derivation would invalidate them all.
    assert derive_canary(SEED, "trial-1").value == "rl-djqsicruedgsypym"


@pytest.mark.parametrize("length", [0, 15, 65])
def test_a_seed_of_the_wrong_length_is_refused(length: int) -> None:
    with pytest.raises(ValueError, match="run seed"):
        derive_canary(b"x" * length, "trial-1")


@pytest.mark.parametrize("length", [16, 64])
def test_seed_lengths_at_the_bounds_are_accepted(length: int) -> None:
    derive_canary(b"x" * length, "trial-1")


def test_an_empty_trial_key_is_refused() -> None:
    with pytest.raises(ValueError, match="trial key"):
        derive_canary(SEED, "")


@pytest.mark.parametrize(
    "value",
    [
        "rl-abcdefghijklmnop",
        "rl-abcdefghijklmn23",
    ],
)
def test_well_formed_canaries_are_accepted(value: str) -> None:
    assert Canary(value).value == value


@pytest.mark.parametrize(
    "value",
    [
        "",
        "abcdefghijklmnop",
        "rl-abcdefghijklmno",
        "rl-abcdefghijklmnopq",
        "rl-ABCDEFGHIJKLMNOP",
        "rl-abcdefghijklmno1",
        "rl-abcdefghijklmno8",
        " rl-abcdefghijklmnop",
        "rl-abcdefghijklmnop\n",
    ],
)
def test_malformed_canaries_are_refused(value: str) -> None:
    with pytest.raises(ValueError, match="not a canary"):
        Canary(value)
