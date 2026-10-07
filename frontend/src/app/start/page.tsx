import type { Metadata } from "next";
import { ArrowLeft, Sparkles } from "lucide-react";
import { ButtonLink, Pill } from "@/components/ui";
export const metadata: Metadata = { title: "For organizers" };
export default function StartPage() {
  return (
    <main id="main" className="container inner-page">
      <Pill>FOR THE ONES WHO MAKE IT HAPPEN</Pill>
      <h1>
        Every great event
        <br />
        starts with <em>someone.</em>
      </h1>
      <div className="empty-state card">
        <Sparkles size={45} strokeWidth={1.3} />
        <h2>That someone could be you.</h2>
        <p>
          Organizer registration is coming soon. This is an early look at
          TICKETÉ; account creation and event publishing aren’t open yet.
        </p>
        <ButtonLink href="/" variant="secondary">
          <ArrowLeft size={18} /> Back to the experience
        </ButtonLink>
      </div>
    </main>
  );
}
