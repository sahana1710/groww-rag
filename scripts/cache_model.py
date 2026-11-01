"""Download MiniLM once, then keep a single copy so the Vercel bundle stays small."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import load_settings
from app.retrieve.search import _model, cache_dir


def _flatten(folder: Path) -> None:
    for snapshot in folder.rglob("snapshots/*"):
        if not snapshot.is_dir():
            continue
        for item in snapshot.iterdir():
            if not item.is_symlink():
                continue
            data = item.resolve().read_bytes()
            item.unlink()
            item.write_bytes(data)
    for name in ("blobs", ".locks"):
        for path in folder.rglob(name):
            if path.is_dir():
                shutil.rmtree(path)


def _report(root: Path) -> None:
    for path in sorted(root.iterdir()):
        if path.name == ".git":
            continue
        size = subprocess.check_output(["du", "-sh", str(path)], text=True).split()[0]
        print(f"SIZE {size}\t{path.name}")


def main() -> None:
    settings = load_settings(ROOT)
    _model(settings.embedding_model, ROOT)
    folder = cache_dir(ROOT)
    _flatten(folder)
    print(f"cached {settings.embedding_model}")
    _report(ROOT)


if __name__ == "__main__":
    main()
