import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("landing is usable, accessible and honest about availability", async ({
  page,
}, testInfo) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText(
    "Your next moment.",
  );
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
  await expect(
    page.getByRole("link", { name: "Find your next event" }),
  ).toBeVisible();
  await page.getByText("Can I buy tickets right now?", { exact: true }).click();
  await expect(
    page.getByText(/You’re exploring our first design preview/),
  ).toBeVisible();
  const accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await page.getByRole("heading", { level: 1 }).click();
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await page.screenshot({
    path: `../docs/screenshots/landing-${testInfo.project.name}.png`,
    fullPage: true,
  });
  await page.getByRole("link", { name: "Find your next event" }).click();
  await expect(
    page.getByRole("heading", { level: 1, name: /Your next/ }),
  ).toBeVisible();
});

test("design controls, focus restoration and empty states", async ({
  page,
}, testInfo) => {
  await page.goto("/design");
  await page.getByRole("button", { name: "Increase quantity" }).click();
  await expect(
    page.getByText("Preview total: BDT 2,400", { exact: false }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Decrease quantity" }).click();
  const trigger = page.getByRole("button", { name: "Open preview dialog" });
  await trigger.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
  await page.getByRole("combobox", { name: "Event category" }).click();
  await page.getByRole("option", { name: "Workshop" }).click();
  await expect(page.getByRole("combobox")).toHaveText("Workshop");
  await page.getByRole("checkbox", { name: "This ticket is a gift" }).click();
  await expect(page.getByRole("checkbox")).toBeChecked();
  await page
    .getByRole("button", { name: "Primary action", exact: true })
    .click();
  await expect(
    page.getByText("That’s the TICKETÉ touch.", { exact: true }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Dismiss", exact: true }).click();
  expect(
    await page.evaluate(
      () =>
        document.documentElement.scrollWidth <=
        document.documentElement.clientWidth,
    ),
  ).toBe(true);
  const accessibility = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(accessibility.violations).toEqual([]);
  await page.getByRole("heading", { level: 1 }).click();
  await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
  await page.screenshot({
    path: `../docs/screenshots/design-${testInfo.project.name}.png`,
    fullPage: true,
  });
});

test("mobile menu has keyboard dismissal", async ({ page, isMobile }) => {
  test.skip(!isMobile, "Menu is mobile-only.");
  await page.goto("/");
  const trigger = page.getByRole("button", { name: "Open navigation" });
  await trigger.click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await expect(trigger).toBeFocused();
});
