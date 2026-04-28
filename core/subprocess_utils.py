from __future__ import annotations

import subprocess
import sys


def creationflags_no_window() -> int:
    """CREATE_NO_WINDOW для subprocess на Windows, иначе 0."""
    if sys.platform == "win32" and hasattr(subprocess, "CREATE_NO_WINDOW"):
        return subprocess.CREATE_NO_WINDOW
    return 0

