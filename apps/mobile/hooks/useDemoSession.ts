import { apiBaseUrl, dataMode, defaultDemoUserId, demoUsers } from "@/lib/apiConfig";

export function useDemoSession() {
  return {
    apiBaseUrl,
    currentUserId: defaultDemoUserId,
    dataMode,
    demoUsers
  };
}
