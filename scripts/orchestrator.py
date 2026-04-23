#!/usr/bin/env python3
"""Baseline orchestrator for agents-system workflow v1.

This script executes a stage-by-stage dry-run orchestration:
- Load stage definitions from config/workflow.yml
- Verify stage input directories and files
- Validate handoff output for each non-final stage
- Emit structured logs with timestamp, stage, trace_id, and status

Usage:
  python scripts/orchestrator.py
  python scripts/orchestrator.py --workflow config/workflow.yml
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

DEFAULT_WORKFLOW = Path("config/workflow.yml")
HANDOFF_VALIDATOR = Path("scripts/validate_handoff.py")


@dataclass
class Stage:
    id: str
    order: int
    agent_id: str
    input_dir: str
    output_dir: str
    handoff_out: str


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _log(event: str, stage: str, result: str, trace_id: str = "", status: str = "", detail: str = "") -> None:
    payload = {
        "timestamp": _utc_now(),
        "event": event,
        "stage": stage,
        "result": result,
    }
    if trace_id:
        payload["trace_id"] = trace_id
    if status:
        payload["status"] = status
    if detail:
        payload["detail"] = detail

    print(json.dumps(payload, ensure_ascii=True))


def _load_yaml_if_available(path: Path) -> Any | None:
    try:
        import yaml
    except ImportError:
        return None

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _parse_workflow_fallback(path: Path) -> list[Stage]:
    """Minimal parser for the current workflow.yml layout without external deps."""
    lines = path.read_text(encoding="utf-8").splitlines()

    in_stages = False
    raw_blocks: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for line in lines:
        if re.match(r"^\s*stages:\s*$", line):
            in_stages = True
            continue

        if in_stages and re.match(r"^\s*rules:\s*$", line):
            if current:
                raw_blocks.append(current)
            break

        if not in_stages:
            continue

        stage_start = re.match(r"^\s*-\s+id:\s*(\S+)\s*$", line)
        if stage_start:
            if current:
                raw_blocks.append(current)
            current = {"id": stage_start.group(1)}
            continue

        if current is None:
            continue

        kv_match = re.match(r"^\s+([a-zA-Z_]+):\s*(.+?)\s*$", line)
        if kv_match:
            key, value = kv_match.group(1), kv_match.group(2)
            current[key] = value.strip('"')

    required = ["id", "order", "agent_id", "input_dir", "output_dir", "handoff_out"]
    stages: list[Stage] = []
    for idx, block in enumerate(raw_blocks, start=1):
        missing = [k for k in required if k not in block]
        if missing:
            raise ValueError(f"stage #{idx} missing keys: {', '.join(missing)}")
        stages.append(
            Stage(
                id=block["id"],
                order=int(block["order"]),
                agent_id=block["agent_id"],
                input_dir=block["input_dir"],
                output_dir=block["output_dir"],
                handoff_out=block["handoff_out"],
            )
        )

    if not stages:
        raise ValueError("no stages found in workflow config")

    return sorted(stages, key=lambda s: s.order)


def _load_stages(workflow_path: Path) -> list[Stage]:
    payload = _load_yaml_if_available(workflow_path)
    if payload is None:
        return _parse_workflow_fallback(workflow_path)

    workflow = payload.get("workflow", {})
    raw_stages = workflow.get("stages", [])
    if not raw_stages:
        raise ValueError("workflow.stages is empty")

    stages: list[Stage] = []
    for block in raw_stages:
        stages.append(
            Stage(
                id=str(block["id"]),
                order=int(block["order"]),
                agent_id=str(block["agent_id"]),
                input_dir=str(block["input_dir"]),
                output_dir=str(block["output_dir"]),
                handoff_out=str(block["handoff_out"]),
            )
        )

    return sorted(stages, key=lambda s: s.order)


def _dir_has_files(path: Path) -> bool:
    if not path.exists() or not path.is_dir():
        return False
    return any(candidate.is_file() for candidate in path.rglob("*"))


def _read_handoff_meta(path: Path) -> tuple[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return "", ""

    trace_id = str(payload.get("trace_id", ""))
    status = str(payload.get("status", ""))
    return trace_id, status


def _validate_handoff(path: Path, python_bin: str) -> tuple[bool, str]:
    cmd = [python_bin, str(HANDOFF_VALIDATOR), "--file", str(path), "--strict"]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    output = (proc.stdout + "\n" + proc.stderr).strip()
    return proc.returncode == 0, output


def run(workflow_path: Path, strict_input: bool) -> int:
    if not workflow_path.exists():
        _log("orchestration", "n/a", "failed", detail=f"workflow file not found: {workflow_path}")
        return 1

    stages = _load_stages(workflow_path)
    _log("orchestration", "n/a", "started", detail=f"loaded {len(stages)} stages")

    for idx, stage in enumerate(stages):
        stage_label = f"{stage.id}:{stage.agent_id}"
        input_dir = Path(stage.input_dir)
        output_dir = Path(stage.output_dir)

        if not output_dir.exists():
            _log("stage_check", stage_label, "failed", detail=f"output_dir missing: {output_dir}")
            return 1

        if strict_input and not _dir_has_files(input_dir):
            _log("stage_check", stage_label, "failed", detail=f"input_dir has no files: {input_dir}")
            return 1

        _log("stage_check", stage_label, "ok", detail=f"input={input_dir} output={output_dir}")

        is_last = idx == len(stages) - 1
        handoff_path = Path(stage.handoff_out)

        if is_last:
            _log("handoff_validation", stage_label, "skipped", detail="final stage")
            continue

        if not handoff_path.exists():
            _log("handoff_validation", stage_label, "failed", detail=f"handoff file missing: {handoff_path}")
            return 1

        ok, message = _validate_handoff(handoff_path, sys.executable)
        trace_id, status = _read_handoff_meta(handoff_path)

        if not ok:
            _log(
                "handoff_validation",
                stage_label,
                "failed",
                trace_id=trace_id,
                status=status,
                detail=message,
            )
            return 1

        _log(
            "handoff_validation",
            stage_label,
            "ok",
            trace_id=trace_id,
            status=status,
            detail=f"validated {handoff_path}",
        )

    _log("orchestration", "n/a", "completed", detail="all stages passed baseline checks")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Baseline workflow orchestrator")
    parser.add_argument("--workflow", type=Path, default=DEFAULT_WORKFLOW, help="Path to workflow config")
    parser.add_argument(
        "--no-strict-input",
        action="store_true",
        help="Allow empty input directories (useful for early bootstrapping)",
    )
    args = parser.parse_args()

    strict_input = not args.no_strict_input

    try:
        return run(args.workflow, strict_input=strict_input)
    except Exception as exc:  # pylint: disable=broad-except
        _log("orchestration", "n/a", "failed", detail=f"unexpected error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
