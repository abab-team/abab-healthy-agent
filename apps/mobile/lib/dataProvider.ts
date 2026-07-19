import { family as mockFamily, members as mockMembers, reminders as mockReminders } from "@/constants/mockData";
import { dataMode, defaultDemoUserId } from "@/lib/apiConfig";
import { backendApi } from "@/lib/backendApi";
import { mockApi } from "@/lib/mockApi";
import type {
  AgentRunDetail,
  AgentRunResponse,
  AgentMemoryItem,
  AgentMessageSummary,
  AgentSessionSummary,
  Alert,
  AlertCreateInput,
  ArchiveTrends,
  ApiFamilyOverview,
  ApiMemberDetail,
  ApiResult,
  BloodPressureRecord,
  ChatHealthQueryInput,
  DocumentPipelineDetail,
  Family,
  FamilyCreationResult,
  FamilyInvitation,
  FamilyMember,
  FamilySharePermission,
  HealthStatus,
  HealthMetricRecord,
  HealthMetricCreateInput,
  BloodPressureCreateInput,
  ImportPreviewResult,
  ImportPreviewRow,
  LatestDailyHealthBrief,
  JoinedFamilyResult,
  MedicalDocument,
  MedicalTimelineEvent,
  MedicalEventDraftInput,
  SymptomRecord,
  SymptomDraftInput
} from "@/types/api";

export type MemberArchiveSection = "records" | "metrics" | "documents" | "ai";

export type MemberArchiveSectionData = {
  member: FamilyMember;
  source: "mock" | "api";
  bloodPressure: BloodPressureRecord[];
  metrics: HealthMetricRecord[];
  symptoms: SymptomRecord[];
  documents: MedicalDocument[];
  medicalEvents: MedicalTimelineEvent[];
  profileSummary?: string;
};

export type PersonalHealthMetricsData = {
  bloodPressure: BloodPressureRecord[];
  metrics: HealthMetricRecord[];
  source: "mock" | "api";
};

export type PersonalArchiveRecentRecordsData = {
  alerts: Alert[];
  bloodPressure: BloodPressureRecord[];
  documents: MedicalDocument[];
  medicalEvents: MedicalTimelineEvent[];
  metrics: HealthMetricRecord[];
  source: "mock" | "api";
  symptoms: SymptomRecord[];
};

function ok<T>(data: T): ApiResult<T> {
  return { ok: true, data };
}

function fail<T>(error: unknown): ApiResult<T> {
  const message = error instanceof Error ? error.message : "请求失败，请检查 API 配置。";
  const code = error && typeof error === "object" && "code" in error ? String((error as { code: unknown }).code) : "request_failed";
  return { ok: false, error: { code, message } };
}

function buildMockChatReply(question: string): string {
  const text = question.trim();
  if (/你好|您好|hello|^hi\b/i.test(text)) {
    return "你好，Gala 👋 今天过得怎么样？想聊聊近况，或看看已经记录的健康信息，都可以直接告诉我。";
  }
  if (/血压/.test(text)) {
    return "演示数据里有几条血压记录。我可以像正式模式一样帮你按时间范围整理；真实数据需要连接后端后才会显示。";
  }
  if (/睡眠/.test(text)) {
    return "演示数据里最近有睡眠记录。连接后端后，我可以帮你按最近一周、一个月等范围整理系统内已有信息。";
  }
  if (/记录|提醒/.test(text)) {
    return "我可以先帮你整理成待确认草稿或普通健康提醒。预览不会写入，确认后才会继续。";
  }
  return "我在。你可以和我聊聊近况，也可以问我已经记录的睡眠、血压、提醒、资料或家庭健康信息。";
}

async function getApiFamilyOverview(currentUserId: string): Promise<ApiResult<ApiFamilyOverview>> {
  try {
    const families = await backendApi.listFamilies(currentUserId);
    const firstFamily = families[0];
    if (!firstFamily) {
      return ok({
        family: { id: "empty", name: "系统内暂无家庭", owner_user_id: currentUserId },
        members: [],
        reminders: [],
        source: "api",
        mockSections: ["今日待办", "最近动态"]
      });
    }
    const members = await backendApi.listFamilyMembers(firstFamily.id, currentUserId);
    return ok<ApiFamilyOverview>({
      family: firstFamily,
      members,
      reminders: mockReminders,
      source: "api",
      mockSections: ["提醒聚合", "今日待办", "最近动态"]
    });
  } catch (error) {
    return fail(error);
  }
}

async function getApiMemberDetail(id: string, currentUserId: string): Promise<ApiResult<ApiMemberDetail>> {
  try {
    const overview = await getApiFamilyOverview(currentUserId);
    if (!overview.ok || !overview.data) {
      return fail<ApiMemberDetail>(overview.error?.message ?? "家庭概览加载失败。");
    }
    const member = overview.data.members.find((item) => item.id === id || item.user_id === id) ?? overview.data.members[0];
    if (!member) {
      return fail(new Error("系统内暂无可展示成员。"));
    }
    const isSelf = member.user_id === currentUserId || member.id === "me";
    const profile = isSelf
      ? await backendApi.getMyHealthProfile(currentUserId).catch(() => undefined)
      : await backendApi.getFamilyMemberHealthProfile(member.family_id, member.user_id, currentUserId).catch(() => undefined);
    const bloodPressureSummary = isSelf
      ? await backendApi.getMyBloodPressureSummary(currentUserId).catch(() => undefined)
      : await backendApi.getFamilyMemberBloodPressureSummary(member.family_id, member.user_id, currentUserId).catch(() => undefined);
    const symptomSummary = isSelf
      ? await backendApi.getMySymptomsSummary(currentUserId).catch(() => undefined)
      : await backendApi.getFamilyMemberSymptomsSummary(member.family_id, member.user_id, currentUserId).catch(() => undefined);
    const activeAlerts = isSelf
      ? []
      : await backendApi.getFamilyMemberActiveAlerts(member.family_id, member.user_id, currentUserId).catch(() => []);
    return ok({
      activeAlerts,
      bloodPressureSummary,
      member,
      mockSections: ["提醒文案", "待确认草稿"],
      profile,
      source: "api",
      symptomSummary
    });
  } catch (error) {
    return fail(error);
  }
}

async function getApiMemberArchiveSection(
  id: string,
  section: MemberArchiveSection,
  currentUserId: string
): Promise<ApiResult<MemberArchiveSectionData>> {
  const overview = await getApiFamilyOverview(currentUserId);
  if (!overview.ok || !overview.data) {
    return fail(overview.error?.message ?? "家庭资料加载失败");
  }
  const member = overview.data.members.find((item) => item.user_id === id || item.id === id);
  if (!member) {
    return fail(new Error("未找到该家庭成员"));
  }
  try {
    const base: MemberArchiveSectionData = {
      bloodPressure: [],
      metrics: [],
      documents: [],
      medicalEvents: [],
      member,
      source: "api",
      symptoms: []
    };
    const isSelf = member.user_id === currentUserId;
    if (section === "metrics") {
      const [bloodPressure, metrics] = await Promise.all(isSelf ? [
        backendApi.getMyBloodPressureRecent(currentUserId),
        backendApi.getMyRecentMetrics(currentUserId)
      ] : [
        backendApi.getFamilyMemberBloodPressureRecent(member.family_id, member.user_id, currentUserId),
        backendApi.getFamilyMemberRecentMetrics(member.family_id, member.user_id, currentUserId)
      ]);
      base.bloodPressure = bloodPressure;
      base.metrics = metrics;
    } else if (section === "records") {
      const [bloodPressure, documents, medicalEvents, metrics, symptoms] = await Promise.all(isSelf ? [
        backendApi.getMyBloodPressureRecent(currentUserId),
        backendApi.listMyDocuments(currentUserId),
        backendApi.listMyMedicalEvents(currentUserId),
        backendApi.getMyRecentMetrics(currentUserId),
        backendApi.getMyRecentSymptoms(currentUserId)
      ] : [
        backendApi.getFamilyMemberBloodPressureRecent(member.family_id, member.user_id, currentUserId),
        backendApi.listFamilyMemberDocuments(member.family_id, member.user_id, currentUserId),
        backendApi.listFamilyMemberMedicalEvents(member.family_id, member.user_id, currentUserId),
        backendApi.getFamilyMemberRecentMetrics(member.family_id, member.user_id, currentUserId),
        backendApi.getFamilyMemberRecentSymptoms(member.family_id, member.user_id, currentUserId)
      ]);
      base.bloodPressure = bloodPressure;
      base.documents = documents;
      base.medicalEvents = medicalEvents;
      base.metrics = metrics;
      base.symptoms = symptoms;
    } else if (section === "documents") {
      const [documents, medicalEvents] = await Promise.all(isSelf ? [
        backendApi.listMyDocuments(currentUserId),
        backendApi.listMyMedicalEvents(currentUserId)
      ] : [
        backendApi.listFamilyMemberDocuments(member.family_id, member.user_id, currentUserId),
        backendApi.listFamilyMemberMedicalEvents(member.family_id, member.user_id, currentUserId)
      ]);
      base.documents = documents;
      base.medicalEvents = medicalEvents;
    } else {
      base.profileSummary = (isSelf ? await backendApi.getMyHealthProfile(currentUserId) : await backendApi.getFamilyMemberHealthProfile(member.family_id, member.user_id, currentUserId)).summary;
    }
    return ok(base);
  } catch (error) {
    return fail<MemberArchiveSectionData>(error);
  }
}

export function getDataProvider(currentUserId = defaultDemoUserId) {
  if (dataMode === "mock") {
    return {
      getHealthStatus: () => ok<HealthStatus>({ service: "family-health-agent", status: "mock" }),
      getFamilyOverview: async () => {
        const result = await mockApi.getFamilyOverview();
        if (!result.ok || !result.data) {
          return fail<ApiFamilyOverview>(result.error?.message ?? "演示数据加载失败");
        }
        const data = result.data;
        return ok<ApiFamilyOverview>({
          family: { id: data.family.id, name: data.family.name, owner_user_id: "me" },
          members: data.members.map((member) => ({
            display_name: member.name,
            family_id: data.family.id,
            id: member.id,
            relationship_label: member.relation,
            share_status: member.shareStatus,
            user_id: member.id
          })),
          mockSections: ["全部页面数据"],
          reminders: data.reminders,
          source: "mock"
        });
      },
      listMyFamilies: async () => ok<Family[]>([{ id: mockFamily.id, name: mockFamily.name, owner_user_id: "me" }]),
      createFamily: async () => fail<FamilyCreationResult>(new Error("演示模式不会创建真实家庭。")),
      joinFamilyByCode: async () => fail<JoinedFamilyResult>(new Error("演示模式不会加入真实家庭。")),
      createFamilyInvitationCode: async () => fail<FamilyInvitation>(new Error("演示模式不会生成真实邀请码。")),
      getMyFamilySharePermission: async () => ok<FamilySharePermission>({ family_id: mockFamily.id, user_id: "me", share_all: false, can_view_profile: false, can_view_metrics: false, can_view_symptoms: false, can_view_medical_events: false, can_view_documents: false }),
      updateMyFamilySharePermission: async (_familyId: string, input: Partial<FamilySharePermission>) => ok<FamilySharePermission>({ family_id: mockFamily.id, user_id: "me", share_all: false, can_view_profile: false, can_view_metrics: false, can_view_symptoms: false, can_view_medical_events: false, can_view_documents: false, ...input }),
      getMemberDetail: async (id: string) => {
        const member = mockMembers.find((item) => item.id === id) ?? mockMembers[0];
        return ok<ApiMemberDetail>({
          activeAlerts: [],
          member: {
            display_name: member.name,
            family_id: mockFamily.id,
            id: member.id,
            relationship_label: member.relation,
            share_status: member.shareStatus,
            user_id: member.id
          },
          mockSections: ["全部页面数据"],
          source: "mock"
        });
      },
      getMemberArchiveSection: async (id: string, section: MemberArchiveSection) => {
        const member = mockMembers.find((item) => item.id === id) ?? mockMembers[0];
        const base: MemberArchiveSectionData = {
          bloodPressure: section === "metrics" ? [
            { diastolic: 78, id: "mock-bp-1", recorded_at: "2026-07-10T07:30:00", systolic: 120, user_id: member.id },
            { diastolic: 76, id: "mock-bp-2", recorded_at: "2026-07-07T07:20:00", systolic: 118, user_id: member.id }
          ] : [],
          metrics: section === "metrics" ? [
            { id: "mock-sleep-1", measured_at: "2026-07-10T22:00:00", metric_type: "sleep_duration", unit: "hours", user_id: member.id, value_numeric: 7.2 },
            { id: "mock-weight-1", measured_at: "2026-07-10T07:00:00", metric_type: "weight", unit: "kg", user_id: member.id, value_numeric: 62.1 },
            { id: "mock-steps-1", measured_at: "2026-07-10T20:00:00", metric_type: "steps", unit: "steps", user_id: member.id, value_numeric: 6100 }
          ] : [],
          documents: section === "documents" ? [{ ai_extract_status: "completed", created_at: "2026-07-08", file_name: "annual-checkup.pdf", id: "mock-document-1", title: "年度体检报告" }] : [],
          medicalEvents: section === "documents" ? [{ event_date: "2026-06-28", event_type: "复查", id: "mock-event-1", title: "内科复查" }] : [],
          member: { display_name: member.name, family_id: mockFamily.id, id: member.id, relationship_label: member.relation, share_status: member.shareStatus, user_id: member.id },
          profileSummary: section === "ai" ? "系统内已有基础健康资料" : undefined,
          source: "mock",
          symptoms: section === "records" ? [{ id: "mock-symptom-1", recorded_at: "2026-07-09T10:30:00", summary: "已保存的症状记录摘要", title: "症状记录", user_id: member.id }] : []
        };
        return ok(base);
      },
      getArchiveTrends: async () => mockApi.getArchiveTrends(),
      getPersonalHealthMetrics: async () => ok<PersonalHealthMetricsData>({
        bloodPressure: [{ diastolic: 78, id: "mock-self-bp-1", recorded_at: "2026-07-10T07:30:00", systolic: 120, user_id: "me" }],
        metrics: [
          { id: "mock-self-sleep-1", measured_at: "2026-07-10T22:00:00", metric_type: "sleep_duration", unit: "hours", user_id: "me", value_numeric: 7.2 },
          { id: "mock-self-weight-1", measured_at: "2026-07-10T07:00:00", metric_type: "weight", unit: "kg", user_id: "me", value_numeric: 62.1 },
          { id: "mock-self-steps-1", measured_at: "2026-07-10T20:00:00", metric_type: "steps", unit: "steps", user_id: "me", value_numeric: 6100 }
        ],
        source: "mock"
      }),
      getPersonalArchiveRecentRecords: async () => ok<PersonalArchiveRecentRecordsData>({
        alerts: [],
        bloodPressure: [{ diastolic: 78, id: "mock-self-bp-1", recorded_at: "2026-07-10T07:30:00", systolic: 120, user_id: "me" }],
        documents: [{ ai_extract_status: "completed", created_at: "2026-07-08T16:20:00", file_name: "annual-checkup.pdf", id: "mock-document-1", title: "年度体检报告" }],
        medicalEvents: [{ created_at: "2026-07-07T09:00:00", event_type: "复查", id: "mock-event-1", title: "内科复查" }],
        metrics: [
          { id: "mock-self-sleep-1", measured_at: "2026-07-10T22:00:00", metric_type: "sleep_duration", unit: "hours", user_id: "me", value_numeric: 7.2 },
          { id: "mock-self-weight-1", measured_at: "2026-07-10T07:00:00", metric_type: "weight", unit: "kg", user_id: "me", value_numeric: 62.1 }
        ],
        source: "mock",
        symptoms: [{ id: "mock-symptom-1", recorded_at: "2026-07-09T10:30:00", summary: "已保存的症状记录摘要", title: "症状记录", user_id: "me" }]
      }),
      createHealthMetric: async (_input: HealthMetricCreateInput | BloodPressureCreateInput) => fail(new Error("演示模式不会提交真实健康记录。")),
      previewHealthDataImport: async (rows: ImportPreviewRow[]) => mockApi.previewHealthDataImport(rows),
      confirmHealthDataImport: async (rows: ImportPreviewRow[]) => mockApi.confirmHealthDataImport(rows),
      runDailyHealthBrief: async () => {
        const result = await mockApi.getAgentBrief();
        if (!result.ok || !result.data) {
          return fail<AgentRunResponse>(result.error?.message ?? "演示简报加载失败");
        }
        return ok<AgentRunResponse>({
          generated_content: result.data.generatedContent,
          status: "completed",
          trace_id: result.data.id,
          workflow_type: "daily_health_brief"
        });
      },
      getLatestDailyHealthBrief: async () => ok<LatestDailyHealthBrief | null>(null),
      runChatHealthQuery: async (input: ChatHealthQueryInput) =>
        ok<AgentRunResponse>({
          generated_content: buildMockChatReply(input.question),
          session_id: input.sessionId ?? "mock-session-1",
          status: "completed",
          trace_id: `mock-chat-${Date.now()}`,
          workflow_type: "chat"
        }),
      createSymptomDraftPreview: (input: SymptomDraftInput) => mockApi.createSymptomDraftPreview(input),
      createSymptomDraftConfirmed: (input: SymptomDraftInput) => mockApi.createSymptomDraftConfirmed(input),
      createMedicalEventDraftPreview: (input: MedicalEventDraftInput) => mockApi.createMedicalEventDraftPreview(input),
      createMedicalEventDraftConfirmed: (input: MedicalEventDraftInput) => mockApi.createMedicalEventDraftConfirmed(input),
      createAlertPreview: (input: AlertCreateInput) => mockApi.createAlertPreview(input),
      createAlertConfirmed: (input: AlertCreateInput) => mockApi.createAlertConfirmed(input),
      listDocuments: async () =>
        ok({
          items: [
            {
              ai_extract_status: "not_started",
              created_at: "demo",
              file_mime_type: "application/pdf",
              file_name: "demo-report.pdf",
              file_size: 1024,
              id: "mock-document-1",
              title: "演示健康资料"
            }
          ],
          mockSections: ["document_upload", "ocr", "draft_generation"],
          source: "mock" as const
        }),
      getDocumentPipelineDetail: async (documentId: string) =>
        ok<DocumentPipelineDetail>({
          document: {
            ai_extract_status: "not_started",
            created_at: "demo",
            file_mime_type: "application/pdf",
            file_name: "demo-report.pdf",
            file_size: 1024,
            id: documentId,
            title: "演示健康资料"
          },
          extractionResults: [],
          jobs: [],
          mockSections: ["真实上传、OCR、草稿生成在后端模式验证"],
          source: "mock"
        }),
      getAgentRun: (id: string) => mockApi.getAgentRun(id),
      listAgentSessions: async () =>
        ok<AgentSessionSummary[]>([
          {
            created_at: "demo",
            id: "mock-session-1",
            last_active_at: "demo",
            title: "演示对话"
          }
        ]),
      listAgentSessionMessages: async () =>
        ok<AgentMessageSummary[]>([
          {
            content_summary: "最近一周我的血压记录怎么样？",
            created_at: "demo",
            id: "mock-message-user-1",
            role: "user"
          },
          {
            content_summary: "根据演示数据，仅整理系统内记录，不替代医生判断。",
            created_at: "demo",
            id: "mock-message-ai-1",
            role: "assistant"
          }
        ]),
      listAgentMemory: async () =>
        ok<AgentMemoryItem[]>([
          {
            confidence: 80,
            content: "用户希望回答时优先说明系统内记录覆盖情况。",
            created_at: "demo",
            id: "mock-memory-1",
            is_user_editable: true,
            memory_type: "response_preference",
            source: "demo",
            updated_at: "demo"
          }
        ]),
      deleteAgentMemory: async () => ok({ deleted: true })
    };
  }

  return {
    getHealthStatus: async () => {
      try {
        return ok(await backendApi.getHealth());
      } catch (error) {
        return fail<HealthStatus>(error);
      }
    },
    getFamilyOverview: () => getApiFamilyOverview(currentUserId),
    listMyFamilies: async () => {
      try { return ok(await backendApi.listFamilies(currentUserId)); } catch (error) { return fail<Family[]>(error); }
    },
    createFamily: async (input: { name: string; ownerDisplayName: string }) => {
      try { return ok(await backendApi.createFamily(input, currentUserId)); } catch (error) { return fail<FamilyCreationResult>(error); }
    },
    joinFamilyByCode: async (inviteCode: string) => {
      try { return ok(await backendApi.joinFamilyByCode(inviteCode, currentUserId)); } catch (error) { return fail<JoinedFamilyResult>(error); }
    },
    createFamilyInvitationCode: async (familyId: string) => {
      try { return ok(await backendApi.createFamilyInvitationCode(familyId, currentUserId)); } catch (error) { return fail<FamilyInvitation>(error); }
    },
    getMyFamilySharePermission: async (familyId: string) => {
      try { return ok(await backendApi.getMyFamilySharePermission(familyId, currentUserId)); } catch (error) { return fail<FamilySharePermission>(error); }
    },
    updateMyFamilySharePermission: async (familyId: string, input: Partial<FamilySharePermission>) => {
      try { return ok(await backendApi.updateMyFamilySharePermission(familyId, input, currentUserId)); } catch (error) { return fail<FamilySharePermission>(error); }
    },
    getMemberDetail: (id: string) => getApiMemberDetail(id, currentUserId),
    getMemberArchiveSection: (id: string, section: MemberArchiveSection) => getApiMemberArchiveSection(id, section, currentUserId),
    getArchiveTrends: async () => {
      try {
        return ok<ArchiveTrends>(await backendApi.getMyArchiveTrends(currentUserId));
      } catch (error) {
        return fail<ArchiveTrends>(error);
      }
    },
    getPersonalHealthMetrics: async () => {
      try {
        const [bloodPressure, metrics] = await Promise.all([
          backendApi.getMyBloodPressureRecent(currentUserId),
          backendApi.getMyRecentMetrics(currentUserId)
        ]);
        return ok<PersonalHealthMetricsData>({ bloodPressure, metrics, source: "api" });
      } catch (error) {
        return fail<PersonalHealthMetricsData>(error);
      }
    },
    getPersonalArchiveRecentRecords: async () => {
      try {
        const [alerts, bloodPressure, documents, medicalEvents, metrics, symptoms] = await Promise.all([
          backendApi.getMyAlerts(currentUserId),
          backendApi.getMyBloodPressureRecent(currentUserId, 365),
          backendApi.listMyDocuments(currentUserId),
          backendApi.listMyMedicalEvents(currentUserId),
          backendApi.getMyRecentMetrics(currentUserId, 365),
          backendApi.getMyRecentSymptoms(currentUserId, 365)
        ]);
        return ok<PersonalArchiveRecentRecordsData>({ alerts, bloodPressure, documents, medicalEvents, metrics, source: "api", symptoms });
      } catch (error) {
        return fail<PersonalArchiveRecentRecordsData>(error);
      }
    },
    createHealthMetric: async (input: HealthMetricCreateInput | BloodPressureCreateInput) => {
      try {
        if ("systolic" in input) {
          return ok(await backendApi.createMyBloodPressure(input, currentUserId));
        }
        return ok(await backendApi.createMyMetric(input, currentUserId));
      } catch (error) {
        return fail<HealthMetricRecord | BloodPressureRecord>(error);
      }
    },
    previewHealthDataImport: async (rows: ImportPreviewRow[]) => {
      try {
        return ok<ImportPreviewResult>(await backendApi.previewMyHealthDataImport(currentUserId, rows));
      } catch (error) {
        return fail<ImportPreviewResult>(error);
      }
    },
    confirmHealthDataImport: async (rows: ImportPreviewRow[]) => {
      try {
        return ok<ImportPreviewResult>(await backendApi.confirmMyHealthDataImport(currentUserId, rows));
      } catch (error) {
        return fail<ImportPreviewResult>(error);
      }
    },
    runDailyHealthBrief: async (targetUserId = currentUserId, familyId?: string) => {
      try {
        return ok(await backendApi.runDailyHealthBrief({ currentUserId, familyId, targetUserId }));
      } catch (error) {
        return fail<AgentRunResponse>(error);
      }
    },
    getLatestDailyHealthBrief: async () => {
      try {
        return ok<LatestDailyHealthBrief | null>(await backendApi.getLatestDailyHealthBrief(currentUserId));
      } catch (error) {
        return fail<LatestDailyHealthBrief | null>(error);
      }
    },
    runChatHealthQuery: async (input: ChatHealthQueryInput) => {
      try {
        return ok(await backendApi.runChatHealthQuery({ ...input, currentUserId }));
      } catch (error) {
        return fail<AgentRunResponse>(error);
      }
    },
    createSymptomDraftPreview: async (input: SymptomDraftInput) => {
      try {
        return ok(await backendApi.createSymptomDraftPreview({ ...input, currentUserId }));
      } catch (error) {
        return fail<AgentRunResponse>(error);
      }
    },
    createSymptomDraftConfirmed: async (input: SymptomDraftInput) => {
      try {
        return ok(await backendApi.createSymptomDraftConfirmed({ ...input, currentUserId }));
      } catch (error) {
        return fail<AgentRunResponse>(error);
      }
    },
    createMedicalEventDraftPreview: async (input: MedicalEventDraftInput) => {
      try {
        return ok(await backendApi.createMedicalEventDraftPreview({ ...input, currentUserId }));
      } catch (error) {
        return fail<AgentRunResponse>(error);
      }
    },
    createMedicalEventDraftConfirmed: async (input: MedicalEventDraftInput) => {
      try {
        return ok(await backendApi.createMedicalEventDraftConfirmed({ ...input, currentUserId }));
      } catch (error) {
        return fail<AgentRunResponse>(error);
      }
    },
    createAlertPreview: async (input: AlertCreateInput) => {
      try {
        return ok(await backendApi.createAlertPreview({ ...input, currentUserId }));
      } catch (error) {
        return fail<AgentRunResponse>(error);
      }
    },
    createAlertConfirmed: async (input: AlertCreateInput) => {
      try {
        return ok(await backendApi.createAlertConfirmed({ ...input, currentUserId }));
      } catch (error) {
        return fail<AgentRunResponse>(error);
      }
    },
    listDocuments: async () => {
      try {
        return ok({ items: await backendApi.listMyDocuments(currentUserId), mockSections: [], source: "api" as const });
      } catch (error) {
        return fail(error);
      }
    },
    getDocumentPipelineDetail: async (documentId: string): Promise<ApiResult<DocumentPipelineDetail>> => {
      try {
        const [document, jobs, extractionResults] = await Promise.all([
          backendApi.getMyDocument(documentId, currentUserId),
          backendApi.listMyDocumentJobs(documentId, currentUserId).catch(() => []),
          backendApi.listMyExtractionResults(documentId, currentUserId).catch(() => [])
        ]);
        return ok({ document, extractionResults, jobs, mockSections: [], source: "api" });
      } catch (error) {
        return fail<DocumentPipelineDetail>(error);
      }
    },
    createDocumentOcrJob: async (documentId: string) => {
      try {
        return ok(await backendApi.createMyDocumentOcrJob(documentId, currentUserId));
      } catch (error) {
        return fail(error);
      }
    },
    runMockOcr: async (jobId: string) => {
      try {
        return ok(await backendApi.runMyMockOcr(jobId, currentUserId));
      } catch (error) {
        return fail(error);
      }
    },
    getAgentRun: async (id: string): Promise<ApiResult<AgentRunDetail>> => {
      try {
        const [run, toolCalls, safetyChecks] = await Promise.all([
          backendApi.getAgentRun(id, currentUserId),
          backendApi.getAgentRunToolCalls(id, currentUserId),
          backendApi.getAgentRunSafetyChecks(id, currentUserId)
        ]);
        return ok({
          generated_content: run.output_summary ?? "系统内暂无可展示摘要。",
          safety_checks: safetyChecks,
          completed_at: run.ended_at,
          created_at: run.started_at,
          status: run.status,
          source: run.source,
          tool_calls: toolCalls,
          trace_id: run.trace_id,
          workflow_type: run.workflow_type
        });
      } catch (error) {
        return fail<AgentRunDetail>(error);
      }
    },
    listAgentSessions: async () => {
      try {
        return ok(await backendApi.listAgentSessions(currentUserId));
      } catch (error) {
        return fail<AgentSessionSummary[]>(error);
      }
    },
    listAgentSessionMessages: async (sessionId: string) => {
      try {
        return ok(await backendApi.listAgentSessionMessages(sessionId, currentUserId));
      } catch (error) {
        return fail<AgentMessageSummary[]>(error);
      }
    },
    listAgentMemory: async () => {
      try {
        return ok(await backendApi.listAgentMemory(currentUserId));
      } catch (error) {
        return fail<AgentMemoryItem[]>(error);
      }
    },
    deleteAgentMemory: async (memoryId: string) => {
      try {
        return ok(await backendApi.deleteAgentMemory(memoryId, currentUserId));
      } catch (error) {
        return fail<{ deleted: boolean }>(error);
      }
    }
  };
}
