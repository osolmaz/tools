import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const INTENT_EXTRACTION_PROMPT = [
  "You are processing one PR at a time.",
  "Use only the PR context below.",
  "Extract the plain-language human intent of this PR and the underlying problem it is trying to solve.",
  "Return exactly one JSON object with this shape:",
  "{",
  '  "intent": "plain-language human goal",',
  '  "problem": "short description of the underlying issue",',
  '  "confidence": 0.0,',
  '  "reason": "short explanation"',
  "}",
].join("\n");

const REVIEW_LOOP_PROMPT = [
  "Stay on the autonomous review lane for this single PR.",
  "Use the PR context already in this session, plus the earlier intent, solution, and refactor judgments.",
  "Run or inspect AI review on the current PR head.",
  "Address valid P0 and P1 findings before continuing.",
  "If blocking review findings still remain after this pass, route back to review_loop.",
  "If blocking review findings are cleared, route to fix_ci_failures.",
  "Return exactly one JSON object with this shape:",
  "{",
  '  "route": "review_loop" | "fix_ci_failures",',
  '  "review_status": "blocking_findings_remain" | "clear",',
  '  "summary": "short explanation",',
  '  "blocking_findings": ["brief finding"]',
  "}",
].join("\n");

const flow = {
  name: "pr-triage",
  startAt: "load_pr",
  nodes: {
    load_pr: {
      kind: "compute",
      run: async ({ input }) => loadPullRequestContext(input),
    },

    extract_intent: {
      kind: "acp",
      async prompt({ outputs }) {
        return [INTENT_EXTRACTION_PROMPT, "", loadPrOutput(outputs).promptContext].join("\n");
      },
      parse: (text) => extractJson(text),
    },

    judge_solution: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptJudgeSolution(loadPrOutput(outputs).promptContext, outputs.extract_intent);
      },
      parse: (text) => extractJson(text),
    },

    judge_refactor: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptJudgeRefactor(outputs.extract_intent, outputs.judge_solution);
      },
      parse: (text) => extractJson(text),
    },

    do_superficial_refactor: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptSuperficialRefactor(outputs.extract_intent, outputs.judge_solution, outputs.judge_refactor);
      },
      parse: (text) => extractJson(text),
    },

    review_loop: {
      kind: "acp",
      async prompt({ outputs }) {
        return [
          REVIEW_LOOP_PROMPT,
          "",
          `Intent: ${JSON.stringify(outputs.extract_intent, null, 2)}`,
          `Solution judgment: ${JSON.stringify(outputs.judge_solution, null, 2)}`,
          `Refactor judgment: ${JSON.stringify(outputs.judge_refactor, null, 2)}`,
          outputs.do_superficial_refactor
            ? `Superficial refactor result: ${JSON.stringify(outputs.do_superficial_refactor, null, 2)}`
            : "",
        ]
          .filter(Boolean)
          .join("\n\n");
      },
      parse: (text) => extractJson(text),
    },

    fix_ci_failures: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptFixCiFailures(
          outputs.extract_intent,
          outputs.judge_solution,
          outputs.judge_refactor,
          outputs.review_loop,
        );
      },
      parse: (text) => extractJson(text),
    },

    comment_and_close_pr: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptCloseComment(outputs);
      },
      parse: (text) => extractJson(text),
    },

    comment_and_escalate_to_human: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptHumanComment(outputs);
      },
      parse: (text) => extractJson(text),
    },

    finalize: {
      kind: "compute",
      run: ({ outputs, state }) => {
        const final =
          outputs.comment_and_close_pr ?? outputs.comment_and_escalate_to_human ?? outputs.fix_ci_failures;

        return {
          final,
          intent: outputs.extract_intent,
          solution: outputs.judge_solution,
          refactor: outputs.judge_refactor ?? null,
          review: outputs.review_loop ?? null,
          ci: outputs.fix_ci_failures ?? null,
          sessionBindings: state.sessionBindings,
        };
      },
    },
  },
  edges: [
    { from: "load_pr", to: "extract_intent" },
    { from: "extract_intent", to: "judge_solution" },
    {
      from: "judge_solution",
      switch: {
        on: "$.route",
        cases: {
          close_pr: "comment_and_close_pr",
          comment_and_escalate_to_human: "comment_and_escalate_to_human",
          judge_refactor: "judge_refactor",
        },
      },
    },
    {
      from: "judge_refactor",
      switch: {
        on: "$.route",
        cases: {
          review_loop: "review_loop",
          do_superficial_refactor: "do_superficial_refactor",
          comment_and_escalate_to_human: "comment_and_escalate_to_human",
        },
      },
    },
    { from: "do_superficial_refactor", to: "review_loop" },
    {
      from: "review_loop",
      switch: {
        on: "$.route",
        cases: {
          review_loop: "review_loop",
          fix_ci_failures: "fix_ci_failures",
        },
      },
    },
    {
      from: "fix_ci_failures",
      switch: {
        on: "$.route",
        cases: {
          fix_ci_failures: "fix_ci_failures",
          comment_and_escalate_to_human: "comment_and_escalate_to_human",
        },
      },
    },
    { from: "comment_and_close_pr", to: "finalize" },
    { from: "comment_and_escalate_to_human", to: "finalize" },
  ],
};

export default flow;

function promptJudgeSolution(promptContext, intentOutput) {
  return [
    "You are doing maintainability-first PR triage for one PR.",
    "Use the PR context already in this session and the extracted intent below.",
    "Judge whether this PR is a good solution to the underlying problem.",
    "Use these verdicts:",
    '- "good_enough" if the solution is right-shaped and can continue.',
    '- "localized_fix" if it only treats a symptom or is too local for the real problem.',
    '- "bad_fix" if it is solving the wrong problem or is the wrong approach.',
    '- "unclear" if the PR is too unclear to evaluate confidently.',
    '- "needs_human_call" if it seems plausible but needs a design decision or human call before continuing.',
    "Route `close_pr` for localized_fix, bad_fix, or unclear.",
    "Route `comment_and_escalate_to_human` for needs_human_call.",
    "Route `judge_refactor` for good_enough.",
    "Return exactly one JSON object with this shape:",
    "{",
    '  "verdict": "good_enough" | "localized_fix" | "bad_fix" | "unclear" | "needs_human_call",',
    '  "route": "close_pr" | "comment_and_escalate_to_human" | "judge_refactor",',
    '  "reason": "short explanation",',
    '  "evidence": ["brief evidence item"]',
    "}",
    "",
    `Extracted intent: ${JSON.stringify(intentOutput, null, 2)}`,
    "",
    promptContext,
  ].join("\n");
}

function promptJudgeRefactor(intentOutput, solutionOutput) {
  return [
    "You are still triaging the same PR.",
    "Use the PR context already in this session, plus the extracted intent and solution judgment below.",
    "Judge whether this PR needs no refactor, a superficial refactor, or a fundamental refactor.",
    "Route `review_loop` for none.",
    "Route `do_superficial_refactor` for superficial.",
    "Route `comment_and_escalate_to_human` for fundamental.",
    "Return exactly one JSON object with this shape:",
    "{",
    '  "refactor_needed": "none" | "superficial" | "fundamental",',
    '  "route": "review_loop" | "do_superficial_refactor" | "comment_and_escalate_to_human",',
    '  "reason": "short explanation"',
    "}",
    "",
    `Extracted intent: ${JSON.stringify(intentOutput, null, 2)}`,
    `Solution judgment: ${JSON.stringify(solutionOutput, null, 2)}`,
  ].join("\n");
}

function promptSuperficialRefactor(intentOutput, solutionOutput, refactorOutput) {
  return [
    "You are still working on the same PR in the same session.",
    "Do the superficial refactor needed before the PR moves into the review loop.",
    "Keep the change superficial. Do not reframe the problem or turn this into a fundamental rewrite.",
    "Return exactly one JSON object with this shape:",
    "{",
    '  "route": "review_loop",',
    '  "summary": "short explanation",',
    '  "files_touched": ["path/to/file"]',
    "}",
    "",
    `Extracted intent: ${JSON.stringify(intentOutput, null, 2)}`,
    `Solution judgment: ${JSON.stringify(solutionOutput, null, 2)}`,
    `Refactor judgment: ${JSON.stringify(refactorOutput, null, 2)}`,
  ].join("\n");
}

function promptFixCiFailures(intentOutput, solutionOutput, refactorOutput, reviewOutput) {
  return [
    "Stay on the autonomous CI lane for this single PR.",
    "Check CI/CD for the current PR head and decide whether any failures are actually related to the PR.",
    "Fix related failures you can fix in this pass.",
    "If related failures still remain or the PR needs another CI pass, route back to fix_ci_failures.",
    "If CI is green or remaining failures are clearly unrelated, route to comment_and_escalate_to_human for the final human handoff.",
    "Return exactly one JSON object with this shape:",
    "{",
    '  "route": "fix_ci_failures" | "comment_and_escalate_to_human",',
    '  "ci_status": "related_failures_remain" | "green_or_unrelated",',
    '  "summary": "short explanation",',
    '  "related_failures": ["brief failure"],',
    '  "unrelated_failures": ["brief failure"]',
    "}",
    "",
    `Extracted intent: ${JSON.stringify(intentOutput, null, 2)}`,
    `Solution judgment: ${JSON.stringify(solutionOutput, null, 2)}`,
    `Refactor judgment: ${JSON.stringify(refactorOutput, null, 2)}`,
    `Review status: ${JSON.stringify(reviewOutput, null, 2)}`,
  ].join("\n");
}

function promptCloseComment(outputs) {
  return [
    "Write the final close-out result for this PR.",
    "The workflow reached the close path because the solution was bad, localized, or unclear.",
    "Return exactly one JSON object with this shape:",
    "{",
    '  "route": "close_pr",',
    '  "summary": "short explanation",',
    '  "comment": "markdown comment to post before closing the PR"',
    "}",
    "",
    decisionContext(outputs),
  ].join("\n");
}

function promptHumanComment(outputs) {
  return [
    "Write the final human handoff result for this PR.",
    "The workflow reached the human path either because a design decision is needed, a fundamental refactor is needed, or the PR cleared autonomous review and CI and now needs a human landing decision.",
    "Return exactly one JSON object with this shape:",
    "{",
    '  "route": "escalate_to_human",',
    '  "summary": "short explanation",',
    '  "human_decision_needed": "short explanation",',
    '  "comment": "markdown comment to post for the human handoff"',
    "}",
    "",
    decisionContext(outputs),
  ].join("\n");
}

function decisionContext(outputs) {
  return [
    `Intent: ${JSON.stringify(outputs.extract_intent ?? null, null, 2)}`,
    `Solution judgment: ${JSON.stringify(outputs.judge_solution ?? null, null, 2)}`,
    `Refactor judgment: ${JSON.stringify(outputs.judge_refactor ?? null, null, 2)}`,
    `Superficial refactor: ${JSON.stringify(outputs.do_superficial_refactor ?? null, null, 2)}`,
    `Review loop: ${JSON.stringify(outputs.review_loop ?? null, null, 2)}`,
    `CI loop: ${JSON.stringify(outputs.fix_ci_failures ?? null, null, 2)}`,
  ].join("\n");
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

function loadPrOutput(outputs) {
  return outputs.load_pr;
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

function formatPromptContext({
  repo,
  pr,
  linkedIssue,
  diff,
}) {
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
    if (!starts.includes(text[i] ?? "")) {
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
