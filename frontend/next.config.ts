import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  devIndicators: false,
  poweredByHeader: false,
  skipTrailingSlashRedirect: true,
  // Keep browser auth cookies first-party when API and UI use different hosts.
  // API_BASE_URL remains absolute for server-rendered event requests.
  async rewrites() {
    const origin = process.env.BACKEND_ORIGIN?.replace(/\/$/, "");
    if (!origin) return [];
    if (!origin.startsWith("https://")) {
      throw new Error("BACKEND_ORIGIN must use HTTPS");
    }
    return [
      {
        source: "/api/v1/orders/:id/tickets.pdf",
        destination: `${origin}/api/v1/orders/:id/tickets.pdf`,
      },
      // Next's wildcard omits the incoming trailing slash. Django endpoints
      // require it, so include it explicitly to avoid redirect loops on POST.
      { source: "/api/:path*", destination: `${origin}/api/:path*/` },
    ];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
          {
            key: "Permissions-Policy",
            value: "camera=(self), microphone=(), geolocation=()",
          },
        ],
      },
    ];
  },
};
export default nextConfig;
