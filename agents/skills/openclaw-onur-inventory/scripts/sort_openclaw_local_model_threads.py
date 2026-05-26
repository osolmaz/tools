#!/usr/bin/env python3
"""Sort OpenClaw local-model thread tables by GitHub number descending."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


DEFAULT_PATH = Path("OPENCLAW_ONUR_INVENTORY.md")
THREAD_ROW_RE = re.compile(r"^\| \[#(?P<number>\d+)\]\(")
SECTION_RE = re.compile(
    r"^## (?P<title>OPEN ISSUES|OPEN PRS|RECENTLY CLOSED OR REMOVED FROM OPEN INVENTORY)(?: \((?P<count>\d+)\))?$",
)


def thread_number(row: str) -> int:
    match = THREAD_ROW_RE.match(row)
    if not match:
        raise ValueError(f"not a thread table row: {row}")
    return int(match.group("number"))


def next_section_index(lines: list[str], start: int) -> int:
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            return index
    return len(lines)


def sort_section_rows(lines: list[str], start: int, end: int) -> int:
    row_indexes = [
        index
        for index in range(start, end)
        if THREAD_ROW_RE.match(lines[index])
    ]
    if not row_indexes:
        return 0

    sorted_rows = sorted(
        (lines[index] for index in row_indexes),
        key=thread_number,
        reverse=True,
    )
    for index, row in zip(row_indexes, sorted_rows, strict=True):
        lines[index] = row
    return len(sorted_rows)


def replace_count_line(lines: list[str], prefix: str, count: int) -> None:
    for index, line in enumerate(lines):
        if line.startswith(prefix):
            lines[index] = f"{prefix}{count}."
            return


def sort_document(path: Path) -> tuple[int, int, int, bool]:
    original = path.read_text()
    lines = original.splitlines()
    issue_count = 0
    pr_count = 0
    closed_count = 0

    for index, line in enumerate(lines):
        match = SECTION_RE.match(line)
        if not match:
            continue

        end = next_section_index(lines, index)
        count = sort_section_rows(lines, index, end)
        title = match.group("title")

        if title == "OPEN ISSUES":
            issue_count = count
            lines[index] = f"## OPEN ISSUES ({count})"
        elif title == "OPEN PRS":
            pr_count = count
            lines[index] = f"## OPEN PRS ({count})"
        elif title == "RECENTLY CLOSED OR REMOVED FROM OPEN INVENTORY":
            closed_count = count

    replace_count_line(lines, "- Kept open issues: ", issue_count)
    replace_count_line(lines, "- Kept open PRs: ", pr_count)

    updated = "\n".join(lines) + "\n"
    changed = updated != original
    if changed:
        path.write_text(updated)

    return issue_count, pr_count, closed_count, changed


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sort OpenClaw local-model issue/PR tables newest-first.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=DEFAULT_PATH,
        type=Path,
        help="Markdown file to sort.",
    )
    args = parser.parse_args()

    issue_count, pr_count, closed_count, changed = sort_document(args.path)
    status = "updated" if changed else "already sorted"
    print(
        f"{status}: issues={issue_count} prs={pr_count} closed={closed_count}",
    )


if __name__ == "__main__":
    main()
