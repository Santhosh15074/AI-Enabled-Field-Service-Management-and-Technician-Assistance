import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/lib/api'

export type StaffRole = 'admin' | 'technician'

export type StaffUser = {
  id: number
  name: string
  email: string | null
  role: StaffRole | 'customer'
  is_active: boolean
  created_at: string
  skill_area: string | null
  phone: string | null
}

export function useUsers() {
  return useQuery({
    queryKey: ['users'],
    queryFn: () => api<StaffUser[]>('/api/users'),
  })
}

export type CreateStaffUserInput = {
  name: string
  email: string
  password: string
  role: StaffRole
  skill_area?: string
}

export function useCreateStaffUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: CreateStaffUserInput) => api<StaffUser>('/api/users', { method: 'POST', body }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })
}

export function useSetUserActive() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, is_active }: { id: number; is_active: boolean }) =>
      api<StaffUser>(`/api/users/${id}/active`, { method: 'PATCH', body: { is_active } }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  })
}
