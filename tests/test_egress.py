"""Tests for the egress allowlist, including the URL forms parsers disagree about."""

import pytest

from redline.models.egress import AllowedHost, EgressDeniedError, EgressPolicy

OLLAMA = EgressPolicy.from_entries(["localhost:11434"])


@pytest.mark.parametrize(
    "url",
    [
        "http://localhost:11434/api/chat",
        "HTTP://LOCALHOST:11434/api/chat",
        "http://localhost.:11434/",
        "http://localhost:011434/",
    ],
    ids=["plain", "upper-case", "trailing-dot", "leading-zero-port"],
)
def test_the_allowed_host_is_reachable_however_it_is_cased(url: str) -> None:
    assert OLLAMA.permits(url)
    OLLAMA.check(url)


@pytest.mark.parametrize(
    "url",
    [
        "http://evil.test/",
        "http://localhost:11435/",
        "http://localhost/",
        "http://127.0.0.1:11434/",
        "ftp://localhost:11434/",
        "file:///etc/passwd",
        "http://localhost:11434@evil.test/",
        "http://evil.test#@localhost:11434/",
        "http://user:pass@localhost:11434/",
        "http://@localhost:11434/",
        "http://evil.test\\@localhost:11434/",
        "http://local\thost:11434/",
        "http://localhost:11434/\n",
        "http://%6cocalhost:11434/",
        "http://localhost:99999/",
        "http://localhost:port/",
        "localhost:11434",
        "",
    ],
    ids=[
        "other-host",
        "wrong-port",
        "default-port",
        "loopback-ip-is-not-localhost",
        "ftp",
        "file",
        "userinfo-hides-real-host",
        "fragment-trick",
        "credentials",
        "empty-user",
        "backslash",
        "tab-inside-host",
        "trailing-newline",
        "percent-encoded-host",
        "port-out-of-range",
        "port-not-a-number",
        "no-scheme",
        "empty",
    ],
)
def test_everything_else_is_refused(url: str) -> None:
    assert not OLLAMA.permits(url)
    with pytest.raises(EgressDeniedError, match="not on the allowlist"):
        OLLAMA.check(url)


def test_an_entry_without_a_port_allows_any_port_including_the_defaults() -> None:
    policy = EgressPolicy.from_entries(["models.example.test"])
    assert policy.permits("https://models.example.test/v1")
    assert policy.permits("http://models.example.test:8080/v1")


def test_a_port_specific_entry_matches_a_default_port() -> None:
    policy = EgressPolicy.from_entries(["models.example.test:443"])
    assert policy.permits("https://models.example.test/v1")
    assert not policy.permits("http://models.example.test/v1")


def test_ipv6_must_be_written_as_the_entry_is() -> None:
    policy = EgressPolicy.from_entries(["[::1]:11434"])
    assert policy.permits("http://[::1]:11434/")
    assert not policy.permits("http://[0:0:0:0:0:0:0:1]:11434/")


def test_an_empty_policy_refuses_everything() -> None:
    assert not EgressPolicy.from_entries([]).permits("http://localhost:11434/")


def test_entries_are_lower_cased_and_lose_a_trailing_dot() -> None:
    assert AllowedHost.parse("Models.Example.Test.:8080") == AllowedHost(
        "models.example.test", 8080
    )


@pytest.mark.parametrize(
    ("entry", "message"),
    [
        ("http://localhost:11434", "host and optional port"),
        ("localhost:11434/api", "host and optional port"),
        ("user@localhost", "host and optional port"),
        ("localhost?x=1", "host and optional port"),
        ("localhost#x", "host and optional port"),
        ("local host", "host and optional port"),
        ("localhost:99999", "invalid port"),
        ("localhost:port", "invalid port"),
        (":11434", "no host"),
        ("", "no host"),
    ],
)
def test_a_bad_entry_rejects_the_whole_policy(entry: str, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        EgressPolicy.from_entries(["localhost:11434", entry])
