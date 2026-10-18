import { useQuery } from '@tanstack/react-query'

import { api } from '@/lib/api'
import type { CustomerSummary, RiskLevel } from '@/lib/requests'

export type FleetEquipment = {
  id: number
  name: string
  type: string
  serial_number: string | null
  last_service_date: string | null
  risk_level: RiskLevel | null
  risk_score: number | null
  customer: CustomerSummary
}

/** Every customer's equipment, worst risk first — see app.routes.equipment.list_all_equipment. */
export function useAllEquipment() {
  return useQuery({
    queryKey: ['equipment', 'all'],
    queryFn: () => api<FleetEquipment[]>('/api/equipment/all'),
  })
}
