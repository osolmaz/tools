import { execFile } from "node:child_process";
import { readFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const PROMPTS_DIR = fileURLToPath(new URL("../prompts/pr-triage/", import.meta.url));

export default {
  name: "pr-triage",
  startAt: "load_pr",
  nodes: {
    load_pr: {
      kind: "compute",
      run: async ({ input }) => loadPullRequestContext(input),
    },

    solution_fit: {
      kind: "acp",
      async prompt({ outputs }) {
        return await loadPrompt("pr-triage/solution-fit.md", {
          promptContext: outputs.load_pr.promptContext,
        });
      },
      parse: (text) => extractJson(text),
    },

    issue_clarity: {
      kind: "acp",
      async prompt() {
        return await loadPrompt("pr-triage/issue-clarity.md");
      },
      parse: (text) => extractJson(text),
    },

    scope_assessment: {
      kind: "acp",
      async prompt() {
        return await loadPrompt("pr-triage/scope-assessment.md");
      },
      parse: (text) => extractJson(text),
    },

    route: {
      kind: "compute",
      run: ({ outputs }) => {
        const reasons = [];
        if (outputs.solution_fit.verdict !== "right_solution") {
          reasons.push(`solution_fit=${outputs.solution_fit.verdict}`);
        }
        if (outputs.issue_clarity.verdict !== "clear") {
          reasons.push(`issue_clarity=${outputs.issue_clarity.verdict}`);
        }
        if (outputs.scope_assessment.scope !== "appropriately_local") {
          reasons.push(`scope=${outputs.scope_assessment.scope}`);
        }
        if (outputs.scope_assessment.refactor_needed === "fundamental") {
          reasons.push("refactor_needed=fundamental");
        }
        if (outputs.scope_assessment.human_judgment_needed) {
          reasons.push("human_judgment_needed=true");
        }

        return {
          next: reasons.length > 0 ? "human_review" : "continue_lane",
          reasons,
        };
      },
    },

    continue_lane: {
      kind: "acp",
      async prompt({ outputs }) {
        return await loadPrompt("pr-triage/continue-lane.md", {
          reasons: JSON.stringify(outputs.route.reasons),
        });
      },
      parse: (text) => extractJson(text),
    },

    human_review: {
      kind: "acp",
      async prompt({ outputs }) {
        return await loadPrompt("pr-triage/human-review.md", {
          reasons: JSON.stringify(outputs.route.reasons),
        });
      },
      parse: (text) => extractJson(text),
    },

    finalize: {
      kind: "compute",
      run: ({ outputs, state }) => {
        const branch =
          outputs.route.next === "continue_lane" ? outputs.continue_lane : outputs.human_review;
        return {
          route: branch.route,
          routeReasons: outputs.route.reasons,
          final: branch,
          sessionBindings: state.sessionBindings,
        };
      },
    },
  },
  edges: [
    { from: "load_pr", to: "solution_fit" },
    { from: "solution_fit", to: "issue_clarity" },
    { from: "issue_clarity", to: "scope_assessment" },
    { from: "scope_assessment", to: "route" },
    {
      from: "route",
      switch: {
        on: "$.next",
        cases: {
          continue_lane: "continue_lane",
          human_review: "human_review",
        },
      },
    },
    { from: "continue_lane", to: "finalize" },
    { from: "human_review", to: "finalize" },
  ],
};

async function loadPrompt(relativePath, variables = {}) {
  const promptPath = path.join(PROMPTS_DIR, relativePath.replace(/^pr-triage\//, ""));
  let text = await readFile(promptPath, "utf8");

  for (const [key, value] of Object.entries(variables)) {
    text = text.replaceAll(`{{${key}}}`, String(value));
  }

  return text.trim();
}

async function loadPullRequestContext(input) {
  const repo = String(input?.repo ?? "").trim();
  const prNumber = Number(input?.prNumber);

  if (!repo) {
    throw new Error('Flow input must include a non-empty "repo" string');
  }
  if (!Number.isInteger(prNumber) || prNumber <= 0) {
    throw new Error('Flow input must include a positive integer "prNumber"');
  }

  const pr = await ghJson([
    "pr",
    "view",
    String(prNumber),
    "-R",
    repo,
    "--json",
    "number,title,body,author,url,additions,deletions,changedFiles,files,baseRefName,headRefName",
  ]);

  const linkedIssueNumber = findLinkedIssueNumber(pr.body);
  const linkedIssue = linkedIssueNumber
    ? await ghJson([
        "issue",
        "view",
        String(linkedIssueNumber),
        "-R",
        repo,
        "--json",
        "number,title,body,url",
      ])
    : null;

  const diff = await ghText(["pr", "diff", String(prNumber), "-R", repo]);
  const maxDiffChars = 30000;
  const truncatedDiff =
    diff.length > maxDiffChars
      ? `${diff.slice(0, maxDiffChars)}\n\n[diff truncated at ${maxDiffChars} characters]`
      : diff;

  return {
    repo,
    pr,
    linkedIssue,
    promptContext: formatPromptContext({ repo, pr, linkedIssue, diff: truncatedDiff }),
  };
}

async function ghJson(args) {
  return JSON.parse(await ghText(args));
}

async function ghText(args) {
  const result = await execFileAsync("gh", args, {
    maxBuffer: 10 * 1024 * 1024,
  });
  return result.stdout.trim();
}

function findLinkedIssueNumber(body) {
  const match = String(body ?? "").match(/\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)\b/i);
  return match ? Number(match[1]) : null;
}

function formatPromptContext({ repo, pr, linkedIssue, diff }) {
  const files = (pr.files ?? [])
    .map((file) => `- ${file.path} (+${file.additions} / -${file.deletions})`)
    .join("\n");

  const issueSection = linkedIssue
    ? `Linked issue #${linkedIssue.number}: ${linkedIssue.title}\n${linkedIssue.body ?? ""}`
    : "No linked issue was found in the PR body.";

  return [
    `Repository: ${repo}`,
    `PR #${pr.number}: ${pr.title}`,
    `URL: ${pr.url}`,
    `Author: ${pr.author?.login ?? "unknown"}`,
    `Base: ${pr.baseRefName}`,
    `Head: ${pr.headRefName}`,
    `Changed files: ${pr.changedFiles}`,
    `Additions: ${pr.additions}`,
    `Deletions: ${pr.deletions}`,
    "",
    "PR body:",
    pr.body || "(empty)",
    "",
    "Changed files:",
    files || "(none)",
    "",
    "Underlying issue:",
    issueSection,
    "",
    "Diff:",
    diff || "(empty diff)",
  ].join("\n");
}

function extractJson(text) {
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
