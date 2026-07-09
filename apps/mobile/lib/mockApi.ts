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
  ArchiveTrends,
  ApiResult,
  DraftStatus,
  ImportPreviewResult,
  ImportPreviewRow,
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
      generated_content: "演示模式已生成待确认症状草稿；真实提交需要后端模式。",
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
      generated_content: "演示模式已生成待确认健康事件草稿；真实提交需要后端模式。",
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
      generated_content: "演示模式已创建普通健康提醒；真实提交需要后端模式。",
      status: "completed",
      trace_id: "run-alert-create-preview",
      workflow_type: "alert_create"
    });
  },

  getArchiveTrends() {
    return wait<ArchiveTrends>({
      days: 90,
      disclaimer: "基于系统内记录整理，不替代医生判断。",
      generated_from: "demo_records",
      series: [
        {
          count: 4,
          data_quality: "demo",
          label: "睡眠",
          metric_type: "sleep_duration",
          points: [
            { measured_at: "2026-07-01T22:30:00Z", unit: "hours", value: 6.5 },
            { measured_at: "2026-07-02T22:40:00Z", unit: "hours", value: 7 },
            { measured_at: "2026-07-03T22:50:00Z", unit: "hours", value: 6.8 },
            { measured_at: "2026-07-04T22:45:00Z", unit: "hours", value: 7.2 }
          ],
          summary: "系统内共有 4 条睡眠记录，仅作长期整理。",
          unit: "hours"
        },
        {
          count: 4,
          data_quality: "demo",
          label: "步数",
          metric_type: "steps",
          points: [
            { measured_at: "2026-07-01T20:00:00Z", unit: "steps", value: 5200 },
            { measured_at: "2026-07-02T20:00:00Z", unit: "steps", value: 6400 },
            { measured_at: "2026-07-03T20:00:00Z", unit: "steps", value: 7000 },
            { measured_at: "2026-07-04T20:00:00Z", unit: "steps", value: 6100 }
          ],
          summary: "系统内共有 4 条步数记录，仅作数据归档。",
          unit: "steps"
        },
        {
          count: 2,
          data_quality: "demo",
          label: "体重",
          metric_type: "weight",
          points: [
            { measured_at: "2026-07-01T08:00:00Z", unit: "kg", value: 62.5 },
            { measured_at: "2026-07-04T08:00:00Z", unit: "kg", value: 62.2 }
          ],
          summary: "系统内共有 2 条体重记录，不进行医学判断。",
          unit: "kg"
        },
        {
          count: 2,
          data_quality: "demo",
          label: "血压",
          metric_type: "blood_pressure",
          points: [
            { diastolic: 78, measured_at: "2026-07-01T07:30:00Z", pulse: 70, systolic: 120 },
            { diastolic: 76, measured_at: "2026-07-04T07:30:00Z", pulse: 72, systolic: 118 }
          ],
          summary: "系统内共有 2 条血压记录，本页不判断健康状态。"
        }
      ]
    });
  },

  previewHealthDataImport(rows: ImportPreviewRow[]) {
    return wait<ImportPreviewResult>({
      disclaimer: "预览不会写入正式健康数据。",
      errors: rows.length > 0 ? [] : [{ field: "rows", message: "请先准备导入行" }],
      file_name: "mobile-health-data-demo.csv",
      import_type: "csv",
      invalid_count: rows.length > 0 ? 0 : 1,
      preview_rows: rows,
      total_count: rows.length,
      valid_count: rows.length,
      will_write: false
    });
  },

  confirmHealthDataImport(rows: ImportPreviewRow[]) {
    return wait<ImportPreviewResult>({
      created_records_count: rows.length,
      disclaimer: "确认导入只写入通过校验的系统记录，不生成医学判断。",
      errors: [],
      file_name: "mobile-health-data-demo.csv",
      import_type: "csv",
      invalid_count: 0,
      job_id: "mock-import-job-1",
      preview_rows: rows,
      status: "completed",
      total_count: rows.length,
      valid_count: rows.length,
      will_write: true
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
