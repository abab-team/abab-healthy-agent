import { apiClient } from "@/lib/apiClient";
import type {
  AgentRunResponse,
  AgentMemoryItem,
  LatestDailyHealthBrief,
  AgentMessageSummary,
  AgentSessionSummary,
  AgentSafetyCheckSummary,
  AgentToolCallSummary,
  Alert,
  AlertCreateInput,
  AgentRunRequest,
  ArchiveTrends,
  BloodPressureRecord,
  ChatHealthQueryInput,
  DocumentExtractionResult,
  DocumentProcessingJob,
  Family,
  FamilyCreationResult,
  FamilyInvitation,
  FamilyMember,
  FamilySharePermission,
  HealthProfile,
  JoinedFamilyResult,
  HealthMetricRecord,
  HealthMetricCreateInput,
  BloodPressureCreateInput,
  HealthStatus,
  ImportPreviewResult,
  ImportPreviewRow,
  MedicalDocument,
  MedicalTimelineEvent,
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
  workflow_type: AgentRunResponse["workflow_type"];
  status: AgentRunResponse["status"];
  output_summary?: string | null;
  source?: string | null;
  started_at?: string | null;
  ended_at?: string | null;
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

type BackendBloodPressureRecord = Omit<BloodPressureRecord, "recorded_at"> & { measured_at?: string; recorded_at?: string };

type BackendSymptomRecord = {
  id: string;
  user_id: string;
  symptom_name?: string | null;
  ai_summary?: string | null;
  raw_text?: string | null;
  created_at?: string | null;
};

function toBloodPressureRecord(record: BackendBloodPressureRecord): BloodPressureRecord {
  return { ...record, recorded_at: record.recorded_at ?? record.measured_at ?? new Date(0).toISOString() };
}

function toSymptomRecord(record: BackendSymptomRecord): SymptomRecord {
  return {
    id: record.id,
    recorded_at: record.created_at ?? new Date(0).toISOString(),
    summary: record.ai_summary?.trim() || record.raw_text?.trim() || "已保存的症状记录",
    title: record.symptom_name?.trim() || "症状记录",
    user_id: record.user_id
  };
}

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

  createFamily(input: { name: string; ownerDisplayName: string }, currentUserId: string) {
    return apiClient.post<FamilyCreationResult>("/api/v1/families", { name: input.name, owner_display_name: input.ownerDisplayName }, currentUserId);
  },

  joinFamilyByCode(inviteCode: string, currentUserId: string) {
    return apiClient.post<JoinedFamilyResult>("/api/v1/families/join-by-code", { invite_code: inviteCode }, currentUserId);
  },

  createFamilyInvitationCode(familyId: string, currentUserId: string) {
    return apiClient.post<FamilyInvitation>(`/api/v1/families/${familyId}/invitation-codes`, {}, currentUserId);
  },

  listFamilyMembers(familyId: string, currentUserId: string) {
    return apiClient
      .get<BackendFamilyMember[]>(`/api/v1/families/${familyId}/members`, currentUserId)
      .then((items) => items.map(toFamilyMember));
  },

  listFamilyPermissions(familyId: string, currentUserId: string) {
    return apiClient.get<Record<string, unknown>[]>(`/api/v1/families/${familyId}/permissions`, currentUserId);
  },

  getMyFamilySharePermission(familyId: string, currentUserId: string) {
    return apiClient.get<FamilySharePermission>(`/api/v1/families/${familyId}/members/${currentUserId}/permissions`, currentUserId);
  },

  updateMyFamilySharePermission(familyId: string, input: Partial<FamilySharePermission>, currentUserId: string) {
    return apiClient.patch<FamilySharePermission>(`/api/v1/families/${familyId}/members/${currentUserId}/permissions`, input, currentUserId);
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
    return apiClient
      .get<{ items: BackendBloodPressureRecord[] }>(`/api/v1/health-data/me/blood-pressure/recent?days=${days}`, currentUserId)
      .then((response) => response.items.map(toBloodPressureRecord));
  },

  getMyRecentMetrics(currentUserId: string, days = 30) {
    return apiClient
      .get<{ items: HealthMetricRecord[] }>(`/api/v1/health-data/me/metrics/recent?days=${days}`, currentUserId)
      .then((response) => response.items);
  },

  createMyMetric(input: HealthMetricCreateInput, currentUserId: string) {
    return apiClient.post<HealthMetricRecord>("/api/v1/health-data/me/metrics", { ...input, source: "manual" }, currentUserId);
  },

  createMyBloodPressure(input: BloodPressureCreateInput, currentUserId: string) {
    return apiClient
      .post<BackendBloodPressureRecord>("/api/v1/health-data/me/blood-pressure", { ...input, source: "manual" }, currentUserId)
      .then(toBloodPressureRecord);
  },

  getFamilyMemberBloodPressureRecent(familyId: string, targetUserId: string, currentUserId: string, days = 30) {
    return apiClient
      .get<{ items: BackendBloodPressureRecord[] }>(`/api/v1/families/${familyId}/members/${targetUserId}/health-data/blood-pressure/recent?days=${days}`, currentUserId)
      .then((response) => response.items.map(toBloodPressureRecord));
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

  getFamilyMemberRecentMetrics(familyId: string, targetUserId: string, currentUserId: string, days = 30) {
    return apiClient
      .get<{ items: HealthMetricRecord[] }>(`/api/v1/families/${familyId}/members/${targetUserId}/health-data/metrics/recent?days=${days}`, currentUserId)
      .then((response) => response.items);
  },

  getFamilyMemberRecentSymptoms(familyId: string, targetUserId: string, currentUserId: string, days = 30) {
    return apiClient
      .get<{ items: SymptomRecord[] }>(`/api/v1/families/${familyId}/members/${targetUserId}/health-records/symptoms/recent?days=${days}`, currentUserId)
      .then((response) => response.items);
  },

  getMyArchiveTrends(currentUserId: string, days = 90) {
    return apiClient.get<ArchiveTrends>(`/api/v1/health-data/me/archive/trends?days=${days}`, currentUserId);
  },

  previewMyHealthDataImport(currentUserId: string, rows: ImportPreviewRow[]) {
    return apiClient.post<ImportPreviewResult>(
      "/api/v1/health-data/me/imports/preview",
      {
        file_name: "mobile-health-data-demo.csv",
        import_type: "csv",
        rows
      },
      currentUserId
    );
  },

  confirmMyHealthDataImport(currentUserId: string, rows: ImportPreviewRow[]) {
    return apiClient.post<ImportPreviewResult>(
      "/api/v1/health-data/me/imports/confirm",
      {
        confirmation: true,
        file_name: "mobile-health-data-demo.csv",
        import_type: "csv",
        rows
      },
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
    return apiClient
      .get<{ items: BackendSymptomRecord[] }>(`/api/v1/health-records/me/symptoms/recent?days=${days}`, currentUserId)
      .then((response) => response.items.map(toSymptomRecord));
  },

  getMyActiveAlerts(currentUserId: string) {
    return apiClient.get<{ items: Alert[] }>("/api/v1/alerts/me/active", currentUserId).then((response) => response.items);
  },

  getMyAlerts(currentUserId: string) {
    return apiClient.get<{ items: Alert[] }>("/api/v1/alerts/me", currentUserId).then((response) => response.items);
  },

  getFamilyMemberActiveAlerts(familyId: string, targetUserId: string, currentUserId: string) {
    return apiClient
      .get<{ items: Alert[] }>(`/api/v1/families/${familyId}/members/${targetUserId}/alerts/active`, currentUserId)
      .then((response) => response.items);
  },

  listMyDocuments(currentUserId: string) {
    return apiClient.get<{ items: MedicalDocument[] }>("/api/v1/documents/me", currentUserId).then((response) => response.items);
  },

  uploadMyDocument(
    input: { content: Blob; documentType: "checkup_report" | "medical_record" | "lab_test" | "prescription" | "other"; fileName: string; mimeType: string; title: string },
    currentUserId: string
  ) {
    const query = new URLSearchParams({
      document_type: input.documentType,
      title: input.title
    });
    return apiClient.upload<MedicalDocument>(
      `/api/v1/documents/me/upload?${query.toString()}`,
      input.content,
      { "Content-Type": input.mimeType, "X-File-Name": input.fileName },
      currentUserId
    );
  },

  listFamilyMemberDocuments(familyId: string, targetUserId: string, currentUserId: string) {
    return apiClient
      .get<{ items: MedicalDocument[] }>(`/api/v1/families/${familyId}/members/${targetUserId}/documents`, currentUserId)
      .then((response) => response.items);
  },

  listFamilyMemberMedicalEvents(familyId: string, targetUserId: string, currentUserId: string) {
    return apiClient
      .get<{ items: Array<{ id: string; title?: string | null; event_type?: string | null; event_date?: string | null; hospital_or_org?: string | null }> }>(
        `/api/v1/families/${familyId}/members/${targetUserId}/medical-timeline/events`,
        currentUserId
      )
      .then((response) => response.items);
  },

  listMyMedicalEvents(currentUserId: string) {
    return apiClient
      .get<{ items: MedicalTimelineEvent[] }>("/api/v1/medical-timeline/me/events", currentUserId)
      .then((response) => response.items);
  },

  getMyDocument(documentId: string, currentUserId: string) {
    return apiClient.get<MedicalDocument>(`/api/v1/documents/me/${documentId}`, currentUserId);
  },

  downloadMyDocument(documentId: string, currentUserId: string) {
    return apiClient.download(`/api/v1/documents/me/${documentId}/content`, currentUserId);
  },

  listMyDocumentJobs(documentId: string, currentUserId: string) {
    return apiClient
      .get<{ items: DocumentProcessingJob[] }>(`/api/v1/document-processing/me/documents/${documentId}/jobs`, currentUserId)
      .then((response) => response.items);
  },

  createMyDocumentOcrJob(documentId: string, currentUserId: string) {
    return apiClient.post<DocumentProcessingJob>(
      `/api/v1/document-processing/me/documents/${documentId}/jobs`,
      { job_type: "ocr" },
      currentUserId
    );
  },

  runMyMockOcr(jobId: string, currentUserId: string) {
    return apiClient.post<DocumentExtractionResult>(`/api/v1/document-processing/me/jobs/${jobId}/run-mock-ocr`, {}, currentUserId);
  },

  listMyExtractionResults(documentId: string, currentUserId: string) {
    return apiClient
      .get<{ items: DocumentExtractionResult[] }>(
        `/api/v1/document-processing/me/documents/${documentId}/extraction-results`,
        currentUserId
      )
      .then((response) => response.items);
  },

  runDailyHealthBrief(input: { currentUserId: string; targetUserId: string; familyId?: string }) {
    return postAgentRun({
      currentUserId: input.currentUserId,
      body: {
        family_id: input.familyId,
        source: "mobile_home_daily_health_brief",
        target_user_id: input.targetUserId,
        user_message: "请根据系统内记录生成今日健康简报。",
        workflow_type: "daily_health_brief"
      }
    });
  },

  getLatestDailyHealthBrief(currentUserId: string) {
    return apiClient.get<LatestDailyHealthBrief>("/api/v1/agent/daily-health-brief/latest", currentUserId);
  },

  runChatHealthQuery(input: ChatHealthQueryInput & { currentUserId: string }) {
    return postAgentRun({
      currentUserId: input.currentUserId,
      body: {
        family_id: input.familyId,
        session_id: input.sessionId ?? undefined,
        source: "mobile_phase_16_chat",
        quick_note_mode: Boolean(input.quickNoteMode),
        target_user_id: input.targetUserId,
        user_message: input.question,
        workflow_type: "chat"
      }
    });
  },

  confirmQuickNote(sessionId: string, taskId: string, currentUserId: string) {
    return apiClient.post<{ conversation_task: NonNullable<AgentRunResponse["conversation_task"]>; message: string }>(`/api/v1/agent/sessions/${sessionId}/quick-note/${taskId}/confirm`, {}, currentUserId);
  },

  cancelQuickNote(sessionId: string, taskId: string, currentUserId: string) {
    return apiClient.post<{ conversation_task: NonNullable<AgentRunResponse["conversation_task"]>; message: string }>(`/api/v1/agent/sessions/${sessionId}/quick-note/${taskId}/cancel`, {}, currentUserId);
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
  },

  listAgentSessions(currentUserId: string) {
    return apiClient.get<AgentSessionSummary[]>("/api/v1/agent/sessions", currentUserId);
  },

  listAgentSessionMessages(sessionId: string, currentUserId: string) {
    return apiClient.get<AgentMessageSummary[]>(`/api/v1/agent/sessions/${sessionId}/messages`, currentUserId);
  },

  listAgentMemory(currentUserId: string) {
    return apiClient.get<AgentMemoryItem[]>("/api/v1/agent/memory", currentUserId);
  },

  deleteAgentMemory(memoryId: string, currentUserId: string) {
    return apiClient.delete<{ deleted: boolean }>(`/api/v1/agent/memory/${memoryId}`, currentUserId);
  }
};
