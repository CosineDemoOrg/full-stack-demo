import { Button, Menu, MenuButton, MenuItem, MenuList, Text } from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { useState } from "react"

type Organization = {
  id: string
  name: string
}

async function fetchOrgs(): Promise<Organization[]> {
  const res = await fetch("/api/v1/orgs/")
  const data = await res.json()
  return data.data
}

async function switchOrg(orgId: string): Promise<string> {
  const res = await fetch(`/api/v1/orgs/switch/${orgId}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
  const data = await res.json()
  return data.access_token
}

export default function OrgSwitcher() {
  const { data: orgs } = useQuery({ queryKey: ["orgs"], queryFn: fetchOrgs })
  const [activeName, setActiveName] = useState<string>("Select org")

  const onSwitch = async (org: Organization) => {
    const token = await switchOrg(org.id)
    // store token and refresh
    localStorage.setItem("access_token", token)
    setActiveName(org.name)
    window.location.reload()
  }

  return (
    <Menu>
      <MenuButton as={Button} variant="subtle">
        <Text>{activeName}</Text>
      </MenuButton>
      <MenuList>
        {orgs?.map((org) => (
          <MenuItem key={org.id} onClick={() => onSwitch(org)}>
            {org.name}
          </MenuItem>
        ))}
      </MenuList>
    </Menu>
  )
}