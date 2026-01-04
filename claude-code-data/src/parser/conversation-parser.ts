/**
 * Parser for Claude Code conversation JSONL files
 */

import { createReadStream } from "node:fs";
import { createInterface } from "node:readline";
import {
  ConversationEntry,
  SummaryMessage,
  ConversationMessage,
} from "../types/index";
import { isSummaryMessage, isConversationMessage } from "../utils/type-guards";

export interface ParsedConversation {
  summaries: SummaryMessage[];
  messages: ConversationMessage[];
  filePath: string;
  lineCount: number;
  parseErrors: ParseError[];
}

export interface ParseError {
  line: number;
  error: string;
  content: string;
}

/**
 * Asynchronously read and parse a conversation JSONL file
 */
export async function* readConversationLines(
  filePath: string,
): AsyncGenerator<ConversationEntry, void, undefined> {
  const fileStream = createReadStream(filePath);
  const rl = createInterface({
    input: fileStream,
    crlfDelay: Infinity, // Handle Windows line endings
  });

  let lineNumber = 0;

  for await (const line of rl) {
    lineNumber++;

    if (!line.trim()) {
      continue; // Skip empty lines
    }

    try {
      const entry = JSON.parse(line) as ConversationEntry;
      yield entry;
    } catch (error) {
      throw new Error(
        `Failed to parse line ${lineNumber}: ${error instanceof Error ? error.message : String(error)}`,
      );
    }
  }
}

/**
 * Parse an entire conversation file and return structured data
 */
export async function parseConversation(
  filePath: string,
): Promise<ParsedConversation> {
  const summaries: SummaryMessage[] = [];
  const messages: ConversationMessage[] = [];
  const parseErrors: ParseError[] = [];
  let lineCount = 0;

  try {
    for await (const entry of readConversationLines(filePath)) {
      lineCount++;

      if (isSummaryMessage(entry)) {
        summaries.push(entry);
      } else if (isConversationMessage(entry)) {
        messages.push(entry);
      } else {
        parseErrors.push({
          line: lineCount,
          error: "Unknown entry type",
          content: JSON.stringify(entry),
        });
      }
    }
  } catch (error) {
    if (
      error instanceof Error &&
      error.message.includes("Failed to parse line")
    ) {
      const match = error.message.match(/line (\d+)/);
      if (match) {
        parseErrors.push({
          line: parseInt(match[1], 10),
          error: error.message,
          content: "",
        });
      }
    } else {
      throw error;
    }
  }

  return {
    summaries,
    messages,
    filePath,
    lineCount,
    parseErrors,
  };
}

/**
 * Parse conversation with validation
 */
export async function parseAndValidateConversation(
  filePath: string,
): Promise<ParsedConversation> {
  const result = await parseConversation(filePath);

  // Validate message structure
  const messageIds = new Set<string>();
  const validationErrors: ParseError[] = [];

  result.messages.forEach((message, index) => {
    // Check for duplicate UUIDs
    if (messageIds.has(message.uuid)) {
      validationErrors.push({
        line: index + result.summaries.length + 1,
        error: `Duplicate UUID: ${message.uuid}`,
        content: "",
      });
    }
    messageIds.add(message.uuid);

    // Check parent references exist
    if (message.parentUuid && !messageIds.has(message.parentUuid)) {
      // Parent might appear later, so we'll check this after all messages are processed
    }
  });

  // Second pass: check parent references
  result.messages.forEach((message, index) => {
    if (
      message.parentUuid &&
      message.parentUuid !== null &&
      !messageIds.has(message.parentUuid)
    ) {
      validationErrors.push({
        line: index + result.summaries.length + 1,
        error: `Orphaned message: parent UUID ${message.parentUuid} not found`,
        content: "",
      });
    }
  });

  result.parseErrors.push(...validationErrors);

  return result;
}
