"""Deterministic judges over a trace: did the attack work, and was the user's task still done.

Owned by `docs/oracles.md` and decision 0002. No judge model, no I/O, no randomness: the same trace
always gets the same verdict. Every rule here has an independently written expected result in
`tests/fixtures/oracle_cases.json`.
"""

from redline.oracles.attack import judge_attack
from redline.oracles.utility import judge_utility

__all__ = ["judge_attack", "judge_utility"]
