#!/usr/bin/env python3
"""Validate handoff JSON files against Workflow Contract v1.

Usage:
  python scripts/validate_handoff.py --file stages/01_requirements/output/handoff_to_ba.json
  python scripts/validate_handoff.py --dir stages --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

SCHEMA_PATH = Path("config/schemas/handoff.schema.json")
WORKFLOW_PATH = Path("config/workflow.yml")
VALID_STATUS = {"draft", "submitted", "approved", "rejected", "revised"}
VALID_STAGES = {
    "01_requirements",
    "02_analysis",
    "03_design",
    "04_implementation",
    "05_testing",
    "06_delivery",
}
VALID_AGENTS = {"po", "ba", "designer", "developer", "tester", "pm"}


def _load_workflow_policy() -> dict[str, Any]:
    raw = WORKFLOW_PATH.read_text(encoding="utf-8").splitlines()
    policy: dict[str, Any] = {
        "allowed_statuses": [],
        "transitions": {},
    }

    in_state_machine = False
    in_allowed_statuses = False
    in_transitions = False
    current_status = ""

    for line in raw:
        stripped = line.strip()

        if stripped == "state_machine:":
            in_state_machine = True
            in_allowed_statuses = False
            in_transitions = False
            current_status = ""
            continue

        if not in_state_machine:
            continue

        if stripped == "allowed_statuses:":
            in_allowed_statuses = True
            in_transitions = False
            current_status = ""
            continue

        if stripped == "transitions:":
            in_allowed_statuses = False
            in_transitions = True
            current_status = ""
            continue

        if in_allowed_statuses and stripped.startswith("- "):
            policy["allowed_statuses"].append(stripped[2:].strip())
            continue

        if in_transitions:
            status_match = stripped[:-1] if stripped.endswith(":") else ""
            if status_match in VALID_STATUS:
                current_status = status_match
                policy["transitions"][current_status] = []
                continue

            if stripped.startswith("- ") and current_status:
                policy["transitions"][current_status].append(stripped[2:].strip())

    if not policy["allowed_statuses"]:
        policy["allowed_statuses"] = sorted(VALID_STATUS)

    return policy


def _load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _validate_manual(contract: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    required = [
        "contract_version",
        "trace_id",
        "stage_id",
        "from_agent",
        "to_agent",
        "created_at",
        "status",
        "review_required",
        "artifacts",
    ]

    for field in required:
        if field not in contract:
            errors.append(f"missing required field: {field}")

    if errors:
        return errors

    if not str(contract["contract_version"]).startswith("1."):
        errors.append("contract_version must start with '1.'")

    if contract["stage_id"] not in VALID_STAGES:
        errors.append("stage_id is invalid")

    if contract["from_agent"] not in VALID_AGENTS:
        errors.append("from_agent is invalid")

    if contract["to_agent"] not in VALID_AGENTS:
        errors.append("to_agent is invalid")

    if contract["status"] not in VALID_STATUS:
        errors.append("status is invalid")

    if not isinstance(contract["review_required"], bool):
        errors.append("review_required must be boolean")

    artifacts = contract.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("artifacts must be an object")
        return errors

    for key in ("input_refs", "output_refs"):
        if key not in artifacts:
            errors.append(f"artifacts.{key} is required")
        elif not isinstance(artifacts[key], list):
            errors.append(f"artifacts.{key} must be an array")

    output_refs = artifacts.get("output_refs", [])
    if isinstance(output_refs, list) and len(output_refs) < 1:
        errors.append("artifacts.output_refs must contain at least one item")

    if contract["review_required"] and "reviewer_agent" not in contract:
        errors.append("reviewer_agent is required when review_required=true")

    if contract["status"] in {"approved", "rejected", "revised"} and not contract["review_required"]:
        errors.append(f"status={contract['status']} requires review_required=true")

    if contract["status"] == "draft" and contract["review_required"]:
        errors.append("status=draft requires review_required=false")

    if contract["status"] == "rejected" and not contract.get("review_reason"):
        errors.append("review_reason is required when status=rejected")

    if contract["status"] == "revised" and not contract.get("review_reason"):
        errors.append("review_reason is required when status=revised")

    return errors


def _validate_state_machine(contract: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    allowed_statuses = set(policy.get("allowed_statuses", []))
    if contract.get("status") not in allowed_statuses:
        errors.append(f"status {contract.get('status')} is not allowed by workflow state machine")
        return errors

    if contract["status"] in {"approved", "rejected", "revised"} and not contract["review_required"]:
        errors.append(f"status={contract['status']} cannot be used when review_required=false")

    if contract["status"] == "draft" and contract["review_required"]:
        errors.append("draft handoffs must not require review")

    transitions = policy.get("transitions", {})
    if contract["status"] in transitions and not isinstance(transitions[contract["status"]], list):
        errors.append(f"state machine transition list for {contract['status']} must be an array")

    return errors


def _validate_with_jsonschema(contract: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return _validate_manual(contract)

    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for err in sorted(validator.iter_errors(contract), key=lambda e: e.path):
        path = ".".join(str(p) for p in err.path) or "root"
        errors.append(f"{path}: {err.message}")

    return errors


def _iter_handoff_files(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
        return

    for candidate in sorted(path.rglob("handoff_*.json")):
        if candidate.is_file():
            yield candidate


def _validate_file(file_path: Path, schema: dict[str, Any], policy: dict[str, Any], strict: bool) -> tuple[bool, list[str]]:
    try:
        payload = _load_json(file_path)
    except Exception as exc:  # pylint: disable=broad-except
        return False, [f"invalid JSON: {exc}"]

    if not isinstance(payload, dict):
        return False, ["top-level JSON value must be an object"]

    errors = _validate_with_jsonschema(payload, schema)
    errors.extend(_validate_state_machine(payload, policy))

    if strict:
        allowed_keys = {
            "contract_version",
            "trace_id",
            "stage_id",
            "from_agent",
            "to_agent",
            "created_at",
            "status",
            "review_required",
            "reviewer_agent",
            "review_reason",
            "rollback_to_stage",
            "artifacts",
            "extensions",
        }
        extra_keys = [k for k in payload.keys() if k not in allowed_keys]
        for key in sorted(extra_keys):
            errors.append(f"unexpected top-level field in strict mode: {key}")

    return len(errors) == 0, errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate handoff contracts")
    parser.add_argument("--file", type=Path, help="Validate a single handoff json file")
    parser.add_argument("--dir", type=Path, help="Validate all handoff_*.json files in a directory")
    parser.add_argument("--schema", type=Path, default=SCHEMA_PATH, help="Schema path")
    parser.add_argument("--strict", action="store_true", help="Disallow unknown top-level keys")
    args = parser.parse_args()

    if not args.file and not args.dir:
        parser.error("Provide --file or --dir")

    schema = _load_json(args.schema)
    policy = _load_workflow_policy()
    targets = list(_iter_handoff_files(args.file if args.file else args.dir))

    if not targets:
        print("No handoff files found.")
        return 1

    has_error = False
    for target in targets:
        ok, errors = _validate_file(target, schema, policy, args.strict)
        if ok:
            print(f"PASS {target}")
            continue

        has_error = True
        print(f"FAIL {target}")
        for err in errors:
            print(f"  - {err}")

    return 1 if has_error else 0


if __name__ == "__main__":
    sys.exit(main())
