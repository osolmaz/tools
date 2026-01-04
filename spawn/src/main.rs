use anyhow::{Context, Result, bail};
use clap::{Parser, Subcommand};
use regex::Regex;
use shell_words::split as shell_split;
use std::fs;
use std::path::PathBuf;
use std::process::Command;

#[derive(Parser, Debug)]
#[command(
    name = "spawn",
    version,
    about = "Spawn tmux sessions from markdown todos"
)]
struct Cli {
    /// Path to markdown file containing todos
    #[arg(short, long, value_name = "FILE")]
    file: PathBuf,

    /// Tmux session name
    #[arg(long, default_value = "spawn")]
    session: String,

    /// Prefix to add before each prompt
    #[arg(long)]
    prefix: Option<String>,

    /// Suffix to add after each prompt
    #[arg(long)]
    suffix: Option<String>,

    /// Tmux binary to use
    #[arg(long, default_value = "tmux")]
    tmux_bin: String,

    /// Replace existing tmux session if it already exists
    #[arg(long)]
    replace: bool,

    /// Print prompts instead of launching tmux
    #[arg(long)]
    dry_run: bool,

    /// Attach to the tmux session after spawning
    #[arg(long)]
    attach: bool,

    /// Skip confirmation prompt (assume yes)
    #[arg(long)]
    yes: bool,

    #[command(subcommand)]
    command: Commands,
}

#[derive(Subcommand, Debug)]
enum Commands {
    /// Run a harness command template that includes {item}
    Run {
        /// Harness command template (use {item} to insert the prompt)
        #[arg(required = true, trailing_var_arg = true, allow_hyphen_values = true)]
        harness_cmd: Vec<String>,
    },
}

fn main() -> Result<()> {
    let cli = Cli::parse();
    let content = fs::read_to_string(&cli.file)
        .with_context(|| format!("failed to read {}", cli.file.display()))?;

    let items = extract_unchecked_todos(&content);
    if items.is_empty() {
        bail!("no unchecked todos found in {}", cli.file.display());
    }

    let prompts: Vec<String> = items
        .into_iter()
        .map(|item| build_prompt(&item, cli.prefix.as_deref(), cli.suffix.as_deref()))
        .collect();

    if cli.dry_run {
        for (i, prompt) in prompts.iter().enumerate() {
            println!("--- prompt {} ---\n{}\n", i + 1, prompt);
        }
        return Ok(());
    }

    let harness_cmd = match &cli.command {
        Commands::Run { harness_cmd } => harness_cmd,
    };
    let harness_cmd = normalize_harness_cmd(harness_cmd)?;

    if !cli.yes {
        if !confirm_spawn(&cli, &harness_cmd, &prompts)? {
            println!("aborted.");
            return Ok(());
        }
    }
    let used_existing_session = spawn_tmux(&cli, &harness_cmd, &prompts)?;

    if cli.attach {
        run_tmux(&cli.tmux_bin, ["attach", "-t", cli.session.as_str()])?;
    } else {
        if used_existing_session {
            println!(
                "tmux session '{}' already existed; added {} window(s).",
                cli.session,
                prompts.len()
            );
        } else {
            println!(
                "tmux session '{}' created with {} window(s).",
                cli.session,
                prompts.len()
            );
        }
        println!("attach with: tmux attach -t {}", cli.session);
    }

    Ok(())
}

fn extract_unchecked_todos(content: &str) -> Vec<String> {
    let re = Regex::new(r"^(\s*)([-*+])\s+\[\s*\]\s*(.*)$").unwrap();
    let lines: Vec<&str> = content.lines().collect();
    let mut items = Vec::new();
    let mut i = 0;

    while i < lines.len() {
        let line = lines[i];
        if let Some(caps) = re.captures(line) {
            let indent = caps.get(1).map(|m| m.as_str().len()).unwrap_or(0);
            let mut block = vec![line.to_string()];
            let mut j = i + 1;

            while j < lines.len() {
                let next = lines[j];
                if next.trim().is_empty() {
                    block.push(next.to_string());
                    j += 1;
                    continue;
                }

                let next_indent = next.chars().take_while(|c| c.is_whitespace()).count();
                if next_indent > indent {
                    block.push(next.to_string());
                    j += 1;
                    continue;
                }
                break;
            }

            items.push(block.join("\n"));
            i = j;
        } else {
            i += 1;
        }
    }

    items
}

fn build_prompt(item: &str, prefix: Option<&str>, suffix: Option<&str>) -> String {
    let mut parts = Vec::new();
    if let Some(p) = prefix {
        if !p.trim().is_empty() {
            parts.push(p.trim_end().to_string());
        }
    }
    parts.push(item.trim_end().to_string());
    if let Some(s) = suffix {
        if !s.trim().is_empty() {
            parts.push(s.trim_start().to_string());
        }
    }
    parts.join("\n\n")
}

fn spawn_tmux(cli: &Cli, harness_cmd: &[String], prompts: &[String]) -> Result<bool> {
    let session = cli.session.as_str();
    let tmux = cli.tmux_bin.as_str();

    let mut created_session = false;
    let mut used_existing_session = false;
    let start_index = if tmux_has_session(tmux, session)? {
        if cli.replace {
            run_tmux(tmux, ["kill-session", "-t", session])?;
            run_tmux(tmux, ["new-session", "-d", "-s", session, "-n", "1"])?;
            created_session = true;
            1
        } else {
            used_existing_session = true;
            tmux_next_window_index(tmux, session)?
        }
    } else {
        run_tmux(tmux, ["new-session", "-d", "-s", session, "-n", "1"])?;
        created_session = true;
        1
    };

    for (idx, prompt) in prompts.iter().enumerate() {
        let window_number = start_index + idx as u32;
        let window_name = format!("{}", window_number);
        if created_session && idx == 0 {
            // use the initial window created with the session
        } else {
            run_tmux(tmux, ["new-window", "-t", session, "-n", &window_name])?;
        }

        let target = format!("{}:{}", session, window_name);
        let cmd = build_shell_command(harness_cmd, prompt)?;
        run_tmux(tmux, ["send-keys", "-t", &target, "-l", &cmd])?;
        run_tmux(tmux, ["send-keys", "-t", &target, "C-m"])?;
    }

    Ok(used_existing_session)
}

fn build_shell_command(harness_cmd: &[String], prompt: &str) -> Result<String> {
    if !contains_item_token(harness_cmd) {
        bail!("harness command must include {{item}}");
    }
    let mut parts = Vec::with_capacity(harness_cmd.len());
    for arg in harness_cmd {
        let replaced = replace_item_token(arg, prompt);
        parts.push(shell_escape(&replaced));
    }
    Ok(parts.join(" "))
}

fn shell_escape(input: &str) -> String {
    if input.is_empty() {
        return "''".to_string();
    }
    if !input.contains([
        ' ', '\t', '\n', '\r', '\'', '"', '\\', '$', '`', '!', '(', ')',
    ]) {
        return input.to_string();
    }
    let escaped = input.replace('\'', r#"'"'"'"#);
    format!("'{}'", escaped)
}

fn normalize_harness_cmd(raw: &[String]) -> Result<Vec<String>> {
    if raw.is_empty() {
        bail!("harness command is empty");
    }
    if raw.len() == 1 {
        let single = raw[0].trim();
        if single.chars().any(char::is_whitespace) {
            let parsed = shell_split(single).with_context(
                || "failed to parse harness command string; try quoting individual args or use --",
            )?;
            if parsed.is_empty() {
                bail!("harness command is empty");
            }
            return Ok(parsed);
        }
    }
    Ok(raw.to_vec())
}

fn confirm_spawn(cli: &Cli, harness_cmd: &[String], prompts: &[String]) -> Result<bool> {
    let count = prompts.len();
    println!("About to create tmux session '{}'", cli.session);
    if cli.replace {
        println!("  - will replace existing session if present");
    }
    println!("  - windows: {}", count);
    println!("  - harness: {}", harness_cmd.join(" "));
    print_prompt_previews(prompts);
    println!("Proceed? [Y/n] ");

    let mut input = String::new();
    std::io::stdin()
        .read_line(&mut input)
        .context("failed to read confirmation input")?;
    let answer = input.trim().to_ascii_lowercase();
    Ok(answer.is_empty() || answer == "y" || answer == "yes")
}

fn print_prompt_previews(prompts: &[String]) {
    let preview_count = 5.min(prompts.len());
    println!("  - preview ({} of {}):", preview_count, prompts.len());
    for (idx, prompt) in prompts.iter().take(preview_count).enumerate() {
        let mut lines = prompt.lines();
        let first = lines.next().unwrap_or("");
        let mut preview = first.trim_end().to_string();
        if let Some(next) = lines.next() {
            if !next.trim().is_empty() {
                preview.push_str(" …");
            }
        }
        if preview.is_empty() {
            preview = "<empty>".to_string();
        }
        println!("    {}. {}", idx + 1, preview);
    }
    if prompts.len() > preview_count {
        println!("    … and {} more", prompts.len() - preview_count);
    }
}

fn contains_item_token(args: &[String]) -> bool {
    args.iter()
        .any(|arg| ITEM_TOKENS.iter().any(|token| arg.contains(token)))
}

fn replace_item_token(arg: &str, prompt: &str) -> String {
    let mut out = arg.to_string();
    for token in ITEM_TOKENS {
        out = out.replace(token, prompt);
    }
    out
}

const ITEM_TOKENS: [&str; 1] = ["{item}"];

fn tmux_has_session(tmux: &str, session: &str) -> Result<bool> {
    let status = Command::new(tmux)
        .args(["has-session", "-t", session])
        .status();
    match status {
        Ok(s) if s.success() => Ok(true),
        Ok(_) => Ok(false),
        Err(e) => Err(e).with_context(|| format!("failed to run {}", tmux)),
    }
}

fn tmux_next_window_index(tmux: &str, session: &str) -> Result<u32> {
    let output = Command::new(tmux)
        .args(["list-windows", "-t", session, "-F", "#I"])
        .output()
        .with_context(|| format!("failed to run {}", tmux))?;
    if !output.status.success() {
        bail!("tmux command failed: {}", tmux);
    }
    let stdout = String::from_utf8_lossy(&output.stdout);
    let mut max_index: Option<u32> = None;
    for line in stdout.lines() {
        if let Ok(num) = line.trim().parse::<u32>() {
            max_index = Some(max_index.map_or(num, |cur| cur.max(num)));
        }
    }
    Ok(max_index.unwrap_or(0).saturating_add(1))
}

fn run_tmux<I, S>(tmux: &str, args: I) -> Result<()>
where
    I: IntoIterator<Item = S>,
    S: AsRef<std::ffi::OsStr>,
{
    let status = Command::new(tmux)
        .args(args)
        .status()
        .with_context(|| format!("failed to run {}", tmux))?;
    if !status.success() {
        bail!("tmux command failed: {}", tmux);
    }
    Ok(())
}
