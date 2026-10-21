import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { randomBytes, randomUUID } from "node:crypto";
import { execFileSync } from "node:child_process";

test("guest recovers paid tickets with email proof and can request a resend", async ({
  page,
}, info) => {
  test.skip(
    process.env.AUTH_E2E_LIVE !== "1",
    "Disposable CI PostgreSQL only.",
  );
  const root = "http://127.0.0.1:8000/api/v1";
  const email = `recovery-${info.project.name}-${Date.now()}@example.com`;
  const event = await (
    await page.request.get(`${root}/public/events/fictional-checkout-demo/`)
  ).json();
  const csrf = await (await page.request.get(`${root}/auth/csrf/`)).json();
  const token = randomBytes(32).toString("base64url");
  const headers = { "X-CSRFToken": csrf.csrf_token, "X-Checkout-Token": token };
  const created = await page.request.post(`${root}/orders/`, {
    headers,
    data: {
      event_id: event.id,
      buyer_email: email,
      access_token: token,
      idempotency_key: randomUUID(),
      selections: [{ category_id: event.categories[0].id, quantity: 1 }],
      answers: {},
    },
  });
  expect(created.ok()).toBeTruthy();
  const order = await created.json();
  expect(
    (
      await page.request.post(`${root}/orders/${order.id}/payments/`, {
        headers,
        data: { provider: "dummy_bkash", phone: "01700000000" },
      })
    ).ok(),
  ).toBeTruthy();
  expect(
    (
      await page.request.post(`${root}/orders/${order.id}/verify/`, {
        headers,
        data: { otp: "123456" },
      })
    ).ok(),
  ).toBeTruthy();
  await page.goto("/find-my-ticket");
  await page.getByLabel("Email address", { exact: true }).fill(email);
  const pending = page.waitForResponse(
    (r) =>
      r.url().endsWith("/tickets/recovery/") && r.request().method() === "POST",
  );
  await page
    .getByRole("button", { name: "Send recovery code", exact: true })
    .click();
  const started = await pending;
  expect(started.status()).toBe(202);
  const { id } = await started.json();
  // Fixture only: seed a known code in guarded disposable services. Production
  // never exposes a code endpoint. Worker email generation is covered in pytest.
  execFileSync(
    "python",
    [
      "-c",
      `
import os, sys
assert os.environ.get('DJANGO_SETTINGS_MODULE') == 'config.settings.browser_tests'
assert os.environ.get('AUTH_E2E_LIVE') == '1'
import django
django.setup()
from datetime import timedelta
from django.utils import timezone
from apps.tickets.models import TicketRecovery
from apps.tickets.recovery import code_digest
item = TicketRecovery.objects.get(pk=sys.argv[1])
assert item.email.endswith('@example.com')
item.code_digest = code_digest(item, '482961')
item.sent_at = timezone.now()
item.expires_at = item.sent_at + timedelta(minutes=10)
item.save()
`,
      id,
    ],
    { cwd: "../backend", stdio: "pipe" },
  );
  await page.getByLabel("Recovery code", { exact: true }).fill("111111");
  await page
    .getByRole("button", { name: "Find my tickets", exact: true })
    .click();
  await expect(page.getByRole("alert")).toBeVisible();
  await page.getByLabel("Recovery code", { exact: true }).fill("482961");
  await page
    .getByRole("button", { name: "Find my tickets", exact: true })
    .click();
  await expect(page.getByText(order.number, { exact: false })).toBeVisible();
  await page
    .getByRole("button", { name: "Resend to original recipient", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText("original recipient");
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
  await page.getByRole("heading", { level: 1 }).click();
  await page.screenshot({
    path: `../docs/screenshots/recovery-${info.project.name}.png`,
    fullPage: true,
  });
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Send recovery code", exact: true }),
  ).toBeVisible();
  await expect(page.getByText(order.number, { exact: false })).toHaveCount(0);
});
