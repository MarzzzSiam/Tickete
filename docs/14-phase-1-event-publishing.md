# Event publishing increment — 2026-10-18

This continues Phase 1 after authentication. It does not start checkout/payment Phase 2.

## Implemented behavior

- Organizer-owned private drafts with title, description, venue, UTC event/sales times, per-order and per-email/event cap, attendee-name switch, ticket categories and custom fields.
- Categories use decimal BDT, nullable unlimited capacity and nonnegative prices. Zero-price payment behavior remains undecided for Phase 2; creating a zero-price category does not enable checkout.
- Nested categories/fields are replaced atomically on draft save. Existing IDs must belong to the event; unknown/duplicate IDs are rejected. Pending/approved records cannot be edited. Rejected edits restore draft status before resubmission.
- Submission requires verified organizer email, complete valid schedules, a not-ended event and at least one active category. Banner is optional in this increment. The single configured cap applies both per order and per buyer email/event in the future purchase service.
- Admin-only pending queue and approve/reject actions; rejection requires a reason. Row locks serialize decisions. Approval assigns a readable slug with the event UUID suffix. Audit records and in-app notifications commit in the same transaction as the decision.
- Public APIs return approved records only. Owner/reviewer and rejection feedback are excluded. Public pages render on the server and include title/description/Open Graph data. Search is by title, with paginated lists. Sales are explicitly unavailable until Phase 2.
- JPEG/PNG/WebP banners are limited to 5 MB and 16 megapixels, re-encoded to JPEG and stored through the existing storage adapter. Public reads require an approved event; private preview reads require owner or admin. A race after upload can leave an unused storage object; cleanup is a later maintenance task.

## Routes and contract

All API paths begin `/api/v1/` and end with `/`. Cookie authentication and CSRF protect private mutations.

| Path | Methods | Access |
|---|---|---|
| events | GET, POST | Organizer's own list / create draft |
| events/{id} | GET, PATCH | Owner; edits only draft/rejected |
| events/{id}/preview | GET | Owner preview |
| events/{id}/submit | POST | Verified owner |
| events/{id}/banner | GET, POST | Owner uploads; owner/admin reads |
| admin/events | GET | Admin pending queue |
| admin/events/{id}/approve, reject | POST | Admin; pending only |
| public/events | GET | Anonymous, search and page parameters |
| public/events/{slug}, public/events/{slug}/banner | GET | Anonymous approved content |
| notifications | GET | Current recipient, paginated |
| notifications/{id}/read | POST | Current recipient only |

Categories and fields are nested in POST/PATCH event documents rather than separate child endpoints for this increment. Protected fields (owner, state, slug, reviewer and inventory counts) are not accepted from clients. Full array entries are required even during PATCH. Omitting an array retains it; sending an empty array removes it from a draft.

Screens: `/organizer/events`, `/organizer/events/new`, `/organizer/events/{id}`, `/admin/events`, `/notifications`, `/events`, `/events/{slug}`. Dates entered in the organizer form are interpreted in Asia/Dhaka regardless of the browser timezone.

## Manual acceptance

1. Start frontend/backend as documented in the README. Create an organizer account and verify its email using the configured worker/provider.
2. Open Organizer studio from Account. Save a draft with dates, an active category and optional custom questions/banner. Reload to check persistence.
3. Submit; confirm edits are unavailable while pending and the event is absent from public listings.
4. A separately provisioned admin opens `/admin/events`, reviews details and approves or rejects. Check the notification list under each account.
5. After approval, open the public link while logged out. After rejection, edit/save and resubmit. Verify another organizer cannot read the private draft.

For isolated CI only, `seed_demo_accounts` creates fictional verified organizer/admin accounts when local settings, `TICKETE_ALLOW_DEMO_SEED=1`, and a private `DEMO_ACCOUNT_PASSWORD` are set. It never changes existing users and is disabled in hosted settings. Do not seed these accounts into a live customer database. Real administrators should be provisioned deliberately through Django's `createsuperuser`, not public signup.

## Remaining Phase 1 acceptance

Live email/worker delivery, hosted Supabase banner storage, deployment-domain share previews, manual visual review, advanced date/category listing filters and the full three-category demo event remain separate follow-ups. Team-manager editing comes with Phase 3 team membership; only owners edit in this increment. SMTP or API acceptance never proves inbox delivery. See the email setup guide.
