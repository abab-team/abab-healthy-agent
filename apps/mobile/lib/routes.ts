import type { Href } from "expo-router";
export const routes = {
  home: "/" as Href,
  family: "/family" as Href,
  agent: "/agent" as Href,
  settings: "/settings" as Href,
  drafts: "/drafts" as Href,
  agentBrief: "/agent-brief" as Href,
  createSymptomDraft: "/create-symptom-draft" as Href,
  createAlert: "/create-alert" as Href,
  createHealthEventDraft: "/create-health-event-draft" as Href,
  inviteMember: "/invite-member" as Href,
  permissionSettings: "/permission-settings" as Href,
  member: (id: string) => `/member/${id}` as Href,
  agentRun: (id: string) => `/agent-run/${id}` as Href,
  activity: (id: string) => `/activity/${id}` as Href
};
