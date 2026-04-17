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


def default_dest_root() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


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


def sync_skill(skill: Skill, dest_root: Path, *, dry_run: bool) -> None:
    dest_path = dest_root / skill.skill_id
    print(f"{'Would sync' if dry_run else 'Syncing'} {skill.skill_id} -> {dest_path}")
    if dry_run:
        return
    with tempfile.TemporaryDirectory(
        prefix=f".{skill.skill_id}.tmp-",
        dir=dest_root,
    ) as temp_dir:
        temp_path = Path(temp_dir) / skill.skill_id
        shutil.copytree(skill.source_path, temp_path, copy_function=shutil.copy2)
        if dest_path.exists():
            remove_path(dest_path, dry_run=False)
        temp_path.replace(dest_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Synchronize repo-local skills into Codex's skills directory."
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
        help="Destination Codex skills root. Defaults to $CODEX_HOME/skills or ~/.codex/skills.",
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
    source_root = args.source_root.expanduser().resolve()
    dest_root = args.dest.expanduser().resolve()
    state_path = dest_root / STATE_FILE_NAME

    skills = discover_skills(source_root)
    selected = resolve_selection(skills, args.skills)

    old_state = load_state(state_path)
    old_managed = set(old_state.get("managed_skill_ids", []))
    selected_ids = {skill.skill_id for skill in selected}
    discovered_ids = {skill.skill_id for skill in skills}

    if args.prune:
        prune = True
    elif args.no_prune:
        prune = False
    else:
        prune = not args.skills

    stale_ids = sorted(old_managed - selected_ids) if prune else []

    print(f"Source root: {source_root}")
    print(f"Destination root: {dest_root}")
    if selected:
        print("Selected skills: " + ", ".join(skill.skill_id for skill in selected))
    else:
        print("Selected skills: none")
    print(f"Prune stale managed skills: {'yes' if prune else 'no'}")

    if not args.dry_run:
        dest_root.mkdir(parents=True, exist_ok=True)

    for stale_id in stale_ids:
        stale_path = dest_root / stale_id
        if stale_path.exists():
            print(f"{'Would remove' if args.dry_run else 'Removing'} stale managed skill {stale_id}")
            remove_path(stale_path, dry_run=args.dry_run)

    for skill in selected:
        sync_skill(skill, dest_root, dry_run=args.dry_run)

    if prune:
        managed_ids = sorted(discovered_ids if not args.skills else selected_ids)
    else:
        managed_ids = sorted((old_managed - set(stale_ids)) | selected_ids)

    write_state(
        state_path,
        source_root=source_root,
        managed_skill_ids=managed_ids,
        dry_run=args.dry_run,
    )

    if managed_ids:
        print("Managed skill ids: " + ", ".join(managed_ids))
    else:
        print("Managed skill ids: none")
    print("Restart Codex to pick up synced skills.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
