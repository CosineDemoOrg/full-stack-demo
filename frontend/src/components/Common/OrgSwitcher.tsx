import { Button, Menu, MenuButton, MenuItem, MenuList } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { ChevronDownIcon } from "@chakra-ui/icons"

type Org = { id: string; name: string }

const API_BASE = import.meta.env.VITE_API_URL

async function fetchOrgs(): Promise<Org[]> {
  const res = await fetch(`${API_BASE}/orgs/`, {
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
    },
  })
  if (!res.ok) throw new Error("Failed to load orgs")
  const data = await res.json()
  return data.data as Org[]
}

async function switchOrg(orgId: string): Promise<string> {
  const res = await fetch(`${API_BASE}/orgs/${orgId}/switch`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${localStorage.getItem("access_token") || ""}`,
    },
  })
  if (!res.ok) throw new Error("Failed to switch org")
  const data = await res.json()
  return data.access_token as string
}

export default function OrgSwitcher() {
  const { data: orgs } = useQuery({ queryKey: ["orgs"], queryFn: fetchOrgs })
  const onSelect = async (orgId: string) => {
    const token = await switchOrg(orgId)
    localStorage.setItem("access_token", token)
    window.location.reload()
  }
  const current = "Active Org"

  return (
    <Menu>
      <MenuButton as={Button} rightIcon={<ChevronDownIcon />} size="sm" variant="outline">
        {current}
      </MenuButton>
      <MenuList>
        {orgs?.map((org) => (
          <MenuItem key={org.id} onClick={() => onSelect(org.id)}>
            {org.name}
          </MenuItem>
        ))}
      </MenuList>
    </Menu>
  )
}