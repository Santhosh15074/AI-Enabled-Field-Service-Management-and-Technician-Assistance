import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, ApiError } from '@/lib/api'

export type Role = 'admin' | 'customer' | 'technician'

export type User = {
  id: number
  name: string
  email: string
  role: Role
}

export const ROLE_HOME: Record<Role, string> = {
  admin: '/admin',
  customer: '/customer',
  technician: '/technician',
}

export const ROLE_LABEL: Record<Role, string> = {
  admin: 'Admin',
  customer: 'Customer',
  technician: 'Technician',
}

const ME_KEY = ['auth', 'me']

/** The logged-in user, or null when nobody is logged in. */
export function useCurrentUser() {
  return useQuery({
    queryKey: ME_KEY,
    queryFn: async () => {
      try {
        return await api<User>('/api/auth/me')
      } catch (error) {
        if (error instanceof ApiError && error.status === 401) return null
        throw error
      }
    },
    staleTime: 5 * 60 * 1000,
  })
}

export function useLogin() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: { email: string; password: string }) =>
      api<User>('/api/auth/login', { method: 'POST', body }),
    onSuccess: (user) => {
      // Drop anything cached for a previous user before showing the new one's data.
      queryClient.clear()
      queryClient.setQueryData(ME_KEY, user)
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api<void>('/api/auth/logout', { method: 'POST' }),
    onSuccess: () => {
      queryClient.clear()
      queryClient.setQueryData(ME_KEY, null)
    },
  })
}

export function initials(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]!.toUpperCase())
    .join('')
}
