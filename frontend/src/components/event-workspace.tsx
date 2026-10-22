"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useFieldArray, useForm, useWatch } from "react-hook-form";
import Image from "next/image";
import Link from "next/link";
import {
  AccountError,
  accountRequest,
  apiRequest,
  type Profile,
} from "@/lib/auth-api";
import { dhakaTime, type EventRecord, type EventPage } from "@/lib/events";
import { Badge, Button, ButtonLink, Pill } from "./ui";

function message(error: unknown): string {
  if (!(error instanceof AccountError))
    return "Something went wrong. Please try again.";
  const details = Object.entries(error.fields)
    .map(([key, value]) => `${key.replaceAll("_", " ")}: ${value}`)
    .join(" ");
  return details || error.message;
}

export function EventPreview({ event }: { event: EventRecord }) {
  return (
    <section className="event-preview">
      {event.has_banner && (
        <Image
          className="event-banner"
          style={{ width: "100%", height: "auto" }}
          src={`${process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api/v1"}/events/${event.id}/banner/`}
          alt={`${event.title} banner`}
          width={1000}
          height={500}
          unoptimized
        />
      )}
      <Pill>EVENT PREVIEW</Pill>
      <h2>{event.title}</h2>
      <p>{dhakaTime(event.starts_at)} · Asia/Dhaka</p>
      <p>{event.venue || "Venue to be added"}</p>
      <p className="event-description">{event.description}</p>
      <h3>Ticket categories</h3>
      {event.categories.map((category, index) => (
        <p key={category.id || index}>
          {category.name} · BDT {category.price} ·{" "}
          {category.seat_limit ?? "Unlimited"} seats
          {!category.is_active && " · Inactive"}
        </p>
      ))}
      <p>
        Limit: {event.max_per_order} tickets per order and per buyer email
        across this event.
      </p>
      {event.form_fields.length > 0 && (
        <>
          <h3>Checkout questions</h3>
          {event.form_fields.map((field, index) => (
            <p key={field.id || index}>
              {field.label} · {field.type}
              {field.required && " · Required"}
              {field.options.length > 0 && ` (${field.options.join(", ")})`}
            </p>
          ))}
        </>
      )}
    </section>
  );
}

type EditorData = {
  title: string;
  description: string;
  venue: string;
  starts_at: string;
  ends_at: string;
  sales_start: string;
  sales_end: string;
  max_per_order: number;
  collect_attendee_names: boolean;
  categories: {
    recordId?: string;
    name: string;
    price: string;
    seat_limit: string;
    is_active: boolean;
  }[];
  form_fields: {
    recordId?: string;
    label: string;
    type: "text" | "number" | "dropdown" | "checkbox";
    required: boolean;
    optionsText: string;
  }[];
};
function localDate(value: string | null) {
  return value
    ? new Date(new Date(value).getTime() + 6 * 3600000)
        .toISOString()
        .slice(0, 16)
    : "";
}

function EventEditor({
  event,
  onSave,
  onDirty,
}: {
  event: EventRecord | null;
  onSave: (event: EventRecord) => void;
  onDirty: (dirty: boolean) => void;
}) {
  const [step, setStep] = useState(0);
  const [problem, setProblem] = useState("");
  const [notice, setNotice] = useState("");
  const [upload, setUpload] = useState<File | null>(null);
  const form = useForm<EditorData>({
    defaultValues: {
      title: event?.title || "",
      description: event?.description || "",
      venue: event?.venue || "",
      starts_at: localDate(event?.starts_at || null),
      ends_at: localDate(event?.ends_at || null),
      sales_start: localDate(event?.sales_start || null),
      sales_end: localDate(event?.sales_end || null),
      max_per_order: event?.max_per_order || 10,
      collect_attendee_names: event?.collect_attendee_names || false,
      categories:
        event?.categories.map((c) => ({
          recordId: c.id,
          name: c.name,
          price: c.price,
          seat_limit: c.seat_limit?.toString() || "",
          is_active: c.is_active,
        })) || [],
      form_fields:
        event?.form_fields.map((f) => ({
          recordId: f.id,
          label: f.label,
          type: f.type,
          required: f.required,
          optionsText: f.options.join(", "),
        })) || [],
    },
  });
  const categories = useFieldArray({
    control: form.control,
    name: "categories",
  });
  const customFields = useFieldArray({
    control: form.control,
    name: "form_fields",
  });
  const values = useWatch({ control: form.control }) as EditorData;
  const dirty = form.formState.isDirty;
  useEffect(() => {
    onDirty(dirty);
    return () => onDirty(false);
  }, [dirty, onDirty]);
  function payload(data: EditorData) {
    const dates = Object.fromEntries(
      (["starts_at", "ends_at", "sales_start", "sales_end"] as const).map(
        (key) => [
          key,
          data[key] ? new Date(`${data[key]}:00+06:00`).toISOString() : null,
        ],
      ),
    );
    return {
      ...data,
      ...dates,
      categories: data.categories.map((c) => ({
        ...(c.recordId ? { id: c.recordId } : {}),
        name: c.name,
        price: c.price,
        seat_limit: c.seat_limit ? Number(c.seat_limit) : null,
        is_active: c.is_active,
      })),
      form_fields: data.form_fields.map((f, index) => ({
        ...(f.recordId ? { id: f.recordId } : {}),
        label: f.label,
        type: f.type,
        required: f.required,
        options:
          f.type === "dropdown"
            ? f.optionsText
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean)
            : [],
        sort_order: index,
      })),
    };
  }
  async function save(data: EditorData) {
    setProblem("");
    setNotice("");
    try {
      const result = await apiRequest<EventRecord>(
        event ? `events/${event.id}` : "events",
        event ? "PATCH" : "POST",
        payload(data),
        true,
      );
      onSave(result);
      setNotice("Draft saved. Submit it when you’re ready for admin review.");
      if (upload) {
        const body = new FormData();
        body.append("banner", upload);
        try {
          onSave(
            await apiRequest<EventRecord>(
              `events/${result.id}/banner`,
              "POST",
              body,
              true,
            ),
          );
          setUpload(null);
        } catch (error) {
          setProblem(
            `Your draft was saved, but the banner was not uploaded. ${message(error)}`,
          );
        }
      }
    } catch (error) {
      setProblem(message(error));
    }
  }
  const steps = ["Details", "Tickets", "Form fields", "Review"];
  return (
    <div className="event-editor">
      <form
        className="card auth-card auth-form"
        onSubmit={form.handleSubmit(save, () => setStep(0))}
        noValidate
      >
        <nav className="event-steps" aria-label="Event creation steps">
          {steps.map((label, index) => (
            <button
              type="button"
              key={label}
              aria-current={step === index ? "step" : undefined}
              onClick={() => setStep(index)}
            >
              {index + 1}. {label}
            </button>
          ))}
        </nav>
        <h2>{steps[step]}</h2>
        <div hidden={step !== 0} className="auth-form">
          <label className="field">
            Event title
            <input
              className="field-input"
              {...form.register("title", { required: "Enter an event title." })}
              maxLength={180}
            />
          </label>
          {form.formState.errors.title && (
            <p role="alert" className="auth-field-error">
              {form.formState.errors.title.message}
            </p>
          )}
          <label className="field">
            Description
            <textarea
              className="field-input"
              rows={5}
              {...form.register("description")}
              maxLength={20000}
            />
          </label>
          <label className="field">
            Venue
            <input
              className="field-input"
              {...form.register("venue")}
              maxLength={300}
            />
          </label>
          <p className="muted">
            All times below are Bangladesh time (Asia/Dhaka).
          </p>
          {(
            [
              ["starts_at", "Event starts"],
              ["ends_at", "Event ends"],
              ["sales_start", "Sales start"],
              ["sales_end", "Sales end"],
            ] as const
          ).map(([key, label]) => (
            <label className="field" key={key}>
              {label}
              <input
                className="field-input"
                type="datetime-local"
                {...form.register(key)}
              />
            </label>
          ))}
          <label className="field">
            Event banner
            <input
              type="file"
              accept="image/png,image/jpeg,image/webp"
              onChange={(e) => setUpload(e.target.files?.[0] || null)}
            />
            <span className="field-hint">
              JPEG, PNG or WebP. Up to 5 MB and 16 megapixels.
              {event?.has_banner && " A banner is already saved."}
            </span>
          </label>
        </div>
        <div hidden={step !== 1} className="auth-form">
          <label className="field">
            Ticket limit per order and per email
            <input
              className="field-input"
              type="number"
              min={1}
              max={1000}
              {...form.register("max_per_order", { valueAsNumber: true })}
            />
          </label>
          <label className="event-checkbox">
            <input
              type="checkbox"
              {...form.register("collect_attendee_names")}
            />
            Collect attendee names
          </label>
          {categories.fields.map((field, index) => (
            <fieldset className="event-fieldset" key={field.id}>
              <legend>Category {index + 1}</legend>
              <label className="field">
                Category name
                <input
                  className="field-input"
                  {...form.register(`categories.${index}.name`)}
                />
              </label>
              <label className="field">
                Price (BDT)
                <input
                  className="field-input"
                  type="number"
                  min={0}
                  step="0.01"
                  {...form.register(`categories.${index}.price`)}
                />
              </label>
              <label className="field">
                Seat limit (blank = unlimited)
                <input
                  className="field-input"
                  type="number"
                  min={1}
                  {...form.register(`categories.${index}.seat_limit`)}
                />
              </label>
              <label className="event-checkbox">
                <input
                  type="checkbox"
                  {...form.register(`categories.${index}.is_active`)}
                />
                Active category
              </label>
              <Button
                type="button"
                variant="secondary"
                onClick={() => categories.remove(index)}
              >
                Remove category {index + 1}
              </Button>
            </fieldset>
          ))}
          <Button
            type="button"
            variant="secondary"
            onClick={() =>
              categories.append({
                name: "",
                price: "0.00",
                seat_limit: "",
                is_active: true,
              })
            }
          >
            Add ticket category
          </Button>
        </div>
        <div hidden={step !== 2} className="auth-form">
          <p className="muted">
            Optional questions collected at checkout. Avoid requesting sensitive
            personal information.
          </p>
          {customFields.fields.map((field, index) => (
            <fieldset className="event-fieldset" key={field.id}>
              <legend>Question {index + 1}</legend>
              <label className="field">
                Question label
                <input
                  className="field-input"
                  {...form.register(`form_fields.${index}.label`)}
                />
              </label>
              <label className="field">
                Question type
                <select
                  className="field-input"
                  {...form.register(`form_fields.${index}.type`)}
                >
                  <option value="text">Text</option>
                  <option value="number">Number</option>
                  <option value="dropdown">Dropdown</option>
                  <option value="checkbox">Checkbox</option>
                </select>
              </label>
              {values.form_fields[index]?.type === "dropdown" && (
                <label className="field">
                  Options (comma separated)
                  <input
                    className="field-input"
                    {...form.register(`form_fields.${index}.optionsText`)}
                  />
                </label>
              )}
              <label className="event-checkbox">
                <input
                  type="checkbox"
                  {...form.register(`form_fields.${index}.required`)}
                />
                Answer required
              </label>
              <Button
                type="button"
                variant="secondary"
                onClick={() => customFields.remove(index)}
              >
                Remove question {index + 1}
              </Button>
            </fieldset>
          ))}
          <Button
            type="button"
            variant="secondary"
            onClick={() =>
              customFields.append({
                label: "",
                type: "text",
                required: false,
                optionsText: "",
              })
            }
          >
            Add question
          </Button>
        </div>
        {step === 3 && (
          <EventPreview
            event={
              {
                ...payload(values),
                id: event?.id || "preview",
                slug: null,
                status: "draft",
                rejection_reason: "",
                has_banner: false,
              } as EventRecord
            }
          />
        )}
        {step === 3 && (
          <p>
            Review your details, save the draft, then submit it from the event
            page. Email verification is required for submission. Pending and
            approved events cannot be edited.
          </p>
        )}
        {problem && (
          <p role="alert" className="auth-error">
            {problem}
          </p>
        )}
        {notice && (
          <p role="status" className="auth-notice">
            {notice}
          </p>
        )}
        <div className="auth-actions">
          {step > 0 && (
            <Button
              type="button"
              variant="secondary"
              onClick={() => setStep(step - 1)}
            >
              Back
            </Button>
          )}
          {step < 3 && (
            <Button type="button" onClick={() => setStep(step + 1)}>
              Next step
            </Button>
          )}
          <Button
            type="submit"
            variant="secondary"
            loading={form.formState.isSubmitting}
          >
            Save draft
          </Button>
        </div>
      </form>
      <aside className="card auth-card event-live-preview">
        <Pill>LIVE PREVIEW</Pill>
        <h2>{values.title || "Your event title"}</h2>
        <p>{values.venue || "Your venue"}</p>
        <p className="event-description">
          {values.description ||
            "Tell people what makes your event worth being there for."}
        </p>
        {values.categories.map((category, index) => (
          <p key={index}>
            {category.name || "Ticket category"} · BDT{" "}
            {category.price || "0.00"}
          </p>
        ))}
      </aside>
    </div>
  );
}

export function EventWorkspace({ eventId }: { eventId?: string }) {
  const router = useRouter();
  const [profile, setProfile] = useState<Profile | null>(null);
  const [event, setEvent] = useState<EventRecord | null>(null);
  const [events, setEvents] = useState<EventPage | null>(null);
  const [problem, setProblem] = useState("");
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [dirty, setDirty] = useState(false);
  const [page, setPage] = useState(1);
  useEffect(() => {
    let active = true;
    async function load() {
      try {
        const user = await accountRequest<Profile>(
          "me",
          "GET",
          undefined,
          true,
        );
        if (!active) return;
        setProfile(user);
        if (user.role !== "organizer" && (!eventId || eventId === "new"))
          return;
        if (eventId && eventId !== "new") {
          const item = await apiRequest<EventRecord>(
            `events/${eventId}`,
            "GET",
            undefined,
            true,
          );
          if (active) setEvent(item);
        } else if (!eventId) {
          const list = await apiRequest<EventPage>(
            `events?page=${page}`,
            "GET",
            undefined,
            true,
          );
          if (active) setEvents(list);
        }
      } catch (error) {
        if (active) setProblem(message(error));
      } finally {
        if (active) setLoading(false);
      }
    }
    void load();
    return () => {
      active = false;
    };
  }, [eventId, page]);
  async function submit() {
    if (!event) return;
    setBusy(true);
    setProblem("");
    try {
      setEvent(
        await apiRequest<EventRecord>(
          `events/${event.id}/submit`,
          "POST",
          undefined,
          true,
        ),
      );
    } catch (error) {
      setProblem(message(error));
    } finally {
      setBusy(false);
    }
  }
  function saved(item: EventRecord) {
    setEvent(item);
    if (eventId === "new") router.replace(`/organizer/events/${item.id}`);
  }
  return (
    <main id="main" className="container account-page">
      <Pill>ORGANIZER STUDIO</Pill>
      <h1>
        {eventId ? event?.title || "Make something happen." : "Your events."}
      </h1>
      <p className="auth-actions">
        <Link className="button button-secondary" href="/organizer/events">
          All events
        </Link>
        <Link className="button button-secondary" href="/notifications">
          Notifications
        </Link>
        <Link className="button button-secondary" href="/account">
          Account
        </Link>
      </p>
      {problem && (
        <p role="alert" className="auth-error">
          {problem}
        </p>
      )}
      {loading ? (
        <p role="status">Loading…</p>
      ) : !profile ? (
        <ButtonLink href="/login">Log in</ButtonLink>
      ) : profile.role !== "organizer" && !event ? (
        <p>
          An organizer account is required.{" "}
          <Link href="/account" className="auth-link">
            View your account
          </Link>
          .
        </p>
      ) : (
        <>
          {!profile.email_verified && (
            <p className="auth-notice">
              You can save drafts now.{" "}
              <Link className="auth-link" href="/account">
                Verify your email
              </Link>{" "}
              before submitting for approval.
            </p>
          )}
          {event && (
            <div className="event-status">
              <ButtonLink href={`/organizer/events/${event.id}/operations`}>
                Purchases, team and check-in
              </ButtonLink>
              <Badge>{event.status}</Badge>
              {event.rejection_reason && (
                <p>Review feedback: {event.rejection_reason}</p>
              )}
              {event.status === "draft" && (
                <Button
                  onClick={submit}
                  disabled={!profile.email_verified || dirty}
                  loading={busy}
                >
                  Submit for approval
                </Button>
              )}
              {dirty && <p>Save your changes before submitting.</p>}
              {event.slug && (
                <ButtonLink href={`/events/${event.slug}`}>
                  View public event
                </ButtonLink>
              )}
            </div>
          )}
          {eventId === "new" ||
          (event && ["draft", "rejected"].includes(event.status)) ? (
            <EventEditor
              key={event ? `${event.id}:${event.updated_at}` : "new"}
              event={event}
              onSave={saved}
              onDirty={setDirty}
            />
          ) : event ? (
            <div className="card auth-card">
              <EventPreview event={event} />
            </div>
          ) : (
            !eventId && (
              <>
                <div className="auth-actions">
                  <ButtonLink href="/organizer/events/new">
                    Create event
                  </ButtonLink>
                </div>
                <div className="event-list">
                  {events?.results.map((item) => (
                    <article className="card auth-card" key={item.id}>
                      <Badge>{item.status}</Badge>
                      <h2>{item.title}</h2>
                      <p>{dhakaTime(item.starts_at)}</p>
                      <Link
                        className="button button-secondary"
                        href={`/organizer/events/${item.id}`}
                      >
                        Open event →
                      </Link>
                    </article>
                  ))}
                  {events?.count === 0 && (
                    <p>No events yet. Start with a draft.</p>
                  )}
                </div>
                <div className="auth-actions">
                  {page > 1 && (
                    <Button
                      onClick={() => setPage(page - 1)}
                      variant="secondary"
                    >
                      Previous page
                    </Button>
                  )}
                  {events?.next && (
                    <Button
                      onClick={() => setPage(page + 1)}
                      variant="secondary"
                    >
                      Next page
                    </Button>
                  )}
                </div>
              </>
            )
          )}
        </>
      )}
    </main>
  );
}
