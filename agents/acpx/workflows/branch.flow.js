import { acp, compute, defineFlow } from "../lib/flow.js";
import { extractJson } from "../lib/json.js";
import { loadPrompt } from "../lib/prompts.js";

export default defineFlow({
  name: "branch",
  startAt: "classify",
  nodes: {
    classify: acp({
      async prompt({ input }) {
        return await loadPrompt("branch/classify.md", {
          task: input.task ?? "FIX: add a regression test for the reconnect bug.",
        });
      },
      parse: (text) => extractJson(text),
    }),
    continue_lane: compute({
      run: ({ outputs }) => ({
        route: "continue",
        summary: outputs.classify.reason,
      }),
    }),
    needs_review: compute({
      run: ({ outputs }) => ({
        route: "needs_review",
        summary: outputs.classify.reason,
      }),
    }),
  },
  edges: [
    {
      from: "classify",
      switch: {
        on: "$.route",
        cases: {
          continue: "continue_lane",
          needs_review: "needs_review",
        },
      },
    },
  ],
});
