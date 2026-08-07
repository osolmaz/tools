from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from response_style import adapters
from response_style.dataset import (
    DatasetSettings,
    DatasetSummary,
    read_summary,
    verify_dataset,
    write_dataset,
)
from response_style.miner import mine_examples
from response_style.model import Issue, SourceBatch


def main() -> None:
    os.umask(0o077)
    parser = _parser()
    arguments = parser.parse_args()
    try:
        if arguments.command == "mine":
            summary = _mine(arguments)
        elif arguments.command == "stats":
            summary = read_summary(arguments.dataset)
        elif arguments.command == "verify":
            summary = verify_dataset(arguments.dataset)
        else:
            parser.error("a command is required")
    except (OSError, ValueError) as error:
        print(f"response-style: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(json.dumps(summary.to_record(), indent=2, sort_keys=True))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="response-style",
        description="Mine private response-style examples from local conversations",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    mine = commands.add_parser("mine", help="mine explicitly supplied conversation roots")
    mine.add_argument("--unix-user", required=True)
    mine.add_argument("--output", type=Path, default=_default_dataset_path())
    mine.add_argument("--long-word-count", type=_positive_integer, default=400)
    mine.add_argument("--pi-sessions", type=Path)
    mine.add_argument("--codex-sessions", type=Path)
    mine.add_argument("--claude-projects", type=Path)
    mine.add_argument("--cursor-chats", type=Path)
    mine.add_argument("--cursor-acp-sessions", type=Path)
    for name in ("stats", "verify"):
        command = commands.add_parser(name, help=f"{name} a private dataset without printing text")
        command.add_argument("--dataset", type=Path, default=_default_dataset_path())
    return parser


def _mine(arguments: argparse.Namespace) -> DatasetSummary:
    roots = _source_roots(arguments)
    if not roots:
        raise ValueError("at least one conversation source must be supplied")
    if (arguments.cursor_chats is None) != (arguments.cursor_acp_sessions is None):
        raise ValueError("Cursor chats and ACP session roots must be supplied together")
    _reject_output_in_sources(arguments.output, roots)
    _reject_git_worktree_output(arguments.output)
    batches: list[SourceBatch] = []
    if arguments.pi_sessions is not None:
        batches.append(adapters.extract_pi(arguments.pi_sessions))
    if arguments.codex_sessions is not None:
        batches.append(adapters.extract_codex(arguments.codex_sessions))
    if arguments.claude_projects is not None:
        batches.append(adapters.extract_claude(arguments.claude_projects))
    if arguments.cursor_chats is not None and arguments.cursor_acp_sessions is not None:
        batches.append(
            adapters.extract_cursor(arguments.cursor_chats, arguments.cursor_acp_sessions)
        )
    conversations = tuple(conversation for batch in batches for conversation in batch.conversations)
    source_issues = tuple(issue for batch in batches for issue in batch.issues)
    examples, mining_issues = mine_examples(conversations, arguments.long_word_count)
    issues = tuple(sorted((*source_issues, *mining_issues), key=Issue.sort_key))
    source_agents = tuple(sorted({conversation.agent for conversation in conversations}))
    settings = DatasetSettings(arguments.unix_user, arguments.long_word_count, source_agents)
    return write_dataset(arguments.output, examples, issues, settings)


def _source_roots(arguments: argparse.Namespace) -> tuple[Path, ...]:
    values = (
        arguments.pi_sessions,
        arguments.codex_sessions,
        arguments.claude_projects,
        arguments.cursor_chats,
        arguments.cursor_acp_sessions,
    )
    return tuple(value for value in values if isinstance(value, Path))


def _reject_output_in_sources(output: Path, roots: tuple[Path, ...]) -> None:
    output_path = output.expanduser().resolve(strict=False)
    for root in roots:
        source = root.expanduser().resolve(strict=True)
        if output_path == source or output_path.is_relative_to(source):
            raise ValueError("dataset output cannot be inside a source root")


def _reject_git_worktree_output(output: Path) -> None:
    destination = output.expanduser().resolve(strict=False)
    for parent in (destination, *destination.parents):
        if (parent / ".git").exists():
            raise ValueError("dataset output cannot be inside a Git worktree")


def _default_dataset_path() -> Path:
    data_home = os.environ.get("XDG_DATA_HOME")
    root = Path(data_home).expanduser() if data_home else Path.home() / ".local" / "share"
    return root / "response-style-private"


def _positive_integer(value: str) -> int:
    parsed = int(value)
    if parsed < 1:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


if __name__ == "__main__":
    main()
