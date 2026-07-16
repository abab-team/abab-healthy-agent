import { useCallback, useEffect, useState } from "react";
import {
  getAuthSessionSnapshot,
  loginWithPassword,
  logoutStoredAuthSession,
  registerWithPassword,
  subscribeAuthSession,
  tokenPreview
} from "@/lib/authSession";
import type { AuthSession } from "@/types/api";

export function useAuthSession() {
  const [session, setSession] = useState<AuthSession | null>(() => getAuthSessionSnapshot());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => subscribeAuthSession(() => setSession(getAuthSessionSnapshot())), []);

  const login = useCallback(async (email: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      const nextSession = await loginWithPassword(email, password);
      setSession(nextSession);
      return nextSession;
    } catch (loginError) {
      const message = loginError instanceof Error ? loginError.message : "登录失败。";
      setError(message);
      throw loginError;
    } finally {
      setLoading(false);
    }
  }, []);

  const logout = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      await logoutStoredAuthSession();
      setSession(null);
    } catch (logoutError) {
      const message = logoutError instanceof Error ? logoutError.message : "退出登录失败。";
      setError(message);
    } finally {
      setLoading(false);
    }
  }, []);

  const register = useCallback(async (email: string, password: string, nickname?: string) => {
    setLoading(true);
    setError(null);
    try {
      const nextSession = await registerWithPassword(email, password, nickname);
      setSession(nextSession);
      return nextSession;
    } catch (registerError) {
      const message = registerError instanceof Error ? registerError.message : "注册失败。";
      setError(message);
      throw registerError;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    accessTokenPreview: tokenPreview(session?.access_token),
    error,
    loading,
    login,
    logout,
    register,
    refreshTokenStored: Boolean(session?.refresh_token),
    session,
    user: session?.user ?? null
  };
}
