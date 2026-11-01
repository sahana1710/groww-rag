"""Download the MiniLM files into the project so a Vercel build can ship them."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import load_settings
from app.retrieve.search import _model


def main() -> None:
    settings = load_settings(ROOT)
    _model(settings.embedding_model, ROOT)
    print(f"cached {settings.embedding_model}")


if __name__ == "__main__":
    main()
