import { Box, Button, Flex, Heading, Input, Select, Text } from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"
import { useMutation, useQuery } from "@tanstack/react-query"
import { useState } from "react"
import { OpenAPI } from "@/client"
import useOrgs from "@/hooks/useOrgs"

type Role = "admin" | "member"
type MembershipPublic = {
  id: string
  user_id: string
  org_id: string
  role: Role
}

export const Route = createFileRoute("/members")({
  component: MembersPage,
})

function MembersPage() {
  const { orgs } = useOrgs()
  const activeOrgId = orgs[0]?.id
  const { data, refetch } = useQuery<{ data: MembershipPublic[]; count: number }>({
    queryKey: ["members", activeOrgId],
    enabled: !!activeOrgId,
    queryFn: async () => {
      const res = await fetch(`${OpenAPI.BASE}/api/v1/memberships/org/${activeOrgId}`, {
        headers: {
          Authorization: `Bearer ${await Promise.resolve(OpenAPI.TOKEN?.({} as any) as any)}`,
        },
      })
      if (!res.ok) throw new Error("Failed to load members")
      return res.json()
    },
  })
  const [email, setEmail] = useState("")
  const [role, setRole] = useState<Role>("member")
  const inviteMutation = useMutation({
    mutationFn: async () => {
      // backend invite expects user_id + org_id; in real app we'd lookup by email.
      // For demo, we cannot lookup by email -> skip unless API supports it.
      // Example stub: no-op
      return Promise.resolve()
    },
    onSuccess: () => {
      setEmail("")
      refetch()
    },
  })

  return (
    <Flex direction="column" gap={4}>
      <Heading size="md">Organization Members</Heading>
      <Box>
        <Heading size="sm">Invite Member</Heading>
        <Flex gap={2} mt={2}>
          <Input placeholder="user email (demo)" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Select value={role} onChange={(e) => setRole(e.target.value as Role)}>
            <option value="member">Member</option>
            <option value="admin">Admin</option>
          </Select>
          <Button onClick={() => inviteMutation.mutate()}>Invite</Button>
        </Flex>
        <Text mt={2} fontSize="sm">Demo invite does not send email; endpoint requires user_id.</Text>
      </Box>
      <Box>
        <Heading size="sm">Members</Heading>
        <Box mt={2}>
          {data?.data?.map((m) => (
            <Flex key={m.id} justify="space-between" p={2} borderWidth="1px" borderRadius="md">
              <Text>Member #{m.user_id.slice(0, 8)}…</Text>
              <Text>Role: {m.role}</Text>
            </Flex>
          )) ?? <Text>No members</Text>}
        </Box>
      </Box>
    </Flex>
  )
}

export default MembersPage