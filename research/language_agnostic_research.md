# Language-Agnostic Architecture Research (V1)

## 1. Purpose
This document explains why the current agents-system architecture is language-agnostic and framework-agnostic, what trade-offs this decision introduces in V1, and which design directions should be prioritized for V2.

## 2. Rationale

### 2.1 Config-as-Contract Instead of Framework-as-Core
The system is centered on declarative files in `config/` and `config/schemas/`.
- Workflow behavior is defined in `config/workflow.yml`.
- Agent responsibilities are defined in `config/agents.yml`.
- Data exchange contracts are enforced by JSON Schema.

Why this supports language-agnostic design:
- Any runtime (Python, Node.js, Go, Rust, Java) can parse YAML/JSON.
- Validation logic can be reproduced in any language with equivalent schema tooling.
- Core behavior is described by data contracts, not tied to one SDK or framework.

### 2.2 Folder-Based Handoff as Universal Interface
Agents exchange artifacts through files under `stages/*/input` and `stages/*/output`.
- Handoff contract files provide explicit metadata.
- Artifact references make data flow auditable and deterministic.

Why this supports framework-agnostic design:
- File I/O is the most universal integration surface.
- No dependency on message queues, proprietary agent runtimes, or cloud-specific services in V1.
- Works in local development, CI pipelines, and containerized environments.

### 2.3 Per-Agent Instruction Ownership
Each agent has isolated instruction files (`persona.md`, `skills.yml`) and memory directories.
- Behavior specialization is local to each agent folder.
- Global rules remain minimal and interoperability-focused.

Why this supports scalable architecture evolution:
- New roles can be added without refactoring global orchestration logic.
- Agent-specific updates avoid broad regressions across the whole system.

### 2.4 Schema-Driven Validation as Safety Layer
Validation scripts enforce consistency before orchestration advances.
- `scripts/validate_handoff.py` validates handoff shape and critical rules.
- `scripts/validate_config.py` validates workflow and agent registry structure.

Why this matters:
- Prevents silent contract drift.
- Creates a portable quality gate independent of runtime implementation language.

## 3. Trade-Off Analysis

### 3.1 Strengths
1. Portability
- Core assets are readable and executable across language ecosystems.

2. Auditability
- Every transition leaves explicit artifacts and metadata.

3. Determinism
- Sequential stage model and explicit handoffs reduce hidden side effects.

4. Incremental Adoption
- Teams can start simple (file-based orchestration) and evolve later.

### 3.2 Costs and Constraints
1. Limited Runtime Sophistication in V1
- No native support yet for dynamic routing, parallel branch execution, or event-driven scheduling.

2. Operational Overhead
- File lifecycle management can become noisy at scale.
- Requires naming and versioning discipline.

3. Validation Depth Gap
- Structural validation is strong; semantic and policy validation still partial.

4. Potential Config Drift
- As workflow complexity grows, keeping config, schemas, and scripts aligned requires stricter governance.

## 4. Why V1 Scope Is Correct
V1 intentionally prioritizes:
- Contract clarity
- Baseline orchestration reliability
- Reproducible validation

This avoids premature optimization and framework lock-in. It establishes a stable control plane before introducing advanced runtime complexity.

## 5. V2 Directions

### 5.1 Validation Depth and Policy Engine
- Add explicit state transition matrix validation.
- Add cross-file consistency checks:
  - stage-to-agent mapping integrity
  - handoff direction correctness
  - artifact reference existence and ownership policy
- Add policy modules for reject/revise/rollback markers.

### 5.2 Preflight and CI Integration
- Introduce a one-command preflight script:
  - validate schemas
  - validate configs
  - validate handoffs
  - run orchestrator smoke pass
- Make preflight a required CI gate.

### 5.3 Observability Standardization
- Standardize structured logs around:
  - timestamp
  - trace_id
  - stage
  - status
  - result
- Add run summary report for each orchestration execution.

### 5.4 Contract Versioning and Migration
- Define compatibility policy for `contract_version`.
- Add migration notes and tooling support for 1.x to 2.x transitions.

### 5.5 Extensibility Without Lock-In
- Keep core contracts runtime-neutral.
- Add adapters for optional execution backends while preserving the same contract interface.

## 6. Recommended V2 Milestones
1. V2.0-alpha
- State transition validation
- Invalid fixture suite
- Preflight script

2. V2.0-beta
- CI gate
- richer orchestration report
- migration documentation

3. V2.0
- Stable policy engine for review and rollback markers
- optional backend adapters with identical contract semantics

## 7. Decision Summary
- Keep config and schemas as source of truth.
- Keep file-based handoff as baseline interoperability layer.
- Add deeper semantic validation before expanding runtime complexity.
- Treat advanced orchestration as additive capability, not a replacement of the contract-first model.
