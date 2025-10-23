import { Button, Container, Flex, Heading, Input, Table } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { useState } from "react"

import { OpenAPI } from "@/client"

type Member = { id: string; user_id: string; org_id: string; role: string; accepted: boolean }

export const Route = createFileRoute("/_layout/members")({
  component: MembersPage,
})

async function fetchMembers(): Promise<Member[]> {
  const token = await OpenAPI.TOKEN?.({} as any)
  const orgsRes = await fetch(`${OpenAPI.BASE}/api/v1/orgs/`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  const orgsData = await orgsRes.json()
  const activeOrgId = orgsData?.data?.[0]?.id
  if (!activeOrgId) return []
  const res = await fetch(`${OpenAPI.BASE}/api/v1/orgs/${activeOrgId}/members`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  const data = await res.json()
  return data.data ?? []
}

function MembersTable() {
  const { data } = useQuery({ queryKey: ["members"], queryFn: fetchMembers })
  const members = data ?? []

  return (
    <Table.Root size={{ base: "sm", md: "md" }}>
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeader w="sm">User ID</Table.ColumnHeader>
          <Table.ColumnHeader w="sm">Role</Table.ColumnHeader>
          <Table.ColumnHeader w="sm">Accepted</Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {members.map((m) => (
          <Table.Row key={m.id}>
            <Table.Cell>{m.user_id}</Table.Cell>
            <Table.Cell>{m.role}</Table.Cell>
            <Table.Cell>{m.accepted ? "Yes" : "No"}</Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table.Root>
  )
}

function InviteForm() {
  const [userId, setUserId] = useState("")
  const [role, setRole] = useState("member")

  const invite = async () => {
    const token = await OpenAPI.TOKEN?.({} as any)
    const orgsRes = await fetch(`${OpenAPI.BASE}/api/v1/orgs/`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const orgsData = await orgsRes.json()
    const activeOrgId = orgsData?.data?.[0]?.id
    if (!activeOrgId) return
    await fetch(`${OpenAPI.BASE}/api/v1/orgs/${activeOrgId}/invite`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ user_id: userId, role }),
    })
    window.location.reload()
  }

  return (
    <Flex gap={2} my={4}>
      <Input placeholder="User ID" value={userId} onChange={(e) => setUserId(e.target.value)} bg="white" color="black" />
      <Input placeholder="Role (admin/member)" value={role} onChange={(e) => setRole(e.target.value)} bg="white" color="black" />
      <Button onClick={invite}>Invite</Button>
    </Flex>
  )
}

function MembersPage() {
  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Organization Members
      </Heading>
      <InviteForm />
      <MembersTable />
    </Container>
  )
}