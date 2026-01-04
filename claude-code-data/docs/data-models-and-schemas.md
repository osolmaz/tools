# Claude Code Data Models and Schemas

## Overview

This document provides comprehensive TypeScript interfaces and schemas for all data structures used by Claude Code. These models can be used for type-safe parsing, validation, and tooling development.

## Core Configuration Models

### Main Configuration (.claude.json)

```typescript
interface ClaudeConfiguration {
  // Application metadata
  numStartups: number;
  autoUpdaterStatus: "enabled" | "disabled";
  verbose: boolean;

  // User identity and onboarding
  userID: string; // SHA-256 hash
  hasCompletedOnboarding: boolean;
  lastOnboardingVersion: string; // Semantic version

  // UI state tracking
  tipsHistory: Record<string, number>;

  // Project configurations
  projects: Record<string, ProjectConfiguration>;
}

interface TipsHistory {
  "terminal-setup": number;
  "shift-enter": number;
  "memory-command": number;
  "theme-command": number;
  "prompt-queue": number;
  "enter-to-steer-in-relatime": number;
  "todo-list": number;
  "ide-hotkey": number;
  "git-worktrees": number;
  [key: string]: number; // Extensible for future tips
}
```

### Project Configuration

```typescript
interface ProjectConfiguration {
  allowedTools: string[];
  context: Record<string, any>;
  history: ConversationHistoryItem[];
}

interface ConversationHistoryItem {
  display: string;
  pastedContents: Record<string, PastedContent>;
}

interface PastedContent {
  id: number;
  type: "text";
  content: string;
}
```

## Conversation Models

### Base Message Structure

```typescript
interface BaseMessage {
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

type MessageType = "user" | "assistant" | "summary";
```

### Summary Messages

```typescript
interface SummaryMessage {
  type: "summary";
  summary: string;
  leafUuid: string;
}
```

### User Messages

```typescript
interface UserMessage extends BaseMessage {
  type: "user";
  message: UserMessageContent;
  isMeta?: boolean;
  toolUseResult?: ToolUseResult;
}

interface UserMessageContent {
  role: "user";
  content: string | UserContentBlock[];
}

type UserContentBlock = ToolResultBlock;

interface ToolResultBlock {
  tool_use_id: string;
  type: "tool_result";
  content: string | ToolResultContent[];
  is_error?: boolean;
}

interface ToolResultContent {
  type: "text";
  text: string;
}
```

### Assistant Messages

```typescript
interface AssistantMessage extends BaseMessage {
  type: "assistant";
  message: ClaudeAPIResponse;
  costUSD: number;
  durationMs: number;
}

interface ClaudeAPIResponse {
  id: string;
  type: "message";
  role: "assistant";
  model: string;
  content: AssistantContentBlock[];
  stop_reason: StopReason;
  stop_sequence: string | null;
  usage: TokenUsage;
}

type StopReason = "end_turn" | "tool_use" | "max_tokens" | "stop_sequence";

interface TokenUsage {
  input_tokens: number;
  cache_creation_input_tokens: number;
  cache_read_input_tokens: number;
  output_tokens: number;
  service_tier: "standard" | "premium";
}
```

### Assistant Content Types

```typescript
type AssistantContentBlock = TextContentBlock | ToolUseContentBlock;

interface TextContentBlock {
  type: "text";
  text: string;
}

interface ToolUseContentBlock {
  type: "tool_use";
  id: string;
  name: string;
  input: ToolInput;
}

// Tool-specific input types
type ToolInput =
  | BashToolInput
  | ReadToolInput
  | EditToolInput
  | WriteToolInput
  | TodoToolInput
  | Record<string, any>; // Generic fallback

interface BashToolInput {
  command: string;
  description?: string;
  timeout?: number;
}

interface ReadToolInput {
  file_path: string;
  limit?: number;
  offset?: number;
}

interface EditToolInput {
  file_path: string;
  old_string: string;
  new_string: string;
  replace_all?: boolean;
}

interface WriteToolInput {
  file_path: string;
  content: string;
}

interface TodoToolInput {
  todos: TodoItem[];
}
```

## Tool Use Result Models

```typescript
interface ToolUseResult {
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

interface FileResult {
  filePath: string;
  content: string;
}
```

## Todo System Models

```typescript
interface TodoItem {
  id: string;
  content: string;
  status: TodoStatus;
  priority: TodoPriority;
}

type TodoStatus = "pending" | "in_progress" | "completed" | "cancelled";
type TodoPriority = "high" | "medium" | "low";

// Todo file format (array of TodoItems)
type TodoFile = TodoItem[];
```

## Settings and Permissions

```typescript
interface LocalSettings {
  permissions: PermissionSettings;
}

interface PermissionSettings {
  allow: string[]; // Permission patterns like "Bash(find:*)"
  deny: string[]; // Denial patterns
}

// Permission pattern examples:
// "Bash(find:*)" - Allow find commands
// "Bash(ls:*)" - Allow ls commands
// "Bash(rm:*)" - Allow rm commands (dangerous)
// "Read(/safe/path/*)" - Allow reading from safe paths only
```

## IDE Integration Models

```typescript
interface IDELockFile {
  pid: number;
  workspaceFolders: string[];
  ideName: string; // "Cursor", "VSCode", etc.
  transport: "ws" | "http"; // Communication protocol
}
```

## Analytics and Feature Flags (Statsig)

```typescript
interface StatsigEvaluation {
  source: "Network" | "Cache";
  data: StatsigData;
  receivedAt: number; // Unix timestamp
  stableID: string;
  fullUserHash: string;
}

interface StatsigData {
  feature_gates: Record<string, FeatureGate>;
  dynamic_configs: Record<string, DynamicConfig>;
  layer_configs: Record<string, LayerConfig>;
  sdkParams: Record<string, any>;
  has_updates: boolean;
  generator: string;
  time: number;
  company_lcut: number;
  evaluated_keys: EvaluatedKeys;
  hash_used: string;
  derived_fields: DerivedFields;
  hashed_sdk_key_used: string;
  can_record_session: boolean;
  recording_blocked: boolean;
  session_recording_rate: number;
  auto_capture_settings: AutoCaptureSettings;
  target_app_used: string;
  full_checksum: string;
}

interface FeatureGate {
  name: string;
  value: boolean;
  rule_id: string;
  id_type: string;
  secondary_exposures: any[];
}

interface DynamicConfig {
  name: string;
  value: Record<string, any>;
  rule_id: string;
  group: string;
  is_device_based: boolean;
  passed?: boolean;
  id_type: string;
  is_experiment_active?: boolean;
  is_user_in_experiment?: boolean;
  secondary_exposures: any[];
  group_name?: string;
}

interface LayerConfig {
  // Layer-specific configuration
  [key: string]: any;
}

interface EvaluatedKeys {
  userID: string;
  stableID: string;
  customIDs: Record<string, string>;
}

interface DerivedFields {
  ip: string;
  country: string;
  appVersion: string;
  app_version: string;
  browserName: string;
  browserVersion: string;
  osName: string;
  osVersion: string;
  browser_name: string;
  browser_version: string;
  os_name: string;
  os_version: string;
}

interface AutoCaptureSettings {
  disabled_events: Record<string, any>;
}
```

## Validation Schemas

### JSON Schema Definitions

```typescript
// For runtime validation using libraries like Ajv
const MessageSchema = {
  type: "object",
  properties: {
    uuid: { type: "string", format: "uuid" },
    parentUuid: { type: ["string", "null"], format: "uuid" },
    type: { enum: ["user", "assistant", "summary"] },
    timestamp: { type: "string", format: "date-time" },
    sessionId: { type: "string", format: "uuid" },
    userType: { enum: ["external"] },
    version: { type: "string", pattern: "^\\d+\\.\\d+\\.\\d+$" },
    cwd: { type: "string" },
    isSidechain: { type: "boolean" },
  },
  required: [
    "uuid",
    "type",
    "timestamp",
    "sessionId",
    "userType",
    "version",
    "cwd",
    "isSidechain",
  ],
};

const UserMessageSchema = {
  allOf: [
    { $ref: "#/definitions/Message" },
    {
      type: "object",
      properties: {
        type: { const: "user" },
        message: {
          type: "object",
          properties: {
            role: { const: "user" },
            content: {
              oneOf: [
                { type: "string" },
                {
                  type: "array",
                  items: { $ref: "#/definitions/UserContentBlock" },
                },
              ],
            },
          },
          required: ["role", "content"],
        },
        isMeta: { type: "boolean" },
        toolUseResult: { $ref: "#/definitions/ToolUseResult" },
      },
      required: ["message"],
    },
  ],
};
```

## Type Guards and Utilities

```typescript
// Type guard functions for runtime type checking
function isUserMessage(message: BaseMessage): message is UserMessage {
  return message.type === "user";
}

function isAssistantMessage(message: BaseMessage): message is AssistantMessage {
  return message.type === "assistant";
}

function isSummaryMessage(entry: any): entry is SummaryMessage {
  return entry.type === "summary";
}

function isToolUseContent(
  content: AssistantContentBlock,
): content is ToolUseContentBlock {
  return content.type === "tool_use";
}

function isTextContent(
  content: AssistantContentBlock,
): content is TextContentBlock {
  return content.type === "text";
}

// Utility functions
function getConversationRoot(messages: BaseMessage[]): BaseMessage | null {
  return messages.find((msg) => msg.parentUuid === null) || null;
}

function getMessageChildren(
  messages: BaseMessage[],
  parentUuid: string,
): BaseMessage[] {
  return messages.filter((msg) => msg.parentUuid === parentUuid);
}

function buildConversationTree(messages: BaseMessage[]): ConversationNode {
  // Implementation for building conversation tree structure
}

interface ConversationNode {
  message: BaseMessage;
  children: ConversationNode[];
}
```

## Enums and Constants

```typescript
// Claude model identifiers
enum ClaudeModel {
  OPUS_4 = "claude-opus-4-20250514",
  SONNET_4 = "claude-sonnet-4-20250514",
  SONNET_3_7 = "claude-3-7-sonnet-20250219",
  HAIKU_3_5 = "claude-3-5-haiku-20241022",
}

// Tool names
enum ToolName {
  BASH = "Bash",
  READ = "Read",
  EDIT = "Edit",
  WRITE = "Write",
  GLOB = "Glob",
  GREP = "Grep",
  LS = "LS",
  TODO_READ = "TodoRead",
  TODO_WRITE = "TodoWrite",
  MULTI_EDIT = "MultiEdit",
  NOTEBOOK_READ = "NotebookRead",
  NOTEBOOK_EDIT = "NotebookEdit",
  WEB_FETCH = "WebFetch",
  WEB_SEARCH = "WebSearch",
  TASK = "Task",
}

// File extensions for different content types
const SUPPORTED_EXTENSIONS = {
  TEXT: [".txt", ".md", ".json", ".yaml", ".yml", ".toml"],
  CODE: [
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".cpp",
    ".c",
    ".h",
    ".rs",
    ".go",
    ".php",
    ".rb",
    ".swift",
  ],
  CONFIG: [".env", ".gitignore", ".dockerignore", ".editorconfig"],
  NOTEBOOK: [".ipynb"],
  IMAGE: [".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg"],
  BINARY: [".pdf", ".zip", ".tar", ".gz", ".exe", ".dmg"],
} as const;
```

## Migration and Versioning

```typescript
interface VersionMigration {
  fromVersion: string;
  toVersion: string;
  migrate: (data: any) => any;
}

// Example migration for schema changes
const migrations: VersionMigration[] = [
  {
    fromVersion: "1.0.2",
    toVersion: "1.0.3",
    migrate: (message: any) => {
      // Add new fields, transform existing data
      return {
        ...message,
        newField: "defaultValue",
      };
    },
  },
];

function migrateMessage(message: any, targetVersion: string): BaseMessage {
  // Apply migrations in sequence
  let migrated = message;
  for (const migration of migrations) {
    if (shouldApplyMigration(message.version, migration)) {
      migrated = migration.migrate(migrated);
    }
  }
  return migrated;
}
```

## Error Types

```typescript
interface ConversationError extends Error {
  code: ConversationErrorCode;
  context?: Record<string, any>;
}

enum ConversationErrorCode {
  INVALID_UUID = "INVALID_UUID",
  ORPHANED_MESSAGE = "ORPHANED_MESSAGE",
  DUPLICATE_UUID = "DUPLICATE_UUID",
  INVALID_TIMESTAMP = "INVALID_TIMESTAMP",
  MISSING_TOOL_RESULT = "MISSING_TOOL_RESULT",
  CIRCULAR_REFERENCE = "CIRCULAR_REFERENCE",
  UNSUPPORTED_VERSION = "UNSUPPORTED_VERSION",
  CORRUPTED_DATA = "CORRUPTED_DATA",
}
```

## Export/Import Models

```typescript
interface ConversationExport {
  metadata: ExportMetadata;
  conversation: ConversationData;
}

interface ExportMetadata {
  exportVersion: string;
  sourceVersion: string;
  exportedAt: string;
  conversationId: string;
  projectPath: string;
  messageCount: number;
}

interface ConversationData {
  summaries: SummaryMessage[];
  messages: (UserMessage | AssistantMessage)[];
}

// For bulk operations
interface BulkExport {
  metadata: BulkExportMetadata;
  conversations: Record<string, ConversationData>;
}

interface BulkExportMetadata {
  exportVersion: string;
  sourceVersion: string;
  exportedAt: string;
  projectPaths: string[];
  conversationCount: number;
  totalMessageCount: number;
}
```

These comprehensive data models provide a complete type-safe foundation for working with Claude Code's data structures, enabling robust tooling, analysis, and integration development.
