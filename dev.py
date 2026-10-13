"""Run the project.

    uv run dev.py          migrate, then start Django on http://localhost:8000
    uv run dev.py check    confirm your setup works (run this before the interview)
"""

import os
import subprocess
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent / "backend"
HOST = "0.0.0.0" if os.environ.get("CODESPACES") == "true" else "127.0.0.1"


def manage(*args):
    return subprocess.call([sys.executable, "manage.py", *args], cwd=BACKEND)


if __name__ == "__main__":
    if sys.argv[1:] == ["check"]:
        ok = manage("check") == 0 and manage("migrate", "--noinput", "-v", "0") == 0
        print("\nAll set." if ok else "\nSetup problem - send the output above to your interviewer.")
        sys.exit(0 if ok else 1)
    if manage("migrate", "--noinput", "-v", "0") == 0:
        manage("runserver", f"{HOST}:8000")
