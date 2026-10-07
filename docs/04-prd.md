# Requirements baseline

This summary supplements, and does not replace, the supplied PRD and features PDF. The user confirmed the MD as the latest authority except for ticket limits, which apply both per order and per buyer email across an event. See the source reconciliation decision for implementation assumptions.

| Requirement IDs | Delivery phase | Scope |
|---|---|---|
| FR-A1–A3 | 1 | Registration, cookie JWT login, verification, reset, roles |
| Features 4.1 Profile | 1 | Name, phone and password changes |
| FR-E1–E7 | 1 | Draft event, categories, sales window, limits, attendee-name switch, custom fields, preview |
| FR-D1–D3 | 1 | Approval queue, required rejection reason, notifications, public slug |
| FR-P1 | 1 | Server-rendered event and share metadata |
| FR-P2–P6 | 2 | Guest/login checkout, inventory, hold, gifting, sold-out handling |
| FR-Y1–Y4 | 2 | Simulated mobile banking, OTP, failure/timeout, payment attempts and interface |
| FR-T1–T5 | 2 | Secure QR, readable ID, PDF, delivery, download, recovery |
| FR-C1–C4 | 3 | Camera/manual scan, atomic admission, result and live count |
| FR-M1–M3 | 3 | Expiring invitations, roles, revocation |
| FR-R1–R2 | 4 | Dashboard and final report |

V2: FR-A4, E8, D4 user-facing suspension/audit views, T6, C5, M4, R3. Audit record creation is in MVP under the confirmed MD security rules. Later: FR-P7, duplicate events and real payments.

Out of scope: refund workflows, payouts, platform fees, native apps and assigned seat maps. Ticket cancellation to refuse admission is explicitly in scope; it does not issue a refund.

Pilot targets from the PRD are acceptance goals, not measured results: zero overselling and duplicate admissions; purchase under two minutes; scan request response under one second; 95% of delivery emails within one minute; 60% checkout completion. Approval turnaround depends on human admin availability; the under-15-minute publishing goal cannot be guaranteed by software alone.
