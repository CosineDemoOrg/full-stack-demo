import { Container, Heading, Table } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"

type Member = {
  id: string
  user_id: string
  org_id: string
  role: string
}

function getActiveOrgId(): string | null {
  const token = localStorage.getItem("access_token")
  if (!token) return null
  const parts = token.split(".")
  if (parts.length !== 3) return null
  try {
    const payload = JSON.parse(atob(parts[1]))
    return payload.active_org_id ?? null
  } catch {
    return null
  }
}

async function fetchMembers(): Promise<Member[]> {
  const orgId = getActiveOrgId()
  if (!orgId) return []
  const res = await fetch(`/api/v1/orgs/${orgId}/members`)
  return await res.json()
}

export const Route = createFileRoute("/_layout/members")({
  component: Members,
})

function MembersTable() {
  const { data: members } = useQuery({ queryKey: ["members"], queryFn: fetchMembers })

  return (
    <Table.Root>
      <Table.Header>
        <Table.Row>
          <Table.ColumnHeader>User ID</Table.ColumnHeader>
          <Table.ColumnHeader>Role</Table.ColumnHeader>
        </Table.Row>
      </Table.Header>
      <Table.Body>
        {members?.map((m) => (
          <Table.Row key={m.id}>
            <Table.Cell>{m.user_id}</Table.Cell>
            <Table.Cell>{m.role}</Table.Cell>
          </Table.Row>
        ))}
      </Table.Body>
    </Table.Root>
  )
}

function Members() {
  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Organization Members
      </Heading>
      <MembersTable />
    </Container>
  )
}