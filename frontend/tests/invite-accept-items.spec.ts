import { test, expect } from "@playwright/test"

test("admin invites user, user accepts and lists items", async ({ page, request }) => {
  // Login as superuser
  const loginResp = await request.post("/api/v1/login/access-token", {
    form: {
      username: process.env.FIRST_SUPERUSER as string,
      password: process.env.FIRST_SUPERUSER_PASSWORD as string,
    },
  })
  const loginData = await loginResp.json()
  const superToken = loginData.access_token

  // Create org and switch
  const orgResp = await request.post("/api/v1/orgs/", {
    headers: { Authorization: `Bearer ${superToken}` },
    data: { name: "Playwright Org" },
  })
  const org = await orgResp.json()
  const switchResp = await request.post(`/api/v1/orgs/switch/${org.id}`, {
    headers: { Authorization: `Bearer ${superToken}` },
  })
  const switched = await switchResp.json()
  const adminToken = switched.access_token

  // Create a user
  const email = `play-${Date.now()}@example.com`
  const password = "playpassword"
  await request.post("/api/v1/users/open", {
    data: { email, password },
  })
  const userLoginResp = await request.post("/api/v1/login/access-token", {
    form: { username: email, password },
  })
  const userLoginData = await userLoginResp.json()
  const userToken = userLoginData.access_token

  // Admin invites user to org
  const meResp = await request.get("/api/v1/users/me", {
    headers: { Authorization: `Bearer ${userToken}` },
  })
  const me = await meResp.json()
  const inviteResp = await request.post(`/api/v1/orgs/${org.id}/members/invite`, {
    headers: { Authorization: `Bearer ${adminToken}` },
    params: { org_id: org.id, user_id: me.id },
  })
  expect(inviteResp.ok()).toBeTruthy()

  // User switches to org
  const userSwitchResp = await request.post(`/api/v1/orgs/switch/${org.id}`, {
    headers: { Authorization: `Bearer ${userToken}` },
  })
  const userSwitchData = await userSwitchResp.json()
  const userOrgToken = userSwitchData.access_token

  // User creates an item
  const createItemResp = await request.post("/api/v1/items/", {
    headers: { Authorization: `Bearer ${userOrgToken}` },
    data: { title: "Play Item", description: "Desc" },
  })
  expect(createItemResp.ok()).toBeTruthy()

  // Go to items page and see the item
  await page.goto("/")
  // store token
  await page.addInitScript((token) => localStorage.setItem("access_token", token), userOrgToken)
  await page.goto("/items")
  await expect(page.getByText("Play Item")).toBeVisible()
})