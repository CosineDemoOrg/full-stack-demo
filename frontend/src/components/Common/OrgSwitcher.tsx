import { Button, Select } from "@chakra-ui/react"
import { useEffect, useState } from "react"
import useOrgs from "@/hooks/useOrgs"

const OrgSwitcher = () => {
  const { orgs, switchMutation } = useOrgs()
  const [selected, setSelected] = useState<string | undefined>(undefined)

  useEffect(() => {
    if (orgs.length && !selected) {
      setSelected(orgs[0].id)
    }
  }, [orgs])

  const onSwitch = () => {
    if (selected) {
      switchMutation.mutate(selected)
    }
  }

  return (
    <>
      <Select
        size="sm"
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
        maxW="200px"
        color="black"
        bg="white"
      >
        {orgs.map((o) => (
          <option key={o.id} value={o.id}>
            {o.name}
          </option>
        ))}
      </Select>
      <Button onClick={onSwitch} size="sm" variant="outline" colorScheme="teal">
        Switch
      </Button>
    </>
  )
}

export default OrgSwitcher