/**
 * Tests for type guard functions
 */

import { describe, it, expect } from "vitest";
import {
  isUserMessage,
  isAssistantMessage,
  isSummaryMessage,
  isConversationMessage,
  isToolUseContent,
  isTextContent,
  hasToolResult,
} from "./type-guards";
import type {
  UserMessage,
  AssistantMessage,
  SummaryMessage,
  TextContentBlock,
  ToolUseContentBlock,
} from "../types/index";

describe("Type Guards", () => {
  describe("isUserMessage", () => {
    it("should identify user messages", () => {
      const userMessage = {
        type: "user",
        uuid: "test-uuid",
        parentUuid: null,
        timestamp: new Date().toISOString(),
        sessionId: "session-id",
        userType: "external",
        version: "1.0.0",
        cwd: "/test",
        isSidechain: false,
        message: {
          role: "user",
          content: "Hello",
        },
      } as UserMessage;

      expect(isUserMessage(userMessage)).toBe(true);
    });

    it("should reject non-user messages", () => {
      const assistantMessage = {
        type: "assistant",
        uuid: "test-uuid",
        // ... other fields
      } as any;

      expect(isUserMessage(assistantMessage)).toBe(false);
    });
  });

  describe("isAssistantMessage", () => {
    it("should identify assistant messages", () => {
      const assistantMessage = {
        type: "assistant",
        uuid: "test-uuid",
        // ... other required fields
      } as any;

      expect(isAssistantMessage(assistantMessage)).toBe(true);
    });
  });

  describe("isSummaryMessage", () => {
    it("should identify summary messages", () => {
      const summary: SummaryMessage = {
        type: "summary",
        summary: "Test conversation",
        leafUuid: "leaf-uuid",
      };

      expect(isSummaryMessage(summary)).toBe(true);
    });

    it("should reject non-summary objects", () => {
      expect(isSummaryMessage(null)).toBe(false);
      expect(isSummaryMessage(undefined)).toBe(false);
      expect(isSummaryMessage({ type: "other" })).toBe(false);
      expect(isSummaryMessage("not an object")).toBe(false);
    });
  });

  describe("isConversationMessage", () => {
    it("should identify conversation messages", () => {
      const userMessage = {
        type: "user",
        uuid: "test-uuid",
        // ... other fields
      } as any;

      const assistantMessage = {
        type: "assistant",
        uuid: "test-uuid",
        // ... other fields
      } as any;

      expect(isConversationMessage(userMessage)).toBe(true);
      expect(isConversationMessage(assistantMessage)).toBe(true);
    });

    it("should reject summary messages", () => {
      const summary: SummaryMessage = {
        type: "summary",
        summary: "Test",
        leafUuid: "uuid",
      };

      expect(isConversationMessage(summary)).toBe(false);
    });
  });

  describe("Content type guards", () => {
    it("should identify tool use content", () => {
      const toolUse: ToolUseContentBlock = {
        type: "tool_use",
        id: "tool-id",
        name: "Read",
        input: { file_path: "/test.txt" },
      };

      expect(isToolUseContent(toolUse)).toBe(true);
      expect(isTextContent(toolUse)).toBe(false);
    });

    it("should identify text content", () => {
      const text: TextContentBlock = {
        type: "text",
        text: "Hello world",
      };

      expect(isTextContent(text)).toBe(true);
      expect(isToolUseContent(text)).toBe(false);
    });
  });

  describe("hasToolResult", () => {
    it("should detect tool results in user messages", () => {
      const messageWithToolResult: UserMessage = {
        type: "user",
        uuid: "test",
        parentUuid: null,
        timestamp: new Date().toISOString(),
        sessionId: "session",
        userType: "external",
        version: "1.0.0",
        cwd: "/test",
        isSidechain: false,
        message: {
          role: "user",
          content: [
            {
              tool_use_id: "tool-123",
              type: "tool_result",
              content: "Result data",
            },
          ],
        },
      };

      expect(hasToolResult(messageWithToolResult)).toBe(true);
    });

    it("should return false for messages without tool results", () => {
      const simpleMessage: UserMessage = {
        type: "user",
        uuid: "test",
        parentUuid: null,
        timestamp: new Date().toISOString(),
        sessionId: "session",
        userType: "external",
        version: "1.0.0",
        cwd: "/test",
        isSidechain: false,
        message: {
          role: "user",
          content: "Simple text message",
        },
      };

      expect(hasToolResult(simpleMessage)).toBe(false);
    });
  });
});
