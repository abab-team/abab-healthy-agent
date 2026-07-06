import {
  agentRun,
  family,
  members,
  pendingDrafts,
  reminders,
  safetyChecks,
  toolCalls
} from "@/constants/mockData";
import type {
  AgentRunDetail,
  AgentRunResponse,
  AgentSafetyCheckSummary,
  AgentToolCallSummary,
  AlertCreateInput,
  ApiResult,
  DraftStatus,
  MedicalEventDraftInput,
  SymptomDraftInput
} from "@/types/api";

function wait<T>(data: T, delay = 260): Promise<ApiResult<T>> {
  return new Promise((resolve) => {
    setTimeout(() => resolve({ ok: true, data }), delay);
  });
}

export const mockApi = {
  getCurrentUser() {
    return wait({ id: "me", name: "Gala", current_family_id: family.id });
  },

  getFamilyOverview() {
    return wait({ family, members, reminders });
  },

  getMemberDetail(id: string) {
    return wait(members.find((member) => member.id === id) ?? members[0]);
  },

  getDrafts() {
    return wait(pendingDrafts);
  },

  updateDraftStatus(id: string, status: DraftStatus) {
    return wait({ id, status });
  },

  getAgentBrief() {
    return wait(agentRun);
  },

  createSymptomDraftPreview(input: SymptomDraftInput) {
    return wait<AgentRunResponse>({
      generated_content: input.description.trim()
        ? "mock 已生成症状草稿预览；confirmation=false 不会写入。"
        : "请补充症状描述后再生成草稿预览。",
      status: "preview",
      trace_id: "run-symptom-draft-preview",
      workflow_type: "symptom_draft_create"
    });
  },

  createSymptomDraftConfirmed(input: SymptomDraftInput) {
    return wait<AgentRunResponse>({
      generated_content: "mock 已生成待确认症状草稿；真实提交需要 api mode。",
      status: "completed",
      trace_id: "run-symptom-draft-preview",
      workflow_type: "symptom_draft_create"
    });
  },

  createMedicalEventDraftPreview(input: MedicalEventDraftInput) {
    return wait<AgentRunResponse>({
      generated_content: input.summary.trim()
        ? "mock 已生成健康事件草稿预览；confirmation=false 不会写入。"
        : "请补充健康事项内容后再生成草稿预览。",
      status: "preview",
      trace_id: "run-medical-event-draft-preview",
      workflow_type: "medical_event_draft_create"
    });
  },

  createMedicalEventDraftConfirmed(_input: MedicalEventDraftInput) {
    return wait<AgentRunResponse>({
      generated_content: "mock 已生成待确认健康事件草稿；真实提交需要 api mode。",
      status: "completed",
      trace_id: "run-medical-event-draft-preview",
      workflow_type: "medical_event_draft_create"
    });
  },

  createAlertPreview(input: AlertCreateInput) {
    return wait<AgentRunResponse>({
      generated_content: input.title.trim()
        ? "mock 已生成普通健康提醒预览；confirmation=false 不会写入。"
        : "请填写提醒标题后再生成预览。",
      status: "preview",
      trace_id: "run-alert-create-preview",
      workflow_type: "alert_create"
    });
  },

  createAlertConfirmed(_input: AlertCreateInput) {
    return wait<AgentRunResponse>({
      generated_content: "mock 已创建普通健康提醒；真实提交需要 api mode。",
      status: "completed",
      trace_id: "run-alert-create-preview",
      workflow_type: "alert_create"
    });
  },

  getAgentRun(id: string) {
    return wait<AgentRunDetail>({
      generated_content: agentRun.generatedContent,
      safety_checks: safetyChecks as AgentSafetyCheckSummary[],
      status: "completed",
      tool_calls: toolCalls as AgentToolCallSummary[],
      trace_id: id,
      workflow_type: "daily_health_brief"
    });
  }
};
