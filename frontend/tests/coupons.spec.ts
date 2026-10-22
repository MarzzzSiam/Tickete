import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";

test("owner creates and pauses a coupon; checkout uses the discounted total", async ({
  page,
  browser,
}, info) => {
  test.skip(process.env.AUTH_E2E_LIVE !== "1", "Disposable CI services only.");
  const id = execFileSync(
    "python",
    [
      "-c",
      `
import os, uuid
assert os.environ.get('DJANGO_SETTINGS_MODULE')=='config.settings.browser_tests'
assert os.environ.get('AUTH_E2E_LIVE')=='1'
import django
django.setup()
from datetime import timedelta
from django.utils import timezone
from apps.accounts.models import User
from apps.events.models import Event, TicketCategory
now=timezone.now()
event=Event.objects.create(owner=User.objects.get(email='demo-organizer@example.com'),title='Fictional coupon showcase',slug='coupon-'+uuid.uuid4().hex,status='approved',starts_at=now+timedelta(days=1),ends_at=now+timedelta(days=2),sales_start=now-timedelta(days=1),sales_end=now+timedelta(hours=2))
TicketCategory.objects.create(event=event,name='General',price=500,seat_limit=20)
print(str(event.pk)+'|'+event.slug)
`,
    ],
    { cwd: "../backend", encoding: "utf8" },
  )
    .trim()
    .split("|");
  await page.goto("/login");
  await page.getByLabel("Email address").fill("demo-organizer@example.com");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.DEMO_ACCOUNT_PASSWORD!);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page).toHaveURL(/\/account$/);
  await page.goto("/organizer/events/new");
  await page.getByRole("button", { name: "2. Tickets", exact: true }).click();
  await expect(page.getByLabel("Coupon code", { exact: true })).toHaveCount(0);
  await page.getByLabel("Enable event coupons").check();
  await page.getByLabel("Coupon code", { exact: true }).fill("DRAFT10");
  await page.getByLabel("Percentage off", { exact: true }).fill("10");
  await page.getByRole("button", { name: "Add another coupon" }).click();
  await page.getByRole("button", { name: "Add another coupon" }).click();
  await expect(
    page.getByRole("button", { name: "Add another coupon" }),
  ).toBeDisabled();
  // A separate approved fixture exercises coupon changes without changing event approval.
  await page.goto(`/organizer/events/${id[0]}`);
  await page.getByLabel("Add an optional coupon").check();
  await page.getByLabel("Coupon code", { exact: true }).fill("Tickete10");
  await page.getByLabel("Percentage off", { exact: true }).fill("10");
  await page
    .getByRole("button", { name: "Create coupon", exact: true })
    .click();
  await expect(
    page.getByRole("button", { name: "Pause TICKETE10" }),
  ).toBeVisible();
  await page.screenshot({
    path: `../docs/screenshots/coupons-owner-${info.project.name}.png`,
    fullPage: true,
  });
  await page.goto(`/events/${id[1]}/checkout`);
  await page
    .getByRole("group", { name: "General quantity", exact: true })
    .getByRole("button", { name: "Increase quantity" })
    .click();
  await page.getByLabel("Any coupon code? (optional)").fill("tickete10");
  await page.getByRole("button", { name: "Apply coupon", exact: true }).click();
  await expect(page.locator(".checkout-total")).toHaveText("BDT 450.00");
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({
    path: `../docs/screenshots/coupons-checkout-${info.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole("button", { name: "Continue to details" }).click();
  await page
    .getByRole("button", { name: "Reserve tickets", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Complete your test payment" }),
  ).toBeVisible();
  await page.getByLabel("Test phone number").fill("01700000000");
  await page.getByRole("button", { name: "Continue to test OTP" }).click();
  await page.getByLabel("Test OTP", { exact: true }).fill("123456");
  await page.getByRole("button", { name: "Confirm test payment" }).click();
  await expect(
    page.getByRole("heading", { name: "You’re on the list." }),
  ).toBeVisible();
  await page.reload();
  await expect(page.locator(".checkout-total")).toHaveText("BDT 450.00");
  await expect(page.getByLabel("Price breakdown")).toContainText("50.00");
  await page.goto(`/organizer/events/${id[0]}`);
  page.once("dialog", (d) => d.accept());
  await page.getByRole("button", { name: "Pause TICKETE10" }).click();
  await expect(
    page.getByRole("button", { name: "Resume TICKETE10" }),
  ).toBeVisible();
  const guest = await browser.newContext({ baseURL: "http://127.0.0.1:3000" });
  const buyer = await guest.newPage();
  await buyer.goto(`/events/${id[1]}/checkout`);
  await buyer
    .getByRole("group", { name: "General quantity", exact: true })
    .getByRole("button", { name: "Increase quantity" })
    .click();
  await buyer.getByLabel("Any coupon code? (optional)").fill("TICKETE10");
  await buyer
    .getByRole("button", { name: "Apply coupon", exact: true })
    .click();
  await expect(buyer.getByRole("alert")).toContainText("invalid or paused");
  await guest.close();
});
