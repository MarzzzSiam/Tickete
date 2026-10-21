import type { Metadata } from "next";
import Image from "next/image";
import { notFound } from "next/navigation";
import { publicApiBase, publicEvent } from "@/lib/public-events";
import { dhakaTime } from "@/lib/events";
import { Pill, ButtonLink } from "@/components/ui";
type Props = { params: Promise<{ slug: string }> };
export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const event = await publicEvent(slug);
  if (!event) return { title: "Event not found" };
  const site = process.env.SITE_URL || "http://127.0.0.1:3000";
  const browserApi = process.env.NEXT_PUBLIC_API_BASE_URL || publicApiBase;
  return {
    title: event.title,
    description: event.description.slice(0, 160),
    openGraph: {
      title: event.title,
      description: event.description.slice(0, 160),
      url: `${site}/events/${slug}`,
      ...(event.has_banner
        ? {
            images: [
              {
                url: `${browserApi}/public/events/${slug}/banner/`,
                alt: event.title,
              },
            ],
          }
        : {}),
    },
  };
}
export default async function Page({ params }: Props) {
  const { slug } = await params;
  const event = await publicEvent(slug);
  if (!event) notFound();
  const browserApi = process.env.NEXT_PUBLIC_API_BASE_URL || publicApiBase;
  return (
    <main id="main" className="container account-page">
      <Pill>APPROVED EVENT · BDT</Pill>
      <h1>{event.title}</h1>
      {event.has_banner && (
        <Image
          className="event-banner"
          style={{ width: "100%", height: "auto" }}
          src={`${browserApi}/public/events/${slug}/banner/`}
          alt={`${event.title} event banner`}
          width={1200}
          height={600}
          unoptimized
        />
      )}
      <div className="account-grid">
        <section className="card auth-card">
          <h2>Be there.</h2>
          <p>
            {dhakaTime(event.starts_at)} – {dhakaTime(event.ends_at)}
          </p>
          <p>Asia/Dhaka · {event.venue}</p>
          <p className="event-description">{event.description}</p>
        </section>
        <section className="card auth-card">
          <h2>Tickets</h2>
          {event.categories
            .filter((c) => c.is_active)
            .map((c) => (
              <div className="event-ticket-row" key={c.id}>
                <strong>{c.name}</strong>
                <p>
                  BDT {c.price} · {c.seat_limit ?? "Unlimited"} capacity
                </p>
              </div>
            ))}
          <p>
            Sales window: {dhakaTime(event.sales_start)} –{" "}
            {dhakaTime(event.sales_end)} (Asia/Dhaka)
          </p>
          <p>
            Maximum {event.max_per_order} per order and per buyer email for this
            event.
          </p>
          <ButtonLink href={`/events/${slug}/checkout`}>
            Choose tickets
          </ButtonLink>
          <p className="auth-notice">
            Test checkout · no real money is charged. PDF and email delivery are
            still being built.
          </p>
        </section>
      </div>
    </main>
  );
}
