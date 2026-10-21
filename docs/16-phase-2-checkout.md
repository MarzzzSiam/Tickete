# Phase 2 — checkout increment, 2026-10-21

The owner reports event creation/viewing and direct Gmail SMTP delivery working. These are user-confirmed manual results; a hosted worker has not been deployed. Zero-cost development remains required.

## Decisions confirmed today

- Exclude zero-price categories from purchasing for now. Their drafts can still exist; checkout rejects them.
- Attendee names remain optional when collection is enabled. When disabled, checkout rejects supplied attendee names.
- Payments are simulations only, not real bKash/Nagad transactions. No money or SMS is sent.

## Implemented

`/events/{slug}/checkout` offers Tickets → Details → Payment → Done. Guests may purchase; signed-in users get their email prefilled. Gift recipient details and event custom answers are validated. The server calculates decimal BDT prices and stores an immutable event/category/answer snapshot.

Orders reserve inventory for up to ten minutes (shortened at sales/event end). The Event row is locked before categories and existing order/payment rows, serializing purchases within an event. Paid quantities plus unexpired pending orders count against the normalized buyer email across all categories; gifts count against the buyer. Inactive, foreign-event and zero-price categories are rejected. Expired reservations stop consuming availability immediately based on the server timestamp, even before their status is cleaned up; reads/payment actions persist expiry and release holds.

The browser creates a random 256-bit checkout capability and stores it in sessionStorage, never in the URL. Only its SHA-256 digest is stored in PostgreSQL. Every status/payment/cancellation request requires the capability, even for a logged-in buyer. A buyer email or order UUID alone grants no access. Requests retain an idempotency key and exact payload across uncertain network errors. Repeated identical requests return the same order; altered requests are rejected. Closing the browser session loses this capability until the recovery feature is implemented. Do not share storage contents or checkout tokens.

The dummy gateway accepts `123456`, visibly shown as a test code, with five attempts before terminal failure. The displayed fictional phone `01700000000` avoids requiring real payment details. There is one payment attempt per order; after terminal failure or expiry, create a new order. Success converts holds, updates sold counts and issues tickets atomically. Repeated/concurrent confirmations return the existing result. Each ticket has a random unique code and private random QR payload, but this increment does not render or deliver QR images.

## API

All routes have `/api/v1/` prefix and trailing slash. Unsafe requests require CSRF. Capability header: `X-Checkout-Token`. Responses are `Cache-Control: no-store`; checkout requests are limited per IP through Redis. All four new tables have RLS enabled and Supabase browser-role grants revoked by the privacy migration.

| Route | Method | Purpose |
|---|---|---|
| orders | POST | Validate selection and reserve, idempotently |
| orders/{id}/status | GET | Private order state and lazy expiry |
| orders/{id}/payments | POST | Initiate simulated payment |
| orders/{id}/verify | POST | Verify fixed test OTP and issue once |
| orders/{id}/cancel | POST | Release a pending reservation |

## Ticket design review

Open `/ticket-preview`. The fictional HTML sample uses the original horizontal logo, brand blue, serif event title, black ticket outline, perforated stub, event details and ticket/order identity. The eventual PDF will be one page per ticket with a black-on-white QR of at least 35 mm and an unobstructed quiet zone. The placeholder is deliberately not scannable.

The supplied MD says: “Before building the PDF module, show me an HTML mock-up of the design for approval.” This increment supplies that reviewable mock-up. PDF generation, font embedding and real QR readability must be verified after approval; the HTML screenshot is not proof of PDF rendering.

## Manual test

1. Restart backend/frontend. Open an approved event whose sales window is currently open and choose tickets.
2. Select a paid category, enter buyer email, optionally gift it or add names, and reserve.
3. Reload: the pending order should restore in the same tab, with remaining server-derived time.
4. Select a simulated provider, enter `01700000000`, and use `123456`. Wrong codes reduce the remaining attempt budget; five failures release the reservation.
5. Confirm ticket codes appear once, with an explicit notice that PDF/email delivery is not implemented. Reload and confirm the same order/tickets remain.
6. Try a fresh checkout in a separate browser session with the same buyer email to exercise the aggregate limit. Existing paid tickets continue to count.

## 2026-10-21 — approved PDF and local delivery processor

The owner approved the blue-and-white HTML design. The PDF uses embedded Inter/Playfair fonts, the original logo, event banner when supplied, Dhaka time and a 45 mm QR including its quiet zone. One page is generated per ticket. Template values are escaped and the renderer cannot fetch arbitrary URLs or local files. The fictional two-page preview was generated without touching the database or sending email.

Successful payment creates a durable delivery row in the same transaction. A free local processor locks one job at a time, generates a private PDF, sends it to the recipient and sends a separate receipt for gifts. It retries failures up to five times with increasing delays. Completed recipient sends are retained if the buyer receipt fails. SMTP acceptance is not an inbox-delivery guarantee. A crash after SMTP accepts a message but before the database commits can produce a duplicate email; email delivery is at-least-once.

From `D:\TICKETÉ\backend`, keep a third VS Code terminal open:

```powershell
.\.venv\Scripts\python.exe manage.py process_ticket_jobs
```

Use `--once` to process currently due jobs and exit. Stopping the processor retains queued work; restart it to resume. The processor needs the same database, private storage and email settings as Django. It works on Windows without Celery, Docker or a paid Render worker. Do not start another production worker against a different local media folder.

This PC has portable Windows Pango libraries at `.tools/pdf-runtime/ucrt64/bin`, automatically detected by local settings. They are ignored by Git. On another Windows PC, follow the official WeasyPrint/MSYS2 Pango setup and set `WEASYPRINT_DLL_DIRECTORIES` to its DLL folder. Linux CI installs Pango via apt. Fonts and their OFL licenses are committed; system runtime binaries are not.

After migrating and restarting Django/frontend, buy tickets, refresh the confirmation status and use **Download tickets PDF** when ready. `GET /api/v1/orders/{id}/tickets.pdf` requires the same checkout token header, returns no-store PDF bytes and never exposes storage paths or credentials. The delivery queue table is protected by the RLS migration too. The earlier no-delivery notice in this document describes the first checkout increment and is superseded here.

Failed jobs report only `pdf_failed` or `email_failed`, without provider secrets. After fixing configuration, an administrator can reset the failed delivery's attempt count and next-attempt timestamp using Django; a dedicated recovery/resend interface is still pending. Existing orders created before this queue feature are not automatically emailed.

## Still required before Phase 2 is complete

Email-OTP recovery/resend; expiry cleanup scheduling; deployment acceptance and a real end-to-end user mailbox check. Gate scanning is a later phase: the ticket QR is generated now but no gate-validation UI is claimed complete. Payment is still simulated.

## Verification — 2026-10-21

[CI run 39556864201](https://github.com/MarzzzSiam/TICKETE/actions/runs/39556864201) passed 100 PostgreSQL-backed backend tests (89% coverage) and 20 browser tests. Coverage includes inventory races, repeated payment verification, private downloads, real PDF generation, gift receipts and retry behavior. Local production build, type checks, lint and schema validation passed. The final original licensed Playfair font was restored and its embedding verified locally, alongside Inter. Both pages of the fictional PDF were visually inspected and their QR codes decoded from rendered page images. Maximum-length title, venue and attendee fields were also visually checked.

Applied `orders.0001`, `tickets.0001`/`0002`, `payments.0001` and `core.0003`/`0004` to the configured Supabase development database; `migrate --check` reports no pending migrations. No customer emails were sent during these checks. A live purchase with the local processor running is the remaining mailbox acceptance step.
