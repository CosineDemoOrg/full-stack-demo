import {
  Box,
  Container,
  Flex,
  Heading,
  Table,
  Text,
  VStack,
  EmptyState,
} from "@chakra-ui/react"
import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link } from "@tanstack/react-router"
import { FiArrowRight, FiSearch } from "react-icons/fi"

import { ItemsService, type ItemsPublic } from "@/client"
import useAuth from "@/hooks/useAuth"
import PendingItems from "@/components/Pending/PendingItems"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

function useOutgoings() {
  return useQuery<ItemsPublic>({
    queryKey: ["outgoings", { page: 1 }],
    queryFn: () => ItemsService.readItems({ skip: 0, limit: 10 }),
    placeholderData: (prev) => prev,
  })
}

function OutgoingsTable() {
  const { data, isLoading, isPlaceholderData } = useOutgoings()

  if (isLoading) {
    return <PendingItems />
  }

  const outgoings = data?.data ?? []
  if (outgoings.length === 0) {
    return (
      <EmptyState.Root>
        <EmptyState.Content>
          <EmptyState.Indicator>
            <FiSearch />
          </EmptyState.Indicator>
          <VStack textAlign="center">
            <EmptyState.Title>No outgoings found</EmptyState.Title>
            <EmptyState.Description>
              There are no records in your product catalogue yet.
            </EmptyState.Description>
          </VStack>
        </EmptyState.Content>
      </EmptyState.Root>
    )
  }

  return (
    <>
      <Table.Root size={{ base: "sm", md: "md" }}>
        <Table.Header>
          <Table.Row>
            <Table.ColumnHeader w="sm">ID</Table.ColumnHeader>
            <Table.ColumnHeader w="sm">Product</Table.ColumnHeader>
            <Table.ColumnHeader w="lg">Description</Table.ColumnHeader>
          </Table.Row>
        </Table.Header>
        <Table.Body>
          {outgoings.map((item) => (
            <Table.Row key={item.id} opacity={isPlaceholderData ? 0.5 : 1}>
              <Table.Cell truncate maxW="sm">{item.id}</Table.Cell>
              <Table.Cell truncate maxW="sm">{item.title}</Table.Cell>
              <Table.Cell color={!item.description ? "gray" : "inherit"} truncate maxW="2xl">
                {item.description || "N/A"}
              </Table.Cell>
            </Table.Row>
          ))}
        </Table.Body>
      </Table.Root>
      <Flex justifyContent="flex-end" mt={4}>
        <Link to="/items">
          <Flex align="center" gap={2} color="fg.muted" _hover={{ color: "fg" }}>
            <Text fontSize="sm">View all outgoings</Text>
            <FiArrowRight />
          </Flex>
        </Link>
      </Flex>
    </>
  )
}

function Dashboard() {
  const { user: currentUser } = useAuth()

  return (
    <Container maxW="full">
      <Box pt={12} m={4}>
        <Text fontSize="2xl" truncate maxW="sm">
          Hi, {currentUser?.full_name || currentUser?.email} 👋🏼
        </Text>
        <Text>Welcome back, nice to see you again!</Text>
      </Box>

      <Box mt={8}>
        <Heading size="md" mb={4}>
          Outgoings
        </Heading>
        <OutgoingsTable />
      </Box>
    </Container>
  )
}
