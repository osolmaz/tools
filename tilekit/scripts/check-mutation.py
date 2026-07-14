#!/usr/bin/env python3
"""Run mutmut and fail when its kill rate is below the requested floor."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys

STATS = re.compile(
    r"(?P<done>\d+)/(?P<total>\d+)\s+🎉 (?P<killed>\d+)\s+🫥 (?P<uncovered>\d+)"
    r"\s+⏰ (?P<timeout>\d+)\s+🤔 (?P<suspicious>\d+)\s+🙁 (?P<survived>\d+)"
    r"\s+🔇 (?P<skipped>\d+)"
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-kill-rate", type=float, required=True)
    arguments = parser.parse_args()

    completed = subprocess.run(
        ["mutmut", "run"],
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout + completed.stderr
    shutil.rmtree("mutants", ignore_errors=True)
    if completed.returncode != 0:
        sys.stderr.write(output)
        return 2

    matches = list(STATS.finditer(output.replace("\r", "\n")))
    if not matches:
        sys.stderr.write(output)
        sys.stderr.write("mutation gate failed: no mutmut statistics found\n")
        return 2

    stats = {key: int(value) for key, value in matches[-1].groupdict().items()}
    if stats["done"] != stats["total"]:
        sys.stderr.write("mutation gate failed: mutmut did not finish\n")
        return 2

    caught = stats["killed"] + stats["timeout"]
    catchable = caught + stats["survived"] + stats["uncovered"]
    if catchable == 0:
        sys.stderr.write("mutation gate failed: no mutants were generated\n")
        return 2

    rate = 100 * caught / catchable
    print(f"mutation kill rate: {rate:.1f}% ({caught} of {catchable})")
    if rate < arguments.min_kill_rate:
        sys.stderr.write(
            f"mutation gate failed: {rate:.1f}% is below {arguments.min_kill_rate:.1f}%\n"
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
