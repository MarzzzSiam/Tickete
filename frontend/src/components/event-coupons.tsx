"use client";
import { useEffect, useState } from "react";
import { AccountError, apiRequest } from "@/lib/auth-api";
import { Button } from "./ui";

export type CouponDraft = { code: string; percentage: string };
type Coupon = {
  id: string;
  code: string;
  percentage: number;
  is_active: boolean;
};

export function CouponFields({
  value,
  onChange,
  prefix = "coupon",
  disabled = false,
}: {
  value: CouponDraft;
  onChange: (value: CouponDraft) => void;
  prefix?: string;
  disabled?: boolean;
}) {
  return (
    <div className="coupon-fields">
      <label className="field" htmlFor={`${prefix}-code`}>
        Coupon code
        <input
          id={`${prefix}-code`}
          className="field-input"
          value={value.code}
          disabled={disabled}
          maxLength={32}
          placeholder="TICKETE10"
          autoCapitalize="characters"
          onChange={(e) =>
            onChange({ ...value, code: e.target.value.toUpperCase() })
          }
        />
      </label>
      <label className="field" htmlFor={`${prefix}-percentage`}>
        Percentage off
        <input
          id={`${prefix}-percentage`}
          className="field-input"
          type="number"
          min={1}
          max={100}
          step={1}
          value={value.percentage}
          disabled={disabled}
          placeholder="10"
          onChange={(e) => onChange({ ...value, percentage: e.target.value })}
        />
      </label>
    </div>
  );
}

export function EventCoupons({
  eventId,
  closed,
}: {
  eventId: string;
  closed: boolean;
}) {
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [enabled, setEnabled] = useState(false);
  const [value, setValue] = useState<CouponDraft>({ code: "", percentage: "" });
  const [busy, setBusy] = useState(false);
  const [ready, setReady] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    apiRequest<Coupon[]>(`events/${eventId}/coupons`)
      .then((rows) => {
        if (active) {
          setCoupons(rows);
          setReady(true);
        }
      })
      .catch(() => {
        if (active)
          setError("Could not load coupons. Reload this page to retry.");
      });
    return () => {
      active = false;
    };
  }, [eventId]);
  async function save(coupon?: Coupon) {
    if (
      coupon?.is_active &&
      !window.confirm(
        "Pause this coupon? Unpaid reservations using it will expire immediately. Paid tickets stay valid.",
      )
    )
      return;
    setBusy(true);
    setError("");
    try {
      const result = await apiRequest<Coupon>(
        `events/${eventId}/coupons${coupon ? `/${coupon.id}` : ""}`,
        coupon ? "PATCH" : "POST",
        coupon
          ? { is_active: !coupon.is_active }
          : { code: value.code.trim(), percentage: Number(value.percentage) },
        true,
      );
      setCoupons((rows) =>
        coupon
          ? rows.map((row) => (row.id === result.id ? result : row))
          : [...rows, result],
      );
      if (!coupon) {
        setValue({ code: "", percentage: "" });
        setEnabled(false);
      }
    } catch (e) {
      setError(
        e instanceof AccountError
          ? [e.message, ...Object.values(e.fields)].join(" ")
          : "Could not save coupon. Reload to check its status before retrying.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <section
      className="card auth-card auth-form coupon-panel"
      aria-labelledby="coupons-heading"
    >
      <h2 id="coupons-heading">Event coupons</h2>
      <p>
        Up to three codes per event, including paused codes. One code per order,
        1–100% off. Codes and percentages stay fixed after creation.
      </p>
      {error && (
        <p role="alert" className="auth-error">
          {error}
        </p>
      )}
      {!ready && !error && <p role="status">Loading coupons…</p>}
      {coupons.map((c) => (
        <div className="coupon-row" key={c.id}>
          <p>
            <strong>{c.code}</strong> · {c.percentage}% off ·{" "}
            {c.is_active ? "Active" : "Paused"}
          </p>
          <Button
            variant="secondary"
            disabled={busy || closed}
            onClick={() => void save(c)}
          >
            {c.is_active ? "Pause" : "Resume"} {c.code}
          </Button>
        </div>
      ))}
      {ready && coupons.length < 3 && !closed && (
        <>
          <label className="event-checkbox">
            <input
              type="checkbox"
              checked={enabled}
              disabled={busy}
              onChange={(e) => setEnabled(e.target.checked)}
            />
            Add an optional coupon
          </label>
          {enabled && (
            <>
              <CouponFields value={value} onChange={setValue} disabled={busy} />
              <Button
                disabled={busy || !value.code.trim() || !value.percentage}
                onClick={() => void save()}
              >
                Create coupon
              </Button>
            </>
          )}
        </>
      )}
      {closed && <p>This event is closed. Coupons cannot be changed.</p>}
    </section>
  );
}
