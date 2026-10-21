"use client";

import Link from "next/link";
import { useCallback, useEffect, useRef, useState } from "react";
import type QrScanner from "qr-scanner";
import { AccountError, apiRequest } from "@/lib/auth-api";
import {
  checkoutSessionEvent,
  checkoutSessionKey,
} from "@/lib/checkout-session";
import { dhakaTime } from "@/lib/events";
import { Button, Pill } from "@/components/ui";

type Summary = {
  id: string;
  title: string;
  role: string;
  tickets_sold: number;
  checked_in: number;
  orders?: number;
  revenue?: string;
  categories?: { category__name: string; sold: number; checked_in: number }[];
};
type Attendee = {
  id: string;
  code: string;
  buyer_email: string;
  recipient_email: string;
  attendee_name: string;
  category: string;
  status: string;
  order_number: string;
  order_quantity: number;
};
type Team = {
  server_time: string;
  members: { id: string; user__email: string; role: string; active: boolean }[];
  invitations: {
    id: string;
    email: string;
    role: string;
    sent_at: string | null;
    accepted_at: string | null;
    revoked_at: string | null;
    expires_at: string;
    attempts: number;
  }[];
};
type ScanResult = {
  result: string;
  checked_in: number;
  ticket: {
    code: string;
    attendee_name: string;
    category: string;
    used_at: string | null;
    used_by: string | null;
  } | null;
};
const outcomes: Record<string, string> = {
  admitted: "Entry approved",
  already_used: "Already checked in",
  cancelled: "Ticket cancelled",
  wrong_event: "Ticket belongs to another event",
  invalid: "Ticket not found",
  event_unavailable: "Event is not approved for admission",
};
const describe = (e: unknown) =>
  e instanceof AccountError
    ? e.message
    : "Unable to complete this request. Please retry.";

export function EventOperations({ eventId }: { eventId: string }) {
  const [summary, setSummary] = useState<Summary | null>(null);
  const [attendees, setAttendees] = useState<{
    count: number;
    next: string | null;
    results: Attendee[];
  } | null>(null);
  const [team, setTeam] = useState<Team | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [email, setEmail] = useState("");
  const [role, setRole] = useState("scanner");
  const [ticketId, setTicketId] = useState("");
  const [result, setResult] = useState<ScanResult | null>(null);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  const [camera, setCamera] = useState(false);
  const [loading, setLoading] = useState(true);
  const video = useRef<HTMLVideoElement>(null);
  const scanner = useRef<QrScanner | null>(null);
  const scanning = useRef(false);
  const mounted = useRef(true);
  const base = `events/${eventId}`;
  const stop = useCallback(() => {
    scanner.current?.destroy();
    scanner.current = null;
    setCamera(false);
  }, []);
  const load = useCallback(async () => {
    try {
      const info = await apiRequest<Summary>(
        `${base}/operations`,
        "GET",
        undefined,
        true,
      );
      if (!mounted.current) return;
      setSummary(info);
      if (["owner", "manager", "admin"].includes(info.role)) {
        const list = await apiRequest<typeof attendees>(
          `${base}/attendees?page=${page}&search=${encodeURIComponent(query)}`,
          "GET",
          undefined,
          true,
        );
        if (mounted.current) setAttendees(list);
      } else setAttendees(null);
      if (info.role === "owner") {
        const members = await apiRequest<Team>(
          `${base}/team`,
          "GET",
          undefined,
          true,
        );
        if (mounted.current) setTeam(members);
      } else setTeam(null);
    } catch (e) {
      if (mounted.current) {
        setError(describe(e));
        setSummary(null);
        setAttendees(null);
        setTeam(null);
        setResult(null);
        stop();
      }
    } finally {
      if (mounted.current) setLoading(false);
    }
  }, [base, page, query, stop]);
  useEffect(() => {
    mounted.current = true;
    const initial = setTimeout(() => void load(), 0);
    const timer = setInterval(() => void load(), 15000);
    const reload = () => window.location.reload();
    const storage = (e: StorageEvent) => {
      if (e.key === checkoutSessionKey || e.key === null) reload();
    };
    window.addEventListener(checkoutSessionEvent, reload);
    window.addEventListener("storage", storage);
    return () => {
      mounted.current = false;
      clearTimeout(initial);
      clearInterval(timer);
      scanner.current?.destroy();
      scanner.current = null;
      window.removeEventListener(checkoutSessionEvent, reload);
      window.removeEventListener("storage", storage);
    };
  }, [load]);

  async function act(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await work();
      await load();
    } catch (e) {
      setError(describe(e));
    } finally {
      setBusy(false);
    }
  }
  async function admit(value: string, method: "qr" | "manual") {
    if (scanning.current) return;
    scanning.current = true;
    stop();
    setResult(null);
    await act(async () => {
      const response = await apiRequest<ScanResult>(
        `${base}/scan`,
        "POST",
        { value, method },
        true,
      );
      if (mounted.current) {
        setResult(response);
        setTicketId("");
      }
    });
    scanning.current = false;
  }
  async function startCamera() {
    setError("");
    setResult(null);
    if (!window.isSecureContext) {
      setError(
        "Camera access requires HTTPS or localhost. Use manual ticket ID entry here.",
      );
      return;
    }
    try {
      stop();
      const { default: Reader } = await import("qr-scanner");
      if (!mounted.current || !video.current) return;
      const reader = new Reader(
        video.current,
        (decoded) => void admit(decoded.data, "qr"),
        {
          preferredCamera: "environment",
          maxScansPerSecond: 3,
          returnDetailedScanResult: true,
        },
      );
      scanner.current = reader;
      await reader.start();
      if (!mounted.current || scanner.current !== reader) {
        reader.destroy();
        return;
      }
      setCamera(true);
    } catch {
      stop();
      setError(
        "Camera could not start. Allow camera access or type the ticket ID below.",
      );
    }
  }
  return (
    <main id="main" className="container account-page">
      <Pill>EVENT OPERATIONS</Pill>
      <h1>{summary?.title || "Your event workspace"}</h1>
      <p>
        <Link href="/team">My event teams</Link> ·{" "}
        <Link href="/organizer/events">Organizer events</Link>
      </p>
      {error && (
        <p className="auth-error" role="alert">
          {error}
        </p>
      )}
      {notice && (
        <p className="auth-notice" role="status">
          {notice}
        </p>
      )}
      {loading ? (
        <p role="status">Loading event access…</p>
      ) : !summary ? (
        <p>
          Sign in with a verified account assigned to this event.{" "}
          <Link href="/login">Log in</Link> ·{" "}
          <Link href="/account">Verify email</Link>{" "}
          <Button variant="secondary" onClick={() => void load()}>
            Retry
          </Button>
        </p>
      ) : (
        <>
          <p>
            Your role: <strong>{summary.role}</strong>. Counts refresh every 15
            seconds.
          </p>
          <div className="operations-stats">
            <div className="card auth-card">
              <span>Tickets purchased</span>
              <strong>{summary.tickets_sold}</strong>
            </div>
            <div className="card auth-card">
              <span>Checked in</span>
              <strong>{summary.checked_in}</strong>
            </div>
            {summary.revenue !== undefined && (
              <>
                <div className="card auth-card">
                  <span>Paid orders</span>
                  <strong>{summary.orders}</strong>
                </div>
                <div className="card auth-card">
                  <span>Simulated revenue · BDT</span>
                  <strong>{summary.revenue}</strong>
                </div>
              </>
            )}
          </div>
          {summary.categories && (
            <section className="card auth-card">
              <h2>Sales by category</h2>
              {summary.categories.length ? (
                summary.categories.map((c) => (
                  <p key={c.category__name}>
                    {c.category__name}: {c.sold} purchased · {c.checked_in}{" "}
                    checked in
                  </p>
                ))
              ) : (
                <p>No paid tickets yet.</p>
              )}
            </section>
          )}
          {["owner", "manager", "scanner"].includes(summary.role) && (
            <section className="card auth-card operations-scanner">
              <h2>Check in a guest</h2>
              <p>
                Scanning or submitting a ticket ID immediately admits one
                person. A repeated ticket is rejected.
              </p>
              <video
                ref={video}
                muted
                playsInline
                className={
                  camera ? "scanner-video" : "scanner-video scanner-idle"
                }
                aria-label="QR camera preview"
              />
              <div className="auth-actions">
                <Button
                  disabled={busy || camera}
                  onClick={() => void startCamera()}
                >
                  Start QR camera
                </Button>
                {camera && (
                  <Button variant="secondary" onClick={stop}>
                    Stop camera
                  </Button>
                )}
              </div>
              <form
                className="auth-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  void admit(ticketId.trim(), "manual");
                }}
              >
                <label htmlFor="manual-ticket">Ticket ID</label>
                <input
                  id="manual-ticket"
                  value={ticketId}
                  onChange={(e) => setTicketId(e.target.value)}
                  required
                  maxLength={128}
                  placeholder="TE-…"
                  autoComplete="off"
                />
                <Button disabled={busy || !ticketId.trim()}>
                  Check in ticket
                </Button>
              </form>
              {result && (
                <div
                  role="status"
                  aria-live="polite"
                  className={`scan-result ${result.result === "admitted" ? "scan-admitted" : "scan-rejected"}`}
                >
                  <h3>{outcomes[result.result] || "Ticket rejected"}</h3>
                  {result.ticket && (
                    <>
                      <p>
                        {result.ticket.attendee_name || "Name not provided"} ·{" "}
                        {result.ticket.category}
                      </p>
                      <p>{result.ticket.code}</p>
                      {result.ticket.used_at && (
                        <p>
                          Checked in {dhakaTime(result.ticket.used_at)} by{" "}
                          {result.ticket.used_by}
                        </p>
                      )}
                    </>
                  )}
                  <p>{result.checked_in} guests checked in</p>
                </div>
              )}
            </section>
          )}
          {attendees && (
            <section className="card auth-card">
              <h2>Purchases and attendees</h2>
              <p>
                {attendees.count} matching tickets. Gift recipients are listed
                separately from buyers.
              </p>
              <form
                className="auth-actions"
                onSubmit={(e) => {
                  e.preventDefault();
                  setPage(1);
                  setQuery(search.trim());
                }}
              >
                <label htmlFor="attendee-search">
                  Search email, name or ticket ID
                </label>
                <input
                  id="attendee-search"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  maxLength={254}
                />
                <Button>Search purchases</Button>
              </form>
              <div className="operations-attendees">
                {attendees.results.map((t) => (
                  <article className="checkout-issued" key={t.id}>
                    <h3>{t.attendee_name || "Unnamed attendee"}</h3>
                    <p>
                      {t.category} · <strong>{t.status}</strong>
                    </p>
                    <p>
                      Buyer: {t.buyer_email}
                      <br />
                      Recipient: {t.recipient_email}
                    </p>
                    <p>
                      {t.code}
                      <br />
                      Order {t.order_number} · {t.order_quantity} ticket(s)
                    </p>
                    {summary.role === "owner" && t.status === "valid" && (
                      <Button
                        variant="danger"
                        disabled={busy}
                        onClick={() => {
                          if (
                            window.confirm(
                              "Cancel this ticket? It will be refused at the gate. No refund is issued.",
                            )
                          )
                            void act(async () => {
                              await apiRequest(
                                `${base}/tickets/${t.id}/cancel`,
                                "POST",
                                undefined,
                                true,
                              );
                            });
                        }}
                      >
                        Cancel ticket
                      </Button>
                    )}
                  </article>
                ))}
              </div>
              <div className="auth-actions">
                {page > 1 && (
                  <Button variant="secondary" onClick={() => setPage(page - 1)}>
                    Previous purchases
                  </Button>
                )}
                {attendees.next && (
                  <Button variant="secondary" onClick={() => setPage(page + 1)}>
                    Next purchases
                  </Button>
                )}
              </div>
            </section>
          )}
          {team && (
            <section className="card auth-card">
              <h2>Event team</h2>
              <p>
                Scanner: admission only. Manager: purchases, draft editing and
                admission. Viewer: totals only. Only you manage access.
              </p>
              <form
                className="auth-form"
                onSubmit={(e) => {
                  e.preventDefault();
                  void act(async () => {
                    await apiRequest(
                      `${base}/team`,
                      "POST",
                      { email, role },
                      true,
                    );
                    setEmail("");
                    setNotice(
                      "Invitation queued. The local processor sends the email; the recipient must accept with their verified account.",
                    );
                  });
                }}
              >
                <label htmlFor="invite-email">
                  Volunteer or teammate email
                </label>
                <input
                  id="invite-email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                />
                <label htmlFor="invite-role">Invitation role</label>
                <select
                  id="invite-role"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  <option value="scanner">Scanner</option>
                  <option value="manager">Manager</option>
                  <option value="viewer">Viewer</option>
                </select>
                <Button disabled={busy}>Invite teammate</Button>
              </form>
              <h3>Accepted members</h3>
              {team.members.length === 0 && <p>No accepted invitations yet.</p>}
              {team.members.map((m) => (
                <div className="checkout-issued" key={m.id}>
                  <p>
                    {m.user__email} · {m.active ? "Active" : "Revoked"}
                  </p>
                  <label htmlFor={`role-${m.id}`}>
                    Role for {m.user__email}
                  </label>
                  <select
                    id={`role-${m.id}`}
                    value={m.role}
                    disabled={busy || !m.active}
                    onChange={(e) =>
                      void act(async () => {
                        await apiRequest(
                          `${base}/team/${m.id}`,
                          "PATCH",
                          { role: e.target.value },
                          true,
                        );
                      })
                    }
                  >
                    {["scanner", "manager", "viewer"].map((r) => (
                      <option key={r} value={r}>
                        {r}
                      </option>
                    ))}
                  </select>
                  {m.active && (
                    <Button
                      variant="danger"
                      disabled={busy}
                      onClick={() =>
                        void act(async () => {
                          await apiRequest(
                            `${base}/team/${m.id}`,
                            "PATCH",
                            { active: false },
                            true,
                          );
                        })
                      }
                    >
                      Revoke access
                    </Button>
                  )}
                </div>
              ))}
              <h3>Recent invitations</h3>
              {team.invitations.map((i) => (
                <div className="checkout-issued" key={i.id}>
                  <p>
                    {i.email} · {i.role}
                  </p>
                  <p>
                    {i.revoked_at
                      ? "Revoked"
                      : i.accepted_at
                        ? "Accepted"
                        : Date.parse(i.expires_at) <=
                            Date.parse(team.server_time)
                          ? "Expired"
                          : i.sent_at
                            ? "Email sent; awaiting acceptance"
                            : i.attempts >= 5
                              ? "Email failed; revoke and reinvite"
                              : "Email queued"}
                  </p>
                  {!i.revoked_at && !i.accepted_at && (
                    <Button
                      variant="secondary"
                      disabled={busy}
                      onClick={() =>
                        void act(async () => {
                          await apiRequest(
                            `${base}/invitations/${i.id}/revoke`,
                            "POST",
                            undefined,
                            true,
                          );
                        })
                      }
                    >
                      Revoke invitation
                    </Button>
                  )}
                </div>
              ))}
            </section>
          )}
        </>
      )}
    </main>
  );
}

export function TeamEvents() {
  const [events, setEvents] = useState<
    { id: string; title: string; role: string }[]
  >([]);
  const [page, setPage] = useState(1);
  const [next, setNext] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    apiRequest<{ results: typeof events; next: string | null }>(
      `team/events?page=${page}`,
      "GET",
      undefined,
      true,
    )
      .then((data) => {
        if (active) {
          setEvents(data.results);
          setNext(Boolean(data.next));
        }
      })
      .catch((e) => {
        if (active) setError(describe(e));
      });
    return () => {
      active = false;
    };
  }, [page]);
  return (
    <main id="main" className="container account-page">
      <Pill>YOUR EVENT TEAMS</Pill>
      <h1>Ready at the gate.</h1>
      <p>
        Accept an email invitation with the matching verified account to see an
        assigned event.
      </p>
      {error && (
        <p role="alert" className="auth-error">
          {error} <Link href="/login">Log in</Link>
        </p>
      )}
      {events.map((e) => (
        <article key={e.id} className="card auth-card">
          <h2>{e.title}</h2>
          <p>{e.role}</p>
          <Link href={`/organizer/events/${e.id}/operations`}>
            Open event operations →
          </Link>
          {e.role === "manager" && (
            <p>
              <Link href={`/organizer/events/${e.id}`}>Edit event draft</Link>
            </p>
          )}
        </article>
      ))}
      {!error && !events.length && (
        <p>
          No assigned events. Verify your account and accept your invitation.
        </p>
      )}
      <div className="auth-actions">
        {page > 1 && (
          <Button onClick={() => setPage(page - 1)}>Previous</Button>
        )}
        {next && <Button onClick={() => setPage(page + 1)}>Next</Button>}
      </div>
    </main>
  );
}

export function AcceptTeamInvitation() {
  const [invitation, setInvitation] = useState("");
  const [token, setToken] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [event, setEvent] = useState("");
  useEffect(() => {
    const timer = setTimeout(() => {
      const params = new URLSearchParams(window.location.hash.slice(1));
      setInvitation(params.get("invitation") || "");
      setToken(params.get("token") || "");
    }, 0);
    return () => clearTimeout(timer);
  }, []);
  return (
    <main id="main" className="container account-page">
      <Pill>EVENT TEAM INVITATION</Pill>
      <h1>Your team is waiting.</h1>
      <p>
        Sign in with the invited email address and verify it before accepting.
        After signing in, reopen the invitation from your email.
      </p>
      <p>
        <Link href="/login">Log in</Link> ·{" "}
        <Link href="/signup">Create account</Link> ·{" "}
        <Link href="/account">Verify email</Link>
      </p>
      {error && (
        <p className="auth-error" role="alert">
          {error}
        </p>
      )}
      {event ? (
        <p role="status">
          Invitation accepted.{" "}
          <Link href={`/organizer/events/${event}/operations`}>
            Open event operations
          </Link>
        </p>
      ) : (
        <Button
          disabled={busy || !invitation || !token}
          onClick={async () => {
            setBusy(true);
            setError("");
            try {
              const response = await apiRequest<{ event_id: string }>(
                "team/accept",
                "POST",
                { invitation, token },
                true,
              );
              setEvent(response.event_id);
              setToken("");
              window.history.replaceState(null, "", window.location.pathname);
            } catch (e) {
              setError(describe(e));
            } finally {
              setBusy(false);
            }
          }}
        >
          Accept invitation
        </Button>
      )}
    </main>
  );
}
