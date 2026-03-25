import { acp, compute, defineFlow } from "../lib/flow.js";
import { extractJson } from "../lib/json.js";
import { loadPrompt } from "../lib/prompts.js";

export default defineFlow({
  name: "echo",
  startAt: "reply",
  nodes: {
    reply: acp({
      async prompt({ input }) {
        return await loadPrompt("echo/reply.md", {
          request: input.request ?? "Say hello in one short sentence.",
        });
      },
      parse: (text) => extractJson(text),
    }),
    finalize: compute({
      run: ({ outputs }) => outputs.reply,
    }),
  },
  edges: [{ from: "reply", to: "finalize" }],
});
