import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/lib/api'

export type Plan = 'starter' | 'growth' | 'pro'

/** What each plan includes (founder/pricing.md); mirrors PLAN_LIMITS in app/models.py. */
export const PLANS: Record<Plan, { label: string; price: string; technicians: number; reports: number }> = {
  starter: { label: 'Starter', price: '₹1,499', technicians: 10, reports: 750 },
  growth: { label: 'Growth', price: '₹2,999', technicians: 25, reports: 2000 },
  pro: { label: 'Pro', price: '₹5,999', technicians: 50, reports: 4000 },
}

export type ShopSummary = {
  id: number
  name: string
  slug: string
  is_active: boolean
  plan: Plan
  technician_limit: number
  monthly_report_limit: number
  contact_phone: string | null
  created_at: string
  active_technicians: number
  customers: number
  reports_this_month: number
}

export type StaffRole = 'admin' | 'technician'

export type Staff = {
  id: number
  name: string
  email: string | null
  role: StaffRole
  is_active: boolean
  skill_area: string | null
}

export type ShopDetail = ShopSummary & { staff: Staff[] }

export type NewShop = {
  name: string
  slug: string
  plan: Plan
  contact_phone?: string
  owner_name: string
  owner_email: string
  owner_password: string
}

export type ShopChanges = Partial<{
  name: string
  slug: string
  is_active: boolean
  plan: Plan
  technician_limit: number
  monthly_report_limit: number
  contact_phone: string
}>

export type NewStaff = { name: string; email: string; password: string; role: StaffRole; skill_area?: string }

export const ROLE_LABEL: Record<StaffRole, string> = { admin: 'Owner', technician: 'Technician' }

/** The link a shop sends its customers to sign up with; it puts them in that shop. */
export function signUpLink(slug: string): string {
  return `${window.location.origin}/portal/register?shop=${slug}`
}

const SHOPS_KEY = ['shops']
const shopKey = (id: number) => ['shops', id]

export function useShops() {
  return useQuery({ queryKey: SHOPS_KEY, queryFn: () => api<ShopSummary[]>('/api/platform/shops') })
}

export function useShop(id: number) {
  return useQuery({ queryKey: shopKey(id), queryFn: () => api<ShopDetail>(`/api/platform/shops/${id}`) })
}

/** Every mutation answers with the shop's fresh detail; store it, and let the list refetch. */
function useShopMutation<T>(request: (body: T) => Promise<ShopDetail>) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: request,
    onSuccess: (shop) => {
      queryClient.setQueryData(shopKey(shop.id), shop)
      queryClient.invalidateQueries({ queryKey: SHOPS_KEY, exact: true })
    },
  })
}

export function useCreateShop() {
  return useShopMutation((body: NewShop) => api<ShopDetail>('/api/platform/shops', { method: 'POST', body }))
}

export function useUpdateShop(id: number) {
  return useShopMutation((body: ShopChanges) => api<ShopDetail>(`/api/platform/shops/${id}`, { method: 'PATCH', body }))
}

export function useAddStaff(shopId: number) {
  return useShopMutation((body: NewStaff) =>
    api<ShopDetail>(`/api/platform/shops/${shopId}/staff`, { method: 'POST', body }),
  )
}

export function useSetStaffActive() {
  return useShopMutation(({ userId, is_active }: { userId: number; is_active: boolean }) =>
    api<ShopDetail>(`/api/platform/users/${userId}/active`, { method: 'PATCH', body: { is_active } }),
  )
}

export function useResetPassword() {
  return useMutation({
    mutationFn: ({ userId, password }: { userId: number; password: string }) =>
      api<void>(`/api/platform/users/${userId}/password`, { method: 'POST', body: { password } }),
  })
}
