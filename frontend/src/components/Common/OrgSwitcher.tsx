import { Select } from "@chakra-ui/react"
import { useEffect, useState } from "react"
import { OpenAPI } from "@/client"

type Org = { id: string; name: string }

function OrgSwitcher() {
  const [orgs, setOrgs] = useState<Org[]>([])
  const [activeOrgId, setActiveOrgId] = useState<string | null>(null)

  useEffect(() => {
    const loadOrgs = async () => {
      try {
        const resp = await fetch(`${OpenAPI.BASE}/api/v1/orgs/`, {
          headers: {
            Authorization: `Bearer ${await Promise.resolve(
              typeof OpenAPI.TOKEN === "function" ? OpenAPI.TOKEN({} as any) : OpenAPI.TOKEN!,
            )}`,
          },
        })
        const data = await resp.json()
        const list = (data.data ?? []) as Org[]
        setOrgs(list)
        // Try to decode token active_org_id
        const token = localStorage.getItem("access_token")
        if (token) {
          const payload = JSON.parse(atob(token.split(".")[1]))
          setActiveOrgId(payload.active_org_id ?? null)
        }
      } catch {
        // noop
      }
    }
    loadOrgs()
  }, [])

  const onChange = async (e: React.ChangeEvent<HTMLSelectElement>) => {
    const newOrgId = e.target.value
    try {
      const resp = await fetch(`${OpenAPI.BASE}/api/v1/orgs/switch/${newOrgId}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${await Promise.resolve(
            typeof OpenAPI.TOKEN === "function" ? OpenAPI.TOKEN({} as any) : OpenAPI.TOKEN!,
          )}`,
        },
      })
      const data = await resp.json()
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token)
        setActiveOrgId(newOrgId)
        // reload to refetch queries with new org
        location.reload()
      }
    } catch {
      // noop
    }
  }

  if (orgs.length === 0) return null

  return (
    <Select
      size="sm"
      value={activeOrgId ?? ""}
      onChange={onChange}
      placeholder="Select organization"
      variant="filled"
      bg="gray.700"
      color="white"
      maxW="xs"
    >
      {orgs.map((o) => (
        <option key={o.id} value={o.id}>
          {o.name}
        </option>
      ))}
    </Select>
  )
}

export default OrgSwitcher