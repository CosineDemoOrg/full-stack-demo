import {
  Container,
  Heading,
  Table,
  Button,
  Flex,
  Input,
  Select,
  VStack,
} from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { OpenAPI } from "@/client"

type Member = { id: string; user_id: string; org_id: string; role: string }
type Org = { id: string; name: string }

export const Route = createFileRoute("/_layout/org-members")({
  component: OrgMembers,
})

function OrgMembers() {
  const [members, setMembers] = useState<Member[]>([])
  const [orgs, setOrgs] = useState<Org[]>([])
  const [orgId, setOrgId] = useState<string>("")
  const [inviteEmail, setInviteEmail] = useState<string>("")
  const [role, setRole] = useState<string>("member")

  useEffect(() => {
    const load = async () => {
      const token = localStorage.getItem("access_token")
      if (token) {
        const payload = JSON.parse(atob(token.split(".")[1]))
        setOrgId(payload.active_org_id ?? "")
      }
      const orgsResp = await fetch(`${OpenAPI.BASE}/api/v1/orgs/`, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      })
      const orgsData = await orgsResp.json()
      setOrgs(orgsData.data ?? [])
    }
    load()
  }, [])

  useEffect(() => {
    const loadMembers = async () => {
      if (!orgId) return
      const resp = await fetch(`${OpenAPI.BASE}/api/v1/orgs/${orgId}/members`, {
        headers: {
          Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        },
      })
      const data = await resp.json()
      setMembers(data ?? [])
    }
    loadMembers()
  }, [orgId])

  const invite = async () => {
    if (!inviteEmail || !orgId) return
    // find user by email first via users list (admin can list all users)
    const usersResp = await fetch(`${OpenAPI.BASE}/api/v1/users/?limit=1000`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
    })
    const usersData = await usersResp.json()
    const user = (usersData.data ?? []).find((u: any) => u.email === inviteEmail)
    if (!user) return
    await fetch(`${OpenAPI.BASE}/api/v1/memberships/${orgId}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ user_id: user.id, role }),
    })
    setInviteEmail("")
    setRole("member")
    // reload members
    const resp = await fetch(`${OpenAPI.BASE}/api/v1/orgs/${orgId}/members`, {
      headers: {
        Authorization: `Bearer ${localStorage.getItem("access_token")}`,
      },
    })
    const data = await resp.json()
    setMembers(data ?? [])
  }

  return (
    <Container maxW="full">
      <Heading size="lg" pt={12}>
        Organization Members
      </Heading>

      <Flex my={4} gap={2}>
        <Select
          placeholder="Select org"
          value={orgId}
          onChange={(e) => setOrgId(e.target.value)}
          maxW="xs"
        >
          {orgs.map((o) => (
            <option key={o.id} value={o.id}>
              {o.name}
            </option>
          ))}
        </Select>
      </Flex>

      <VStack align="start" gap={2} my={4}>
        <Heading size="sm">Invite Member</Heading>
        <Flex gap={2}>
          <Input
            placeholder="User email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
          />
          <Select value={role} onChange={(e) => setRole(e.target.value)} maxW="xs">
            <option value="member">Member</option>
            <option value="viewer">Viewer</option>
            <option value="admin">Admin</option>
          </Select>
          <Button onClick={invite} colorScheme="blue">
            Invite
          </Button>
        </Flex>
      </VStack>

      <Table.Root size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader w="sm">Membership ID</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">User ID</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Role</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {members.map((m) => (
            <Table.Row key={m.id}>
              <Table.Cell truncate maxW="sm">{m.id}</Table.Cell>
              <Table.Cell truncate maxW="sm">{m.user_id}</Table.Cell>
              <Table.Cell truncate maxW="sm">{m.role}</Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
    </Container>
  )
}