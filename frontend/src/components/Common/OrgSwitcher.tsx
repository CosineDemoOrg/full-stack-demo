import { Button, Menu, MenuContent, MenuItem, MenuTrigger } from "@chakra-ui/react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { OpenAPI } from "@/client"

type Org = { id: string; name: string }

async function fetchMyOrgs(): Promise<Org[]> {
  const res = await fetch(`${OpenAPI.BASE}/api/v1/orgs/my`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
    },
  })
  if (!res.ok) throw new Error("Failed to load orgs")
  const data = await res.json()
  return data.data as Org[]
}

async function switchOrg(orgId: string): Promise<void> {
  const res = await fetch(`${OpenAPI.BASE}/api/v1/orgs/switch/${orgId}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
    },
  })
  if (!res.ok) throw new Error("Failed to switch organization")
  const data = await res.json()
  localStorage.setItem("access_token", data.access_token)
}

export default function OrgSwitcher() {
  const queryClient = useQueryClient()
  const { data: orgs = [] } = useQuery({ queryKey: ["my-orgs"], queryFn: fetchMyOrgs })

  const onSelect = async (org: Org) => {
    await switchOrg(org.id)
    // invalidate queries to reload with new token/org
    queryClient.invalidateQueries()
  }

  if (orgs.length === 0) return null

  return (
    <Menu>
      <MenuTrigger asChild>
        <Button variant="outline" size="sm">
          Switch Org
        </Button>
      </MenuTrigger>
      <MenuContent>
        {orgs.map((org) => (
          <MenuItem key={org.id} onClick={() => onSelect(org)}>
            {org.name}
          </MenuItem>
        ))}
      </MenuContent>
    </Menu>
  )
}