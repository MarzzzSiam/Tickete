# Phase 2 completion — ticket recovery and form clarity

## 2026-10-21 — implementation

The owner requested the unfinished recovery/resend flow and reported invisible checkout fields. This increment closes those gaps before reporting/launch work.

**Find my ticket** (`/find-my-ticket`) is available in navigation and the footer. Guests and account holders enter their buyer or gift-recipient email, receive a six-digit code and verify it in the same browser page. Every valid address receives the same queued response and code email, even with no matching orders, so the request endpoint does not reveal purchase history. A code expires ten minutes after sending and permits five guesses. Codes are single use and stored only as a keyed digest; browser capability tokens are stored only as a SHA-256 digest. The browser keeps access in memory and clears it on reload, departure or account change. Verified access expires after 30 minutes.

Verified users see a paginated list of their paid orders. Recipients can download existing private PDFs. Gift buyers can request delivery to the original recipient but do not receive the recipient's PDF through recovery. Resending never accepts a new destination and reuses existing ticket IDs, QR codes and PDF assets. Used/cancelled tickets remain blocked. Pending jobs are not duplicated; completed or exhausted jobs are reset under a row lock. Each order has a one-minute resend cooldown. Recovery requests are limited by IP (30/minute) and email (5/hour), with five guesses per challenge regardless of IP. Redis failure denies recovery requests.

The existing free `process_ticket_jobs` processor now sends recovery codes as well as tickets and invitations. It retries failed code mail up to five times within a 30-minute queue lifetime. It also releases up to 100 expired pending holds every minute using the same event-before-order locking order as payment. Paid orders and sold counts are not changed by cleanup. Without the processor, emails remain queued and scheduled cleanup pauses; checkout still ignores expired holds when calculating available seats.

Native text inputs, number/date/email fields, textareas and selects now receive visible outlines even when a component lacks its own class. Labels have spacing above their fields; checkboxes retain their compact layout. File uploads use a dashed border. Keyboard focus is highlighted in brand blue.

## Local acceptance

1. Restart Django, Next.js and `python manage.py process_ticket_jobs` in the backend virtual environment.
2. Open **Find my ticket**, enter an email used for a test purchase and keep the page open.
3. Enter the actual code received by email (not the simulated-payment OTP).
4. Download the ticket PDF or select **Resend to original recipient**. Check the original recipient's inbox/spam folder.
5. Verify a used ticket is still rejected by check-in after resending.
6. Inspect checkout details/payment and event creation fields on desktop and mobile.

## Verification and remaining work

[CI run 39647608207](https://github.com/MarzzzSiam/TICKETE/actions/runs/39647608207) passed 126 backend and 26 browser tests, production build, lint, formatting, type checks and OpenAPI validation on implementation commit `d6c9484`. Desktop/mobile checkout, event-editor and recovery screenshots were reviewed. No real email recipients are contacted by automated tests. Browser OTP fixtures only run with guarded disposable CI services; production has no code-reading endpoint. Supabase migrations were applied on 2026-10-21 with none pending. The recovery table has RLS enabled and denies SELECT to both browser roles. Real Gmail recovery-code/resend inbox acceptance remains a local manual check; SMTP was not invoked against real recipients during automated verification. Physical phone-camera and real volunteer invitation acceptance remain pending from Phase 3. Phase 4 reporting charts, final report and launch hardening follow next; payment remains simulated.
