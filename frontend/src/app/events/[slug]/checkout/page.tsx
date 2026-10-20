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
  return <Checkout event={event} />;
}
