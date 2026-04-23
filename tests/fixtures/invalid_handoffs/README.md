# Invalid Handoff Fixtures

These fixtures are intentionally invalid and are meant to exercise failure paths in `scripts/validate_handoff.py`.

## Cases
- `missing_trace_id.json`
  - Expected failure: required field `trace_id` is missing.
- `invalid_status_enum.json`
  - Expected failure: `status` value is not in the allowed enum.
- `missing_reviewer_when_review_required.json`
  - Expected failure: `review_required=true` without `reviewer_agent`.
- `approved_without_review.json`
  - Expected failure: state-machine rule rejects `status=approved` when `review_required=false`.
- `wrong_artifacts_type.json`
  - Expected failure: `artifacts.output_refs` is not an array.

## Validation Command

```bash
python3 scripts/validate_handoff.py --file tests/fixtures/invalid_handoffs/<fixture>.json --strict
```

Each file should fail validation with a specific error message.
