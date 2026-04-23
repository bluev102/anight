# AGENT SYSTEM CONFIGURATION
> This file is automatically read by all Kilo agents. Do not remove.

## 🏛️ System Identity
This is the `anight` multi-agent workflow system.
Core specification: immutable, language-agnostic contracts in `core/` directory.

## 🎯 Agent Role Detection
When you enter this repository:
1.  Check which agent persona you were invoked as
2.  Locate your role definition in `core/config/agents.yml`
3.  Read your full persona instructions at `core/agents/[your-folder]/persona.md`

## 📋 Standard Workflow for ALL Agents
When you are active:

1.  **Bootstrap Check**:
    ```bash
    python adapters/python/scripts/preflight.py
    ```
    ✅ Always run this first. Fix any failures before starting work.

2.  **Locate Your Work**:
    - Your input directory: `workspace/stages/[your-stage]/input/`
    - Your output directory: `workspace/stages/[your-stage]/output/`

3.  **Do Your Work**:
    - Read all files in your input directory
    - Perform the tasks defined in your persona
    - Write all output artifacts to your output directory
    - Never modify files outside your stage directory

4.  **Handoff Preparation**:
    - Create a valid handoff contract to the next agent
    - Follow schema at `core/schemas/handoff.schema.json`
    - Set appropriate status and review requirements

5.  **Validation**:
    ```bash
    python adapters/python/scripts/validate_handoff.py --file [your-handoff-file] --strict
    ```
    ✅ Only proceed if validation passes.

6.  **Completion**:
    - Commit only files in your output directory
    - Do NOT commit handoff files unless explicitly required
    - Do NOT modify files in `core/` directory

## ⚠️ Hard Rules for ALL Agents
1.  ❌ NEVER modify anything under `core/` directory
2.  ❌ NEVER modify files belonging to another agent's stage
3.  ❌ NEVER skip validation steps
4.  ❌ NEVER commit handoff files to git
5.  ✅ ALWAYS run preflight before starting any work
6.  ✅ ALWAYS follow the exact schema for handoff contracts

## 📚 Reference Documentation
- Workflow definition: `core/config/workflow.yml`
- Agent definitions: `core/config/agents.yml`
- Handoff schema: `core/schemas/handoff.schema.json`
- Core philosophy: `core/PHILOSOPHY.md`
