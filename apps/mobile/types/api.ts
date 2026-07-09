export type ApiResult<T> = {
  ok: boolean;
  data?: T;
  error?: {
    code: string;
    message: string;
  };
};

export type CurrentUser = {
  id: string;
  name: string;
  nickname?: string;
  current_family_id?: string;
};

export type Family = {
  id: string;
  name: string;
  owner_user_id: string;
};

export type FamilyMember = {
  id: string;
  family_id: string;
  user_id: string;
  display_name: string;
  relationship_label: string;
  share_status: string;
};

export type HealthProfile = {
  user_id: string;
  display_name: string;
  summary: string;
};

export type BloodPressureRecord = {
  id: string;
  user_id: string;
  recorded_at: string;
  systolic: number;
  diastolic: number;
};

export type SymptomRecord = {
  id: string;
  user_id: string;
  title: string;
  summary: string;
  recorded_at: string;
};

export type DraftStatus = "pending" | "confirmed" | "later";

export type HealthRecordDraft = {
  id: string;
  target_user_id: string;
  title: string;
  summary: string;
  status: DraftStatus;
};

export type MedicalEventDraft = {
  id: string;
  target_user_id: string;
  title: string;
  summary: string;
  status: DraftStatus;
};

export type Alert = {
  id: string;
  target_user_id: string;
  title: string;
  reminder_type: string;
  scheduled_at: string;
  status: "preview" | "created" | "active";
};

export type MedicalDocument = {
  id: string;
  title: string;
  file_name: string;
  file_mime_type?: string | null;
  file_size?: number | null;
  ai_extract_status: string;
  created_at?: string | null;
};

export type DocumentProcessingJob = {
  id: string;
  document_id: string;
  job_type: string;
  status: string;
  error_message?: string | null;
  created_at?: string | null;
};

export type DocumentExtractionResult = {
  id: string;
  document_id: string;
  processing_job_id?: string | null;
  ai_summary?: string | null;
  key_findings?: Record<string, unknown>[] | null;
  suggested_events?: Record<string, unknown>[] | null;
  safety_notes?: string[] | null;
  status: string;
  raw_text_excerpt?: string | null;
};

export type DocumentPipelineDetail = {
  document: MedicalDocument;
  jobs: DocumentProcessingJob[];
  extractionResults: DocumentExtractionResult[];
  source: DataMode;
  mockSections: string[];
};

export type ReminderSummary = {
  id: string;
  title: string;
  time: string;
  member: string;
  note: string;
};

export type AgentWorkflowType =
  | "chat"
  | "daily_health_brief"
  | "symptom_draft_create"
  | "medical_event_draft_create"
  | "alert_create";

type AgentRunBaseRequest = {
  target_user_id: string;
  family_id?: string;
  session_id?: string;
  user_message: string;
  confirmation?: boolean;
  source?: string;
  tool_name?: never;
  input_data?: never;
};

export type SymptomDraftWorkflowPayload = {
  raw_text: string;
  target_display_name?: string;
  missing_fields?: string[];
  safety_flags?: string[];
};

export type MedicalEventDraftWorkflowPayload = {
  title?: string;
  draft_title?: string;
  summary: string;
  extracted_text_preview?: string;
  structured_hints?: Record<string, unknown>;
  draft_event_type?: string;
  event_date?: string;
  hospital_or_org?: string;
  department?: string;
  missing_fields?: string[];
  safety_flags?: string[];
};

export type AlertCreateWorkflowPayload = {
  title: string;
  message: string;
  alert_type?: string;
  level?: string;
  suggested_action?: string;
  trigger_reason?: string;
  due_at?: string;
  remind_at?: string;
  scheduled_at?: string;
  source?: string;
};

export type AgentRunRequest =
  | (AgentRunBaseRequest & {
      workflow_type: "daily_health_brief";
      workflow_payload?: never;
    })
  | (AgentRunBaseRequest & {
      workflow_type: "chat";
      workflow_payload?: never;
    })
  | (AgentRunBaseRequest & {
      workflow_type: "symptom_draft_create";
      workflow_payload: SymptomDraftWorkflowPayload;
    })
  | (AgentRunBaseRequest & {
      workflow_type: "medical_event_draft_create";
      workflow_payload: MedicalEventDraftWorkflowPayload;
    })
  | (AgentRunBaseRequest & {
      workflow_type: "alert_create";
      workflow_payload: AlertCreateWorkflowPayload;
    });

export type AgentRunResponse = {
  trace_id: string;
  session_id?: string | null;
  status: "completed" | "blocked" | "failed" | "preview";
  workflow_type: AgentWorkflowType;
  message?: string;
  blocked?: boolean;
  safety_level?: string;
  tool_calls_count?: number;
  generated_content: string;
};

export type AgentRunDetail = AgentRunResponse & {
  completed_at?: string | null;
  created_at?: string | null;
  source?: string | null;
  tool_calls: AgentToolCallSummary[];
  safety_checks: AgentSafetyCheckSummary[];
};

export type AgentToolCallSummary = {
  id: string;
  name: string;
  status: "completed" | "blocked" | "failed";
  summary: string;
};

export type AgentSafetyCheckSummary = {
  id: string;
  stage: "input" | "output";
  status: "passed" | "caution" | "blocked";
  summary: string;
};

export type DataMode = "mock" | "api";

export type AuthMode = "demo" | "auth";

export type AuthUser = {
  id: string;
  email?: string | null;
  nickname?: string | null;
};

export type AuthSession = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_at: number;
  user: AuthUser;
};

export type HealthStatus = {
  status: string;
  service: string;
};

export type ApiFamilyOverview = {
  family: Family;
  members: FamilyMember[];
  reminders: ReminderSummary[];
  source: DataMode;
  mockSections: string[];
};

export type ApiMemberDetail = {
  member: FamilyMember;
  profile?: HealthProfile;
  bloodPressureSummary?: Record<string, unknown>;
  symptomSummary?: Record<string, unknown>;
  activeAlerts?: Alert[];
  source: DataMode;
  mockSections: string[];
};

export type ControlledWorkflowInput = {
  targetUserId: string;
  familyId?: string;
};

export type SymptomDraftInput = ControlledWorkflowInput & {
  description: string;
  targetDisplayName?: string;
};

export type MedicalEventDraftInput = ControlledWorkflowInput & {
  title: string;
  summary: string;
  eventType?: string;
  eventDate?: string;
  hospitalOrOrg?: string;
  department?: string;
};

export type AlertCreateInput = ControlledWorkflowInput & {
  title: string;
  message: string;
  alertType?: string;
  level?: string;
  scheduledAt?: string;
};

export type ChatHealthQueryInput = ControlledWorkflowInput & {
  question: string;
  sessionId?: string | null;
};

export type AgentSessionSummary = {
  id: string;
  family_id?: string | null;
  title?: string | null;
  last_active_at: string;
  created_at: string;
};

export type AgentMessageSummary = {
  id: string;
  role: "user" | "assistant" | string;
  content_summary: string;
  intent?: string | null;
  member_label?: string | null;
  metric_type?: string | null;
  time_range_label?: string | null;
  time_range_days?: number | null;
  tool_name?: string | null;
  created_at: string;
};

export type AgentMemoryItem = {
  id: string;
  family_id?: string | null;
  memory_type: string;
  content: string;
  confidence: number;
  source: string;
  is_user_editable: boolean;
  created_at: string;
  updated_at: string;
};
