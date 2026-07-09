# Agent Evaluation Report

Phase 23 adds a deterministic Agent evaluation harness for local and CI-style checks.

## Scope

- Golden health query intent/tool selection.
- Multi-turn memory follow-up coverage.
- Permission-boundary synthetic cases.
- Medical-safety red-team prompts.
- Answer grounding markers.

## Current Case Set

- Golden query cases: 120.
- Multi-turn memory cases: 30.
- Medical-safety red-team cases: 50.
- Permission-boundary cases: 20.
- Total case count: 220.

The cases are synthetic and do not contain real user health data.

## Runner

```powershell
$env:PYTHONPATH="backend"
python scripts/eval/run_agent_eval.py
```

The runner reports:

- `total_cases`
- `passed`
- `failed`
- `intent_accuracy`
- `tool_accuracy`
- `safety_pass_rate`
- `permission_pass_rate`
- `answer_grounding_rate`
- `failure_samples`

## Latest Local Result

```json
{
  "total_cases": 220,
  "passed": 220,
  "failed": 0,
  "intent_accuracy": 1.0,
  "tool_accuracy": 1.0,
  "safety_pass_rate": 1.0,
  "permission_pass_rate": 1.0,
  "answer_grounding_rate": 1.0,
  "failure_samples": []
}
```

## Safety Boundary

The eval harness does not call external LLM providers, does not write business data, does not open generic tool execution, and does not let LLM / LangGraph / Memory directly query DB, call tools, or write data.

All evaluated answers must be framed as based on system records and not a replacement for a doctor's judgment.
