# Claude Code Implementation Notes

## Overview

This document contains detailed implementation notes, patterns, and insights discovered during the reverse engineering analysis of Claude Code's data storage system.

## Architecture Patterns

### Local-First Data Storage

Claude Code implements a local-first architecture with several key characteristics:

1. **No Cloud Dependencies**: All conversation data stored locally in user's filesystem
2. **Offline Operation**: Full functionality without internet connectivity (except for LLM API calls)
3. **Privacy by Design**: User data never leaves local machine unless explicitly shared
4. **Fast Access**: Local storage enables instant conversation loading and searching

### Append-Only Message Storage

The conversation storage uses an append-only pattern:

```
Conversation File: session-uuid.jsonl
Line 1: {"type": "summary", ...}
Line 2: {"type": "user", "uuid": "msg-1", ...}
Line 3: {"type": "assistant", "uuid": "msg-2", "parentUuid": "msg-1", ...}
Line 4: {"type": "user", "uuid": "msg-3", "parentUuid": "msg-2", ...}
...
```

**Benefits:**

- Atomic writes prevent corruption
- Efficient for sequential access
- Easy to backup and sync
- Natural ordering preservation

**Trade-offs:**

- Updates require rewriting entire file
- Memory usage scales with conversation length
- No built-in indexing for random access

### Project-Based Organization

Projects are identified by their absolute filesystem paths, with encoding for safe filename usage:

```typescript
function encodeProjectPath(path: string): string {
  return path.replace(/\//g, "-");
}

function decodeProjectPath(encoded: string): string {
  return encoded.replace(/^-/, "/").replace(/-/g, "/");
}
```

**Examples:**

- `/Users/john/my-project` → `-Users-john-my-project`
- `/home/user/app` → `-home-user-app`

This encoding ensures:

- Valid filenames across operating systems
- Deterministic project directory names
- No conflicts with actual project names containing hyphens

## Message Threading Implementation

### UUID-Based Message Linking

Each message has a unique UUID and optional parent UUID, creating a directed graph:

```typescript
interface MessageGraph {
  nodes: Map<string, BaseMessage>;
  edges: Map<string, string[]>; // parentUuid -> childUuids[]
}

function buildMessageGraph(messages: BaseMessage[]): MessageGraph {
  const nodes = new Map();
  const edges = new Map();

  for (const message of messages) {
    nodes.set(message.uuid, message);

    if (message.parentUuid) {
      if (!edges.has(message.parentUuid)) {
        edges.set(message.parentUuid, []);
      }
      edges.get(message.parentUuid)!.push(message.uuid);
    }
  }

  return { nodes, edges };
}
```

### Conversation Branching

Claude Code supports conversation branching through the parent-child relationship:

```
Root Message
├── Assistant Response A
│   ├── User Follow-up A1
│   │   └── Assistant Response A1
│   └── User Follow-up A2  ← Branch
│       └── Assistant Response A2
└── User Follow-up B  ← Another branch
    └── Assistant Response B
```

The `isSidechain` boolean indicates whether a message is part of an alternate conversation path.

### Conversation State Tracking

Summary entries track the "active" or "latest" message in each conversation branch:

```typescript
interface ConversationState {
  summaries: SummaryMessage[];
  activeBranches: Set<string>; // leafUuids from summaries
}

function getActiveMessages(conversation: ConversationState): BaseMessage[] {
  // Returns the current "head" messages for each active branch
}
```

## Tool Integration Patterns

### Request-Response Cycle

Tool usage follows a specific pattern:

1. **Tool Request**: Assistant message with `tool_use` content block
2. **Tool Execution**: System executes tool (not stored as message)
3. **Tool Result**: User message with `tool_result` content and `toolUseResult` metadata
4. **Tool Processing**: Assistant processes results in next response

```typescript
// Tool request from assistant
{
  type: "assistant",
  message: {
    content: [{
      type: "tool_use",
      id: "toolu_123",
      name: "Read",
      input: { file_path: "/path/to/file" }
    }]
  }
}

// Tool result to assistant
{
  type: "user",
  message: {
    content: [{
      tool_use_id: "toolu_123",
      type: "tool_result",
      content: "file contents here"
    }]
  },
  toolUseResult: {
    type: "text",
    file: { filePath: "/path/to/file", content: "file contents here" }
  }
}
```

### Tool Permission System

The permission system uses glob patterns for granular control:

```typescript
interface PermissionMatcher {
  allow: RegExp[];
  deny: RegExp[];
}

function createPermissionMatcher(
  settings: PermissionSettings,
): PermissionMatcher {
  const allow = settings.allow.map((pattern) => globToRegex(pattern));
  const deny = settings.deny.map((pattern) => globToRegex(pattern));
  return { allow, deny };
}

function isToolAllowed(
  toolName: string,
  args: any,
  matcher: PermissionMatcher,
): boolean {
  const toolCall = `${toolName}(${JSON.stringify(args)})`;

  // Check deny patterns first
  if (matcher.deny.some((regex) => regex.test(toolCall))) {
    return false;
  }

  // Check allow patterns
  return matcher.allow.some((regex) => regex.test(toolCall));
}
```

**Example Patterns:**

- `Bash(find:*)` - Allow any find command
- `Read(/safe/path/*)` - Only allow reading from safe path
- `Bash(rm:*)` - Explicitly deny dangerous rm commands

## Cost and Usage Tracking

### Token-Based Cost Calculation

Each assistant message includes detailed token usage and cost calculation:

```typescript
interface CostCalculation {
  inputTokens: number;
  outputTokens: number;
  cacheCreationTokens: number;
  cacheReadTokens: number;
  model: string;
  costUSD: number;
}

function calculateCost(usage: TokenUsage, model: string): number {
  const rates = getModelRates(model);

  return (
    (usage.input_tokens * rates.input +
      usage.output_tokens * rates.output +
      usage.cache_creation_input_tokens * rates.cacheCreation +
      usage.cache_read_input_tokens * rates.cacheRead) /
    1_000_000
  ); // Convert from tokens to USD
}
```

### Performance Metrics

Response time tracking enables performance analysis:

```typescript
interface PerformanceMetrics {
  durationMs: number; // Total response time
  tokensPerSecond: number; // Output tokens / (duration / 1000)
  costEfficiency: number; // Value metric: output_tokens / costUSD
}

function calculateMetrics(message: AssistantMessage): PerformanceMetrics {
  const {
    durationMs,
    costUSD,
    message: { usage },
  } = message;

  return {
    durationMs,
    tokensPerSecond: (usage.output_tokens * 1000) / durationMs,
    costEfficiency: usage.output_tokens / costUSD,
  };
}
```

## Feature Flag System (Statsig)

### Cached Evaluation Storage

Statsig evaluations are cached locally to reduce API calls:

```typescript
interface CacheStrategy {
  // Cache file per user hash to avoid conflicts
  filename: string; // `statsig.cached.evaluations.${userHash}`

  // Timestamp-based invalidation
  lastModified: number;
  ttl: number; // Time to live in milliseconds

  // Evaluation data
  data: StatsigEvaluation;
}

function getCachedEvaluation(userHash: string): StatsigEvaluation | null {
  const cacheFile = `statsig.cached.evaluations.${userHash}`;
  const lastModFile = "statsig.last_modified_time.evaluations";

  // Check if cache is still valid
  const lastModified = readTimestamp(lastModFile);
  const cacheAge = Date.now() - lastModified;

  if (cacheAge > CACHE_TTL) {
    return null; // Cache expired
  }

  return readEvaluation(cacheFile);
}
```

### Dynamic Configuration

Feature flags enable runtime behavior changes:

```typescript
interface FeatureManager {
  gates: Map<string, boolean>;
  configs: Map<string, Record<string, any>>;
}

function initializeFeatures(evaluation: StatsigEvaluation): FeatureManager {
  const gates = new Map();
  const configs = new Map();

  // Process feature gates
  for (const [id, gate] of Object.entries(evaluation.data.feature_gates)) {
    gates.set(gate.name, gate.value);
  }

  // Process dynamic configs
  for (const [id, config] of Object.entries(evaluation.data.dynamic_configs)) {
    configs.set(config.name, config.value);
  }

  return { gates, configs };
}
```

## Todo System Implementation

### Session-Based Todo Storage

Todos are stored per conversation session rather than globally:

```typescript
interface TodoManager {
  sessionTodos: Map<string, TodoItem[]>; // sessionId -> todos
}

function loadTodosForSession(sessionId: string): TodoItem[] {
  const todoFile = `.claude/todos/${sessionId}.json`;

  if (fs.existsSync(todoFile)) {
    return JSON.parse(fs.readFileSync(todoFile, "utf8"));
  }

  return [];
}

function saveTodosForSession(sessionId: string, todos: TodoItem[]): void {
  const todoFile = `.claude/todos/${sessionId}.json`;
  fs.writeFileSync(todoFile, JSON.stringify(todos, null, 2));
}
```

### Todo State Transitions

Todo items follow a defined state machine:

```
pending → in_progress → completed
   ↓           ↓           ↓
cancelled   cancelled   (final)
```

```typescript
function isValidTransition(from: TodoStatus, to: TodoStatus): boolean {
  const validTransitions: Record<TodoStatus, TodoStatus[]> = {
    pending: ["in_progress", "cancelled"],
    in_progress: ["completed", "cancelled"],
    completed: [], // Final state
    cancelled: [], // Final state
  };

  return validTransitions[from].includes(to);
}
```

## Data Integrity and Validation

### Message Validation Rules

```typescript
interface ValidationRule<T> {
  name: string;
  validate: (item: T) => ValidationResult;
}

interface ValidationResult {
  valid: boolean;
  errors: string[];
}

const messageValidationRules: ValidationRule<BaseMessage>[] = [
  {
    name: "valid-uuid",
    validate: (msg) => ({
      valid: isValidUUID(msg.uuid),
      errors: isValidUUID(msg.uuid) ? [] : ["Invalid UUID format"]
    })
  },
  {
    name: "valid-parent-reference",
    validate: (msg) => {
      if (msg.parentUuid === null) return { valid: true, errors: [] };

      // Parent must exist in conversation
      const parentExists = /* check if parent exists */;
      return {
        valid: parentExists,
        errors: parentExists ? [] : ["Parent message not found"]
      };
    }
  },
  {
    name: "chronological-ordering",
    validate: (msg) => {
      // Messages must be chronologically ordered relative to parent
      const parentTimestamp = /* get parent timestamp */;
      const isAfterParent = new Date(msg.timestamp) > new Date(parentTimestamp);

      return {
        valid: isAfterParent,
        errors: isAfterParent ? [] : ["Message timestamp before parent"]
      };
    }
  }
];
```

### Conversation Consistency Checks

```typescript
function validateConversation(messages: BaseMessage[]): ValidationResult {
  const errors: string[] = [];

  // Check for orphaned messages (invalid parent references)
  const messageIds = new Set(messages.map((m) => m.uuid));
  for (const msg of messages) {
    if (msg.parentUuid && !messageIds.has(msg.parentUuid)) {
      errors.push(
        `Orphaned message: ${msg.uuid} references missing parent ${msg.parentUuid}`,
      );
    }
  }

  // Check for duplicate UUIDs
  const uuidCounts = new Map<string, number>();
  for (const msg of messages) {
    uuidCounts.set(msg.uuid, (uuidCounts.get(msg.uuid) || 0) + 1);
  }

  for (const [uuid, count] of uuidCounts) {
    if (count > 1) {
      errors.push(`Duplicate UUID: ${uuid} appears ${count} times`);
    }
  }

  // Check for circular references
  if (hasCircularReferences(messages)) {
    errors.push("Circular reference detected in message chain");
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}
```

## Performance Optimizations

### Lazy Loading Strategies

```typescript
interface ConversationLoader {
  // Load only summary for quick overview
  loadSummary(conversationId: string): Promise<SummaryMessage[]>;

  // Load messages in chunks for large conversations
  loadMessages(
    conversationId: string,
    offset: number,
    limit: number,
  ): Promise<BaseMessage[]>;

  // Stream messages for real-time processing
  streamMessages(conversationId: string): AsyncIterable<BaseMessage>;
}

class LazyConversationLoader implements ConversationLoader {
  async loadSummary(conversationId: string): Promise<SummaryMessage[]> {
    const file = `.claude/projects/${project}/${conversationId}.jsonl`;
    const summaries: SummaryMessage[] = [];

    // Read only first few lines for summaries
    const rl = readline.createInterface({
      input: fs.createReadStream(file),
    });

    for await (const line of rl) {
      const entry = JSON.parse(line);
      if (entry.type === "summary") {
        summaries.push(entry);
      } else {
        break; // Found first message, stop reading
      }
    }

    return summaries;
  }
}
```

### Memory Management

```typescript
interface ConversationCache {
  maxSize: number;
  cache: Map<string, CacheEntry>;
  lru: LRUList;
}

interface CacheEntry {
  conversationId: string;
  messages: BaseMessage[];
  lastAccessed: number;
  size: number; // Memory footprint estimate
}

function evictLRU(cache: ConversationCache): void {
  while (cache.cache.size >= cache.maxSize) {
    const oldestId = cache.lru.removeLast();
    const entry = cache.cache.get(oldestId);

    if (entry) {
      cache.cache.delete(oldestId);
      console.log(`Evicted conversation ${oldestId} (${entry.size} bytes)`);
    }
  }
}
```

## Security Considerations

### Path Sanitization

```typescript
function sanitizePath(userPath: string): string {
  // Resolve to absolute path
  const resolved = path.resolve(userPath);

  // Ensure path is within allowed directories
  const allowedRoots = [os.homedir(), "/tmp", process.cwd()];

  const isAllowed = allowedRoots.some((root) =>
    resolved.startsWith(path.resolve(root)),
  );

  if (!isAllowed) {
    throw new Error(`Path ${resolved} is outside allowed directories`);
  }

  return resolved;
}
```

### Tool Execution Sandboxing

```typescript
interface SandboxConfig {
  allowedCommands: string[];
  timeoutMs: number;
  maxMemoryMB: number;
  workingDirectory: string;
}

async function executeBashCommand(
  command: string,
  config: SandboxConfig,
): Promise<ToolUseResult> {
  // Validate command against whitelist
  const commandName = command.split(" ")[0];
  if (!config.allowedCommands.includes(commandName)) {
    throw new Error(`Command ${commandName} not allowed`);
  }

  // Execute with timeout and resource limits
  const result = await spawn(command, {
    timeout: config.timeoutMs,
    cwd: config.workingDirectory,
    maxBuffer: config.maxMemoryMB * 1024 * 1024,
  });

  return {
    stdout: result.stdout,
    stderr: result.stderr,
    interrupted: result.killed,
  };
}
```

## Migration Strategies

### Version Migration Framework

```typescript
interface MigrationPlan {
  targetVersion: string;
  migrations: Migration[];
}

interface Migration {
  fromVersion: string;
  toVersion: string;
  description: string;
  migrate: (data: any) => any;
  rollback: (data: any) => any;
}

async function migrateConversation(
  conversationPath: string,
  plan: MigrationPlan,
): Promise<void> {
  const backup = `${conversationPath}.backup`;

  try {
    // Create backup
    await fs.copyFile(conversationPath, backup);

    // Apply migrations
    let data = await readConversation(conversationPath);

    for (const migration of plan.migrations) {
      console.log(`Applying migration: ${migration.description}`);
      data = migration.migrate(data);
    }

    // Write migrated data
    await writeConversation(conversationPath, data);

    // Remove backup on success
    await fs.unlink(backup);
  } catch (error) {
    // Restore backup on failure
    if (await fs.exists(backup)) {
      await fs.copyFile(backup, conversationPath);
      await fs.unlink(backup);
    }
    throw error;
  }
}
```

These implementation notes provide deep insights into the engineering decisions and patterns used in Claude Code's data storage system, enabling developers to build compatible tools and extensions.
