"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { AccountError, accountRequest } from "@/lib/auth-api";
import { Button, Pill } from "./ui";

export type AuthMode = "login" | "signup" | "forgot" | "reset" | "verify";
const fields = z.object({
  email: z.string().optional(),
  password: z.string().optional(),
  full_name: z.string().optional(),
  confirm: z.string().optional(),
  role: z.enum(["buyer", "organizer"]).optional(),
});
type FormData = z.infer<typeof fields>;
const copy = {
  login: ["Welcome back.", "Your next moment is waiting.", "Log in"],
  signup: [
    "Your story starts here.",
    "One account for the moments you find and the events you create.",
    "Create account",
  ],
  forgot: [
    "Let’s get you back in.",
    "Enter your account email to request a password reset link.",
    "Request reset link",
  ],
  reset: [
    "A fresh start.",
    "Choose a new password for your TICKETÉ account.",
    "Reset password",
  ],
  verify: [
    "Make it official.",
    "Confirm your email to get ready to publish your first event.",
    "Verify email",
  ],
};

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const [notice, setNotice] = useState("");
  const [problem, setProblem] = useState("");
  const [link, setLink] = useState<{
    challenge_id: string;
    token: string;
  } | null>(null);
  const [linkLoaded, setLinkLoaded] = useState(false);
  const needsLink = mode === "reset" || mode === "verify";
  const schema = useMemo(
    () =>
      fields.superRefine((data, ctx) => {
        const add = (field: keyof FormData, message: string) =>
          ctx.addIssue({ code: "custom", path: [field], message });
        if (
          ["login", "signup", "forgot"].includes(mode) &&
          !z.email().safeParse(data.email?.trim()).success
        )
          add("email", "Enter a valid email address.");
        if (["login", "signup", "reset"].includes(mode) && !data.password)
          add("password", "Enter your password.");
        if ((data.password?.length || 0) > 128)
          add("password", "Use no more than 128 characters.");
        if (mode === "signup" || mode === "reset") {
          if ((data.password?.length || 0) < 8)
            add("password", "Use at least 8 characters.");
          if (data.password !== data.confirm)
            add("confirm", "Passwords don’t match.");
        }
        if (mode === "signup" && !data.full_name?.trim())
          add("full_name", "Enter your full name.");
      }),
    [mode],
  );
  const {
    register,
    handleSubmit,
    setError,
    formState: { errors, isSubmitting },
  } = useForm<FormData>({
    resolver: zodResolver(schema),
    defaultValues: { role: "buyer" },
  });

  useEffect(() => {
    if (!needsLink) return;
    const fragment = new URLSearchParams(window.location.hash.slice(1));
    const challenge_id = fragment.get("challenge_id");
    const token = fragment.get("token");
    if (challenge_id && token) {
      setLink({ challenge_id, token });
      window.history.replaceState(
        null,
        "",
        window.location.pathname + window.location.search,
      );
    }
    setLinkLoaded(true);
  }, [needsLink]);

  async function submit(data: FormData) {
    setProblem("");
    setNotice("");
    try {
      if (mode === "signup") {
        await accountRequest("register", "POST", {
          email: data.email?.trim(),
          password: data.password,
          full_name: data.full_name?.trim(),
          role: data.role,
        });
        // Registration and login are separate. A login failure must not look like a failed signup.
        setNotice("Your account is created. Log in to continue.");
      } else if (mode === "login") {
        await accountRequest("login", "POST", {
          email: data.email?.trim(),
          password: data.password,
        });
        router.replace("/account");
      } else if (mode === "forgot") {
        await accountRequest("password-reset/request", "POST", {
          email: data.email?.trim(),
        });
        setNotice(
          "If an eligible account exists, a reset link will be sent. Delivery may be delayed.",
        );
      } else if (link) {
        await accountRequest(
          mode === "verify" ? "verify-email/confirm" : "password-reset/confirm",
          "POST",
          {
            ...link,
            ...(mode === "reset" ? { password: data.password } : {}),
          },
        );
        setNotice(
          mode === "verify"
            ? "Your email is verified. You can return to your account."
            : "Password updated. Log in with your new password.",
        );
        setLink(null);
      }
    } catch (error) {
      if (error instanceof AccountError) {
        setProblem(error.message);
        for (const [field, message] of Object.entries(error.fields)) {
          if (
            ["email", "password", "full_name", "role", "confirm"].includes(
              field,
            )
          )
            setError(field as keyof FormData, { message });
          else setProblem(message);
        }
      } else setProblem("Something went wrong. Please try again.");
    }
  }

  function input(
    name: "email" | "password" | "full_name" | "confirm",
    label: string,
    type = "text",
    autoComplete = "",
  ) {
    return (
      <label className="field" htmlFor={name}>
        <span>{label}</span>
        <input
          {...register(name)}
          id={name}
          type={type}
          autoComplete={autoComplete}
          className="field-input"
          maxLength={name === "full_name" ? 150 : name === "email" ? 254 : 128}
          aria-invalid={!!errors[name]}
          aria-describedby={errors[name] ? `${name}-error` : undefined}
        />
        {errors[name] && (
          <span className="auth-field-error" id={`${name}-error`}>
            {errors[name]?.message}
          </span>
        )}
      </label>
    );
  }

  return (
    <main id="main" className="container auth-page">
      <section className="auth-story">
        <Pill>YOUR PEOPLE. YOUR MOMENTS.</Pill>
        <h1>{copy[mode][0]}</h1>
        <p>{copy[mode][1]}</p>
        <div className="auth-stamp" aria-hidden="true">
          TICKETÉ
          <br />
          <span>GOOD TIMES AHEAD</span>
        </div>
      </section>
      <section className="card auth-card" aria-label={copy[mode][2]}>
        <h2>{copy[mode][2]}</h2>
        {problem && (
          <p className="auth-error" role="alert">
            {problem}
          </p>
        )}
        {notice ? (
          <div role="status">
            <p className="auth-notice">{notice}</p>
            <Link
              className="auth-link"
              href={mode === "verify" ? "/account" : "/login"}
            >
              {mode === "verify" ? "Go to your account" : "Go to log in"} →
            </Link>
          </div>
        ) : needsLink && linkLoaded && !link ? (
          <p role="alert">
            This link is missing its verification details. Open the complete
            link from your email, or{" "}
            <Link
              className="auth-link"
              href={mode === "reset" ? "/forgot-password" : "/account"}
            >
              request a new one
            </Link>
            .
          </p>
        ) : (
          <form
            onSubmit={handleSubmit(submit)}
            noValidate
            className="auth-form"
          >
            {mode === "signup" &&
              input("full_name", "Full name", "text", "name")}
            {["login", "signup", "forgot"].includes(mode) &&
              input("email", "Email address", "email", "email")}
            {["login", "signup", "reset"].includes(mode) &&
              input(
                "password",
                mode === "reset" ? "New password" : "Password",
                "password",
                mode === "login" ? "current-password" : "new-password",
              )}
            {(mode === "signup" || mode === "reset") && (
              <>
                <p className="field-hint">
                  Use at least 8 characters. Avoid common passwords and personal
                  details.
                </p>
                {input(
                  "confirm",
                  "Confirm password",
                  "password",
                  "new-password",
                )}
              </>
            )}
            {mode === "signup" && (
              <label className="field" htmlFor="role">
                <span>I’m here to</span>
                <select {...register("role")} id="role" className="field-input">
                  <option value="buyer">Discover and attend events</option>
                  <option value="organizer">Organize events</option>
                </select>
              </label>
            )}
            <Button
              type="submit"
              loading={isSubmitting}
              disabled={needsLink && !link}
            >
              {copy[mode][2]}
            </Button>
            {mode === "login" && (
              <Link className="auth-link" href="/forgot-password">
                Forgot your password?
              </Link>
            )}
          </form>
        )}
        {mode === "login" && (
          <p className="auth-bottom">
            New here?{" "}
            <Link className="auth-link" href="/signup">
              Create an account
            </Link>
          </p>
        )}
        {mode === "signup" && (
          <p className="auth-bottom">
            Already have an account?{" "}
            <Link className="auth-link" href="/login">
              Log in
            </Link>
          </p>
        )}
      </section>
    </main>
  );
}
