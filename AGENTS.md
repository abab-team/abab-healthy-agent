# AGENTS.md

This repository is developed by Codex agents under the constraints below. These instructions are mandatory for all future implementation tasks.

## Source Of Truth

- Strictly follow `CODEX_IMPLEMENTATION_PLAN.md`.
- Use the project architecture documents as implementation constraints:
  - `家庭健康Agent_项目架构设计_v1.0.md`
  - `docs/architecture/CODEX_IMPLEMENTATION_PLAN_v1.0.md`
  - `docs/architecture/家庭健康Agent_项目架构设计_v1.0.md`
- If an implementation request conflicts with the plan or architecture documents, stop and report the conflict before making code changes.

## Scope Control

- Do not restructure the repository directories.
- Do not implement work from later phases before the current approved phase.
- Do not create unrelated scaffolding, services, models, or integrations outside the requested task.
- For each task, make the smallest change that satisfies the current phase and request.

## Layering Rules

- Do not put business logic in the API layer.
- Keep API handlers thin: request validation, authentication context extraction, service invocation, and response mapping only.
- Put business rules in the appropriate service/domain layer defined by the architecture.
- Agents must not access the database directly.
- Database access must go through the approved repository/data-access layer.

## Identity And Authorization

- LLM output must never decide or override `current_user_id`, `family_id`, or `target_user_id`.
- These identifiers must come from authenticated application context and authorization checks.
- Do not bypass the permission system.
- Every family/member/target-user operation must enforce the architecture-defined authorization boundary.

## AI Draft Safety

- Do not persist unconfirmed AI drafts as final records.
- AI-generated content must remain draft/proposal content until explicitly confirmed by the user through the approved workflow.
- Persisted AI content must retain the required auditability and confirmation state defined by the implementation plan.

## Medical Safety Boundary

- Do not implement medical diagnosis.
- Do not implement prescription recommendations.
- Do not implement medication dosage recommendations.
- The product may support health record organization, reminders, summaries, and user-facing safety disclaimers only within the approved project scope.

## Task Completion Requirements

After every task:

- Run the relevant checks or tests for the files changed.
- If any test or check fails, fix the failure before ending the task.
- Report the modified files.
- Report the checks/tests run and their results.
- Report remaining work or explicitly state that there is none for the current task.

## Current Task Guardrail

For the initial task that creates this file:

- Only create `AGENTS.md`.
- Do not write business code.
- Do not initialize FastAPI.
- Do not create database models.
