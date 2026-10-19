import { useQuery } from '@tanstack/react-query'

import { api } from '@/lib/api'

export type NamedCount = { name: string; count: number }

export type Analytics = {
  days: number
  daily: { date: string; created: number; resolved: number }[]
  by_status: NamedCount[]
  by_urgency: NamedCount[]
  by_category: NamedCount[]
  equipment_risk: NamedCount[]
  technicians: {
    id: number
    name: string
    active: number
    resolved: number
    avg_resolution_hours: number | null
  }[]
  avg_resolution_hours: number | null
}

/** Trends, workload and risk for the admin analytics page — see app.routes.analytics. */
export function useAnalytics() {
  return useQuery({
    queryKey: ['analytics'],
    queryFn: () => api<Analytics>('/api/analytics'),
  })
}
