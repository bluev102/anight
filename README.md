# Agents System (V1)

A language-agnostic and framework-agnostic multi-agent workflow system based on declarative config and folder-based handoff contracts.

## Architecture Summary
- Pipeline mode: sequential (6 stages)
- Communication pattern: file handoff (`handoff_*.json`)
- Source of truth: `config/*.yml` + `config/schemas/*.json`
- Validation strategy:
  - Handoff contract validation: `scripts/validate_handoff.py`
  - Config validation (agents/workflow): `scripts/validate_config.py`

## Folder Layout
- `system.yml`: system manifest
- `config/`: agent/workflow registries and schemas
- `agents/`: per-agent instructions (`persona.md`, `skills.yml`, `memory/`)
- `shared/`: shared context, handoff template, shared schema copy
- `workflows/`: executable workflow description
- `stages/`: pipeline inputs/outputs and handoff chain
- `scripts/`: validation and orchestration scripts
- `research/`: architecture rationale and research notes

## Quick Start
1. Validate config files:

```bash
python3 scripts/validate_config.py --all
```

2. Validate handoff contracts (strict mode):

```bash
python3 scripts/validate_handoff.py --dir stages --strict
```

3. Validate a single handoff file:

```bash
python3 scripts/validate_handoff.py --file stages/01_requirements/output/handoff_to_ba.json --strict
```

4. Run the full preflight gate:

```bash
python3 scripts/preflight.py
```

5. CI gate:

- `.github/workflows/ci.yml` runs the same preflight gate on push, pull request, and manual dispatch.
- Treat preflight success as the merge requirement for V1.

## Optional Python Dependencies
The project supports optional richer validation if these packages are available:

```bash
python3 -m pip install pyyaml jsonschema
```

If dependencies are missing, config validation still runs in fallback structural mode.

## Workflow Contract Rules (V1)
- Required handoff fields include: `contract_version`, `trace_id`, `stage_id`, `from_agent`, `to_agent`, `created_at`, `status`, `review_required`, `artifacts`.
- `review_required=true` requires `reviewer_agent`.
- `status=rejected` requires `review_reason`.
- `rollback_to_stage` is a marker field only in V1.

## Roadmap Pointer
Execution roadmap is documented in `plan-v1.md`.

## Current Status
- A1 implemented: documentation baseline available in this file.
- A2 implemented:
  - `config/schemas/agent.schema.json`
  - `scripts/validate_config.py`
  - existing workflow/handoff schema validation chain remains active.
- A3 implemented:
  - `scripts/orchestrator.py`
- B1/B2 implemented:
  - state transition validation
  - invalid fixture suite under `tests/fixtures/invalid_handoffs/`
- B3 implemented:
  - `scripts/preflight.py`
- CI gate implemented:
  - `.github/workflows/ci.yml`
