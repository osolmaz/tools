/**
 * Base types and enums for Claude Code data structures
 */

export type MessageType = "user" | "assistant" | "summary";

export type TodoStatus = "pending" | "in_progress" | "completed" | "cancelled";
export type TodoPriority = "high" | "medium" | "low";

export type StopReason =
  | "end_turn"
  | "tool_use"
  | "max_tokens"
  | "stop_sequence";
export type ServiceTier = "standard" | "premium";

export interface BaseMessage {
  // Core identification
  uuid: string;
  parentUuid: string | null;

  // Message metadata
  type: MessageType;
  timestamp: string; // ISO 8601

  // Session context
  sessionId: string;
  userType: "external";
  version: string; // Claude Code version

  // Execution context
  cwd: string;
  isSidechain: boolean;
}

export interface TokenUsage {
  input_tokens: number;
  cache_creation_input_tokens: number;
  cache_read_input_tokens: number;
  output_tokens: number;
  service_tier: ServiceTier;
}

export interface TodoItem {
  id: string;
  content: string;
  status: TodoStatus;
  priority: TodoPriority;
}
