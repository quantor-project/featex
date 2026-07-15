#!/usr/bin/env -S uv run

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import threading
from collections import defaultdict
from collections.abc import Generator, Iterator, Sequence
from pathlib import Path

_EMPTY = ""
_EOL = "-::-EOL-::-"
_CQP_MIN_VERSION = 3.004060
_FEATURE_RE = re.compile(r"^=====(TOKENS|COUNTS)\s+(\S+)$")
_CODE_FENCE_RE = re.compile(r"^\s*```cqp", re.MULTILINE)

FeatureMatrix = dict[str, dict[str, int]]


def _build_feature_matrix(stdout: Iterator[str]) -> FeatureMatrix | None:
    feature_matrix: FeatureMatrix = defaultdict(lambda: defaultdict(int))
    line = next(stdout, None)
    if line is None:
        sys.stderr.write("Missing feature 'n_token'\n")
        return None
    match = _FEATURE_RE.fullmatch(line)
    if match is None:
        sys.stderr.write(f"Invalid feature declaration {line!r}.\n")
        return None
    ftype, feature = match.groups()
    if ftype != "TOKENS" or feature != "n_token":
        sys.stderr.write(f"Unexpected feature {feature!r}\n")
        return None
    n_tokens = 0
    sattrs = set[str]()
    while (line := next(stdout)) != _EOL:
        start, end, sattr = line.split("\t")
        n_tokens += int(end) - int(start) + 1
        feature_matrix["n_token"][sattr] += int(end) - int(start) + 1
        sattrs.add(sattr)
    sys.stderr.write(f"{len(sattrs)} texts, {n_tokens / 1e6:.1f}M tokens\n")
    while (line := next(stdout, None)) is not None:
        match = _FEATURE_RE.fullmatch(line)
        if match is None:
            sys.stderr.write(f"Invalid feature declaration {line!r}.\n")
            return None
        ftype, feature = match.groups()
        if feature in feature_matrix:
            sys.stderr.write(f"Duplicate entry for feature {feature!r}\n")
            return None
        if ftype == "TOKENS":
            while (line := next(stdout)) != _EOL:
                _start, _end, sattr = line.split("\t")
                if sattr not in sattrs:
                    sys.stderr.write(f"Unknown s-attribute {sattr!r}\n")
                    return None
                feature_matrix[feature][sattr] += 1
        elif ftype == "COUNTS":
            while (line := next(stdout)) != _EOL:
                sattr, count = line.split("\t")
                if sattr not in sattrs:
                    sys.stderr.write(f"Unknown s-attribute {sattr!r}\n")
                    return None
                if sattr in feature_matrix[feature]:
                    sys.stderr.write(f"Duplicate entry for s-attribute {sattr!r}\n")
                    return None
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


def _run_cqp(script: Path, *args: str) -> Generator[str] | None:
    with script.open(encoding="utf-8") as fp:
        content = fp.read()
    type = "-f" if _CODE_FENCE_RE.search(content) is None else "-n"
    proc = subprocess.Popen(
        args=["cqp", "-c", type, script, *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        encoding="utf-8",
    )
    assert proc.stdout is not None
    stdout = (line.rstrip("\r\n") for line in proc.stdout)
    cqp_error = threading.Event()

    def _watch_stderr() -> None:
        assert proc.stderr is not None
        while (line := proc.stderr.readline()) != _EMPTY:
            sys.stderr.write(line)
            if not cqp_error.is_set():
                cqp_error.set()
                proc.terminate()

    stderr_thread = threading.Thread(target=_watch_stderr)
    stderr_thread.start()

    def _shutdown() -> None:
        proc.wait()
        stderr_thread.join()

    version_line = next(stdout, None)
    if version_line is None:
        _shutdown()
        return None
    version = _parse_cqp_version(version_line)
    if version < _CQP_MIN_VERSION:
        sys.stderr.write(f"CQP version {version!r} is too old (<{_CQP_MIN_VERSION}).\n")
        _shutdown()
        return None

    def _stdout() -> Generator[str]:
        try:
            for line in stdout:
                if cqp_error.is_set():
                    break
                yield line
        finally:
            _shutdown()

    return _stdout()


def featex(script: Path, *args: str) -> int:
    stdout = _run_cqp(script, *args)
    if stdout is None:
        return 1
    feature_matrix = _build_feature_matrix(stdout)
    if feature_matrix is None:
        return 1
    return _write_feature_matrix(feature_matrix)


class Ns(argparse.Namespace):
    script: Path
    cqp_args: list[str]


def main(args: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("script", type=Path, help="Path to CQP command script.")
    parser.add_argument(
        "cqp_args", nargs=argparse.REMAINDER, help="Arguments forwarded to CQP."
    )
    ns = parser.parse_args(args, namespace=Ns())
    if not ns.script.exists():
        sys.stderr.write(f"{ns.script.as_posix()!r} does not exist.\n")
        return 1
    if not ns.script.is_file():
        sys.stderr.write(f"{ns.script.as_posix()!r} is not a file.\n")
        return 1
    return featex(ns.script, *ns.cqp_args)


if __name__ == "__main__":
    raise SystemExit(main())
