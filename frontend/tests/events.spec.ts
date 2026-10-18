import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("organizer draft editor works on desktop and mobile", async ({
  page,
}, testInfo) => {
  await page.route("**/api/v1/auth/me/", (route) =>
    route.fulfill({
      json: {
        id: "demo",
        email: "demo@example.com",
        full_name: "Demo",
        role: "organizer",
        email_verified: false,
        phone: "",
      },
    }),
  );
  await page.goto("/organizer/events/new");
  await page
    .getByLabel("Event title", { exact: true })
    .fill("A night to remember");
  await page.getByRole("button", { name: "Next step", exact: true }).click();
  await page.getByRole("button", { name: "Add ticket category" }).click();
  await page.getByLabel("Category name").fill("General admission");
  await page.getByLabel("Price (BDT)").fill("500");
  await page.getByRole("button", { name: "Next step", exact: true }).click();
  await page.getByRole("button", { name: "Add question", exact: true }).click();
  await page.getByLabel("Question label").fill("Meal preference");
  await page.getByLabel("Question type").selectOption("dropdown");
  await page
    .getByLabel("Options (comma separated)")
    .fill("Standard, Vegetarian");
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
    path: `../docs/screenshots/event-editor-${testInfo.project.name}.png`,
    fullPage: true,
  });
});

test("real organizer submission becomes a public server-rendered event after admin approval", async ({
  page,
  browser,
  request,
}, testInfo) => {
  test.skip(
    process.env.AUTH_E2E_LIVE !== "1" || testInfo.project.name !== "desktop",
    "Uses isolated CI services and seeded review accounts.",
  );
  const password = process.env.DEMO_ACCOUNT_PASSWORD!;
  const title = `Browser festival ${Date.now()}`;
  await page.goto("/login");
  await page.getByLabel("Email address").fill("demo-organizer@example.com");
  await page.getByLabel("Password", { exact: true }).fill(password);
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toContainText("Hello,");
  await page.goto("/organizer/events/new");
  await page.getByLabel("Event title", { exact: true }).fill(title);
  await page
    .getByLabel("Description", { exact: true })
    .fill("A fictional event for browser integration testing.");
  await page.getByLabel("Venue", { exact: true }).fill("Demo Hall, Dhaka");
  const date = (days: number) =>
    new Date(Date.now() + days * 86400000).toISOString().slice(0, 16);
  await page.getByLabel("Event starts", { exact: true }).fill(date(3));
  await page.getByLabel("Event ends", { exact: true }).fill(date(4));
  await page.getByLabel("Sales start", { exact: true }).fill(date(1));
  await page.getByLabel("Sales end", { exact: true }).fill(date(2));
  await page.getByRole("button", { name: "Next step", exact: true }).click();
  await page.getByRole("button", { name: "Add ticket category" }).click();
  await page.getByLabel("Category name").fill("General");
  await page.getByLabel("Price (BDT)").fill("500");
  await page.getByRole("button", { name: "Save draft", exact: true }).click();
  await expect(
    page.getByRole("button", { name: "Submit for approval" }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Submit for approval" }).click();
  await expect(page.getByText("pending", { exact: true })).toBeVisible();
  const context = await browser.newContext();
  const admin = await context.newPage();
  await admin.goto("http://127.0.0.1:3000/login");
  await admin.getByLabel("Email address").fill("demo-admin@example.com");
  await admin.getByLabel("Password", { exact: true }).fill(password);
  await admin.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(admin.getByRole("heading", { level: 1 })).toContainText(
    "Hello,",
  );
  await admin.goto("http://127.0.0.1:3000/admin/events");
  await admin
    .getByRole("button", { name: `Review ${title}`, exact: true })
    .click();
  await expect(admin.getByRole("dialog")).toBeVisible();
  expect(
    (
      await new AxeBuilder({ page: admin })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await admin
    .getByRole("button", { name: "Approve event", exact: true })
    .click();
  await expect(admin.getByRole("dialog")).toHaveCount(0);
  await page.reload();
  await page
    .getByRole("link", { name: "View public event", exact: true })
    .click();
  await expect(page).toHaveURL(/^http:\/\/127\.0\.0\.1:3000\/events\/[^/]+$/);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(title);
  const response = await request.get(page.url());
  expect(response.ok()).toBe(true);
  const html = await response.text();
  expect(html).toContain(title);
  expect(html).toContain('property="og:title"');
  await page.screenshot({
    path: "../docs/screenshots/public-event-desktop.png",
    fullPage: true,
  });
  await context.close();
});
