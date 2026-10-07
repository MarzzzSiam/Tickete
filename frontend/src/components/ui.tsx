import Link from "next/link";
import { LoaderCircle, Minus, Plus } from "lucide-react";
import { clsx } from "clsx";
import type { ButtonHTMLAttributes, ReactNode } from "react";

export function Button({
  children,
  variant = "primary",
  loading = false,
  className,
  disabled,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger";
  loading?: boolean;
}) {
  return (
    <button
      className={clsx("button", `button-${variant}`, className)}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      {...props}
    >
      {loading && (
        <LoaderCircle className="spin" size={18} aria-hidden="true" />
      )}
      {children}
    </button>
  );
}
export function ButtonLink({
  href,
  children,
  variant = "primary",
  className,
}: {
  href: string;
  children: ReactNode;
  variant?: "primary" | "secondary";
  className?: string;
}) {
  return (
    <Link
      href={href}
      className={clsx("button", `button-${variant}`, className)}
    >
      {children}
    </Link>
  );
}
export function Pill({ children }: { children: ReactNode }) {
  return <span className="pill">{children}</span>;
}
export function Badge({
  children,
  status = "neutral",
}: {
  children: ReactNode;
  status?: "neutral" | "success" | "warning" | "danger";
}) {
  return <span className={`badge badge-${status}`}>{children}</span>;
}
export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`card ${className}`}>{children}</div>;
}
export function Stepper({
  value,
  onChange,
  max = 5,
  label = "Ticket quantity",
}: {
  value: number;
  onChange: (value: number) => void;
  max?: number;
  label?: string;
}) {
  return (
    <div className="stepper" role="group" aria-label={label}>
      <button
        type="button"
        aria-label="Decrease quantity"
        disabled={value <= 0}
        onClick={() => onChange(value - 1)}
      >
        <Minus size={16} />
      </button>
      <output aria-live="polite">{value}</output>
      <button
        type="button"
        aria-label="Increase quantity"
        disabled={value >= max}
        onClick={() => onChange(value + 1)}
      >
        <Plus size={16} />
      </button>
    </div>
  );
}
export function Skeleton() {
  return (
    <div className="skeleton" role="status" aria-label="Loading content">
      <span />
      <span />
      <span />
    </div>
  );
}
