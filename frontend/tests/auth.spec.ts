import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

test("signup validates input and is accessible on both layouts", async ({
  page,
}, testInfo) => {
  await page.goto("/signup");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(page.getByText("Enter a valid email address.")).toBeVisible();
  await expect(page.getByText("Enter your full name.")).toBeVisible();
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
    path: `../docs/screenshots/signup-${testInfo.project.name}.png`,
    fullPage: true,
  });
});

test("login explains service errors without pretending to sign in", async ({
  page,
}) => {
  await page.route("**/api/v1/auth/**", async (route) => {
    await route.fulfill({
      status: route.request().url().includes("/csrf/") ? 200 : 503,
      contentType: "application/json",
      body: JSON.stringify({
        csrf_token: "test-csrf",
        error: { message: "Unavailable" },
      }),
    });
  });
  await page.goto("/login");
  await page.getByLabel("Email address").fill("test@example.com");
  await page.getByLabel("Password", { exact: true }).fill("Test-password-54!");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.getByRole("main").getByRole("alert")).toContainText(
    "temporarily unavailable",
  );
  await expect(page).toHaveURL(/\/login$/);
});

test("incomplete email links cannot submit a confirmation", async ({
  page,
}) => {
  for (const path of ["reset-password", "verify-email"]) {
    await page.goto(`/${path}`);
    await expect(page.getByRole("main").getByRole("alert")).toContainText(
      "missing its verification details",
    );
    await expect(
      page.getByRole("button", {
        name: path === "reset-password" ? "Reset password" : "Verify email",
        exact: true,
      }),
    ).toHaveCount(0);
  }
});

test("real API signup, login, session refresh, profile and logout", async ({
  page,
  context,
}, testInfo) => {
  test.skip(
    process.env.AUTH_E2E_LIVE !== "1",
    "Requires the isolated CI PostgreSQL/Redis API; never use the shared development database.",
  );
  const email = `browser-${testInfo.project.name}-${Date.now()}@example.com`;
  await page.goto("/signup");
  await page.getByLabel("Full name", { exact: true }).fill("Browser Tester");
  await page.getByLabel("Email address").fill(email);
  await page
    .getByLabel("Password", { exact: true })
    .fill("Browser-Str0ng-Pass!58");
  await page
    .getByLabel("Confirm password", { exact: true })
    .fill("Browser-Str0ng-Pass!58");
  await page
    .getByRole("button", { name: "Create account", exact: true })
    .click();
  await expect(page.getByRole("status")).toContainText(
    "Your account is created",
  );
  await page.getByRole("link", { name: "Go to log in" }).click();
  await page.getByLabel("Email address").fill(email);
  await page
    .getByLabel("Password", { exact: true })
    .fill("Browser-Str0ng-Pass!58");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Hello, Browser Tester.",
  );
  const cookies = await context.cookies();
  for (const name of ["tickete_access", "tickete_refresh"])
    expect(cookies.find((cookie) => cookie.name === name)?.httpOnly).toBe(true);
  // Simulate expiry of the short-lived access cookie, retaining the refresh cookie.
  await context.clearCookies({ name: "tickete_access" });
  await page.reload();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Hello, Browser Tester.",
  );
  await page.getByLabel("Full name", { exact: true }).fill("Updated Tester");
  await page.getByRole("button", { name: "Save details" }).click();
  await expect(page.getByText("Profile saved.")).toBeVisible();
  await page.reload();
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(
    "Hello, Updated Tester.",
  );
  expect(await page.evaluate(() => Object.keys(localStorage))).toEqual([]);
  expect(
    (
      await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await expect(page).toHaveURL(/\/login$/);
  await page.goto("/account");
  await expect(
    page.getByRole("heading", { name: "Log in to your account" }),
  ).toBeVisible();
});
