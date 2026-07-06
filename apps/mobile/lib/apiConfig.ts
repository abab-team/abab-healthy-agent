import type { DataMode } from "@/types/api";

function envValue(name: string): string | undefined {
  const value = process.env[name];
  return value && value.trim().length > 0 ? value.trim() : undefined;
}

export const dataMode: DataMode = envValue("EXPO_PUBLIC_DATA_MODE") === "api" ? "api" : "mock";

export const apiBaseUrl = (envValue("EXPO_PUBLIC_API_BASE_URL") ?? "").replace(/\/+$/, "");
const configuredDemoUserId = envValue("EXPO_PUBLIC_DEMO_USER_ID");

export const demoUsers = [
  {
    id: envValue("EXPO_PUBLIC_DEMO_USER_GALA_ID") ?? "me",
    label: "Gala"
  },
  {
    id: envValue("EXPO_PUBLIC_DEMO_USER_FATHER_ID") ?? "dad",
    label: "爸爸"
  },
  {
    id: envValue("EXPO_PUBLIC_DEMO_USER_MOTHER_ID") ?? "mom",
    label: "妈妈"
  }
] as const;

export const defaultDemoUserId = configuredDemoUserId ?? demoUsers[0].id;

export const apiModeWarnings = [
  ...(dataMode === "api" && !apiBaseUrl ? ["API Base URL 未配置。"] : []),
  ...(dataMode === "api" && !configuredDemoUserId ? ["X-Current-User-Id 未配置，将使用 mock id，真实后端可能拒绝。"] : [])
];
