import { Container, Heading, Table } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute } from "@tanstack/react-router"
import { OpenAPI } from "@/client"

type Member = { id: string; user_id: string; org_id: string; role: string }

async function fetchMembers(): Promise<Member[]> {
  // we need active org id, which backend reads from token
  const res = await fetch(`${OpenAPI.BASE}/api/v1/orgs/my`, {
    headers: { Authorization: `Bearer ${localStorage.getItem("access_token") || ""}` },
  })
  const data = await res.json()
  const orgs: { id: string }[] = data.data || []
  const activeMembersRes = await fetch(`${OpenAPI.BASE}/api/v1/memberships/org/${orgs[0]?.id}`, {
    headers: { Authorization: `Bearer ${localStorage.getItem("access_token") || ""}` },
  })
  const membersData = await activeMembersRes.json()
  return membersData.data as Member[]
}

export const Route = createFileRoute("/_layout/org-members")({
  component: OrgMembers,
})

function OrgMembers() {
  const { data: members = [] } = useQuery({ queryKey: ["org-members"], queryFn: fetchMembers })

  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Organization Members
      </Heading>
      <Table.Root mt={4}>
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