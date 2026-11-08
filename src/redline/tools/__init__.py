"""Fake tools for the test assistants: they record what they were asked to do and do nothing else.

Owned by decision 0003. No tool here opens a socket, touches the file system or sends anything.
"Exfiltration" is a recorded `send_email` or `http_get` call, which proves the same thing a captured
packet would without giving the harness a network surface.
"""

from redline.tools.fake import TOOL_SPECS, Toolbox

__all__ = ["TOOL_SPECS", "Toolbox"]
