# ADR 0001: Requirements reconciliation

Status: source precedence, purchase limit and design/implementation plan accepted by the user. Later-phase open questions remain listed below. Date: 2026-10-07.

The user supplied the MD, ERD and logos first, then supplied the base PRD and features list and requested work based on the MD. The MD explicitly requires conflicts to be raised and design approval before application code. Prepare the design and task plan now; do not decide conflicting business behavior silently.

## Confirmed decisions

1. **Purchase limit:** the user selected "Per order and per email across the event". Enforce the configured maximum on each order and on the aggregate for normalized buyer email within the event. Count paid quantities plus unexpired pending reservations; released/failed/expired orders do not consume the cap. Proposed cancellation treatment: retain paid quantities in this cap because cancellation does not refund or release inventory. Serialize checks with inventory writes; a checkout-only count would race.
2. **Document precedence:** the user selected "Yes, use the MD as the latest authority". This places find-my-ticket in Phase 2, records admin audit actions in MVP, and uses the detailed role matrix over broad statements that all team members can see buyer data. The explicit user decision on the purchase cap overrides the MD.

## Other discrepancies and proposals covered by that decision

- MD logo guidance mentions QR center decoration; its later PDF rules require unobstructed black-on-white QR. Proposal: no logo overlay on any scannable QR.
- Held ticket lifecycle versus ticket creation after payment: propose that SeatHold represents the pre-payment reservation, and Ticket records are created as Valid only on successful payment. No live QR exists for an unpaid reservation. If persistent Held tickets are required, specify their release state before implementation.
- Immediate download versus asynchronous PDF generation: display a preparation state, then enable authorized download when ready; no false claim that a PDF or email is ready.
- PRD asks whether a gift buyer also receives the PDF, while MD specifies recipient PDF email and buyer receipt email, plus tickets/download on confirmation. Follow MD: recipient receives the PDF email; buyer receives a receipt and can view/download through their authorized checkout confirmation. Neither route is public; recipient recovery remains bound to recipient email proof.
- ERD CheckInLog enum omits wrong-event although the scan requirements include it. Propose a `wrong_event` result with no unrelated attendee disclosure.
- PRD open question on English/Bangla is answered by MD: English MVP, translation-ready layout.
- Event status text in the ERD stops at ended; MD includes report ready. Propose storing report generation status separately while exposing Report ready as the final display state.

## Unanswered product choices (not blockers for Phase 0)

2026-10-21 update: the owner selected **exclude free tickets for now** and **keep attendee names optional** when collection is enabled. These resolve the corresponding questions below. Checkout rejects zero-price categories; it does not implement a free-payment bypass.

- Are zero-price tickets allowed? Do not implement a payment bypass until decided in Phase 2.
- Is a minimum submission notice required? Proposed MVP: no arbitrary notice period; reject invalid or already-ended event schedules.
- Should organizer staff see payment phone numbers? Proposed default: no; keep them out of attendee APIs and logs.
- Must attendee names be required when collection is enabled? The sources mandate showing fields but do not clearly state requiredness.
- Who can cancel tickets besides the owner? Proposed MVP: owner only; retain historical revenue and sold count, and do not reopen inventory automatically.

Missing reference screenshots and vector logos do not block design planning. Supabase, hosting and email configuration are needed for integration and deployment, not for writing this plan. Never send production secrets in chat; use local environment files or provider secret settings.
