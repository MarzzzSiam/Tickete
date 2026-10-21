# Phase 3 — organizer sales and venue operations

## 2026-10-21 — implementation

The owner confirmed ticket PDF email delivery works and requested organizer purchase visibility, volunteer invitations and single-use check-in. This advances the venue stage while keeping unfinished Phase 2 recovery/resend and scheduled expiry cleanup on the backlog.

Inside an organizer event, **Purchases, team and check-in** opens `/organizer/events/{id}/operations`. It shows sold tickets, paid order count, simulated revenue, category totals, attendance and a searchable paginated ticket list with buyer and gift-recipient email addresses. Ticket QR secrets are never returned by this list. Owner-only cancellation blocks future entry without issuing a refund or reducing paid sales totals; already-used tickets cannot be cancelled.

Owners invite a teammate by email with Manager, Scanner or Viewer access. The existing free `process_ticket_jobs` command now also sends invitation emails, retrying failed sends up to five times. Restart the processor after updating. Links expire after seven days and require explicit acceptance by the matching verified email account. Accepting an old link cannot reinstate revoked membership. Owners can change roles, revoke members or revoke pending invitations. Failed invitations can be revoked and replaced. Invite delivery status reports provider acceptance, not guaranteed inbox placement.

| Role | Purchase emails | Summary | Admission | Team controls | Draft editing |
|---|---|---|---|---|---|
| Owner | Yes | Yes | Yes | Yes | Yes |
| Manager | Yes | Yes | Yes | No | Yes |
| Scanner | Scan result only (name/category, no buyer email) | Attendance totals only | Yes | No | No |
| Viewer | No | Yes | No | No | No |
| Admin | Yes | Yes | No | No | No |

Assigned volunteers use **My event teams** after accepting. The scanner supports camera QR and manual ticket ID entry. Both submit the same server admission operation. Each successful scan changes `valid` to `used` atomically and records who admitted the ticket and when. Every authorized scan attempt records its result and a digest of the submitted value, never the raw QR token. Invalid, wrong-event, cancelled and already-used tickets have distinct rejection results; wrong-event responses disclose no attendee details. The event lock serializes permission changes with admission, so a revoked scanner cannot pass a stale membership check. Two simultaneous scans admit exactly one person.

Counts refresh every 15 seconds. Network errors never show admission success. Camera scanning pauses after one result; start it again for the next attendee. The page releases camera tracks when stopped or left. Camera access needs a secure browser context (HTTPS or localhost); manual entry remains available when permission is denied. Physical phone-camera acceptance still needs a real device check. The scanner uses [qr-scanner's documented camera API](https://github.com/nimiq/qr-scanner#readme).

## API

All paths below have `/api/v1/` prefix. Authenticated writes require CSRF; access is checked server-side for the selected event. Private responses use `Cache-Control: no-store`; operations, invitation creation and scanning have separate Redis-backed limits.

- `GET team/events/` — paginated assigned events.
- `POST team/accept/` — verified matching-email invitation acceptance.
- `GET events/{id}/operations/` — role-limited summary.
- `GET events/{id}/attendees/?search=&page=` — owner/manager/admin ticket list.
- `GET/POST events/{id}/team/` — owner membership/invitation management.
- `PATCH events/{id}/team/{member_id}/` — change role or revoke.
- `POST events/{id}/invitations/{invitation_id}/revoke/` — revoke invitation.
- `POST events/{id}/scan/` — `{value, method: "qr" | "manual"}`.
- `POST events/{id}/tickets/{ticket_id}/cancel/` — owner cancellation.

New team and scan-log tables have migrations enabling RLS and revoking Supabase browser-role privileges. Check-in timestamps reference the admitting user. Integration tests and remote migration status will be recorded after verification; do not treat this entry as deployment acceptance.

## Still pending

Ticket recovery/resend and scheduled hold cleanup; full reporting charts and final event-close report; hosted acceptance, physical phone-camera verification, and real volunteer invitation mailbox acceptance. No invitation emails are sent to real recipients during automated checks.
