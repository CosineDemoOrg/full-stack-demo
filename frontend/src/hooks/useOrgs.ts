import { useMutation, useQuery } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"
import { OpenAPI } from "@/client"

type OrganizationPublic = {
  id: string
  name: string
  description?: string | null
}
type OrganizationsPublic = {
  data: OrganizationPublic[]
  count: number
}

const useOrgs = () => {
  const navigate = useNavigate()
  const { data } = useQuery<OrganizationsPublic>({
    queryKey: ["orgs"],
    queryFn: async () => {
      const res = await fetch(`${OpenAPI.BASE}/api/v1/orgs/`, {
        headers: {
          Authorization: `Bearer ${await Promise.resolve(OpenAPI.TOKEN?.({} as any) as any)}`,
        },
      })
      if (!res.ok) throw new Error("Failed to load orgs")
      return res.json()
    },
  })

  const switchMutation = useMutation({
    mutationFn: async (orgId: string) => {
      const res = await fetch(`${OpenAPI.BASE}/api/v1/orgs/switch/${orgId}`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${await Promise.resolve(OpenAPI.TOKEN?.({} as any) as any)}`,
        },
      })
      if (!res.ok) throw new Error("Failed to switch org")
      return res.json() as Promise<{ access_token: string }>
    },
    onSuccess: (token) => {
      localStorage.setItem("access_token", token.access_token)
      // refresh current page
      navigate({ to: ".", replace: true })
    },
  })

  return {
    orgs: data?.data ?? [],
    switchMutation,
  }
}

export default useOrgs