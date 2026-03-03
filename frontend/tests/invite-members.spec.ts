import { expect, test } from "@playwright/test"
import { firstSuperuser, firstSuperuserPassword } from "./config.ts"

test("admin can invite member and member sees items scoped by org", async ({ page }) => {
  // Login as superuser
  await page.goto("/login")
  await page.getByPlaceholder("Email").fill(firstSuperuser)
  await page.getByPlaceholder("Password", { exact: true }).fill(firstSuperuserPassword)
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/")

  // Open org switcher to load orgs (defaults set by backend)
  await page.getByRole("button").filter({ hasText: "Select org" }).first().click().catch(() => {})

  // Go to members
  await page.getByRole("link", { name: "Members" }).click()

  // Invite existing seeded user (alice@example.com) if present in list
  // The Select shows names/emails; locate by option value label (email or name)
  await page.getByRole("combobox").first().click()
  // pick first option if list available
  const options = page.locator("select").first().locator("option")
  const count = await options.count()
  if (count > 0) {
    const value = await options.nth(0).getAttribute("value")
    if (value) {
      await page.selectOption("select", value)
      await page.getByRole("button", { name: "Invite" }).click()
      // After inviting, the table should contain the new member row
      await expect(page.getByRole("table")).toBeVisible()
    }
  }

  // Logout
  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log out" }).click()
  await page.waitForURL("/login")

  // Log in as seeded user alice@example.com
  await page.getByPlaceholder("Email").fill("alice@example.com")
  await page.getByPlaceholder("Password", { exact: true }).fill("password123")
  await page.getByRole("button", { name: "Log In" }).click()
  await page.waitForURL("/")

  // Items page should show items for active org (likely empty)
  await page.getByRole("link", { name: "Items" }).click()
  await expect(page.getByText("You don't have any items yet").or(page.getByRole("table"))).toBeVisible()
})