# Claude Code Data Storage Analysis

## Overview

This repository contains a comprehensive reverse engineering analysis of Claude Code's data storage system, including conversation formats, configuration structures, and data models.

## Repository Structure

```
docs/
├── README.md                           # This file
├── claude-code-data-storage-analysis.md # High-level analysis and overview
├── conversation-format-specification.md # Detailed JSONL conversation format
├── data-models-and-schemas.md          # TypeScript interfaces and schemas
└── implementation-notes.md             # Technical patterns and insights
```

## Quick Start

### Understanding the File Structure

Claude Code stores its data in a `.claude/` directory with the following structure:

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

### Key Files to Read

1. **[Storage Analysis](claude-code-data-storage-analysis.md)** - Start here for a high-level overview
2. **[Conversation Format](conversation-format-specification.md)** - Deep dive into message structure
3. **[Data Models](data-models-and-schemas.md)** - TypeScript definitions for type-safe parsing
4. **[Implementation Notes](implementation-notes.md)** - Engineering patterns and insights

## Data Format Summary

### Conversation Storage (JSONL)

Each conversation is stored as a JSON Lines file:

```jsonl
{"type":"summary","summary":"Conversation Title","leafUuid":"last-message-id"}
{"type":"user","uuid":"msg-1","parentUuid":null,"message":{"role":"user","content":"Hello"},"timestamp":"2025-06-05T10:00:00.000Z"}
{"type":"assistant","uuid":"msg-2","parentUuid":"msg-1","message":{"role":"assistant","content":[{"type":"text","text":"Hi there!"}]},"costUSD":0.001,"durationMs":1500}
```

### Main Configuration (.claude.json)

Global application state and project configurations:

```json
{
  "numStartups": 69,
  "userID": "sha256-hash",
  "hasCompletedOnboarding": true,
  "projects": {
    "/path/to/project": {
      "allowedTools": [],
      "context": {},
      "history": []
    }
  }
}
```

## Key Insights

### Architecture Patterns

- **Local-First**: All data stored locally, no cloud dependencies
- **Append-Only**: Conversations use append-only JSONL for integrity
- **UUID-Based**: Message threading through parent-child UUIDs
- **Project-Scoped**: Conversations organized by project directory

### Message Threading

Messages form directed graphs through parent-child relationships:

```
Root Message (parentUuid: null)
├── Assistant Response
│   ├── User Follow-up A
│   └── User Follow-up B (branch)
└── User Follow-up C (another branch)
```

### Tool Integration

Tools follow a request-response pattern:

1. Assistant requests tool use
2. System executes tool (not stored)
3. User message contains tool results
4. Assistant processes results

### Cost Tracking

Every assistant message includes:

- Token usage breakdown (input/output/cache)
- Response time in milliseconds
- Cost calculation in USD
- Model information

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
  const messageMap = new Map(messages.map((m) => [m.uuid, m]));
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
  const root = messages.find((m) => m.parentUuid === null);
  if (!root) throw new Error("No root message found");

  return buildNode(root, children);
}
```

### Calculating Conversation Stats

```typescript
function calculateConversationStats(
  messages: BaseMessage[],
): ConversationStats {
  const assistantMessages = messages.filter((m) => m.type === "assistant");

  return {
    messageCount: messages.length,
    totalCost: assistantMessages.reduce((sum, m) => sum + m.costUSD, 0),
    totalTokens: assistantMessages.reduce(
      (sum, m) => sum + m.message.usage.output_tokens,
      0,
    ),
    averageResponseTime:
      assistantMessages.reduce((sum, m) => sum + m.durationMs, 0) /
      assistantMessages.length,
    conversationDuration:
      new Date(messages[messages.length - 1].timestamp).getTime() -
      new Date(messages[0].timestamp).getTime(),
  };
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

This documentation is provided for educational and interoperability purposes. Claude Code is proprietary software by Anthropic - respect their terms of service when using this information.

## Version

Analysis based on Claude Code version 1.0.3 (May 2025). Data formats may evolve in future versions.
