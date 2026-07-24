# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "huggingface-hub>=1.2,<2",
# ]
# ///

"""Publish and inspect versioned control documents for detached HF Jobs."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any

from huggingface_hub import CommitOperationAdd, HfApi, hf_hub_download
from huggingface_hub.errors import EntryNotFoundError

SCHEMA_VERSION = 1
DEFAULT_REPO = "osolmaz/jobs-control"
DEFAULT_REVISION = "main"
ACTIONS = ("run", "pause", "stop", "abort")
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
REPO_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
ALLOWED_FIELDS = {
    "schema_version",
    "run_id",
    "generation",
    "action",
    "reason",
    "max_epochs",
    "resume_from",
}
RESUME_FIELDS = {"bucket", "key", "sha256", "bytes"}


@dataclass(frozen=True)
class FetchedControl:
    revision: str
    path: str
    sha256: str | None
    control: dict[str, Any] | None


def control_path(run_id: str) -> str:
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run_id must match ^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
    return f"controls/{run_id}.json"


def stable_json_bytes(value: dict[str, Any]) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _require_integer(value: Any, name: str, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer >= {minimum}")
    return value


def _validate_resume(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("resume_from must be an object")
    unknown = set(value) - RESUME_FIELDS
    missing = RESUME_FIELDS - set(value)
    if unknown or missing:
        raise ValueError(
            f"resume_from fields mismatch: missing={sorted(missing)} "
            f"unknown={sorted(unknown)}"
        )
    bucket = value["bucket"]
    if not isinstance(bucket, str) or not REPO_ID_RE.fullmatch(bucket):
        raise ValueError("resume_from.bucket must be a namespace/name Bucket ID")
    key = value["key"]
    if not isinstance(key, str) or not key or len(key) > 1024:
        raise ValueError("resume_from.key must be a non-empty string <= 1024 chars")
    if key.startswith(("/", "\\")) or "\\" in key:
        raise ValueError("resume_from.key must be a relative POSIX key")
    parts = PurePosixPath(key).parts
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("resume_from.key contains an unsafe path component")
    digest = value["sha256"]
    if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
        raise ValueError("resume_from.sha256 must be 64 lowercase hex characters")
    if f"sha256-{digest}" not in parts:
        raise ValueError("resume_from.key must contain a sha256-<digest> segment")
    _require_integer(value["bytes"], "resume_from.bytes", 1)
    return value


def validate_control(
    value: Any,
    *,
    expected_run_id: str | None = None,
    hard_max_epochs: float | None = None,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("control must be an object")
    unknown = set(value) - ALLOWED_FIELDS
    required = {"schema_version", "run_id", "generation", "action"}
    missing = required - set(value)
    if unknown or missing:
        raise ValueError(
            f"control fields mismatch: missing={sorted(missing)} "
            f"unknown={sorted(unknown)}"
        )
    if value["schema_version"] != SCHEMA_VERSION:
        raise ValueError(f"schema_version must be {SCHEMA_VERSION}")
    run_id = value["run_id"]
    control_path(run_id)
    if expected_run_id is not None and run_id != expected_run_id:
        raise ValueError(f"run_id mismatch: {run_id!r} != {expected_run_id!r}")
    _require_integer(value["generation"], "generation", 1)
    if value["action"] not in ACTIONS:
        raise ValueError(f"action must be one of {ACTIONS}")
    if "reason" in value:
        reason = value["reason"]
        if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
            raise ValueError("reason must be a non-empty string <= 2000 chars")
    if "max_epochs" in value:
        max_epochs = value["max_epochs"]
        if (
            isinstance(max_epochs, bool)
            or not isinstance(max_epochs, (int, float))
            or not math.isfinite(float(max_epochs))
            or float(max_epochs) <= 0
        ):
            raise ValueError("max_epochs must be a finite number > 0")
        if hard_max_epochs is not None and float(max_epochs) > hard_max_epochs:
            raise ValueError(
                f"max_epochs {max_epochs} exceeds hard maximum {hard_max_epochs}"
            )
    if "resume_from" in value:
        _validate_resume(value["resume_from"])
    return value


def fetch_control(
    *,
    repo_id: str,
    run_id: str,
    revision: str = DEFAULT_REVISION,
    api: HfApi | None = None,
    allow_missing: bool = False,
) -> FetchedControl | None:
    path = control_path(run_id)
    client = api or HfApi()
    info = client.repo_info(repo_id=repo_id, repo_type="dataset", revision=revision)
    head = str(info.sha)
    try:
        local_path = Path(
            hf_hub_download(
                repo_id=repo_id,
                repo_type="dataset",
                filename=path,
                revision=head,
            )
        )
    except EntryNotFoundError:
        if allow_missing:
            return FetchedControl(
                revision=head,
                path=path,
                sha256=None,
                control=None,
            )
        raise ValueError(f"missing control document {repo_id}@{head}:{path}") from None
    raw = local_path.read_bytes()
    control = json.loads(raw)
    validate_control(control, expected_run_id=run_id)
    return FetchedControl(
        revision=head,
        path=path,
        sha256=sha256_bytes(raw),
        control=control,
    )


def build_next_control(
    *,
    run_id: str,
    action: str,
    previous: dict[str, Any] | None,
    reason: str | None,
    max_epochs: float | None,
    clear_max_epochs: bool,
    resume_from: dict[str, Any] | None,
    clear_resume: bool,
    hard_max_epochs: float | None,
) -> dict[str, Any]:
    if previous is not None:
        validate_control(previous, expected_run_id=run_id)
    value: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "run_id": run_id,
        "generation": 1 if previous is None else previous["generation"] + 1,
        "action": action,
    }
    if reason is not None:
        value["reason"] = reason
    if max_epochs is not None:
        if hard_max_epochs is None:
            raise ValueError("--hard-max-epochs is required with --max-epochs")
        value["max_epochs"] = max_epochs
    elif not clear_max_epochs and previous is not None and "max_epochs" in previous:
        value["max_epochs"] = previous["max_epochs"]
    if resume_from is not None:
        value["resume_from"] = resume_from
    elif not clear_resume and previous is not None and "resume_from" in previous:
        value["resume_from"] = previous["resume_from"]
    return validate_control(
        value,
        expected_run_id=run_id,
        hard_max_epochs=hard_max_epochs,
    )


def _add_common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--repo", default=DEFAULT_REPO)
    parser.add_argument("--revision", default=DEFAULT_REVISION)
    parser.add_argument("--run-id", required=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    show = subparsers.add_parser("show", help="Show the current exact control")
    _add_common(show)

    validate = subparsers.add_parser("validate", help="Validate a local control file")
    validate.add_argument("path", type=Path)
    validate.add_argument("--run-id")
    validate.add_argument("--hard-max-epochs", type=float)

    publish = subparsers.add_parser(
        "publish", help="Publish the next control generation"
    )
    _add_common(publish)
    publish.add_argument("--action", required=True, choices=ACTIONS)
    publish.add_argument("--reason")
    max_group = publish.add_mutually_exclusive_group()
    max_group.add_argument("--max-epochs", type=float)
    max_group.add_argument("--clear-max-epochs", action="store_true")
    publish.add_argument("--hard-max-epochs", type=float)
    resume_group = publish.add_argument_group("resume payload")
    resume_group.add_argument("--resume-bucket")
    resume_group.add_argument("--resume-key")
    resume_group.add_argument("--resume-sha256")
    resume_group.add_argument("--resume-bytes", type=int)
    resume_group.add_argument("--clear-resume", action="store_true")
    publish.add_argument("--expected-generation", type=int)
    return parser.parse_args()


def _resume_from_args(args: argparse.Namespace) -> dict[str, Any] | None:
    values = {
        "bucket": args.resume_bucket,
        "key": args.resume_key,
        "sha256": args.resume_sha256,
        "bytes": args.resume_bytes,
    }
    present = {name for name, value in values.items() if value is not None}
    if present and present != set(values):
        missing = sorted(set(values) - present)
        raise ValueError(f"resume payload is incomplete; missing {missing}")
    if present and args.clear_resume:
        raise ValueError("resume payload and --clear-resume are mutually exclusive")
    return values if present else None


def main() -> int:
    args = parse_args()
    if args.command == "validate":
        value = json.loads(args.path.read_text(encoding="utf-8"))
        validate_control(
            value,
            expected_run_id=args.run_id,
            hard_max_epochs=args.hard_max_epochs,
        )
        print(json.dumps(value, indent=2, sort_keys=True))
        return 0

    if not REPO_ID_RE.fullmatch(args.repo):
        raise ValueError("--repo must be a namespace/name dataset ID")
    api = HfApi()
    fetched = fetch_control(
        repo_id=args.repo,
        run_id=args.run_id,
        revision=args.revision,
        api=api,
        allow_missing=args.command == "publish",
    )
    if args.command == "show":
        assert fetched is not None
        print(
            json.dumps(
                {
                    "repo": args.repo,
                    "revision": fetched.revision,
                    "path": fetched.path,
                    "sha256": fetched.sha256,
                    "control": fetched.control,
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 0

    assert args.command == "publish"
    assert fetched is not None
    previous = fetched.control
    if args.expected_generation is not None:
        actual = 0 if previous is None else previous["generation"]
        if actual != args.expected_generation:
            raise ValueError(
                f"expected generation {args.expected_generation}, found {actual}"
            )
    resume_from = _resume_from_args(args)
    control = build_next_control(
        run_id=args.run_id,
        action=args.action,
        previous=previous,
        reason=args.reason,
        max_epochs=args.max_epochs,
        clear_max_epochs=args.clear_max_epochs,
        resume_from=resume_from,
        clear_resume=args.clear_resume,
        hard_max_epochs=args.hard_max_epochs,
    )
    raw = stable_json_bytes(control)
    path = control_path(args.run_id)
    head = api.repo_info(
        repo_id=args.repo,
        repo_type="dataset",
        revision=args.revision,
    ).sha
    if str(head) != fetched.revision:
        raise RuntimeError(
            f"control repository advanced from {fetched.revision} to {head}; retry"
        )
    commit = api.create_commit(
        repo_id=args.repo,
        repo_type="dataset",
        revision=args.revision,
        parent_commit=str(head),
        operations=[CommitOperationAdd(path_in_repo=path, path_or_fileobj=raw)],
        commit_message=(
            f"control({args.run_id}): generation {control['generation']} "
            f"{control['action']}"
        ),
        commit_description=control.get("reason"),
    )
    print(
        json.dumps(
            {
                "repo": args.repo,
                "revision": commit.oid,
                "path": path,
                "sha256": sha256_bytes(raw),
                "control": control,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, RuntimeError) as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(2) from error
