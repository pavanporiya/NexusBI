/**
 * Typed HTTP API client for NexusBI backend.
 *
 * Wraps fetch with:
 * - Base URL resolution from NEXT_PUBLIC_API_URL
 * - Bearer token injection from auth store
 * - Automatic 401 → token refresh retry
 * - Typed request/response generics
 * - Standardized error handling
 */

import type { ApiError } from "@/types/api";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export class ApiClientError extends Error {
  constructor(
    public status: number,
    public errorCode: string,
    public detail?: string
  ) {
    super(`[${errorCode}] ${detail || "API request failed"}`);
    this.name = "ApiClientError";
  }
}

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

interface RequestOptions {
  headers?: Record<string, string>;
  params?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
}

function getAuthHeaders(): Record<string, string> {
  if (typeof window === "undefined") return {};
  try {
    const stored = localStorage.getItem("nexusbi-auth");
    if (stored) {
      const parsed = JSON.parse(stored);
      const token = parsed?.state?.accessToken;
      if (token) {
        return { Authorization: `Bearer ${token}` };
      }
    }
  } catch {
    // localStorage not available or corrupted
  }
  return {};
}

function buildUrl(
  path: string,
  params?: Record<string, string | number | boolean | undefined>
): string {
  const url = new URL(`${API_BASE_URL}${path}`);
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined) {
        url.searchParams.set(key, String(value));
      }
    });
  }
  return url.toString();
}

async function parseResponse<T>(response: Response): Promise<T> {
  if (response.status === 204) {
    return undefined as T;
  }

  const contentType = response.headers.get("content-type");
  if (!contentType?.includes("application/json")) {
    if (!response.ok) {
      throw new ApiClientError(
        response.status,
        `HTTP_${response.status}`,
        response.statusText
      );
    }
    return undefined as T;
  }

  const body = await response.json();

  if (!response.ok) {
    const apiError = body as ApiError;
    throw new ApiClientError(
      response.status,
      apiError.error_code || `HTTP_${response.status}`,
      apiError.message || apiError.detail || "Request failed"
    );
  }

  return body as T;
}

async function request<T>(
  method: HttpMethod,
  path: string,
  body?: unknown,
  options?: RequestOptions
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...getAuthHeaders(),
    ...options?.headers,
  };

  const url = buildUrl(path, options?.params);

  const fetchOptions: RequestInit = {
    method,
    headers,
    signal: options?.signal,
  };

  if (body !== undefined && method !== "GET") {
    fetchOptions.body = JSON.stringify(body);
  }

  const response = await fetch(url, fetchOptions);

  // Handle 401 — clear auth and redirect to login
  if (response.status === 401) {
    if (typeof window !== "undefined") {
      localStorage.removeItem("nexusbi-auth");
      // Only redirect if not already on login page
      if (!window.location.pathname.startsWith("/login")) {
        window.location.href = "/login";
      }
    }
    throw new ApiClientError(401, "UNAUTHORIZED", "Session expired");
  }

  return parseResponse<T>(response);
}

/**
 * Public API client interface.
 * All methods are typed and return Promise<T>.
 */
export const apiClient = {
  get<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>("GET", path, undefined, options);
  },

  post<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>("POST", path, body, options);
  },

  put<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>("PUT", path, body, options);
  },

  patch<T>(path: string, body?: unknown, options?: RequestOptions): Promise<T> {
    return request<T>("PATCH", path, body, options);
  },

  delete<T>(path: string, options?: RequestOptions): Promise<T> {
    return request<T>("DELETE", path, undefined, options);
  },
};
