import { apiBaseUrl, apiModeWarnings, authMode, dataMode, defaultDemoUserId, demoUsers } from "@/lib/apiConfig";
import { useAuthSession } from "@/hooks/useAuthSession";

export function useDemoSession() {
  const authSession = useAuthSession();
  const authUserId = authSession.user?.id;
  return {
    apiBaseUrl,
    authMode,
    authSession,
    currentUserId: authMode === "auth" && authUserId ? authUserId : defaultDemoUserId,
    dataMode,
    demoUsers,
    isAuthenticated: authMode !== "auth" || Boolean(authUserId),
    warnings: apiModeWarnings
  };
}
