import type { Metadata } from "next";
import { ArrowUpRight, Ticket } from "lucide-react";
import { ButtonLink, Pill } from "@/components/ui";
export const metadata: Metadata = { title: "Explore events" };
export default function EventsPage() {
  return (
    <main id="main" className="container inner-page">
      <Pill>THE GOOD STUFF IS ON ITS WAY</Pill>
      <h1>
        Your next <em>“I was there.”</em>
      </h1>
      <p className="page-lead">A new home for live moments in Bangladesh.</p>
      <div className="empty-state card">
        <Ticket size={48} strokeWidth={1.3} />
        <h2>The stage is being set.</h2>
        <p>
          There are no events on sale yet. We’re getting TICKETÉ ready for its
          first organizers and their communities.
        </p>
        <ButtonLink href="/start">
          Have an event in mind? <ArrowUpRight size={18} />
        </ButtonLink>
      </div>
    </main>
  );
}
