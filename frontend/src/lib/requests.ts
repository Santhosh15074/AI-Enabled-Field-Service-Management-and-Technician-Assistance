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
  /** How urgency was decided (see app.ml.triage); null on requests from before triage existed. */
  urgency_source: 'safety_rule' | 'ai' | 'model' | null
  urgency_reason: string | null
  /** 'ai' when the category was picked by AI rather than by whoever raised the request. */
  category_source: 'ai' | null
  created_at: string
  equipment: Equipment | null
  category: ComplaintCategory | null
  customer: CustomerSummary
  technician: TechnicianSummary | null
}

// ---- Equipment ----

export function useMyEquipment(enabled = true) {
  return useQuery({
    queryKey: ['equipment', 'mine'],
    queryFn: () => api<Equipment[]>('/api/equipment'),
    enabled,
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
    mutationFn: (body: {
      description: string
      equipment_id?: number
      category_id?: number
      address?: string
      // Staff only: the customer a request is raised for.
      customer_id?: number
    }) =>
      api<ServiceRequest>('/api/requests', { method: 'POST', body }),
    onSuccess: () => {
      invalidateRequestLists(queryClient)
      // The request may have just set the customer's address for the first time.
      queryClient.invalidateQueries({ queryKey: ['auth', 'me'] })
      queryClient.invalidateQueries({ queryKey: ['customers'] })
    },
  })
}

export type CustomerChoice = {
  id: number
  name: string
  phone: string
  address: string | null
  equipment: { id: number; name: string; type: string }[]
}

/** Customers and their equipment, for staff raising a request on someone's behalf. */
export function useCustomerChoices(enabled: boolean) {
  return useQuery({
    queryKey: ['customers', 'choices'],
    queryFn: () => api<CustomerChoice[]>('/api/requests/customers'),
    enabled,
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

export type AssignmentSuggestion = {
  technician_id: number
  technician_name: string
  reason: string
  source: 'ai' | 'rules'
}

/** Who should take this request, and why — see app.ml.assignment. Fetched only when asked for. */
export function useAssignmentSuggestion(requestId: number, enabled: boolean) {
  return useQuery({
    queryKey: ['requests', requestId, 'assignment-suggestion'],
    queryFn: () => api<AssignmentSuggestion | null>(`/api/requests/${requestId}/assignment-suggestion`),
    enabled,
  })
}

export type Suggestion = {
  equipment_type: string | null
  issue_pattern: string
  suggested_fix: string
  /** 0-1 for a knowledge-base match; null for an AI draft. */
  similarity: number | null
  /** 'ai': generated because nothing in the knowledge base matched, unchecked, staff only. */
  source: 'knowledge_base' | 'ai'
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
