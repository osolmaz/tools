# Claude Code Data Storage Analysis

## Overview

This document provides a comprehensive reverse engineering analysis of how Claude Code stores its data, conversations, and configuration. The analysis is based on examining the `.claude.json` file and `.claude/` directory structure.

## Directory Structure

### Root Level Files

- `.claude.json` - Main configuration and global state file (924KB)
- `.claude/` - Primary data directory containing all persistent storage

### .claude Directory Structure

```
.claude/
├── ide/
│   └── 18022.lock
├── projects/
│   ├── -Users-onur-projects-alman-alman-research/
│   ├── -Users-onur-projects-claude-code-pr-autodoc-action/
│   ├── -Users-onur-projects-horse/
│   ├── -Users-onur-tc-backend-api/
│   ├── -Users-onur-tc-claude-code-pr-autodoc-action/
│   ├── -Users-onur-tc-claude-code-sandbox/
│   ├── -Users-onur-tc-frontend/
│   ├── -Users-onur-tc-JSON-DOC/
│   └── -Users-onur-tc-JSON-DOC-typescript/
├── settings.local.json
├── statsig/
│   ├── statsig.cached.evaluations.*
│   ├── statsig.last_modified_time.evaluations
│   └── statsig.session_id.*
└── todos/
    └── [UUID].json files (60+ individual todo files)
```

## Main Configuration File (.claude.json)

### Top-Level Structure

The `.claude.json` file contains global application state and configuration:

```json
{
  "numStartups": 69,
  "autoUpdaterStatus": "enabled",
  "verbose": true,
  "tipsHistory": {
    "terminal-setup": 8,
    "shift-enter": 53,
    "memory-command": 43,
    "theme-command": 55,
    "prompt-queue": 58,
    "enter-to-steer-in-relatime": 57,
    "todo-list": 60,
    "ide-hotkey": 33,
    "git-worktrees": 52
  },
  "userID": "a6e0588335b350a8373cec1f126acb4d5a9d05c039deac5e201746f60d33e44f",
  "hasCompletedOnboarding": true,
  "lastOnboardingVersion": "1.0.3",
  "projects": {
    /* Project configurations */
  }
}
```

### Project Configuration Model

Each project in the `projects` object follows this structure:

```typescript
interface ProjectConfig {
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

### Key Fields Explained

- **numStartups**: Counter tracking application startup count
- **autoUpdaterStatus**: Auto-update configuration ("enabled"/"disabled")
- **verbose**: Debug logging flag
- **tipsHistory**: Tracks display count for various UI tips/tutorials
- **userID**: SHA-256 hash identifier for the user
- **hasCompletedOnboarding**: Boolean flag for onboarding completion
- **lastOnboardingVersion**: Version string for onboarding completion
- **projects**: Map of project paths to their configurations

## Project Storage Structure

### Project Directory Naming

Project directories use a path-encoding scheme where `/` characters are replaced with `-`:

- `/Users/onur/tc/backend-api` → `-Users-onur-tc-backend-api`

### Conversation Files (JSONL Format)

Each conversation is stored as a `.jsonl` file with the conversation's UUID as the filename.

#### Conversation File Structure

Conversations use JSON Lines format with each line representing either:

1. Summary metadata
2. Individual messages in the conversation thread

#### Summary Entries

```json
{
  "type": "summary",
  "summary": "Human-readable conversation summary",
  "leafUuid": "uuid-of-last-message"
}
```

#### Message Entries

All messages share common fields:

```typescript
interface BaseMessage {
  parentUuid: string | null;
  isSidechain: boolean;
  userType: "external";
  cwd: string;
  sessionId: string;
  version: string;
  uuid: string;
  timestamp: string; // ISO 8601 format
}
```

#### User Messages

```typescript
interface UserMessage extends BaseMessage {
  type: "user";
  message: {
    role: "user";
    content: string | ComplexContent[];
  };
  isMeta?: boolean; // For system-generated messages
}
```

#### Assistant Messages

```typescript
interface AssistantMessage extends BaseMessage {
  type: "assistant";
  message: {
    id: string;
    type: "message";
    role: "assistant";
    model: string; // e.g., "claude-opus-4-20250514"
    content: ContentBlock[];
    stop_reason: string;
    stop_sequence: string | null;
    usage: {
      input_tokens: number;
      cache_creation_input_tokens: number;
      cache_read_input_tokens: number;
      output_tokens: number;
      service_tier: string;
    };
  };
  costUSD: number;
  durationMs: number;
}
```

#### Content Types

Assistant messages can contain various content types:

```typescript
type ContentBlock =
  | { type: "text"; text: string }
  | {
      type: "tool_use";
      id: string;
      name: string;
      input: Record<string, any>;
    };
```

#### Special Message Types

- **Meta Messages**: `isMeta: true` for system-generated context messages
- **Command Messages**: Messages containing `<command-name>`, `<command-message>`, and `<command-args>` for CLI interactions
- **Command Output**: Messages with `<local-command-stdout>` containing command results

## Settings and Configuration

### Local Settings (.claude/settings.local.json)

```json
{
  "permissions": {
    "allow": ["Bash(find:*)", "Bash(ls:*)", "Bash(grep:*)", "Bash(mkdir:*)"],
    "deny": []
  }
}
```

This file manages tool permissions with granular control over allowed and denied operations.

## Todo System

### Todo Storage Structure

Todos are stored as individual JSON files in `.claude/todos/` with UUID filenames.

#### Todo File Structure

```typescript
interface TodoFile {
  content: string;
  status: "pending" | "in_progress" | "completed";
  priority: "high" | "medium" | "low";
  id: string;
}
[];
```

Example todo file:

```json
[
  {
    "content": "Find the Zenochat input box component and analyze the flickering issue",
    "status": "completed",
    "priority": "high",
    "id": "1"
  },
  {
    "content": "Identify what causes the 'Ask anything' text to flicker during loading",
    "status": "completed",
    "priority": "high",
    "id": "2"
  }
]
```

## Feature Flags and Analytics

### Statsig Integration

The `.claude/statsig/` directory contains cached feature flag evaluations and session tracking:

#### Files:

- `statsig.cached.evaluations.*` - Cached feature flag states
- `statsig.last_modified_time.evaluations` - Timestamp for cache invalidation
- `statsig.session_id.*` - Session tracking files
- `statsig.stable_id.*` - Stable user identifier

#### Evaluation Structure

```typescript
interface StatsigEvaluation {
  source: "Network";
  data: {
    feature_gates: Record<string, FeatureGate>;
    dynamic_configs: Record<string, DynamicConfig>;
    layer_configs: Record<string, any>;
    // ... additional metadata
  };
  receivedAt: number;
  stableID: string;
  fullUserHash: string;
}
```

## IDE Integration

### IDE Lock File (.claude/ide/18022.lock)

```json
{
  "pid": 76135,
  "workspaceFolders": ["/Users/onur/tc/backend-api"],
  "ideName": "Cursor",
  "transport": "ws"
}
```

This file tracks active IDE connections and workspace state.

## Data Models Summary

### Core Entities

1. **User Identity**

   - SHA-256 hashed userID for privacy
   - Stable ID for analytics correlation
   - Session tracking across app restarts

2. **Project Management**

   - Path-based project identification
   - Per-project tool permissions
   - Conversation history preservation
   - Context and configuration storage

3. **Conversation Threading**

   - UUID-based message identification
   - Parent-child relationship tracking
   - Branch/sidechain support
   - Message metadata (timestamps, costs, duration)

4. **Tool Usage Tracking**

   - Granular permission system
   - Usage analytics and optimization
   - Error tracking and debugging

5. **Feature Management**
   - A/B testing through Statsig
   - Dynamic configuration updates
   - User segmentation and targeting

## Storage Characteristics

### Performance Optimizations

- **JSONL Format**: Append-only conversation storage for efficient writes
- **File-per-conversation**: Parallel access and reduced lock contention
- **Cached Evaluations**: Reduced network calls for feature flags
- **Separate Todo Storage**: Independent todo management per session

### Data Integrity

- **UUID-based identification**: Prevents ID collisions across distributed usage
- **Immutable message history**: Append-only conversation logs
- **Version tracking**: Schema evolution through version fields
- **Timestamp precision**: Millisecond-accurate event ordering

### Privacy Considerations

- **Hashed user identifiers**: No PII in primary identifiers
- **Local-first storage**: All data stored locally, not in cloud
- **Granular permissions**: User controls over tool access
- **Session isolation**: Separate tracking per usage session

## Technical Implementation Notes

### Message Threading

- Conversations form directed acyclic graphs (DAGs) through parent-child relationships
- Support for conversation branching and merging
- Efficient traversal through UUID-based linking

### Cost Tracking

- Per-message cost calculation in USD
- Token usage breakdown (input, output, cache)
- Performance metrics (duration, model used)
- Aggregatable for usage analytics

### Tool Integration

- Dynamic tool permission management
- Command execution tracking
- File system operation logging
- Integration with external services (GitHub, etc.)

### Extensibility

- Schema versioning for backwards compatibility
- Plugin-based tool architecture
- Configurable feature flags
- Modular storage components

This analysis reveals a sophisticated data storage system optimized for local-first operation, detailed conversation tracking, and extensible tool integration while maintaining user privacy and system performance.
