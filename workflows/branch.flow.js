import { acp, compute, defineFlow } from "../acpxflow/src/flow.js";
import { extractJson } from "../acpxflow/src/json.js";

export default defineFlow({
  name: "branch",
  startAt: "classify",
  nodes: {
    classify: acp({
      async prompt({ input }) {
        return [
          "Read the task below.",
          "If it is concrete and scoped, route `continue`.",
          "If it is ambiguous or needs clarification, route `needs_review`.",
          "Return exactly one JSON object with this shape:",
          "{",
          '  "route": "continue" | "needs_review",',
          '  "reason": "short explanation"',
          "}",
          "",
          `Task: ${input.task ?? "FIX: add a regression test for the reconnect bug."}`,
        ].join("\n");
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
