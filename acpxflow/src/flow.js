import { mkdir, rename, writeFile, appendFile } from "node:fs/promises";
import path from "node:path";
import crypto from "node:crypto";

export function defineFlow(spec) {
  return spec;
}

export function acp(options) {
  return { kind: "acp", ...options };
}

export function compute(options) {
  return { kind: "compute", ...options };
}

export class FlowRunner {
  constructor(options) {
    this.acpx = options.acpx;
    this.github = options.github;
    this.outputRoot = options.outputRoot;
  }

  async run(flow, input) {
    const runId = createRunId(flow.name, input);
    const runDir = path.join(this.outputRoot, runId);
    const state = {
      runId,
      flowName: flow.name,
      startedAt: new Date().toISOString(),
      status: "running",
      input,
      outputs: {},
      steps: [],
      sessionBindings: {},
    };

    await mkdir(runDir, { recursive: true });
    await this.persist(runDir, state, { type: "run_started" });

    let current = flow.startAt;
    while (current) {
      const node = flow.nodes[current];
      if (!node) {
        throw new Error(`Unknown node: ${current}`);
      }

      const startedAt = new Date().toISOString();
      const context = this.makeContext(state, input);
      let output;
      let promptText = null;
      let rawText = null;
      let sessionInfo = null;

      if (node.kind === "compute") {
        output = await node.run(context);
      } else if (node.kind === "acp") {
        promptText = await node.prompt(context);
        if (node.session?.kind === "isolated") {
          rawText = await this.acpx.execPrompt(promptText);
        } else {
          sessionInfo = await this.ensureSession(state, flow, input, node.session?.handle ?? "main");
          rawText = await this.acpx.promptSession(sessionInfo.name, promptText);
        }
        output = await node.parse(rawText, context);
      } else {
        throw new Error(`Unsupported node kind: ${node.kind}`);
      }

      const step = {
        nodeId: current,
        kind: node.kind,
        startedAt,
        finishedAt: new Date().toISOString(),
        promptText,
        rawText,
        output,
        session: sessionInfo,
      };
      state.outputs[current] = output;
      state.steps.push(step);

      await this.persist(runDir, state, {
        type: "node_completed",
        nodeId: current,
        output,
      });

      current = resolveNext(flow.edges, current, output);
    }

    state.status = "completed";
    state.finishedAt = new Date().toISOString();
    await this.persist(runDir, state, { type: "run_completed" });
    return { runDir, state };
  }

  makeContext(state, input) {
    return {
      input,
      outputs: state.outputs,
      state,
      services: {
        github: this.github,
        acpx: this.acpx,
      },
    };
  }

  async ensureSession(state, flow, input, handle) {
    const existing = state.sessionBindings[handle];
    if (existing) {
      return existing;
    }

    const name = `${flow.name}-pr-${input.prNumber}-${handle}-${state.runId.slice(-8)}`;
    const session = await this.acpx.createSession(name);
    const binding = {
      handle,
      name,
      acpxRecordId: session.acpxRecordId ?? session.acpx_record_id ?? null,
      acpSessionId: session.acpSessionId ?? session.acp_session_id ?? null,
    };
    state.sessionBindings[handle] = binding;
    return binding;
  }

  async persist(runDir, state, event) {
    const runPath = path.join(runDir, "run.json");
    const tmpPath = `${runPath}.tmp`;
    await writeFile(tmpPath, JSON.stringify(state, null, 2));
    await rename(tmpPath, runPath);
    if (event) {
      await appendFile(
        path.join(runDir, "events.ndjson"),
        `${JSON.stringify({ at: new Date().toISOString(), ...event })}\n`,
      );
    }
  }
}

function resolveNext(edges, from, output) {
  const edge = edges.find((candidate) => candidate.from === from);
  if (!edge) {
    return null;
  }

  if (edge.to) {
    return edge.to;
  }

  if (edge.switch) {
    const value = getByPath(output, edge.switch.on);
    const next = edge.switch.cases[value];
    if (!next) {
      throw new Error(`No switch case for ${edge.switch.on}=${JSON.stringify(value)}`);
    }
    return next;
  }

  throw new Error(`Unsupported edge from ${from}`);
}

function getByPath(value, jsonPath) {
  if (!jsonPath.startsWith("$.")) {
    throw new Error(`Unsupported JSON path: ${jsonPath}`);
  }

  return jsonPath
    .slice(2)
    .split(".")
    .reduce((current, key) => (current == null ? undefined : current[key]), value);
}

function createRunId(flowName, input) {
  const stamp = new Date().toISOString().replaceAll(":", "").replaceAll(".", "");
  const slug = flowName.replace(/[^a-z0-9]+/gi, "-").replace(/^-+|-+$/g, "").toLowerCase();
  const suffix = crypto.randomUUID().slice(0, 8);
  return `${stamp}-${slug}-pr-${input.prNumber}-${suffix}`;
}
