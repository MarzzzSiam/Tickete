import type { Metadata } from "next";
import { ArrowUpRight, Ticket } from "lucide-react";
import { ButtonLink, Pill } from "@/components/ui";
import Link from "next/link";
import { publicEvents } from "@/lib/public-events";
import { dhakaTime, type EventPage } from "@/lib/events";
export const metadata: Metadata = { title: "Explore events" };
export default async function EventsPage({
  searchParams,
}: {
  searchParams: Promise<{ search?: string; page?: string }>;
}) {
  const params = await searchParams;
  const search = params.search || "";
  const page = Math.max(1, Math.min(10000, Number(params.page) || 1));
  let data: EventPage | null = null;
  try {
    data = await publicEvents(search, page);
  } catch {
    /* Render an honest retry state below. */
  }
  return (
    <main id="main" className="container inner-page">
      <Pill>THE GOOD STUFF IS ON ITS WAY</Pill>
      <h1>
        Your next <em>“I was there.”</em>
      </h1>
      <p className="page-lead">A new home for live moments in Bangladesh.</p>
      <form className="event-search" action="/events">
        <label className="field">
          Search events
          <input
            className="field-input"
            name="search"
            defaultValue={search}
            maxLength={180}
          />
        </label>
        <button className="button button-secondary" type="submit">
          Search
        </button>
      </form>
      {data?.results.length ? (
        <>
          <div className="event-list">
            {data.results.map((event) => (
              <article className="card auth-card" key={event.id}>
                <Pill>APPROVED EVENT</Pill>
                <h2>{event.title}</h2>
                <p>
                  {dhakaTime(event.starts_at)} · {event.venue}
                </p>
                <Link className="auth-link" href={`/events/${event.slug}`}>
                  View event →
                </Link>
              </article>
            ))}
          </div>
          <div className="auth-actions">
            {page > 1 && (
              <Link
                className="auth-link"
                href={`/events?search=${encodeURIComponent(search)}&page=${page - 1}`}
              >
                Previous page
              </Link>
            )}
            {data.next && (
              <Link
                className="auth-link"
                href={`/events?search=${encodeURIComponent(search)}&page=${page + 1}`}
              >
                Next page
              </Link>
            )}
          </div>
        </>
      ) : (
        <div className="empty-state card">
          <Ticket size={48} strokeWidth={1.3} />
          <h2>The stage is being set.</h2>
          <p>
            {data
              ? "No approved events match this view yet. Check back soon or create your own event."
              : "We couldn’t reach the event service. Please try again shortly."}
          </p>
          <ButtonLink href="/start">
            Have an event in mind? <ArrowUpRight size={18} />
          </ButtonLink>
        </div>
      )}
    </main>
  );
}
