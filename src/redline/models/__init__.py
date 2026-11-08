"""The model layer: the only part of redline allowed to open a network connection.

Owned by the architecture in `docs/design.md`. Every request it makes is checked against an
allowlist first (see `redline.models.egress`), so pointing redline at a host it has no permission
to reach fails in code rather than relying on configuration being right.
"""
