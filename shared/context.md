# Shared Context

## Working Rules
- The system is language-agnostic and framework-agnostic.
- Each agent owns its own instructions and output artifacts.
- Agents communicate using handoff contract JSON files only.
- Output from stage N is immutable for stage N+1; downstream agents can reference, not rewrite.

## Contract Rules
- Use `config/schemas/handoff.schema.json` as the handoff source of truth.
- `status` lifecycle for v1: `draft -> submitted -> approved/rejected -> revised`.
- Use `rollback_to_stage` as a marker only in v1 (no runtime rollback engine yet).

## Quality Rules
- Every rejected handoff must include `review_reason`.
- Every handoff must include at least one `output_refs` item.
- Custom metadata must be placed under `extensions`.
