"""prooompter CLI command derived from files-to-prompt v0.6.

Original source: https://github.com/simonw/files-to-prompt (Apache-2.0 licensed).
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from collections import OrderedDict
from contextlib import contextmanager, nullcontext
from fnmatch import fnmatch
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple

import click

try:  # Python 3.11+
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - fallback for older interpreters
    import tomli as tomllib  # type: ignore

global_index = 1
DEFAULT_MAX_CHARS = 400_000
CONFIG_FILENAME = "prooompter.toml"


class OutputLimitReached(RuntimeError):
    """Raised when the output character limit is exceeded."""

    def __init__(
        self,
        *,
        limit: int,
        total_before: int,
        attempted_add: int,
        current_file: Optional[str],
        file_totals: dict[str, int],
    ):
        super().__init__("Output limit reached")
        self.limit = limit
        self.total_before = total_before
        self.attempted_add = attempted_add
        self.current_file = current_file
        self.file_totals = file_totals


class LimitedWriter:
    """Wrapper that enforces a character limit and tracks per-file contributions."""

    def __init__(self, writer, max_chars: Optional[int]):
        self.writer = writer
        self.limit = None if max_chars in (None, 0) else max_chars
        self.total = 0
        self.current_file: Optional[str] = None
        self.file_totals: OrderedDict[str, int] = OrderedDict()

    def set_current_file(self, path: Optional[str]) -> None:
        self.current_file = path
        if path is not None and path not in self.file_totals:
            self.file_totals[path] = 0

    def clear_current_file(self) -> None:
        self.current_file = None

    def __call__(self, message):
        text = "" if message is None else str(message)
        additional = len(text) + 1
        if self.limit is not None and self.total + additional > self.limit:
            raise OutputLimitReached(
                limit=self.limit,
                total_before=self.total,
                attempted_add=additional,
                current_file=self.current_file,
                file_totals=dict(self.file_totals),
            )
        self.writer(text)
        self.total += additional
        if self.current_file is not None:
            self.file_totals[self.current_file] = (
                self.file_totals.get(self.current_file, 0) + additional
            )


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/")


def _match_glob(path: str, pattern: str) -> bool:
    return fnmatch(_normalize_path(path), _normalize_path(pattern))


def _load_cli_config(repo_root: Path) -> dict[str, Any]:
    config_path = repo_root / CONFIG_FILENAME
    if not config_path.is_file():
        return {}
    try:
        with config_path.open("rb") as fp:
            data = tomllib.load(fp)
    except (OSError, tomllib.TOMLDecodeError) as exc:
        click.echo(
            click.style(
                f"Warning: Failed to load {CONFIG_FILENAME}: {exc}", fg="yellow"
            ),
            err=True,
        )
        return {}
    if not isinstance(data, dict):
        click.echo(
            click.style(
                f"Warning: {CONFIG_FILENAME} must contain a TOML table at the root.",
                fg="yellow",
            ),
            err=True,
        )
        return {}
    return data


def _coerce_string_list(value: Any, *, context: str) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        strings: List[str] = []
        for idx, item in enumerate(value):
            if isinstance(item, str):
                strings.append(item)
            else:
                click.echo(
                    click.style(
                        f"Warning: {context}[{idx}] must be a string in {CONFIG_FILENAME}.",
                        fg="yellow",
                    ),
                    err=True,
                )
        return strings
    click.echo(
        click.style(
            f"Warning: {context} must be a string or list of strings in {CONFIG_FILENAME}.",
            fg="yellow",
        ),
        err=True,
    )
    return []


def _emit_summary(destination: str, writer: LimitedWriter) -> None:
    files = writer.file_totals.items()
    total_chars = writer.total
    click.echo(
        click.style(
            f"Included {len(writer.file_totals)} files ({total_chars:,} chars) into {destination}:",
            fg="cyan",
        ),
        err=True,
    )
    for path, chars in files:
        label = path or "(no file context)"
        click.echo(f"  - {label}: {chars:,} chars", err=True)


def _run_git(
    args: Iterable[str], cwd: Path, check: bool = True
) -> subprocess.CompletedProcess[str]:
    """Run a git command and optionally raise if it fails."""
    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    if check and result.returncode != 0:
        stderr = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {stderr or 'unknown error'}")
    return result


def _detect_repo_root() -> Path:
    """Return the repository root directory."""
    result = _run_git(["rev-parse", "--show-toplevel"], Path.cwd())
    return Path(result.stdout.strip())


def _ref_exists(ref: str, cwd: Path) -> bool:
    """Return True if the ref exists."""
    result = _run_git(
        ["rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        cwd,
        check=False,
    )
    return result.returncode == 0


def _default_remote_head(remote: str, cwd: Path) -> str:
    """Determine the default branch for the remote."""
    # Fast path using origin/HEAD
    result = _run_git(
        ["symbolic-ref", "--quiet", "--short", f"refs/remotes/{remote}/HEAD"],
        cwd,
        check=False,
    )
    if result.returncode == 0:
        value = result.stdout.strip()
        if value:
            return value

    # Fallback to parsing `git remote show`
    remote_info = _run_git(["remote", "show", remote], cwd)
    for line in remote_info.stdout.splitlines():
        line = line.strip()
        if line.startswith("HEAD branch:"):
            branch = line.split(":", 1)[1].strip()
            if branch:
                return f"{remote}/{branch}"
    raise RuntimeError(
        f"Unable to determine default branch for remote '{remote}'. "
        "Provide --base explicitly."
    )


def _resolve_base_ref(base: str | None, remote: str, cwd: Path) -> str:
    """Resolve the base reference, preferring the user-provided value."""
    if base:
        if _ref_exists(base, cwd):
            return base
        candidate = f"{remote}/{base}"
        if _ref_exists(candidate, cwd):
            return candidate
        raise RuntimeError(
            f"Unable to locate base reference '{base}'. "
            f"Tried '{base}' and '{candidate}'."
        )

    return _default_remote_head(remote, cwd)


def _collect_changed_files(
    base_ref: str,
    cwd: Path,
    include_untracked: bool,
) -> Tuple[List[str], List[str]]:
    """Return (paths, missing_paths) relative to cwd."""
    files: List[str] = []
    missing: List[str] = []

    seen: set[str] = set()

    def add_path(path: str) -> None:
        norm = path.strip()
        if not norm or norm in seen:
            return
        seen.add(norm)
        files.append(norm)

    diff_result = _run_git(
        ["diff", "--name-only", "--no-ext-diff", f"{base_ref}...HEAD"],
        cwd,
    )
    for line in diff_result.stdout.splitlines():
        add_path(line)

    status_result = _run_git(["status", "--porcelain"], cwd)
    for line in status_result.stdout.splitlines():
        if not line or len(line) < 4:
            continue
        status_code = line[:2]
        payload = line[3:]

        if " -> " in payload:
            candidates = payload.split(" -> ", 1)
        else:
            candidates = [payload]

        for candidate in candidates:
            if status_code == "??":
                if include_untracked:
                    add_path(candidate)
            else:
                add_path(candidate)

    repo_root = cwd
    existing: List[str] = []
    for path in files:
        file_path = repo_root / path
        if file_path.is_file():
            existing.append(path)
        else:
            missing.append(path)

    return existing, missing


@contextmanager
def _temporary_cwd(path: Path) -> Iterable[None]:
    """Temporarily switch working directory."""
    previous = Path.cwd()
    try:
        os.chdir(path)
        yield
    finally:
        os.chdir(previous)


EXT_TO_LANG = {
    "py": "python",
    "c": "c",
    "cpp": "cpp",
    "java": "java",
    "js": "javascript",
    "ts": "typescript",
    "html": "html",
    "css": "css",
    "xml": "xml",
    "json": "json",
    "yaml": "yaml",
    "yml": "yaml",
    "sh": "bash",
    "rb": "ruby",
}


def should_ignore(path, gitignore_rules):
    for rule in gitignore_rules:
        if fnmatch(os.path.basename(path), rule):
            return True
        if os.path.isdir(path) and fnmatch(os.path.basename(path) + "/", rule):
            return True
    return False


def read_gitignore(path):
    gitignore_path = os.path.join(path, ".gitignore")
    if os.path.isfile(gitignore_path):
        with open(gitignore_path, "r") as f:
            return [
                line.strip() for line in f if line.strip() and not line.startswith("#")
            ]
    return []


def add_line_numbers(content):
    lines = content.splitlines()

    padding = len(str(len(lines)))

    numbered_lines = [f"{i + 1:{padding}}  {line}" for i, line in enumerate(lines)]
    return "\n".join(numbered_lines)


def print_path(writer, path, content, cxml, markdown, line_numbers):
    if cxml:
        print_as_xml(writer, path, content, line_numbers)
    elif markdown:
        print_as_markdown(writer, path, content, line_numbers)
    else:
        print_default(writer, path, content, line_numbers)


def print_default(writer, path, content, line_numbers):
    writer(path)
    writer("---")
    if line_numbers:
        content = add_line_numbers(content)
    writer(content)
    writer("")
    writer("---")


def print_as_xml(writer, path, content, line_numbers):
    global global_index
    writer(f'<document index="{global_index}">')
    writer(f"<source>{path}</source>")
    writer("<document_content>")
    if line_numbers:
        content = add_line_numbers(content)
    writer(content)
    writer("</document_content>")
    writer("</document>")
    global_index += 1


def print_as_markdown(writer, path, content, line_numbers):
    lang = EXT_TO_LANG.get(path.split(".")[-1], "")
    # Figure out how many backticks to use
    backticks = "```"
    while backticks in content:
        backticks += "`"
    writer(path)
    writer(f"{backticks}{lang}")
    if line_numbers:
        content = add_line_numbers(content)
    writer(content)
    writer(f"{backticks}")


def process_path(
    path,
    extensions,
    include_hidden,
    ignore_files_only,
    ignore_gitignore,
    gitignore_rules,
    ignore_patterns,
    writer,
    claude_xml,
    markdown,
    line_numbers=False,
):
    if os.path.isfile(path):
        try:
            if hasattr(writer, "set_current_file"):
                writer.set_current_file(path)
            with open(path, "r") as f:
                print_path(writer, path, f.read(), claude_xml, markdown, line_numbers)
        except UnicodeDecodeError:
            warning_message = f"Warning: Skipping file {path} due to UnicodeDecodeError"
            click.echo(click.style(warning_message, fg="red"), err=True)
        finally:
            if hasattr(writer, "clear_current_file"):
                writer.clear_current_file()
    elif os.path.isdir(path):
        for root, dirs, files in os.walk(path):
            if not include_hidden:
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                files = [f for f in files if not f.startswith(".")]

            if not ignore_gitignore:
                gitignore_rules.extend(read_gitignore(root))
                dirs[:] = [
                    d
                    for d in dirs
                    if not should_ignore(os.path.join(root, d), gitignore_rules)
                ]
                files = [
                    f
                    for f in files
                    if not should_ignore(os.path.join(root, f), gitignore_rules)
                ]

            if ignore_patterns:
                if not ignore_files_only:
                    dirs[:] = [
                        d
                        for d in dirs
                        if not any(fnmatch(d, pattern) for pattern in ignore_patterns)
                    ]
                files = [
                    f
                    for f in files
                    if not any(fnmatch(f, pattern) for pattern in ignore_patterns)
                ]

            if extensions:
                files = [f for f in files if f.endswith(extensions)]

            for file in sorted(files):
                file_path = os.path.join(root, file)
                try:
                    if hasattr(writer, "set_current_file"):
                        writer.set_current_file(file_path)
                    with open(file_path, "r") as f:
                        print_path(
                            writer,
                            file_path,
                            f.read(),
                            claude_xml,
                            markdown,
                            line_numbers,
                        )
                except UnicodeDecodeError:
                    warning_message = (
                        f"Warning: Skipping file {file_path} due to UnicodeDecodeError"
                    )
                    click.echo(click.style(warning_message, fg="red"), err=True)
                finally:
                    if hasattr(writer, "clear_current_file"):
                        writer.clear_current_file()


def read_paths_from_stdin(use_null_separator):
    if sys.stdin.isatty():
        # No ready input from stdin, don't block for input
        return []

    stdin_content = sys.stdin.read()
    if use_null_separator:
        paths = stdin_content.split("\0")
    else:
        paths = stdin_content.split()  # split on whitespace
    return [p for p in paths if p]


@click.command()
@click.argument("paths", nargs=-1, type=click.Path(exists=True))
@click.option("extensions", "-e", "--extension", multiple=True)
@click.option(
    "--include-hidden",
    is_flag=True,
    help="Include files and folders starting with .",
)
@click.option(
    "--ignore-files-only",
    is_flag=True,
    help="--ignore option only ignores files",
)
@click.option(
    "--ignore-gitignore",
    is_flag=True,
    help="Ignore .gitignore files and include all files",
)
@click.option(
    "ignore_patterns",
    "--ignore",
    multiple=True,
    default=[],
    help="List of patterns to ignore",
)
@click.option(
    "output_file",
    "-o",
    "--output",
    type=click.Path(writable=True, allow_dash=True),
    help="Output to a file instead of stdout",
)
@click.option(
    "claude_xml",
    "-c",
    "--cxml",
    is_flag=True,
    help="Output in XML-ish format suitable for Claude's long context window.",
)
@click.option(
    "markdown",
    "-m",
    "--markdown",
    is_flag=True,
    help="Output Markdown with fenced code blocks",
)
@click.option(
    "line_numbers",
    "-n",
    "--line-numbers",
    is_flag=True,
    help="Add line numbers to the output",
)
@click.option(
    "--null",
    "-0",
    is_flag=True,
    help="Use NUL character as separator when reading from stdin",
)
@click.option(
    "--changed",
    is_flag=True,
    help="Instead of positional paths, emit files changed relative to a Git base ref.",
)
@click.option(
    "--base",
    help="Base branch or ref used together with --changed (default: remote HEAD).",
)
@click.option(
    "--remote",
    default="origin",
    show_default=True,
    help="Remote to inspect when resolving the default base branch (requires --changed).",
)
@click.option(
    "--fetch",
    is_flag=True,
    help="Fetch the remote before computing diffs (requires --changed).",
)
@click.option(
    "--skip-untracked",
    is_flag=True,
    help="Exclude untracked files when collecting changed files (requires --changed).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print the detected base ref and files without emitting content (requires --changed).",
)
@click.option(
    "max_chars",
    "--max-chars",
    type=click.IntRange(min=0),
    default=DEFAULT_MAX_CHARS,
    show_default=True,
    help="Maximum characters to emit before truncating output (0 disables the limit).",
)
@click.version_option()
def cli(
    paths,
    extensions,
    include_hidden,
    ignore_files_only,
    ignore_gitignore,
    ignore_patterns,
    output_file,
    claude_xml,
    markdown,
    line_numbers,
    null,
    changed,
    base,
    remote,
    fetch,
    skip_untracked,
    dry_run,
    max_chars,
):
    """
    Takes one or more paths to files or directories and outputs every file,
    recursively, each one preceded with its filename like this:

    \b
        path/to/file.py
        ----
        Contents of file.py goes here
        ---
        path/to/file2.py
        ---
        ...

    If the `--cxml` flag is provided, the output will be structured as follows:

    \b
        <documents>
        <document path="path/to/file1.txt">
        Contents of file1.txt
        </document>
        <document path="path/to/file2.txt">
        Contents of file2.txt
        </document>
        ...
        </documents>

    If the `--markdown` flag is provided, the output will be structured as follows:

    \b
        path/to/file1.py
        ```python
        Contents of file1.py
        ```
    """
    # Reset global_index for pytest
    global global_index
    global_index = 1

    # Read paths from stdin if available
    stdin_paths = read_paths_from_stdin(use_null_separator=null)

    # Combine paths from arguments and stdin
    paths = [*paths, *stdin_paths]

    if not changed and (
        base or fetch or skip_untracked or dry_run or remote != "origin"
    ):
        raise click.ClickException(
            "--base/--remote/--fetch/--skip-untracked/--dry-run can only be used with --changed."
        )

    repo_root: Optional[Path] = None
    base_ref: Optional[str] = None
    repo_config: dict[str, Any] = {}
    changed_ignore_patterns: List[str] = []

    try:
        repo_root = _detect_repo_root()
    except RuntimeError as exc:
        if changed or paths:
            raise click.ClickException(str(exc)) from exc
        repo_root = None

    if repo_root:
        repo_config = _load_cli_config(repo_root)
        ignore_section = repo_config.get("ignore")
        if ignore_section is not None and not isinstance(ignore_section, dict):
            click.echo(
                click.style(
                    f"Warning: 'ignore' section in {CONFIG_FILENAME} must be a table.",
                    fg="yellow",
                ),
                err=True,
            )
            ignore_section = {}
        if isinstance(ignore_section, dict):
            changed_ignore_patterns = _coerce_string_list(
                ignore_section.get("paths"), context="ignore.paths"
            )

        if fetch:
            fetch_result = _run_git(["fetch", remote], repo_root, check=False)
            if fetch_result.returncode != 0:
                warning = fetch_result.stderr.strip() or fetch_result.stdout.strip()
                click.echo(
                    click.style(
                        f"Warning: git fetch {remote} failed: {warning or 'unknown error'}",
                        fg="yellow",
                    ),
                    err=True,
                )

        try:
            base_ref = _resolve_base_ref(base, remote, repo_root)
        except RuntimeError as exc:
            raise click.ClickException(str(exc)) from exc

        try:
            changed_files, missing_files = _collect_changed_files(
                base_ref=base_ref,
                cwd=repo_root,
                include_untracked=not skip_untracked,
            )
        except RuntimeError as exc:
            raise click.ClickException(str(exc)) from exc

        if changed_ignore_patterns:
            filtered: List[str] = []
            skipped: List[str] = []
            for path in changed_files:
                if any(
                    _match_glob(path, pattern) for pattern in changed_ignore_patterns
                ):
                    skipped.append(path)
                    continue
                filtered.append(path)
            changed_files = filtered
            if skipped:
                click.echo(
                    click.style(
                        f"Ignoring paths via {CONFIG_FILENAME}: "
                        + ", ".join(skipped),
                        fg="yellow",
                    ),
                    err=True,
                )

        if missing_files:
            click.echo(
                click.style(
                    f"Skipping missing or non-file paths: {', '.join(missing_files)}",
                    fg="yellow",
                ),
                err=True,
            )

        if not changed_files and not paths:
            click.echo(
                click.style(f"No files changed relative to {base_ref}.", fg="yellow"),
                err=True,
            )
            return

        if dry_run:
            click.echo(f"Base ref: {base_ref}", err=True)
            for path in changed_files:
                click.echo(path, err=True)
            click.echo("Dry run requested; no files emitted.", err=True)
            return

        if changed_files:
            click.echo(
                click.style(f"Using base ref {base_ref}.", fg="green"),
                err=True,
            )

        combined: list[str] = []
        seen: set[str] = set()
        for candidate in [*changed_files, *paths]:
            if candidate not in seen:
                combined.append(candidate)
                seen.add(candidate)
        paths = combined

    if not paths:
        raise click.ClickException(
            "No paths to process. Provide explicit files (or pipe them via stdin) "
            "or use --changed to collect them from Git."
        )

    gitignore_rules = []
    writer = click.echo
    temp_path: Optional[str] = None
    fp = None
    destination_label = "stdout"
    if output_file is None:
        temp_file = tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            delete=False,
            prefix="prooompter_",
            suffix=".txt",
        )
        fp = temp_file
        temp_path = temp_file.name
        destination_label = temp_path
        writer = lambda s: print("" if s is None else s, file=fp)
    elif output_file == "-":
        writer = click.echo
    else:
        fp = open(output_file, "w", encoding="utf-8")
        destination_label = output_file
        writer = lambda s: print("" if s is None else s, file=fp)
    limited_writer = LimitedWriter(writer, max_chars)
    limit_reached_exc: Optional[OutputLimitReached] = None

    context_manager = (
        _temporary_cwd(repo_root) if repo_root is not None else nullcontext()
    )

    try:
        with context_manager:
            for path in paths:
                if not os.path.exists(path):
                    raise click.BadArgumentUsage(f"Path does not exist: {path}")
                if not ignore_gitignore:
                    gitignore_rules.extend(read_gitignore(os.path.dirname(path)))
                if claude_xml and path == paths[0]:
                    if hasattr(limited_writer, "clear_current_file"):
                        limited_writer.clear_current_file()
                    limited_writer("<documents>")
                process_path(
                    path,
                    extensions,
                    include_hidden,
                    ignore_files_only,
                    ignore_gitignore,
                    gitignore_rules,
                    ignore_patterns,
                    limited_writer,
                    claude_xml,
                    markdown,
                    line_numbers,
                )
            if claude_xml:
                if hasattr(limited_writer, "clear_current_file"):
                    limited_writer.clear_current_file()
                limited_writer("</documents>")
    except OutputLimitReached as exc:
        limit_reached_exc = exc
    finally:
        if fp:
            fp.flush()
            fp.close()
    if limit_reached_exc:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass
        limit_display = (
            f"{limit_reached_exc.limit:,}"
            if limit_reached_exc.limit is not None
            else "unknown"
        )
        over_by = max(
            limit_reached_exc.total_before
            + limit_reached_exc.attempted_add
            - (limit_reached_exc.limit or 0),
            0,
        )
        current_label = (
            f'"{limit_reached_exc.current_file}"'
            if limit_reached_exc.current_file
            else "the current chunk"
        )
        message_lines = [
            f"Output exceeded the maximum of {limit_display} characters by {over_by:,} "
            f"while adding {limit_reached_exc.attempted_add:,} characters from {current_label}.",
            "Use --max-chars to increase the limit or 0 to disable it.",
        ]
        if limit_reached_exc.file_totals:
            message_lines.append("Characters emitted per file before stopping:")
            for path, chars in limit_reached_exc.file_totals.items():
                label = path or "(no file context)"
                message_lines.append(f"  - {label}: {chars:,} chars")
        raise click.ClickException("\n".join(message_lines))
    if temp_path:
        click.echo(
            click.style(f"Wrote prooompter output to {temp_path}", fg="green"),
            err=True,
        )
    elif output_file not in (None, "-"):
        click.echo(
            click.style(f"Wrote prooompter output to {output_file}", fg="green"),
            err=True,
        )

    if limited_writer.file_totals:
        _emit_summary(destination_label, limited_writer)


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Entry point used by backend CLI packaging."""
    try:
        cli.main(args=argv, prog_name="prooompter", standalone_mode=False)
    except SystemExit as exc:
        return int(exc.code)
    return 0


if __name__ == "__main__":
    sys.exit(main())
