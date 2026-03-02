import { Button, Flex, Image, Select, useBreakpointValue } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { useEffect, useState } from "react"

import { OpenAPI } from "@/client"
import Logo from "/assets/images/fastapi-logo.svg"
import UserMenu from "./UserMenu"

type Org = { id: string; name: string }

function OrgSwitcher() {
  const [orgs, setOrgs] = useState<Org[]>([])
  const [activeOrg, setActiveOrg] = useState<string | null>(null)

  useEffect(() => {
    const load = async () => {
      try {
        const token = await OpenAPI.TOKEN?.({} as any)
        if (!token) return
        const res = await fetch(`${OpenAPI.BASE}/api/v1/orgs/`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        const data = await res.json()
        setOrgs(data.data || [])
      } catch {
        // ignore
      }
    }
    load()
  }, [])

  const onSwitch = async (orgId: string) => {
    const token = await OpenAPI.TOKEN?.({} as any)
    if (!token) return
    const res = await fetch(`${OpenAPI.BASE}/api/v1/orgs/${orgId}/switch`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    })
    if (res.ok) {
      const data = await res.json()
      localStorage.setItem("access_token", data.access_token)
      setActiveOrg(orgId)
      // force reload queries
      window.location.reload()
    }
  }

  return (
    <Flex align="center" gap={2}>
      <Select
        placeholder="Select org"
        value={activeOrg ?? ""}
        onChange={(e) => onSwitch(e.target.value)}
        bg="white"
        color="black"
        minW="200px"
      >
        {orgs.map((o) => (
          <option key={o.id} value={o.id}>
            {o.name}
          </option>
        ))}
      </Select>
      <Button variant="outline" size="sm" onClick={() => window.location.href = "/members"}>
        Manage
      </Button>
    </Flex>
  )
}

function Navbar() {
  const display = useBreakpointValue({ base: "none", md: "flex" })

  return (
    <Flex
      display={display}
      justify="space-between"
      position="sticky"
      color="white"
      align="center"
      bg="bg.muted"
      w="100%"
      top={0}
      p={4}
    >
      <Link to="/">
        <Image src={Logo} alt="Logo" maxW="3xs" p={2} />
      </Link>
      <Flex gap={4} alignItems="center">
        <OrgSwitcher />
        <UserMenu />
      </Flex>
    </Flex>
  )
}

export default Navbar
