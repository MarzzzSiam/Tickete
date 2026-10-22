"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import {
  accountRequest,
  apiRequest,
  AccountError,
  downloadTickets,
  type Profile,
} from "@/lib/auth-api";
import { dhakaTime, type EventRecord } from "@/lib/events";
import { Button, Pill, Stepper } from "@/components/ui";
import {
  checkoutEpoch,
  checkoutSessionEvent,
  checkoutSessionKey,
  clearCheckoutAccess,
} from "@/lib/checkout-session";

type Pricing = {
  subtotal: string;
  discount: string;
  total: string;
  coupon: null | { code: string; percentage: number };
};
type Order = {
  snapshot?: Partial<Pricing>;
  id: string;
  number: string;
  status: "pending" | "paid" | "failed" | "expired";
  total: string;
  quantity: number;
  expires_at: string;
  server_time: string;
  recipient_email: string;
  is_gift: boolean;
  delivery_status: string;
  pdf_ready: boolean;
  payment: null | {
    provider: string;
    status: string;
    attempts_remaining: number;
  };
  tickets: {
    id: string;
    code: string;
    attendee_name: string;
    position: number;
  }[];
};
type Saved = {
  owner: string;
  epoch: string;
  token: string;
  key: string;
  orderId?: string;
  payload?: unknown;
};
function capability(owner: string): Saved {
  const bytes = crypto.getRandomValues(new Uint8Array(32));
  const token = btoa(String.fromCharCode(...bytes))
    .replaceAll("+", "-")
    .replaceAll("/", "_")
    .replaceAll("=", "");
  return { token, key: crypto.randomUUID(), owner, epoch: checkoutEpoch() };
}

export function Checkout({ event }: { event: EventRecord }) {
  const storageKey = `tickete-checkout-${event.id}`;
  const [step, setStep] = useState(0);
  const [quantities, setQuantities] = useState<Record<string, number>>({});
  const [email, setEmail] = useState("");
  const [couponCode, setCouponCode] = useState("");
  const [quote, setQuote] = useState<
    (Pricing & { selectionKey: string; input: string }) | null
  >(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [gift, setGift] = useState(false);
  const [recipient, setRecipient] = useState("");
  const [names, setNames] = useState<Record<string, string>>({});
  const [answers, setAnswers] = useState<Record<string, string | boolean>>({});
  const [saved, setSaved] = useState<Saved | null>(null);
  const [order, setOrder] = useState<Order | null>(null);
  const [provider, setProvider] = useState("dummy_bkash");
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [remaining, setRemaining] = useState(0);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);
  const [identityReady, setIdentityReady] = useState(false);
  const [error, setError] = useState("");
  const categories = event.categories.filter(
    (c) => c.is_active && Number(c.price) > 0 && c.id,
  );
  const totalQuantity = Object.values(quantities).reduce((a, b) => a + b, 0);
  const total =
    categories.reduce(
      (sum, c) =>
        sum + Math.round(Number(c.price) * 100) * (quantities[c.id!] || 0),
      0,
    ) / 100;

  const selectionKey = JSON.stringify(
    categories.map((c) => [c.id, quantities[c.id!] || 0]),
  );
  const appliedQuote =
    quote &&
    quote.selectionKey === selectionKey &&
    quote.input === couponCode.trim().toUpperCase()
      ? quote
      : null;
  const pricing = order?.snapshot || appliedQuote;

  async function applyCoupon() {
    setQuote(null);
    const input = couponCode.trim().toUpperCase();
    const result = await apiRequest<Pricing>(
      "orders/coupon-quote",
      "POST",
      {
        event_id: event.id,
        coupon_code: input,
        selections: categories
          .filter((c) => quantities[c.id!] > 0)
          .map((c) => ({ category_id: c.id, quantity: quantities[c.id!] })),
      },
      true,
    );
    setQuote({ ...result, selectionKey, input });
  }

  useEffect(() => {
    let active = true;
    const initialEpoch = checkoutEpoch();
    const reset = () => {
      clearCheckoutAccess();
      window.location.reload();
    };
    const storageChanged = (e: StorageEvent) => {
      if (e.key === checkoutSessionKey || e.key === null) reset();
    };
    const checkSession = () => {
      if (checkoutEpoch() !== initialEpoch) reset();
    };
    window.addEventListener(checkoutSessionEvent, reset);
    window.addEventListener("storage", storageChanged);
    window.addEventListener("focus", checkSession);
    async function load() {
      try {
        let identity: Profile | null = null;
        try {
          identity = await accountRequest<Profile>(
            "me",
            "GET",
            undefined,
            true,
          );
        } catch (e) {
          // A service/network failure is not proof that this is a guest session.
          if (!(e instanceof AccountError) || e.status !== 401) throw e;
        }
        if (!active || checkoutEpoch() !== initialEpoch) return;
        setProfile(identity);
        setEmail(identity?.email || "");
        setIdentityReady(true);
        const raw = sessionStorage.getItem(storageKey);
        if (raw) {
          const previous = JSON.parse(raw) as Saved;
          // Legacy entries have no owner and must never be restored for another user.
          if (
            previous.owner !== (identity?.id || "guest") ||
            previous.epoch !== initialEpoch
          ) {
            sessionStorage.removeItem(storageKey);
            return;
          }
          if (active) setSaved(previous);
          if (previous.orderId) {
            const current = await apiRequest<Order>(
              `orders/${previous.orderId}/status`,
              "GET",
              undefined,
              true,
              previous.token,
            );
            if (active) {
              setOrder(current);
              setStep(current.status === "paid" ? 3 : 2);
            }
          } else if (previous.payload && active) {
            setStep(1);
            setError(
              "A previous checkout request may have completed. Use Retry saved checkout to recover it safely.",
            );
          }
        }
      } catch {
        if (active)
          setError(
            "Could not restore checkout. Retry loading this page before starting another order.",
          );
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
      window.removeEventListener(checkoutSessionEvent, reset);
      window.removeEventListener("storage", storageChanged);
      window.removeEventListener("focus", checkSession);
    };
  }, [storageKey]);

  useEffect(() => {
    if (!order || order.status !== "pending") return;
    const initial = Math.max(
      0,
      Date.parse(order.expires_at) - Date.parse(order.server_time),
    );
    const start = performance.now();
    const tick = () =>
      setRemaining(
        Math.max(0, Math.ceil((initial - (performance.now() - start)) / 1000)),
      );
    tick();
    const timer = setInterval(tick, 1000);
    return () => clearInterval(timer);
  }, [order]);

  async function action(work: () => Promise<void>) {
    setBusy(true);
    setError("");
    try {
      await work();
    } catch (e) {
      setError(
        e instanceof AccountError
          ? [e.message, ...Object.values(e.fields)].join(" ")
          : "Could not save checkout. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }
  async function reserve() {
    if (!saved?.payload && couponCode.trim() && !appliedQuote) {
      setError(
        "Apply your coupon to check the discount, or clear the code before reserving.",
      );
      return;
    }
    const access = saved || capability(profile?.id || "guest");
    const payload = access.payload || {
      event_id: event.id,
      buyer_email: email,
      ...(appliedQuote ? { coupon_code: appliedQuote.coupon!.code } : {}),
      is_gift: gift,
      ...(gift ? { recipient_email: recipient } : {}),
      selections: categories
        .filter((c) => quantities[c.id!] > 0)
        .map((c) => ({
          category_id: c.id,
          quantity: quantities[c.id!],
          attendee_names: event.collect_attendee_names
            ? Array.from(
                { length: quantities[c.id!] },
                (_, i) => names[`${c.id}-${i}`] || "",
              )
            : [],
        })),
      answers,
      idempotency_key: access.key,
      access_token: access.token,
    };
    const pending = { ...access, payload };
    // Keep the exact request and capability across uncertain network failures.
    sessionStorage.setItem(storageKey, JSON.stringify(pending));
    setSaved(pending);
    let current: Order;
    try {
      current = await apiRequest<Order>("orders", "POST", payload, true);
    } catch (e) {
      if (e instanceof AccountError && [400, 404, 409].includes(e.status)) {
        sessionStorage.removeItem(storageKey);
        setSaved(null);
      }
      throw e;
    }
    const confirmed = {
      owner: access.owner,
      epoch: access.epoch,
      token: access.token,
      key: access.key,
      orderId: current.id,
    };
    sessionStorage.setItem(storageKey, JSON.stringify(confirmed));
    setSaved(confirmed);
    setOrder(current);
    setStep(current.status === "paid" ? 3 : 2);
  }
  async function orderAction(path: string, body?: unknown, method = "POST") {
    if (!saved || !order) return;
    const current = await apiRequest<Order>(
      `orders/${order.id}/${path}`,
      method,
      body,
      true,
      saved.token,
    );
    setOrder(current);
    if (current.status === "paid") setStep(3);
    else if (path === "verify" && current.status === "pending")
      setError(
        `Incorrect test code. ${current.payment?.attempts_remaining} attempts remain.`,
      );
  }
  function startAgain() {
    sessionStorage.removeItem(storageKey);
    setSaved(null);
    setOrder(null);
    setStep(0);
    setOtp("");
    setCouponCode("");
    setQuote(null);
    setError("");
  }

  return (
    <main id="main" className="container account-page checkout-page">
      <Pill>TEST CHECKOUT · NO REAL CHARGE</Pill>
      <h1>Your next great memory.</h1>
      <p>
        {event.title} · {dhakaTime(event.starts_at)} · Asia/Dhaka
      </p>
      <ol className="checkout-steps" aria-label="Checkout progress">
        {["Tickets", "Details", "Payment", "Done"].map((label, i) => (
          <li key={label} aria-current={step === i ? "step" : undefined}>
            <span>{i + 1}</span>
            {label}
          </li>
        ))}
      </ol>
      {error && (
        <p className="auth-error" role="alert">
          {error}
        </p>
      )}
      {loading ? (
        <p role="status">Restoring checkout…</p>
      ) : !identityReady ? (
        <Button onClick={() => window.location.reload()}>
          Retry loading checkout
        </Button>
      ) : (
        <div className="checkout-grid">
          <section className="card auth-card">
            {step === 0 && (
              <>
                <h2>Choose your tickets</h2>
                <p>
                  Availability is confirmed when you reserve. Free tickets are
                  not available yet.
                </p>
                {categories.map((c) => (
                  <div className="checkout-category" key={c.id}>
                    <div>
                      <strong>{c.name}</strong>
                      <p>BDT {c.price}</p>
                    </div>
                    <Stepper
                      label={`${c.name} quantity`}
                      value={quantities[c.id!] || 0}
                      max={Math.max(
                        0,
                        event.max_per_order -
                          totalQuantity +
                          (quantities[c.id!] || 0),
                      )}
                      onChange={(n) =>
                        setQuantities({ ...quantities, [c.id!]: n })
                      }
                    />
                  </div>
                ))}
                {!categories.length && (
                  <p>No paid ticket categories are available.</p>
                )}
                <Button
                  disabled={!totalQuantity || busy}
                  onClick={() => setStep(1)}
                >
                  Continue to details
                </Button>
              </>
            )}
            {step === 1 && (
              <>
                <h2>Who’s coming?</h2>
                {saved?.payload ? (
                  <>
                    <p>
                      Your saved request is protected against duplicate orders.
                      Retry it before changing details.
                    </p>
                    <Button loading={busy} onClick={() => void action(reserve)}>
                      Retry saved checkout
                    </Button>
                  </>
                ) : (
                  <form
                    className="auth-form"
                    onSubmit={(e) => {
                      e.preventDefault();
                      void action(reserve);
                    }}
                  >
                    <div className="auth-notice">
                      {profile ? (
                        `Signed in as ${profile.email}`
                      ) : (
                        <>
                          Continue as a guest, or{" "}
                          <Link href="/login">log in</Link> before reserving.
                        </>
                      )}
                    </div>
                    <label>
                      Email address
                      <input
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        autoComplete="email"
                      />
                    </label>
                    <label className="checkout-toggle">
                      <input
                        type="checkbox"
                        checked={gift}
                        onChange={(e) => setGift(e.target.checked)}
                      />{" "}
                      Gift these tickets
                    </label>
                    {gift && (
                      <label>
                        Recipient email
                        <input
                          type="email"
                          required
                          value={recipient}
                          onChange={(e) => setRecipient(e.target.value)}
                        />
                      </label>
                    )}
                    {event.collect_attendee_names &&
                      categories.flatMap((c) =>
                        Array.from(
                          { length: quantities[c.id!] || 0 },
                          (_, i) => (
                            <label key={`${c.id}-${i}`}>
                              {c.name} · attendee {i + 1} (optional)
                              <input
                                maxLength={150}
                                value={names[`${c.id}-${i}`] || ""}
                                onChange={(e) =>
                                  setNames({
                                    ...names,
                                    [`${c.id}-${i}`]: e.target.value,
                                  })
                                }
                              />
                            </label>
                          ),
                        ),
                      )}
                    {event.form_fields.map((field) => (
                      <label key={field.id}>
                        {field.label}
                        {field.required ? " (required)" : " (optional)"}
                        {field.type === "dropdown" ? (
                          <select
                            required={field.required}
                            value={String(answers[field.id!] || "")}
                            onChange={(e) =>
                              setAnswers({
                                ...answers,
                                [field.id!]: e.target.value,
                              })
                            }
                          >
                            <option value="">Choose an option</option>
                            {field.options.map((o) => (
                              <option key={o}>{o}</option>
                            ))}
                          </select>
                        ) : field.type === "checkbox" ? (
                          <input
                            type="checkbox"
                            required={field.required}
                            checked={answers[field.id!] === true}
                            onChange={(e) =>
                              setAnswers({
                                ...answers,
                                [field.id!]: e.target.checked,
                              })
                            }
                          />
                        ) : (
                          <input
                            type={field.type === "number" ? "number" : "text"}
                            step="any"
                            maxLength={2000}
                            required={field.required}
                            value={String(answers[field.id!] ?? "")}
                            onChange={(e) =>
                              setAnswers({
                                ...answers,
                                [field.id!]: e.target.value,
                              })
                            }
                          />
                        )}
                      </label>
                    ))}
                    <p>
                      We’ll hold these tickets for up to 10 minutes, or until
                      sales close. Your email’s paid and reserved tickets
                      count toward the event limit.
                    </p>
                    <Button type="submit" loading={busy}>
                      Reserve tickets
                    </Button>
                    <Button
                      type="button"
                      variant="secondary"
                      disabled={busy}
                      onClick={() => setStep(0)}
                    >
                      Back to tickets
                    </Button>
                  </form>
                )}
              </>
            )}
            {step === 2 && order && (
              <>
                <h2>
                  {order.status === "pending"
                    ? "Complete your test payment"
                    : `Order ${order.status}`}
                </h2>
                {order.status === "pending" ? (
                  <>
                    <p className="checkout-timer">
                      Hold remaining: {Math.floor(remaining / 60)}:
                      {String(remaining % 60).padStart(2, "0")}
                    </p>
                    <p>
                      No money is charged and no SMS is sent. Use fictional
                      phone <strong>01700000000</strong> and test OTP{" "}
                      <strong>123456</strong>. Five incorrect attempts end this
                      order.
                    </p>
                    {!order.payment ? (
                      <form
                        className="auth-form"
                        onSubmit={(e) => {
                          e.preventDefault();
                          void action(() =>
                            orderAction("payments", { provider, phone }),
                          );
                        }}
                      >
                        <label>
                          Test provider
                          <select
                            value={provider}
                            onChange={(e) => setProvider(e.target.value)}
                          >
                            <option value="dummy_bkash">
                              bKash-style simulation
                            </option>
                            <option value="dummy_nagad">
                              Nagad-style simulation
                            </option>
                          </select>
                        </label>
                        <label>
                          Test phone number
                          <input
                            type="tel"
                            inputMode="numeric"
                            pattern="01[3-9][0-9]{8}"
                            required
                            value={phone}
                            onChange={(e) => setPhone(e.target.value)}
                          />
                        </label>
                        <Button loading={busy} disabled={remaining === 0}>
                          Continue to test OTP
                        </Button>
                      </form>
                    ) : (
                      <form
                        className="auth-form"
                        onSubmit={(e) => {
                          e.preventDefault();
                          void action(() => orderAction("verify", { otp }));
                        }}
                      >
                        <label>
                          Test OTP
                          <input
                            inputMode="numeric"
                            pattern="[0-9]{6}"
                            maxLength={6}
                            required
                            value={otp}
                            onChange={(e) => setOtp(e.target.value)}
                          />
                        </label>
                        <Button loading={busy} disabled={remaining === 0}>
                          Confirm test payment
                        </Button>
                      </form>
                    )}
                    <div className="checkout-actions">
                      <Button
                        variant="secondary"
                        disabled={busy}
                        onClick={() =>
                          void action(() =>
                            orderAction("status", undefined, "GET"),
                          )
                        }
                      >
                        Refresh order status
                      </Button>
                      <Button
                        variant="secondary"
                        disabled={busy}
                        onClick={() => void action(() => orderAction("cancel"))}
                      >
                        Cancel reservation
                      </Button>
                    </div>
                    {remaining === 0 && (
                      <p role="status">
                        This hold has ended. Refresh order status to confirm and
                        start again.
                      </p>
                    )}
                  </>
                ) : (
                  <>
                    <p>
                      Your reservation has been released. No payment was
                      collected.
                    </p>
                    <Button onClick={startAgain}>Choose tickets again</Button>
                  </>
                )}
              </>
            )}
            {step === 3 && order && (
              <>
                <Pill>TEST PAYMENT CONFIRMED</Pill>
                <h2>You’re on the list.</h2>
                <p>
                  {order.quantity} ticket(s) issued for {order.recipient_email}
                  {order.is_gift ? " as a gift" : ""}.
                </p>
                {order.tickets.map((t) => (
                  <article className="checkout-issued" key={t.id}>
                    <span>
                      ADMIT ONE · {t.position} OF {order.quantity}
                    </span>
                    <h3>{event.title}</h3>
                    <p>{t.attendee_name || "General admission"}</p>
                    <code>{t.code}</code>
                  </article>
                ))}
                <p className="auth-notice">
                  {order.delivery_status === "sent"
                    ? "Your ticket email was accepted by the mail service. Check your inbox and spam folder."
                    : order.delivery_status === "failed"
                      ? "Ticket delivery needs attention. Contact support with your order number."
                      : "Your ticket PDF and email are queued. Refresh the status shortly."}{" "}
                  Keep this browser tab to return to your order.
                </p>
                <Button
                  variant="secondary"
                  disabled={busy}
                  onClick={() =>
                    void action(() => orderAction("status", undefined, "GET"))
                  }
                >
                  Refresh order status
                </Button>
                {order.pdf_ready && (
                  <Button
                    disabled={busy}
                    onClick={() =>
                      void action(async () => {
                        if (!saved) return;
                        const blob = await downloadTickets(
                          order.id,
                          saved.token,
                        );
                        const url = URL.createObjectURL(blob);
                        const link = document.createElement("a");
                        link.href = url;
                        link.download = `${order.number}.pdf`;
                        link.click();
                        setTimeout(() => URL.revokeObjectURL(url), 30000);
                      })
                    }
                  >
                    Download tickets PDF
                  </Button>
                )}
              </>
            )}
          </section>
          <aside className="card auth-card checkout-summary">
            <Pill>YOUR EXPERIENCE</Pill>
            <h2>{event.title}</h2>
            <p>{event.venue}</p>
            <p>{dhakaTime(event.starts_at)}</p>
            <hr />
            <p>{order?.quantity ?? totalQuantity} ticket(s)</p>
            {!order && !saved?.payload && (
              <div className="auth-form">
                <label className="field">
                  Any coupon code? (optional)
                  <input
                    className="field-input"
                    value={couponCode}
                    disabled={busy}
                    maxLength={32}
                    placeholder="Enter coupon code"
                    onChange={(e) => {
                      setCouponCode(e.target.value);
                      setQuote(null);
                    }}
                  />
                </label>
                <div className="auth-actions">
                  <Button
                    variant="secondary"
                    disabled={busy || !couponCode.trim() || totalQuantity === 0}
                    onClick={() => void action(applyCoupon)}
                  >
                    Apply coupon
                  </Button>
                  {couponCode && (
                    <Button
                      variant="secondary"
                      disabled={busy}
                      onClick={() => {
                        setCouponCode("");
                        setQuote(null);
                      }}
                    >
                      Remove coupon
                    </Button>
                  )}
                </div>
                {appliedQuote && (
                  <p role="status" className="auth-notice">
                    {appliedQuote.coupon?.code} applied:{" "}
                    {appliedQuote.coupon?.percentage}% off. Rechecked when you
                    reserve.
                  </p>
                )}
              </div>
            )}
            {pricing?.coupon && (
              <div aria-label="Price breakdown">
                <p>Subtotal: BDT {pricing.subtotal}</p>
                <p>
                  {pricing.coupon.code} ({pricing.coupon.percentage}% off): −BDT{" "}
                  {pricing.discount}
                </p>
              </div>
            )}
            <strong className="checkout-total">
              BDT {order?.total ?? appliedQuote?.total ?? total.toFixed(2)}
            </strong>
            <p>
              Maximum {event.max_per_order} per order and per buyer email across
              this event.
            </p>
            {order && (
              <p>
                Order <code>{order.number}</code>
              </p>
            )}
            <Link href={`/events/${event.slug}`}>Back to event</Link>
          </aside>
        </div>
      )}
    </main>
  );
}
