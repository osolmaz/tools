import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export class AcpxClient {
  constructor(options) {
    this.command = options.command;
    this.cwd = options.cwd;
    this.agent = options.agent ?? "codex";
    this.timeoutSeconds = options.timeoutSeconds ?? 240;
  }

  async createSession(sessionName) {
    await this.run([
      "--cwd",
      this.cwd,
      this.agent,
      "sessions",
      "new",
      "--name",
      sessionName,
    ]);
    return this.showSession(sessionName);
  }

  async showSession(sessionName) {
    const stdout = await this.run([
      "--cwd",
      this.cwd,
      "--format",
      "json",
      this.agent,
      "sessions",
      "show",
      sessionName,
    ]);
    return JSON.parse(stdout);
  }

  async promptSession(sessionName, prompt) {
    return this.run([
      "--cwd",
      this.cwd,
      "--deny-all",
      "--format",
      "quiet",
      "--timeout",
      String(this.timeoutSeconds),
      this.agent,
      "-s",
      sessionName,
      prompt,
    ]);
  }

  async execPrompt(prompt) {
    return this.run([
      "--cwd",
      this.cwd,
      "--deny-all",
      "--format",
      "quiet",
      "--timeout",
      String(this.timeoutSeconds),
      this.agent,
      "exec",
      prompt,
    ]);
  }

  async run(args) {
    const command = resolveCommand(this.command);
    try {
      const result = await execFileAsync(command.file, [...command.args, ...args], {
        maxBuffer: 10 * 1024 * 1024,
      });
      return result.stdout.trim();
    } catch (error) {
      const stderr = error.stderr?.trim();
      const stdout = error.stdout?.trim();
      const detail = [stderr, stdout].filter(Boolean).join("\n");
      throw new Error(detail || error.message);
    }
  }
}

function resolveCommand(command) {
  if (!command || command === "acpx") {
    return { file: "acpx", args: [] };
  }

  if (command.endsWith(".js")) {
    return { file: "node", args: [command] };
  }

  return { file: command, args: [] };
}
