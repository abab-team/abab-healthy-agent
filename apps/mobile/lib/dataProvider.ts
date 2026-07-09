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
  AlertCreateInput,
  ArchiveTrends,
  ApiFamilyOverview,
  ApiMemberDetail,
  ApiResult,
  ChatHealthQueryInput,
  DocumentPipelineDetail,
  HealthStatus,
  ImportPreviewResult,
  ImportPreviewRow,
  MedicalEventDraftInput,
  SymptomDraftInput
} from "@/types/api";

function ok<T>(data: T): ApiResult<T> {
  return { ok: true, data };
}

function fail<T>(error: unknown): ApiResult<T> {
  const message = error instanceof Error ? error.message : "请求失败，请检查 API 配置。";
  const code = error && typeof error === "object" && "code" in error ? String((error as { code: unknown }).code) : "request_failed";
  return { ok: false, error: { code, message } };
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
      getArchiveTrends: async () => mockApi.getArchiveTrends(),
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
      runChatHealthQuery: async (input: ChatHealthQueryInput) =>
        ok<AgentRunResponse>({
          generated_content: `根据演示数据，已收到你的问题：“${input.question}”。当前演示回答只整理系统内记录示例，不用于医疗判断。如有明显不适或紧急情况，请联系医生或当地急救服务。`,
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
    getMemberDetail: (id: string) => getApiMemberDetail(id, currentUserId),
    getArchiveTrends: async () => {
      try {
        return ok<ArchiveTrends>(await backendApi.getMyArchiveTrends(currentUserId));
      } catch (error) {
        return fail<ArchiveTrends>(error);
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
