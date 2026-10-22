import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { execFileSync } from "node:child_process";

test("decorative motion can pause and respects reduced motion", async ({
  page,
}, info) => {
  await page.goto("/");
  await expect(page.locator(".hero-ticket")).toHaveCSS(
    "animation-name",
    "ticket-float",
  );
  await expect(page.locator(".marquee-track")).toHaveCSS(
    "animation-name",
    "marquee-crawl",
  );
  await expect(page.locator(".ambient-particles")).toHaveAttribute(
    "aria-hidden",
    "true",
  );
  await page.getByRole("button", { name: "Pause motion", exact: true }).click();
  await expect(page.locator(".hero-ticket")).toHaveCSS(
    "animation-play-state",
    "paused",
  );
  await expect(page.locator(".marquee-track")).toHaveCSS(
    "animation-play-state",
    "paused",
  );
  await page.screenshot({
    path: `../docs/screenshots/motion-${info.project.name}.png`,
    fullPage: true,
  });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await expect(page.locator(".hero-ticket")).toHaveCSS(
    "animation-name",
    "none",
  );
  await expect(page.locator(".marquee-track")).toHaveCSS(
    "animation-name",
    "none",
  );
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
  await page.goto("/login");
  await expect(page.locator(".ambient-particles")).toBeVisible();
  await expect(page.locator(".ambient-particles i").first()).toHaveCSS(
    "animation-name",
    "none",
  );
  await page.getByLabel("Email address").fill("motion-check@example.com");
  await expect(page.getByLabel("Email address")).toHaveValue(
    "motion-check@example.com",
  );
  await page.screenshot({
    path: `../docs/screenshots/motion-login-${info.project.name}.png`,
    fullPage: true,
  });
});

test("owner views charts and closes a dedicated event with a fixed report", async ({
  page,
}, info) => {
  test.skip(process.env.AUTH_E2E_LIVE !== "1", "Disposable CI services only.");
  const id = execFileSync(
    "python",
    [
      "-c",
      `
import os
assert os.environ.get('DJANGO_SETTINGS_MODULE')=='config.settings.browser_tests'
assert os.environ.get('AUTH_E2E_LIVE')=='1'
import django
django.setup()
from datetime import timedelta
from django.utils import timezone
from apps.accounts.models import User
from apps.events.models import Event, TicketCategory
from apps.orders.services import create_order
from apps.checkin.services import scan
from tests.test_orders import data, pay
now=timezone.now()
owner=User.objects.get(email='demo-organizer@example.com')
event=Event.objects.create(owner=owner,title='Fictional report showcase',status='approved',starts_at=now+timedelta(days=1),ends_at=now+timedelta(days=2),sales_start=now-timedelta(days=1),sales_end=now+timedelta(hours=2))
category=TicketCategory.objects.create(event=event,name='General',price=500,seat_limit=100)
payload=data(event,category,quantity=2)
order=pay(create_order(payload),payload['access_token'])
scan(owner,event.pk,order.tickets.first().code,'manual')
print(event.pk)
`,
    ],
    { cwd: "../backend", encoding: "utf8" },
  ).trim();
  await page.goto("/login");
  await page.getByLabel("Email address").fill("demo-organizer@example.com");
  await page
    .getByLabel("Password", { exact: true })
    .fill(process.env.DEMO_ACCOUNT_PASSWORD!);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page).toHaveURL(/\/account$/);
  await page.goto(`/organizer/events/${id}/report`);
  await expect(
    page.getByRole("heading", { name: "Tickets sold over time", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Daily simulated revenue", exact: true }),
  ).toBeVisible();
  page.once("dialog", (d) => d.accept());
  await page
    .getByRole("button", { name: "Close event and save final report" })
    .click();
  await expect(
    page.getByText("Final report · event closed", { exact: false }),
  ).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Close event and save final report" }),
  ).toHaveCount(0);
  await expect(
    page.getByText("No-show (excluding cancelled)", { exact: true }),
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
  await page.getByRole("heading", { level: 1 }).click();
  await page.screenshot({
    path: `../docs/screenshots/report-${info.project.name}.png`,
    fullPage: true,
  });
  await page.reload();
  await expect(
    page.getByText("Final report · event closed", { exact: false }),
  ).toBeVisible();
});
