const flow = {
  name: "pr-triage",
  startAt: "load_pr",
  nodes: {
    load_pr: {
      kind: "compute",
      run: ({ input }) => loadPullRequestInput(input),
    },

    prepare_workspace: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptPrepareWorkspace(loadPrOutput(outputs));
      },
      parse: (text) => extractJson(text),
    },

    extract_intent: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptExtractIntent(loadPrOutput(outputs));
      },
      parse: (text) => extractJson(text),
    },

    judge_solution: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptJudgeSolution(loadPrOutput(outputs));
      },
      parse: (text) => extractJson(text),
    },

    judge_refactor: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptJudgeRefactor(loadPrOutput(outputs));
      },
      parse: (text) => extractJson(text),
    },

    do_superficial_refactor: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptDoSuperficialRefactor(loadPrOutput(outputs));
      },
      parse: (text) => extractJson(text),
    },

    review_loop: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptReviewLoop(loadPrOutput(outputs), Boolean(outputs.do_superficial_refactor));
      },
      parse: (text) => extractJson(text),
    },

    fix_ci_failures: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptFixCiFailures(loadPrOutput(outputs));
      },
      parse: (text) => extractJson(text),
    },

    comment_and_close_pr: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptCommentAndClose(loadPrOutput(outputs));
      },
      parse: (text) => extractJson(text),
    },

    comment_and_escalate_to_human: {
      kind: "acp",
      async prompt({ outputs }) {
        return promptCommentAndEscalate(loadPrOutput(outputs));
      },
      parse: (text) => extractJson(text),
    },

    finalize: {
      kind: "compute",
      run: ({ outputs, state }) => ({
        final: outputs.comment_and_close_pr ?? outputs.comment_and_escalate_to_human ?? null,
        intent: outputs.extract_intent ?? null,
        solution: outputs.judge_solution ?? null,
        refactor: outputs.judge_refactor ?? null,
        review: outputs.review_loop ?? null,
        ci: outputs.fix_ci_failures ?? null,
        sessionBindings: state.sessionBindings,
      }),
    },
  },
  edges: [
    { from: "load_pr", to: "prepare_workspace" },
    { from: "prepare_workspace", to: "extract_intent" },
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

function promptPrepareWorkspace(pr) {
  return [
    "You are processing one pull request at a time.",
    `Target PR: ${prRef(pr)}`,
    "Act autonomously inside the repo.",
    "Use git and gh yourself.",
    "Make sure the current workspace is checked out to the PR head. If it is not, use gh/git to fetch and check out the PR branch in this repo before continuing.",
    "Inspect the PR page, linked issue, changed files, and local diff yourself. Do not rely on prompt-injected diffs.",
    "When you need PR discussion, review, or comment state, prefer REST-backed `gh api` calls such as `repos/{owner}/{repo}/pulls/{pr}/reviews`, `repos/{owner}/{repo}/pulls/{pr}/comments`, `repos/{owner}/{repo}/issues/{pr}/comments`, and workflow-run endpoints. Do not rely on `gh pr view --comments`.",
    "Do not explain your work. Take the preparation actions first, then return only JSON.",
    "Return exactly one JSON object with this shape:",
    "{",
    '  "prepared": true,',
    '  "summary": "short explanation",',
    '  "head_ref": "branch or sha"',
    "}",
  ].join("\n");
}

function promptExtractIntent(pr) {
  return [
    "You are still in the same PR session.",
    `Target PR: ${prRef(pr)}`,
    "Use the checked-out repo, gh, and the context you already inspected in this session.",
    "Extract the plain-language human intent and the underlying problem.",
    "Do not paste the full PR body, issue body, diff, or earlier JSON back to me.",
    "Return exactly one JSON object with this shape and nothing else:",
    "{",
    '  "intent": "plain-language human goal",',
    '  "problem": "short description of the underlying issue",',
    '  "confidence": 0.0,',
    '  "reason": "short explanation"',
    "}",
  ].join("\n");
}

function promptJudgeSolution(pr) {
  return [
    "You are still in the same PR session.",
    `Target PR: ${prRef(pr)}`,
    "Use your current session understanding of the PR, issue, code, and diff.",
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
    "Do not repeat earlier JSON or the full diff.",
    "Return exactly one JSON object and nothing else:",
    "{",
    '  "verdict": "good_enough" | "localized_fix" | "bad_fix" | "unclear" | "needs_human_call",',
    '  "route": "close_pr" | "comment_and_escalate_to_human" | "judge_refactor",',
    '  "reason": "short explanation",',
    '  "evidence": ["brief evidence item"]',
    "}",
  ].join("\n");
}

function promptJudgeRefactor(pr) {
  return [
    "You are still in the same PR session.",
    `Target PR: ${prRef(pr)}`,
    "Use your current session understanding of the PR.",
    "Judge whether this PR needs no refactor, a superficial refactor, or a fundamental refactor.",
    "Route `review_loop` for none.",
    "Route `do_superficial_refactor` for superficial.",
    "Route `comment_and_escalate_to_human` for fundamental.",
    "Do not restate earlier outputs. Return only the new decision.",
    "Return exactly one JSON object and nothing else:",
    "{",
    '  "refactor_needed": "none" | "superficial" | "fundamental",',
    '  "route": "review_loop" | "do_superficial_refactor" | "comment_and_escalate_to_human",',
    '  "reason": "short explanation"',
    "}",
  ].join("\n");
}

function promptDoSuperficialRefactor(pr) {
  return [
    "You are still in the same PR session.",
    `Target PR: ${prRef(pr)}`,
    "Perform the superficial refactor directly in the checked-out repo.",
    "Keep it minor and maintainability-focused. Do not reframe the problem or turn this into a fundamental rewrite.",
    "If you change files, run focused checks when feasible, then commit and push the PR branch yourself.",
    "After taking the action, return only JSON.",
    "Return exactly one JSON object with this shape:",
    "{",
    '  "route": "review_loop",',
    '  "summary": "short explanation",',
    '  "files_touched": ["path/to/file"],',
    '  "committed": true | false',
    "}",
  ].join("\n");
}

function promptReviewLoop(pr, hadSuperficialRefactor) {
  return [
    "Stay on the autonomous review lane for this single PR.",
    `Target PR: ${prRef(pr)}`,
    "Use your existing session understanding. Do not ask the outer runtime to process your findings.",
    "Handle review in this order.",
    "First, inspect existing Codex review comments on GitHub for the current PR head and address any valid unresolved P0 or P1 findings from those reviews.",
    "Use stable REST-backed `gh api` calls for this, such as `repos/{owner}/{repo}/pulls/{pr}/reviews`, `repos/{owner}/{repo}/pulls/{pr}/comments`, and `repos/{owner}/{repo}/issues/{pr}/comments`. Do not rely on `gh pr view --comments`.",
    "Then fetch the PR base branch from origin, determine the correct updated base ref or merge base from the checked-out repo, and run a fresh local `codex review --base <base>` against that fresh base ref.",
    "Do not review against a stale local base branch, against the whole repository state, or against a stale local diff.",
    "If you find valid P0 or P1 issues from either the existing GitHub Codex reviews or the fresh local Codex review, fix them directly in the repo, run focused checks when feasible, and commit/push the branch yourself.",
    "If blocking review findings still remain after this pass, route back to `review_loop`.",
    "If blocking review findings are cleared, route to `fix_ci_failures`.",
    hadSuperficialRefactor
      ? "A superficial refactor was already done earlier in this run; build on the current branch state."
      : "No superficial refactor step ran earlier in this session.",
    "Do not restate prior JSON or the full diff.",
    "Return exactly one JSON object and nothing else:",
    "{",
    '  "route": "review_loop" | "fix_ci_failures",',
    '  "review_status": "blocking_findings_remain" | "clear",',
    '  "summary": "short explanation",',
    '  "github_codex_reviews_handled": true | false,',
    '  "local_codex_review_ran": true | false,',
    '  "blocking_findings": ["brief finding"],',
    '  "committed": true | false',
    "}",
  ].join("\n");
}

function promptFixCiFailures(pr) {
  return [
    "Stay on the autonomous CI lane for this single PR.",
    `Target PR: ${prRef(pr)}`,
    "Use gh and the checked-out repo yourself.",
    "Inspect current CI/check status for the PR head and decide whether any failures are actually related to this change.",
    "Use REST-backed `gh api` or other stable gh commands to inspect workflow runs and checks. Do not rely on fragile PR view comment output.",
    "If a workflow run is blocked only because it needs maintainer approval to run, approve or enable that run yourself if you have permission, for example with `gh api -X POST repos/{owner}/{repo}/actions/runs/{run_id}/approve`, then route back to `fix_ci_failures` so CI can be checked again after the run starts.",
    "If related failures exist, fix them directly in the repo, run focused checks when feasible, commit/push the branch yourself, and route back to `fix_ci_failures` if another CI pass is needed.",
    "If CI is green or remaining failures are clearly unrelated, route to `comment_and_escalate_to_human`.",
    "If the only remaining blocker is a workflow approval gate that you cannot clear yourself, route to `comment_and_escalate_to_human` and make that the explicit human action needed next.",
    "Do not restate earlier JSON or the full diff.",
    "Return exactly one JSON object and nothing else:",
    "{",
    '  "route": "fix_ci_failures" | "comment_and_escalate_to_human",',
    '  "ci_status": "related_failures_remain" | "green_or_unrelated" | "approval_blocked",',
    '  "summary": "short explanation",',
    '  "related_failures": ["brief failure"],',
    '  "unrelated_failures": ["brief failure"],',
    '  "workflow_approval_attempted": true | false,',
    '  "workflow_approved": true | false,',
    '  "committed": true | false',
    "}",
  ].join("\n");
}

function promptCommentAndClose(pr) {
  return [
    "You are on the close path for this PR.",
    `Target PR: ${prRef(pr)}`,
    "Write and post the comment using the exact triage markdown structure below. Do not invent a different layout.",
    "Use these exact headings in this order: `## Triage result`, `### Quick read`, `### Intent`, `### Why`, `### Codex review`, `### CI/CD`, `### Recommendation`.",
    "For this close path, the comment must make these top-line outcomes explicit:",
    "- `Solves the right problem: 🛑 Localized, bad, or unclear fix`",
    "- `Close PR: 🛑 Yes`",
    "- `Recommendation: 🏁 close PR`",
    "Use short plain-language bullets under `### Why`.",
    "Use this exact comment shape:",
    "```md",
    "## Triage result",
    "",
    "### Quick read",
    "- Intent valid: <✅ Yes / ❌ No>",
    "- Solves the right problem: 🛑 Localized, bad, or unclear fix",
    "- Close PR: 🛑 Yes",
    "- Refactor needed: <✅ None / 🔧 Superficial / 🧱 Fundamental>",
    "- Human attention: 🛑 Not applicable because PR should close",
    "- Recommendation: 🏁 close PR",
    "",
    "### Intent",
    "> <plain-language intention>",
    "",
    "### Why",
    "- <short reason>",
    "",
    "### Codex review",
    "- Status: <🧪 Not run / 🧪 Already present / ✅ Clear / 🔴 Blocking findings remain>",
    "- Notes: <short review summary>",
    "",
    "### CI/CD",
    "- Status: <🚦 Green / 🚦 Mixed but unrelated / 🔴 Related failures remain / ⏸️ Approval needed / ⏸️ Not checked>",
    "- Notes: <short CI summary>",
    "",
    "### Recommendation",
    "🏁 close PR",
    "```",
    "Post that comment directly on GitHub with `gh pr comment`.",
    "Then close the PR with `gh pr close`.",
    "Take the GitHub actions yourself in this run.",
    "Return exactly one JSON object and nothing else:",
    "{",
    '  "route": "close_pr",',
    '  "summary": "short explanation",',
    '  "comment_format_followed": true | false,',
    '  "comment_posted": true | false,',
    '  "pr_closed": true | false',
    "}",
  ].join("\n");
}

function promptCommentAndEscalate(pr) {
  return [
    "You are on the human handoff path for this PR.",
    `Target PR: ${prRef(pr)}`,
    "Write and post the comment using the exact triage markdown structure below. Do not invent a different layout.",
    "Use these exact headings in this order: `## Triage result`, `### Quick read`, `### Intent`, `### Why`, `### Codex review`, `### CI/CD`, `### Recommendation`.",
    "For this human handoff path, the comment must make these top-line outcomes explicit:",
    "- `Human attention: ⚠️ Required`",
    "- `Recommendation: 🏁 escalate to a human`",
    "- `Human decision needed: <explicit next human action>` near the top of the comment",
    "Use short plain-language bullets under `### Why`.",
    "Use this exact comment shape:",
    "```md",
    "## Triage result",
    "",
    "### Quick read",
    "- Intent valid: <✅ Yes / ❌ No>",
    "- Solves the right problem: <✅ Yes / ⚠️ Partly / ❌ No / 🛑 Localized, bad, or unclear fix>",
    "- Close PR: ✅ No",
    "- Refactor needed: <✅ None / 🔧 Superficial / 🧱 Fundamental>",
    "- Human attention: ⚠️ Required",
    "- Recommendation: 🏁 escalate to a human",
    "- Human decision needed: <design decision/human call | ready for human landing decision | workflow approval needed | other explicit reason>",
    "",
    "### Intent",
    "> <plain-language intention>",
    "",
    "### Why",
    "- <short reason>",
    "",
    "### Codex review",
    "- Status: <🧪 Not run / 🧪 Already present / ✅ Clear / 🔴 Blocking findings remain>",
    "- Notes: <short review summary>",
    "",
    "### CI/CD",
    "- Status: <🚦 Green / 🚦 Mixed but unrelated / 🔴 Related failures remain / ⏸️ Approval needed / ⏸️ Not checked>",
    "- Notes: <short CI summary>",
    "",
    "### Recommendation",
    "🏁 escalate to a human",
    "```",
    "If the reason is a blocked workflow approval gate, say plainly that the needed next action is approving or enabling the PR workflow run.",
    "Post that comment directly on GitHub with `gh pr comment`.",
    "Do not close the PR on this path.",
    "Take the GitHub action yourself in this run.",
    "Return exactly one JSON object and nothing else:",
    "{",
    '  "route": "escalate_to_human",',
    '  "summary": "short explanation",',
    '  "human_decision_needed": "short explanation",',
    '  "comment_format_followed": true | false,',
    '  "comment_posted": true | false',
    "}",
  ].join("\n");
}

function loadPullRequestInput(input) {
  const repo = String(input?.repo ?? "").trim();
  const prNumber = Number(input?.prNumber);

  if (!repo) {
    throw new Error('Flow input must include a non-empty "repo" string');
  }
  if (!Number.isInteger(prNumber) || prNumber <= 0) {
    throw new Error('Flow input must include a positive integer "prNumber"');
  }

  return {
    repo,
    prNumber,
    prUrl: `https://github.com/${repo}/pull/${prNumber}`,
  };
}

function loadPrOutput(outputs) {
  return outputs.load_pr;
}

function prRef(pr) {
  return `${pr.repo}#${pr.prNumber} (${pr.prUrl})`;
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

  for (const candidate of extractBalancedJsonCandidates(trimmed)) {
    const parsed = tryParse(candidate);
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

function extractBalancedJsonCandidates(text) {
  const candidates = [];
  const starts = ["{", "["];
  for (let i = 0; i < text.length; i += 1) {
    if (!starts.includes(text[i] ?? "")) {
      continue;
    }

    const result = scanBalanced(text, i);
    if (result) {
      candidates.push(result);
    }
  }

  return candidates;
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
