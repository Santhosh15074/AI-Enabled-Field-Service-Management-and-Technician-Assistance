import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/lib/api'

export type Notification = {
  id: number
  message: string
  link: string | null
  status: 'unread' | 'read'
  sent_on: string
}

export function useNotifications() {
  return useQuery({
    queryKey: ['notifications'],
    queryFn: () => api<Notification[]>('/api/notifications'),
  })
}

export function useUnreadCount() {
  return useQuery({
    queryKey: ['notifications', 'unread-count'],
    queryFn: () => api<{ count: number }>('/api/notifications/unread-count'),
    // A light poll so the bell's badge updates even if nothing else on the page refetches —
    // notifications arrive from someone else's action (an admin assigning you a job, say).
    refetchInterval: 30_000,
  })
}

function invalidate(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ['notifications'] })
}

export function useMarkRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => api<Notification>(`/api/notifications/${id}/read`, { method: 'PATCH' }),
    onSuccess: () => invalidate(queryClient),
  })
}

export function useMarkAllRead() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api<void>('/api/notifications/read-all', { method: 'POST' }),
    onSuccess: () => invalidate(queryClient),
  })
}
