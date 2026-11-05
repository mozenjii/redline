# Security policy

redline is a tool for attacking AI assistants in a controlled setting. This page is about vulnerabilities
in redline itself.

## Reporting a vulnerability

Please report privately through GitHub: the repository's **Security** tab, then **Report a vulnerability**.
Do not open a public issue for a security problem.

I aim to acknowledge a report within a week and to say what I plan to do about it within two. redline is
maintained by one person, so these are intentions rather than guarantees.

## What counts

Please report anything that lets redline do something its design says it cannot:

- reach a network host that is not on the allowlist;
- make a fake tool cause a real effect, such as sending an email or making a request;
- write a secret, an API key or visitor input to logs, recordings or published results;
- once the playground exists, get past its rate limits or input caps, reach the host, or use it as a
  general-purpose model endpoint;
- run code from an attack payload, a recording or an experiment config.

## What doesn't

- **Attack payloads in the corpus.** They are prompt injections on purpose. That a payload hijacks a test
  assistant is the measurement, not a bug.
- **A test assistant falling for an attack.** The test assistants are built to be vulnerable at their lower
  protection levels.
- **A defense that an attack gets past.** Useful, and welcome as an ordinary issue or pull request with the
  attack attached, because that is a result. It is not a vulnerability in redline.

## Supported versions

Until 1.0, only the latest commit on `main` is supported.
