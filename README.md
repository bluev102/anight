# anight (Core-First Architecture)

anight is a language-agnostic, framework-agnostic multi-agent workflow system with an immutable specification core.

## Core-First Philosophy

The architecture is split into three explicit layers:
- `core/`: immutable specification (contracts, schemas, role definitions)
- `adapters/`: replaceable implementations (Python is one adapter)
- `workspace/`: runtime data produced by executions

If you want to implement anight in another language, `core/` is the source of truth you should read first.
See `core/PHILOSOPHY.md` for the rationale and governance model.

## Structure

```text
anight/
├── core/                # Immutable contracts and system definitions
├── adapters/
│   └── python/          # Python implementation of core contracts
└── workspace/           # Runtime artifacts (stages, memory)
```

## Quick Start (Python Adapter)

1. Validate declarative config:

```bash
python3 adapters/python/scripts/validate_config.py --all
```

2. Validate runtime handoff contracts:

```bash
python3 adapters/python/scripts/validate_handoff.py --dir workspace/stages --strict
```

3. Validate a single handoff file:

```bash
python3 adapters/python/scripts/validate_handoff.py --file workspace/stages/01_requirements/output/handoff_to_ba.json --strict
```

4. Run full preflight gate:

```bash
python3 adapters/python/scripts/preflight.py
```

## Optional Dependencies

For richer validation:

```bash
python3 -m pip install pyyaml jsonschema
```

Fallback structural validation is still available when dependencies are missing.

## Contribution Rule

Treat `core/` as read-only unless you are intentionally changing architecture philosophy/contracts.
All changes under `core/` require architectural review.
