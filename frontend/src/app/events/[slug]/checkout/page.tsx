import { notFound } from "next/navigation";
import { publicEvent } from "@/lib/public-events";
import { Checkout } from "@/components/checkout";

export const metadata = {
  title: "Checkout",
  robots: { index: false, follow: false },
};
export default async function Page({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const event = await publicEvent(slug);
  if (!event) notFound();
  if (event.closed_at)
    return (
      <main id="main" className="container account-page">
        <h1>This event is closed.</h1>
        <p>
          Ticket sales and admission have ended. Use Find my ticket to recover
          an existing purchase.
        </p>
      </main>
    );
  return <Checkout event={event} />;
}
