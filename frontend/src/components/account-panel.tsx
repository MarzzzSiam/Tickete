"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AccountError, accountRequest, type Profile } from "@/lib/auth-api";
import { Badge, Button, ButtonLink, Pill } from "./ui";

const profileSchema = z.object({
  full_name: z.string().trim().min(1, "Enter your full name.").max(150),
  phone: z.string().max(30),
});
const passwordSchema = z
  .object({
    current_password: z.string().min(1, "Enter your current password."),
    password: z.string().min(8, "Use at least 8 characters.").max(128),
    confirm: z.string(),
  })
  .refine((data) => data.password === data.confirm, {
    message: "Passwords don’t match.",
    path: ["confirm"],
  });

function errorMessage(error: unknown) {
  if (error instanceof AccountError)
    return Object.values(error.fields).join(" ") || error.message;
  return "Something went wrong. Please try again.";
}

function ProfileEditor({
  user,
  onUpdate,
}: {
  user: Profile;
  onUpdate: (user: Profile) => void;
}) {
  const [message, setMessage] = useState("");
  const [problem, setProblem] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof profileSchema>>({
    resolver: zodResolver(profileSchema),
    defaultValues: { full_name: user.full_name, phone: user.phone },
  });
  async function save(data: z.infer<typeof profileSchema>) {
    setMessage("");
    setProblem("");
    try {
      onUpdate(await accountRequest<Profile>("me", "PATCH", data, true));
      setMessage("Profile saved.");
    } catch (error) {
      setProblem(errorMessage(error));
    }
  }
  return (
    <form className="auth-form" onSubmit={handleSubmit(save)} noValidate>
      <h2>Your details</h2>
      <label className="field" htmlFor="profile-name">
        <span>Full name</span>
        <input
          id="profile-name"
          className="field-input"
          autoComplete="name"
          {...register("full_name")}
          aria-invalid={!!errors.full_name}
          aria-describedby={errors.full_name ? "profile-name-error" : undefined}
        />
        {errors.full_name && (
          <span id="profile-name-error" className="auth-field-error">
            {errors.full_name.message}
          </span>
        )}
      </label>
      <label className="field" htmlFor="profile-phone">
        <span>Phone (optional)</span>
        <input
          id="profile-phone"
          className="field-input"
          autoComplete="tel"
          type="tel"
          {...register("phone")}
          maxLength={30}
        />
      </label>
      {problem && (
        <p role="alert" className="auth-error">
          {problem}
        </p>
      )}
      {message && (
        <p role="status" className="auth-notice">
          {message}
        </p>
      )}
      <Button loading={isSubmitting} type="submit">
        Save details
      </Button>
    </form>
  );
}

function PasswordEditor() {
  const router = useRouter();
  const [problem, setProblem] = useState("");
  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<z.infer<typeof passwordSchema>>({
    resolver: zodResolver(passwordSchema),
  });
  async function save(data: z.infer<typeof passwordSchema>) {
    setProblem("");
    try {
      await accountRequest(
        "change-password",
        "POST",
        { current_password: data.current_password, password: data.password },
        true,
      );
      router.replace("/login");
    } catch (error) {
      setProblem(errorMessage(error));
    }
  }
  return (
    <form className="auth-form" onSubmit={handleSubmit(save)} noValidate>
      <h2>Change password</h2>
      <p className="muted">
        You’ll be signed out on every device after changing your password.
      </p>
      {(
        [
          ["current_password", "Current password"],
          ["password", "New password"],
          ["confirm", "Confirm new password"],
        ] as const
      ).map(([name, label]) => (
        <label className="field" key={name} htmlFor={`change-${name}`}>
          <span>{label}</span>
          <input
            id={`change-${name}`}
            type="password"
            className="field-input"
            autoComplete={
              name === "current_password" ? "current-password" : "new-password"
            }
            {...register(name)}
            maxLength={128}
            aria-invalid={!!errors[name]}
            aria-describedby={errors[name] ? `change-${name}-error` : undefined}
          />
          {errors[name] && (
            <span className="auth-field-error" id={`change-${name}-error`}>
              {errors[name]?.message}
            </span>
          )}
        </label>
      ))}
      {problem && (
        <p role="alert" className="auth-error">
          {problem}
        </p>
      )}
      <Button loading={isSubmitting} variant="secondary">
        Update password
      </Button>
    </form>
  );
}

export function AccountPanel() {
  const router = useRouter();
  const [user, setUser] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const [problem, setProblem] = useState("");
  const [message, setMessage] = useState("");
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    let active = true;
    accountRequest<Profile>("me", "GET", undefined, true)
      .then((profile) => {
        if (active) setUser(profile);
      })
      .catch((error) => {
        if (
          active &&
          (!(error instanceof AccountError) || error.status !== 401)
        )
          setProblem(errorMessage(error));
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);
  async function action(kind: "logout" | "verify-email/request") {
    setBusy(true);
    setProblem("");
    setMessage("");
    try {
      await accountRequest(kind, "POST", undefined, kind !== "logout");
      if (kind === "logout") {
        setUser(null);
        router.replace("/login");
      } else
        setMessage(
          "Verification requested. Check your inbox; delivery may be delayed.",
        );
    } catch (error) {
      setProblem(errorMessage(error));
    } finally {
      setBusy(false);
    }
  }
  return (
    <main id="main" className="container account-page">
      <Pill>YOUR TICKETÉ ACCOUNT</Pill>
      <h1>
        {user ? `Hello, ${user.full_name || "there"}.` : "Your next chapter."}
      </h1>
      {loading ? (
        <p role="status">Loading your account…</p>
      ) : (
        <>
          {problem && (
            <p role="alert" className="auth-error">
              {problem}
            </p>
          )}
          {!user ? (
            <section className="card auth-card">
              <h2>Log in to your account</h2>
              <p className="muted">
                Your account details are private. Log in or create an account to
                continue.
              </p>
              <div className="auth-actions">
                <ButtonLink href="/login">Log in</ButtonLink>
                <ButtonLink href="/signup" variant="secondary">
                  Create account
                </ButtonLink>
              </div>
            </section>
          ) : (
            <>
              <section className="card account-summary">
                <div>
                  <p className="account-email">{user.email}</p>
                  <Badge status={user.email_verified ? "success" : "warning"}>
                    {user.email_verified
                      ? "Email verified"
                      : "Email not verified"}
                  </Badge>
                  <p className="muted">
                    {user.role === "organizer"
                      ? "Organizer account"
                      : user.role === "admin"
                        ? "Admin account"
                        : "Attendee account"}
                  </p>
                </div>
                <div className="auth-actions">
                  {!user.email_verified && (
                    <Button
                      variant="secondary"
                      disabled={busy}
                      onClick={() => action("verify-email/request")}
                    >
                      Request verification email
                    </Button>
                  )}
                  <Button
                    variant="secondary"
                    disabled={busy}
                    onClick={() => action("logout")}
                  >
                    Log out
                  </Button>
                </div>
                {message && (
                  <p role="status" className="auth-notice">
                    {message}
                  </p>
                )}
              </section>
              <div className="account-grid">
                <section className="card auth-card">
                  <ProfileEditor user={user} onUpdate={setUser} />
                </section>
                <section className="card auth-card">
                  <PasswordEditor />
                </section>
              </div>
              <div className="auth-actions">
                {user.role === "organizer" && (
                  <ButtonLink href="/organizer/events">
                    Organizer studio
                  </ButtonLink>
                )}
                {user.role === "admin" && (
                  <ButtonLink href="/admin/events">Review events</ButtonLink>
                )}
                <Link className="button button-secondary" href="/notifications">
                  Notifications
                </Link>
                <Link className="button button-secondary" href="/events">
                  Explore events →
                </Link>
              </div>
            </>
          )}
        </>
      )}
    </main>
  );
}
