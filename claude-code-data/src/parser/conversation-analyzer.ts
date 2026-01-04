/**
 * Analyzer for conversation data - extracts statistics and insights
 */

import type { ConversationMessage } from "../types/index";
import {
  isAssistantMessage,
  isUserMessage,
  hasToolResult,
  isToolUseContent,
} from "../utils/type-guards";
import type { ParsedConversation } from "./conversation-parser";

export interface ConversationStats {
  messageCount: number;
  userMessageCount: number;
  assistantMessageCount: number;
  totalCostUSD: number;
  totalTokens: {
    input: number;
    output: number;
    cacheCreation: number;
    cacheRead: number;
  };
  averageResponseTimeMs: number;
  conversationDurationMs: number;
  toolUsageCount: number;
  models: Map<string, number>;
  branches: number;
}

export interface ConversationNode {
  message: ConversationMessage;
  children: ConversationNode[];
}

/**
 * Calculate comprehensive statistics for a conversation
 */
export function calculateConversationStats(
  conversation: ParsedConversation,
): ConversationStats {
  const { messages } = conversation;

  if (messages.length === 0) {
    return {
      messageCount: 0,
      userMessageCount: 0,
      assistantMessageCount: 0,
      totalCostUSD: 0,
      totalTokens: {
        input: 0,
        output: 0,
        cacheCreation: 0,
        cacheRead: 0,
      },
      averageResponseTimeMs: 0,
      conversationDurationMs: 0,
      toolUsageCount: 0,
      models: new Map(),
      branches: 0,
    };
  }

  const assistantMessages = messages.filter(isAssistantMessage);
  const userMessages = messages.filter(isUserMessage);

  // Calculate token totals
  const totalTokens = assistantMessages.reduce(
    (acc, msg) => ({
      input: acc.input + msg.message.usage.input_tokens,
      output: acc.output + msg.message.usage.output_tokens,
      cacheCreation:
        acc.cacheCreation + msg.message.usage.cache_creation_input_tokens,
      cacheRead: acc.cacheRead + msg.message.usage.cache_read_input_tokens,
    }),
    { input: 0, output: 0, cacheCreation: 0, cacheRead: 0 },
  );

  // Calculate model usage
  const models = new Map<string, number>();
  assistantMessages.forEach((msg) => {
    const model = msg.message.model;
    models.set(model, (models.get(model) || 0) + 1);
  });

  // Count tool usage
  const toolUsageCount =
    assistantMessages.reduce((count, msg) => {
      return count + msg.message.content.filter(isToolUseContent).length;
    }, 0) + userMessages.filter(hasToolResult).length;

  // Calculate conversation duration
  const timestamps = messages.map((m) => new Date(m.timestamp).getTime());
  const conversationDurationMs =
    Math.max(...timestamps) - Math.min(...timestamps);

  // Calculate branches (messages with multiple children)
  const childrenCount = new Map<string | null, number>();
  messages.forEach((msg) => {
    const parent = msg.parentUuid;
    childrenCount.set(parent, (childrenCount.get(parent) || 0) + 1);
  });
  const branches = Array.from(childrenCount.values()).filter(
    (count) => count > 1,
  ).length;

  return {
    messageCount: messages.length,
    userMessageCount: userMessages.length,
    assistantMessageCount: assistantMessages.length,
    totalCostUSD: assistantMessages.reduce(
      (sum, msg) => sum + (msg.costUSD || 0),
      0,
    ),
    totalTokens,
    averageResponseTimeMs:
      assistantMessages.length > 0
        ? assistantMessages.reduce(
            (sum, msg) => sum + (msg.durationMs || 0),
            0,
          ) / assistantMessages.length
        : 0,
    conversationDurationMs,
    toolUsageCount,
    models,
    branches,
  };
}

/**
 * Build a tree structure from flat messages
 */
export function buildConversationTree(
  messages: ConversationMessage[],
): ConversationNode[] {
  const messageMap = new Map<string, ConversationMessage>();
  const childrenMap = new Map<string | null, ConversationMessage[]>();

  // Build lookup maps
  messages.forEach((msg) => {
    messageMap.set(msg.uuid, msg);

    const siblings = childrenMap.get(msg.parentUuid) || [];
    siblings.push(msg);
    childrenMap.set(msg.parentUuid, siblings);
  });

  // Recursive function to build tree nodes
  function buildNode(message: ConversationMessage): ConversationNode {
    const children = childrenMap.get(message.uuid) || [];
    return {
      message,
      children: children.map((child) => buildNode(child)),
    };
  }

  // Find root messages (parentUuid === null)
  const roots = childrenMap.get(null) || [];
  return roots.map((root) => buildNode(root));
}

/**
 * Get the active conversation branch (following leafUuid from summaries)
 */
export function getActiveBranch(
  conversation: ParsedConversation,
): ConversationMessage[] {
  if (
    conversation.summaries.length === 0 ||
    conversation.messages.length === 0
  ) {
    return [];
  }

  // Use the first summary's leafUuid as the active branch
  const leafUuid = conversation.summaries[0].leafUuid;
  const messageMap = new Map(conversation.messages.map((m) => [m.uuid, m]));

  // Check if the leafUuid exists in messages
  if (!messageMap.has(leafUuid)) {
    // If not found, return all messages (could be a different format)
    return conversation.messages;
  }

  // Trace back from leaf to root
  const branch: ConversationMessage[] = [];
  let currentUuid: string | null = leafUuid;

  while (currentUuid !== null) {
    const message = messageMap.get(currentUuid);
    if (!message) break;

    branch.unshift(message); // Add to beginning to maintain order
    currentUuid = message.parentUuid;
  }

  return branch;
}
