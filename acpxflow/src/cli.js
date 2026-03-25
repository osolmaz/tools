#!/usr/bin/env node
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

import { AcpxClient, FlowRunner, GitHubClient } from "./index.js";

async function main() {
  const [, , command, flowFile, ...rest] = process.argv;

  if (command !== "run" || !flowFile) {
    printUsage();
    process.exitCode = 1;
    return;
  }

  const options = parseFlags(rest);
  requireFlag(options, "repo");
  requireFlag(options, "pr");
  requireFlag(options, "acpx-cwd");

  const flowModulePath = path.resolve(process.cwd(), flowFile);
  const flowModule = await import(pathToFileURL(flowModulePath).href);
  const flow = flowModule.default;

  const acpx = new AcpxClient({
    command: options.acpx ?? process.env.ACPX_CLI_PATH ?? "acpx",
    cwd: options["acpx-cwd"],
    agent: options.agent ?? "codex",
    timeoutSeconds: options.timeout ? Number(options.timeout) : 240,
  });

  const github = new GitHubClient();
  const outputRoot =
    options["output-dir"] ??
    path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..", "runs");

  const runner = new FlowRunner({
    acpx,
    github,
    outputRoot,
  });

  const result = await runner.run(flow, {
    repo: options.repo,
    prNumber: Number(options.pr),
  });

  process.stdout.write(`${JSON.stringify(result, null, 2)}\n`);
}

function parseFlags(argv) {
  const flags = {};
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (!token.startsWith("--")) {
      throw new Error(`Unexpected positional argument: ${token}`);
    }
    const key = token.slice(2);
    const value = argv[i + 1];
    if (!value || value.startsWith("--")) {
      throw new Error(`Missing value for --${key}`);
    }
    flags[key] = value;
    i += 1;
  }
  return flags;
}

function requireFlag(flags, key) {
  if (!flags[key]) {
    throw new Error(`Missing required flag --${key}`);
  }
}

function printUsage() {
  process.stderr.write(
    [
      "Usage:",
      "  node src/cli.js run <flow-file> --repo <owner/name> --pr <number> --acpx-cwd <repo-path> [--acpx <path>] [--agent codex] [--output-dir <dir>]",
    ].join("\n"),
  );
}

main().catch((error) => {
  process.stderr.write(`${error.stack ?? error.message}\n`);
  process.exitCode = 1;
});
