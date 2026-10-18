import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/lib/api'

export type KnowledgeBaseEntry = {
  id: number
  category_id: number
  category_name: string
  equipment_type: string | null
  issue_pattern: string
  suggested_fix: string
}

export type KnowledgeBaseEntryInput = {
  category_id: number
  equipment_type?: string
  issue_pattern: string
  suggested_fix: string
}

export function useKnowledgeBase() {
  return useQuery({
    queryKey: ['knowledge-base'],
    queryFn: () => api<KnowledgeBaseEntry[]>('/api/knowledge-base'),
  })
}

function invalidate(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ['knowledge-base'] })
}

export function useCreateKnowledgeBaseEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: KnowledgeBaseEntryInput) => api<KnowledgeBaseEntry>('/api/knowledge-base', { method: 'POST', body }),
    onSuccess: () => invalidate(queryClient),
  })
}

export function useUpdateKnowledgeBaseEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, ...body }: KnowledgeBaseEntryInput & { id: number }) =>
      api<KnowledgeBaseEntry>(`/api/knowledge-base/${id}`, { method: 'PATCH', body }),
    onSuccess: () => invalidate(queryClient),
  })
}

export function useDeleteKnowledgeBaseEntry() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api<void>(`/api/knowledge-base/${id}`, { method: 'DELETE' }),
    onSuccess: () => invalidate(queryClient),
  })
}
