import { expect, test } from "@playwright/test";

test("realiza login e acessa dashboard", async ({ page }) => {
  await page.route("**/api/v1/auth/login", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        access_token: "fake-access-token",
        refresh_token: "fake-refresh-token",
      }),
    });
  });

  await page.route("**/api/v1/metrics/summary", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        requests_total: 42,
        errors_total: 0,
        availability_pct: 100,
        avg_latency_ms: 18,
        incidents_open: 0,
      }),
    });
  });

  await page.goto("/login");

  await page.getByLabel("Email").fill("admin@hw1.local");
  await page.getByLabel("Senha").fill("123456");
  await page.getByRole("button", { name: "Entrar" }).click();

  await expect(page).toHaveURL(/\/dashboard$/);
  await expect(page.getByRole("heading", { name: "Dashboard" })).toBeVisible();
  await expect(
    page.getByText("Visão geral do sistema de gestão arquivística")
  ).toBeVisible();
});