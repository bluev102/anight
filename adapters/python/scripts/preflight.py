#!/usr/bin/env python3
"""One-command preflight for agents-system V1.

Runs the full baseline gate in order:
1. config validation
2. handoff validation
3. orchestrator smoke run

Usage:
    python adapters/python/scripts/preflight.py
    python adapters/python/scripts/preflight.py --workflow core/config/workflow.yml --stages workspace/stages
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
DEFAULT_WORKFLOW = REPO_ROOT / "core/config/workflow.yml"
DEFAULT_STAGES = REPO_ROOT / "workspace/stages"
VALIDATE_CONFIG = SCRIPT_DIR / "validate_config.py"
VALIDATE_HANDOFF = SCRIPT_DIR / "validate_handoff.py"
ORCHESTRATOR = SCRIPT_DIR / "orchestrator.py"


@dataclass
class StepResult:
    name: str
    command: list[str]
    returncode: int
    output: str


def _run_command(command: list[str]) -> StepResult:
    proc = subprocess.run(command, capture_output=True, text=True, check=False)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return StepResult(
        name=command[0], command=command, returncode=proc.returncode, output=output
    )


def _print_step_header(step_name: str, command: list[str]) -> None:
    print(f"== {step_name} ==")
    print("$ " + " ".join(command))


def _print_step_output(result: StepResult) -> None:
    if result.output:
        print(result.output)


def run(workflow: Path, stages: Path) -> int:
    steps = [
        ("config-validation", [sys.executable, str(VALIDATE_CONFIG), "--all"]),
        (
            "handoff-validation",
            [sys.executable, str(VALIDATE_HANDOFF), "--dir", str(stages), "--strict"],
        ),
        (
            "orchestrator-smoke",
            [
                sys.executable,
                str(ORCHESTRATOR),
                "--workflow",
                str(workflow),
                "--no-strict-input",
                "--no-strict-handoff",
            ],
        ),
    ]

    for step_name, command in steps:
        _print_step_header(step_name, command)
        result = _run_command(command)
        _print_step_output(result)
        if result.returncode != 0:
            print(f"[preflight] {step_name} failed with exit code {result.returncode}")
            return result.returncode
        print(f"[preflight] {step_name} passed")
        print()

    print("[preflight] all checks passed")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run all baseline checks for agents-system"
    )
    parser.add_argument(
        "--workflow", type=Path, default=DEFAULT_WORKFLOW, help="Workflow config path"
    )
    parser.add_argument(
        "--stages", type=Path, default=DEFAULT_STAGES, help="Stages directory path"
    )
    args = parser.parse_args()

    try:
        return run(args.workflow, args.stages)
    except Exception as exc:  # pylint: disable=broad-except
        print(f"[preflight] unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
