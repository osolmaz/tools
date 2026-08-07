from __future__ import annotations

import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import cast

import pytest

from response_style import adapters
from response_style.cli import main
from response_style.dataset import DatasetSettings, verify_dataset, write_dataset
from response_style.model import Issue
from test_response_style import _cursor_db, _sample_examples, _write_jsonl


def test_jsonl_snapshot_accepts_append_and_rejects_changed_prefix(tmp_path: Path) -> None:
    path = tmp_path / "source.jsonl"
    _write_jsonl(path, [{"type": "one"}])

    def append_handler(_record: dict[str, object], _line: int, _offset: int) -> None:
        with path.open("ab") as target:
            target.write(b'{"type":"two"}\n')

    stable, issues = adapters._process_jsonl("pi", path, "source.jsonl", append_handler)
    assert stable
    assert not issues

    path.write_text('{"type":"one"}\n', encoding="utf-8")

    def mutate_handler(_record: dict[str, object], _line: int, _offset: int) -> None:
        with path.open("r+b") as target:
            target.write(b"[")

    stable, issues = adapters._process_jsonl("pi", path, "source.jsonl", mutate_handler)
    assert not stable
    assert issues[-1].code == "source_changed"


def test_jsonl_snapshot_reports_non_object_and_partial_tail(tmp_path: Path) -> None:
    path = tmp_path / "source.jsonl"
    path.write_bytes(b'[]\n{"partial":true}')
    seen: list[dict[str, object]] = []
    stable, issues = adapters._process_jsonl(
        "pi", path, "source.jsonl", lambda record, _line, _offset: seen.append(record)
    )
    assert stable
    assert not seen
    assert [issue.code for issue in issues] == ["unsupported_jsonl_record"]


def test_source_walk_ignores_symlinks_and_rejects_files(tmp_path: Path) -> None:
    root = tmp_path / "root"
    root.mkdir()
    outside = tmp_path / "outside.jsonl"
    outside.write_text("{}\n", encoding="utf-8")
    (root / "linked.jsonl").symlink_to(outside)
    assert adapters._source_files(root, suffix=".jsonl") == []
    with pytest.raises(ValueError, match="not a directory"):
        adapters.extract_pi(outside)


def test_cursor_wire_reader_skips_supported_unknown_fields() -> None:
    message_id = bytes.fromhex("33" * 32)
    data = b"\x10\x01" + b"\x19" + b"0" * 8 + b"\x25" + b"0" * 4 + b"\x0a\x20" + message_id
    assert adapters._cursor_message_ids(data) == [message_id.hex()]
    with pytest.raises(ValueError, match="message ID"):
        adapters._cursor_message_ids(b"\x0a\x01x")
    with pytest.raises(ValueError, match="wire type"):
        adapters._cursor_message_ids(b"\x0b")
    with pytest.raises(ValueError, match="varint"):
        adapters._cursor_message_ids(b"\x80" * 10)


def test_cursor_reports_missing_message_and_ignores_non_messages(tmp_path: Path) -> None:
    chats = tmp_path / "chats"
    acp = tmp_path / "acp"
    _cursor_db(chats / "missing" / "store.db")
    connection = sqlite3.connect(chats / "missing" / "store.db")
    connection.execute("DELETE FROM blobs WHERE id = ?", ("22" * 32,))
    connection.commit()
    connection.close()
    _cursor_db(acp / "skip" / "store.db")
    connection = sqlite3.connect(acp / "skip" / "store.db")
    connection.execute("UPDATE blobs SET data = ? WHERE id = ?", (b"not-json", "11" * 32))
    connection.commit()
    connection.close()
    batch = adapters.extract_cursor(chats, acp)
    assert [issue.code for issue in batch.issues] == ["missing_cursor_message"]
    assert len(batch.conversations) == 1
    assert [node.role for node in batch.conversations[0].nodes] == ["assistant"]


def test_dataset_rejects_unexpected_files_and_invalid_manifest_counts(tmp_path: Path) -> None:
    output = tmp_path / "dataset"
    settings = DatasetSettings("onur", 5, ("pi",))
    write_dataset(output, _sample_examples(), (Issue("pi", "x", "code", "message"),), settings)
    extra = output / "extra"
    extra.write_text("x", encoding="utf-8")
    os.chmod(extra, 0o600)
    with pytest.raises(ValueError, match="unexpected"):
        verify_dataset(output)
    extra.unlink()

    manifest_path = output / "manifest.json"
    manifest = cast(dict[str, object], json.loads(manifest_path.read_text()))
    counts = cast(dict[str, object], manifest["counts"])
    counts["examples"] = 999
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    os.chmod(manifest_path, 0o600)
    with pytest.raises(ValueError, match="example count"):
        verify_dataset(output)


def test_dataset_rejects_invalid_example_metrics_after_manifest_update(tmp_path: Path) -> None:
    output = tmp_path / "dataset"
    write_dataset(output, _sample_examples(), (), DatasetSettings("onur", 5, ("pi",)))
    examples_path = output / "examples.jsonl"
    records = [
        cast(dict[str, object], json.loads(line)) for line in examples_path.read_text().splitlines()
    ]
    records[0]["initial_word_count"] = 999
    data = "".join(
        json.dumps(record, separators=(",", ":"), sort_keys=True) + "\n" for record in records
    )
    examples_path.write_text(data, encoding="utf-8")
    os.chmod(examples_path, 0o600)
    manifest_path = output / "manifest.json"
    manifest = cast(dict[str, object], json.loads(manifest_path.read_text()))
    files = cast(dict[str, object], manifest["files"])
    metadata = cast(dict[str, object], files["examples.jsonl"])
    encoded = data.encode()
    import hashlib

    metadata["bytes"] = len(encoded)
    metadata["sha256"] = hashlib.sha256(encoded).hexdigest()
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    os.chmod(manifest_path, 0o600)
    with pytest.raises(ValueError, match="word count"):
        verify_dataset(output)


def test_cli_verify_and_invalid_threshold(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    output = tmp_path / "dataset"
    write_dataset(output, (), (), DatasetSettings("onur", 5, ()))
    monkeypatch.setattr(sys, "argv", ["response-style", "verify", "--dataset", str(output)])
    main()
    assert '"example_count": 0' in capsys.readouterr().out

    monkeypatch.setattr(
        sys,
        "argv",
        ["response-style", "mine", "--unix-user", "onur", "--long-word-count", "0"],
    )
    with pytest.raises(SystemExit) as error:
        main()
    assert error.value.code == 2
