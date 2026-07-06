import { apiClient } from "@/lib/apiClient";
import type {
  AgentRunResponse,
  AgentSafetyCheckSummary,
  AgentToolCallSummary,
  Alert,
  AlertCreateInput,
  AgentRunRequest,
  BloodPressureRecord,
  Family,
  FamilyMember,
  HealthProfile,
  HealthStatus,
  MedicalEventDraftInput,
  SymptomDraftInput,
  SymptomRecord
} from "@/types/api";

type BackendFamily = Family & { created_at?: string; updated_at?: string };

type BackendFamilyMember = {
  id: string;
  family_id: string;
  user_id: string;
  display_name?: string | null;
  relationship_label?: string | null;
  role?: string;
  status?: string;
};

type BackendAgentTrace = {
  trace_id: string;
  workflow_type: string;
  status: AgentRunResponse["status"];
  output_summary?: string | null;
};

type BackendToolCall = {
  id: string;
  tool_name: string;
  status: "completed" | "blocked" | "failed";
  output_summary?: Record<string, unknown> | null;
  input_summary?: Record<string, unknown> | null;
};

type BackendSafetyCheck = {
  id: string;
  safety_level: string;
  passed: boolean;
  blocked_reason?: string | null;
  input_risk_summary?: string | null;
  revised_answer_summary?: string | null;
};

function toFamilyMember(member: BackendFamilyMember): FamilyMember {
  return {
    id: member.id,
    family_id: member.family_id,
    user_id: member.user_id,
    display_name: member.display_name ?? member.relationship_label ?? "家庭成员",
    relationship_label: member.relationship_label ?? "家庭成员",
    share_status: member.status ?? "active"
  };
}

function summarizeMapping(value: Record<string, unknown> | null | undefined): string {
  if (!value) {
    return "安全摘要";
  }
  const keys = Object.keys(value).filter((key) => !key.toLowerCase().includes("raw") && !key.toLowerCase().includes("path"));
  return keys.length > 0 ? keys.slice(0, 4).join(", ") : "安全摘要";
}

function postAgentRun(input: { currentUserId: string; body: AgentRunRequest }) {
  return apiClient.post<AgentRunResponse>("/api/v1/agent/runs", input.body, input.currentUserId);
}

export const backendApi = {
  getHealth() {
    return apiClient.get<HealthStatus>("/health");
  },

  listFamilies(currentUserId: string) {
    return apiClient.get<BackendFamily[]>("/api/v1/families", currentUserId);
  },

  listFamilyMembers(familyId: string, currentUserId: string) {
    return apiClient
      .get<BackendFamilyMember[]>(`/api/v1/families/${familyId}/members`, currentUserId)
      .then((items) => items.map(toFamilyMember));
  },

  listFamilyPermissions(familyId: string, currentUserId: string) {
    return apiClient.get<Record<string, unknown>[]>(`/api/v1/families/${familyId}/permissions`, currentUserId);
  },

  getMyHealthProfile(currentUserId: string) {
    return apiClient.get<HealthProfile>("/api/v1/health-profile/me", currentUserId);
  },

  getFamilyMemberHealthProfile(familyId: string, targetUserId: string, currentUserId: string) {
    return apiClient.get<HealthProfile>(
      `/api/v1/families/${familyId}/members/${targetUserId}/health-profile`,
      currentUserId
    );
  },

  getMyBloodPressureRecent(currentUserId: string, days = 30) {
    return apiClient.get<BloodPressureRecord[]>(`/api/v1/health-data/me/blood-pressure/recent?days=${days}`, currentUserId);
  },

  getFamilyMemberBloodPressureRecent(familyId: string, targetUserId: string, currentUserId: string, days = 30) {
    return apiClient.get<BloodPressureRecord[]>(
      `/api/v1/families/${familyId}/members/${targetUserId}/health-data/blood-pressure/recent?days=${days}`,
      currentUserId
    );
  },

  getMyBloodPressureSummary(currentUserId: string, days = 30) {
    return apiClient.get<Record<string, unknown>>(`/api/v1/health-data/me/blood-pressure/summary?days=${days}`, currentUserId);
  },

  getFamilyMemberBloodPressureSummary(familyId: string, targetUserId: string, currentUserId: string, days = 30) {
    return apiClient.get<Record<string, unknown>>(
      `/api/v1/families/${familyId}/members/${targetUserId}/health-data/blood-pressure/summary?days=${days}`,
      currentUserId
    );
  },

  getMySymptomsSummary(currentUserId: string, days = 30) {
    return apiClient.get<Record<string, unknown>>(`/api/v1/health-records/me/symptoms/summary?days=${days}`, currentUserId);
  },

  getFamilyMemberSymptomsSummary(familyId: string, targetUserId: string, currentUserId: string, days = 30) {
    return apiClient.get<Record<string, unknown>>(
      `/api/v1/families/${familyId}/members/${targetUserId}/health-records/symptoms/summary?days=${days}`,
      currentUserId
    );
  },

  getMyRecentSymptoms(currentUserId: string, days = 30) {
    return apiClient.get<SymptomRecord[]>(`/api/v1/health-records/me/symptoms/recent?days=${days}`, currentUserId);
  },

  getFamilyMemberActiveAlerts(familyId: string, targetUserId: string, currentUserId: string) {
    return apiClient.get<Alert[]>(`/api/v1/families/${familyId}/members/${targetUserId}/alerts/active`, currentUserId);
  },

  runDailyHealthBrief(input: { currentUserId: string; targetUserId: string; familyId?: string }) {
    return postAgentRun({
      currentUserId: input.currentUserId,
      body: {
        family_id: input.familyId,
        source: "mobile_phase_09_3_a",
        target_user_id: input.targetUserId,
        user_message: "请根据系统内记录生成今日健康简报。",
        workflow_type: "daily_health_brief"
      }
    });
  },

  createSymptomDraftPreview(input: SymptomDraftInput & { currentUserId: string }) {
    return postAgentRun({
      currentUserId: input.currentUserId,
      body: {
        confirmation: false,
        family_id: input.familyId,
        source: "mobile_phase_09_3_d",
        target_user_id: input.targetUserId,
        user_message: "请基于用户提供的健康记录内容生成待确认症状草稿预览。",
        workflow_payload: {
          raw_text: input.description,
          target_display_name: input.targetDisplayName
        },
        workflow_type: "symptom_draft_create"
      }
    });
  },

  createSymptomDraftConfirmed(input: SymptomDraftInput & { currentUserId: string }) {
    return postAgentRun({
      currentUserId: input.currentUserId,
      body: {
        confirmation: true,
        family_id: input.familyId,
        source: "mobile_phase_09_3_d",
        target_user_id: input.targetUserId,
        user_message: "请基于用户确认的健康记录内容创建待确认症状草稿。",
        workflow_payload: {
          raw_text: input.description,
          target_display_name: input.targetDisplayName
        },
        workflow_type: "symptom_draft_create"
      }
    });
  },

  createMedicalEventDraftPreview(input: MedicalEventDraftInput & { currentUserId: string }) {
    return postAgentRun({
      currentUserId: input.currentUserId,
      body: {
        confirmation: false,
        family_id: input.familyId,
        source: "mobile_phase_09_3_d",
        target_user_id: input.targetUserId,
        user_message: "请基于用户提供的健康事项内容生成待确认健康事件草稿预览。",
        workflow_payload: {
          department: input.department,
          draft_event_type: input.eventType,
          event_date: input.eventDate,
          hospital_or_org: input.hospitalOrOrg,
          summary: input.summary,
          title: input.title
        },
        workflow_type: "medical_event_draft_create"
      }
    });
  },

  createMedicalEventDraftConfirmed(input: MedicalEventDraftInput & { currentUserId: string }) {
    return postAgentRun({
      currentUserId: input.currentUserId,
      body: {
        confirmation: true,
        family_id: input.familyId,
        source: "mobile_phase_09_3_d",
        target_user_id: input.targetUserId,
        user_message: "请基于用户确认的健康事项内容创建待确认健康事件草稿。",
        workflow_payload: {
          department: input.department,
          draft_event_type: input.eventType,
          event_date: input.eventDate,
          hospital_or_org: input.hospitalOrOrg,
          summary: input.summary,
          title: input.title
        },
        workflow_type: "medical_event_draft_create"
      }
    });
  },

  createAlertPreview(input: AlertCreateInput & { currentUserId: string }) {
    return postAgentRun({
      currentUserId: input.currentUserId,
      body: {
        confirmation: false,
        family_id: input.familyId,
        source: "mobile_phase_09_3_d",
        target_user_id: input.targetUserId,
        user_message: "请基于用户提供的信息生成普通健康提醒预览。",
        workflow_payload: {
          alert_type: input.alertType ?? "medical_follow_up",
          level: input.level ?? "info",
          message: input.message,
          scheduled_at: input.scheduledAt,
          title: input.title
        },
        workflow_type: "alert_create"
      }
    });
  },

  createAlertConfirmed(input: AlertCreateInput & { currentUserId: string }) {
    return postAgentRun({
      currentUserId: input.currentUserId,
      body: {
        confirmation: true,
        family_id: input.familyId,
        source: "mobile_phase_09_3_d",
        target_user_id: input.targetUserId,
        user_message: "请基于用户确认的信息创建普通健康提醒。",
        workflow_payload: {
          alert_type: input.alertType ?? "medical_follow_up",
          level: input.level ?? "info",
          message: input.message,
          scheduled_at: input.scheduledAt,
          title: input.title
        },
        workflow_type: "alert_create"
      }
    });
  },

  getAgentRun(traceId: string, currentUserId: string) {
    return apiClient.get<BackendAgentTrace>(`/api/v1/agent/runs/${traceId}`, currentUserId);
  },

  getAgentRunToolCalls(traceId: string, currentUserId: string) {
    return apiClient.get<BackendToolCall[]>(`/api/v1/agent/runs/${traceId}/tool-calls`, currentUserId).then((items) =>
      items.map<AgentToolCallSummary>((item) => ({
        id: item.id,
        name: item.tool_name,
        status: item.status,
        summary: summarizeMapping(item.output_summary ?? item.input_summary)
      }))
    );
  },

  getAgentRunSafetyChecks(traceId: string, currentUserId: string) {
    return apiClient.get<BackendSafetyCheck[]>(`/api/v1/agent/runs/${traceId}/safety-checks`, currentUserId).then((items) =>
      items.map<AgentSafetyCheckSummary>((item) => ({
        id: item.id,
        stage: item.revised_answer_summary ? "output" : "input",
        status: item.passed ? "passed" : item.safety_level === "blocked" ? "blocked" : "caution",
        summary: item.blocked_reason ?? item.input_risk_summary ?? item.revised_answer_summary ?? "安全检查摘要"
      }))
    );
  }
};
