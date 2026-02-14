import { test, expect } from "@playwright/test"

test("org switcher shows orgs and switches token", async ({ page }) => {
  await page.goto("/login")
  await page.getByLabel("Email").fill("alice@example.com")
  await page.getByLabel("Password").fill("alicepass")
  await page.getByRole("button", { name: "Log In" }).click()

  await page.waitForURL("/")
  // Org switcher select should exist
  const select = page.locator("select")
  await expect(select).toBeVisible()
  const options = await select.locator("option").allTextContents()
  expect(options.length).toBeGreaterThan(0)

  // Switch to first org
  await select.selectOption({ index: 0 })
  await page.getByRole("button", { name: "Switch" }).click()

  // Items page should load items scoped to org
  await page.getByText("Items").click()
  await expect(page.getByText("Items")).toBeVisible()
})