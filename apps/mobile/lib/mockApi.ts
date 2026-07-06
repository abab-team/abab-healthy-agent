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

  createSymptomDraftPreview(input: { target_user_id: string; description: string }) {
    return wait<HealthRecordDraft>({
      id: "draft-preview-symptom",
      status: "pending",
      summary: input.description.trim() || "请补充症状描述后再生成草稿预览。",
      target_user_id: input.target_user_id,
      title: "症状草稿预览"
    });
  },

  createSymptomDraftConfirmed(input: { target_user_id: string; description: string }) {
    return wait<AgentRunResponse>({
      generated_content: `已生成待确认症状草稿：${input.description.trim()}`,
      status: "completed",
      trace_id: "run-symptom-draft-preview",
      workflow_type: "symptom_draft_create"
    });
  },

  createAlertPreview(input: { target_user_id: string; title: string; reminder_type: string; scheduled_at: string }) {
    return wait<Alert>({
      id: "alert-preview",
      reminder_type: input.reminder_type,
      scheduled_at: input.scheduled_at,
      status: "preview",
      target_user_id: input.target_user_id,
      title: input.title.trim() || "请填写提醒标题"
    });
  },

  createAlertConfirmed(input: { target_user_id: string; title: string; reminder_type: string; scheduled_at: string }) {
    return wait<AgentRunResponse>({
      generated_content: `已创建普通健康提醒：${input.title.trim()} · ${input.scheduled_at}`,
      status: "completed",
      trace_id: "run-alert-create-preview",
      workflow_type: "alert_create"
    });
  },

  runAgentWorkflow(request: AgentRunRequest) {
    return wait<AgentRunResponse>({
      generated_content: request.user_message || "根据系统内记录生成的 mock 结果。",
      status: request.confirmation === false ? "preview" : "completed",
      trace_id: request.workflow_type === "daily_health_brief" ? agentRun.id : "run-mock-preview",
      workflow_type: request.workflow_type
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
