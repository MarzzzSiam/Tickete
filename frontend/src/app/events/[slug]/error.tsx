"use client";
import { Button } from "@/components/ui";
export default function Error({ reset }: { reset: () => void }) {
  return (
    <main id="main" className="container account-page">
      <h1>We couldn’t load this event.</h1>
      <p>The event service may be temporarily unavailable.</p>
      <Button onClick={reset}>Try again</Button>
    </main>
  );
}
