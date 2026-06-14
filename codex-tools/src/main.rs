use std::collections::HashSet;
use std::env;
use std::fs::{self, File, OpenOptions};
use std::io::{self, BufRead, BufReader, Write};
use std::path::{Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use anyhow::{Context, Result, anyhow, bail};
use clap::{Args, Parser, Subcommand};
use rusqlite::{Connection, OptionalExtension, params};
use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Parser)]
#[command(about = "Local utilities for Codex session files")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Debug, Subcommand)]
enum Command {
    /// Extract recoverable plaintext messages from a Codex rollout JSONL file.
    Extract(ExtractArgs),
    /// Change the stored working directory for a Codex session.
    SetCwd(SetCwdArgs),
}

#[derive(Debug, Args)]
struct ExtractArgs {
    /// Rollout JSONL file to inspect.
    #[arg(value_name = "INPUT")]
    input: PathBuf,

    /// Output machine-readable JSON Lines instead of Markdown.
    #[arg(long)]
    jsonl: bool,

    /// Also print opaque encrypted_content locations and lengths.
    #[arg(long)]
    include_encrypted: bool,

    /// Include injected setup/instruction messages such as developer instructions and AGENTS.md.
    #[arg(long)]
    include_setup: bool,
}

#[derive(Debug, Args)]
struct SetCwdArgs {
    /// Session id, unique session id prefix, or rollout JSONL path.
    #[arg(value_name = "SESSION")]
    target: String,

    /// New working directory for the session.
    #[arg(value_name = "CWD")]
    cwd: PathBuf,

    /// Codex home directory. Defaults to CODEX_HOME or ~/.codex.
    #[arg(long, value_name = "DIR")]
    codex_home: Option<PathBuf>,

    /// State SQLite DB. Defaults to <codex-home>/state_5.sqlite.
    #[arg(long, value_name = "DB")]
    state_db: Option<PathBuf>,

    /// Do not add the new cwd to ~/.codex/config.toml as a trusted project.
    #[arg(long)]
    no_trust_project: bool,

    /// Show what would change without writing files.
    #[arg(long)]
    dry_run: bool,
}

#[derive(Debug, Clone)]
struct SessionTarget {
    id: String,
    rollout_path: PathBuf,
    current_cwd: Option<String>,
    db_row_found: bool,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
struct ExtractedMessage {
    line: usize,
    timestamp: Option<String>,
    source: String,
    index: Option<usize>,
    role: Option<String>,
    text: String,
}

#[derive(Debug, Clone, Serialize, PartialEq, Eq)]
struct EncryptedBlob {
    line: usize,
    timestamp: Option<String>,
    source: String,
    index: Option<usize>,
    chars: usize,
}

#[derive(Debug, Default)]
struct Extraction {
    messages: Vec<ExtractedMessage>,
    encrypted: Vec<EncryptedBlob>,
}

fn main() -> Result<()> {
    if let Err(error) = run() {
        if is_broken_pipe(&error) {
            return Ok(());
        }
        return Err(error);
    }
    Ok(())
}

fn run() -> Result<()> {
    match Cli::parse().command {
        Command::Extract(args) => run_extract(args),
        Command::SetCwd(args) => run_set_cwd(args),
    }
}

fn run_extract(args: ExtractArgs) -> Result<()> {
    let extraction = extract_file(&args.input)?;
    let messages = filtered_messages(&extraction, args.include_setup);
    let stdout = io::stdout();
    let mut out = stdout.lock();

    if args.jsonl {
        write_jsonl(&mut out, &messages, &extraction, args.include_encrypted)?;
    } else {
        write_markdown(
            &mut out,
            &args.input,
            &messages,
            &extraction,
            args.include_encrypted,
        )?;
    }

    Ok(())
}

fn run_set_cwd(args: SetCwdArgs) -> Result<()> {
    let codex_home = args.codex_home.unwrap_or(resolve_codex_home()?);
    let state_db = args
        .state_db
        .unwrap_or_else(|| codex_home.join("state_5.sqlite"));
    let new_cwd = normalize_existing_dir(&args.cwd)?;
    let target = resolve_session_target(&args.target, &codex_home, &state_db)?;

    println!("session: {}", target.id);
    println!("rollout: {}", target.rollout_path.display());
    println!(
        "current cwd: {}",
        target.current_cwd.as_deref().unwrap_or("<unknown>")
    );
    println!("new cwd: {}", new_cwd.display());

    if args.dry_run {
        println!("dry run: no files changed");
        return Ok(());
    }

    if target.db_row_found {
        update_state_db_cwd(&state_db, &target.id, &new_cwd)?;
        println!("updated sqlite: {}", state_db.display());
    } else {
        println!("sqlite: no matching thread row found; skipped");
    }

    let jsonl_changes = rewrite_rollout_cwd(&target.rollout_path, &new_cwd)?;
    println!(
        "updated rollout metadata: {} rows",
        jsonl_changes.changed_rows
    );

    if !args.no_trust_project {
        let config_path = codex_home.join("config.toml");
        let changed = ensure_trusted_project(&config_path, &new_cwd)?;
        if changed {
            println!("trusted project added: {}", config_path.display());
        } else {
            println!("trusted project already present");
        }
    }

    Ok(())
}

fn resolve_codex_home() -> Result<PathBuf> {
    if let Some(value) = env::var_os("CODEX_HOME") {
        return Ok(PathBuf::from(value));
    }
    Ok(home_dir()?.join(".codex"))
}

fn home_dir() -> Result<PathBuf> {
    env::var_os("HOME")
        .map(PathBuf::from)
        .ok_or_else(|| anyhow!("HOME is not set"))
}

fn normalize_existing_dir(path: &Path) -> Result<PathBuf> {
    let canonical =
        fs::canonicalize(path).with_context(|| format!("failed to resolve {}", path.display()))?;
    if !canonical.is_dir() {
        bail!("{} is not a directory", canonical.display());
    }
    Ok(canonical)
}

fn resolve_session_target(
    target: &str,
    codex_home: &Path,
    state_db: &Path,
) -> Result<SessionTarget> {
    let target_path = PathBuf::from(target);
    if target_path.exists() {
        let rollout_path = fs::canonicalize(&target_path)
            .with_context(|| format!("failed to resolve {}", target_path.display()))?;
        let (id, current_cwd) = read_rollout_identity(&rollout_path)?;
        let db_row = lookup_thread_by_id(state_db, &id)?;
        return Ok(SessionTarget {
            id,
            rollout_path,
            current_cwd: db_row
                .as_ref()
                .and_then(|row| row.cwd.clone())
                .or(current_cwd),
            db_row_found: db_row.is_some(),
        });
    }

    if state_db.exists()
        && let Some(session) = lookup_thread_by_prefix(state_db, target)?
    {
        return Ok(session);
    }

    let rollout_path = find_rollout_by_prefix(&codex_home.join("sessions"), target)?;
    let (id, current_cwd) = read_rollout_identity(&rollout_path)?;
    Ok(SessionTarget {
        id,
        rollout_path,
        current_cwd,
        db_row_found: false,
    })
}

#[derive(Debug, Clone)]
struct ThreadRow {
    id: String,
    rollout_path: PathBuf,
    cwd: Option<String>,
}

fn lookup_thread_by_id(state_db: &Path, id: &str) -> Result<Option<ThreadRow>> {
    if !state_db.exists() {
        return Ok(None);
    }
    let conn = Connection::open(state_db)
        .with_context(|| format!("failed to open {}", state_db.display()))?;
    integrity_check(&conn, state_db)?;
    conn.query_row(
        "SELECT id, rollout_path, cwd FROM threads WHERE id = ?1",
        params![id],
        row_to_thread,
    )
    .optional()
    .with_context(|| format!("failed to query {}", state_db.display()))
}

fn lookup_thread_by_prefix(state_db: &Path, prefix: &str) -> Result<Option<SessionTarget>> {
    let conn = Connection::open(state_db)
        .with_context(|| format!("failed to open {}", state_db.display()))?;
    integrity_check(&conn, state_db)?;
    let like = format!("{prefix}%");
    let rows = {
        let mut statement = conn.prepare(
            "SELECT id, rollout_path, cwd FROM threads WHERE id LIKE ?1 ORDER BY updated_at_ms DESC",
        )?;
        statement
            .query_map(params![like], row_to_thread)?
            .collect::<std::result::Result<Vec<_>, _>>()?
    };

    if rows.is_empty() {
        return Ok(None);
    }
    if rows.len() > 1 && !rows.iter().any(|row| row.id == prefix) {
        let matches = rows
            .iter()
            .take(10)
            .map(|row| row.id.as_str())
            .collect::<Vec<_>>()
            .join(", ");
        bail!("session prefix is ambiguous; matches: {matches}");
    }
    let row = rows
        .iter()
        .find(|row| row.id == prefix)
        .unwrap_or(&rows[0])
        .clone();
    Ok(Some(SessionTarget {
        id: row.id.clone(),
        rollout_path: row.rollout_path.clone(),
        current_cwd: row.cwd.clone(),
        db_row_found: true,
    }))
}

fn row_to_thread(row: &rusqlite::Row<'_>) -> rusqlite::Result<ThreadRow> {
    Ok(ThreadRow {
        id: row.get(0)?,
        rollout_path: PathBuf::from(row.get::<_, String>(1)?),
        cwd: row.get(2)?,
    })
}

fn read_rollout_identity(path: &Path) -> Result<(String, Option<String>)> {
    let file = File::open(path).with_context(|| format!("failed to open {}", path.display()))?;
    let reader = BufReader::new(file);
    for (offset, line) in reader.lines().enumerate() {
        let line_number = offset + 1;
        let line = line.with_context(|| format!("failed to read line {line_number}"))?;
        if line.trim().is_empty() {
            continue;
        }
        let value: Value = serde_json::from_str(&line)
            .with_context(|| format!("failed to parse JSON on line {line_number}"))?;
        if value.get("type").and_then(Value::as_str) == Some("session_meta") {
            let payload = value.get("payload").unwrap_or(&Value::Null);
            let id = payload
                .get("id")
                .and_then(Value::as_str)
                .ok_or_else(|| anyhow!("session_meta is missing payload.id"))?;
            let cwd = payload
                .get("cwd")
                .and_then(Value::as_str)
                .map(ToOwned::to_owned);
            return Ok((id.to_string(), cwd));
        }
    }
    bail!("{} does not contain a session_meta row", path.display())
}

fn find_rollout_by_prefix(sessions_dir: &Path, prefix: &str) -> Result<PathBuf> {
    let mut matches = Vec::new();
    collect_rollout_matches(sessions_dir, prefix, &mut matches)?;
    matches.sort();
    matches.dedup();

    if matches.is_empty() {
        bail!("no rollout JSONL found for session prefix {prefix}");
    }
    if matches.len() > 1 {
        let rendered = matches
            .iter()
            .take(10)
            .map(|path| path.display().to_string())
            .collect::<Vec<_>>()
            .join("\n");
        bail!("session prefix is ambiguous; rollout matches:\n{rendered}");
    }
    Ok(matches.remove(0))
}

fn collect_rollout_matches(dir: &Path, prefix: &str, matches: &mut Vec<PathBuf>) -> Result<()> {
    if !dir.exists() {
        return Ok(());
    }
    for entry in fs::read_dir(dir).with_context(|| format!("failed to read {}", dir.display()))? {
        let entry = entry?;
        let path = entry.path();
        if path.is_dir() {
            collect_rollout_matches(&path, prefix, matches)?;
        } else if path
            .file_name()
            .and_then(|name| name.to_str())
            .is_some_and(|name| {
                name.starts_with("rollout-") && name.contains(prefix) && name.ends_with(".jsonl")
            })
        {
            matches.push(path);
        }
    }
    Ok(())
}

fn update_state_db_cwd(state_db: &Path, session_id: &str, new_cwd: &Path) -> Result<()> {
    let mut conn = Connection::open(state_db)
        .with_context(|| format!("failed to open {}", state_db.display()))?;
    integrity_check(&conn, state_db)?;
    let backup_path = backup_path(state_db);
    vacuum_backup(&conn, &backup_path)?;

    let tx = conn.transaction()?;
    let changed = tx.execute(
        "UPDATE threads SET cwd = ?1 WHERE id = ?2",
        params![new_cwd.display().to_string(), session_id],
    )?;
    if changed != 1 {
        bail!("expected to update 1 thread row, updated {changed}");
    }
    tx.commit()?;
    integrity_check(&conn, state_db)?;
    println!("sqlite backup: {}", backup_path.display());
    Ok(())
}

fn integrity_check(conn: &Connection, db_path: &Path) -> Result<()> {
    let result: String = conn
        .query_row("PRAGMA integrity_check", [], |row| row.get(0))
        .with_context(|| format!("failed to integrity-check {}", db_path.display()))?;
    if result != "ok" {
        bail!("{} failed integrity_check: {result}", db_path.display());
    }
    Ok(())
}

fn vacuum_backup(conn: &Connection, backup_path: &Path) -> Result<()> {
    let sql = format!("VACUUM INTO '{}'", sql_string_literal(backup_path));
    conn.execute_batch(&sql)
        .with_context(|| format!("failed to create sqlite backup {}", backup_path.display()))
}

fn sql_string_literal(path: &Path) -> String {
    path.display().to_string().replace('\'', "''")
}

#[derive(Debug, Clone, Copy)]
struct RewriteResult {
    changed_rows: usize,
}

fn rewrite_rollout_cwd(path: &Path, new_cwd: &Path) -> Result<RewriteResult> {
    let backup = backup_path(path);
    fs::copy(path, &backup)
        .with_context(|| format!("failed to create rollout backup {}", backup.display()))?;

    let file = File::open(path).with_context(|| format!("failed to open {}", path.display()))?;
    let reader = BufReader::new(file);
    let temp = path.with_extension(format!("jsonl.tmp-{}", timestamp()));
    let mut writer = OpenOptions::new()
        .create_new(true)
        .write(true)
        .open(&temp)
        .with_context(|| format!("failed to create {}", temp.display()))?;

    let mut changed_rows = 0;
    for (offset, line) in reader.lines().enumerate() {
        let line_number = offset + 1;
        let line = line.with_context(|| format!("failed to read line {line_number}"))?;
        if line.trim().is_empty() {
            writeln!(writer)?;
            continue;
        }
        let mut value: Value = serde_json::from_str(&line)
            .with_context(|| format!("failed to parse JSON on line {line_number}"))?;
        if rewrite_rollout_row(&mut value, new_cwd) {
            changed_rows += 1;
        }
        writeln!(writer, "{}", serde_json::to_string(&value)?)?;
    }
    writer.flush()?;

    // Validate the replacement before it becomes authoritative.
    let _ = read_rollout_identity(&temp)?;
    fs::rename(&temp, path).with_context(|| format!("failed to replace {}", path.display()))?;
    println!("rollout backup: {}", backup.display());
    Ok(RewriteResult { changed_rows })
}

fn rewrite_rollout_row(row: &mut Value, new_cwd: &Path) -> bool {
    let Some(kind) = row
        .get("type")
        .and_then(Value::as_str)
        .map(ToOwned::to_owned)
    else {
        return false;
    };
    if kind != "session_meta" && kind != "turn_context" {
        return false;
    }
    let Some(payload) = row.get_mut("payload").and_then(Value::as_object_mut) else {
        return false;
    };

    let new_cwd = Value::String(new_cwd.display().to_string());
    let mut changed = payload.get("cwd") != Some(&new_cwd);
    payload.insert("cwd".to_string(), new_cwd.clone());

    if kind == "turn_context" {
        let roots = Value::Array(vec![new_cwd]);
        changed |= payload.get("workspace_roots") != Some(&roots);
        payload.insert("workspace_roots".to_string(), roots);
    }

    changed
}

fn ensure_trusted_project(config_path: &Path, cwd: &Path) -> Result<bool> {
    let header = format!("[projects.\"{}\"]", toml_basic_string(cwd));
    let existing = match fs::read_to_string(config_path) {
        Ok(content) => content,
        Err(error) if error.kind() == io::ErrorKind::NotFound => String::new(),
        Err(error) => {
            return Err(error).with_context(|| format!("failed to read {}", config_path.display()));
        }
    };

    if existing.lines().any(|line| line.trim() == header) {
        return Ok(false);
    }

    if let Some(parent) = config_path.parent() {
        fs::create_dir_all(parent)?;
    }
    let backup = if config_path.exists() {
        let backup = backup_path(config_path);
        fs::copy(config_path, &backup)
            .with_context(|| format!("failed to create config backup {}", backup.display()))?;
        Some(backup)
    } else {
        None
    };

    let mut file = OpenOptions::new()
        .create(true)
        .append(true)
        .open(config_path)
        .with_context(|| format!("failed to open {}", config_path.display()))?;
    if !existing.ends_with('\n') && !existing.is_empty() {
        writeln!(file)?;
    }
    writeln!(file)?;
    writeln!(file, "{header}")?;
    writeln!(file, "trust_level = \"trusted\"")?;
    if let Some(backup) = backup {
        println!("config backup: {}", backup.display());
    }
    Ok(true)
}

fn toml_basic_string(path: &Path) -> String {
    path.display()
        .to_string()
        .replace('\\', "\\\\")
        .replace('"', "\\\"")
}

fn backup_path(path: &Path) -> PathBuf {
    let file_name = path
        .file_name()
        .and_then(|name| name.to_str())
        .unwrap_or("backup");
    path.with_file_name(format!("{file_name}.backup-{}", timestamp()))
}

fn timestamp() -> u128 {
    SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_nanos()
}

fn is_broken_pipe(error: &anyhow::Error) -> bool {
    error
        .chain()
        .filter_map(|cause| cause.downcast_ref::<io::Error>())
        .any(|error| error.kind() == io::ErrorKind::BrokenPipe)
}

fn extract_file(path: &PathBuf) -> Result<Extraction> {
    let file = File::open(path).with_context(|| format!("failed to open {}", path.display()))?;
    let reader = BufReader::new(file);
    let mut extraction = Extraction::default();

    for (offset, line) in reader.lines().enumerate() {
        let line_number = offset + 1;
        let line = line.with_context(|| format!("failed to read line {line_number}"))?;
        if line.trim().is_empty() {
            continue;
        }
        let value: Value = serde_json::from_str(&line)
            .with_context(|| format!("failed to parse JSON on line {line_number}"))?;
        extract_rollout_line(line_number, &value, &mut extraction);
    }

    Ok(extraction)
}

fn extract_rollout_line(line: usize, row: &Value, extraction: &mut Extraction) {
    let timestamp = row
        .get("timestamp")
        .and_then(Value::as_str)
        .map(ToOwned::to_owned);
    let Some(kind) = row.get("type").and_then(Value::as_str) else {
        return;
    };
    let payload = row.get("payload").unwrap_or(&Value::Null);

    match kind {
        "event_msg" => {
            collect_encrypted(line, timestamp.as_deref(), kind, None, payload, extraction);
            extract_event_msg(line, timestamp, payload, extraction);
        }
        "response_item" => {
            collect_encrypted(line, timestamp.as_deref(), kind, None, payload, extraction);
            extract_response_item(line, timestamp, "response_item", None, payload, extraction)
        }
        "compacted" => extract_compacted(line, timestamp, payload, extraction),
        _ => collect_encrypted(line, timestamp.as_deref(), kind, None, payload, extraction),
    }
}

fn extract_event_msg(
    line: usize,
    timestamp: Option<String>,
    payload: &Value,
    extraction: &mut Extraction,
) {
    let Some(event_type) = payload.get("type").and_then(Value::as_str) else {
        return;
    };
    let role = match event_type {
        "user_message" => Some("user"),
        "agent_message" => Some("assistant"),
        _ => None,
    };
    let Some(role) = role else {
        return;
    };
    let Some(message) = payload.get("message").and_then(Value::as_str) else {
        return;
    };
    if message.is_empty() {
        return;
    }
    extraction.messages.push(ExtractedMessage {
        line,
        timestamp,
        source: format!("event_msg.{event_type}"),
        index: None,
        role: Some(role.to_string()),
        text: message.to_string(),
    });
}

fn extract_compacted(
    line: usize,
    timestamp: Option<String>,
    payload: &Value,
    extraction: &mut Extraction,
) {
    let Some(replacement_history) = payload.get("replacement_history").and_then(Value::as_array)
    else {
        return;
    };

    for (index, item) in replacement_history.iter().enumerate() {
        collect_encrypted(
            line,
            timestamp.as_deref(),
            "compacted.replacement_history",
            Some(index),
            item,
            extraction,
        );
        extract_response_item(
            line,
            timestamp.clone(),
            "compacted.replacement_history",
            Some(index),
            item,
            extraction,
        );
    }
}

fn extract_response_item(
    line: usize,
    timestamp: Option<String>,
    source: &str,
    index: Option<usize>,
    item: &Value,
    extraction: &mut Extraction,
) {
    if item.get("type").and_then(Value::as_str) != Some("message") {
        return;
    }
    let role = item
        .get("role")
        .and_then(Value::as_str)
        .map(ToOwned::to_owned);
    let text = collect_content_text(item.get("content").unwrap_or(&Value::Null));
    if text.is_empty() {
        return;
    }
    extraction.messages.push(ExtractedMessage {
        line,
        timestamp,
        source: source.to_string(),
        index,
        role,
        text,
    });
}

fn collect_content_text(content: &Value) -> String {
    match content {
        Value::String(text) => text.clone(),
        Value::Array(items) => items
            .iter()
            .filter_map(|item| match item {
                Value::String(text) => Some(text.as_str()),
                Value::Object(map) => map
                    .get("text")
                    .or_else(|| map.get("content"))
                    .and_then(Value::as_str),
                _ => None,
            })
            .collect::<Vec<_>>()
            .join("\n"),
        _ => String::new(),
    }
}

fn collect_encrypted(
    line: usize,
    timestamp: Option<&str>,
    source: &str,
    index: Option<usize>,
    value: &Value,
    extraction: &mut Extraction,
) {
    match value {
        Value::Object(map) => {
            if let Some(encrypted_content) = map.get("encrypted_content").and_then(Value::as_str) {
                extraction.encrypted.push(EncryptedBlob {
                    line,
                    timestamp: timestamp.map(ToOwned::to_owned),
                    source: source.to_string(),
                    index,
                    chars: encrypted_content.len(),
                });
            }
            for child in map.values() {
                collect_encrypted(line, timestamp, source, index, child, extraction);
            }
        }
        Value::Array(items) => {
            for child in items {
                collect_encrypted(line, timestamp, source, index, child, extraction);
            }
        }
        _ => {}
    }
}

fn filtered_messages(extraction: &Extraction, include_setup: bool) -> Vec<&ExtractedMessage> {
    extraction
        .messages
        .iter()
        .filter(|message| include_setup || !is_setup_message(message))
        .collect()
}

fn is_setup_message(message: &ExtractedMessage) -> bool {
    if message.role.as_deref() == Some("developer") {
        return true;
    }
    let text = message.text.trim_start();
    text.starts_with("<permissions instructions>")
        || text.starts_with("<environment_context>")
        || text.starts_with("# AGENTS.md instructions for ")
        || text.starts_with("# Collaboration Mode:")
}

fn write_jsonl(
    out: &mut impl Write,
    messages: &[&ExtractedMessage],
    extraction: &Extraction,
    include_encrypted: bool,
) -> Result<()> {
    for message in messages {
        writeln!(out, "{}", serde_json::to_string(message)?)?;
    }
    if include_encrypted {
        for encrypted in &extraction.encrypted {
            writeln!(out, "{}", serde_json::to_string(encrypted)?)?;
        }
    }
    Ok(())
}

fn write_markdown(
    out: &mut impl Write,
    path: &Path,
    messages: &[&ExtractedMessage],
    extraction: &Extraction,
    include_encrypted: bool,
) -> Result<()> {
    let rendered = deduped_messages(messages);
    let user_count = rendered
        .iter()
        .filter(|message| message.role.as_deref() == Some("user"))
        .count();
    let assistant_count = rendered
        .iter()
        .filter(|message| message.role.as_deref() == Some("assistant"))
        .count();

    writeln!(out, "<!-- codex-tools extract:start -->")?;
    writeln!(out, "## Codex Session Extract")?;
    writeln!(out)?;
    writeln!(out, "<details>")?;
    writeln!(out, "<summary>Recoverable plaintext transcript</summary>")?;
    writeln!(out)?;
    writeln!(out, "````text")?;
    writeln!(out, "source: {}", path.display())?;
    writeln!(
        out,
        "view: raw recoverable plaintext rows, deduped for reading"
    )?;
    writeln!(
        out,
        "omitted: setup messages unless --include-setup, raw tool outputs, opaque encrypted_content"
    )?;
    writeln!(
        out,
        "stats: messages={} deduped={} user={} assistant={} encrypted_blobs={}",
        messages.len(),
        rendered.len(),
        user_count,
        assistant_count,
        extraction.encrypted.len()
    )?;
    writeln!(out)?;

    for message in rendered {
        let role = message.role.as_deref().unwrap_or("unknown role");
        writeln!(out, "[{role}]")?;
        writeln!(out, "{}", message.text)?;
        writeln!(out)?;
    }
    writeln!(out, "````")?;
    writeln!(out)?;
    writeln!(out, "</details>")?;

    if include_encrypted {
        writeln!(out)?;
        writeln!(out, "<details>")?;
        writeln!(out, "<summary>Encrypted content locations</summary>")?;
        writeln!(out)?;
        writeln!(out, "````text")?;
        for encrypted in &extraction.encrypted {
            let timestamp = encrypted
                .timestamp
                .as_deref()
                .unwrap_or("unknown timestamp");
            let index = encrypted
                .index
                .map(|index| format!("[{index}]"))
                .unwrap_or_default();
            writeln!(
                out,
                "- line {} {}{} encrypted_content chars={} timestamp={}",
                encrypted.line, encrypted.source, index, encrypted.chars, timestamp
            )?;
        }
        writeln!(out, "````")?;
        writeln!(out)?;
        writeln!(out, "</details>")?;
    }
    writeln!(out, "<!-- codex-tools extract:end -->")?;
    Ok(())
}

fn deduped_messages<'a>(messages: &[&'a ExtractedMessage]) -> Vec<&'a ExtractedMessage> {
    let mut seen = HashSet::new();
    let mut rendered = Vec::new();
    for message in messages {
        let key = dedupe_key(message);
        if seen.insert(key) {
            rendered.push(*message);
        }
    }
    rendered
}

fn dedupe_key(message: &ExtractedMessage) -> String {
    let role = message.role.as_deref().unwrap_or("");
    let text = message
        .text
        .split_whitespace()
        .collect::<Vec<_>>()
        .join(" ");
    format!("{role}\n{text}")
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn extracts_top_level_and_compacted_messages() {
        let mut extraction = Extraction::default();
        let row = serde_json::json!({
            "timestamp": "2026-05-26T13:12:12.371Z",
            "type": "response_item",
            "payload": {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "hello"}]
            }
        });
        extract_rollout_line(6, &row, &mut extraction);

        let compacted = serde_json::json!({
            "timestamp": "2026-05-27T06:39:53.184Z",
            "type": "compacted",
            "payload": {
                "replacement_history": [
                    {"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": "hi"}]},
                    {"type": "reasoning", "encrypted_content": "opaque"}
                ]
            }
        });
        extract_rollout_line(1850, &compacted, &mut extraction);

        assert_eq!(extraction.messages.len(), 2);
        assert_eq!(extraction.messages[0].text, "hello");
        assert_eq!(extraction.messages[1].text, "hi");
        assert_eq!(extraction.encrypted.len(), 1);
        assert_eq!(
            extraction.encrypted[0].source,
            "compacted.replacement_history"
        );
        assert_eq!(extraction.encrypted[0].index, Some(1));
    }

    #[test]
    fn filters_setup_messages_by_default() {
        let extraction = Extraction {
            messages: vec![
                ExtractedMessage {
                    line: 1,
                    timestamp: None,
                    source: "response_item".to_string(),
                    index: None,
                    role: Some("user".to_string()),
                    text: "<environment_context>\nsecret".to_string(),
                },
                ExtractedMessage {
                    line: 2,
                    timestamp: None,
                    source: "response_item".to_string(),
                    index: None,
                    role: Some("user".to_string()),
                    text: "actual request".to_string(),
                },
            ],
            encrypted: Vec::new(),
        };

        let filtered = filtered_messages(&extraction, false);
        assert_eq!(filtered.len(), 1);
        assert_eq!(filtered[0].text, "actual request");
        assert_eq!(filtered_messages(&extraction, true).len(), 2);
    }

    #[test]
    fn rewrites_rollout_metadata_cwd() {
        let new_cwd = PathBuf::from("/tmp/new-cwd");
        let mut session_meta = serde_json::json!({
            "type": "session_meta",
            "payload": {"id": "abc", "cwd": "/tmp/old"}
        });
        let mut turn_context = serde_json::json!({
            "type": "turn_context",
            "payload": {"cwd": "/tmp/old", "workspace_roots": ["/tmp/old", "/tmp/other"]}
        });
        let mut message = serde_json::json!({
            "type": "response_item",
            "payload": {"type": "message", "role": "user", "content": "hello"}
        });

        assert!(rewrite_rollout_row(&mut session_meta, &new_cwd));
        assert!(rewrite_rollout_row(&mut turn_context, &new_cwd));
        assert!(!rewrite_rollout_row(&mut message, &new_cwd));

        assert_eq!(
            session_meta["payload"]["cwd"],
            Value::String("/tmp/new-cwd".to_string())
        );
        assert_eq!(
            turn_context["payload"]["workspace_roots"],
            Value::Array(vec![Value::String("/tmp/new-cwd".to_string())])
        );
    }

    #[test]
    fn detects_broken_pipe_in_error_chain() {
        let error: anyhow::Error = io::Error::new(io::ErrorKind::BrokenPipe, "pipe").into();
        assert!(is_broken_pipe(&error));
    }

    #[test]
    fn updates_sqlite_cwd_with_integrity_checked_backup() {
        let root = test_temp_dir("sqlite-cwd");
        let db = root.join("state_5.sqlite");
        let conn = Connection::open(&db).unwrap();
        conn.execute_batch(
            "CREATE TABLE threads (
                id TEXT PRIMARY KEY,
                rollout_path TEXT NOT NULL,
                cwd TEXT NOT NULL,
                updated_at_ms INTEGER
            );
            INSERT INTO threads VALUES ('abc123', '/tmp/rollout.jsonl', '/old/cwd', 1);",
        )
        .unwrap();
        drop(conn);

        update_state_db_cwd(&db, "abc123", Path::new("/new/cwd")).unwrap();

        let conn = Connection::open(&db).unwrap();
        let integrity: String = conn
            .query_row("PRAGMA integrity_check", [], |row| row.get(0))
            .unwrap();
        let cwd: String = conn
            .query_row("SELECT cwd FROM threads WHERE id = 'abc123'", [], |row| {
                row.get(0)
            })
            .unwrap();
        assert_eq!(integrity, "ok");
        assert_eq!(cwd, "/new/cwd");
        assert!(backup_count(&root, "state_5.sqlite.backup-") >= 1);
    }

    #[test]
    fn rewrites_rollout_file_metadata_with_backup() {
        let root = test_temp_dir("rollout-cwd");
        let rollout = root.join("rollout-abc123.jsonl");
        fs::write(
            &rollout,
            [
                r#"{"type":"session_meta","payload":{"id":"abc123","cwd":"/old/cwd"}}"#,
                r#"{"type":"turn_context","payload":{"cwd":"/old/cwd","workspace_roots":["/old/cwd"]}}"#,
                r#"{"type":"response_item","payload":{"type":"message","role":"user","content":"hello"}}"#,
            ]
            .join("\n"),
        )
        .unwrap();

        let result = rewrite_rollout_cwd(&rollout, Path::new("/new/cwd")).unwrap();

        assert_eq!(result.changed_rows, 2);
        let content = fs::read_to_string(&rollout).unwrap();
        assert!(content.contains(r#""cwd":"/new/cwd""#));
        assert!(content.contains(r#""workspace_roots":["/new/cwd"]"#));
        assert!(content.contains(r#""content":"hello""#));
        assert!(backup_count(&root, "rollout-abc123.jsonl.backup-") >= 1);
    }

    #[test]
    fn appends_trusted_project_once() {
        let root = test_temp_dir("trust-config");
        let config = root.join("config.toml");

        assert!(ensure_trusted_project(&config, Path::new("/new/cwd")).unwrap());
        assert!(!ensure_trusted_project(&config, Path::new("/new/cwd")).unwrap());

        let content = fs::read_to_string(&config).unwrap();
        assert_eq!(content.matches("[projects.\"/new/cwd\"]").count(), 1);
        assert!(content.contains("trust_level = \"trusted\""));
    }

    fn test_temp_dir(name: &str) -> PathBuf {
        let path = env::temp_dir().join(format!(
            "codex-tools-test-{name}-{}-{}",
            std::process::id(),
            timestamp()
        ));
        fs::create_dir_all(&path).unwrap();
        path
    }

    fn backup_count(dir: &Path, prefix: &str) -> usize {
        fs::read_dir(dir)
            .unwrap()
            .filter_map(Result::ok)
            .filter(|entry| {
                entry
                    .file_name()
                    .to_str()
                    .is_some_and(|name| name.starts_with(prefix))
            })
            .count()
    }
}
