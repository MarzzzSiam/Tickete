import { AcceptTeamInvitation } from "@/components/event-operations";
export const metadata = {
  title: "Accept team invitation",
  robots: { index: false, follow: false },
};
export default function Page() {
  return <AcceptTeamInvitation />;
}
