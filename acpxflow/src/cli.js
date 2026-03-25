#!/usr/bin/env node
import { readFile } from "node:fs/promises";
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
  requireFlag(options, "acpx-cwd");
  const input = await readInput(options);

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
    ...input,
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

async function readInput(flags) {
  if (flags["input-json"] && flags["input-file"]) {
    throw new Error("Use only one of --input-json or --input-file");
  }

  if (flags["input-json"]) {
    return parseJson(flags["input-json"], "--input-json");
  }

  if (flags["input-file"]) {
    return parseJson(await readFile(path.resolve(flags["input-file"]), "utf8"), "--input-file");
  }

  if (flags.repo || flags.pr) {
    requireFlag(flags, "repo");
    requireFlag(flags, "pr");
    return {
      repo: flags.repo,
      prNumber: Number(flags.pr),
    };
  }

  return {};
}

function parseJson(raw, label) {
  try {
    return JSON.parse(raw);
  } catch (error) {
    throw new Error(`${label} must contain valid JSON: ${error.message}`);
  }
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
      "  node src/cli.js run <flow-file> --acpx-cwd <repo-path> [--input-json <json> | --input-file <path> | --repo <owner/name> --pr <number>] [--acpx <path>] [--agent codex] [--output-dir <dir>]",
    ].join("\n"),
  );
}

main().catch((error) => {
  process.stderr.write(`${error.stack ?? error.message}\n`);
  process.exitCode = 1;
});
