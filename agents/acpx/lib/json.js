export function extractJson(text) {
  const trimmed = String(text ?? "").trim();
  if (!trimmed) {
    throw new Error("Expected JSON output, got empty text");
  }

  const direct = tryParse(trimmed);
  if (direct.ok) {
    return direct.value;
  }

  const fencedMatch = trimmed.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fencedMatch) {
    const fenced = tryParse(fencedMatch[1].trim());
    if (fenced.ok) {
      return fenced.value;
    }
  }

  const balanced = extractBalancedJson(trimmed);
  if (balanced) {
    const parsed = tryParse(balanced);
    if (parsed.ok) {
      return parsed.value;
    }
  }

  throw new Error(`Could not parse JSON from assistant output:\n${trimmed}`);
}

function tryParse(text) {
  try {
    return { ok: true, value: JSON.parse(text) };
  } catch {
    return { ok: false };
  }
}

function extractBalancedJson(text) {
  const starts = ["{", "["];
  for (let i = 0; i < text.length; i += 1) {
    if (!starts.includes(text[i])) {
      continue;
    }

    const result = scanBalanced(text, i);
    if (result) {
      return result;
    }
  }

  return null;
}

function scanBalanced(text, startIndex) {
  const stack = [];
  let inString = false;
  let escaped = false;

  for (let i = startIndex; i < text.length; i += 1) {
    const char = text[i];

    if (inString) {
      if (escaped) {
        escaped = false;
      } else if (char === "\\") {
        escaped = true;
      } else if (char === "\"") {
        inString = false;
      }
      continue;
    }

    if (char === "\"") {
      inString = true;
      continue;
    }

    if (char === "{" || char === "[") {
      stack.push(char);
      continue;
    }

    if (char === "}" || char === "]") {
      const last = stack.at(-1);
      if ((last === "{" && char !== "}") || (last === "[" && char !== "]")) {
        return null;
      }

      stack.pop();
      if (stack.length === 0) {
        return text.slice(startIndex, i + 1);
      }
    }
  }

  return null;
}
