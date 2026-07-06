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

export type ReminderSummary = {
  id: string;
  title: string;
  time: string;
  member: string;
  note: string;
};

export type AgentWorkflowType =
  | "daily_health_brief"
  | "symptom_draft_create"
  | "medical_event_draft_create"
  | "alert_create";

export type AgentRunRequest = {
  target_user_id: string;
  family_id?: string;
  workflow_type: AgentWorkflowType;
  user_message: string;
  confirmation?: boolean;
  workflow_payload?: Record<string, unknown>;
  source?: string;
  tool_name?: never;
  input_data?: never;
};

export type AgentRunResponse = {
  trace_id: string;
  status: "completed" | "blocked" | "failed" | "preview";
  workflow_type: AgentWorkflowType;
  message?: string;
  blocked?: boolean;
  safety_level?: string;
  tool_calls_count?: number;
  generated_content: string;
};

export type AgentRunDetail = AgentRunResponse & {
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
