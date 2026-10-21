import { EventOperations } from "@/components/event-operations";

export const metadata = {
  title: "Event operations",
  robots: { index: false, follow: false },
};
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <EventOperations key={id} eventId={id} />;
}
