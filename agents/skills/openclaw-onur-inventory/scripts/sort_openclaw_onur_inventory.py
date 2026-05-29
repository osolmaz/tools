#!/usr/bin/env python3
"""Sort OpenClaw Onur inventory tables and refresh GitHub activity counts."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_PATH = Path("OPENCLAW_ONUR_INVENTORY.md")
DEFAULT_REPO = "openclaw/openclaw"
COMMENT_WEIGHT = 4
REVIEW_COMMENT_WEIGHT = 4
REVIEW_BODY_WEIGHT = 5
REACTION_WEIGHT = 1

THREAD_ROW_RE = re.compile(r"^\| \[#(?P<number>\d+)\]\((?P<url>[^)]+)\)")
SECTION_RE = re.compile(
    r"^## (?P<title>OPEN ISSUES|OPEN PRS|RECENTLY CLOSED OR REMOVED FROM OPEN INVENTORY)(?: \((?P<count>\d+)\))?$",
)
THREAD_URL_RE = re.compile(
    r"https://github\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/(?:issues|pull)/(?P<number>\d+)",
)


@dataclass(frozen=True)
class ThreadRef:
    owner: str
    repo: str
    number: int
    kind: str

    @property
    def full_repo(self) -> str:
        return f"{self.owner}/{self.repo}"


@dataclass
class Activity:
    issue_comments: int = 0
    issue_body_reactions: int = 0
    issue_comment_reactions: int = 0
    pr_review_comments: int = 0
    pr_review_comment_reactions: int = 0
    pr_review_bodies: int = 0

    @property
    def reactions(self) -> int:
        return (
            self.issue_body_reactions
            + self.issue_comment_reactions
            + self.pr_review_comment_reactions
        )

    @property
    def score(self) -> int:
        return (
            self.issue_comments * COMMENT_WEIGHT
            + self.issue_body_reactions * REACTION_WEIGHT
            + self.issue_comment_reactions * REACTION_WEIGHT
            + self.pr_review_comments * REVIEW_COMMENT_WEIGHT
            + self.pr_review_comment_reactions * REACTION_WEIGHT
            + self.pr_review_bodies * REVIEW_BODY_WEIGHT
        )

    def format_cell(self, kind: str) -> str:
        parts = [f"c{self.issue_comments}", f"r{self.reactions}"]
        if kind == "pr":
            parts.insert(1, f"rc{self.pr_review_comments}")
            parts.insert(2, f"rv{self.pr_review_bodies}")
        return f"{self.score} ({' '.join(parts)})"


class GithubActivityClient:
    def __init__(self, *, exclude_spam: bool = True) -> None:
        self.exclude_spam = exclude_spam
        self.cache: dict[ThreadRef, Activity] = {}

    def activity_for(self, thread: ThreadRef) -> Activity:
        if thread not in self.cache:
            self.cache[thread] = self._fetch_activity(thread)
        return self.cache[thread]

    def _fetch_activity(self, thread: ThreadRef) -> Activity:
        issue_comments = self._issue_comments(thread)
        issue_body_reactions = self._reactions(
            f"repos/{thread.full_repo}/issues/{thread.number}/reactions?per_page=100",
        )
        issue_comment_reactions = sum(
            self._reactions(
                f"repos/{thread.full_repo}/issues/comments/{comment['id']}/reactions?per_page=100",
            )
            for comment in issue_comments
        )

        activity = Activity(
            issue_comments=len(issue_comments),
            issue_body_reactions=issue_body_reactions,
            issue_comment_reactions=issue_comment_reactions,
        )
        if thread.kind == "pr":
            review_comments = self._pr_review_comments(thread)
            reviews = self._pr_reviews(thread)
            activity.pr_review_comments = len(review_comments)
            activity.pr_review_comment_reactions = sum(
                self._reactions(
                    f"repos/{thread.full_repo}/pulls/comments/{comment['id']}/reactions?per_page=100",
                )
                for comment in review_comments
            )
            activity.pr_review_bodies = len(reviews)
        return activity

    def _issue_comments(self, thread: ThreadRef) -> list[dict[str, Any]]:
        comments = self._gh_json(
            "api",
            f"repos/{thread.full_repo}/issues/{thread.number}/comments?per_page=100",
            "--paginate",
            "--slurp",
        )
        comments = flatten_pages(comments)
        minimized = self._minimized_comment_ids(thread)
        kept = []
        for comment in comments:
            user = comment.get("user") or {}
            if is_bot(user.get("login"), user.get("type")):
                continue
            if self.exclude_spam and comment.get("id") in minimized:
                continue
            kept.append(comment)
        return kept

    def _reactions(self, endpoint: str) -> int:
        reactions = self._gh_json("api", endpoint, "--paginate", "--slurp")
        count = 0
        for reaction in flatten_pages(reactions):
            user = reaction.get("user") or {}
            if not is_bot(user.get("login"), user.get("type")):
                count += 1
        return count

    def _pr_review_comments(self, thread: ThreadRef) -> list[dict[str, Any]]:
        comments = self._gh_json(
            "api",
            f"repos/{thread.full_repo}/pulls/{thread.number}/comments?per_page=100",
            "--paginate",
            "--slurp",
        )
        kept = []
        for comment in flatten_pages(comments):
            user = comment.get("user") or {}
            if not is_bot(user.get("login"), user.get("type")):
                kept.append(comment)
        return kept

    def _pr_reviews(self, thread: ThreadRef) -> list[dict[str, Any]]:
        reviews = self._gh_json(
            "api",
            f"repos/{thread.full_repo}/pulls/{thread.number}/reviews?per_page=100",
            "--paginate",
            "--slurp",
        )
        kept = []
        for review in flatten_pages(reviews):
            user = review.get("user") or {}
            body = (review.get("body") or "").strip()
            if body and not is_bot(user.get("login"), user.get("type")):
                kept.append(review)
        return kept

    def _minimized_comment_ids(self, thread: ThreadRef) -> set[int]:
        if not self.exclude_spam:
            return set()

        node = "pullRequest" if thread.kind == "pr" else "issue"
        query = f"""
        query($owner: String!, $repo: String!, $number: Int!, $cursor: String) {{
          repository(owner: $owner, name: $repo) {{
            {node}(number: $number) {{
              comments(first: 100, after: $cursor) {{
                pageInfo {{ hasNextPage endCursor }}
                nodes {{ databaseId isMinimized minimizedReason }}
              }}
            }}
          }}
        }}
        """
        variables: dict[str, Any] = {
            "owner": thread.owner,
            "repo": thread.repo,
            "number": thread.number,
            "cursor": None,
        }
        ids: set[int] = set()
        while True:
            result = self._gh_json(
                "api",
                "graphql",
                "-f",
                f"query={query}",
                "-F",
                f"owner={variables['owner']}",
                "-F",
                f"repo={variables['repo']}",
                "-F",
                f"number={variables['number']}",
                "-F",
                f"cursor={variables['cursor']}" if variables["cursor"] else "cursor=",
            )
            comments = (
                result.get("data", {})
                .get("repository", {})
                .get(node, {})
                .get("comments", {})
            )
            for comment in comments.get("nodes") or []:
                if (
                    comment.get("isMinimized")
                    and comment.get("minimizedReason") == "SPAM"
                    and comment.get("databaseId") is not None
                ):
                    ids.add(int(comment["databaseId"]))
            page_info = comments.get("pageInfo") or {}
            if not page_info.get("hasNextPage"):
                return ids
            variables["cursor"] = page_info.get("endCursor")

    def _gh_json(self, *args: str) -> Any:
        command = ["gh", *args]
        try:
            proc = subprocess.run(
                command,
                check=True,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError as exc:
            raise RuntimeError("gh is not installed or not on PATH") from exc
        except subprocess.CalledProcessError as exc:
            detail = exc.stderr.strip() or exc.stdout.strip() or str(exc)
            raise RuntimeError(f"{' '.join(command)} failed: {detail}") from exc
        if not proc.stdout.strip():
            return []
        return json.loads(proc.stdout)


def flatten_pages(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    if value and all(isinstance(item, list) for item in value):
        flattened: list[dict[str, Any]] = []
        for page in value:
            flattened.extend(item for item in page if isinstance(item, dict))
        return flattened
    return [item for item in value if isinstance(item, dict)]


def is_bot(login: str | None, user_type: str | None) -> bool:
    return user_type == "Bot" or bool(login and login.endswith("[bot]"))


def thread_number(row: str) -> int:
    match = THREAD_ROW_RE.match(row)
    if not match:
        raise ValueError(f"not a thread table row: {row}")
    return int(match.group("number"))


def thread_ref_from_row(row: str, section_title: str, default_repo: str) -> ThreadRef | None:
    match = THREAD_ROW_RE.match(row)
    if not match:
        return None
    url_match = THREAD_URL_RE.search(match.group("url"))
    if url_match:
        return ThreadRef(
            owner=url_match.group("owner"),
            repo=url_match.group("repo"),
            number=int(url_match.group("number")),
            kind="pr" if "/pull/" in match.group("url") else "issue",
        )
    owner, repo = default_repo.split("/", maxsplit=1)
    return ThreadRef(
        owner=owner,
        repo=repo,
        number=int(match.group("number")),
        kind="pr" if section_title == "OPEN PRS" else "issue",
    )


def next_section_index(lines: list[str], start: int) -> int:
    for index in range(start + 1, len(lines)):
        if lines[index].startswith("## "):
            return index
    return len(lines)


def split_row(row: str) -> list[str]:
    stripped = row.strip()
    if not (stripped.startswith("|") and stripped.endswith("|")):
        raise ValueError(f"not a markdown table row: {row}")
    return [cell.strip() for cell in stripped.strip("|").split("|")]


def join_row(cells: list[str]) -> str:
    return "| " + " | ".join(cells) + " |"


def ensure_activity_column(lines: list[str], start: int, end: int) -> int | None:
    for index in range(start + 1, end):
        if not lines[index].startswith("| "):
            continue
        header = split_row(lines[index])
        if not header or not header[0] in {"Issue", "PR", "Thread"}:
            continue
        if "Activity" in header:
            return header.index("Activity")
        insert_at = min(2, len(header))
        header.insert(insert_at, "Activity")
        lines[index] = join_row(header)
        if index + 1 < end and lines[index + 1].startswith("| "):
            separator = split_row(lines[index + 1])
            separator.insert(insert_at, "---")
            lines[index + 1] = join_row(separator)
        for row_index in range(index + 2, end):
            if THREAD_ROW_RE.match(lines[row_index]):
                cells = split_row(lines[row_index])
                cells.insert(insert_at, "")
                lines[row_index] = join_row(cells)
        return insert_at
    return None


def set_activity_cell(row: str, activity_index: int, value: str) -> str:
    cells = split_row(row)
    while len(cells) <= activity_index:
        cells.append("")
    cells[activity_index] = value
    return join_row(cells)


def sort_section_rows(
    lines: list[str],
    start: int,
    end: int,
    *,
    section_title: str,
    activity_index: int | None,
    activity_client: GithubActivityClient | None,
    default_repo: str,
    warnings: list[str],
) -> int:
    row_indexes = [
        index
        for index in range(start, end)
        if THREAD_ROW_RE.match(lines[index])
    ]
    if not row_indexes:
        return 0

    if activity_client is not None and activity_index is not None:
        for index in row_indexes:
            thread = thread_ref_from_row(lines[index], section_title, default_repo)
            if thread is None:
                continue
            try:
                activity = activity_client.activity_for(thread)
            except RuntimeError as exc:
                warnings.append(f"activity skipped for #{thread.number}: {exc}")
                continue
            lines[index] = set_activity_cell(
                lines[index],
                activity_index,
                activity.format_cell(thread.kind),
            )

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


def sort_document(
    path: Path,
    *,
    update_activity: bool = True,
    default_repo: str = DEFAULT_REPO,
    exclude_spam: bool = True,
) -> tuple[int, int, int, bool, list[str]]:
    original = path.read_text()
    lines = original.splitlines()
    issue_count = 0
    pr_count = 0
    closed_count = 0
    warnings: list[str] = []

    activity_client = None
    if update_activity:
        activity_client = GithubActivityClient(exclude_spam=exclude_spam)

    for index, line in enumerate(lines):
        match = SECTION_RE.match(line)
        if not match:
            continue

        end = next_section_index(lines, index)
        title = match.group("title")
        activity_index = None
        section_activity_client = None
        if activity_client is not None and title in {"OPEN ISSUES", "OPEN PRS"}:
            activity_index = ensure_activity_column(lines, index, end)
            section_activity_client = activity_client

        count = sort_section_rows(
            lines,
            index,
            end,
            section_title=title,
            activity_index=activity_index,
            activity_client=section_activity_client,
            default_repo=default_repo,
            warnings=warnings,
        )

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

    return issue_count, pr_count, closed_count, changed, warnings


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Sort OpenClaw Onur inventory tables newest-first and refresh activity scores.",
    )
    parser.add_argument(
        "path",
        nargs="?",
        default=DEFAULT_PATH,
        type=Path,
        help="Markdown file to sort.",
    )
    parser.add_argument(
        "--no-activity",
        action="store_true",
        help="Only sort/count rows; do not fetch GitHub activity scores.",
    )
    parser.add_argument(
        "--include-minimized-spam",
        action="store_true",
        help="Include comments minimized by GitHub as spam in activity counts.",
    )
    parser.add_argument(
        "--repo",
        default=DEFAULT_REPO,
        help="Default owner/repo for rows without a GitHub URL.",
    )
    args = parser.parse_args()

    env_skip_activity = os.environ.get("OPENCLAW_ONUR_INVENTORY_SKIP_ACTIVITY") == "1"
    issue_count, pr_count, closed_count, changed, warnings = sort_document(
        args.path,
        update_activity=not args.no_activity and not env_skip_activity,
        default_repo=args.repo,
        exclude_spam=not args.include_minimized_spam,
    )
    status = "updated" if changed else "already sorted"
    print(
        f"{status}: issues={issue_count} prs={pr_count} closed={closed_count}",
    )
    for warning in warnings:
        print(f"warning: {warning}", file=sys.stderr)


if __name__ == "__main__":
    main()
