import test from "node:test";
import assert from "node:assert/strict";

import { FlowRunner, compute, defineFlow } from "../lib/flow.js";

test("switch edges branch by structured output", async () => {
  const flow = defineFlow({
    name: "branch-test",
    startAt: "decide",
    nodes: {
      decide: compute({
        run: () => ({ next: "right" }),
      }),
      right: compute({
        run: () => ({ ok: true }),
      }),
      left: compute({
        run: () => ({ ok: false }),
      }),
    },
    edges: [
      {
        from: "decide",
        switch: {
          on: "$.next",
          cases: {
            left: "left",
            right: "right",
          },
        },
      },
    ],
  });

  const runner = new FlowRunner({
    acpx: null,
    github: null,
    outputRoot: "/tmp/acpx-agents-test",
  });

  const result = await runner.run(flow, {});
  assert.equal(result.state.outputs.right.ok, true);
  assert.equal(result.state.outputs.left, undefined);
});
