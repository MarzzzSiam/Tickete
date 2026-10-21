import { TicketRecovery } from "@/components/ticket-recovery";
export const metadata = {
  title: "Find my ticket · TICKETÉ",
  robots: { index: false, follow: false },
};
export default function Page() {
  return <TicketRecovery />;
}
