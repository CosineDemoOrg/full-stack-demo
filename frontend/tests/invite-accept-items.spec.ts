import { expect, test } from "@playwright/test"
import { BASE_URL } from "./config"

test("invite -> accept -> list items", async ({ page }) => {
  // Login as superuser
  await page.goto(`${BASE_URL}/login`)
  await page.getByLabel("Email").fill(process.env.FIRST_SUPERUSER || "admin@example.com")
  await page.getByLabel("Password").fill(process.env.FIRST_SUPERUSER_PASSWORD || "changethis")
  await page.getByRole("button", { name: "Login" }).click()

  // Switch to an org (first in list)
  await page.waitForURL("**/")
  // Open members page
  await page.goto(`${BASE_URL}/members`)

  // Invite bob (assumes seeded)
  await page.getByPlaceholder("User ID").fill(process.env.BOB_USER_ID || "")
  await page.getByPlaceholder("Role (admin/member)").fill("member")
  await page.getByRole("button", { name: "Invite" }).click()

  // Log out
  await page.getByTestId("user-menu").click()
  await page.getByRole("menuitem", { name: "Log Out" }).click()

  // Login as Bob and accept
  await page.goto(`${BASE_URL}/login`)
  await page.getByLabel("Email").fill("bob@example.com")
  await page.getByLabel("Password").fill("bobpassword")
  await page.getByRole("button", { name: "Login" }).click()
  await page.waitForURL("**/")

  // Go to Items, should be empty, then add one
  await page.goto(`${BASE_URL}/items`)
  await expect(page.getByText("You don't have any items yet")).toBeVisible()
})