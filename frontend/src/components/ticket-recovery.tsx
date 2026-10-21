"use client";

import { useEffect, useState } from "react";
import { Button, Pill } from "./ui";
import { AccountError } from "@/lib/auth-api";
import { recoveryRequest } from "@/lib/ticket-recovery";
import {
  checkoutSessionEvent,
  checkoutSessionKey,
} from "@/lib/checkout-session";
import { dhakaTime } from "@/lib/events";

type Order = {
  id: string;
  number: string;
  title: string;
  quantity: number;
  paid_at: string;
  can_download: boolean;
  delivery_status: string;
};
type Results = { results: Order[]; next: string | null; count: number };

export function TicketRecovery() {
  const [email, setEmail] = useState("");
  const [session, setSession] = useState<{ id: string; token: string } | null>(
    null,
  );
  const [code, setCode] = useState("");
  const [results, setResults] = useState<Results | null>(null);
  const [verified, setVerified] = useState(false);
  const [page, setPage] = useState(1);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!verified) return;
    const timer = setTimeout(() => window.location.reload(), 30 * 60 * 1000);
    return () => clearTimeout(timer);
  }, [verified]);
  useEffect(() => {
    const reload = () => window.location.reload();
    const storage = (e: StorageEvent) => {
      if (e.key === checkoutSessionKey || e.key === null) reload();
    };
    window.addEventListener(checkoutSessionEvent, reload);
    window.addEventListener("storage", storage);
    return () => {
      window.removeEventListener(checkoutSessionEvent, reload);
      window.removeEventListener("storage", storage);
    };
  }, []);
  async function act(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await work();
    } catch (e) {
      setError(
        e instanceof AccountError
          ? e.message
          : "Unable to connect. Check your connection and retry.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function load(target = page) {
    if (!session) return;
    const data = await recoveryRequest<Results>(
      `${session.id}/orders/?page=${target}`,
      "GET",
      undefined,
      session.token,
    );
    setResults(data);
    setPage(target);
  }
  return (
    <main id="main" className="container account-page recovery-page">
      <Pill>FIND MY TICKET</Pill>
      <h1>Your plans, recovered.</h1>
      <p>
        Use the email you purchased with, or the email that received your gift.
        No account needed.
      </p>
      {error && (
        <p role="alert" className="auth-error">
          {error}
        </p>
      )}
      {notice && (
        <p role="status" className="auth-notice">
          {notice}
        </p>
      )}
      {!session ? (
        <form
          className="card auth-card auth-form"
          onSubmit={(e) => {
            e.preventDefault();
            void act(async () => {
              const token = Array.from(
                crypto.getRandomValues(new Uint8Array(32)),
                (byte) => byte.toString(16).padStart(2, "0"),
              ).join("");
              const response = await recoveryRequest<{
                id: string;
                detail: string;
              }>("", "POST", { email, access_token: token });
              setSession({ id: response.id, token });
              setNotice(response.detail);
            });
          }}
        >
          <label>
            Email address
            <input
              type="email"
              required
              maxLength={254}
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </label>
          <Button disabled={busy}>Send recovery code</Button>
        </form>
      ) : !verified ? (
        <form
          className="card auth-card auth-form"
          onSubmit={(e) => {
            e.preventDefault();
            void act(async () => {
              await recoveryRequest(
                `${session.id}/verify/`,
                "POST",
                { code },
                session.token,
              );
              setVerified(true);
              setCode("");
              await load(1);
            });
          }}
        >
          <p>
            Check {email} for your six-digit code. It expires 10 minutes after
            sending. Keep this page open.
          </p>
          <label>
            Recovery code
            <input
              inputMode="numeric"
              autoComplete="one-time-code"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              value={code}
              onChange={(e) => setCode(e.target.value)}
            />
          </label>
          <Button disabled={busy}>Find my tickets</Button>
        </form>
      ) : (
        <section aria-label="Recovered orders">
          <div className="auth-actions">
            <Button
              variant="secondary"
              disabled={busy}
              onClick={() => void act(() => load())}
            >
              Refresh orders
            </Button>
          </div>
          <p>
            Your private recovery session lasts 30 minutes. Reloading or leaving
            this page clears access.
          </p>
          {results && !results.count && (
            <p role="status">
              No paid orders were found for this email. Try the buyer or
              gift-recipient email used at checkout.
            </p>
          )}
          {results?.results.map((order) => (
            <article className="card auth-card" key={order.id}>
              <h2>{order.title}</h2>
              <p>
                {order.quantity} ticket(s) · {order.number}
              </p>
              <p>{dhakaTime(order.paid_at)}</p>
              <p>
                Email delivery: {order.delivery_status}. Resending keeps the
                same ticket IDs and QR codes; used or cancelled tickets remain
                blocked.
              </p>
              {!order.can_download && (
                <p>
                  This is a gift purchase. Its ticket PDF is available to the
                  original recipient.
                </p>
              )}
              <div className="auth-actions">
                {order.can_download && (
                  <Button
                    disabled={busy}
                    onClick={() =>
                      void act(async () => {
                        const blob = await recoveryRequest<Blob>(
                          `${session.id}/orders/${order.id}/pdf/`,
                          "GET",
                          undefined,
                          session.token,
                          true,
                        );
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement("a");
                        link.href = url;
                        link.download = `${order.number}.pdf`;
                        link.click();
                        setTimeout(() => URL.revokeObjectURL(url), 1000);
                      })
                    }
                  >
                    Download PDF
                  </Button>
                )}
                <Button
                  variant="secondary"
                  disabled={busy}
                  onClick={() =>
                    void act(async () => {
                      const response = await recoveryRequest<{
                        detail: string;
                      }>(
                        `${session.id}/orders/${order.id}/resend/`,
                        "POST",
                        {},
                        session.token,
                      );
                      setNotice(response.detail);
                      await load();
                    })
                  }
                >
                  Resend to original recipient
                </Button>
              </div>
            </article>
          ))}
          <div className="auth-actions">
            {page > 1 && (
              <Button
                disabled={busy}
                onClick={() => void act(() => load(page - 1))}
              >
                Previous
              </Button>
            )}
            {results?.next && (
              <Button
                disabled={busy}
                onClick={() => void act(() => load(page + 1))}
              >
                Next
              </Button>
            )}
          </div>
        </section>
      )}
      {session && (
        <Button
          variant="secondary"
          disabled={busy}
          onClick={() => {
            setSession(null);
            setCode("");
            setVerified(false);
            setResults(null);
            setPage(1);
            setError("");
            setNotice("");
          }}
        >
          Start again / use another email
        </Button>
      )}
    </main>
  );
}
