"use client";

import { accountRequest, AccountError } from "./auth-api";
const base = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

export async function recoveryRequest<T>(
  path: string,
  method = "GET",
  body?: unknown,
  token?: string,
  pdf = false,
): Promise<T> {
  const csrf =
    method === "POST"
      ? await accountRequest<{ csrf_token: string }>("csrf")
      : null;
  const response = await fetch(`${base}/tickets/recovery/${path}`, {
    method,
    credentials: "include",
    cache: "no-store",
    signal: AbortSignal.timeout(30000),
    headers: {
      ...(body ? { "Content-Type": "application/json" } : {}),
      ...(csrf ? { "X-CSRFToken": csrf.csrf_token } : {}),
      ...(token ? { "X-Recovery-Token": token } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const data = await response.json().catch(() => null);
    throw new AccountError(
      response.status === 429
        ? "Too many requests. Please wait before trying again."
        : data?.error?.message ||
            data?.detail ||
            "Recovery could not complete. Please retry.",
      response.status,
    );
  }
  return (pdf ? response.blob() : response.json()) as Promise<T>;
}
