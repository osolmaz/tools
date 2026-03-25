import { acp, compute, defineFlow } from "../lib/flow.js";
import { extractJson } from "../lib/json.js";
import { loadPrompt } from "../lib/prompts.js";

export default defineFlow({
  name: "two-turn",
  startAt: "draft",
  nodes: {
    draft: acp({
      async prompt({ input }) {
        return await loadPrompt("two-turn/draft.md", {
          topic: input.topic ?? "How should we validate a new ACP adapter?",
        });
      },
      parse: (text) => extractJson(text),
    }),
    refine: acp({
      async prompt({ outputs }) {
        return await loadPrompt("two-turn/refine.md", {
          draft: JSON.stringify(outputs.draft),
        });
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
