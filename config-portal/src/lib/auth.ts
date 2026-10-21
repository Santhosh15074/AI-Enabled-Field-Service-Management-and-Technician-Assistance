import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api, ApiError } from '@/lib/api'

/** A Sollu operator. Separate from shop accounts: own login, own cookie (app/operator_auth.py). */
export type Operator = { id: number; name: string; email: string }

const ME_KEY = ['operator', 'me']

/** The logged-in operator, or null when nobody is logged in. */
export function useOperator() {
  return useQuery({
    queryKey: ME_KEY,
    queryFn: async () => {
      try {
        return await api<Operator>('/api/platform/auth/me')
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
      api<Operator>('/api/platform/auth/login', { method: 'POST', body }),
    onSuccess: (operator) => {
      queryClient.clear()
      queryClient.setQueryData(ME_KEY, operator)
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => api<void>('/api/platform/auth/logout', { method: 'POST' }),
    onSuccess: () => {
      queryClient.clear()
      queryClient.setQueryData(ME_KEY, null)
    },
  })
}
