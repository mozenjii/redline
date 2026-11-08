"""The egress allowlist: which hosts the model layer may contact, decided before any socket opens.

Owned by the "Egress" section of `docs/oracles.md`. The check is a pure function of the URL and the
allowlist. It does no DNS lookup and decodes nothing, so a host is allowed only when it is written
exactly as an entry is; every form it does not recognise is refused rather than interpreted.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from urllib.parse import SplitResult, urlsplit

_DEFAULT_PORTS = {"http": 80, "https": 443}
_FORBIDDEN_IN_ENTRY = ("/", "?", "#", "@")


class EgressDeniedError(Exception):
    """A request was refused because its URL is not on the allowlist."""


def _normalize_host(host: str) -> str:
    host = host.lower()
    return host[:-1] if host.endswith(".") else host


def _unsafe(text: str) -> bool:
    return any(char.isspace() or ord(char) < 0x20 or ord(char) == 0x7F for char in text) or (
        "\\" in text
    )


@dataclass(frozen=True, slots=True)
class AllowedHost:
    """One allowlist entry.

    Attributes:
        host: The host name or IP address, lower-cased, without a trailing dot or IPv6 brackets.
        port: The only port allowed, or None for any port.
    """

    host: str
    port: int | None = None

    @classmethod
    def parse(cls, entry: str) -> "AllowedHost":
        """Read an entry such as `localhost:11434`, `[::1]:11434` or `models.example.test`.

        Raises:
            ValueError: If the entry has a scheme, user, path, query or fragment, an invalid port,
                unsafe characters, or no host.
        """
        if "://" in entry or any(mark in entry for mark in _FORBIDDEN_IN_ENTRY) or _unsafe(entry):
            raise ValueError(f"allowlist entry must be a host and optional port: {entry!r}")
        parts = urlsplit(f"//{entry}")
        try:
            port = parts.port
        except ValueError as error:
            raise ValueError(f"allowlist entry has an invalid port: {entry!r}") from error
        if not parts.hostname:
            raise ValueError(f"allowlist entry has no host: {entry!r}")
        return cls(_normalize_host(parts.hostname), port)


@dataclass(frozen=True, slots=True)
class EgressPolicy:
    """The set of hosts the model layer may reach.

    Attributes:
        allowed: The entries. An empty policy refuses everything.
    """

    allowed: tuple[AllowedHost, ...]

    @classmethod
    def from_entries(cls, entries: Iterable[str]) -> "EgressPolicy":
        """Build a policy from entries in the form `AllowedHost.parse` reads.

        Raises:
            ValueError: If any entry is invalid. One bad entry rejects the whole policy.
        """
        return cls(tuple(AllowedHost.parse(entry) for entry in entries))

    def permits(self, url: str) -> bool:
        """Return whether a request to this URL is allowed."""
        parts = _parse(url)
        if parts is None:
            return False
        host = _normalize_host(parts.hostname or "")
        port = _DEFAULT_PORTS[parts.scheme] if parts.port is None else parts.port
        return any(
            entry.host == host and (entry.port is None or entry.port == port)
            for entry in self.allowed
        )

    def check(self, url: str) -> None:
        """Do nothing if the URL is allowed.

        Raises:
            EgressDeniedError: If it is not. The message names the URL, which never holds a secret
                because credentials in a URL are themselves refused.
        """
        if not self.permits(url):
            raise EgressDeniedError(f"egress to {url!r} is not on the allowlist")


def _parse(url: str) -> SplitResult | None:
    """Split a URL, or return None for any form the policy refuses outright."""
    if _unsafe(url):
        return None
    try:
        parts = urlsplit(url)
        _ = parts.port  # Reading the port is what validates it.
    except ValueError:
        return None
    if parts.scheme not in _DEFAULT_PORTS:
        return None
    if parts.username is not None or parts.password is not None or "@" in parts.netloc:
        return None
    if not parts.hostname:
        return None
    return parts
