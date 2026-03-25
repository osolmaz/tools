import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

const PROMPTS_DIR = fileURLToPath(new URL("../prompts/", import.meta.url));

export async function loadPrompt(relativePath, variables = {}) {
  const promptPath = path.join(PROMPTS_DIR, relativePath);
  let text = await readFile(promptPath, "utf8");

  for (const [key, value] of Object.entries(variables)) {
    text = text.replaceAll(`{{${key}}}`, String(value));
  }

  return text.trim();
}
