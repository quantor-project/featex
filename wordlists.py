#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from pathlib import Path


def _fix_wordlist(filepath: Path) -> int:
    content = filepath.read_text()
    entries = list(
        sorted(
            filter(bool, map(str.strip, set(content.splitlines()))),
            key=str.lower,
        ),
    )
    for lineno, entry in enumerate(entries, start=1):
        if entry.startswith("#"):
            continue
        ws_colnos = [i for i, c in enumerate(entry) if c.isspace()]
        for ws_colno in ws_colnos:
            print(
                f"{filepath}:{lineno}:{ws_colno}: whitespace in entry",
                file=sys.stderr,
            )
        if len(ws_colnos) > 0:
            return 1
        try:
            re.compile(entry)
        except re.error as err:
            print(
                f"{filepath}:{lineno}:{err.colno}: {err}",
                file=sys.stderr,
            )
            return 1

    filepath.write_text("\n".join(entries) + "\n")
    return 0


class Ns(argparse.Namespace):
    input_dir: Path
    pattern: str


# python wordlist.py wordlists
def main(args: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("-p", "--pattern", default="*")
    parser.add_argument("--exit-zero", action="store_true")
    ns = parser.parse_args(args, namespace=Ns())
    retv = 0
    for filepath in ns.input_dir.rglob(ns.pattern):
        if filepath.is_dir():
            continue
        retv |= _fix_wordlist(filepath)
    return retv


if __name__ == "__main__":
    raise SystemExit(main())
