#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from dataclasses import dataclass
from pathlib import Path


STATE_FILE_NAME = ".tools-agents-skill-sync.json"
FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---(?:\n|$)", re.DOTALL)
NAME_RE = re.compile(r"^name:\s*(.+?)\s*$", re.MULTILINE)


@dataclass(frozen=True)
class Skill:
    source_name: str
    skill_id: str
    source_path: Path


@dataclass(frozen=True)
class Destination:
    name: str
    skills_root: Path
    agents_dest: Path
    restart_hint: str


def default_dest_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def default_claude_dest_root() -> Path:
    claude_home = os.environ.get("CLAUDE_CONFIG_DIR")
    if claude_home:
        return Path(claude_home).expanduser() / "skills"
    return Path.home() / ".claude" / "skills"


def default_agents_source() -> Path:
    return Path(__file__).resolve().parent / "AGENTS.md"


def parse_skill_id(skill_dir: Path) -> str:
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        raise ValueError(f"missing SKILL.md in {skill_dir}")
    content = skill_md.read_text(encoding="utf-8")
    frontmatter = FRONTMATTER_RE.match(content)
    if not frontmatter:
        raise ValueError(f"invalid SKILL.md frontmatter in {skill_md}")
    name_match = NAME_RE.search(frontmatter.group(1))
    if not name_match:
        raise ValueError(f"missing frontmatter name in {skill_md}")
    raw_name = name_match.group(1).strip().strip("\"'")
    if not raw_name:
        raise ValueError(f"empty frontmatter name in {skill_md}")
    return raw_name


def discover_skills(source_root: Path) -> list[Skill]:
    if not source_root.exists():
        return []
    skills: list[Skill] = []
    seen_ids: dict[str, Path] = {}
    for child in sorted(source_root.iterdir()):
        if not child.is_dir():
            continue
        if not (child / "SKILL.md").exists():
            continue
        skill_id = parse_skill_id(child)
        if skill_id in seen_ids:
            other = seen_ids[skill_id]
            raise ValueError(
                f"duplicate skill id {skill_id!r} in {other} and {child}"
            )
        seen_ids[skill_id] = child
        skills.append(
            Skill(source_name=child.name, skill_id=skill_id, source_path=child)
        )
    return skills


def load_state(state_path: Path) -> dict:
    if not state_path.exists():
        return {"version": 1, "managed_skill_ids": []}
    return json.loads(state_path.read_text(encoding="utf-8"))


def write_state(
    state_path: Path, *, source_root: Path, managed_skill_ids: list[str], dry_run: bool
) -> None:
    state = {
        "version": 1,
        "source_root": str(source_root),
        "managed_skill_ids": managed_skill_ids,
    }
    if dry_run:
        return
    state_path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def resolve_selection(skills: list[Skill], selectors: list[str]) -> list[Skill]:
    if not selectors:
        return skills
    by_source = {skill.source_name: skill for skill in skills}
    by_id = {skill.skill_id: skill for skill in skills}
    selected: list[Skill] = []
    seen: set[str] = set()
    for selector in selectors:
        skill = by_id.get(selector) or by_source.get(selector)
        if skill is None:
            raise ValueError(f"unknown skill selector {selector!r}")
        if skill.skill_id in seen:
            continue
        seen.add(skill.skill_id)
        selected.append(skill)
    return selected


def remove_path(path: Path, *, dry_run: bool) -> None:
    if not path.exists():
        return
    if dry_run:
        return
    if path.is_dir() and not path.is_symlink():
        shutil.rmtree(path)
    else:
        path.unlink()


def sync_file(source_path: Path, dest_path: Path, *, dry_run: bool, label: str) -> None:
    print(f"{'Would sync' if dry_run else 'Syncing'} {label} -> {dest_path}")
    if dry_run:
        return
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        prefix=f".{dest_path.name}.tmp-",
        dir=dest_path.parent,
        delete=False,
    ) as temp_file:
        temp_path = Path(temp_file.name)
    try:
        shutil.copy2(source_path, temp_path)
        temp_path.replace(dest_path)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def sync_skill(skill: Skill, dest_root: Path, *, dry_run: bool) -> None:
    dest_path = dest_root / skill.skill_id
    print(f"{'Would sync' if dry_run else 'Syncing'} {skill.skill_id} -> {dest_path}")
    if dry_run:
        return
    source_path = skill.source_path.resolve()

    def ignore_nested_skill_files(directory: str, names: list[str]) -> set[str]:
        # Codex discovers SKILL.md files recursively; nested reference copies
        # should not register as additional local skills.
        if Path(directory).resolve() != source_path and "SKILL.md" in names:
            return {"SKILL.md"}
        return set()

    with tempfile.TemporaryDirectory(
        prefix=f".{skill.skill_id}.tmp-",
        dir=dest_root,
    ) as temp_dir:
        temp_path = Path(temp_dir) / skill.skill_id
        shutil.copytree(
            skill.source_path,
            temp_path,
            copy_function=shutil.copy2,
            ignore=ignore_nested_skill_files,
        )
        if dest_path.exists():
            remove_path(dest_path, dry_run=False)
        temp_path.replace(dest_path)


def sync_destination(
    destination: Destination,
    *,
    agents_source: Path,
    source_root: Path,
    skills: list[Skill],
    selected: list[Skill],
    selectors: list[str],
    prune: bool,
    dry_run: bool,
) -> None:
    state_path = destination.skills_root / STATE_FILE_NAME
    old_state = load_state(state_path)
    old_managed = set(old_state.get("managed_skill_ids", []))
    selected_ids = {skill.skill_id for skill in selected}
    discovered_ids = {skill.skill_id for skill in skills}

    stale_ids = sorted(old_managed - selected_ids) if prune else []

    print(f"== {destination.name} ==")
    print(f"Destination root: {destination.skills_root}")
    print(f"Agents destination: {destination.agents_dest}")

    if not dry_run:
        destination.skills_root.mkdir(parents=True, exist_ok=True)

    sync_file(
        agents_source,
        destination.agents_dest,
        dry_run=dry_run,
        label=destination.agents_dest.name,
    )

    for stale_id in stale_ids:
        stale_path = destination.skills_root / stale_id
        if stale_path.exists():
            print(f"{'Would remove' if dry_run else 'Removing'} stale managed skill {stale_id}")
            remove_path(stale_path, dry_run=dry_run)

    for skill in selected:
        sync_skill(skill, destination.skills_root, dry_run=dry_run)

    if prune:
        managed_ids = sorted(discovered_ids if not selectors else selected_ids)
    else:
        managed_ids = sorted((old_managed - set(stale_ids)) | selected_ids)

    write_state(
        state_path,
        source_root=source_root,
        managed_skill_ids=managed_ids,
        dry_run=dry_run,
    )

    if managed_ids:
        print("Managed skill ids: " + ", ".join(managed_ids))
    else:
        print("Managed skill ids: none")
    print(destination.restart_hint)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Synchronize repo-local skills and AGENTS.md into Codex and "
            "Claude Code home directories."
        )
    )
    parser.add_argument(
        "skills",
        nargs="*",
        help="Optional skill ids or source directory names to sync. Defaults to all repo-local skills.",
    )
    parser.add_argument(
        "--source-root",
        default=Path(__file__).resolve().parent / "skills",
        type=Path,
        help="Source skills directory. Defaults to agents/skills next to this script.",
    )
    parser.add_argument(
        "--dest",
        default=default_dest_root(),
        type=Path,
        help="Destination Codex skills root. Also syncs agents/AGENTS.md to the parent Codex home dir. Defaults to $CODEX_HOME/skills or ~/.codex/skills.",
    )
    parser.add_argument(
        "--claude-dest",
        default=default_claude_dest_root(),
        type=Path,
        help="Destination Claude Code skills root. Also syncs agents/AGENTS.md to CLAUDE.md in the parent Claude home dir. Defaults to $CLAUDE_CONFIG_DIR/skills or ~/.claude/skills.",
    )
    parser.add_argument(
        "--skip-codex",
        action="store_true",
        help="Do not sync to the Codex destination.",
    )
    parser.add_argument(
        "--skip-claude",
        action="store_true",
        help="Do not sync to the Claude Code destination.",
    )
    prune = parser.add_mutually_exclusive_group()
    prune.add_argument(
        "--prune",
        action="store_true",
        help="Remove previously synced repo-managed skills that are no longer selected.",
    )
    prune.add_argument(
        "--no-prune",
        action="store_true",
        help="Keep previously synced repo-managed skills even if they are not selected now.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned changes without writing anything.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.skip_codex and args.skip_claude:
        raise ValueError("nothing to do: both --skip-codex and --skip-claude given")

    source_root = args.source_root.expanduser().resolve()
    agents_source = default_agents_source().expanduser().resolve()

    destinations: list[Destination] = []
    if not args.skip_codex:
        codex_skills_root = args.dest.expanduser().resolve()
        destinations.append(
            Destination(
                name="Codex",
                skills_root=codex_skills_root,
                agents_dest=codex_skills_root.parent / "AGENTS.md",
                restart_hint="Restart Codex to pick up synced skills.",
            )
        )
    if not args.skip_claude:
        claude_skills_root = args.claude_dest.expanduser().resolve()
        destinations.append(
            Destination(
                name="Claude Code",
                skills_root=claude_skills_root,
                agents_dest=claude_skills_root.parent / "CLAUDE.md",
                restart_hint="Start a new Claude Code session to pick up synced skills.",
            )
        )

    skills = discover_skills(source_root)
    selected = resolve_selection(skills, args.skills)

    if args.prune:
        prune = True
    elif args.no_prune:
        prune = False
    else:
        prune = not args.skills

    print(f"Source root: {source_root}")
    print(f"AGENTS source: {agents_source}")
    if selected:
        print("Selected skills: " + ", ".join(skill.skill_id for skill in selected))
    else:
        print("Selected skills: none")
    print(f"Prune stale managed skills: {'yes' if prune else 'no'}")

    if not agents_source.exists():
        raise FileNotFoundError(f"missing AGENTS.md at {agents_source}")

    for destination in destinations:
        print()
        sync_destination(
            destination,
            agents_source=agents_source,
            source_root=source_root,
            skills=skills,
            selected=selected,
            selectors=args.skills,
            prune=prune,
            dry_run=args.dry_run,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
