#!/usr/bin/env python3
"""news-image-20261117 entry for @kanbara12.

The front page is pre-rendered (entry.png, drawn at build time by
render.py with PIL). This program only copies that image to the
output directory, exactly like the kit starter. Pure standard
library; deterministic: the same bytes on every run.
"""
import os
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / "entry.png", out_dir / "entry.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
