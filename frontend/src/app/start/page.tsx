import type { Metadata } from "next";
import { ArrowUpRight, Sparkles } from "lucide-react";
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
          Create your account and choose “Organize events” to get started. Event
          publishing is still being built; your account is the first step.
        </p>
        <ButtonLink href="/signup" variant="secondary">
          Create your account <ArrowUpRight size={18} />
        </ButtonLink>
      </div>
    </main>
  );
}
