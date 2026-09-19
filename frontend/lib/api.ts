import {
  clearTokens,
  getAccessToken,
  saveTokens,
} from "@/lib/auth";
import type { LoginResponse, User } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1";

type ApiError = {
  error?: { message?: string };
  detail?: string | Array<{ msg?: string }>;
};

function getApiErrorMessage(body: ApiError, status: number): string {
  if (body.error?.message) return body.error.message;
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail)) {
    const messages = body.detail.map((e) => e.msg).filter(Boolean);
    if (messages.length) return messages.join(", ");
  }
  return `Request failed with HTTP ${status}`;
}

let refreshPromise: Promise<LoginResponse> | null = null;

async function refreshTokens(): Promise<LoginResponse> {
  if (!refreshPromise) {
    refreshPromise = (async () => {
      const response = await fetch(
        `${API_BASE_URL}/auth/refresh`,
        {
          method: "POST",
          credentials: "same-origin",
          headers: {
            "Content-Type": "application/json",
          },
        }
      );

      if (!response.ok) {
        clearTokens();
        throw new Error("Session expired.");
      }

      const tokens = (await response.json()) as LoginResponse;

      saveTokens(tokens);

      return tokens;
    })().finally(() => {
      refreshPromise = null;
    });
  }

  return refreshPromise;
}

/** Shared by api + domainApi */
export async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  token?: string | null,
  allowRefresh = true,
): Promise<T> {
  const headers = new Headers(options.headers);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }

  const access = token === undefined ? getAccessToken() : token;
  if (access) headers.set("Authorization", `Bearer ${access}`);

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers,
    credentials: "same-origin",
  });

  if (response.status === 401 && allowRefresh && path !== "/auth/refresh" && path !== "/auth/login") {
    try {
      const refreshed = await refreshTokens();
      return apiRequest<T>(path, options, refreshed.access_token, false);
    } catch {
      clearTokens();
      throw new Error("Authentication required.");
    }
  }

  if (!response.ok) {
    let body: ApiError = {};
    try {
      body = await response.json();
    } catch {
      /* ignore */
    }
    throw new Error(getApiErrorMessage(body, response.status));
  }

  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}

class ApiClient {
  login(email: string, password: string) {
    return apiRequest<LoginResponse>(
      "/auth/login",
      {
        method: "POST",
        body: JSON.stringify({
          email,
          password,
        }),
      },
      null,
      false,
    ).then((tokens) => {
      saveTokens(tokens);
      return tokens;
    });
  }

  refresh() {
    return refreshTokens();
  }

  async logout(): Promise<void> {
    try {
      await apiRequest<void>(
        "/auth/logout",
        {
          method: "POST",
        },
        null,
        false,
      );
    } finally {
      clearTokens();
    }
  }

  me(): Promise<User> {
    return apiRequest<User>("/auth/me");
  }
}

export const api = new ApiClient();