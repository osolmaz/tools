import { acp, compute, defineFlow } from "../lib/flow.js";
import { extractJson } from "../lib/json.js";
import { loadPrompt } from "../lib/prompts.js";

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
        return await loadPrompt("pr-triage/solution-fit.md", {
          promptContext: outputs.load_pr.promptContext,
        });
      },
      parse: (text) => extractJson(text),
    }),

    issue_clarity: acp({
      async prompt() {
        return await loadPrompt("pr-triage/issue-clarity.md");
      },
      parse: (text) => extractJson(text),
    }),

    scope_assessment: acp({
      async prompt() {
        return await loadPrompt("pr-triage/scope-assessment.md");
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
        return await loadPrompt("pr-triage/continue-lane.md", {
          reasons: JSON.stringify(outputs.route.reasons),
        });
      },
      parse: (text) => extractJson(text),
    }),

    human_review: acp({
      async prompt({ outputs }) {
        return await loadPrompt("pr-triage/human-review.md", {
          reasons: JSON.stringify(outputs.route.reasons),
        });
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
