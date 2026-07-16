import { apiBaseUrl } from "@/lib/apiConfig";
import type { AuthSession, AuthUser } from "@/types/api";

type AuthTokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
  user: AuthUser;
};

type Listener = () => void;

const STORAGE_KEY = "family-health-agent.auth-session.v1";
const listeners = new Set<Listener>();
let memorySession: AuthSession | null = null;
let loaded = false;

function requireBaseUrl(): string {
  if (!apiBaseUrl) {
    throw new Error("API Base URL 未配置，无法登录。");
  }
  return apiBaseUrl;
}

function storage(): Storage | null {
  try {
    if (typeof globalThis.localStorage === "undefined") {
      return null;
    }
    return globalThis.localStorage;
  } catch {
    return null;
  }
}

function normalizeSession(response: AuthTokenResponse): AuthSession {
  const expiresInMs = Math.max(response.expires_in - 30, 1) * 1000;
  return {
    access_token: response.access_token,
    expires_at: Date.now() + expiresInMs,
    refresh_token: response.refresh_token,
    token_type: "bearer",
    user: response.user
  };
}

function emit() {
  listeners.forEach((listener) => listener());
}

export function subscribeAuthSession(listener: Listener): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}

export function loadStoredAuthSession(): AuthSession | null {
  if (loaded) {
    return memorySession;
  }
  loaded = true;
  const stored = storage()?.getItem(STORAGE_KEY);
  if (!stored) {
    memorySession = null;
    return null;
  }
  try {
    memorySession = JSON.parse(stored) as AuthSession;
  } catch {
    memorySession = null;
    storage()?.removeItem(STORAGE_KEY);
  }
  return memorySession;
}

export function getAuthSessionSnapshot(): AuthSession | null {
  return loadStoredAuthSession();
}

export function setAuthSession(session: AuthSession | null): void {
  memorySession = session;
  loaded = true;
  if (session) {
    storage()?.setItem(STORAGE_KEY, JSON.stringify(session));
  } else {
    storage()?.removeItem(STORAGE_KEY);
  }
  emit();
}

export async function loginWithPassword(email: string, password: string): Promise<AuthSession> {
  return authenticateWithPassword("login", { email, password });
}

export async function registerWithPassword(email: string, password: string, nickname?: string): Promise<AuthSession> {
  return authenticateWithPassword("register", { email, nickname, password });
}

async function authenticateWithPassword(endpoint: "login" | "register", body: Record<string, string | undefined>): Promise<AuthSession> {
  const response = await fetch(`${requireBaseUrl()}/api/v1/auth/${endpoint}`, {
    body: JSON.stringify(body),
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(safeAuthError(payload));
  }
  const session = normalizeSession(payload as AuthTokenResponse);
  setAuthSession(session);
  return session;
}

export async function refreshStoredAuthSession(): Promise<AuthSession | null> {
  const current = getAuthSessionSnapshot();
  if (!current?.refresh_token) {
    return null;
  }
  const response = await fetch(`${requireBaseUrl()}/api/v1/auth/refresh`, {
    body: JSON.stringify({ refresh_token: current.refresh_token }),
    headers: {
      Accept: "application/json",
      "Content-Type": "application/json"
    },
    method: "POST"
  });
  const payload = await response.json();
  if (!response.ok) {
    setAuthSession(null);
    return null;
  }
  const session = normalizeSession(payload as AuthTokenResponse);
  setAuthSession(session);
  return session;
}

export async function logoutStoredAuthSession(): Promise<void> {
  const current = getAuthSessionSnapshot();
  if (current?.refresh_token) {
    await fetch(`${requireBaseUrl()}/api/v1/auth/logout`, {
      body: JSON.stringify({ access_token: current.access_token, refresh_token: current.refresh_token }),
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json"
      },
      method: "POST"
    }).catch(() => undefined);
  }
  setAuthSession(null);
}

export function getAccessTokenForRequest(): string | null {
  const session = getAuthSessionSnapshot();
  return session?.access_token ?? null;
}

export function shouldRefreshAuthSession(): boolean {
  const session = getAuthSessionSnapshot();
  return Boolean(session && session.expires_at <= Date.now());
}

export function tokenPreview(value: string | null | undefined): string {
  if (!value) {
    return "未登录";
  }
  return `${value.slice(0, 8)}...${value.slice(-6)}`;
}

function safeAuthError(payload: unknown): string {
  const detail = (payload as { detail?: { message?: string } })?.detail;
  return detail?.message ?? "操作未完成，请检查填写的信息后重试。";
}
