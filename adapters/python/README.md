# Python Adapter

This directory contains the Python implementation adapter for anight.
It is not part of the immutable system definition.

Before contributing here, read `core/` first:
- `core/PHILOSOPHY.md`
- `core/manifest.yml`
- `core/config/agents.yml`
- `core/config/workflow.yml`
- `core/schemas/agent.schema.json`
- `core/schemas/workflow.schema.json`
- `core/schemas/handoff.schema.json`

## What This Adapter Does
- Validates declarative contracts from `core/`
- Validates runtime handoff files from `workspace/stages/`
- Runs baseline orchestration smoke checks

## Scripts
- `scripts/validate_config.py`
- `scripts/validate_handoff.py`
- `scripts/orchestrator.py`
- `scripts/preflight.py`
