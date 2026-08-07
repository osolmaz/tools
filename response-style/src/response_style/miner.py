from __future__ import annotations

import hashlib

from response_style.model import (
    Conversation,
    ConversationPath,
    Example,
    ExampleKind,
    Issue,
    MessageNode,
    Turn,
)
from response_style.text import revision_signals, trigger_terms, word_count


def mine_examples(
    conversations: tuple[Conversation, ...], long_word_count: int
) -> tuple[tuple[Example, ...], tuple[Issue, ...]]:
    if long_word_count < 1:
        raise ValueError("long word count must be positive")
    examples: dict[str, Example] = {}
    issues: list[Issue] = []
    for conversation in conversations:
        paths, path_issues = conversation_paths(conversation)
        issues.extend(path_issues)
        for path in paths:
            for example in _mine_path(path, long_word_count):
                current = examples.get(example.example_id)
                if current is None or example.sort_key() < current.sort_key():
                    examples[example.example_id] = example
    return tuple(sorted(examples.values(), key=Example.sort_key)), tuple(
        sorted(issues, key=Issue.sort_key)
    )


def conversation_paths(
    conversation: Conversation,
) -> tuple[tuple[ConversationPath, ...], tuple[Issue, ...]]:
    if conversation.linear:
        ordered = tuple(
            sorted(conversation.nodes, key=lambda node: (node.sequence, node.message_id))
        )
        branch_id = conversation.branch_id or (ordered[-1].message_id if ordered else "empty")
        turns = _turns(ordered)
        return (ConversationPath(conversation, branch_id, turns),), ()

    by_id: dict[str, MessageNode] = {}
    issues: list[Issue] = []
    for node in sorted(conversation.nodes, key=lambda value: (value.sequence, value.message_id)):
        if node.message_id in by_id:
            issues.append(
                Issue(
                    conversation.agent,
                    conversation.relative_path,
                    "duplicate_message_id",
                    "Conversation contains a duplicate message ID",
                )
            )
            continue
        by_id[node.message_id] = node
    parent_ids = {node.parent_id for node in by_id.values() if node.parent_id in by_id}
    leaves = sorted(
        (node for node in by_id.values() if node.message_id not in parent_ids),
        key=lambda value: (value.sequence, value.message_id),
    )
    if _has_cycle(by_id):
        issues.append(
            Issue(
                conversation.agent,
                conversation.relative_path,
                "message_cycle",
                "Conversation branch contains a parent cycle",
            )
        )
    paths: list[ConversationPath] = []
    for leaf in leaves:
        chain, cycle = _ancestor_chain(leaf, by_id)
        if not cycle:
            paths.append(ConversationPath(conversation, leaf.message_id, _turns(chain)))
    return tuple(paths), tuple(issues)


def _has_cycle(by_id: dict[str, MessageNode]) -> bool:
    return any(_ancestor_chain(node, by_id)[1] for node in by_id.values())


def _ancestor_chain(
    leaf: MessageNode, by_id: dict[str, MessageNode]
) -> tuple[tuple[MessageNode, ...], bool]:
    chain: list[MessageNode] = []
    seen: set[str] = set()
    current: MessageNode | None = leaf
    while current is not None:
        if current.message_id in seen:
            return (), True
        seen.add(current.message_id)
        chain.append(current)
        current = by_id.get(current.parent_id) if current.parent_id is not None else None
    chain.reverse()
    return tuple(chain), False


def _turns(nodes: tuple[MessageNode, ...]) -> tuple[Turn, ...]:
    turns: list[Turn] = []
    user: MessageNode | None = None
    assistant: MessageNode | None = None
    for node in nodes:
        if node.role == "user" and node.text is not None:
            if user is not None and assistant is None:
                user = _merge_user_messages(user, node)
            else:
                _append_turn(turns, user, assistant)
                user = node
                assistant = None
        elif node.role == "assistant" and node.text is not None and user is not None:
            assistant = node
    _append_turn(turns, user, assistant)
    return tuple(turns)


def _merge_user_messages(first: MessageNode, second: MessageNode) -> MessageNode:
    assert first.text is not None
    assert second.text is not None
    return MessageNode(
        message_id=second.message_id,
        parent_id=first.parent_id,
        sequence=second.sequence,
        role="user",
        text=f"{first.text}\n\n{second.text}",
    )


def _append_turn(
    turns: list[Turn], user: MessageNode | None, assistant: MessageNode | None
) -> None:
    if user is None or user.text is None or assistant is None or assistant.text is None:
        return
    turns.append(
        Turn(
            user_message_id=user.message_id,
            user_query=user.text,
            assistant_message_id=assistant.message_id,
            assistant_response=assistant.text,
        )
    )


def _mine_path(path: ConversationPath, long_word_count: int) -> list[Example]:
    examples: list[Example] = []
    turns = path.turns
    for index, turn in enumerate(turns):
        if index > 0:
            terms = trigger_terms(turn.user_query)
            if terms:
                examples.append(_revision_example(path, turns[index - 1], turn, terms))
        initial_words = word_count(turn.assistant_response)
        if initial_words < long_word_count:
            continue
        next_turn = turns[index + 1] if index + 1 < len(turns) else None
        if next_turn is None:
            examples.append(
                _no_revision_example(path, turn, None, "conversation_ended", initial_words)
            )
        elif not revision_signals(next_turn.user_query):
            examples.append(
                _no_revision_example(
                    path,
                    turn,
                    next_turn,
                    "continued_without_revision",
                    initial_words,
                )
            )
    return examples


def _revision_example(
    path: ConversationPath,
    initial: Turn,
    revised: Turn,
    terms: tuple[str, ...],
) -> Example:
    return _example(
        path=path,
        kind="revision_requested",
        initial=initial,
        query_message_id=revised.user_message_id,
        user_query=revised.user_query,
        final_message_id=revised.assistant_message_id,
        final_response=revised.assistant_response,
        matched_terms=terms,
        initial_words=word_count(initial.assistant_response),
        final_words=word_count(revised.assistant_response),
    )


def _no_revision_example(
    path: ConversationPath,
    initial: Turn,
    next_turn: Turn | None,
    kind: ExampleKind,
    initial_words: int,
) -> Example:
    return _example(
        path=path,
        kind=kind,
        initial=initial,
        query_message_id=next_turn.user_message_id if next_turn is not None else None,
        user_query=next_turn.user_query if next_turn is not None else None,
        final_message_id=None,
        final_response=None,
        matched_terms=(),
        initial_words=initial_words,
        final_words=None,
    )


def _example(
    *,
    path: ConversationPath,
    kind: ExampleKind,
    initial: Turn,
    query_message_id: str | None,
    user_query: str | None,
    final_message_id: str | None,
    final_response: str | None,
    matched_terms: tuple[str, ...],
    initial_words: int,
    final_words: int | None,
) -> Example:
    conversation = path.conversation
    parts = (
        "1",
        kind,
        conversation.agent,
        conversation.session_id,
        conversation.relative_path,
        initial.assistant_message_id,
        query_message_id or "",
        final_message_id or "",
    )
    digest = hashlib.sha256("\0".join(parts).encode()).hexdigest()
    return Example(
        example_id=f"sha256:{digest}",
        kind=kind,
        source_agent=conversation.agent,
        source_session_id=conversation.session_id,
        source_branch_id=final_message_id or query_message_id or initial.assistant_message_id,
        source_relative_path=conversation.relative_path,
        initial_message_id=initial.assistant_message_id,
        query_message_id=query_message_id,
        final_message_id=final_message_id,
        initial_assistant_response=initial.assistant_response,
        user_query=user_query,
        final_assistant_response=final_response,
        matched_terms=matched_terms,
        initial_word_count=initial_words,
        final_word_count=final_words,
    )
