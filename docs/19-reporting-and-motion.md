# Phase 4 — reporting and public-page motion

## 2026-10-22 — implementation

The owner requested the next stage plus subtle particles, a floating hero ticket and a continuously scrolling category strip. Reporting is now available from **Event operations → Dashboard and final report**.

The live dashboard includes tickets sold by day, category sales, daily simulated revenue and check-in progress. All figures have visible labels and numeric values, plus a category capacity/sold/unsold/attendance table. Native bar charts avoid a further runtime dependency; dates group by Asia/Dhaka. Cancelled tickets stay in paid revenue/sold totals, but are separate from no-shows. Unlimited categories show no finite unsold count; inactive categories remain in historical reporting. Owner, Manager, Viewer and Admin can read reports; Scanners cannot.

Only the verified owner can explicitly close an approved event, after a confirmation explaining that this is permanent. Closure uses the same event lock as checkout, payment and admission, releases all pending reservations, stops sales and check-in and stores a fixed aggregate report on the event. Repeated closure returns the existing snapshot. Cancellation is disabled after closure to preserve report consistency. Dashboard reads also take the event lock for consistent aggregates. Small aggregate reports are generated synchronously inside closure, avoiding a paid worker or asynchronous report failure state. No existing real event is closed by this implementation or its automated tests.

Public home/event-list backgrounds have 16 low-opacity blue particles. The homepage ticket gently floats without changing its existing rotation; the category strip loops right-to-left with duplicate content hidden from assistive technology. **Pause motion** stops all three effects. Reduced-motion preferences disable animation and show a static wrapping category list. Particle layers cannot receive pointer events; operational screens have no particles. The homepage FAQ now describes the working guest/gift checkout and clearly identifies simulated payments.

## Acceptance and remaining launch work

### 2026-10-22 — site-wide particle follow-up

Later visual revision: the owner preferred the supplied glowing-light reference over spheres. The current design uses 2–4px light cores with diffuse blue-violet halos, no spherical shading, and 36–60 second drift durations. All-page coverage and motion accessibility remain. Both desktop/mobile browser checks and changed-file formatting passed; the mobile form screenshot was reviewed.

At the owner's request, the shared root-layout particle layer now appears on every page, superseding the public-only scope above. There are 36 particles with three sizes, spherical gradient highlights, soft shadows and subtle distant blur. The layer stays behind content and cannot intercept clicks. Pause and reduced-motion support continue to apply globally. This visual change does not change launch readiness or introduce a paid dependency.

Verification: local lint, TypeScript and changed-file formatting checks passed. Both desktop and mobile motion browser tests passed, including reduced motion and usable login inputs on a non-public page. Homepage and mobile login screenshots were visually reviewed. No database changes or backend test runs were needed for this visual follow-up.

Supabase migration `events.0002_final_report` was applied on 2026-10-22 with none pending; it adds report storage without closing existing events. [Final CI run 39691667338](https://github.com/MarzzzSiam/TICKETE/actions/runs/39691667338) passed 134 backend tests and all 30 browser tests on commit `df7eedf`, plus production build, lint, formatting, type checks and schema validation. The initial mobile table keyboard-access failure was fixed by making scrollable table/chart regions keyboard-focusable. Desktop/mobile reporting and motion screenshots were visually reviewed. Reduced motion and pause controls passed browser checks. No real event was closed; real-device and hosted acceptance remain outstanding. Automated tests use disposable PostgreSQL/Redis and a dedicated fictional event for close/report browser checks. Do not test closing a real event unless it is finished: closure cannot be reversed through the app.

Next after this increment: real phone-camera and invitation/recovery mailbox acceptance; performance/load checks with realistic event sizes; a database backup/restore drill; deployment configuration and end-to-end hosted acceptance. Free local development remains supported. Production launch is not claimed, and no paid resources are provisioned. CSV and PDF report export are V2 in the build brief.
## Launch acceptance still required

- [ ] Exercise a real phone camera over HTTPS, including duplicate/manual entry and a revoked volunteer.
- [ ] Receive invitation and recovery codes in real inboxes; verify gift recipient PDF and buyer receipt destinations.
- [ ] Run a realistic burst/concurrency and report-query load test on a staging dataset; define expected event size and response-time targets before testing.
- [ ] Verify backups by restoring into a separate database and checking orders, ticket uniqueness, team access and private PDF availability.
- [ ] Choose a hosting setup that respects the zero-cost constraint; verify Django/Next.js, private storage and a continuously running worker together. A local processor only works while the PC/process remains running.
- [ ] Review production settings, trusted hosts/origins, HTTPS cookies, secret handling, log redaction and recovery procedures.
- [ ] Run a hosted create → approve → guest purchase → email PDF → invite → scan → close → final-report acceptance journey with fictional data.
- [ ] Obtain the owner's release decision. Simulated payment remains prominently labelled; real payment processing is outside the current milestone.
