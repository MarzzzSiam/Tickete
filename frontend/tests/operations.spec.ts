import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { randomBytes, randomUUID } from "node:crypto";

test("organizer sees purchases, invites scanners and rejects duplicate admission", async ({
  page,
}, info) => {
  test.skip(
    process.env.AUTH_E2E_LIVE !== "1",
    "Uses disposable CI services only.",
  );
  await page.goto("/login");
  await page.getByLabel("Email address").fill("demo-organizer@example.com");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.DEMO_ACCOUNT_PASSWORD!);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page).toHaveURL(/\/account$/);
  const root = "http://127.0.0.1:8000/api/v1";
  const event = await (
    await page.request.get(`${root}/public/events/fictional-checkout-demo/`)
  ).json();
  const csrf = await (await page.request.get(`${root}/auth/csrf/`)).json();
  const token = randomBytes(32).toString("base64url");
  const headers = { "X-CSRFToken": csrf.csrf_token, "X-Checkout-Token": token };
  const email = `operations-${info.project.name}-${Date.now()}@example.com`;
  const create = await page.request.post(`${root}/orders/`, {
    headers,
    data: {
      event_id: event.id,
      buyer_email: email,
      is_gift: false,
      access_token: token,
      idempotency_key: randomUUID(),
      selections: [{ category_id: event.categories[0].id, quantity: 2 }],
      answers: {},
    },
  });
  expect(create.ok()).toBeTruthy();
  const order = await create.json();
  expect(
    (
      await page.request.post(`${root}/orders/${order.id}/payments/`, {
        headers,
        data: { provider: "dummy_bkash", phone: "01700000000" },
      })
    ).ok(),
  ).toBeTruthy();
  const paid = await (
    await page.request.post(`${root}/orders/${order.id}/verify/`, {
      headers,
      data: { otp: "123456" },
    })
  ).json();
  await page.goto(`/organizer/events/${event.id}/operations`);
  await expect(
    page.getByRole("heading", { name: "Purchases and attendees" }),
  ).toBeVisible();
  await page.getByLabel("Search email, name or ticket ID").fill(email);
  await page
    .getByRole("button", { name: "Search purchases", exact: true })
    .click();
  await expect(
    page.getByText("2 matching tickets.", { exact: false }),
  ).toBeVisible();
  await page
    .getByLabel("Ticket ID", { exact: true })
    .fill(paid.tickets[0].code);
  await page
    .getByRole("button", { name: "Check in ticket", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Entry approved" }),
  ).toBeVisible();
  await page
    .getByLabel("Ticket ID", { exact: true })
    .fill(paid.tickets[0].code);
  await page
    .getByRole("button", { name: "Check in ticket", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Already checked in" }),
  ).toBeVisible();
  page.once("dialog", (dialog) => dialog.accept());
  await page
    .getByRole("button", { name: "Cancel ticket", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Cancel ticket", exact: true }),
  ).toHaveCount(0);
  await page
    .getByLabel("Ticket ID", { exact: true })
    .fill(paid.tickets[1].code);
  await page
    .getByRole("button", { name: "Check in ticket", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Ticket cancelled" }),
  ).toBeVisible();
  const invitee = `volunteer-${info.project.name}-${Date.now()}@example.com`;
  await page.getByLabel("Volunteer or teammate email").fill(invitee);
  await page
    .getByRole("button", { name: "Invite teammate", exact: true })
    .click();
  await expect(
    page.getByText("Invitation queued.", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByText(`${invitee} · scanner`, { exact: true }),
  ).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: `../docs/screenshots/operations-${info.project.name}.png`,
    fullPage: true,
  });
  // Permission-denied hardware fallback must be actionable, not a pretend scan.
  await page.evaluate(() => {
    navigator.mediaDevices.getUserMedia = async () => {
      throw new DOMException("Denied", "NotAllowedError");
    };
  });
  await page.getByRole("button", { name: "Start QR camera" }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Camera could not start" }),
  ).toBeVisible();
});
