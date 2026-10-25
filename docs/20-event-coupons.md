# Event coupons

## 2026-10-22 — implementation

Owners can optionally enable coupons in the Tickets step when creating an event. After saving, the event workspace has separate coupon controls, including for approved events. Managers, scanners, viewers, admins and other owners cannot manage another owner's coupons. Codes are not listed on public event responses.

Each event allows up to three codes total, including paused codes. Codes use 1–32 ASCII letters, digits, underscores or hyphens and are case-insensitive. Discounts are whole percentages from 1 through 100; zero-priced ticket categories remain excluded. Codes and percentages are fixed once created; owners can pause/resume. Closed events reject coupon changes.

Checkout accepts one optional code for the entire order. Apply coupon requests a server-calculated quote; reservation recalculates the discount against current category prices and coupon state. Amounts use decimal arithmetic, with the order-wide discount rounded half-up to two decimal places. A 100% coupon confirms a zero-total order immediately, issues tickets and queues delivery without creating a payment attempt. Other coupons must leave a total of at least BDT 0.01. The order snapshots subtotal, discount, code and percentage; payments, receipts and revenue reports use the discounted order total. Existing orders without coupon snapshots remain supported.

Pausing takes the same event lock as payment and checkout, immediately expires unpaid coupon reservations, releases their seats and fails initiated simulated payments. Paid tickets remain valid. Resuming never revives expired reservations: customers start a fresh checkout. Creation also uses the event lock to enforce the three-code cap under concurrency. Changes are audited.

The new coupon table has row-level security enabled and browser-role privileges revoked. No paid services are introduced. Payment remains simulated.

## 2026-10-25 — 100% coupons

Expanded the percentage range to 100 and allowed zero-total orders. Full-discount issuance uses the same transaction and event/category locks as normal checkout, consumes inventory immediately and preserves per-email caps, idempotency, gift delivery and reporting. Paid/fulfilled orders retain the existing internal `paid` status for downstream compatibility; no payment record is created for a 100% coupon. Pausing blocks later use but cannot invalidate already-issued tickets. Verification pending.

## Verification

2026-10-23 — [Final CI](https://github.com/MarzzzSiam/TICKETE/actions/runs/39813813045) passed on commit `5013775`: 151 backend tests and 32 desktop/mobile browser tests, production build, lint, formatting, types and schema validation. Owner/checkout desktop and mobile screenshots were visually reviewed. The final browser assertion targets the coupon error specifically, excluding Next.js's hidden route announcer. Backend tests cover normalization, bounds, authorization, event scoping, atomic draft creation, decimal rounding, replay, payment amounts, pause/resume and concurrent pause/payment and creation. Browser coverage exercises creation controls, owner coupon creation on an approved event, discounted purchase and paused-code rejection.

Migration `events.0003_coupon` was applied to Supabase after all 151 isolated backend tests passed. There are no pending migrations. RLS is enabled and both `anon` and `authenticated` roles lack SELECT privileges on the coupon table. No real coupons, purchases or event closures were created for verification.

## Using coupons

1. For a new event, open the Tickets step and tick **Enable event coupons**. Enter a code and percentage, optionally add a second/third code, then save the draft.
2. For a saved event, open **Organizer studio → Open event → Event coupons**. Tick **Add an optional coupon**, enter both fields and select **Create coupon**. This also works after approval.
3. Use **Pause CODE** or **Resume CODE** beside an existing coupon. Pausing asks for confirmation because unpaid discounted reservations will expire.
4. Buyers select tickets, enter the code next to the price summary and select **Apply coupon**. They see subtotal, discount and total before reserving. Changing ticket quantities requires applying the code again.
5. Restart Django if it is not using automatic reload, then refresh the browser. Existing local PDF/email processing continues unchanged.
