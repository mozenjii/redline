"""Pure domain types: what a trial is, what it produced, and what a verdict says.

Everything else in redline depends on this package and it depends on nothing else in redline.
No function here performs I/O, reads a clock or draws randomness, so every value is reproducible
from its inputs. Values are immutable: a trace that has been judged cannot be edited afterwards.
"""
