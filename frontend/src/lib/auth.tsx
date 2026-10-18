import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, ApiError } from '@/lib/api'

export type Role = 'admin' | 'customer' | 'technician'

export type User = {
  id: number
  name: string
  // Optional: customers may register with only a phone number. Staff always have one.
  email: string | null
  role: Role
  // Customers only — null for staff, and null for a customer who hasn't raised a
  // complaint yet (that's when it's first asked for).
  address: string | null
}

export const ROLE_HOME: Record<Role, string> = {
  admin: '/admin',
  customer: '/portal',
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
    // "identifier" because it's an email for staff, but an email or a phone number for a customer.
    mutationFn: (body: { identifier: string; password: string }) =>
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

export type RegisterInput = {
  name: string
  phone: string
  password: string
  email?: string
}

/** The customer portal's sign-up. Always creates a customer account — see app/routes/auth.py. */
export function useRegister() {
  return useMutation({
    mutationFn: (body: RegisterInput) => api<User>('/api/auth/register', { method: 'POST', body }),
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
