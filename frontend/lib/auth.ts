import type { LoginResponse } from "@/lib/types";

let accessTokenMemory: string | null = null;

export function saveTokens(tokens: LoginResponse): void {
  accessTokenMemory = tokens.access_token;
}

export function getAccessToken(): string | null {
  return accessTokenMemory;
}

export function clearTokens(): void {
  accessTokenMemory = null;
}

export function hasToken(): boolean {
  return Boolean(accessTokenMemory);
}