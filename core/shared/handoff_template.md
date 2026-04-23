---
contract_version: "1.0"
trace_id: "replace-with-trace-id"
stage_id: "01_requirements"
from_agent: "po"
to_agent: "ba"
created_at: "2026-04-23T00:00:00Z"
status: "submitted"
review_required: true
reviewer_agent: "ba"
review_reason: ""
rollback_to_stage: ""
---

# Summary
One-paragraph summary of the handoff decision.

# Input References
- workspace/stages/01_requirements/input/brief.md

# Output References
- workspace/stages/01_requirements/output/product_vision.md
- workspace/stages/01_requirements/output/user_stories.md
- workspace/stages/01_requirements/output/backlog_prioritized.md

# Notes
- Keep additions in `extensions` when serializing to JSON.
- Do not modify previous stage outputs directly.
