import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("ticket design preview is accessible and fits the viewport", async ({
  page,
}, info) => {
  await page.goto("/ticket-preview");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "A little keepsake.",
  );
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.getByRole("heading", { level: 1 }).click();
  await page.screenshot({
    path: `../docs/screenshots/ticket-preview-${info.project.name}.png`,
    fullPage: true,
  });
});

test("guest reserves, pays and restores a simulated order", async ({
  page,
}, info) => {
  test.skip(
    process.env.AUTH_E2E_LIVE !== "1",
    "Requires disposable CI database and Redis.",
  );
  await page.goto("/events/fictional-checkout-demo/checkout");
  await expect(
    page.getByRole("heading", { name: "Choose your tickets" }),
  ).toBeVisible();
  await page
    .getByRole("group", { name: "General quantity", exact: true })
    .getByRole("button", { name: "Increase quantity" })
    .click();
  await page.getByRole("button", { name: "Continue to details" }).click();
  await page
    .getByLabel("Email address", { exact: true })
    .fill(`checkout-${info.project.name}-${Date.now()}@example.com`);
  await page.getByLabel("Gift these tickets").check();
  await page.getByLabel("Recipient email").fill("fictional-friend@example.com");
  // Attendee names intentionally left blank: the owner selected optional names.
  await page
    .getByRole("button", { name: "Reserve tickets", exact: true })
    .click();
  await expect(
    page.getByRole("heading", { name: "Complete your test payment" }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "Complete your test payment" }),
  ).toBeVisible();
  await page.getByLabel("Test phone number").fill("01700000000");
  await page.getByRole("button", { name: "Continue to test OTP" }).click();
  await page.getByLabel("Test OTP", { exact: true }).fill("000000");
  await page.getByRole("button", { name: "Confirm test payment" }).click();
  await expect(
    page.getByRole("alert").filter({ hasText: "Incorrect test code" }),
  ).toBeVisible();
  await page.getByLabel("Test OTP", { exact: true }).fill("123456");
  await page.getByRole("button", { name: "Confirm test payment" }).click();
  await expect(
    page.getByRole("heading", { name: "You’re on the list." }),
  ).toBeVisible();
  await expect(
    page.getByText("Your ticket PDF and email are queued.", { exact: false }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByRole("heading", { name: "You’re on the list." }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({
    path: `../docs/screenshots/checkout-confirmation-${info.project.name}.png`,
    fullPage: true,
  });
});
