"""redline: a measurement harness for prompt-injection risk.

The package is a modular monolith. `redline.core` holds pure domain types, and every module with an
external effect sits behind an interface that has a fake, so the measurement logic can be tested
without a model, a network or a clock.
"""

from importlib.metadata import version

__version__: str = version("redline")
"""The installed distribution's version, read from package metadata so it is defined in one place."""
