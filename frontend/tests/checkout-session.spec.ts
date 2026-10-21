import { test, expect } from "@playwright/test";

test("checkout isolates accounts, logout, legacy storage and other tabs", async ({
  page,
  context,
}) => {
  test.skip(
    process.env.AUTH_E2E_LIVE !== "1",
    "Requires the disposable seeded event.",
  );
  const event = await (
    await page.request.get(
      "http://127.0.0.1:8000/api/v1/public/events/fictional-checkout-demo/",
    )
  ).json();
  const key = `tickete-checkout-${event.id}`;
  const checkout = "/events/fictional-checkout-demo/checkout";
  let identity: string | null = "account-a";
  let statusReads = 0;
  await context.route("**/api/v1/auth/me/", (route) =>
    route.fulfill({
      status: identity ? 200 : 401,
      contentType: "application/json",
      body: JSON.stringify(
        identity
          ? {
              id: identity,
              email: `${identity}@example.com`,
              full_name: "Session Tester",
              role: "buyer",
              email_verified: true,
              phone: "",
            }
          : { error: { message: "Not logged in" } },
      ),
    }),
  );
  await context.route("**/api/v1/orders/session-test/status/", (route) => {
    statusReads++;
    return route.fulfill({
      contentType: "application/json",
      body: JSON.stringify({
        id: "session-test",
        number: "TE-PRIVATE",
        status: "paid",
        total: "500.00",
        quantity: 1,
        expires_at: new Date().toISOString(),
        server_time: new Date().toISOString(),
        recipient_email: "private@example.com",
        is_gift: false,
        payment: null,
        tickets: [],
        delivery_status: "queued",
        pdf_ready: false,
      }),
    });
  });
  await page.goto(checkout);
  await expect(
    page.getByRole("heading", { name: "Choose your tickets" }),
  ).toBeVisible();
  const saved = {
    owner: "account-a",
    epoch: "initial",
    token: "x".repeat(43),
    key: "test",
    orderId: "session-test",
  };
  async function restore(value = saved) {
    await page.evaluate(
      ({ key, value }) => sessionStorage.setItem(key, JSON.stringify(value)),
      { key, value },
    );
    await page.goto(checkout);
  }
  await restore();
  await expect(
    page.getByRole("heading", { name: "You’re on the list." }),
  ).toBeVisible();
  expect(statusReads).toBe(1);
  for (const user of [null, "account-b"]) {
    identity = user;
    await restore();
    await expect(
      page.getByRole("heading", { name: "Choose your tickets" }),
    ).toBeVisible();
    expect(statusReads).toBe(1);
  }
  // Old releases stored capabilities with no owner: do not guess their ownership.
  identity = "account-a";
  await restore({ ...saved, owner: "", epoch: "" });
  await expect(
    page.getByRole("heading", { name: "Choose your tickets" }),
  ).toBeVisible();
  expect(statusReads).toBe(1);
  await restore();
  await expect(
    page.getByRole("heading", { name: "You’re on the list." }),
  ).toBeVisible();
  const other = await context.newPage();
  await other.goto("/account");
  await expect(
    other.getByRole("button", { name: "Log out", exact: true }),
  ).toBeVisible();
  await context.route("**/api/v1/auth/logout/", (route) => {
    identity = null;
    return route.fulfill({ status: 204 });
  });
  await other.getByRole("button", { name: "Log out", exact: true }).click();
  await expect(other).toHaveURL(/\/login$/);
  await expect(
    page.getByRole("heading", { name: "Choose your tickets" }),
  ).toBeVisible();
  expect(
    await page.evaluate((key) => sessionStorage.getItem(key), key),
  ).toBeNull();
  // Even if stale tab storage is restored, its pre-logout generation is invalid.
  identity = "account-a";
  await restore();
  await expect(
    page.getByRole("heading", { name: "Choose your tickets" }),
  ).toBeVisible();
  expect(statusReads).toBe(2);
  await context.route("**/api/v1/auth/me/", (route) =>
    route.fulfill({ status: 503, contentType: "application/json", body: "{}" }),
  );
  await page.reload();
  await expect(
    page.getByRole("button", { name: "Retry loading checkout" }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Choose your tickets" }),
  ).toHaveCount(0);
});
