import { acp, compute, defineFlow } from "../flow.js";
import { extractJson } from "../json.js";

export default defineFlow({
  name: "pr-triage",
  startAt: "load_pr",
  nodes: {
    load_pr: compute({
      run: async ({ input, services }) =>
        services.github.loadPullRequestContext({
          repo: input.repo,
          prNumber: input.prNumber,
        }),
    }),

    solution_fit: acp({
      async prompt({ outputs }) {
        return [
          "You are doing maintainability-first PR triage.",
          "Question: is this the right solution for the underlying issue, or is it only a localized fix that does not address the real problem?",
          "Use only the PR context below.",
          "Return exactly one JSON object with this shape:",
          '{',
          '  "verdict": "right_solution" | "localized_fix" | "wrong_problem" | "unclear",',
          '  "confidence": 0.0,',
          '  "reason": "short explanation",',
          '  "evidence": ["short bullet", "short bullet"]',
          '}',
          "",
          outputs.load_pr.promptContext,
        ].join("\n");
      },
      parse: (text) => extractJson(text),
    }),

    issue_clarity: acp({
      async prompt() {
        return [
          "Use the PR context already in this session.",
          "Judge whether the underlying issue is clearly framed enough for safe autonomous continuation.",
          "If there is no linked issue, decide whether the PR body still makes the underlying problem clear.",
          "Return exactly one JSON object with this shape:",
          '{',
          '  "verdict": "clear" | "ambiguous" | "conflicting",',
          '  "confidence": 0.0,',
          '  "reason": "short explanation"',
          '}',
        ].join("\n");
      },
      parse: (text) => extractJson(text),
    }),

    scope_assessment: acp({
      async prompt() {
        return [
          "Use the PR context and earlier reasoning already in this session.",
          "Judge whether the scope is appropriately shaped for the codebase.",
          "Return exactly one JSON object with this shape:",
          '{',
          '  "scope": "appropriately_local" | "too_local" | "cross_cutting_needed",',
          '  "refactor_needed": "none" | "superficial" | "fundamental",',
          '  "human_judgment_needed": true,',
          '  "reason": "short explanation"',
          '}',
        ].join("\n");
      },
      parse: (text) => extractJson(text),
    }),

    route: compute({
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
    }),

    continue_lane: acp({
      async prompt({ outputs }) {
        return [
          "We are continuing on the autonomous lane.",
          "The runtime routed here because the earlier checks did not raise blockers.",
          "Return exactly one JSON object with this shape:",
          '{',
          '  "route": "continue",',
          '  "summary": "short explanation",',
          '  "next_actions": ["action", "action"],',
          '  "residual_risks": ["risk", "risk"]',
          '}',
          "",
          `Runtime reasons: ${JSON.stringify(outputs.route.reasons)}`,
        ].join("\n");
      },
      parse: (text) => extractJson(text),
    }),

    human_review: acp({
      async prompt({ outputs }) {
        return [
          "We are routing this PR to human review.",
          "Return exactly one JSON object with this shape:",
          '{',
          '  "route": "human_review",',
          '  "summary": "short explanation",',
          '  "blocking_reasons": ["reason", "reason"],',
          '  "questions_for_human": ["question", "question"]',
          '}',
          "",
          `Runtime reasons: ${JSON.stringify(outputs.route.reasons)}`,
        ].join("\n");
      },
      parse: (text) => extractJson(text),
    }),

    finalize: compute({
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
    }),
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
});
