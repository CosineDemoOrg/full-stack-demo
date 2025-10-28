import {
  Button,
  Menu,
  MenuButton,
  MenuItem,
  MenuList,
  Spinner,
} from "@chakra-ui/react"
import { useEffect, useState } from "react"
import { ChevronDownIcon } from "@chakra-ui/icons"
import { useQueryClient } from "@tanstack/react-query"

type Org = { id: string; name: string }

async function fetchOrgs(): Promise<Org[]> {
  const token = localStorage.getItem("access_token")
  const res = await fetch("/api/v1/orgs/", {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error("Failed to load orgs")
  const data = await res.json()
  return data.data
}

async function switchOrg(orgId: string): Promise<string> {
  const token = localStorage.getItem("access_token")
  const res = await fetch(`/api/v1/orgs/${orgId}/switch`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!res.ok) throw new Error("Failed to switch org")
  const data = await res.json()
  return data.access_token as string
}

function parseActiveOrgId(token: string | null): string | null {
  if (!token) return null
  try {
    const [, payload] = token.split(".")
    const json = JSON.parse(atob(payload))
    return json.active_org_id ?? null
  } catch {
    return null
  }
}

export default function OrgSwitcher() {
  const [orgs, setOrgs] = useState<Org[] | null>(null)
  const [loading, setLoading] = useState(false)
  const [activeOrgId, setActiveOrgId] = useState<string | null>(parseActiveOrgId(localStorage.getItem("access_token")))
  const qc = useQueryClient()

  useEffect(() => {
    let mounted = true
    setLoading(true)
    fetchOrgs()
      .then((o) => mounted && setOrgs(o))
      .finally(() => mounted && setLoading(false))
    return () => {
      mounted = false
    }
  }, [])

  const activeOrgName =
    orgs?.find((o) => o.id === activeOrgId)?.name ?? "Select org"

  const handleSwitch = async (orgId: string) => {
    setLoading(true)
    try {
      const newToken = await switchOrg(orgId)
      localStorage.setItem("access_token", newToken)
      setActiveOrgId(parseActiveOrgId(newToken))
      // invalidate user and items queries
      qc.invalidateQueries()
    } finally {
      setLoading(false)
    }
  }

  if (loading && !orgs) {
    return <Spinner size="sm" />
  }

  return (
    <Menu>
      <MenuButton as={Button} rightIcon={<ChevronDownIcon />}>
        {activeOrgName}
      </MenuButton>
      <MenuList>
        {(orgs ?? []).map((org) => (
          <MenuItem key={org.id} onClick={() => handleSwitch(org.id)}>
            {org.name}
          </MenuItem>
        ))}
      </MenuList>
    </Menu>
  )
}