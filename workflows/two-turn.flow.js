import { acp, compute, defineFlow } from "../acpxflow/src/flow.js";
import { extractJson } from "../acpxflow/src/json.js";

export default defineFlow({
  name: "two-turn",
  startAt: "draft",
  nodes: {
    draft: acp({
      async prompt({ input }) {
        return [
          "Write a short draft answer about the topic below.",
          "Return exactly one JSON object with this shape:",
          "{",
          '  "draft": "short paragraph"',
          "}",
          "",
          `Topic: ${input.topic ?? "How should we validate a new ACP adapter?"}`,
        ].join("\n");
      },
      parse: (text) => extractJson(text),
    }),
    refine: acp({
      async prompt({ outputs }) {
        return [
          "Use the earlier draft already in this session.",
          "Turn it into a concise checklist.",
          "Return exactly one JSON object with this shape:",
          "{",
          '  "checklist": ["item", "item"]',
          "}",
          "",
          `Draft: ${JSON.stringify(outputs.draft)}`,
        ].join("\n");
      },
      parse: (text) => extractJson(text),
    }),
    finalize: compute({
      run: ({ outputs }) => outputs.refine,
    }),
  },
  edges: [
    { from: "draft", to: "refine" },
    { from: "refine", to: "finalize" },
  ],
});
