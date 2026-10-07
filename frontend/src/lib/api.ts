export type HealthResponse = {
  status: "ok";
  service: "tickete-api";
  version: string;
};
export type ApiError = {
  error: { code: string; message: string; fields: Record<string, unknown> };
};

// Server-only use: no credentials or backend service keys belong in client bundles.
export async function getApiHealth(): Promise<HealthResponse> {
  const base = process.env.API_BASE_URL || "http://127.0.0.1:8000/api/v1";
  const response = await fetch(`${base}/health/`, {
    cache: "no-store",
    signal: AbortSignal.timeout(4000),
  });
  if (!response.ok) throw new Error("API health request failed.");
  const body: unknown = await response.json();
  if (
    !body ||
    typeof body !== "object" ||
    !("status" in body) ||
    body.status !== "ok" ||
    !("service" in body) ||
    body.service !== "tickete-api" ||
    !("version" in body) ||
    typeof body.version !== "string"
  )
    throw new Error("Unexpected API health response.");
  return body as HealthResponse;
}
