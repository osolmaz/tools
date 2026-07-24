use pngscrub::{Inspection, PngError, SanitizeResult, inspect_file, sanitize_file};
use std::env;
use std::fs::{self, OpenOptions};
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::ExitCode;
use std::time::{SystemTime, UNIX_EPOCH};

#[derive(Debug)]
enum Command {
    Inspect {
        input: PathBuf,
        json: bool,
    },
    Clean {
        input: PathBuf,
        output: Option<PathBuf>,
        aggressive: bool,
        force: bool,
        json: bool,
    },
}

fn usage() -> &'static str {
    "Usage:\n  pngscrub inspect <input.png> [--json]\n  pngscrub clean <input.png> [-o <output.png>] [--aggressive] [--force] [--json]"
}

fn parse_inspect(args: &[String]) -> Result<Command, String> {
    let mut input = None;
    let mut json = false;
    for argument in args {
        if argument == "--json" {
            json = true;
        } else if argument.starts_with('-') {
            return Err(format!("unknown option: {argument}"));
        } else if input.replace(PathBuf::from(argument)).is_some() {
            return Err("inspect accepts one input file".to_owned());
        }
    }
    Ok(Command::Inspect {
        input: input.ok_or_else(|| "inspect requires an input file".to_owned())?,
        json,
    })
}

fn take_output(args: &[String], index: &mut usize) -> Result<PathBuf, String> {
    *index += 1;
    args.get(*index)
        .map(PathBuf::from)
        .ok_or_else(|| "-o/--output requires a path".to_owned())
}

fn parse_clean(args: &[String]) -> Result<Command, String> {
    let mut input = None;
    let mut output = None;
    let mut aggressive = false;
    let mut force = false;
    let mut json = false;
    let mut index = 0;
    while index < args.len() {
        match args[index].as_str() {
            "-o" | "--output" => output = Some(take_output(args, &mut index)?),
            "--aggressive" => aggressive = true,
            "--force" => force = true,
            "--json" => json = true,
            option if option.starts_with('-') => return Err(format!("unknown option: {option}")),
            value if input.is_none() => input = Some(PathBuf::from(value)),
            _ => return Err("clean accepts one input file".to_owned()),
        }
        index += 1;
    }
    Ok(Command::Clean {
        input: input.ok_or_else(|| "clean requires an input file".to_owned())?,
        output,
        aggressive,
        force,
        json,
    })
}

fn parse_args(args: &[String]) -> Result<Command, String> {
    match args.split_first() {
        Some((command, rest)) if command == "inspect" => parse_inspect(rest),
        Some((command, rest)) if command == "clean" => parse_clean(rest),
        Some((command, _)) => Err(format!("unknown command: {command}")),
        None => Err("missing command".to_owned()),
    }
}

fn default_output(input: &Path) -> Result<PathBuf, String> {
    let stem = input
        .file_stem()
        .and_then(|value| value.to_str())
        .ok_or_else(|| "input has no usable file name".to_owned())?;
    Ok(input.with_file_name(format!("{stem}.sanitized.png")))
}

fn json_string(value: &str) -> String {
    let mut output = String::from("\"");
    for character in value.chars() {
        match character {
            '"' => output.push_str("\\\""),
            '\\' => output.push_str("\\\\"),
            '\n' => output.push_str("\\n"),
            '\r' => output.push_str("\\r"),
            '\t' => output.push_str("\\t"),
            value if value.is_control() => {
                output.push_str(&format!("\\u{:04x}", u32::from(value)));
            }
            value => output.push(value),
        }
    }
    output.push('"');
    output
}

fn json_array(values: &[String]) -> String {
    let items = values
        .iter()
        .map(|value| json_string(value))
        .collect::<Vec<_>>()
        .join(",");
    format!("[{items}]")
}

fn print_inspection(path: &Path, inspection: &Inspection, json: bool) {
    if json {
        println!(
            concat!(
                "{{",
                "\"path\":{},\"size\":{},\"chunks\":{},\"metadata_chunks\":{},",
                "\"c2pa_detected\":{},\"openai_detected\":{},\"trailing_bytes\":{},",
                "\"idat_sha256\":{}",
                "}}"
            ),
            json_string(&path.display().to_string()),
            inspection.size,
            json_array(&inspection.chunks),
            json_array(&inspection.metadata_chunks),
            inspection.c2pa_detected,
            inspection.openai_detected,
            inspection.trailing_bytes,
            json_string(&inspection.idat_sha256),
        );
        return;
    }

    let signer = if inspection.openai_detected {
        " (OpenAI signer found)"
    } else {
        ""
    };
    let metadata = if inspection.metadata_chunks.is_empty() {
        "none".to_owned()
    } else {
        inspection.metadata_chunks.join(", ")
    };
    println!("file: {}", path.display());
    println!(
        "C2PA: {}{signer}",
        if inspection.c2pa_detected {
            "yes"
        } else {
            "no"
        }
    );
    println!("metadata chunks: {metadata}");
    println!("trailing bytes: {}", inspection.trailing_bytes);
    println!("IDAT sha256: {}", inspection.idat_sha256);
}

fn print_result(path: &Path, result: &SanitizeResult, json: bool) {
    if json {
        println!(
            concat!(
                "{{",
                "\"output_path\":{},\"input_size\":{},\"output_size\":{},",
                "\"removed_chunks\":{},\"removed_bytes\":{},",
                "\"trailing_bytes_removed\":{},\"idat_sha256\":{},",
                "\"image_data_unchanged\":{}",
                "}}"
            ),
            json_string(&path.display().to_string()),
            result.input_size,
            result.output_size,
            json_array(&result.removed_chunks),
            result.removed_bytes,
            result.trailing_bytes_removed,
            json_string(&result.idat_sha256),
            result.image_data_unchanged,
        );
        return;
    }

    let removed = if result.removed_chunks.is_empty() {
        "none".to_owned()
    } else {
        result.removed_chunks.join(", ")
    };
    println!("wrote: {}", path.display());
    println!("removed chunks: {removed}");
    println!("removed bytes: {}", result.removed_bytes);
    println!(
        "image data unchanged: {}",
        if result.image_data_unchanged {
            "yes"
        } else {
            "no"
        }
    );
    println!("pixel-level watermarks: not inspected or removed");
}

fn temporary_path(destination: &Path) -> Result<PathBuf, String> {
    let parent = destination.parent().unwrap_or_else(|| Path::new("."));
    let name = destination
        .file_name()
        .and_then(|value| value.to_str())
        .ok_or_else(|| "output has no usable file name".to_owned())?;
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| format!("system clock error: {error}"))?
        .as_nanos();
    Ok(parent.join(format!(".{name}.{}.{}", std::process::id(), nonce)))
}

fn write_output(destination: &Path, content: &[u8], force: bool) -> Result<(), String> {
    let parent = destination.parent().unwrap_or_else(|| Path::new("."));
    fs::create_dir_all(parent)
        .map_err(|error| format!("cannot create {}: {error}", parent.display()))?;
    if !force {
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(destination)
            .map_err(|error| format!("cannot create {}: {error}", destination.display()))?;
        file.write_all(content)
            .map_err(|error| format!("cannot write {}: {error}", destination.display()))?;
        return Ok(());
    }

    let temporary = temporary_path(destination)?;
    let result = (|| {
        let mut file = OpenOptions::new()
            .write(true)
            .create_new(true)
            .open(&temporary)
            .map_err(|error| format!("cannot create {}: {error}", temporary.display()))?;
        file.write_all(content)
            .map_err(|error| format!("cannot write {}: {error}", temporary.display()))?;
        fs::rename(&temporary, destination).map_err(|error| {
            format!(
                "cannot replace {} with {}: {error}",
                destination.display(),
                temporary.display()
            )
        })
    })();
    if result.is_err() {
        let _ = fs::remove_file(&temporary);
    }
    result
}

fn run(command: Command) -> Result<(), String> {
    match command {
        Command::Inspect { input, json } => {
            let inspection = inspect_file(&input).map_err(|error| error.to_string())?;
            print_inspection(&input, &inspection, json);
        }
        Command::Clean {
            input,
            output,
            aggressive,
            force,
            json,
        } => {
            let output = output.map_or_else(|| default_output(&input), Ok)?;
            let input_resolved = fs::canonicalize(&input)
                .map_err(|error| format!("cannot resolve {}: {error}", input.display()))?;
            let output_resolved = if output.exists() {
                fs::canonicalize(&output)
                    .map_err(|error| format!("cannot resolve {}: {error}", output.display()))?
            } else {
                output.clone()
            };
            if input_resolved == output_resolved {
                return Err(
                    "refusing to overwrite the source; choose a separate output path".into(),
                );
            }
            let (content, result) =
                sanitize_file(&input, aggressive).map_err(|error: PngError| error.to_string())?;
            write_output(&output, &content, force)?;
            print_result(&output, &result, json);
        }
    }
    Ok(())
}

fn main() -> ExitCode {
    let args = env::args().skip(1).collect::<Vec<_>>();
    match parse_args(&args).and_then(run) {
        Ok(()) => ExitCode::SUCCESS,
        Err(error) => {
            eprintln!("pngscrub: {error}");
            eprintln!("{}", usage());
            ExitCode::FAILURE
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn parses_inspect_command() {
        assert!(matches!(
            parse_args(&["inspect".into(), "image.png".into(), "--json".into()]),
            Ok(Command::Inspect { json: true, .. })
        ));
    }

    #[test]
    fn parses_clean_command() {
        assert!(matches!(
            parse_args(&[
                "clean".into(),
                "image.png".into(),
                "-o".into(),
                "clean.png".into(),
                "--force".into(),
            ]),
            Ok(Command::Clean {
                force: true,
                output: Some(_),
                ..
            })
        ));
    }

    #[test]
    fn rejects_unknown_command() {
        assert_eq!(
            parse_args(&["wat".into()]).expect_err("must reject"),
            "unknown command: wat"
        );
    }

    #[test]
    fn escapes_json_strings() {
        assert_eq!(json_string("a\"b\n"), "\"a\\\"b\\n\"");
    }
}
