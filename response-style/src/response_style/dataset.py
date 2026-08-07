from __future__ import annotations

import hashlib
import json
import os
import shutil
import stat
import tempfile
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import cast

from response_style.model import Example, Issue, JsonValue
from response_style.text import revision_signals, trigger_terms, word_count

_SCHEMA_VERSION = 1
_MAX_DATASET_BYTES = 10_000_000_000
_DATA_FILES = ("examples.jsonl", "issues.jsonl", "manifest.json")


@dataclass(frozen=True)
class DatasetSettings:
    unix_user: str
    long_word_count: int
    source_agents: tuple[str, ...]


@dataclass(frozen=True)
class DatasetSummary:
    schema_version: int
    example_count: int
    issue_count: int
    counts_by_kind: dict[str, int]
    counts_by_agent: dict[str, int]
    examples_sha256: str
    examples_bytes: int

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema_version": self.schema_version,
            "example_count": self.example_count,
            "issue_count": self.issue_count,
            "counts_by_kind": dict(sorted(self.counts_by_kind.items())),
            "counts_by_agent": dict(sorted(self.counts_by_agent.items())),
            "examples_sha256": self.examples_sha256,
            "examples_bytes": self.examples_bytes,
        }


def write_dataset(
    output: Path,
    examples: tuple[Example, ...],
    issues: tuple[Issue, ...],
    settings: DatasetSettings,
) -> DatasetSummary:
    requested = output.expanduser()
    if requested.is_symlink():
        raise ValueError("dataset path cannot be a symlink")
    destination = requested.resolve(strict=False)
    parent = destination.parent
    parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=f".{destination.name}.staging-", dir=parent))
    os.chmod(staging, 0o700)
    try:
        example_bytes = _jsonl(example.to_record() for example in examples)
        issue_bytes = _jsonl(issue.to_record() for issue in issues)
        if len(example_bytes) + len(issue_bytes) > _MAX_DATASET_BYTES:
            raise ValueError("dataset would exceed the 10 GB limit")
        _write_private(staging / "examples.jsonl", example_bytes)
        _write_private(staging / "issues.jsonl", issue_bytes)
        manifest = _manifest(examples, issues, settings, example_bytes, issue_bytes)
        _write_private(staging / "manifest.json", _json_bytes(manifest, pretty=True))
        summary = verify_dataset(staging)
        _replace_directory(staging, destination)
        return summary
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def verify_dataset(dataset: Path) -> DatasetSummary:
    requested = dataset.expanduser()
    if requested.is_symlink():
        raise ValueError("dataset is not a private directory")
    root = requested.resolve(strict=False)
    _verify_layout(root)
    manifest = _read_object(root / "manifest.json")
    if _integer(manifest.get("schema_version")) != _SCHEMA_VERSION:
        raise ValueError("unsupported dataset schema")
    settings = _required_object(manifest, "settings")
    long_word_count = _required_integer(settings, "long_word_count")
    files = _required_object(manifest, "files")
    _verify_digest(root / "examples.jsonl", _required_object(files, "examples.jsonl"))
    _verify_digest(root / "issues.jsonl", _required_object(files, "issues.jsonl"))
    example_count, by_kind, by_agent = _verify_examples(root / "examples.jsonl", long_word_count)
    issue_count = _verify_issues(root / "issues.jsonl")
    _verify_manifest_counts(manifest, example_count, issue_count, by_kind, by_agent)
    example_digest, example_size = _file_digest(root / "examples.jsonl")
    return DatasetSummary(
        schema_version=_SCHEMA_VERSION,
        example_count=example_count,
        issue_count=issue_count,
        counts_by_kind=by_kind,
        counts_by_agent=by_agent,
        examples_sha256=example_digest,
        examples_bytes=example_size,
    )


def _verify_layout(root: Path) -> None:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("dataset is not a private directory")
    _verify_private_mode(root, directory=True)
    names = tuple(sorted(path.name for path in root.iterdir()))
    if names != tuple(sorted(_DATA_FILES)):
        raise ValueError("dataset contains unexpected files")
    for name in _DATA_FILES:
        path = root / name
        if path.is_symlink() or not path.is_file():
            raise ValueError("dataset contains an invalid file")
        _verify_private_mode(path, directory=False)


def _verify_manifest_counts(
    manifest: dict[str, object],
    example_count: int,
    issue_count: int,
    by_kind: dict[str, int],
    by_agent: dict[str, int],
) -> None:
    counts = _required_object(manifest, "counts")
    if _required_integer(counts, "examples") != example_count:
        raise ValueError("example count does not match manifest")
    if _required_integer(counts, "issues") != issue_count:
        raise ValueError("issue count does not match manifest")
    if _string_integer_map(_required_object(counts, "by_kind")) != by_kind:
        raise ValueError("kind counts do not match manifest")
    if _string_integer_map(_required_object(counts, "by_agent")) != by_agent:
        raise ValueError("agent counts do not match manifest")


def read_summary(dataset: Path) -> DatasetSummary:
    return verify_dataset(dataset)


def _manifest(
    examples: tuple[Example, ...],
    issues: tuple[Issue, ...],
    settings: DatasetSettings,
    example_bytes: bytes,
    issue_bytes: bytes,
) -> dict[str, JsonValue]:
    by_kind: dict[str, int] = {}
    by_agent: dict[str, int] = {}
    for example in examples:
        by_kind[example.kind] = by_kind.get(example.kind, 0) + 1
        by_agent[example.source_agent] = by_agent.get(example.source_agent, 0) + 1
    return {
        "schema_version": _SCHEMA_VERSION,
        "dataset_name": "response-style-private",
        "settings": {
            "unix_user": settings.unix_user,
            "long_word_count": settings.long_word_count,
            "trigger_terms": ["amk", "plain"],
            "source_agents": list(settings.source_agents),
        },
        "counts": {
            "examples": len(examples),
            "issues": len(issues),
            "by_kind": dict(sorted(by_kind.items())),
            "by_agent": dict(sorted(by_agent.items())),
        },
        "files": {
            "examples.jsonl": _bytes_metadata(example_bytes),
            "issues.jsonl": _bytes_metadata(issue_bytes),
        },
    }


def _bytes_metadata(data: bytes) -> dict[str, JsonValue]:
    return {"bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}


def _jsonl(records: Iterable[dict[str, JsonValue]]) -> bytes:
    output = bytearray()
    for record in records:
        output.extend(_json_bytes(record, pretty=False))
        output.extend(b"\n")
    return bytes(output)


def _json_bytes(record: dict[str, JsonValue], *, pretty: bool) -> bytes:
    if pretty:
        text = json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    else:
        text = json.dumps(record, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return text.encode()


def _write_private(path: Path, data: bytes) -> None:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as target:
            target.write(data)
            target.flush()
            os.fsync(target.fileno())
    except BaseException:
        if path.exists():
            path.unlink()
        raise


def _replace_directory(staging: Path, destination: Path) -> None:
    backup = destination.with_name(f".{destination.name}.backup")
    if backup.exists():
        raise ValueError("stale dataset backup requires manual inspection")
    if destination.exists() and not destination.is_dir():
        raise ValueError("dataset path exists and is not a directory")
    if destination.exists():
        verify_dataset(destination)
        os.replace(destination, backup)
        try:
            os.replace(staging, destination)
        except BaseException:
            os.replace(backup, destination)
            raise
        shutil.rmtree(backup)
    else:
        os.replace(staging, destination)


def _verify_private_mode(path: Path, *, directory: bool) -> None:
    mode = stat.S_IMODE(path.stat().st_mode)
    if mode & 0o077:
        raise ValueError("dataset permissions are too broad")
    expected_owner = 0o700 if directory else 0o600
    if mode & expected_owner != expected_owner:
        raise ValueError("dataset owner permissions are incomplete")


def _verify_digest(path: Path, metadata: dict[str, object]) -> None:
    expected_digest = _required_string(metadata, "sha256")
    expected_size = _required_integer(metadata, "bytes")
    digest, size = _file_digest(path)
    if digest != expected_digest or size != expected_size:
        raise ValueError("dataset file digest does not match manifest")


def _file_digest(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def _verify_examples(
    path: Path, long_word_count: int
) -> tuple[int, dict[str, int], dict[str, int]]:
    by_kind: dict[str, int] = {}
    by_agent: dict[str, int] = {}
    ids: set[str] = set()
    for record in _read_jsonl(path):
        kind, agent, example_id = _verify_example(record, long_word_count)
        if example_id in ids:
            raise ValueError("dataset contains duplicate example IDs")
        ids.add(example_id)
        by_kind[kind] = by_kind.get(kind, 0) + 1
        by_agent[agent] = by_agent.get(agent, 0) + 1
    return len(ids), by_kind, by_agent


def _verify_example(record: dict[str, object], long_word_count: int) -> tuple[str, str, str]:
    if _integer(record.get("schema_version")) != _SCHEMA_VERSION:
        raise ValueError("example has unsupported schema")
    example_id = _required_string(record, "example_id")
    kind = _required_string(record, "kind")
    if kind not in {"revision_requested", "continued_without_revision", "conversation_ended"}:
        raise ValueError("example has invalid kind")
    agent = _required_string(record, "source_agent")
    _verify_example_identity(record, example_id, kind, agent)
    initial = _required_string(record, "initial_assistant_response")
    initial_words = _required_integer(record, "initial_word_count")
    if word_count(initial) != initial_words:
        raise ValueError("initial word count is invalid")
    if kind == "revision_requested":
        _verify_revision(record)
    else:
        _verify_no_revision(record, kind, initial_words, long_word_count)
    return kind, agent, example_id


def _verify_example_identity(
    record: dict[str, object], example_id: str, kind: str, agent: str
) -> None:
    session_id = _required_string(record, "source_session_id")
    branch_id = _required_string(record, "source_branch_id")
    relative_path = _required_string(record, "source_relative_path")
    if PurePosixPath(relative_path).is_absolute() or ".." in PurePosixPath(relative_path).parts:
        raise ValueError("example source path is invalid")
    initial_id = _required_string(record, "initial_message_id")
    query_id = _optional_string(record.get("query_message_id"))
    final_id = _optional_string(record.get("final_message_id"))
    if branch_id != (final_id or query_id or initial_id):
        raise ValueError("example branch boundary is invalid")
    parts = (
        "1",
        kind,
        agent,
        session_id,
        relative_path,
        initial_id,
        query_id or "",
        final_id or "",
    )
    expected = "sha256:" + hashlib.sha256("\0".join(parts).encode()).hexdigest()
    if example_id != expected:
        raise ValueError("example ID does not match its source identity")


def _verify_revision(record: dict[str, object]) -> None:
    query = _optional_string(record.get("user_query"))
    final = _optional_string(record.get("final_assistant_response"))
    final_words = _optional_integer(record.get("final_word_count"))
    if query is None or final is None or final_words is None:
        raise ValueError("revision example is incomplete")
    if record.get("query_message_id") is None or record.get("final_message_id") is None:
        raise ValueError("revision example source identity is incomplete")
    terms = _string_list(record.get("matched_terms"))
    if not terms or terms != list(trigger_terms(query)) or word_count(final) != final_words:
        raise ValueError("revision example metrics are invalid")


def _verify_no_revision(
    record: dict[str, object], kind: str, initial_words: int, long_word_count: int
) -> None:
    query = _optional_string(record.get("user_query"))
    final = _optional_string(record.get("final_assistant_response"))
    final_words = _optional_integer(record.get("final_word_count"))
    if initial_words < long_word_count or final is not None or final_words is not None:
        raise ValueError("no-revision example is invalid")
    if _string_list(record.get("matched_terms")):
        raise ValueError("no-revision example has trigger terms")
    if record.get("final_message_id") is not None:
        raise ValueError("no-revision example has a final message ID")
    if kind == "conversation_ended" and (
        query is not None or record.get("query_message_id") is not None
    ):
        raise ValueError("terminal example has a query")
    if kind == "continued_without_revision" and (
        query is None or record.get("query_message_id") is None or revision_signals(query)
    ):
        raise ValueError("continued example has a revision signal")


def _verify_issues(path: Path) -> int:
    count = 0
    for record in _read_jsonl(path):
        if _integer(record.get("schema_version")) != _SCHEMA_VERSION:
            raise ValueError("issue has unsupported schema")
        _required_string(record, "source_agent")
        relative_path = _required_string(record, "source_relative_path")
        if PurePosixPath(relative_path).is_absolute() or ".." in PurePosixPath(relative_path).parts:
            raise ValueError("issue source path is invalid")
        _required_string(record, "code")
        _required_string(record, "message")
        count += 1
    return count


def _read_jsonl(path: Path) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    with path.open("rb") as source:
        for raw in source:
            try:
                value = cast(object, json.loads(raw))
            except (json.JSONDecodeError, UnicodeDecodeError) as error:
                raise ValueError("dataset JSONL is malformed") from error
            if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
                raise ValueError("dataset JSONL record is not an object")
            records.append(cast(dict[str, object], value))
    return records


def _read_object(path: Path) -> dict[str, object]:
    try:
        value = cast(object, json.loads(path.read_bytes()))
    except (json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError("manifest is malformed") from error
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError("manifest is not an object")
    return cast(dict[str, object], value)


def _required_object(record: dict[str, object], key: str) -> dict[str, object]:
    value = record.get(key)
    if not isinstance(value, dict) or not all(isinstance(name, str) for name in value):
        raise ValueError("dataset object field is invalid")
    return cast(dict[str, object], value)


def _required_string(record: dict[str, object], key: str) -> str:
    value = record.get(key)
    if not isinstance(value, str):
        raise ValueError("dataset string field is invalid")
    return value


def _optional_string(value: object) -> str | None:
    if value is None or isinstance(value, str):
        return value
    raise ValueError("dataset optional string field is invalid")


def _integer(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None


def _required_integer(record: dict[str, object], key: str) -> int:
    value = _integer(record.get(key))
    if value is None or value < 0:
        raise ValueError("dataset integer field is invalid")
    return value


def _optional_integer(value: object) -> int | None:
    if value is None:
        return None
    integer = _integer(value)
    if integer is None or integer < 0:
        raise ValueError("dataset optional integer field is invalid")
    return integer


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
        raise ValueError("dataset string-list field is invalid")
    return cast(list[str], value)


def _string_integer_map(record: dict[str, object]) -> dict[str, int]:
    output: dict[str, int] = {}
    for key, value in record.items():
        integer = _integer(value)
        if integer is None or integer < 0:
            raise ValueError("dataset count map is invalid")
        output[key] = integer
    return output
