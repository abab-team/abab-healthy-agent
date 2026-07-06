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
  AgentRunRequest,
  AgentRunResponse,
  AgentSafetyCheckSummary,
  AgentToolCallSummary,
  Alert,
  ApiResult,
  DraftStatus,
  HealthRecordDraft
} from "@/types/api";

function wait<T>(data: T, delay = 380): Promise<ApiResult<T>> {
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

  createSymptomDraftPreview(input: { target_user_id: string; description: string }) {
    return wait<HealthRecordDraft>({
      id: "draft-preview-symptom",
      target_user_id: input.target_user_id,
      title: "症状草稿预览",
      summary: input.description.trim() || "请补充症状描述后再生成草稿预览。",
      status: "pending"
    });
  },

  createSymptomDraftConfirmed(input: { target_user_id: string; description: string }) {
    return wait<AgentRunResponse>({
      trace_id: "run-symptom-draft-preview",
      status: "completed",
      workflow_type: "symptom_draft_create",
      generated_content: `已生成待确认症状草稿：${input.description.trim()}`
    });
  },

  createAlertPreview(input: { target_user_id: string; title: string; reminder_type: string; scheduled_at: string }) {
    return wait<Alert>({
      id: "alert-preview",
      target_user_id: input.target_user_id,
      title: input.title.trim() || "请填写提醒标题",
      reminder_type: input.reminder_type,
      scheduled_at: input.scheduled_at,
      status: "preview"
    });
  },

  createAlertConfirmed(input: { target_user_id: string; title: string; reminder_type: string; scheduled_at: string }) {
    return wait<AgentRunResponse>({
      trace_id: "run-alert-create-preview",
      status: "completed",
      workflow_type: "alert_create",
      generated_content: `已创建普通健康提醒：${input.title.trim()} · ${input.scheduled_at}`
    });
  },

  runAgentWorkflow(request: AgentRunRequest) {
    return wait<AgentRunResponse>({
      trace_id: request.workflow_type === "daily_health_brief" ? agentRun.id : "run-mock-preview",
      status: request.confirmation === false ? "preview" : "completed",
      workflow_type: request.workflow_type,
      generated_content: request.user_message || "根据系统内记录生成的 mock 结果。"
    });
  },

  getAgentRun(id: string) {
    return wait<AgentRunDetail>({
      trace_id: id,
      status: "completed",
      workflow_type: "daily_health_brief",
      generated_content: agentRun.generatedContent,
      tool_calls: toolCalls as AgentToolCallSummary[],
      safety_checks: safetyChecks as AgentSafetyCheckSummary[]
    });
  }
};
