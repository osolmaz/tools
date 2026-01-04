/**
 * Type guard functions for runtime type checking
 */

import type {
  BaseMessage,
  UserMessage,
  AssistantMessage,
  SummaryMessage,
  ConversationEntry,
  AssistantContentBlock,
  TextContentBlock,
  ToolUseContentBlock,
} from "../types/index";

export function isUserMessage(message: BaseMessage): message is UserMessage {
  return message.type === "user";
}

export function isAssistantMessage(
  message: BaseMessage,
): message is AssistantMessage {
  return message.type === "assistant";
}

export function isSummaryMessage(entry: unknown): entry is SummaryMessage {
  return (
    typeof entry === "object" &&
    entry !== null &&
    "type" in entry &&
    entry.type === "summary"
  );
}

export function isConversationMessage(
  entry: ConversationEntry,
): entry is UserMessage | AssistantMessage {
  return (
    "uuid" in entry && (entry.type === "user" || entry.type === "assistant")
  );
}

export function isToolUseContent(
  content: AssistantContentBlock,
): content is ToolUseContentBlock {
  return content.type === "tool_use";
}

export function isTextContent(
  content: AssistantContentBlock,
): content is TextContentBlock {
  return content.type === "text";
}

export function hasToolResult(message: UserMessage): boolean {
  return (
    Array.isArray(message.message.content) &&
    message.message.content.some((block) => block.type === "tool_result")
  );
}
