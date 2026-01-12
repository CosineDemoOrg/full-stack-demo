import { Select } from "@chakra-ui/react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { LoginService, type Token } from "@/client"
import { OrganizationsService } from "@/client/organizations"
import { handleError } from "@/utils"

function OrgSwitcher() {
  const queryClient = useQueryClient()

  const { data: orgsData } = useQuery({
    queryKey: ["organizations"],
    queryFn: OrganizationsService.readOrganizations,
  })

  const switchOrgMutation = useMutation({
    mutationFn: OrganizationsService.switchActiveOrg,
    onSuccess: async (data: Token) => {
      localStorage.setItem("access_token", data.access_token)
      await queryClient.invalidateQueries({ queryKey: ["currentUser"] })
      await queryClient.invalidateQueries({ queryKey: ["items"] })
    },
    onError: handleError,
  })

  const handleChange = (event: React.ChangeEvent<HTMLSelectElement>) => {
    const orgId = event.target.value
    if (!orgId) return
    switchOrgMutation.mutate({ orgId })
  }

  const organizations = orgsData?.data ?? []

  if (organizations.length === 0) {
    return null
  }

  return (
    <Select
      size="sm"
      maxW="200px"
      onChange={handleChange}
      placeholder="Select organization"
    >
      {organizations.map((org) => (
        <option key={org.id} value={org.id}>
          {org.name}
        </option>
      ))}
    </Select>
  )
}

export default OrgSwitcher