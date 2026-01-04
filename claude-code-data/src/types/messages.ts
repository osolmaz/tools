/**
 * Message type definitions for Claude Code conversations
 */

import type { BaseMessage, TokenUsage, StopReason, TodoItem } from "./base";

// Summary Message
export interface SummaryMessage {
  type: "summary";
  summary: string;
  leafUuid: string;
}

// User Message Types
export interface UserMessage extends BaseMessage {
  type: "user";
  message: UserMessageContent;
  isMeta?: boolean;
  toolUseResult?: ToolUseResult;
}

export interface UserMessageContent {
  role: "user";
  content: string | UserContentBlock[];
}

export type UserContentBlock = ToolResultBlock;

export interface ToolResultBlock {
  tool_use_id: string;
  type: "tool_result";
  content: string | ToolResultContent[];
  is_error?: boolean;
}

export interface ToolResultContent {
  type: "text";
  text: string;
}

// Assistant Message Types
export interface AssistantMessage extends BaseMessage {
  type: "assistant";
  message: ClaudeAPIResponse;
  costUSD?: number;
  durationMs?: number;
  requestId?: string; // Some messages have this instead
}

export interface ClaudeAPIResponse {
  id: string;
  type: "message";
  role: "assistant";
  model: string;
  content: AssistantContentBlock[];
  stop_reason: StopReason;
  stop_sequence: string | null;
  usage: TokenUsage;
}

export type AssistantContentBlock = TextContentBlock | ToolUseContentBlock;

export interface TextContentBlock {
  type: "text";
  text: string;
}

export interface ToolUseContentBlock {
  type: "tool_use";
  id: string;
  name: string;
  input: Record<string, any>;
}

// Tool Use Result Types
export interface ToolUseResult {
  // Command execution results
  stdout?: string;
  stderr?: string;
  interrupted?: boolean;
  isImage?: boolean;
  sandbox?: boolean;

  // File operation results
  type?: "text" | "image" | "binary";
  file?: FileResult;

  // Todo operation results
  oldTodos?: TodoItem[];
  newTodos?: TodoItem[];
}

export interface FileResult {
  filePath: string;
  content: string;
}

// Union type for all message types that can appear in a conversation
export type ConversationMessage = UserMessage | AssistantMessage;
export type ConversationEntry = SummaryMessage | ConversationMessage;
