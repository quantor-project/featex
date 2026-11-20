#!/usr/bin/env -S uv run
#
# Reads match<TAB>matchend<TAB>word from stdin and writes a table of
# match<TAB>matchend pairs for concrete or abstract words to stdout.
#
# Words are lowercased and then filtered either based on a wordlist or
# ratings from a pre-trianed linear regression model given the vector
# representation of each word.

from __future__ import annotations

import argparse
import sys
from collections.abc import Generator, Sequence
from pathlib import Path
from typing import IO, Literal

import numpy as np

HERE = Path(__file__).resolve().parent


def score(
    words: set[str], vector_path: Path, model_path: Path
) -> Generator[tuple[str, float]]:
    with model_path.open("rb") as f:
        model = np.load(f)
        coef = model["coef"].ravel()
        intercept = model["intercept"].item()
    todo = words.copy()
    with vector_path.open(encoding="utf-8") as f:
        next(f)  # skip header
        for line in f:
            word, values = line.split(maxsplit=1)
            if word not in todo:
                continue
            todo.discard(word)
            v = np.fromstring(values, sep=" ")
            norm = np.linalg.norm(v)
            if norm != 0:
                yield word, coef @ (v / norm) + intercept
            if len(todo) == 0:
                break


def load_wordlist(path: Path) -> set[str]:
    with path.open(encoding="utf-8") as f:
        return {sys.intern(line.rstrip("\r\n").lower()) for line in f if line.strip()}


def read_table(stream: IO[bytes]) -> Generator[tuple[int, int, str]]:
    for lineno, line in enumerate(stream, start=1):
        text = line.decode("utf-8").rstrip()
        if len(text) == 0:
            continue
        fields = text.split("\t")
        if len(fields) != 3:
            raise ValueError(
                f"<stdin>:{lineno}: expected match<TAB>matchend<TAB>word, found {text}"
            )
        start, end, word = fields
        yield int(start), int(end), sys.intern(word.lower())


def write_table(spans: list[tuple[int, int]], stream: IO[bytes]) -> None:
    stream.write(f"{len(spans)}\n".encode())
    for start, end in spans:
        stream.write(f"{start}\t{end}\n".encode())


def rating_threshold(arg: str) -> float:
    msg = f"{arg!r} is not a valid rating threshold in the range [0.0, 5.0]"
    try:
        rating = float(arg)
    except ValueError as e:
        raise argparse.ArgumentTypeError(msg) from e
    if not 0 <= rating <= 5:
        raise argparse.ArgumentTypeError(msg)
    return rating


def existing_file(arg: str) -> Path:
    path = Path(arg)
    if not path.is_file():
        raise argparse.ArgumentTypeError(f"file {arg!r} does not exist")
    return path


class Ns(argparse.Namespace):
    method: Literal["wordlist", "vectors"]
    wordlist: Path
    vectors: Path
    model: Path
    concrete: float | None
    abstract: float | None


def main(args: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    methods = parser.add_subparsers(dest="method", required=True, metavar="METHOD")
    wordlist_subparser = methods.add_parser(
        "wordlist",
        help="filter words based on a wordlist",
    )
    wordlist_subparser.add_argument(
        "wordlist", type=existing_file, help="path to the wordlist"
    )
    vectors_subparser = methods.add_parser(
        "vectors",
        help="filter words based on word vectors",
    )
    kind = vectors_subparser.add_mutually_exclusive_group(required=True)
    kind.add_argument(
        "--concrete",
        type=rating_threshold,
        metavar="MIN",
        help="concrete rating threshold (above MIN)",
    )
    kind.add_argument(
        "--abstract",
        type=rating_threshold,
        metavar="MAX",
        help="abstract rating threshold (below MAX)",
    )
    vectors_subparser.add_argument(
        "vectors",
        type=existing_file,
        help="path to the word vectors",
    )
    vectors_subparser.add_argument(
        "--model",
        type=existing_file,
        default=HERE / "fasttext_en.npz",
        help="path to the regression model (default: %(default)s)",
    )
    ns = parser.parse_args(args, namespace=Ns())

    try:
        words = list(read_table(sys.stdin.buffer))
    except ValueError as error:
        sys.stderr.write(f"{error}\n")
        return 1
    if len(words) == 0:
        sys.stderr.write("no words on stdin\n")
        return 1

    types = {word[-1] for word in words}
    match ns.method:
        case "wordlist":
            selected = types & load_wordlist(ns.wordlist)
        case "vectors":
            selected = {
                word
                for word, rating in score(types, ns.vectors, ns.model)
                if (ns.concrete is not None and rating > ns.concrete)
                or (ns.abstract is not None and rating < ns.abstract)
            }
    spans = [(start, end) for start, end, key in words if key in selected]
    write_table(spans, sys.stdout.buffer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
