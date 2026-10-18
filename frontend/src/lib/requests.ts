import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/lib/api'

export type RequestStatus = 'open' | 'in_progress' | 'resolved'

export const STATUS_LABEL: Record<RequestStatus, string> = {
  open: 'Open',
  in_progress: 'In progress',
  resolved: 'Resolved',
}

// The order a request moves through; also what a "can this go backward" check compares against.
export const STATUS_ORDER: RequestStatus[] = ['open', 'in_progress', 'resolved']

export type RiskLevel = 'good' | 'moderate' | 'critical'

export type Equipment = {
  id: number
  name: string
  type: string
  serial_number: string | null
  // Both null until a technician has recorded a reading at all — see app.ml.failure.
  risk_level: RiskLevel | null
  risk_score: number | null
}

export type EquipmentReadings = {
  quality_grade: string
  air_temperature_k: number
  process_temperature_k: number
  rotational_speed_rpm: number
  torque_nm: number
  tool_wear_min: number
}

export type TechnicianSummary = {
  id: number
  name: string
  skill_area: string | null
}

export type CustomerSummary = {
  id: number
  name: string
  phone: string
}

export type ComplaintCategory = {
  id: number
  category_name: string
  description: string | null
}

export type ServiceRequest = {
  id: number
  description: string
  status: RequestStatus
  urgency: 'low' | 'medium' | 'high'
  created_at: string
  equipment: Equipment | null
  category: ComplaintCategory | null
  customer: CustomerSummary
  technician: TechnicianSummary | null
}

// ---- Equipment ----

export function useMyEquipment() {
  return useQuery({
    queryKey: ['equipment', 'mine'],
    queryFn: () => api<Equipment[]>('/api/equipment'),
  })
}

export function useRegisterEquipment() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: { name: string; type: string; serial_number?: string }) =>
      api<Equipment>('/api/equipment', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['equipment', 'mine'] }),
  })
}

/** Scored for failure risk as soon as it's saved — see app.ml.failure.predict_risk. */
export function useRecordReadings(equipmentId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: EquipmentReadings) => api<Equipment>(`/api/equipment/${equipmentId}/readings`, { method: 'PATCH', body }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['equipment'] })
      queryClient.invalidateQueries({ queryKey: ['overview'] })
    },
  })
}

// ---- Service requests ----

function invalidateRequestLists(queryClient: ReturnType<typeof useQueryClient>) {
  // Covers mine / assigned / all, and the overview stat strips on every dashboard.
  queryClient.invalidateQueries({ queryKey: ['requests'] })
  queryClient.invalidateQueries({ queryKey: ['overview'] })
}

export function useMyRequests() {
  return useQuery({
    queryKey: ['requests', 'mine'],
    queryFn: () => api<ServiceRequest[]>('/api/requests/mine'),
  })
}

export function useCategories() {
  return useQuery({
    queryKey: ['categories'],
    queryFn: () => api<ComplaintCategory[]>('/api/requests/categories'),
    staleTime: 60 * 60 * 1000, // a fixed list — see the seed migration
  })
}

export function useCreateRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: { description: string; equipment_id?: number; category_id?: number; address?: string }) =>
      api<ServiceRequest>('/api/requests', { method: 'POST', body }),
    onSuccess: () => {
      invalidateRequestLists(queryClient)
      // The complaint may have just set the customer's address for the first time.
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
    },
  })
}

export function useAssignedRequests() {
  return useQuery({
    queryKey: ['requests', 'assigned'],
    queryFn: () => api<ServiceRequest[]>('/api/requests/assigned'),
  })
}

export function useAllRequests() {
  return useQuery({
    queryKey: ['requests', 'all'],
    queryFn: () => api<ServiceRequest[]>('/api/requests'),
  })
}

export function useTechnicians() {
  return useQuery({
    queryKey: ['technicians'],
    queryFn: () => api<TechnicianSummary[]>('/api/requests/technicians'),
  })
}

export type Suggestion = {
  equipment_type: string | null
  issue_pattern: string
  suggested_fix: string
  similarity: number
}

/** Matched against the knowledge base by meaning, not keywords — see app.ml.troubleshooting.
 * Tried before a request even exists, so a customer can attempt an easy fix themselves. */
export function useSuggestFixes() {
  return useMutation({
    mutationFn: (description: string) =>
      api<Suggestion[]>('/api/requests/suggestions', { method: 'POST', body: { description } }),
  })
}

export function useRequestSuggestions(requestId: number, enabled: boolean) {
  return useQuery({
    queryKey: ['requests', requestId, 'suggestions'],
    queryFn: () => api<Suggestion[]>(`/api/requests/${requestId}/suggestions`),
    enabled,
  })
}

export function useUpdateRequest() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: { id: number; technician_id?: number; status?: RequestStatus }) =>
      api<ServiceRequest>(`/api/requests/${id}`, { method: 'PATCH', body }),
    onSuccess: () => invalidateRequestLists(queryClient),
  })
}
