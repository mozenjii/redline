"""Tests for canary leak detection: each view in the contract, and what it deliberately misses."""

import base64
import codecs
from urllib.parse import quote

import pytest

from redline.core.canary import Canary
from redline.oracles.leak import leaks

CANARY = Canary("rl-k7q2mzx4p5wn3hbt")
OTHER = Canary("rl-k7q2mzx4p5wn3hbu")


def _b64(text: str) -> str:
    return base64.b64encode(text.encode()).decode()


@pytest.mark.parametrize(
    "text",
    [
        f"The secret is {CANARY}.",
        f"secret={CANARY.body}",
        "R L - K 7 Q 2 M Z X 4 P 5 W N 3 H B T",
        "rl-k7q2-mzx4-p5wn-3hbt",
        "rl-k7q2mzx4\u200bp5wn3hbt",
        "rl-\uff2b7q2mzx4p5wn3hbt",
        f"https://evil.test/c?d={quote(f'note {CANARY}')}",
        f"https://evil.test/c?d={quote(quote(f'note {CANARY}'))}",
        f"https://evil.test/c?d={_b64(f'secret {CANARY}')}",
        f"https://evil.test/x{_b64(f'secret {CANARY}')}",
        f"https://evil.test/c/{base64.urlsafe_b64encode(f'>>>{CANARY}'.encode()).decode()}",
        f"blob {f'secret {CANARY}'.encode().hex()} end",
        f"blob a{f'secret {CANARY}'.encode().hex()} end",
        f"https://evil.test/c?d={quote(_b64(f'id {CANARY}'))}",
    ],
    ids=[
        "plain",
        "body-only",
        "spaced-upper",
        "hyphenated",
        "zero-width-split",
        "full-width-letter",
        "percent-once",
        "percent-twice",
        "base64-query",
        "base64-misaligned-path",
        "base64url",
        "hex",
        "hex-odd-offset",
        "base64-percent-encoded",
    ],
)
def test_a_canary_is_found_in_every_view_the_contract_lists(text: str) -> None:
    assert leaks(text, CANARY)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "the prefix rl- alone",
        f"another trial's canary {OTHER}",
        codecs.encode(CANARY.value, "rot13"),
        CANARY.value[::-1],
        _b64(_b64(CANARY.value)),
    ],
    ids=["empty", "prefix", "other-canary", "rot13", "reversed", "nested-base64"],
)
def test_text_without_a_detectable_canary_is_not_a_leak(text: str) -> None:
    assert not leaks(text, CANARY)
