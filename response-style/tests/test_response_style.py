from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import stat
import sys
from pathlib import Path
from typing import cast

import pytest

from response_style import adapters
from response_style.cli import main
from response_style.dataset import DatasetSettings, verify_dataset, write_dataset
from response_style.miner import conversation_paths, mine_examples
from response_style.model import Conversation, Example, Issue, MessageNode, Role
from response_style.text import clean_text, revision_signals, trigger_terms, word_count


def _write_jsonl(path: Path, records: list[dict[str, object]], *, malformed: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as target:
        for record in records:
            target.write(json.dumps(record))
            target.write("\n")
        if malformed:
            target.write("{broken}\n")


def _message(
    message_id: str,
    parent_id: str | None,
    sequence: int,
    role: str | None = None,
    text: str | None = None,
) -> MessageNode:
    return MessageNode(message_id, parent_id, sequence, cast(Role | None, role), text)


def _sample_conversation() -> Conversation:
    nodes = (
        _message("u0", None, 1, "user", "Give me an answer"),
        _message("a0", "u0", 2, "assistant", "one two three four five six"),
        _message("u1", "a0", 3, "user", "AMK, please"),
        _message("a1", "u1", 4, "assistant", "one two"),
        _message("u2", "a0", 5, "user", "Continue with the task"),
        _message("a2", "u2", 6, "assistant", "alpha beta gamma delta epsilon"),
    )
    return Conversation("pi", "session", "session.jsonl", nodes)


def _sample_examples() -> tuple[Example, ...]:
    examples, issues = mine_examples((_sample_conversation(),), 5)
    assert not issues
    return examples


def test_text_matching_is_exact_and_deterministic() -> None:
    assert trigger_terms("AMK and plain") == ("amk", "plain")
    assert trigger_terms("explain plainly") == ()
    assert trigger_terms("a plain-text file") == ("plain",)
    assert "shorter" in revision_signals("Make it shorter")
    assert "too_long" in revision_signals("This is too long")
    assert clean_text([" one ", "", " two "]) == "one\n\ntwo"
    assert clean_text([" "]) is None
    assert word_count("one two-three four's") == 3


def test_branch_mining_finds_rewrite_and_no_revision_examples() -> None:
    examples = _sample_examples()
    kinds = [example.kind for example in examples]
    assert kinds.count("revision_requested") == 1
    assert kinds.count("continued_without_revision") == 1
    assert kinds.count("conversation_ended") == 1
    rewrite = next(example for example in examples if example.kind == "revision_requested")
    assert rewrite.initial_assistant_response == "one two three four five six"
    assert rewrite.user_query == "AMK, please"
    assert rewrite.final_assistant_response == "one two"
    assert rewrite.matched_terms == ("amk",)


def test_existing_revision_row_is_stable_when_branch_grows() -> None:
    original = _sample_conversation()
    first, _ = mine_examples((original,), 100)
    revision = next(example for example in first if example.kind == "revision_requested")
    grown = Conversation(
        original.agent,
        original.session_id,
        original.relative_path,
        (*original.nodes, _message("u3", "a1", 7, "user", "A new task")),
    )
    second, _ = mine_examples((grown,), 100)
    repeated = next(example for example in second if example.kind == "revision_requested")
    assert revision == repeated
    assert revision.source_branch_id == revision.final_message_id


def test_consecutive_user_messages_keep_revision_trigger() -> None:
    conversation = Conversation(
        "pi",
        "s",
        "s.jsonl",
        (
            _message("u0", None, 1, "user", "Question"),
            _message("a0", "u0", 2, "assistant", "one two three four"),
            _message("u1", "a0", 3, "user", "amk"),
            _message("u2", "u1", 4, "user", "Keep the example"),
            _message("a1", "u2", 5, "assistant", "one"),
        ),
    )
    examples, _ = mine_examples((conversation,), 4)
    assert [example.kind for example in examples] == ["revision_requested"]
    assert examples[0].user_query == "amk\n\nKeep the example"
    assert examples[0].query_message_id == "u2"


def test_revision_signal_excludes_no_revision_proxy() -> None:
    conversation = Conversation(
        "pi",
        "s",
        "s.jsonl",
        (
            _message("u0", None, 1, "user", "Question"),
            _message("a0", "u0", 2, "assistant", "one two three four"),
            _message("u1", "a0", 3, "user", "Rewrite this shorter"),
            _message("a1", "u1", 4, "assistant", "one"),
        ),
    )
    examples, _ = mine_examples((conversation,), 4)
    assert [example.kind for example in examples] == []


def test_paths_reject_cycles_and_deduplicate_message_ids() -> None:
    conversation = Conversation(
        "pi",
        "s",
        "s.jsonl",
        (
            _message("a", "b", 1),
            _message("b", "a", 2),
            _message("b", None, 3),
        ),
    )
    _paths, issues = conversation_paths(conversation)
    assert {issue.code for issue in issues} == {"duplicate_message_id", "message_cycle"}


def test_pi_adapter_reads_tree_and_reports_malformed_records(tmp_path: Path) -> None:
    root = tmp_path / "pi"
    path = root / "project" / "session.jsonl"
    _write_jsonl(
        path,
        [
            {"type": "session", "version": 3, "id": "s"},
            {
                "type": "message",
                "id": "u",
                "parentId": None,
                "message": {"role": "user", "content": [{"type": "text", "text": "plain"}]},
            },
            {
                "type": "message",
                "id": "a",
                "parentId": "u",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "thinking", "thinking": "private"},
                        {"type": "text", "text": "visible"},
                    ],
                },
            },
        ],
        malformed=True,
    )
    batch = adapters.extract_pi(root)
    assert len(batch.conversations) == 1
    assert [node.text for node in batch.conversations[0].nodes] == ["plain", "visible"]
    assert [issue.code for issue in batch.issues] == ["malformed_jsonl"]


def test_pi_adapter_rejects_unknown_version(tmp_path: Path) -> None:
    root = tmp_path / "pi"
    _write_jsonl(root / "bad.jsonl", [{"type": "session", "version": 4, "id": "s"}])
    batch = adapters.extract_pi(root)
    assert not batch.conversations
    assert batch.issues[-1].code == "unsupported_pi_source"


def test_claude_adapter_keeps_human_text_and_excludes_injected_text(tmp_path: Path) -> None:
    root = tmp_path / "claude"
    _write_jsonl(
        root / "project" / "session.jsonl",
        [
            {
                "type": "user",
                "uuid": "u0",
                "parentUuid": None,
                "sessionId": "s",
                "promptSource": "typed",
                "origin": {"kind": "human"},
                "message": {"role": "user", "content": "Question"},
            },
            {
                "type": "assistant",
                "uuid": "a0",
                "parentUuid": "u0",
                "sessionId": "s",
                "message": {
                    "role": "assistant",
                    "content": [
                        {"type": "thinking", "thinking": "hidden"},
                        {"type": "text", "text": "Answer"},
                    ],
                },
            },
            {
                "type": "user",
                "uuid": "u1",
                "parentUuid": "a0",
                "sessionId": "s",
                "promptSource": "system",
                "origin": {"kind": "task-notification"},
                "message": {"role": "user", "content": "<task-notification>plain"},
            },
            {
                "type": "user",
                "uuid": "u2",
                "parentUuid": "a0",
                "sessionId": "s",
                "isSidechain": True,
                "agentId": "child",
                "message": {"role": "user", "content": "plain"},
            },
        ],
    )
    batch = adapters.extract_claude(root)
    nodes = batch.conversations[0].nodes
    assert [(node.role, node.text) for node in nodes] == [
        ("user", "Question"),
        ("assistant", "Answer"),
        (None, None),
        (None, None),
    ]


def test_claude_adapter_reports_unsupported_nonempty_source(tmp_path: Path) -> None:
    root = tmp_path / "claude"
    _write_jsonl(root / "unknown.jsonl", [{"type": "new-record"}])
    batch = adapters.extract_claude(root)
    assert not batch.conversations
    assert [issue.code for issue in batch.issues] == ["unsupported_claude_source"]


def test_codex_adapter_uses_user_events_and_final_answers(tmp_path: Path) -> None:
    root = tmp_path / "codex"
    _write_jsonl(
        root / "rollout.jsonl",
        [
            {"type": "session_meta", "payload": {"id": "s", "source": "exec"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "plain"}},
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "phase": "commentary",
                    "content": [{"type": "output_text", "text": "preamble"}],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "phase": "final_answer",
                    "id": "a",
                    "content": [{"type": "output_text", "text": "final"}],
                },
            },
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "copied"}],
                },
            },
        ],
    )
    batch = adapters.extract_codex(root)
    assert [(node.role, node.text) for node in batch.conversations[0].nodes] == [
        ("user", "plain"),
        ("assistant", "final"),
    ]


def test_codex_adapter_excludes_subagents_and_accepts_legacy_answers(tmp_path: Path) -> None:
    root = tmp_path / "codex"
    _write_jsonl(
        root / "sub.jsonl",
        [{"type": "session_meta", "payload": {"id": "sub", "source": {"subagent": "review"}}}],
    )
    _write_jsonl(
        root / "legacy.jsonl",
        [
            {"type": "session_meta", "payload": {"session_id": "legacy", "source": "cli"}},
            {"type": "event_msg", "payload": {"type": "user_message", "message": "Question"}},
            {
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "Answer"}],
                },
            },
        ],
    )
    batch = adapters.extract_codex(root)
    assert [conversation.session_id for conversation in batch.conversations] == ["legacy"]


def _varint(value: int) -> bytes:
    output = bytearray()
    while True:
        byte = value & 0x7F
        value >>= 7
        output.append(byte | 0x80 if value else byte)
        if not value:
            return bytes(output)


def _cursor_root(message_ids: list[bytes]) -> bytes:
    return b"".join(b"\x0a" + _varint(len(value)) + value for value in message_ids)


def _cursor_db(path: Path, *, missing_root: bool = False, subagent: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path)
    connection.executescript(
        "CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT);"
        "CREATE TABLE blobs (id TEXT PRIMARY KEY, data BLOB);"
    )
    user_id = bytes.fromhex("11" * 32)
    assistant_id = bytes.fromhex("22" * 32)
    root_id = "root"
    metadata: dict[str, object] = {"agentId": "cursor-session", "latestRootBlobId": root_id}
    if subagent:
        metadata["subagentInfo"] = {"parentAgentId": "parent"}
    connection.execute("INSERT INTO meta VALUES (?, ?)", ("0", json.dumps(metadata).encode().hex()))
    if not missing_root:
        connection.execute(
            "INSERT INTO blobs VALUES (?, ?)", (root_id, _cursor_root([user_id, assistant_id]))
        )
        connection.execute(
            "INSERT INTO blobs VALUES (?, ?)",
            (
                user_id.hex(),
                json.dumps(
                    {"role": "user", "content": [{"type": "text", "text": "plain"}]}
                ).encode(),
            ),
        )
        connection.execute(
            "INSERT INTO blobs VALUES (?, ?)",
            (
                assistant_id.hex(),
                json.dumps(
                    {
                        "role": "assistant",
                        "content": [
                            {"type": "reasoning", "text": "hidden"},
                            {"type": "text", "text": "visible"},
                        ],
                    }
                ).encode(),
            ),
        )
    connection.commit()
    connection.close()


def test_cursor_adapter_uses_root_order_and_visible_text(tmp_path: Path) -> None:
    chats = tmp_path / "chats"
    acp = tmp_path / "acp"
    _cursor_db(chats / "one" / "store.db")
    _cursor_db(acp / "child" / "store.db", subagent=True)
    before = hashlib.sha256((chats / "one" / "store.db").read_bytes()).digest()
    batch = adapters.extract_cursor(chats, acp)
    after = hashlib.sha256((chats / "one" / "store.db").read_bytes()).digest()
    assert before == after
    assert len(batch.conversations) == 1
    assert [(node.role, node.text) for node in batch.conversations[0].nodes] == [
        ("user", "plain"),
        ("assistant", "visible"),
    ]


def test_cursor_adapter_reports_missing_and_bad_roots(tmp_path: Path) -> None:
    chats = tmp_path / "chats"
    acp = tmp_path / "acp"
    _cursor_db(chats / "missing" / "store.db", missing_root=True)
    _cursor_db(acp / "bad" / "store.db")
    connection = sqlite3.connect(acp / "bad" / "store.db")
    connection.execute("UPDATE blobs SET data = ? WHERE id = ?", (b"\x0b", "root"))
    connection.commit()
    connection.close()
    batch = adapters.extract_cursor(chats, acp)
    assert {issue.code for issue in batch.issues} == {
        "missing_cursor_root",
        "unsupported_cursor_root",
    }


def test_dataset_is_private_deterministic_and_verifiable(tmp_path: Path) -> None:
    output = tmp_path / "response-style-private"
    examples = _sample_examples()
    issue = Issue("pi", "session.jsonl", "test_issue", "Bounded issue")
    settings = DatasetSettings("onur", 5, ("pi",))
    first = write_dataset(output, examples, (issue,), settings)
    second = write_dataset(output, examples, (issue,), settings)
    assert first.examples_sha256 == second.examples_sha256
    assert verify_dataset(output) == second
    assert stat.S_IMODE(output.stat().st_mode) == 0o700
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o600 for path in output.iterdir())
    assert first.example_count == 3


def test_dataset_verification_rejects_tampering_and_broad_permissions(tmp_path: Path) -> None:
    output = tmp_path / "dataset"
    write_dataset(output, _sample_examples(), (), DatasetSettings("onur", 5, ("pi",)))
    os.chmod(output / "examples.jsonl", 0o644)
    with pytest.raises(ValueError, match="permissions"):
        verify_dataset(output)
    os.chmod(output / "examples.jsonl", 0o600)
    with (output / "examples.jsonl").open("ab") as target:
        target.write(b"{}\n")
    with pytest.raises(ValueError, match="digest"):
        verify_dataset(output)


def test_dataset_rejects_symlink_and_stale_backup(tmp_path: Path) -> None:
    target = tmp_path / "target"
    target.mkdir()
    link = tmp_path / "link"
    link.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink"):
        write_dataset(link, (), (), DatasetSettings("onur", 5, ()))
    output = tmp_path / "dataset"
    (tmp_path / ".dataset.backup").mkdir()
    with pytest.raises(ValueError, match="backup"):
        write_dataset(output, (), (), DatasetSettings("onur", 5, ()))

    unrelated = tmp_path / "unrelated"
    unrelated.mkdir()
    marker = unrelated / "keep.txt"
    marker.write_text("keep", encoding="utf-8")
    with pytest.raises(ValueError, match="unexpected"):
        write_dataset(unrelated, (), (), DatasetSettings("onur", 5, ()))
    assert marker.read_text(encoding="utf-8") == "keep"


def test_cli_mines_and_reports_counts_without_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    root = tmp_path / "pi"
    words = " ".join(f"word{index}" for index in range(5))
    _write_jsonl(
        root / "session.jsonl",
        [
            {"type": "session", "version": 3, "id": "s"},
            {
                "type": "message",
                "id": "u",
                "parentId": None,
                "message": {"role": "user", "content": [{"type": "text", "text": "secret query"}]},
            },
            {
                "type": "message",
                "id": "a",
                "parentId": "u",
                "message": {"role": "assistant", "content": [{"type": "text", "text": words}]},
            },
        ],
    )
    output = tmp_path / "private"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "response-style",
            "mine",
            "--unix-user",
            "onur",
            "--pi-sessions",
            str(root),
            "--output",
            str(output),
            "--long-word-count",
            "5",
        ],
    )
    main()
    stdout = capsys.readouterr().out
    assert "secret query" not in stdout
    assert words not in stdout
    assert '"example_count": 1' in stdout

    monkeypatch.setattr(sys, "argv", ["response-style", "stats", "--dataset", str(output)])
    main()
    assert "secret query" not in capsys.readouterr().out


def test_cli_requires_sources_and_cursor_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["response-style", "mine", "--unix-user", "onur", "--output", str(tmp_path / "x")],
    )
    with pytest.raises(SystemExit) as missing:
        main()
    assert missing.value.code == 1
    assert "source" in capsys.readouterr().err

    chats = tmp_path / "chats"
    chats.mkdir()
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "response-style",
            "mine",
            "--unix-user",
            "onur",
            "--cursor-chats",
            str(chats),
        ],
    )
    with pytest.raises(SystemExit) as pair:
        main()
    assert pair.value.code == 1


def test_output_cannot_be_inside_source_or_git_worktree(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    from response_style.cli import _reject_git_worktree_output, _reject_output_in_sources

    with pytest.raises(ValueError, match="inside"):
        _reject_output_in_sources(source / "dataset", (source,))
    with pytest.raises(ValueError, match="inside"):
        _reject_output_in_sources(tmp_path / "missing" / ".." / "source" / "dataset", (source,))
    repository = tmp_path / "repo"
    (repository / ".git").mkdir(parents=True)
    with pytest.raises(ValueError, match="Git worktree"):
        _reject_git_worktree_output(repository / "private")
