import type { DataMode } from "@/types/api";

function envValue(name: string): string | undefined {
  const value = process.env[name];
  return value && value.trim().length > 0 ? value.trim() : undefined;
}

export const dataMode: DataMode = envValue("EXPO_PUBLIC_DATA_MODE") === "api" ? "api" : "mock";

export const apiBaseUrl = (envValue("EXPO_PUBLIC_API_BASE_URL") ?? "").replace(/\/+$/, "");

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

export const defaultDemoUserId = envValue("EXPO_PUBLIC_DEMO_USER_ID") ?? demoUsers[0].id;
