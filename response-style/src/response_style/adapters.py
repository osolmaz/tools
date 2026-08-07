from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import stat
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import cast

from response_style.model import Conversation, Issue, MessageNode, Role, SourceBatch
from response_style.text import clean_text

Record = dict[str, object]
RecordHandler = Callable[[Record, int, int], None]


def extract_pi(root: Path) -> SourceBatch:
    return _extract_jsonl_tree("pi", root, _parse_pi)


def extract_claude(root: Path) -> SourceBatch:
    return _extract_jsonl_tree("claude", root, _parse_claude)


def extract_codex(root: Path) -> SourceBatch:
    conversations: list[Conversation] = []
    issues: list[Issue] = []
    checked_root = _checked_root(root)
    for path in _source_files(checked_root, suffix=".jsonl"):
        relative = path.relative_to(checked_root).as_posix()
        conversation, source_issues = _parse_codex(path, relative)
        issues.extend(source_issues)
        if conversation is not None:
            conversations.append(conversation)
    return SourceBatch(tuple(conversations), tuple(issues))


def extract_cursor(chats: Path, acp_sessions: Path) -> SourceBatch:
    conversations: list[Conversation] = []
    issues: list[Issue] = []
    for source_kind, root in (("chats", chats), ("acp-sessions", acp_sessions)):
        checked_root = _checked_root(root)
        for path in _source_files(checked_root, name="store.db"):
            relative = f"{source_kind}/{path.relative_to(checked_root).as_posix()}"
            conversation, source_issues = _parse_cursor(path, relative)
            issues.extend(source_issues)
            if conversation is not None:
                conversations.append(conversation)
    return SourceBatch(tuple(conversations), tuple(issues))


def _extract_jsonl_tree(
    agent: str,
    root: Path,
    parser: Callable[[Path, str], tuple[Conversation | None, list[Issue]]],
) -> SourceBatch:
    conversations: list[Conversation] = []
    issues: list[Issue] = []
    checked_root = _checked_root(root)
    for path in _source_files(checked_root, suffix=".jsonl"):
        relative = path.relative_to(checked_root).as_posix()
        conversation, source_issues = parser(path, relative)
        issues.extend(source_issues)
        if conversation is not None:
            conversations.append(conversation)
    return SourceBatch(tuple(conversations), tuple(issues))


def _checked_root(root: Path) -> Path:
    resolved = root.expanduser().resolve(strict=True)
    if not resolved.is_dir():
        raise ValueError(f"source root is not a directory: {root}")
    return resolved


def _source_files(root: Path, *, suffix: str | None = None, name: str | None = None) -> list[Path]:
    paths: list[Path] = []
    for directory, directory_names, file_names in os.walk(root, followlinks=False):
        directory_names[:] = sorted(
            entry for entry in directory_names if not Path(directory, entry).is_symlink()
        )
        for file_name in sorted(file_names):
            if suffix is not None and not file_name.endswith(suffix):
                continue
            if name is not None and file_name != name:
                continue
            path = Path(directory, file_name)
            if path.is_symlink():
                continue
            resolved = path.resolve(strict=True)
            if not resolved.is_relative_to(root):
                continue
            if stat.S_ISREG(resolved.stat().st_mode):
                paths.append(resolved)
    return sorted(paths)


def _process_jsonl(
    agent: str,
    path: Path,
    relative: str,
    handler: RecordHandler,
) -> tuple[bool, list[Issue]]:
    issues: list[Issue] = []
    before = path.stat()
    digest = hashlib.sha256()
    byte_offset = 0
    line_number = 0
    with path.open("rb") as source:
        while byte_offset < before.st_size:
            remaining = before.st_size - byte_offset
            raw = source.readline(remaining + 1)
            if not raw or len(raw) > remaining or not raw.endswith(b"\n"):
                break
            line_number += 1
            digest.update(raw)
            try:
                value = cast(object, json.loads(raw))
            except (json.JSONDecodeError, UnicodeDecodeError):
                issues.append(
                    Issue(
                        agent,
                        relative,
                        "malformed_jsonl",
                        "JSONL record could not be decoded",
                        line_number,
                        byte_offset,
                    )
                )
            else:
                record = _object(value)
                if record is None:
                    issues.append(
                        Issue(
                            agent,
                            relative,
                            "unsupported_jsonl_record",
                            "JSONL record is not an object",
                            line_number,
                            byte_offset,
                        )
                    )
                else:
                    handler(record, line_number, byte_offset)
            byte_offset += len(raw)
    after = path.stat()
    stable = (before.st_dev, before.st_ino) == (after.st_dev, after.st_ino)
    stable = stable and after.st_size >= before.st_size
    if stable and (after.st_size != before.st_size or after.st_mtime_ns != before.st_mtime_ns):
        stable = _hash_prefix(path, byte_offset) == digest.digest()
    if not stable:
        issues.append(
            Issue(
                agent,
                relative,
                "source_changed",
                "Source changed before its snapshot could be verified",
            )
        )
    return stable, issues


def _hash_prefix(path: Path, size: int) -> bytes:
    digest = hashlib.sha256()
    remaining = size
    with path.open("rb") as source:
        while remaining:
            block = source.read(min(1024 * 1024, remaining))
            if not block:
                break
            digest.update(block)
            remaining -= len(block)
    return digest.digest() if remaining == 0 else b""


def _parse_pi(path: Path, relative: str) -> tuple[Conversation | None, list[Issue]]:
    nodes: list[MessageNode] = []
    session_id: str | None = None
    supported = False

    def handle(record: Record, line_number: int, _byte_offset: int) -> None:
        nonlocal session_id, supported
        if line_number == 1:
            supported = record.get("type") == "session" and record.get("version") == 3
            session_id = _string(record.get("id"))
            return
        message_id = _string(record.get("id"))
        if message_id is None:
            return
        role: Role | None = None
        text = None
        message = _object(record.get("message"))
        if record.get("type") == "message" and message is not None:
            native_role = _string(message.get("role"))
            if native_role in {"user", "assistant"}:
                role = cast(Role, native_role)
                text = _message_text(message, "text")
        nodes.append(
            MessageNode(
                message_id=message_id,
                parent_id=_string(record.get("parentId")),
                sequence=line_number,
                role=role,
                text=text,
            )
        )

    stable, issues = _process_jsonl("pi", path, relative, handle)
    if not stable:
        return None, issues
    if not supported or session_id is None:
        issues.append(Issue("pi", relative, "unsupported_pi_source", "Expected Pi session v3"))
        return None, issues
    return Conversation("pi", session_id, relative, tuple(nodes)), issues


def _parse_claude(path: Path, relative: str) -> tuple[Conversation | None, list[Issue]]:
    state = _ClaudeState()
    stable, issues = _process_jsonl("claude", path, relative, state.handle)
    if not stable:
        return None, issues
    if state.session_id is None:
        if state.records_seen:
            issues.append(
                Issue(
                    "claude",
                    relative,
                    "unsupported_claude_source",
                    "Claude source contains no supported session records",
                )
            )
        return None, issues
    return Conversation("claude", state.session_id, relative, tuple(state.nodes)), issues


@dataclass
class _ClaudeState:
    nodes: list[MessageNode] = field(default_factory=list)
    session_id: str | None = None
    records_seen: int = 0

    def handle(self, record: Record, line_number: int, _byte_offset: int) -> None:
        self.records_seen += 1
        native_session = _string(record.get("sessionId"))
        if self.session_id is None and native_session is not None:
            self.session_id = native_session
        node = _claude_node(record, line_number)
        if node is not None:
            self.nodes.append(node)


def _claude_node(record: Record, line_number: int) -> MessageNode | None:
    message_id = _string(record.get("uuid"))
    if message_id is None:
        return None
    role, text = _claude_role_and_text(record)
    return MessageNode(
        message_id=message_id,
        parent_id=_string(record.get("parentUuid")),
        sequence=line_number,
        role=role,
        text=text,
    )


def _claude_role_and_text(record: Record) -> tuple[Role | None, str | None]:
    message = _object(record.get("message"))
    if message is None:
        return None, None
    native_role = _string(message.get("role"))
    if native_role == "assistant":
        return "assistant", _message_text(message, "text")
    if native_role != "user" or not _is_claude_human(record):
        return None, None
    text = _message_text(message, "text")
    if text is None or _is_injected_claude_text(text):
        return None, None
    return "user", text


def _is_claude_human(record: Record) -> bool:
    if record.get("isSidechain") is True or _string(record.get("agentId")) is not None:
        return False
    prompt_source = _string(record.get("promptSource"))
    if prompt_source in {"system", "sdk"}:
        return False
    origin = _object(record.get("origin"))
    origin_kind = _string(origin.get("kind")) if origin is not None else None
    return origin_kind not in {"task-notification", "coordinator"}


def _is_injected_claude_text(text: str) -> bool:
    stripped = text.lstrip()
    return stripped.startswith("<task-notification>") or stripped.startswith("<system-reminder>")


def _parse_codex(path: Path, relative: str) -> tuple[Conversation | None, list[Issue]]:
    state = _CodexState()
    stable, issues = _process_jsonl("codex", path, relative, state.handle)
    if not stable:
        return None, issues
    if not state.supported or state.session_id is None:
        issues.append(
            Issue("codex", relative, "unsupported_codex_source", "Expected Codex session metadata")
        )
        return None, issues
    if state.is_subagent:
        return None, issues
    return Conversation(
        "codex", state.session_id, relative, tuple(state.nodes), linear=True
    ), issues


@dataclass
class _CodexState:
    nodes: list[MessageNode] = field(default_factory=list)
    session_id: str | None = None
    supported: bool = False
    is_subagent: bool = False
    previous_id: str | None = None

    def handle(self, record: Record, line_number: int, byte_offset: int) -> None:
        payload = _object(record.get("payload"))
        if payload is None:
            return
        if line_number == 1:
            self._header(record, payload)
            return
        if self.is_subagent:
            return
        node = _codex_node(record, payload, line_number, byte_offset, self.previous_id)
        if node is not None:
            self.nodes.append(node)
            self.previous_id = node.message_id

    def _header(self, record: Record, payload: Record) -> None:
        if record.get("type") != "session_meta":
            return
        self.supported = True
        self.session_id = _string(payload.get("id")) or _string(payload.get("session_id"))
        self.is_subagent = isinstance(payload.get("source"), dict)


def _codex_node(
    record: Record,
    payload: Record,
    line_number: int,
    byte_offset: int,
    parent_id: str | None,
) -> MessageNode | None:
    native_type = _string(payload.get("type"))
    if record.get("type") == "event_msg" and native_type == "user_message":
        return _codex_user_node(payload, line_number, byte_offset, parent_id)
    if record.get("type") != "response_item" or native_type != "message":
        return None
    return _codex_assistant_node(payload, line_number, byte_offset, parent_id)


def _codex_user_node(
    payload: Record, line_number: int, byte_offset: int, parent_id: str | None
) -> MessageNode | None:
    text = _string(payload.get("message"))
    if text is None or not text.strip():
        return None
    return MessageNode(f"line:{byte_offset}", parent_id, line_number, "user", text.strip())


def _codex_assistant_node(
    payload: Record, line_number: int, byte_offset: int, parent_id: str | None
) -> MessageNode | None:
    if payload.get("role") != "assistant" or payload.get("phase") not in {None, "final_answer"}:
        return None
    text = _message_text(payload, "output_text")
    if text is None:
        return None
    message_id = _string(payload.get("id")) or f"line:{byte_offset}"
    return MessageNode(message_id, parent_id, line_number, "assistant", text)


def _parse_cursor(path: Path, relative: str) -> tuple[Conversation | None, list[Issue]]:
    connection: sqlite3.Connection | None = None
    try:
        connection = _open_cursor(path)
        snapshot = _cursor_snapshot(connection, path)
        if snapshot is None:
            return None, []
        nodes = _cursor_nodes(connection, snapshot.message_ids)
        connection.rollback()
    except _CursorSourceError as error:
        return None, [_cursor_issue(relative, error.code)]
    except (OSError, sqlite3.Error, ValueError, json.JSONDecodeError, UnicodeDecodeError):
        return None, [_cursor_issue(relative, "cursor_read_failed")]
    finally:
        if connection is not None:
            connection.close()
    return Conversation(
        "cursor",
        snapshot.session_id,
        relative,
        tuple(nodes),
        linear=True,
        branch_id=snapshot.root_id,
    ), []


@dataclass(frozen=True)
class _CursorSnapshot:
    session_id: str
    root_id: str
    message_ids: tuple[str, ...]


class _CursorSourceError(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _open_cursor(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(f"{path.as_uri()}?mode=ro", uri=True)
    connection.execute("PRAGMA query_only = ON")
    connection.execute("BEGIN")
    return connection


def _cursor_snapshot(connection: sqlite3.Connection, path: Path) -> _CursorSnapshot | None:
    row = connection.execute("SELECT value FROM meta WHERE key = ?", ("0",)).fetchone()
    if row is None or not isinstance(row[0], str):
        raise _CursorSourceError("missing_cursor_metadata")
    metadata_value = cast(object, json.loads(bytes.fromhex(row[0])))
    metadata = _object(metadata_value)
    if metadata is None:
        raise _CursorSourceError("unsupported_cursor_metadata")
    subagent = _object(metadata.get("subagentInfo"))
    if subagent is not None and _string(subagent.get("parentAgentId")) is not None:
        return None
    session_id = _string(metadata.get("agentId")) or path.parent.name
    root_id = _string(metadata.get("latestRootBlobId"))
    if root_id is None:
        raise _CursorSourceError("missing_cursor_root")
    root_bytes = _cursor_blob(connection, root_id, "missing_cursor_root")
    try:
        message_ids = tuple(_cursor_message_ids(root_bytes))
    except ValueError as error:
        raise _CursorSourceError("unsupported_cursor_root") from error
    return _CursorSnapshot(session_id, root_id, message_ids)


def _cursor_nodes(
    connection: sqlite3.Connection, message_ids: tuple[str, ...]
) -> list[MessageNode]:
    nodes: list[MessageNode] = []
    previous_id: str | None = None
    for sequence, message_id in enumerate(message_ids, start=1):
        data = _cursor_blob(connection, message_id, "missing_cursor_message")
        node = _cursor_message_node(data, message_id, previous_id, sequence)
        if node is not None:
            nodes.append(node)
            previous_id = message_id
    return nodes


def _cursor_blob(connection: sqlite3.Connection, blob_id: str, missing_code: str) -> bytes:
    row = connection.execute("SELECT data FROM blobs WHERE id = ?", (blob_id,)).fetchone()
    if row is None:
        raise _CursorSourceError(missing_code)
    data = _bytes(row[0])
    if data is None:
        raise _CursorSourceError("unsupported_cursor_blob")
    return data


def _cursor_message_node(
    data: bytes, message_id: str, parent_id: str | None, sequence: int
) -> MessageNode | None:
    try:
        message_value = cast(object, json.loads(data))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    message = _object(message_value)
    if message is None or not isinstance(message.get("content"), list):
        return None
    native_role = _string(message.get("role"))
    if native_role not in {"user", "assistant"}:
        return None
    text = _message_text(message, "text")
    if text is None:
        return None
    return MessageNode(message_id, parent_id, sequence, cast(Role, native_role), text)


def _cursor_issue(relative: str, code: str) -> Issue:
    return Issue(
        "cursor", relative, code, "Cursor source could not be read with its strict adapter"
    )


def _cursor_message_ids(data: bytes) -> list[str]:
    position = 0
    message_ids: list[str] = []
    while position < len(data):
        key, position = _read_varint(data, position)
        field_number = key >> 3
        if field_number == 0:
            raise ValueError("invalid protobuf field")
        value, position = _read_wire_value(data, position, key & 7)
        if field_number == 1 and value is not None:
            if len(value) != 32:
                raise ValueError("invalid Cursor message ID")
            message_ids.append(value.hex())
    return message_ids


def _read_wire_value(data: bytes, position: int, wire_type: int) -> tuple[bytes | None, int]:
    if wire_type == 0:
        _, position = _read_varint(data, position)
        return None, position
    if wire_type == 1:
        return None, _skip(data, position, 8)
    if wire_type == 2:
        size, start = _read_varint(data, position)
        end = _skip(data, start, size)
        return data[start:end], end
    if wire_type == 5:
        return None, _skip(data, position, 4)
    raise ValueError("unsupported protobuf wire type")


def _read_varint(data: bytes, position: int) -> tuple[int, int]:
    value = 0
    shift = 0
    while position < len(data) and shift < 70:
        byte = data[position]
        position += 1
        value |= (byte & 0x7F) << shift
        if byte & 0x80 == 0:
            return value, position
        shift += 7
    raise ValueError("invalid protobuf varint")


def _skip(data: bytes, position: int, size: int) -> int:
    end = position + size
    if size < 0 or end > len(data):
        raise ValueError("truncated protobuf field")
    return end


def _message_text(message: Record, text_kind: str) -> str | None:
    content = message.get("content")
    if isinstance(content, str):
        return clean_text([content])
    if not isinstance(content, list):
        return None
    parts: list[str] = []
    for value in cast(list[object], content):
        block = _object(value)
        if block is None or block.get("type") != text_kind:
            continue
        text = _string(block.get("text"))
        if text is not None:
            parts.append(text)
    return clean_text(parts)


def _object(value: object) -> Record | None:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        return None
    return cast(Record, value)


def _string(value: object) -> str | None:
    return value if isinstance(value, str) else None


def _bytes(value: object) -> bytes | None:
    if isinstance(value, bytes):
        return value
    if isinstance(value, memoryview):
        return value.tobytes()
    return None
