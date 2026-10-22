# Event coupons

## 2026-10-22 — implementation

Owners can optionally enable coupons in the Tickets step when creating an event. After saving, the event workspace has separate coupon controls, including for approved events. Managers, scanners, viewers, admins and other owners cannot manage another owner's coupons. Codes are not listed on public event responses.

Each event allows up to three codes total, including paused codes. Codes use 1–32 ASCII letters, digits, underscores or hyphens and are case-insensitive. Discounts are whole percentages from 1 through 99; free tickets remain excluded. Codes and percentages are fixed once created; owners can pause/resume. Closed events reject coupon changes.

Checkout accepts one optional code for the entire order. Apply coupon requests a server-calculated quote; reservation recalculates the discount against current category prices and coupon state. Amounts use decimal arithmetic, with the order-wide discount rounded half-up to two decimal places. Totals below BDT 0.01 are rejected. The order snapshots subtotal, discount, code and percentage; payments, receipts and revenue reports use the discounted order total. Existing orders without coupon snapshots remain supported.

Pausing takes the same event lock as payment and checkout, immediately expires unpaid coupon reservations, releases their seats and fails initiated simulated payments. Paid tickets remain valid. Resuming never revives expired reservations: customers start a fresh checkout. Creation also uses the event lock to enforce the three-code cap under concurrency. Changes are audited.

The new coupon table has row-level security enabled and browser-role privileges revoked. No paid services are introduced. Payment remains simulated.

## Verification

Pending isolated PostgreSQL/Redis CI and browser acceptance. Backend tests cover normalization, bounds, authorization, event scoping, atomic draft creation, decimal rounding, replay, payment amounts, pause/resume and concurrent pause/payment and creation. Browser coverage exercises creation controls, owner coupon creation on an approved event, discounted purchase and paused-code rejection.

Apply migration `events.0003_coupon` only after isolated checks pass, then restart Django. No real event needs to be modified for verification.
