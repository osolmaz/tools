import { acp, compute, defineFlow } from "../acpxflow/src/flow.js";
import { extractJson } from "../acpxflow/src/json.js";

export default defineFlow({
  name: "echo",
  startAt: "reply",
  nodes: {
    reply: acp({
      async prompt({ input }) {
        return [
          "Return exactly one JSON object with this shape:",
          "{",
          '  "reply": "short response"',
          "}",
          "",
          `Request: ${input.request ?? "Say hello in one short sentence."}`,
        ].join("\n");
      },
      parse: (text) => extractJson(text),
    }),
    finalize: compute({
      run: ({ outputs }) => outputs.reply,
    }),
  },
  edges: [{ from: "reply", to: "finalize" }],
});
