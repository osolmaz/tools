#!/usr/bin/env python3

from __future__ import annotations

import argparse
import hashlib
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path


FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---(?:\n|$)", re.DOTALL)
NAME_RE = re.compile(r"^name:\s*simpledoc\s*$", re.MULTILINE)


def default_source() -> Path:
    repo = os.environ.get("SIMPLEDOC_REPO")
    if repo:
        return Path(repo).expanduser() / "skills" / "simpledoc"
    return Path.home() / "repos" / "SimpleDoc" / "skills" / "simpledoc"


def default_destination() -> Path:
    return Path(__file__).resolve().parent / "skills" / "simpledoc"


def validate_skill(skill_dir: Path) -> None:
    skill_file = skill_dir / "SKILL.md"
    if not skill_file.is_file():
        raise ValueError(f"missing SimpleDoc skill file: {skill_file}")
    content = skill_file.read_text(encoding="utf-8")
    frontmatter = FRONTMATTER_RE.match(content)
    if not frontmatter or not NAME_RE.search(frontmatter.group(1)):
        raise ValueError(f"expected frontmatter name 'simpledoc' in {skill_file}")


def file_manifest(root: Path) -> dict[str, tuple[str, int]]:
    if not root.exists():
        return {}
    manifest: dict[str, tuple[str, int]] = {}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError(f"skill trees must not contain symlinks: {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        mode = stat.S_IMODE(path.stat().st_mode)
        manifest[relative] = (digest, mode)
    return manifest


def describe_drift(
    source: dict[str, tuple[str, int]],
    destination: dict[str, tuple[str, int]],
) -> list[str]:
    messages: list[str] = []
    for path in sorted(source.keys() - destination.keys()):
        messages.append(f"missing from destination: {path}")
    for path in sorted(destination.keys() - source.keys()):
        messages.append(f"only in destination: {path}")
    for path in sorted(source.keys() & destination.keys()):
        if source[path] != destination[path]:
            messages.append(f"different: {path}")
    return messages


def sync_skill(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(
        prefix=".simpledoc-skill-",
        dir=destination.parent,
    ) as temp_dir:
        staged = Path(temp_dir) / "simpledoc"
        shutil.copytree(source, staged, copy_function=shutil.copy2)
        if destination.exists():
            shutil.rmtree(destination)
        staged.replace(destination)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Copy the SimpleDoc skill from a SimpleDoc checkout into "
            "agents/skills/simpledoc."
        )
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=default_source(),
        help=(
            "Source SimpleDoc skill directory. Defaults to "
            "$SIMPLEDOC_REPO/skills/simpledoc or "
            "~/repos/SimpleDoc/skills/simpledoc."
        ),
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=default_destination(),
        help="Destination skill directory. Defaults to agents/skills/simpledoc.",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit nonzero when the checked-in copy differs from the source.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report whether a sync is needed without writing files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source = args.source.expanduser().resolve()
    destination = args.destination.expanduser().resolve()
    if source == destination:
        raise ValueError("source and destination must be different directories")

    validate_skill(source)
    source_manifest = file_manifest(source)
    destination_manifest = file_manifest(destination)
    drift = describe_drift(source_manifest, destination_manifest)

    if not drift:
        print(f"SimpleDoc skill is up to date: {destination}")
        return 0

    if args.check:
        print("SimpleDoc skill copy is out of date:")
        for message in drift:
            print(f"- {message}")
        return 1

    if args.dry_run:
        print(f"Would sync SimpleDoc skill: {source} -> {destination}")
        for message in drift:
            print(f"- {message}")
        return 0

    sync_skill(source, destination)
    print(f"Synced SimpleDoc skill: {source} -> {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
