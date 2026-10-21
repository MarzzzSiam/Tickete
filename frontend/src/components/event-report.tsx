"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { apiRequest, AccountError } from "@/lib/auth-api";
import { dhakaTime } from "@/lib/events";
import { Button, Pill } from "./ui";
import {
  checkoutSessionEvent,
  checkoutSessionKey,
} from "@/lib/checkout-session";

type Report = {
  title: string;
  role: string;
  closed_at: string | null;
  generated_at: string;
  orders: number;
  sold: number;
  revenue: string;
  checked_in: number;
  cancelled: number;
  not_checked_in: number;
  categories: {
    id: string;
    name: string;
    active: boolean;
    capacity: number | null;
    sold: number;
    unsold: number | null;
    checked_in: number;
  }[];
  daily: { day: string; sold: number; revenue: string }[];
};
function Bars({
  title,
  rows,
  money = false,
}: {
  title: string;
  rows: { label: string; value: number }[];
  money?: boolean;
}) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return (
    <section className="card auth-card report-chart">
      <h2>{title}</h2>
      {!rows.length ? (
        <p>No sales yet.</p>
      ) : (
        <ul>
          {rows.map((r, i) => (
            <li key={`${r.label}-${i}`}>
              <div>
                <span>{r.label}</span>
                <strong>{money ? `BDT ${r.value.toFixed(2)}` : r.value}</strong>
              </div>
              <div className="report-bar-track" aria-hidden="true">
                <span style={{ width: `${(r.value / max) * 100}%` }} />
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
export function EventReport({ eventId }: { eventId: string }) {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const load = useCallback(async () => {
    try {
      const data = await apiRequest<Report>(
        `events/${eventId}/dashboard`,
        "GET",
        undefined,
        true,
      );
      setReport(data);
      setError("");
    } catch (e) {
      setReport(null);
      setError(
        e instanceof AccountError ? e.message : "Unable to load the report.",
      );
    }
  }, [eventId]);
  useEffect(() => {
    const timer = setTimeout(() => void load(), 0);
    const poll = setInterval(() => void load(), 30000);
    const reload = () => window.location.reload();
    const storage = (e: StorageEvent) => {
      if (e.key === checkoutSessionKey || e.key === null) reload();
    };
    window.addEventListener(checkoutSessionEvent, reload);
    window.addEventListener("storage", storage);
    return () => {
      clearTimeout(timer);
      clearInterval(poll);
      window.removeEventListener(checkoutSessionEvent, reload);
      window.removeEventListener("storage", storage);
    };
  }, [load]);
  async function close() {
    if (
      !window.confirm(
        "Close this event permanently? This stops sales and check-in, releases unpaid reservations and freezes the final report. This cannot be undone.",
      )
    )
      return;
    setBusy(true);
    try {
      await apiRequest(`events/${eventId}/close`, "POST", {}, true);
      await load();
    } catch (e) {
      setError(
        e instanceof AccountError ? e.message : "Unable to close event.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <main id="main" className="container account-page report-page">
      <Pill>EVENT REPORTING</Pill>
      <h1>{report?.title || "Your event report"}</h1>
      <p>
        <Link href={`/organizer/events/${eventId}/operations`}>
          Back to event operations
        </Link>
      </p>
      {error && (
        <p className="auth-error" role="alert">
          {error}
        </p>
      )}
      {!report ? (
        <Button onClick={() => void load()}>Refresh report</Button>
      ) : (
        <>
          <p className="auth-notice">
            {report.closed_at
              ? `Final report · event closed ${dhakaTime(report.closed_at)}`
              : "Live overview · refreshes every 30 seconds"}
          </p>
          <p>
            As of {dhakaTime(report.generated_at)} · Asia/Dhaka. Payments are
            simulated.
          </p>
          <div className="operations-stats">
            {[
              ["Tickets sold", report.sold],
              ["Paid orders", report.orders],
              ["Simulated revenue (BDT)", report.revenue],
              ["Checked in", report.checked_in],
            ].map(([label, value]) => (
              <div className="card auth-card" key={label}>
                <span>{label}</span>
                <strong>{value}</strong>
              </div>
            ))}
          </div>
          <div className="report-grid">
            <Bars
              title="Tickets sold over time"
              rows={report.daily.map((d) => ({ label: d.day, value: d.sold }))}
            />
            <Bars
              title="Sales by category"
              rows={report.categories.map((c) => ({
                label: c.name,
                value: c.sold,
              }))}
            />
            <Bars
              title="Daily simulated revenue"
              money
              rows={report.daily.map((d) => ({
                label: d.day,
                value: Number(d.revenue),
              }))}
            />
            <Bars
              title="Check-in progress"
              rows={[
                { label: "Checked in", value: report.checked_in },
                {
                  label: report.closed_at
                    ? "No-show (excluding cancelled)"
                    : "Not checked in yet",
                  value: report.not_checked_in,
                },
                { label: "Cancelled tickets", value: report.cancelled },
              ]}
            />
          </div>
          <section className="card auth-card">
            <h2>Category breakdown</h2>
            <p>
              Sold includes cancelled tickets; cancellation does not issue a
              refund. Unlimited categories have no finite unsold count.
            </p>
            <div className="report-table-wrap">
              <table>
                <caption>
                  Capacity, purchases and attendance per category
                </caption>
                <thead>
                  <tr>
                    {[
                      "Category",
                      "Capacity",
                      "Sold",
                      "Unsold",
                      "Checked in",
                    ].map((x) => (
                      <th key={x} scope="col">
                        {x}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {report.categories.map((c) => (
                    <tr key={c.id}>
                      <th scope="row">
                        {c.name}
                        {!c.active ? " (inactive)" : ""}
                      </th>
                      <td>{c.capacity ?? "Unlimited"}</td>
                      <td>{c.sold}</td>
                      <td>{c.unsold ?? "Not applicable"}</td>
                      <td>{c.checked_in}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          {report.role === "owner" && !report.closed_at && (
            <section className="card auth-card">
              <h2>Finish this event</h2>
              <p>
                Closing stops all new sales and admission, releases unpaid
                reservations and saves the final report. Only close when venue
                operations are finished.
              </p>
              <Button
                variant="danger"
                disabled={busy}
                onClick={() => void close()}
              >
                Close event and save final report
              </Button>
            </section>
          )}
        </>
      )}
    </main>
  );
}
