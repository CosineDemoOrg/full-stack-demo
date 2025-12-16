import { Flex, Image, Select, useBreakpointValue } from "@chakra-ui/react"
import { Link } from "@tanstack/react-router"
import { useQuery } from "@tanstack/react-query"
import { useEffect, useState } from "react"

import { type OrganizationPublic, OrganizationsService } from "@/client"
import Logo from "/assets/images/fastapi-logo.svg"
import UserMenu from "./UserMenu"

function Navbar() {
  const display = useBreakpointValue({ base: "none", md: "flex" })
  const [activeOrgId, setActiveOrgId] = useState<string | undefined>(undefined)

  const { data: orgs } = useQuery({
    queryKey: ["organizations"],
    queryFn: () => OrganizationsService.readOrganizations({ skip: 0, limit: 100 }),
    enabled: !!localStorage.getItem("access_token"),
  })

  useEffect(() => {
    if (!orgs || orgs.data.length === 0) {
      return
    }
    if (!activeOrgId) {
      const stored = localStorage.getItem("active_org_id")
      if (stored) {
        setActiveOrgId(stored)
      } else {
        const first = orgs.data[0] as OrganizationPublic
        setActiveOrgId(first.id)
        localStorage.setItem("active_org_id", first.id)
      }
    }
  }, [orgs, activeOrgId])

  const handleOrgChange = async (orgId: string) => {
    setActiveOrgId(orgId)
    localStorage.setItem("active_org_id", orgId)
    await OrganizationsService.switchActiveOrganization({ org_id: orgId })
  }

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
        {orgs && orgs.data.length > 0 && (
          <Select
            size="sm"
            value={activeOrgId ?? ""}
            onChange={(e) => handleOrgChange(e.target.value)}
            maxW="200px"
          >
            {orgs.data.map((org) => (
              <option key={org.id} value={org.id}>
                {org.name}
              </option>
            ))}
          </Select>
        )}
        <UserMenu />
      </Flex>
    </Flex>
  )
}

export default Navbar
