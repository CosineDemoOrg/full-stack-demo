import { Container, Heading, Table } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useState } from "react"

type Member = {
  id: string
  user_id: string
  org_id: string
  role: "admin" | "member"
  is_active: boolean
}

const API_BASE = import.meta.env.VITE_API_URL || ""

export const Route = createFileRoute("/_layout/org-members")({
  component: OrgMembers,
})

function OrgMembers() {
  const [members, setMembers] = useState<Member[]>([])

  useEffect(() => {
    // We don't know active org id on client; list my orgs and pick first
    async function load() {
      const orgsResp = await fetch(`${API_BASE}/api/v1/orgs/`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
      })
      const orgs = await orgsResp.json()
      const org = orgs?.data?.[0]
      if (!org) return
      const resp = await fetch(`${API_BASE}/api/v1/orgs/${org.id}/members`, {
        headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
      })
      const data = await resp.json()
      setMembers(data?.data || [])
    }
    load()
  }, [])

  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Organization Members
      </Heading>
      <Table.Root>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>User ID</Table.ColumnHeader>
            <Table.ColumnHeader>Role</Table.ColumnHeader>
            <Table.ColumnHeader>Status</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {members.map((m) => (
            <Table.Row key={m.id}>
              <Table.Cell>{m.user_id}</Table.Cell>
              <Table.Cell>{m.role}</Table.Cell>
              <Table.Cell>{m.is_active ? "Active" : "Pending"}</Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Container>
  )
}