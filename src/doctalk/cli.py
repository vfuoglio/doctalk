"""Command-line interface: ingest, ask, chat, ui."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from .store import Store


def _print_sources(hits, cited) -> None:
    if not hits:
        return
    print("\n\nSources:")
    for i, h in enumerate(hits, 1):
        mark = "*" if i in cited else " "
        print(f" {mark}[{i}] {h.label}")


def _show_passages(store: Store, question: str, k: int) -> None:
    """Retrieval only: print the top passages. No API key or network needed."""
    hits = store.search(question, k=k)
    if not hits:
        print("No documents indexed yet. Run: doctalk ingest <path>")
    for i, h in enumerate(hits, 1):
        snippet = " ".join(h.text.split())
        if len(snippet) > 300:
            snippet = snippet[:300] + "..."
        print(f"[{i}] {h.label}  (distance {h.distance:.3f})\n    {snippet}\n")


def _ask(store: Store, question: str, k: int, no_llm: bool = False) -> None:
    if no_llm:
        _show_passages(store, question, k)
        return
    from .rag import cited_numbers, stream_answer

    hits, tokens = stream_answer(question, store, k=k)
    text = ""
    for t in tokens:
        print(t, end="", flush=True)
        text += t
    _print_sources(hits, cited_numbers(text, len(hits)))


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="doctalk", description=__doc__)
    p.add_argument("--db", default=".chroma", help="vector store directory")
    sub = p.add_subparsers(dest="cmd", required=True)

    ing = sub.add_parser("ingest", help="index a file or folder (.pdf .md .txt)")
    ing.add_argument("path", type=Path)

    ask = sub.add_parser("ask", help="ask one question")
    ask.add_argument("question")
    ask.add_argument("-k", type=int, default=5, help="passages to retrieve")
    ask.add_argument("--no-llm", action="store_true",
                     help="retrieval only: show matching passages, no API key needed")

    chat = sub.add_parser("chat", help="interactive Q&A in the terminal")
    chat.add_argument("-k", type=int, default=5)
    chat.add_argument("--no-llm", action="store_true",
                      help="retrieval only: show matching passages, no API key needed")

    sub.add_parser("ui", help="launch the Streamlit web app")
    sub.add_parser("list", help="list indexed documents")

    a = p.parse_args(argv)

    if a.cmd == "ui":
        app = Path(__file__).with_name("app.py")
        return subprocess.call([sys.executable, "-m", "streamlit", "run", str(app)])

    store = Store(a.db)
    if (
        a.cmd in {"ask", "chat"}
        and not a.no_llm
        and not os.environ.get("ANTHROPIC_API_KEY")
    ):
        print(
            "Set ANTHROPIC_API_KEY to get answers, or add --no-llm to see the "
            "retrieved passages without calling the API."
        )
        return 1
    if a.cmd == "ingest":
        counts = store.ingest(a.path)
        if not counts:
            print("No supported files found.")
            return 1
        for name, n in counts.items():
            print(f"indexed {name}: {n} chunks")
    elif a.cmd == "list":
        for s in store.sources():
            print(s)
    elif a.cmd == "ask":
        _ask(store, a.question, a.k, a.no_llm)
        print()
    elif a.cmd == "chat":
        print("Ask about your documents (Ctrl-D to quit).")
        while True:
            try:
                q = input("\n> ").strip()
            except EOFError:
                print()
                break
            if q:
                _ask(store, q, a.k, a.no_llm)
                print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
