import { apiBaseUrl } from "@/lib/apiConfig";

type RequestOptions = {
  method?: "GET" | "POST" | "PATCH";
  body?: unknown;
  currentUserId?: string;
};

type BackendErrorDetail =
  | string
  | {
      code?: string;
      message?: string;
      fields?: unknown;
      request_id?: string | null;
    };

export class ApiClientError extends Error {
  code: string;
  status: number;
  fields?: unknown;

  constructor(message: string, options: { code: string; status: number; fields?: unknown }) {
    super(message);
    this.name = "ApiClientError";
    this.code = options.code;
    this.status = options.status;
    this.fields = options.fields;
  }
}

function requireBaseUrl(): string {
  if (!apiBaseUrl) {
    throw new ApiClientError("API mode requires EXPO_PUBLIC_API_BASE_URL.", {
      code: "api_base_url_missing",
      status: 0
    });
  }
  return apiBaseUrl;
}

function buildUrl(path: string): string {
  const normalizedPath = path.startsWith("/") ? path : `/${path}`;
  return `${requireBaseUrl()}${normalizedPath}`;
}

function parseErrorDetail(status: number, payload: unknown): ApiClientError {
  const maybePayload = payload as { detail?: BackendErrorDetail } | undefined;
  const detail = maybePayload?.detail;
  if (typeof detail === "string") {
    return new ApiClientError(detail, { code: "api_error", status });
  }
  if (detail && typeof detail === "object") {
    return new ApiClientError(detail.message ?? "Request failed.", {
      code: detail.code ?? "api_error",
      fields: detail.fields,
      status
    });
  }
  return new ApiClientError("Request failed.", { code: "api_error", status });
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) {
    return null;
  }
  return JSON.parse(text);
}

export const apiClient = {
  async request<T>(path: string, options: RequestOptions = {}): Promise<T> {
    const headers: Record<string, string> = {
      Accept: "application/json"
    };
    if (options.body !== undefined) {
      headers["Content-Type"] = "application/json";
    }
    if (options.currentUserId) {
      headers["X-Current-User-Id"] = options.currentUserId;
    }

    const response = await fetch(buildUrl(path), {
      method: options.method ?? "GET",
      headers,
      body: options.body === undefined ? undefined : JSON.stringify(options.body)
    });
    const payload = await readJson(response);
    if (!response.ok) {
      throw parseErrorDetail(response.status, payload);
    }
    return payload as T;
  },

  get<T>(path: string, currentUserId?: string): Promise<T> {
    return this.request<T>(path, { currentUserId });
  },

  post<T>(path: string, body: unknown, currentUserId?: string): Promise<T> {
    return this.request<T>(path, { body, currentUserId, method: "POST" });
  },

  patch<T>(path: string, body: unknown, currentUserId?: string): Promise<T> {
    return this.request<T>(path, { body, currentUserId, method: "PATCH" });
  }
};
