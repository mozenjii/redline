"""Text normalisation shared by every comparison an oracle makes.

Owned by the "Text normalisation" section of `docs/oracles.md`. One function, so that a goal's
validation and the oracle that later applies it agree on what "empty" and "contains" mean.
"""

import unicodedata

_FORMAT_CATEGORY = "Cf"


def normalize(text: str) -> str:
    """Return text in the form every oracle comparison uses.

    NFKC folds full-width and compatibility letters into ordinary ones; format characters such as
    zero-width spaces are dropped so they cannot split a match; case is folded; whitespace runs
    become one space and the ends are trimmed.
    """
    composed = unicodedata.normalize("NFKC", text)
    visible = "".join(char for char in composed if unicodedata.category(char) != _FORMAT_CATEGORY)
    return " ".join(visible.casefold().split())


def contains(haystack: str, needle: str) -> bool:
    """Return whether the needle occurs in the haystack after normalising both."""
    return normalize(needle) in normalize(haystack)
