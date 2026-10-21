"use client";

export type Profile = {
  id: string;
  email: string;
  full_name: string;
  phone: string;
  role: "buyer" | "organizer" | "admin";
  email_verified: boolean;
};

export class AccountError extends Error {
  constructor(
    message: string,
    public status: number,
    public fields: Record<string, string> = {},
  ) {
    super(message);
  }
}

const base = (
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

export async function downloadTickets(orderId: string, token: string) {
  const run = () =>
    fetch(`${base}/orders/${orderId}/tickets.pdf`, {
      credentials: "include",
      cache: "no-store",
      headers: { "X-Checkout-Token": token },
      signal: AbortSignal.timeout(30000),
    });
  let response = await run();
  if (response.status === 401) {
    await refresh();
    response = await run();
  }
  if (!response.ok)
    throw new AccountError(
      "Tickets are not ready to download. Refresh order status and try again.",
      response.status,
    );
  return response.blob();
}

async function request<T>(
  path: string,
  method = "GET",
  body?: unknown,
  csrf?: string,
  checkoutToken?: string,
): Promise<T> {
  let response: Response;
  try {
    const [route, query] = path.split("?");
    response = await fetch(`${base}/${route}/${query ? `?${query}` : ""}`, {
      method,
      credentials: "include",
      cache: "no-store",
      signal: AbortSignal.timeout(15000),
      headers: {
        ...(body && !(body instanceof FormData)
          ? { "Content-Type": "application/json" }
          : {}),
        ...(csrf ? { "X-CSRFToken": csrf } : {}),
        ...(checkoutToken ? { "X-Checkout-Token": checkoutToken } : {}),
      },
      body:
        body instanceof FormData
          ? body
          : body
            ? JSON.stringify(body)
            : undefined,
    });
  } catch {
    throw new AccountError(
      "We couldn’t reach the account service. Check your connection and try again.",
      0,
    );
  }
  if (!response.ok) {
    const payload = await response.json().catch(() => null);
    const fields: Record<string, string> = {};
    for (const [key, value] of Object.entries(payload?.error?.fields || {})) {
      if (Array.isArray(value)) fields[key] = value.join(" ");
      else if (typeof value === "string") fields[key] = value;
    }
    const message =
      response.status === 429
        ? "Too many attempts. Please wait before trying again."
        : response.status === 503
          ? "The account service is temporarily unavailable. Please try again later."
          : payload?.error?.message ||
            "We couldn’t complete that request. Please try again.";
    throw new AccountError(message, response.status, fields);
  }
  return response.status === 204 ? (undefined as T) : response.json();
}

async function write<T>(
  path: string,
  method: string,
  body?: unknown,
  checkoutToken?: string,
): Promise<T> {
  // Fetch afresh because login and refresh rotate the CSRF cookie.
  const { csrf_token } = await request<{ csrf_token: string }>("auth/csrf");
  return request<T>(path, method, body, csrf_token, checkoutToken);
}

let refreshing: Promise<Profile> | undefined;
async function refresh(): Promise<Profile> {
  if (!refreshing) {
    refreshing = write<Profile>("auth/refresh", "POST").finally(() => {
      refreshing = undefined;
    });
  }
  return refreshing;
}

async function performAccountRequest<T>(
  path: string,
  method = "GET",
  body?: unknown,
  authenticated = false,
  checkoutToken?: string,
): Promise<T> {
  const run = () =>
    method === "GET"
      ? request<T>(path, method, undefined, undefined, checkoutToken)
      : write<T>(path, method, body, checkoutToken);
  try {
    return await run();
  } catch (error) {
    if (
      !(error instanceof AccountError) ||
      error.status !== 401 ||
      !authenticated
    )
      throw error;
    await refresh();
    return run();
  }
}

export async function apiRequest<T>(
  path: string,
  method = "GET",
  body?: unknown,
  authenticated = false,
  checkoutToken?: string,
): Promise<T> {
  const run = () =>
    performAccountRequest<T>(path, method, body, authenticated, checkoutToken);
  // Serialize cookie rotations and CSRF bootstrap/write pairs across tabs.
  // A waiting tab retries its original request with the newly rotated cookies.
  if (typeof navigator !== "undefined" && navigator.locks) {
    return navigator.locks.request("tickete-account-session", run);
  }
  return run();
}

export function accountRequest<T>(
  path: string,
  method = "GET",
  body?: unknown,
  authenticated = false,
): Promise<T> {
  return apiRequest<T>(`auth/${path}`, method, body, authenticated);
}
