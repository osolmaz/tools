use std::fs::{self, File};
use std::io::{BufRead, BufReader, BufWriter, Write};
use std::path::Path;

use clap::{App, Arg};
use regex::Regex;
use walkdir::WalkDir;

fn process_file(path: &Path) -> std::io::Result<()> {
    // Retrieve the original file's metadata and permissions
    let metadata = fs::metadata(&path)?;
    let permissions = metadata.permissions();

    let file = File::open(&path)?;
    let reader = BufReader::new(file);

    let temp_path = path.with_extension("tmp");
    let temp_file = File::create(&temp_path)?;
    let mut writer = BufWriter::new(temp_file);

    // Set the permissions of the temp file to match the original
    fs::set_permissions(&temp_path, permissions.clone())?;

    // Regular expressions for pattern matching
    // Matches 'import pdb' or 'import ipdb' with optional whitespace and captures indentation and module name
    let re_import = Regex::new(r"^(\s*)import\s+(pdb|ipdb)\s*$").unwrap();

    // Matches lines containing 'pdb.set_trace()' or 'ipdb.set_trace()' with optional whitespace
    let re_set_trace = Regex::new(r"^\s*(pdb|ipdb)\.set_trace\(\)\s*$").unwrap();

    // Matches single-line 'import pdb; pdb.set_trace()' or 'import ipdb; ipdb.set_trace()'
    let re_single_line =
        Regex::new(r"^\s*import\s+(pdb|ipdb);\s*(pdb|ipdb)\.set_trace\(\)\s*$").unwrap();

    let mut buffer = Vec::new();

    let lines: Vec<String> = reader.lines().collect::<Result<_, _>>()?;
    let mut i = 0;

    while i < lines.len() {
        let line = &lines[i];

        // Check for the single-line pattern
        if re_single_line.is_match(line) {
            i += 1;
            continue;
        }

        // Check for standalone 'pdb.set_trace()' or 'ipdb.set_trace()' line
        if re_set_trace.is_match(line) {
            i += 1;
            continue;
        }

        // Check for the multiline pattern start
        if let Some(caps) = re_import.captures(line) {
            buffer.push(line.clone());
            let indent = caps.get(1).unwrap().as_str().to_string();
            let module_name = caps.get(2).unwrap().as_str().to_string();
            i += 1;

            // Buffer any whitespace-only lines
            while i < lines.len() && lines[i].trim().is_empty() {
                buffer.push(lines[i].clone());
                i += 1;
            }

            // Check for '<module_name>.set_trace()' with the same indentation
            if i < lines.len() {
                let next_line = &lines[i];
                let expected_set_trace = format!("{}{}.set_trace()", indent, module_name);

                if next_line.trim() == expected_set_trace.trim() {
                    // Skip the buffered lines and the current line
                    buffer.clear();
                    i += 1;
                    continue;
                }
            }

            // Pattern did not match; write buffered lines
            for buf_line in &buffer {
                writer.write_all(buf_line.as_bytes())?;
                writer.write_all(b"\n")?;
            }
            buffer.clear();
        } else {
            // Write the line as it doesn't match any patterns
            writer.write_all(line.as_bytes())?;
            writer.write_all(b"\n")?;
            i += 1;
        }
    }

    // Replace the original file with the temp file
    fs::rename(&temp_path, &path)?;

    Ok(())
}

fn main() {
    let matches = App::new("Remove Debug Lines")
        .version("1.0")
        .author("Assistant")
        .about("Removes lines containing pdb or ipdb debugging statements from Python files.")
        .arg(
            Arg::with_name("TARGETS")
                .help("Target files or directories")
                .required(true)
                .multiple(true)
                .index(1),
        )
        .arg(
            Arg::with_name("extension")
                .short("e")
                .long("extension")
                .value_name("EXT")
                .help("File extension to filter (default: py)")
                .takes_value(true),
        )
        .get_matches();

    let targets: Vec<_> = matches.values_of("TARGETS").unwrap().collect();
    let extension = matches.value_of("extension").unwrap_or("py");

    for target in targets {
        let target_path = Path::new(target);

        if target_path.is_file() {
            if target_path
                .extension()
                .and_then(|ext| ext.to_str())
                .map_or(false, |ext| ext == extension)
            {
                if let Err(e) = process_file(target_path) {
                    eprintln!("Error processing file {}: {}", target, e);
                }
            }
        } else if target_path.is_dir() {
            for entry in WalkDir::new(target_path)
                .into_iter()
                .filter_map(Result::ok)
                .filter(|e| {
                    e.path().is_file()
                        && e.path()
                            .extension()
                            .and_then(|ext| ext.to_str())
                            .map_or(false, |ext| ext == extension)
                })
            {
                if let Err(e) = process_file(entry.path()) {
                    eprintln!("Error processing file {}: {}", entry.path().display(), e);
                }
            }
        } else {
            eprintln!(
                "The target path '{}' is neither a file nor a directory.",
                target
            );
        }
    }
}
