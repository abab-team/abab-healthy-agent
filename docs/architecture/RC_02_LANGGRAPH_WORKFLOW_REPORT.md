# RC 02 Agent LangGraph Workflow Report

## Scope

RC 02 migrates Agent single-run workflow orchestration toward real LangGraph
`StateGraph.compile()` runners while preserving existing service, ToolExecutor,
permission, SafetyPolicy, Critic, Memory, and fallback boundaries.

This release does not add a generic tool execution API and does not allow the
frontend or an LLM to provide `tool_name` or `input_data`.

## Workflow Matrix

| AgentWorkflowName | Current file | Status before RC 02 | RC 02 handling |
| --- | --- | --- | --- |
| `chat_workflow` | `backend/app/agent/workflows/chat_workflow.py` | Full workflow with previous adapter-style graph | Migrated to `ChatHealthQueryGraph` with real `StateGraph.compile()` |
| `free_text_record_workflow` | `backend/app/agent/workflows/free_text_record_workflow.py` | Controlled draft workflow | Added `FreeTextRecordGraph` wrapper, still only via ToolExecutor |
| `doctor_visit_summary_workflow` | `backend/app/agent/workflows/doctor_visit_summary_workflow.py` | Full readonly multi-tool workflow | Added `DoctorVisitSummaryGraph` |
| `document_extract_workflow` | `backend/app/agent/workflows/document_extract_workflow.py` | Placeholder | Added metadata-only MVP workflow and `DocumentExtractGraph` |
| `daily_report_workflow` | `backend/app/agent/workflows/daily_report_workflow.py` | Placeholder | Added generated daily report preview and `DailyReportGraph` |
| `health_knowledge_qa_workflow` | `backend/app/agent/workflows/health_knowledge_qa_workflow.py` | Placeholder | Added internal-safe-context MVP and `HealthKnowledgeQAGraph` |
| `symptom_draft_create_workflow` | `backend/app/agent/workflows/symptom_draft_create.py` | Controlled draft workflow | Added `SymptomDraftGraph` wrapper |
| `medical_event_draft_create_workflow` | `backend/app/agent/workflows/medical_event_draft_create.py` | Controlled draft workflow | Added `MedicalEventDraftGraph` wrapper |
| `alert_create_workflow` | `backend/app/agent/workflows/alert_create.py` | Controlled reminder workflow | Added `AlertCreateGraph` wrapper |
| `daily_health_brief` | `backend/app/agent/workflows/daily_health_brief.py` | Full readonly brief workflow | Added `DailyHealthBriefGraph` |

## Graph Nodes

- `ChatHealthQueryGraph`: `load_memory`, `input_safety`, `rule_planner_rule_parse`,
  `llm_planner_optional`, `validate_plan`, `resolve_member`, `permission_gate`,
  `tool_executor`, `answer_composer`, `critic_review`, `memory_writer`, `trace_record`.
- `FreeTextRecordGraph`: `input_safety`, `resolve_member`, `permission_gate`,
  `draft_tool_executor`, `draft_response_builder`, `critic`, `trace_record`.
- `DoctorVisitSummaryGraph`: `input_safety`, `options_parser`, `resolve_member`,
  `permission_gate`, `blood_pressure_tool`, `symptoms_tool`, `events_tool`,
  `documents_tool`, `alerts_tool`, `summary_builder`, `critic`, `trace_record`.
- `DocumentExtractGraph`: `input_safety`, `document_context_loader`,
  `document_permission_gate`, `ocr_or_text_extract`, `document_summary_builder`,
  `medical_event_draft_builder`, `critic`, `trace_record`.
- `DailyReportGraph`: `load_member_context`, `metrics_tool`,
  `blood_pressure_tool`, `symptoms_tool`, `alerts_tool`, `events_tool`,
  `brief_builder`, `critic`, `optional_store_report`, `trace_record`.
- `HealthKnowledgeQAGraph`: `input_safety`, `query_classifier`,
  `internal_rag_retrieval`, `answer_builder`, `critic`, `trace_record`.
- `AlertCreateGraph`, `SymptomDraftGraph`, `MedicalEventDraftGraph` use the
  shared draft-tool graph node chain and remain confirmation-gated.
- `DailyHealthBriefGraph`: `load_member_context`, `metrics_tool`,
  `blood_pressure_tool`, `symptoms_tool`, `alerts_tool`, `events_tool`,
  `brief_builder`, `critic`, `optional_store_report`, `trace_record`.

## Safety Boundary

- LangGraph nodes orchestrate existing services and tools; they do not directly
  query health business tables.
- Tool execution remains inside `AgentToolExecutor`.
- Family data access remains subject to existing family permission checks.
- LLM planner output remains structured and validated by backend code.
- Graph state safe summaries reject raw prompts, raw LLM responses, raw text,
  raw OCR, file paths, SQL, tokens, passwords, API keys, private keys,
  `tool_name`, `input_data`, and LLM-provided user/family identifiers.
- Document extraction MVP returns metadata-only preview and pending draft
  language. It does not return raw OCR text or local file paths.
- Daily report MVP returns a generated preview. It does not store a formal
  daily report unless a separately reviewed storage path is added later.
- Health knowledge QA uses internal safe context only and does not connect to
  an external medical knowledge base.

## Configuration

All graph execution remains disabled by default:

- `LANGGRAPH_ENABLED=false`
- Per-workflow graph flags default to `false`
- `LANGGRAPH_STRICT_MODE=false`

When a graph is disabled, the previous workflow implementation is used. When a
graph fails and strict mode is disabled, the dispatcher falls back to the
previous workflow implementation.

## Not Added

- No migration or database model.
- No new generic tool execution endpoint.
- No frontend `tool_name` / `input_data`.
- No external medical knowledge base.
- No real OCR provider.
- No diagnosis, prescription, dosage, stop-medication guidance, or
  normal/abnormal medical judgment.
