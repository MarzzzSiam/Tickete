import { getApiHealth } from "@/lib/api";

export async function GET() {
  try {
    return Response.json(await getApiHealth(), {
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return Response.json(
      {
        error: {
          code: "api_unavailable",
          message: "The backend is not available.",
          fields: {},
        },
      },
      { status: 503, headers: { "Cache-Control": "no-store" } },
    );
  }
}
