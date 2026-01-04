# Claude Code Data

This repository contains comprehensive reverse engineering analysis of Claude Code's data storage system **and** a TypeScript library for parsing and analyzing Claude Code conversation files.

## Repository Contents

### 📚 Documentation (Reverse Engineering Analysis)
- **[Storage Analysis](docs/claude-code-data-storage-analysis.md)** - High-level overview of Claude Code's data storage
- **[Conversation Format](docs/conversation-format-specification.md)** - Detailed JSONL conversation format specification
- **[Data Models](docs/data-models-and-schemas.md)** - Complete TypeScript interfaces and schemas
- **[Implementation Notes](docs/implementation-notes.md)** - Technical patterns and engineering insights

### 💻 TypeScript Library (Parser & Analyzer)
- Type-safe parsing of Claude Code conversation files
- Comprehensive analysis tools for conversations
- 34 passing tests with real conversation data
- Modern TypeScript with Vite and Vitest

## Quick Start - Understanding Claude Code Data

Claude Code stores its data in a `.claude/` directory:

```
.claude/
├── settings.local.json                 # Local permissions and settings
├── projects/                           # Project-specific data
│   └── {encoded-project-path}/         # Project directory
│       └── {conversation-uuid}.jsonl   # Individual conversations
├── todos/                              # Session-based todo lists
│   └── {session-uuid}.json             # Todo items per session
├── statsig/                            # Feature flags and analytics
│   └── statsig.cached.evaluations.*    # Cached feature evaluations
└── ide/                                # IDE integration
    └── {port}.lock                     # Active IDE connection info
```

Each conversation is stored as a JSON Lines file:

```jsonl
{"type":"summary","summary":"Conversation Title","leafUuid":"last-message-id"}
{"type":"user","uuid":"msg-1","parentUuid":null,"message":{"role":"user","content":"Hello"},"timestamp":"2025-06-05T10:00:00.000Z"}
{"type":"assistant","uuid":"msg-2","parentUuid":"msg-1","message":{"role":"assistant","content":[{"type":"text","text":"Hi there!"}]},"costUSD":0.001,"durationMs":1500}
```

## TypeScript Library Usage

### Installation

```bash
npm install
```

### Basic Parsing

```typescript
import { parseConversation } from "claude-code-data";

const conversation = await parseConversation("./conversation.jsonl");

console.log(`Found ${conversation.summaries.length} summaries`);
console.log(`Found ${conversation.messages.length} messages`);
```

### Analyzing Conversations

```typescript
import { parseConversation, calculateConversationStats } from "claude-code-data";

const conversation = await parseConversation("./conversation.jsonl");
const stats = calculateConversationStats(conversation);

console.log(`Total cost: $${stats.totalCostUSD.toFixed(4)}`);
console.log(`Total tokens: ${stats.totalTokens.input + stats.totalTokens.output}`);
console.log(`Average response time: ${stats.averageResponseTimeMs.toFixed(0)}ms`);
```

### Type Guards

```typescript
import { isUserMessage, isAssistantMessage, hasToolResult } from "claude-code-data";

for (const message of conversation.messages) {
  if (isUserMessage(message)) {
    console.log("User:", message.message.content);
  } else if (isAssistantMessage(message)) {
    console.log("Assistant:", message.message.content[0].text);
    console.log("Cost:", message.costUSD);
  }
}
```

### Building Conversation Trees

```typescript
import { buildConversationTree } from "claude-code-data";

const tree = buildConversationTree(conversation.messages);
// Tree structure with parent-child relationships
```

## Development

```bash
# Run tests
npm test

# Run tests with UI
npm run test:ui

# Build TypeScript library
npm run build

# Type checking
npm run typecheck
```

## Key Features

### 📖 Parser Library
- **Type-Safe**: Complete TypeScript interfaces for all Claude Code data structures
- **JSONL Parsing**: Stream and parse conversation files efficiently
- **Validation**: Built-in validation for message structure and relationships
- **Error Handling**: Comprehensive error reporting for malformed data

### 📊 Analysis Tools
- **Statistics**: Calculate cost, tokens, duration, and conversation metrics
- **Tree Building**: Convert flat message lists to hierarchical conversation trees
- **Branch Analysis**: Extract active conversation paths from summaries
- **Tool Usage**: Track and analyze tool usage patterns

### 🔍 Data Insights
- **Architecture Patterns**: Local-first, append-only, UUID-based threading
- **Message Threading**: Support for conversation branching and merging
- **Cost Tracking**: Per-message cost calculation and aggregation
- **Tool Integration**: Request-response cycles with detailed results

## API Reference

### Types
- `BaseMessage` - Common fields for all messages
- `UserMessage` - User message with optional tool results
- `AssistantMessage` - Assistant response with cost and usage data
- `SummaryMessage` - Conversation summary metadata
- `ConversationEntry` - Union of all message types

### Parser Functions
- `parseConversation(filePath)` - Parse entire conversation file
- `parseAndValidateConversation(filePath)` - Parse with validation
- `readConversationLines(filePath)` - Async generator for streaming

### Analyzer Functions
- `calculateConversationStats(conversation)` - Get comprehensive statistics
- `buildConversationTree(messages)` - Create hierarchical structure
- `getActiveBranch(conversation)` - Extract active conversation path

### Type Guards
- `isUserMessage(message)` - Check if message is from user
- `isAssistantMessage(message)` - Check if message is from assistant
- `isSummaryMessage(entry)` - Check if entry is a summary
- `hasToolResult(message)` - Check if user message has tool results

## Data Format Notes

This library handles various Claude Code conversation formats:

- Messages may or may not include `costUSD` and `durationMs`
- Summary `leafUuid` may not always correspond to existing messages
- Tool usage appears in both assistant requests and user results
- Parent-child relationships enable conversation branching

## Use Cases

### For Developers
- **Data Export**: Extract conversations for analysis or backup
- **Custom Tools**: Build integrations using the data models
- **Analytics**: Analyze conversation patterns and costs
- **Migration**: Move data between Claude Code installations

### For Researchers
- **Conversation Analysis**: Study human-AI interaction patterns
- **Cost Optimization**: Analyze token usage and efficiency
- **Tool Usage**: Research tool adoption and effectiveness
- **Feature Usage**: Understand feature flag impacts

### For System Administrators
- **Backup Strategies**: Design data protection workflows
- **Storage Management**: Monitor disk usage growth
- **Privacy Compliance**: Understand data collection scope
- **Performance Monitoring**: Track conversation loading times

## Example Code

### Loading a Conversation

```typescript
import { readFileSync } from "fs";
import { BaseMessage, SummaryMessage } from "./types";

function loadConversation(filePath: string): {
  summaries: SummaryMessage[];
  messages: BaseMessage[];
} {
  const lines = readFileSync(filePath, "utf8").split("\n").filter(Boolean);
  const summaries: SummaryMessage[] = [];
  const messages: BaseMessage[] = [];

  for (const line of lines) {
    const entry = JSON.parse(line);
    if (entry.type === "summary") {
      summaries.push(entry);
    } else {
      messages.push(entry);
    }
  }

  return { summaries, messages };
}
```

### Building Conversation Tree

```typescript
function buildConversationTree(messages: BaseMessage[]): ConversationNode {
  const messageMap = new Map(messages.map(m => [m.uuid, m]));
  const children = new Map<string, BaseMessage[]>();

  // Build parent-child relationships
  for (const message of messages) {
    if (message.parentUuid) {
      if (!children.has(message.parentUuid)) {
        children.set(message.parentUuid, []);
      }
      children.get(message.parentUuid)!.push(message);
    }
  }

  // Find root and build tree
  const root = messages.find(m => m.parentUuid === null);
  if (!root) throw new Error("No root message found");

  return buildNode(root, children);
}
```

## Contributing

This analysis is based on reverse engineering Claude Code's data files. If you discover additional patterns or corrections, please:

1. Document your findings clearly
2. Provide example data (anonymized)
3. Include validation methods
4. Update relevant documentation sections

## Privacy and Ethics

When working with Claude Code data:

- **Respect User Privacy**: Never share conversation contents without permission
- **Anonymize Examples**: Remove personal information from code samples
- **Local Processing**: Keep analysis tools local-first like Claude Code itself
- **Secure Storage**: Protect any exported data with appropriate security measures

## License

MIT

## Version

Analysis based on Claude Code version 1.0.3 (May 2025). Data formats may evolve in future versions.