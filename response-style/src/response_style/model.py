from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

type JsonScalar = None | bool | int | float | str
type JsonValue = JsonScalar | list[JsonValue] | dict[str, JsonValue]
type Role = Literal["user", "assistant"]
type ExampleKind = Literal["revision_requested", "continued_without_revision", "conversation_ended"]


@dataclass(frozen=True)
class MessageNode:
    message_id: str
    parent_id: str | None
    sequence: int
    role: Role | None = None
    text: str | None = None


@dataclass(frozen=True)
class Conversation:
    agent: str
    session_id: str
    relative_path: str
    nodes: tuple[MessageNode, ...]
    linear: bool = False
    branch_id: str | None = None


@dataclass(frozen=True)
class Turn:
    user_message_id: str
    user_query: str
    assistant_message_id: str
    assistant_response: str


@dataclass(frozen=True)
class ConversationPath:
    conversation: Conversation
    branch_id: str
    turns: tuple[Turn, ...]


@dataclass(frozen=True)
class Example:
    example_id: str
    kind: ExampleKind
    source_agent: str
    source_session_id: str
    source_branch_id: str
    source_relative_path: str
    initial_message_id: str
    query_message_id: str | None
    final_message_id: str | None
    initial_assistant_response: str
    user_query: str | None
    final_assistant_response: str | None
    matched_terms: tuple[str, ...]
    initial_word_count: int
    final_word_count: int | None

    def sort_key(self) -> tuple[str, ...]:
        return (
            self.source_agent,
            self.source_relative_path,
            self.source_session_id,
            self.source_branch_id,
            self.initial_message_id,
            self.query_message_id or "",
            self.final_message_id or "",
            self.kind,
        )

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema_version": 1,
            "example_id": self.example_id,
            "kind": self.kind,
            "source_agent": self.source_agent,
            "source_session_id": self.source_session_id,
            "source_branch_id": self.source_branch_id,
            "source_relative_path": self.source_relative_path,
            "initial_message_id": self.initial_message_id,
            "query_message_id": self.query_message_id,
            "final_message_id": self.final_message_id,
            "initial_assistant_response": self.initial_assistant_response,
            "user_query": self.user_query,
            "final_assistant_response": self.final_assistant_response,
            "matched_terms": list(self.matched_terms),
            "initial_word_count": self.initial_word_count,
            "final_word_count": self.final_word_count,
        }


@dataclass(frozen=True)
class Issue:
    source_agent: str
    source_relative_path: str
    code: str
    message: str
    line_number: int | None = None
    byte_offset: int | None = None

    def sort_key(self) -> tuple[str, str, int, int, str]:
        return (
            self.source_agent,
            self.source_relative_path,
            self.line_number or 0,
            self.byte_offset or 0,
            self.code,
        )

    def to_record(self) -> dict[str, JsonValue]:
        return {
            "schema_version": 1,
            "source_agent": self.source_agent,
            "source_relative_path": self.source_relative_path,
            "code": self.code,
            "message": self.message,
            "line_number": self.line_number,
            "byte_offset": self.byte_offset,
        }


@dataclass(frozen=True)
class SourceBatch:
    conversations: tuple[Conversation, ...]
    issues: tuple[Issue, ...]
