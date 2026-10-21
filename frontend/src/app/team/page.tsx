import { TeamEvents } from "@/components/event-operations";
export const metadata = {
  title: "My event teams",
  robots: { index: false, follow: false },
};
export default function Page() {
  return <TeamEvents />;
}
