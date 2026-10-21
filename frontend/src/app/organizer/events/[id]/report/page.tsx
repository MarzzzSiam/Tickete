import { EventReport } from "@/components/event-report";
export const metadata = {
  title: "Event report",
  robots: { index: false, follow: false },
};
export default async function Page({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <EventReport key={id} eventId={id} />;
}
