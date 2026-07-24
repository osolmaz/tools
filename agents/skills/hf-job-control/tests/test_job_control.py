from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[1] / "scripts" / "job_control.py"
SPEC = importlib.util.spec_from_file_location("hf_job_control", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
JOB = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = JOB
SPEC.loader.exec_module(JOB)


def minimal_control(**changes: object) -> dict[str, object]:
    value: dict[str, object] = {
        "schema_version": 1,
        "run_id": "training-run-v1",
        "generation": 1,
        "action": "run",
    }
    value.update(changes)
    return value


def test_minimal_control_is_valid() -> None:
    value = minimal_control()
    assert JOB.validate_control(value) == value
    assert JOB.control_path("training-run-v1") == "controls/training-run-v1.json"


def test_unknown_field_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown=.*surprise"):
        JOB.validate_control(minimal_control(surprise=True))


def test_mutable_limit_cannot_exceed_hard_limit() -> None:
    with pytest.raises(ValueError, match="exceeds hard maximum"):
        JOB.validate_control(
            minimal_control(max_epochs=11),
            hard_max_epochs=10,
        )


def test_resume_payload_is_content_addressed() -> None:
    digest = "a" * 64
    value = minimal_control(
        resume_from={
            "bucket": "osolmaz/jobs-artifacts",
            "key": f"program/run/checkpoints/sha256-{digest}/checkpoint.tar.zst",
            "sha256": digest,
            "bytes": 1024,
        }
    )
    assert JOB.validate_control(value) == value


def test_resume_payload_rejects_key_without_digest_segment() -> None:
    with pytest.raises(ValueError, match="sha256-<digest>"):
        JOB.validate_control(
            minimal_control(
                resume_from={
                    "bucket": "osolmaz/jobs-artifacts",
                    "key": "program/run/checkpoints/checkpoint.tar.zst",
                    "sha256": "a" * 64,
                    "bytes": 1024,
                }
            )
        )


def test_next_control_increments_and_carries_desired_state() -> None:
    digest = "b" * 64
    resume = {
        "bucket": "osolmaz/jobs-artifacts",
        "key": f"program/run/checkpoints/sha256-{digest}/checkpoint.tar.zst",
        "sha256": digest,
        "bytes": 2048,
    }
    previous = minimal_control(max_epochs=8, resume_from=resume)
    value = JOB.build_next_control(
        run_id="training-run-v1",
        action="pause",
        previous=previous,
        reason="Maintenance window",
        max_epochs=None,
        clear_max_epochs=False,
        resume_from=None,
        clear_resume=False,
        hard_max_epochs=10,
    )
    assert value == {
        "schema_version": 1,
        "run_id": "training-run-v1",
        "generation": 2,
        "action": "pause",
        "reason": "Maintenance window",
        "max_epochs": 8,
        "resume_from": resume,
    }


def test_setting_max_requires_the_hard_bound() -> None:
    with pytest.raises(ValueError, match="hard-max-epochs"):
        JOB.build_next_control(
            run_id="training-run-v1",
            action="run",
            previous=None,
            reason=None,
            max_epochs=10,
            clear_max_epochs=False,
            resume_from=None,
            clear_resume=False,
            hard_max_epochs=None,
        )
