export type Category = {
  id?: string;
  name: string;
  price: string;
  seat_limit: number | null;
  is_active: boolean;
  sold_count?: number;
};
export type CustomField = {
  id?: string;
  label: string;
  type: "text" | "number" | "dropdown" | "checkbox";
  required: boolean;
  options: string[];
  sort_order: number;
};
export type EventRecord = {
  id: string;
  title: string;
  slug: string | null;
  description: string;
  venue: string;
  has_banner: boolean;
  starts_at: string | null;
  ends_at: string | null;
  sales_start: string | null;
  sales_end: string | null;
  closed_at?: string | null;
  max_per_order: number;
  collect_attendee_names: boolean;
  categories: Category[];
  form_fields: CustomField[];
  status: "draft" | "pending" | "approved" | "rejected";
  rejection_reason: string;
  updated_at?: string;
};
export type EventPage = {
  count: number;
  next: string | null;
  results: EventRecord[];
};
export function dhakaTime(value: string | null) {
  return value
    ? new Intl.DateTimeFormat("en-GB", {
        timeZone: "Asia/Dhaka",
        dateStyle: "medium",
        timeStyle: "short",
      }).format(new Date(value))
    : "Not scheduled";
}
