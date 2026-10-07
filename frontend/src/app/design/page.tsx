import type { Metadata } from "next";
import { DesignPreview } from "@/components/design-preview";
import { Pill } from "@/components/ui";
export const metadata: Metadata = {
  title: "Design system preview",
  robots: { index: false, follow: false },
};
export default function DesignPage() {
  return (
    <main id="main" className="container inner-page">
      <Pill>INTERNAL · DESIGN PREVIEW 0.1</Pill>
      <h1>
        Small details.
        <br />
        <em>One unmistakable feeling.</em>
      </h1>
      <p className="page-lead">
        The building blocks of TICKETÉ. Explore the colors, typography, controls
        and states before they become the full experience.
      </p>
      <DesignPreview />
    </main>
  );
}
