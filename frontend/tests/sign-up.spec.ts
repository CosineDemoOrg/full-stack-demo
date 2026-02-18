import { expect, type Page, test } from "@playwright/test"

import { randomEmail, randomPassword } from "./utils/random"

test.use({ storageState: { cookies: [], origins: [] } })

type OptionsType = {
  exact?: boolean
}

const fillForm = async (
  page: Page,
  full_name: string,
  username: string,
  email: string,
  password: string,
  confirm_password: string,
) => {
  await page.getByPlaceholder("Full Name").fill(full_name)
  await page.getByPlaceholder("Username").fill(username)
  await page.getByPlaceholder("Email").fill(email)
  await page.getByPlaceholder("Password", { exact: true }).fill(password)
  await page.getByPlaceholder("Confirm Password").fill(confirm_password)
}

const verifyInput = async (
  page: Page,
  placeholder: string,
  options?: OptionsType,
) => {
  const input = page.getByPlaceholder(placeholder, options)
  await expect(input).toBeVisible()
  await expect(input).toHaveText("")
  await expect(input).toBeEditable()
}

test("Inputs are visible, empty and editable", async ({ page }) => {
  await page.goto("/signup")

  await verifyInput(page, "Full Name")
  await verifyInput(page, "Username")
  await verifyInput(page, "Email")
  await verifyInput(page, "Password", { exact: true })
  await verifyInput(page, "Confirm Password")
})

test("Sign Up button is visible", async ({ page }) => {
  await page.goto("/signup")

  await expect(page.getByRole("button", { name: "Sign Up" })).toBeVisible()
})

test("Log In link is visible", async ({ page }) => {
  await page.goto("/signup")

  await expect(page.getByRole("link", { name: "Log In" })).toBeVisible()
})

test("Sign up with valid name, username, email, and password", async ({ page }) => {
  const full_name = "Test User"
  const username = "testuser"
  const email = randomEmail()
  const password = randomPassword()

  await page.goto("/signup")
  await fillForm(page, full_name, username, email, password, password)
  await page.getByRole("button", { name: "Sign Up" }).click()
})

test("Sign up with invalid email", async ({ page }) => {
  await page.goto("/signup")

  await fillForm(
    page,
    "Playwright Test",
    "playwright",
    "invalid-email",
    "changethis",
    "changethis",
  )
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page.getByText("Invalid email address")).toBeVisible()
})

test("Sign up with existing email", async ({ page }) => {
  const fullName = "Test User"
  const username = `user_${Math.random().toString(36).substring(2)}`
  const email = randomEmail()
  const password = randomPassword()

  // Sign up with an email
  await page.goto("/signup")
  await fillForm(page, fullName, username, email, password, password)
  await page.getByRole("button", { name: "Sign Up" }).click()

  // Sign up again with the same email
  await page.goto("/signup")
  await fillForm(page, fullName, `${username}_2`, email, password, password)
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page.getByText("Email already exists")).toBeVisible()
})

test("Sign up with existing username", async ({ page }) => {
  const fullName = "Test User"
  const username = `user_${Math.random().toString(36).substring(2)}`
  const email = randomEmail()
  const password = randomPassword()

  await page.goto("/signup")
  await fillForm(page, fullName, username, email, password, password)
  await page.getByRole("button", { name: "Sign Up" }).click()

  await page.goto("/signup")
  await fillForm(page, fullName, username, randomEmail(), password, password)
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page.getByText("Username already exists")).toBeVisible()
})

test("Sign up with weak password", async ({ page }) => {
  const fullName = "Test User"
  const username = `user_${Math.random().toString(36).substring(2)}`
  const email = randomEmail()
  const password = "weak"

  await page.goto("/signup")

  await fillForm(page, fullName, username, email, password, password)
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(
    page.getByText("Password must be at least 8 characters"),
 </old_code><new_code>test("Sign up with mismatched passwords", async ({ page }) => {
  const fullName = "Test User"
  const username = `user_${Math.random().toString(36).substring(2)}`
  const email = randomEmail()
  const password = randomPassword()
  const password2 = randomPassword()

  await page.goto("/signup")

  await fillForm(page, fullName, username, email, password, password2)
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page.getByText("The passwords do not match")).toBeVisible()
})

test("Sign up with missing full name", async ({ page }) => {
  const fullName = ""
  const username = `user_${Math.random().toString(36).substring(2)}`
  const email = randomEmail()
  const password = randomPassword()

  await page.goto("/signup")

  await fillForm(page, fullName, username, email, password, password)
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page.getByText("Full Name is required")).toBeVisible()
})

test("Sign up with missing username", async ({ page }) => {
  const username = ""

  await page.goto("/signup")

  await fillForm(page, "Test User", username, randomEmail(), randomPassword(), randomPassword())
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page.getByText("Username is required")).toBeVisible()
})

test("Sign up with missing email", async ({ page }) => {
  const email = ""
  const password = randomPassword()

  await page.goto("/signup")

  await fillForm(page, "Test User", "playwright", email, password, password)
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page.getByText("Email is required")).toBeVisible()
})

test("Sign up with missing password", async ({ page }) => {
  const email = randomEmail()
  const password = ""

  await page.goto("/signup")

  await fillForm(page, "Test User", "playwright", email, password, password)
  await page.getByRole("button", { name: "Sign Up" }).click()

  await expect(page.getByText("Password is required")).toBeVisible()
})
