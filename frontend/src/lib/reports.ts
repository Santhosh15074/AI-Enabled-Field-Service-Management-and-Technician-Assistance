import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, ApiError } from '@/lib/api'

export type ExtractedFields = {
  issue: string | null
  action_taken: string | null
  parts_used: string | null
  time_spent_minutes: number | null
}

/** 'ai': Gemini structured the notes (app.ml.report_ai); 'rules': the keyword fallback did. */
export type Extraction = ExtractedFields & { source: 'ai' | 'rules' }

export type ServiceReport = ExtractedFields & {
  id: number
  request_id: number
  report_text: string
  created_at: string
}

/** A report for this request, or null if it doesn't have one yet (not an error state). */
export function useReport(requestId: number, enabled = true) {
  return useQuery({
    queryKey: ['requests', requestId, 'report'],
    queryFn: async () => {
      try {
        return await api<ServiceReport>(`/api/requests/${requestId}/report`)
      } catch (error) {
        if (error instanceof ApiError && error.status === 404) return null
        throw error
      }
    },
    enabled,
  })
}

/** A preview only — see app.report_extraction. Nothing is saved until useCreateReport runs. */
export function useExtractReport(requestId: number) {
  return useMutation({
    mutationFn: (reportText: string) =>
      api<Extraction>(`/api/requests/${requestId}/report/extract`, { method: 'POST', body: { report_text: reportText } }),
  })
}

export function useCreateReport(requestId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: ExtractedFields & { report_text: string }) =>
      api<ServiceReport>(`/api/requests/${requestId}/report`, { method: 'POST', body }),
    onSuccess: (report) => queryClient.setQueryData(['requests', requestId, 'report'], report),
  })
}
