import { Button, MenuContent, MenuItem, MenuRoot, MenuTrigger } from "@chakra-ui/react"
import { useEffect, useState } from "react"

type Org = {
  id: string
  name: string
}

const API_BASE = import.meta.env.VITE_API_URL || ""

async function fetchOrgs(): Promise<Org[]> {
  const resp = await fetch(`${API_BASE}/api/v1/orgs/`, {
    headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
  })
  if (!resp.ok) return []
  const data = await resp.json()
  return data.data || []
}

async function switchOrg(orgId: string): Promise<string | null> {
  const resp = await fetch(`${API_BASE}/api/v1/orgs/${orgId}/switch`, {
    method: "POST",
    headers: { Authorization: `Bearer ${localStorage.getItem("access_token")}` },
  })
  if (!resp.ok) return null
  const data = await resp.json()
  return data.access_token as string
}

export default function OrgSwitcher() {
  const [orgs, setOrgs] = useState<Org[]>([])
  const [currentOrg, setCurrentOrg] = useState<Org | null>(null)

  useEffect(() => {
    fetchOrgs().then((o) => {
      setOrgs(o)
      if (o.length > 0) {
        // Best effort: no way to decode token easily here, just show first as selected
        setCurrentOrg(o[0])
      }
    })
  }, [])

  const onSelect = async (org: Org) => {
    const token = await switchOrg(org.id)
    if (token) {
      localStorage.setItem("access_token", token)
      setCurrentOrg(org)
      // Simple reload to refresh data under new org context
      window.location.reload()
    }
  }

  if (orgs.length === 0) return null

  return (
    <MenuRoot>
      <MenuTrigger asChild>
        <Button variant="subtle" data-testid="org-switcher">
          {currentOrg?.name || "Select org"}
        </Button>
      </MenuTrigger>
      <MenuContent>
        {orgs.map((org) => (
          <MenuItem key={org.id} value={org.id} onClick={() => onSelect(org)} style={{ cursor: "pointer" }}>
            {org.name}
          </MenuItem>
        ))}
      </MenuContent>
    </MenuRoot>
  )
}