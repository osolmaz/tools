/**
 * Tests for conversation parser
 */

import { describe, it, expect } from "vitest";
import {
  parseConversation,
  parseAndValidateConversation,
} from "./conversation-parser";
import { isUserMessage, isAssistantMessage } from "../utils/type-guards";
import { join } from "node:path";

const TEST_FILE = join(
  process.cwd(),
  "test-data",
  "example-conversation.jsonl",
);

describe("ConversationParser", () => {
  describe("parseConversation", () => {
    it("should parse example conversation file successfully", async () => {
      const result = await parseConversation(TEST_FILE);

      expect(result).toBeDefined();
      expect(result.filePath).toBe(TEST_FILE);
      expect(result.lineCount).toBeGreaterThan(0);
      expect(result.parseErrors).toHaveLength(0);
    });

    it("should correctly identify summaries and messages", async () => {
      const result = await parseConversation(TEST_FILE);

      expect(result.summaries.length).toBe(2);
      expect(result.messages.length).toBe(28);

      // Verify first summary
      expect(result.summaries[0]).toMatchObject({
        type: "summary",
        summary: expect.any(String),
        leafUuid: expect.any(String),
      });
    });

    it("should parse user messages correctly", async () => {
      const result = await parseConversation(TEST_FILE);
      const userMessages = result.messages.filter(isUserMessage);

      expect(userMessages.length).toBeGreaterThan(0);

      const firstUserMessage = userMessages[0];
      expect(firstUserMessage).toMatchObject({
        type: "user",
        uuid: expect.any(String),
        timestamp: expect.any(String),
        sessionId: expect.any(String),
        message: {
          role: "user",
          content: expect.any(String),
        },
      });
    });

    it("should parse assistant messages with cost and usage", async () => {
      const result = await parseConversation(TEST_FILE);
      const assistantMessages = result.messages.filter(isAssistantMessage);

      expect(assistantMessages.length).toBeGreaterThan(0);

      const firstAssistantMessage = assistantMessages[0];
      expect(firstAssistantMessage).toMatchObject({
        type: "assistant",
        uuid: expect.any(String),
        message: {
          id: expect.any(String),
          role: "assistant",
          model: expect.any(String),
          usage: {
            input_tokens: expect.any(Number),
            output_tokens: expect.any(Number),
            cache_creation_input_tokens: expect.any(Number),
            cache_read_input_tokens: expect.any(Number),
            service_tier: expect.any(String),
          },
        },
      });

      // Cost and duration may be optional
      if (firstAssistantMessage.costUSD !== undefined) {
        expect(firstAssistantMessage.costUSD).toBeTypeOf("number");
      }
      if (firstAssistantMessage.durationMs !== undefined) {
        expect(firstAssistantMessage.durationMs).toBeTypeOf("number");
      }
    });

    it("should handle tool use content", async () => {
      const result = await parseConversation(TEST_FILE);
      const assistantMessages = result.messages.filter(isAssistantMessage);

      // Find messages with tool use
      const toolUseMessages = assistantMessages.filter((msg) =>
        msg.message.content.some((c) => c.type === "tool_use"),
      );

      expect(toolUseMessages.length).toBeGreaterThan(0);

      const firstToolUse = toolUseMessages[0].message.content.find(
        (c) => c.type === "tool_use",
      );
      expect(firstToolUse).toMatchObject({
        type: "tool_use",
        id: expect.any(String),
        name: expect.any(String),
        input: expect.any(Object),
      });
    });

    it("should handle tool results in user messages", async () => {
      const result = await parseConversation(TEST_FILE);
      const userMessages = result.messages.filter(isUserMessage);

      // Find messages with tool results
      const toolResultMessages = userMessages.filter(
        (msg) =>
          Array.isArray(msg.message.content) &&
          msg.message.content.some((c) => c.type === "tool_result"),
      );

      expect(toolResultMessages.length).toBeGreaterThan(0);
    });
  });

  describe("parseAndValidateConversation", () => {
    it("should validate message structure", async () => {
      const result = await parseAndValidateConversation(TEST_FILE);

      // Check that validation passed (no additional errors)
      const validationErrors = result.parseErrors.filter(
        (e) =>
          e.error.includes("Duplicate UUID") ||
          e.error.includes("Orphaned message"),
      );

      expect(validationErrors).toHaveLength(0);
    });

    it("should ensure all parent references exist", async () => {
      const result = await parseAndValidateConversation(TEST_FILE);

      const messageIds = new Set(result.messages.map((m) => m.uuid));

      result.messages.forEach((message) => {
        if (message.parentUuid !== null) {
          expect(messageIds.has(message.parentUuid)).toBe(true);
        }
      });
    });
  });

  describe("Message threading", () => {
    it("should maintain parent-child relationships", async () => {
      const result = await parseConversation(TEST_FILE);

      // Find root messages
      const rootMessages = result.messages.filter((m) => m.parentUuid === null);
      expect(rootMessages.length).toBeGreaterThan(0);

      // Find messages with children
      const parentIds = new Set(
        result.messages.map((m) => m.parentUuid).filter(Boolean),
      );
      expect(parentIds.size).toBeGreaterThan(0);
    });

    it("should preserve chronological order", async () => {
      const result = await parseConversation(TEST_FILE);

      // Check that messages are in chronological order
      for (let i = 1; i < result.messages.length; i++) {
        const prevTime = new Date(result.messages[i - 1].timestamp).getTime();
        const currTime = new Date(result.messages[i].timestamp).getTime();
        expect(currTime).toBeGreaterThanOrEqual(prevTime);
      }
    });
  });
});
