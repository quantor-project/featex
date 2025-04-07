#!/usr/bin/env python3

from __future__ import annotations

import argparse
import subprocess
import sys
from collections import defaultdict
from collections.abc import Iterator, Sequence

_EMPTY = ""
_EOL = "-::-EOL-::-\n"
_CQP_MIN_VERSION = 3.004060

FeatureMatrix = dict[str, dict[str, int]]


class FeatexError(Exception): ...


def _build_feature_matrix(stdout: Iterator[str]) -> FeatureMatrix:
    feature_matrix: FeatureMatrix = defaultdict(lambda: defaultdict(int))
    line = next(stdout, None)
    assert line is not None
    ftype, feature = line.removeprefix("=====").split()
    assert ftype == "TOKENS" and feature == "Corpus"
    n_tokens = 0
    sattrs = set[str]()
    while (line := next(stdout)) != _EOL:
        start, end, sattr = line.strip().split("\t")
        n_tokens += int(end) - int(start) + 1
        sattrs.add(sattr)
    sys.stderr.write(f"{len(sattrs)} texts, {n_tokens / 1e6:.1f}M tokens\n")
    while (line := next(stdout, None)) is not None:
        ftype, feature = line.removeprefix("=====").split()
        if feature in feature_matrix:
            msg = f"Duplicate entry for feature {feature!r}"
            raise FeatexError(msg)
        if ftype == "TOKENS":
            while (line := next(stdout)) != _EOL:
                _start, _end, sattr = line.strip().split("\t")
                if sattr not in sattrs:
                    msg = f"Unknown s-attribute {sattr!r}"
                    raise FeatexError(msg)
                feature_matrix[feature][sattr] += 1
        elif ftype == "COUNTS":
            while (line := next(stdout)) != _EOL:
                sattr, count = line.strip().split("\t")
                if sattr not in sattrs:
                    msg = f"Unknown s-attribute {sattr!r}"
                    raise FeatexError(msg)
                if sattr in feature_matrix[feature]:
                    msg = f"Duplicate entry for s-attribute {sattr!r}"
                    raise FeatexError(msg)
                feature_matrix[feature][sattr] = int(count)
        n = sum(feature_matrix[feature].values())
        sys.stderr.write(f" - feature ({ftype[0]}): {feature} ... ")
        sys.stderr.write(f"{n} hits\n")
    return feature_matrix


def _write_feature_matrix(feature_matrix: FeatureMatrix) -> int:
    sys.stdout.write("ID")
    for feature in feature_matrix.keys():
        sys.stdout.write(f"\t{feature}")
    sys.stdout.write("\n")
    sattrs = {sattr for feature in feature_matrix.values() for sattr in feature.keys()}
    for sattr in sattrs:
        sys.stdout.write(sattr)
        for feature in feature_matrix.keys():
            sys.stdout.write(f"\t{feature_matrix[feature][sattr]}")
        sys.stdout.write("\n")
    return 0


def _parse_cqp_version(line: str) -> float:
    parts = line.split("CQP version")
    assert len(parts) == 2
    version = parts[1].strip()
    major, minor, patch = version.split(".")
    return int(major) + int(minor) / 1e3 + int(patch) / 1e6


def _run_cqp(script: str, corpus: str) -> Iterator[str]:
    proc = subprocess.Popen(
        args=["cqp", "-c", "-n", script, "-D", corpus],
        stdout=subprocess.PIPE,
        stderr=sys.stderr,
        encoding="utf8",
    )
    assert proc.stdout is not None
    stdout = iter(proc.stdout.readline, _EMPTY)
    version = _parse_cqp_version(next(stdout))
    if version < _CQP_MIN_VERSION:
        msg = f"CQP version {version!r} is too old (<{_CQP_MIN_VERSION})."
        raise FeatexError(msg)
    yield from stdout


def featex(script: str, corpus: str) -> int:
    stdout = _run_cqp(script, corpus)
    feature_matrix = _build_feature_matrix(stdout)
    return _write_feature_matrix(feature_matrix)


class Ns(argparse.Namespace):
    script: str
    corpus: str


# python featex.py -D <corpus> featex.cqp > table.tsv
def main(args: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script")
    parser.add_argument("-D", dest="corpus")
    ns = parser.parse_args(args, namespace=Ns())
    return featex(ns.script, ns.corpus)


if __name__ == "__main__":
    raise SystemExit(main())
