import { Container, Heading, Table } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"

type Member = { id: string; user_id: string; org_id: string; role: string }
type MembersResponse = { data: Member[]; count: number }

const API_BASE = import.meta.env.VITE_API_URL

async function fetchMembers(): Promise<MembersResponse> {
  // We need the active org id but backend scopes by token; provide a generic org members list is not discoverable.
  // For demo, we'll fetch current user's orgs and take the first.
  const orgsRes = await fetch(`${API_BASE}/orgs/`, {
    headers: { Authorization: `Bearer ${localStorage.getItem("access_token") || ""}` },
  })
  const orgs = await orgsRes.json()
  const orgId = orgs.data?.[0]?.id
  const res = await fetch(`${API_BASE}/orgs/${orgId}/members`, {
    headers: { Authorization: `Bearer ${localStorage.getItem("access_token") || ""}` },
  })
  if (!res.ok) throw new Error("Failed to load members")
  return res.json()
}

export const Route = createFileRoute("/_layout/members")({
  component: Members,
})

function Members() {
  const { data } = useQuery({ queryKey: ["members"], queryFn: fetchMembers })
  const members = data?.data ?? []
  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Organization Members
      </Heading>
      <Table.Root size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader>User ID</Table.ColumnHeader>
            <Table.ColumnHeader>Role</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {members.map((m) => (
            <Table.Row key={m.id}>
              <Table.Cell>{m.user_id}</Table.Cell>
              <Table.Cell>{m.role}</Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Container>
  )
}