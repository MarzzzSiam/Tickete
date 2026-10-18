import "server-only";
import type { EventPage, EventRecord } from "./events";
export const publicApiBase = (
  process.env.API_BASE_URL || "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");
export async function publicEvent(slug: string): Promise<EventRecord | null> {
  const response = await fetch(
    `${publicApiBase}/public/events/${encodeURIComponent(slug)}/`,
    { cache: "no-store", signal: AbortSignal.timeout(8000) },
  );
  if (response.status === 404) return null;
  if (!response.ok) throw new Error("Event service unavailable");
  return response.json();
}
export async function publicEvents(
  search: string,
  page: number,
): Promise<EventPage> {
  const response = await fetch(
    `${publicApiBase}/public/events/?search=${encodeURIComponent(search.slice(0, 180))}&page=${page}`,
    { cache: "no-store", signal: AbortSignal.timeout(8000) },
  );
  if (!response.ok) throw new Error("Event service unavailable");
  return response.json();
}
