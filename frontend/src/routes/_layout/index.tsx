import {
  Box,
  Container,
  Text,
  SimpleGrid,
  Card,
  GridItem,
  Flex,
  Badge,
} from "@chakra-ui/react"
import { createFileRoute } from "@tanstack/react-router"

import useAuth from "@/hooks/useAuth"

export const Route = createFileRoute("/_layout/")({
  component: Dashboard,
})

type DataPoint = {
  month: string
  projected: number
  actual: number
  credit: number
}

// Spreadsheet data
const data: DataPoint[] = [
  { month: "January", projected: 0, actual: 24217.71, credit: 22808.39 },
  { month: "February", projected: 0, actual: 3634.4, credit: 2540.92 },
  { month: "March", projected: 0, actual: 12142.88, credit: 10679.06 },
]

function sum<T extends keyof DataPoint>(key: T) {
  return data.reduce((acc, d) => acc + d[key], 0)
}

function formatCurrency(n: number) {
  return n.toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  })
}

function BarChart({
  series,
  height = 220,
  barGap = 12,
}: {
  series: { label: string; key: keyof DataPoint; color: string }[]
  height?: number
  barGap?: number
}) {
  const maxValue = Math.max(
    ...data.flatMap((d) => series.map((s) => d[s.key] as number)),
    1,
  )
  const chartPadding = 24
  const barWidth = 22
  const groupWidth = series.length * barWidth + (series.length - 1) * 6
  const chartWidth =
    chartPadding * 2 + data.length * groupWidth + (data.length - 1) * barGap

  return (
    <Box>
      <svg width="100%" viewBox={`0 0 ${chartWidth} ${height}`}>
        {/* Y-axis grid lines */}
        {[0.25, 0.5, 0.75, 1].map((t) => {
          const y = height - chartPadding - t * (height - chartPadding * 2)
          return (
            <line
              key={t}
              x1={chartPadding}
              x2={chartWidth - chartPadding}
              y1={y}
              y2={y}
              stroke="currentColor"
              opacity={0.1}
            />
          )
        })}
        {/* Bars */}
        {data.map((d, i) => {
          const baseX =
            chartPadding + i * (groupWidth + barGap) // start of group
          return series.map((s, j) => {
            const value = d[s.key] as number
            const h = (value / maxValue) * (height - chartPadding * 2)
            const x = baseX + j * (barWidth + 6)
            const y = height - chartPadding - h
            return (
              <g key={`${d.month}-${String(s.key)}`}>
                <rect
                  x={x}
                  y={y}
                  width={barWidth}
                  height={h}
                  fill={s.color}
                  rx={4}
                />
                {/* value label */}
                <text
                  x={x + barWidth / 2}
                  y={y - 6}
                  textAnchor="middle"
                  fontSize="10"
                  fill="currentColor"
                  opacity={0.7}
                >
                  {formatCurrency(value)}
                </text>
              </g>
            )
          })
        })}
        {/* X-axis labels */}
        {data.map((d, i) => {
          const x =
            chartPadding + i * (groupWidth + barGap) + groupWidth / 2
          const y = height - chartPadding / 2
          return (
            <text
              key={d.month}
              x={x}
              y={y}
              textAnchor="middle"
              fontSize="12"
              fill="currentColor"
              opacity={0.8}
            >
              {d.month}
            </text>
          )
        })}
      </svg>
      {/* Legend */}
      <Flex gap={4} mt={2} wrap="wrap">
        {series.map((s) => (
          <Flex key={s.label} align="center" gap={2}>
            <Box w="12px" h="12px" bg={s.color} borderRadius="2px" />
            <Text fontSize="sm">{s.label}</Text>
          </Flex>
        ))}
      </Flex>
    </Box>
  )
}

function LineChart({
  keys,
  height = 220,
}: {
  keys: { label: string; key: keyof DataPoint; color: string }[]
  height?: number
}) {
  const maxValue = Math.max(
    ...data.flatMap((d) => keys.map((k) => d[k.key] as number)),
    1,
  )
  const chartPadding = 24
  const chartWidth = chartPadding * 2 + (data.length - 1) * 140

  const xForIndex = (i: number) =>
    chartPadding + i * ((chartWidth - chartPadding * 2) / (data.length - 1))

  const yForValue = (v: number) =>
    height - chartPadding - (v / maxValue) * (height - chartPadding * 2)

  return (
    <Box>
      <svg width="100%" viewBox={`0 0 ${chartWidth} ${height}`}>
        {/* Grid lines */}
        {[0.25, 0.5, 0.75, 1].map((t) => {
          const y = height - chartPadding - t * (height - chartPadding * 2)
          return (
            <line
              key={t}
              x1={chartPadding}
              x2={chartWidth - chartPadding}
              y1={y}
              y2={y}
              stroke="currentColor"
              opacity={0.1}
            />
          )
        })}
        {/* Lines */}
        {keys.map((k) => {
          const points = data.map((d, i) => `${xForIndex(i)},${yForValue(d[k.key] as number)}`).join(" ")
          return (
            <polyline
              key={k.label}
              fill="none"
              stroke={k.color}
              strokeWidth={2}
              points={points}
            />
          )
        })}
        {/* Points */}
        {keys.map((k) =>
          data.map((d, i) => (
            <circle
              key={`${k.label}-${d.month}`}
              cx={xForIndex(i)}
              cy={yForValue(d[k.key] as number)}
              r={3}
              fill={k.color}
            />
          )),
        )}
        {/* X-axis labels */}
        {data.map((d, i) => (
          <text
            key={d.month}
            x={xForIndex(i)}
            y={height - chartPadding / 2}
            textAnchor="middle"
            fontSize="12"
            fill="currentColor"
            opacity={0.8}
          >
            {d.month}
          </text>
        ))}
      </svg>
      {/* Legend */}
      <Flex gap={4} mt={2} wrap="wrap">
        {keys.map((s) => (
          <Flex key={s.label} align="center" gap={2}>
            <Box w="12px" h="12px" bg={s.color} borderRadius="2px" />
            <Text fontSize="sm">{s.label}</Text>
          </Flex>
        ))}
      </Flex>
    </Box>
  )
}

function StatCard({
  title,
  value,
  color,
}: {
  title: string
  value: string
  color?: string
}) {
  return (
    <Card p={4}>
      <Text fontSize="sm" color="fg.muted">
        {title}
      </Text>
      <Text fontSize="xl" fontWeight="bold">
        {value}
      </Text>
      {color && (
        <Badge mt={2} colorPalette="green" variant="surface">
          {color}
        </Badge>
      )}
    </Card>
  )
}

function Dashboard() {
  const { user: currentUser } = useAuth()

  const totals = {
    projected: sum("projected"),
    actual: sum("actual"),
    credit: sum("credit"),
  }

  return (
    <Container maxW="full">
      <Box pt={12} m={4}>
        <Text fontSize="2xl" truncate maxW="sm">
          Hi, {currentUser?.full_name || currentUser?.email} 👋🏼
        </Text>
        <Text>Welcome back, nice to see you again!</Text>
      </Box>

      <SimpleGrid columns={{ base: 1, md: 3 }} gap={4} m={4}>
        <GridItem>
          <StatCard title="Total Projected" value={formatCurrency(totals.projected)} />
        </GridItem>
        <GridItem>
          <StatCard title="Total Actual" value={formatCurrency(totals.actual)} />
        </GridItem>
        <GridItem>
          <StatCard title="Total Credit" value={formatCurrency(totals.credit)} />
        </GridItem>
      </SimpleGrid>

      <SimpleGrid columns={{ base: 1, xl: 2 }} gap={6} m={4}>
        <Card p={4}>
          <Text fontWeight="bold" mb={2}>
            Actual vs Credit by Month
          </Text>
          <BarChart
            series={[
              { label: "Actual", key: "actual", color: "#3182CE" }, // blue.500
              { label: "Credit", key: "credit", color: "#38A169" }, // green.500
            ]}
          />
        </Card>

        <Card p={4}>
          <Text fontWeight="bold" mb={2}>
            Trends
          </Text>
          <LineChart
            keys={[
              { label: "Actual", key: "actual", color: "#3182CE" },
              { label: "Credit", key: "credit", color: "#38A169" },
            ]}
          />
        </Card>
      </SimpleGrid>
    </Container>
  )
}

export default Dashboard
