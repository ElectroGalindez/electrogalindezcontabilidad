from __future__ import annotations

import os
import sys
from pathlib import Path


def _ensure_repo_root_on_path() -> Path:
    repo_root = Path(__file__).resolve().parent
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    os.chdir(repo_root)
    return repo_root


def main() -> None:
    _ensure_repo_root_on_path()

    from desktop_app import main as desktop_main

    desktop_main()


if __name__ == "__main__":
    main()
