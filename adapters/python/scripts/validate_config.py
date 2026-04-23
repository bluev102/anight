#!/usr/bin/env python3
"""Validate config files for agents-system.

Primary mode (preferred): YAML + JSON Schema validation when optional deps are installed.
Fallback mode: structural checks without external packages.

Usage:
    python adapters/python/scripts/validate_config.py --all
    python adapters/python/scripts/validate_config.py --agents
    python adapters/python/scripts/validate_config.py --workflow
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[2]
AGENTS_YML = REPO_ROOT / "core/config/agents.yml"
WORKFLOW_YML = REPO_ROOT / "core/config/workflow.yml"
AGENT_SCHEMA = REPO_ROOT / "core/schemas/agent.schema.json"
WORKFLOW_SCHEMA = REPO_ROOT / "core/schemas/workflow.schema.json"


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_yaml_if_available(path: Path) -> Any | None:
    try:
        import yaml
    except ImportError:
        return None

    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _validate_schema(payload: Any, schema: dict[str, Any]) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema package is not installed"]

    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(payload), key=lambda e: e.path):
        path = ".".join(str(p) for p in err.path) or "root"
        errors.append(f"{path}: {err.message}")
    return errors


def _validate_agents_fallback(raw: str) -> list[str]:
    errors: list[str] = []
    if not re.search(r"^agents:\s*$", raw, re.MULTILINE):
        errors.append("missing top-level key: agents")

    blocks = re.split(r"\n\s*-\s+id:\s*", raw)
    if len(blocks) <= 1:
        errors.append("no agent entry found (expected '- id: ...')")
        return errors

    required_keys = [
        "name:",
        "folder:",
        "stage:",
        "persona_file:",
        "skills_file:",
        "input_dir:",
        "output_dir:",
        "description:",
    ]

    for idx, block in enumerate(blocks[1:], start=1):
        for key in required_keys:
            if key not in block:
                errors.append(f"agent #{idx}: missing key {key[:-1]}")

    return errors


def _validate_workflow_fallback(raw: str) -> list[str]:
    errors: list[str] = []

    required_top = [
        "workflow:",
        "id:",
        "contract_version:",
        "mode:",
        "stages:",
        "rules:",
        "handoff:",
        "review_gate:",
        "rollback:",
    ]
    for key in required_top:
        if key not in raw:
            errors.append(f"missing required workflow key fragment: {key[:-1]}")

    stage_blocks = re.split(r"\n\s*-\s+id:\s*", raw)
    if len(stage_blocks) <= 1:
        errors.append("no workflow stage entry found")
    else:
        required_stage_keys = ["order:", "agent_id:", "input_dir:", "output_dir:", "handoff_out:"]
        for idx, block in enumerate(stage_blocks[1:], start=1):
            for key in required_stage_keys:
                if key not in block:
                    errors.append(f"workflow stage #{idx}: missing key {key[:-1]}")

    return errors


def _validate_agents() -> tuple[bool, list[str], str]:
    raw = _read_text(AGENTS_YML)

    payload = _load_yaml_if_available(AGENTS_YML)
    if payload is None:
        errors = _validate_agents_fallback(raw)
        return len(errors) == 0, errors, "fallback"

    schema = _load_json(AGENT_SCHEMA)
    errors = _validate_schema(payload, schema)
    if errors == ["jsonschema package is not installed"]:
        fallback = _validate_agents_fallback(raw)
        return len(fallback) == 0, fallback, "fallback"

    return len(errors) == 0, errors, "schema"


def _validate_workflow() -> tuple[bool, list[str], str]:
    raw = _read_text(WORKFLOW_YML)

    payload = _load_yaml_if_available(WORKFLOW_YML)
    if payload is None:
        errors = _validate_workflow_fallback(raw)
        return len(errors) == 0, errors, "fallback"

    schema = _load_json(WORKFLOW_SCHEMA)
    errors = _validate_schema(payload, schema)
    if errors == ["jsonschema package is not installed"]:
        fallback = _validate_workflow_fallback(raw)
        return len(fallback) == 0, fallback, "fallback"

    return len(errors) == 0, errors, "schema"


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate agents/workflow config files")
    parser.add_argument("--all", action="store_true", help="Validate both agents and workflow")
    parser.add_argument("--agents", action="store_true", help="Validate core/config/agents.yml")
    parser.add_argument("--workflow", action="store_true", help="Validate core/config/workflow.yml")
    args = parser.parse_args()

    run_agents = args.all or args.agents
    run_workflow = args.all or args.workflow

    if not run_agents and not run_workflow:
        parser.error("Use --all, --agents, or --workflow")

    has_error = False

    if run_agents:
        ok, errors, mode = _validate_agents()
        if ok:
            print(f"PASS {AGENTS_YML} ({mode})")
        else:
            has_error = True
            print(f"FAIL {AGENTS_YML} ({mode})")
            for err in errors:
                print(f"  - {err}")

    if run_workflow:
        ok, errors, mode = _validate_workflow()
        if ok:
            print(f"PASS {WORKFLOW_YML} ({mode})")
        else:
            has_error = True
            print(f"FAIL {WORKFLOW_YML} ({mode})")
            for err in errors:
                print(f"  - {err}")

    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
