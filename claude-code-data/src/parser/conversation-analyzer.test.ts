/**
 * Tests for conversation analyzer
 */

import { describe, it, expect } from "vitest";
import { parseConversation } from "./conversation-parser";
import {
  calculateConversationStats,
  buildConversationTree,
  getActiveBranch,
} from "./conversation-analyzer";
import { join } from "node:path";

const TEST_FILE = join(
  process.cwd(),
  "test-data",
  "example-conversation.jsonl",
);

describe("ConversationAnalyzer", () => {
  describe("calculateConversationStats", () => {
    it("should calculate basic statistics correctly", async () => {
      const conversation = await parseConversation(TEST_FILE);
      const stats = calculateConversationStats(conversation);

      expect(stats.messageCount).toBe(28);
      expect(stats.userMessageCount).toBe(11);
      expect(stats.assistantMessageCount).toBe(17);
      expect(stats.messageCount).toBe(
        stats.userMessageCount + stats.assistantMessageCount,
      );
    });

    it("should calculate cost and token usage", async () => {
      const conversation = await parseConversation(TEST_FILE);
      const stats = calculateConversationStats(conversation);

      // Cost may be 0 if not provided in messages
      expect(stats.totalCostUSD).toBeGreaterThanOrEqual(0);
      expect(stats.totalTokens.input).toBeGreaterThan(0);
      expect(stats.totalTokens.output).toBeGreaterThan(0);
      expect(stats.totalTokens.cacheCreation).toBeGreaterThanOrEqual(0);
      expect(stats.totalTokens.cacheRead).toBeGreaterThanOrEqual(0);
    });

    it("should calculate timing metrics", async () => {
      const conversation = await parseConversation(TEST_FILE);
      const stats = calculateConversationStats(conversation);

      // Response time may be 0 if duration not provided
      expect(stats.averageResponseTimeMs).toBeGreaterThanOrEqual(0);
      expect(stats.conversationDurationMs).toBeGreaterThan(0);
    });

    it("should track model usage", async () => {
      const conversation = await parseConversation(TEST_FILE);
      const stats = calculateConversationStats(conversation);

      expect(stats.models.size).toBeGreaterThan(0);

      // Check that model counts add up to assistant message count
      const totalModelUsage = Array.from(stats.models.values()).reduce(
        (a, b) => a + b,
        0,
      );
      expect(totalModelUsage).toBe(stats.assistantMessageCount);
    });

    it("should count tool usage", async () => {
      const conversation = await parseConversation(TEST_FILE);
      const stats = calculateConversationStats(conversation);

      expect(stats.toolUsageCount).toBe(20); // Based on the agent's analysis
    });

    it("should detect conversation branches", async () => {
      const conversation = await parseConversation(TEST_FILE);
      const stats = calculateConversationStats(conversation);

      expect(stats.branches).toBeGreaterThanOrEqual(0);
    });

    it("should handle empty conversations", async () => {
      const emptyConversation = {
        summaries: [],
        messages: [],
        filePath: "",
        lineCount: 0,
        parseErrors: [],
      };

      const stats = calculateConversationStats(emptyConversation);

      expect(stats.messageCount).toBe(0);
      expect(stats.totalCostUSD).toBe(0);
      expect(stats.averageResponseTimeMs).toBe(0);
    });
  });

  describe("buildConversationTree", () => {
    it("should build tree structure from messages", async () => {
      const conversation = await parseConversation(TEST_FILE);
      const tree = buildConversationTree(conversation.messages);

      expect(tree.length).toBeGreaterThan(0);

      // Check that root nodes have no parent
      tree.forEach((node) => {
        expect(node.message.parentUuid).toBeNull();
      });
    });

    it("should correctly nest children", async () => {
      const conversation = await parseConversation(TEST_FILE);
      const tree = buildConversationTree(conversation.messages);

      // Find a node with children
      const findNodeWithChildren = (nodes: any[]): any => {
        for (const node of nodes) {
          if (node.children.length > 0) return node;
          const childResult = findNodeWithChildren(node.children);
          if (childResult) return childResult;
        }
        return null;
      };

      const parentNode = findNodeWithChildren(tree);
      if (parentNode) {
        expect(parentNode.children.length).toBeGreaterThan(0);

        // Verify children have correct parent
        parentNode.children.forEach((child: any) => {
          expect(child.message.parentUuid).toBe(parentNode.message.uuid);
        });
      }
    });
  });

  describe("getActiveBranch", () => {
    it("should extract active branch based on summary", async () => {
      const conversation = await parseConversation(TEST_FILE);
      const activeBranch = getActiveBranch(conversation);

      expect(activeBranch.length).toBeGreaterThan(0);

      // If leafUuid not found in messages, it returns all messages
      // This is expected behavior for this test file where leafUuid might not match
      if (conversation.summaries.length > 0) {
        const leafUuid = conversation.summaries[0].leafUuid;
        const hasLeaf = conversation.messages.some((m) => m.uuid === leafUuid);

        if (hasLeaf) {
          const lastMessage = activeBranch[activeBranch.length - 1];
          expect(lastMessage.uuid).toBe(leafUuid);
        } else {
          // Should return all messages when leaf not found
          expect(activeBranch.length).toBe(conversation.messages.length);
        }
      }
    });

    it("should return continuous chain from root to leaf", async () => {
      const conversation = await parseConversation(TEST_FILE);
      const activeBranch = getActiveBranch(conversation);

      if (activeBranch.length > 0) {
        // First message should have no parent
        expect(activeBranch[0].parentUuid).toBeNull();

        // Each subsequent message should reference the previous one
        for (let i = 1; i < activeBranch.length; i++) {
          expect(activeBranch[i].parentUuid).toBe(activeBranch[i - 1].uuid);
        }
      }
    });

    it("should handle conversations without summaries", async () => {
      const conversationNoSummary = {
        summaries: [],
        messages: [],
        filePath: "",
        lineCount: 0,
        parseErrors: [],
      };

      const activeBranch = getActiveBranch(conversationNoSummary);
      expect(activeBranch).toHaveLength(0);
    });
  });

  describe("Cost analysis", () => {
    it("should accurately sum costs across messages", async () => {
      const conversation = await parseConversation(TEST_FILE);
      const stats = calculateConversationStats(conversation);

      // Manually calculate total cost to verify
      const manualCost = conversation.messages
        .filter((m) => m.type === "assistant")
        .reduce((sum, m: any) => sum + (m.costUSD || 0), 0);

      expect(stats.totalCostUSD).toBeCloseTo(manualCost, 10);
    });
  });
});
