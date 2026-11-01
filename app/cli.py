"""Command line entry points. Later phases fill in each command."""

from __future__ import annotations

import argparse
import sys

COMMANDS = ("scrape", "load", "chunk", "embed", "index", "pipeline", "ask")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Groww mutual fund facts assistant")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        command = sub.add_parser(name)
        if name == "ask":
            command.add_argument("question", nargs="?")
    args = parser.parse_args(argv)
    if args.command == "scrape":
        from app.ingest.scrape import run as scrape

        return scrape()
    if args.command == "load":
        from app.ingest.load import run as load

        return load()
    if args.command == "chunk":
        from app.ingest.chunk import run as chunk

        return chunk()
    if args.command == "embed":
        from app.ingest.embed import run as embed

        return embed()
    if args.command == "index":
        from app.ingest.index import run as index

        return index()
    if args.command == "pipeline":
        from app.ingest.scrape import run as scrape
        from app.ingest.load import run as load
        from app.ingest.chunk import run as chunk
        from app.ingest.embed import run as embed
        from app.ingest.index import run as index

        for step in (scrape, load, chunk, embed, index):
            code = step()
            if code != 0:
                return code
        return 0
    if args.command == "ask":
        from app.ask import ask
        from app.store.layout import IndexNotReady

        if not args.question:
            print("usage: python -m app.cli ask \"question\"", file=sys.stderr)
            return 2
        try:
            result = ask(args.question)
        except IndexNotReady:
            print("Index is not ready.", file=sys.stderr)
            return 1
        except ValueError as exc:
            print(str(exc), file=sys.stderr)
            return 2
        print(result["answer"])
        print(result["trace_path"])
        return 0
    print(f"not implemented: {args.command}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
