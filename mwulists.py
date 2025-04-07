#!/usr/bin/env python3

from __future__ import annotations

import argparse
import re
from collections.abc import Generator, Iterable, Sequence
from pathlib import Path


def _mwus2queries(filepath: Path, mwus: Iterable[str]) -> Generator[str, None, None]:
    for lineno, mwu in enumerate(mwus, start=1):
        try:
            re.compile(mwu)
        except re.error as err:
            raise ValueError(f"{filepath}:{lineno}:{err.colno}") from err

        parts = mwu.split()
        yield " ".join([f'"{part}"%c' for part in parts])


def _mwulist2macrofile(filepath: Path) -> int:
    content = filepath.read_text()
    mwus = list(
        sorted(
            filter(bool, map(str.strip, set(content.splitlines()))),
            key=str.lower,
        ),
    )
    macros = _mwus2queries(filepath, mwus)
    print(f"MACRO mwu_{filepath.stem.lower()}(0)")
    print("(")
    print(*macros, sep=" | ")
    print(")")
    print(";")
    return 0


class Ns(argparse.Namespace):
    input_dir: Path
    pattern: str


# python mwulist.py mwulists > macros/mwus.m
def main(args: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_dir", type=Path)
    parser.add_argument("-p", "--pattern", default="*")
    ns = parser.parse_args(args, namespace=Ns())
    retv = 0
    for filepath in ns.input_dir.rglob(ns.pattern):
        if filepath.is_dir():
            continue
        retv |= _mwulist2macrofile(filepath)
    return retv


if __name__ == "__main__":
    raise SystemExit(main())
