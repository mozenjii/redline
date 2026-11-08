"""Test assistants: the systems under attack, each reduced to "run a trial, return a trace".

Owned by the architecture in `docs/design.md`. A target talks to a model only through the `Model`
interface and to tools only through a `Toolbox`, so the same target runs against a hosted model,
a recording or the stand-in, and can never cause a real effect.
"""
