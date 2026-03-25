import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

export class GitHubClient {
  constructor(options = {}) {
    this.ghCommand = options.ghCommand ?? "gh";
    this.maxDiffChars = options.maxDiffChars ?? 30000;
  }

  async loadPullRequestContext({ repo, prNumber }) {
    const pr = await this.ghJson([
      "pr",
      "view",
      String(prNumber),
      "-R",
      repo,
      "--json",
      "number,title,body,author,url,additions,deletions,changedFiles,files,baseRefName,headRefName",
    ]);

    const linkedIssueNumber = findLinkedIssueNumber(pr.body);
    const linkedIssue = linkedIssueNumber
      ? await this.ghJson([
          "issue",
          "view",
          String(linkedIssueNumber),
          "-R",
          repo,
          "--json",
          "number,title,body,url",
        ])
      : null;

    const diff = await this.ghText(["pr", "diff", String(prNumber), "-R", repo]);
    const truncatedDiff =
      diff.length > this.maxDiffChars
        ? `${diff.slice(0, this.maxDiffChars)}\n\n[diff truncated at ${this.maxDiffChars} characters]`
        : diff;

    return {
      repo,
      pr,
      linkedIssue,
      promptContext: formatPromptContext({ repo, pr, linkedIssue, diff: truncatedDiff }),
    };
  }

  async ghJson(args) {
    const stdout = await this.ghText(args);
    return JSON.parse(stdout);
  }

  async ghText(args) {
    const result = await execFileAsync(this.ghCommand, args, {
      maxBuffer: 10 * 1024 * 1024,
    });
    return result.stdout.trim();
  }
}

function findLinkedIssueNumber(body) {
  const match = String(body ?? "").match(/\b(?:close[sd]?|fix(?:e[sd])?|resolve[sd]?)\s+#(\d+)\b/i);
  return match ? Number(match[1]) : null;
}

function formatPromptContext({ repo, pr, linkedIssue, diff }) {
  const files = (pr.files ?? [])
    .map((file) => `- ${file.path} (+${file.additions} / -${file.deletions})`)
    .join("\n");

  const issueSection = linkedIssue
    ? `Linked issue #${linkedIssue.number}: ${linkedIssue.title}\n${linkedIssue.body ?? ""}`
    : "No linked issue was found in the PR body.";

  return [
    `Repository: ${repo}`,
    `PR #${pr.number}: ${pr.title}`,
    `URL: ${pr.url}`,
    `Author: ${pr.author?.login ?? "unknown"}`,
    `Base: ${pr.baseRefName}`,
    `Head: ${pr.headRefName}`,
    `Changed files: ${pr.changedFiles}`,
    `Additions: ${pr.additions}`,
    `Deletions: ${pr.deletions}`,
    "",
    "PR body:",
    pr.body || "(empty)",
    "",
    "Changed files:",
    files || "(none)",
    "",
    "Underlying issue:",
    issueSection,
    "",
    "Diff:",
    diff || "(empty diff)",
  ].join("\n");
}
