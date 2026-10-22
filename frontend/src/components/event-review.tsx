"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import * as Dialog from "@radix-ui/react-dialog";
import { AccountError, apiRequest } from "@/lib/auth-api";
import { type EventPage, type EventRecord } from "@/lib/events";
import { EventPreview } from "./event-workspace";
import { Button, Pill } from "./ui";

export function EventReview() {
  const [events, setEvents] = useState<EventPage | null>(null);
  const [selected, setSelected] = useState<EventRecord | null>(null);
  const [problem, setProblem] = useState("");
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const [page, setPage] = useState(1);
  useEffect(() => {
    let active = true;
    apiRequest<EventPage>(`admin/events?page=${page}`, "GET", undefined, true)
      .then((data) => {
        if (active) setEvents(data);
      })
      .catch((error) => {
        if (active)
          setProblem(
            error instanceof AccountError
              ? error.message
              : "Could not load the review queue.",
          );
      });
    return () => {
      active = false;
    };
  }, [revision, page]);
  async function decide(approved: boolean) {
    if (!selected) return;
    if (!approved && !reason.trim()) {
      setProblem("Enter a rejection reason.");
      return;
    }
    setBusy(true);
    setProblem("");
    try {
      await apiRequest(
        `admin/events/${selected.id}/${approved ? "approve" : "reject"}`,
        "POST",
        approved ? undefined : { reason },
        true,
      );
      setSelected(null);
      setReason("");
      setRevision(revision + 1);
    } catch (error) {
      setProblem(
        error instanceof AccountError
          ? error.message
          : "Review could not be saved.",
      );
    } finally {
      setBusy(false);
    }
  }
  return (
    <main id="main" className="container account-page">
      <Pill>ADMIN REVIEW</Pill>
      <h1>Give good events the go-ahead.</h1>
      <p className="auth-actions">
        <Link className="button button-secondary" href="/notifications">
          Notifications
        </Link>
        <Link className="button button-secondary" href="/account">
          Account
        </Link>
      </p>
      {problem && !selected && (
        <p role="alert" className="auth-error">
          {problem}
        </p>
      )}
      {!events && !problem && <p role="status">Loading pending events…</p>}
      {events?.count === 0 && <p>No events are waiting for review.</p>}
      <Dialog.Root
        open={!!selected}
        onOpenChange={(open) => {
          if (!open && !busy) {
            setSelected(null);
            setProblem("");
          }
        }}
      >
        <div className="event-list">
          {events?.results.map((event) => (
            <article className="card auth-card" key={event.id}>
              <h2>{event.title}</h2>
              <p>{event.venue}</p>
              <Dialog.Trigger asChild>
                <Button
                  variant="secondary"
                  onClick={() => {
                    setSelected(event);
                    setReason("");
                    setProblem("");
                  }}
                >
                  Review {event.title}
                </Button>
              </Dialog.Trigger>
            </article>
          ))}
        </div>
        <Dialog.Portal>
          <Dialog.Overlay className="dialog-overlay" />
          <Dialog.Content className="dialog-panel event-review-dialog">
            <Dialog.Title>Review event</Dialog.Title>
            <Dialog.Description>
              Check the event details and ticket categories before making a
              decision.
            </Dialog.Description>
            {selected && <EventPreview event={selected} />}
            <label className="field">
              Rejection reason
              <textarea
                className="field-input"
                rows={3}
                maxLength={2000}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
            </label>
            {problem && (
              <p role="alert" className="auth-error">
                {problem}
              </p>
            )}
            <div className="auth-actions">
              <Button loading={busy} onClick={() => decide(true)}>
                Approve event
              </Button>
              <Button
                disabled={busy}
                variant="secondary"
                onClick={() => decide(false)}
              >
                Reject event
              </Button>
              <Dialog.Close asChild>
                <Button disabled={busy} variant="secondary">
                  Close review
                </Button>
              </Dialog.Close>
            </div>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
      <div className="auth-actions">
        {page > 1 && (
          <Button variant="secondary" onClick={() => setPage(page - 1)}>
            Previous page
          </Button>
        )}
        {events?.next && (
          <Button variant="secondary" onClick={() => setPage(page + 1)}>
            Next page
          </Button>
        )}
      </div>
    </main>
  );
}
