#!/usr/bin/env python3
"""Launch a balanced tmux grid of concurrent localpi demo sessions."""

from __future__ import annotations

import argparse
import datetime as dt
import os
import shlex
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LaunchPlan:
    session: str
    concurrency: int
    cwd: Path
    command: str
    attach_command: str


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    plan = build_plan(args)

    if args.dry_run:
        print_plan(plan)
        return 0

    require_tmux()
    if tmux_session_exists(plan.session):
        if not args.restart:
            raise SystemExit(
                f"tmux session {plan.session!r} already exists; pass --restart to replace it"
            )
        run(["tmux", "kill-session", "-t", plan.session])

    launch_tmux_grid(plan)
    print(f"tmux session: {plan.session}")
    print(f"panes: {plan.concurrency}")
    print(f"attach: {plan.attach_command}")
    return 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Launch a tmux grid of concurrent localpi --demo panes."
    )
    parser.add_argument(
        "--concurrency",
        "-n",
        type=positive_int,
        required=True,
        help="number of concurrent demo panes to launch",
    )
    parser.add_argument(
        "--session",
        "-s",
        default=default_session_name(),
        help="tmux session name to create",
    )
    parser.add_argument(
        "--cwd",
        default=os.getcwd(),
        help="working directory for each tmux pane",
    )
    parser.add_argument(
        "--command",
        help="shell command to run in every pane; defaults to positional command after --",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="kill an existing tmux session with the same name before launching",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the launch plan without creating a tmux session",
    )
    parser.add_argument(
        "command_args",
        nargs=argparse.REMAINDER,
        help="command to run in each pane, usually after --",
    )
    return parser.parse_args(argv)


def build_plan(args: argparse.Namespace) -> LaunchPlan:
    command = command_from_args(args.command, args.command_args)
    cwd = Path(args.cwd).expanduser().resolve()
    if not cwd.exists() or not cwd.is_dir():
        raise SystemExit(f"--cwd must be an existing directory: {cwd}")

    return LaunchPlan(
        session=args.session,
        concurrency=args.concurrency,
        cwd=cwd,
        command=command,
        attach_command=f"tmux attach -t {shlex.quote(args.session)}",
    )


def command_from_args(command: str | None, command_args: list[str]) -> str:
    if command is not None and command_args:
        raise SystemExit("use either --command or a positional command after --, not both")
    if command is not None:
        return command

    args = command_args[1:] if command_args[:1] == ["--"] else command_args
    if not args:
        return "localpi --demo"
    return shlex.join(args)


def launch_tmux_grid(plan: LaunchPlan) -> None:
    first_command = pane_shell_command(plan, 1)
    run(
        [
            "tmux",
            "new-session",
            "-d",
            "-s",
            plan.session,
            "-n",
            "demo",
            "-c",
            str(plan.cwd),
            first_command,
        ]
    )
    configure_tmux_window(plan.session)

    for index in range(2, plan.concurrency + 1):
        run(
            [
                "tmux",
                "split-window",
                "-t",
                f"{plan.session}:0",
                "-c",
                str(plan.cwd),
                pane_shell_command(plan, index),
            ]
        )
        run(["tmux", "select-layout", "-t", f"{plan.session}:0", "tiled"])

    run(["tmux", "select-layout", "-t", f"{plan.session}:0", "tiled"])


def configure_tmux_window(session: str) -> None:
    target = f"{session}:0"
    run(["tmux", "set-window-option", "-t", target, "remain-on-exit", "on"])
    run(["tmux", "set-window-option", "-t", target, "automatic-rename", "off"])
    run(["tmux", "set-window-option", "-t", target, "aggressive-resize", "on"])
    run(["tmux", "setw", "-t", target, "pane-border-status", "top"])
    run(["tmux", "setw", "-t", target, "pane-border-format", "#{pane_index}"])


def pane_shell_command(plan: LaunchPlan, index: int) -> str:
    env = {
        "LOCALPI_DEMO_INDEX": str(index),
        "LOCALPI_DEMO_TOTAL": str(plan.concurrency),
    }
    exports = " ".join(f"{key}={shlex.quote(value)}" for key, value in env.items())
    label = f"[localpi demo {index}/{plan.concurrency}]"
    return f"printf '%s\\n' {shlex.quote(label)}; {exports} sh -lc {shlex.quote(plan.command)}"


def print_plan(plan: LaunchPlan) -> None:
    print(f"tmux session: {plan.session}")
    print(f"panes: {plan.concurrency}")
    print(f"cwd: {plan.cwd}")
    print(f"command: {plan.command}")
    print(f"layout: tiled")
    print(f"attach: {plan.attach_command}")


def require_tmux() -> None:
    if shutil.which("tmux") is None:
        raise SystemExit("tmux is required but was not found on PATH")


def tmux_session_exists(session: str) -> bool:
    result = subprocess.run(
        ["tmux", "has-session", "-t", session],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    return result.returncode == 0


def run(command: list[str]) -> None:
    subprocess.run(command, check=True)


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("must be a positive integer")
    return parsed


def default_session_name() -> str:
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"pi-demo-{stamp}"


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
