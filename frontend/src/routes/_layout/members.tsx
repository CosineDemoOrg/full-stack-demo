import {
  Box,
  Button,
  Container,
  Heading,
  Input,
  Select,
  Spinner,
  Table,
  Tbody,
  Td,
  Th,
  Thead,
  Tr,
} from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { useEffect, useState } from "react"
import { handleError } from "@/utils"

type Membership = {
  id: string
  user_id: string
  org_id: string
  role: "admin" | "member"
}

type User = { id: string; email: string; full_name?: string | null }

export const Route = createFileRoute("/_layout/members")({
  component: MembersPage,
})

async function fetchMembers(): Promise<Membership[]> {
  const token = localStorage.getItem("access_token")
  const res = await fetch("/api/v1/memberships/", {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error("Failed to load")
  const data = await res.json()
  return data.data
}

async function fetchUsers(): Promise<User[]> {
  const token = localStorage.getItem("access_token")
  const res = await fetch("/api/v1/users/", {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error("Failed to load")
  const data = await res.json()
  return data.data
}

async function invite(user_id: string, role: string) {
  const token = localStorage.getItem("access_token")
  const res = await fetch("/api/v1/memberships/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ user_id, role }),
  })
  if (!res.ok) {
    const body = await res.json()
    throw { body }
  }
}

async function removeMember(membership_id: string) {
  const token = localStorage.getItem("access_token")
  await fetch(`/api/v1/memberships/${membership_id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  })
}

function MembersPage() {
  const [members, setMembers] = useState<Membership[] | null>(null)
  const [users, setUsers] = useState<User[] | null>(null)
  const [selectedUser, setSelectedUser] = useState<string>("")
  const [role, setRole] = useState<string>("member")
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [m, u] = await Promise.all([fetchMembers(), fetchUsers()])
      setMembers(m)
      setUsers(u)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const onInvite = async () => {
    try {
      await invite(selectedUser, role)
      await load()
      setSelectedUser("")
      setRole("member")
    } catch (e: any) {
      handleError(e)
    }
  }

  const onRemove = async (id: string) => {
    await removeMember(id)
    await load()
  }

  return (
    <Container maxW="container.lg">
      <Box pt={12} m={4}>
        <Heading size="md" mb={4}>
          Organization Members
        </Heading>
        {loading || !members ? (
          <Spinner />
        ) : (
          <>
            <Table variant="simple" size="sm">
              <Thead>
                <Tr>
                  <Th>User</Th>
                  <Th>Role</Th>
                  <Th></Th>
                </Tr>
              </Thead>
              <Tbody>
                {members.map((m) => (
                  <Tr key={m.id}>
                    <Td>{m.user_id}</Td>
                    <Td>{m.role}</Td>
                    <Td>
                      <Button size="xs" onClick={() => onRemove(m.id)}>
                        Remove
                      </Button>
                    </Td>
                  </Tr>
                ))}
              </Tbody>
            </Table>

            <Box mt={6} display="flex" gap={2}>
              <Select
                value={selectedUser}
                onChange={(e) => setSelectedUser(e.target.value)}
                placeholder="Select user to invite"
              >
                {(users ?? []).map((u) => (
                  <option key={u.id} value={u.id}>
                    {u.full_name || u.email}
                  </option>
                ))}
              </Select>
              <Select value={role} onChange={(e) => setRole(e.target.value)}>
                <option value="member">Member</option>
                <option value="admin">Admin</option>
              </Select>
              <Button onClick={onInvite} isDisabled={!selectedUser}>
                Invite
              </Button>
            </Box>
          </>
        )}
      </Box>
    </Container>
  )
}