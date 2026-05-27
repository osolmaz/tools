use std::collections::HashSet;
use std::fs::File;
use std::io::{self, BufRead, BufReader, Write};
use std::path::PathBuf;

use anyhow::Context;
use anyhow::Result;
use clap::Parser;
use serde::Serialize;
use serde_json::Value;

#[derive(Debug, Parser)]
#[command(about = "Extract recoverable plaintext messages from a Codex rollout JSONL file")]
struct Cli {
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
    let cli = Cli::parse();
    let extraction = extract_file(&cli.input)?;
    let messages = filtered_messages(&extraction, cli.include_setup);
    let stdout = io::stdout();
    let mut out = stdout.lock();

    if cli.jsonl {
        write_jsonl(&mut out, &messages, &extraction, cli.include_encrypted)?;
    } else {
        write_markdown(
            &mut out,
            &cli.input,
            &messages,
            &extraction,
            cli.include_encrypted,
        )?;
    }

    Ok(())
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
    path: &PathBuf,
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

    writeln!(out, "<!-- codex-session-extract:start -->")?;
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
                "- line {} {}{} {} chars={} timestamp={}",
                encrypted.line,
                encrypted.source,
                index,
                "encrypted_content",
                encrypted.chars,
                timestamp
            )?;
        }
        writeln!(out, "````")?;
        writeln!(out)?;
        writeln!(out, "</details>")?;
    }
    writeln!(out, "<!-- codex-session-extract:end -->")?;
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
        assert_eq!(
            extraction.messages[1].source,
            "compacted.replacement_history"
        );
        assert_eq!(extraction.messages[1].index, Some(0));
        assert_eq!(extraction.messages[1].text, "hi");
        assert_eq!(extraction.encrypted.len(), 1);
    }

    #[test]
    fn setup_filter_keeps_human_dialogue() {
        let extraction = Extraction {
            messages: vec![
                ExtractedMessage {
                    line: 1,
                    timestamp: None,
                    source: "response_item".to_string(),
                    index: None,
                    role: Some("developer".to_string()),
                    text: "<permissions instructions>\nsecret rules".to_string(),
                },
                ExtractedMessage {
                    line: 2,
                    timestamp: None,
                    source: "response_item".to_string(),
                    index: None,
                    role: Some("user".to_string()),
                    text: "# AGENTS.md instructions for /tmp\n<INSTRUCTIONS>".to_string(),
                },
                ExtractedMessage {
                    line: 3,
                    timestamp: None,
                    source: "response_item".to_string(),
                    index: None,
                    role: Some("user".to_string()),
                    text: "pull latest main and tell me what the issues assigned to me are\n"
                        .to_string(),
                },
            ],
            encrypted: Vec::new(),
        };

        let filtered = filtered_messages(&extraction, false);
        assert_eq!(filtered.len(), 1);
        assert!(filtered[0].text.starts_with("pull latest main"));
        assert_eq!(filtered_messages(&extraction, true).len(), 3);
    }

    #[test]
    fn markdown_dedupes_storage_duplicates() {
        let first = ExtractedMessage {
            line: 1,
            timestamp: None,
            source: "response_item".to_string(),
            index: None,
            role: Some("user".to_string()),
            text: "hello\n".to_string(),
        };
        let duplicate = ExtractedMessage {
            line: 2,
            timestamp: None,
            source: "event_msg.user_message".to_string(),
            index: None,
            role: Some("user".to_string()),
            text: "hello".to_string(),
        };
        let messages = vec![&first, &duplicate];

        let deduped = deduped_messages(&messages);

        assert_eq!(deduped.len(), 1);
        assert_eq!(deduped[0].line, 1);
    }
}
