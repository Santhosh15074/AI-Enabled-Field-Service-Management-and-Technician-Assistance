import { Navigate, Outlet, Route, Routes } from 'react-router-dom'
import { Loader2Icon } from 'lucide-react'

import { Layout } from '@/components/layout'
import { useOperator } from '@/lib/auth'
import { LoginPage } from '@/pages/login'
import { NewShopPage } from '@/pages/new-shop'
import { ShopPage } from '@/pages/shop'
import { ShopsPage } from '@/pages/shops'

export default function App() {
  return (
    <Routes>
      <Route element={<GuestOnly />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>
      <Route element={<RequireOperator />}>
        <Route element={<Layout />}>
          <Route path="/" element={<ShopsPage />} />
          <Route path="/shops/new" element={<NewShopPage />} />
          <Route path="/shops/:shopId" element={<ShopPage />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

function Spinner() {
  return (
    <div className="flex min-h-svh items-center justify-center" role="status">
      <Loader2Icon className="size-6 animate-spin text-muted-foreground" aria-hidden="true" />
      <span className="sr-only">Loading…</span>
    </div>
  )
}

function RequireOperator() {
  const { data: operator, isPending } = useOperator()
  if (isPending) return <Spinner />
  return operator ? <Outlet /> : <Navigate to="/login" replace />
}

function GuestOnly() {
  const { data: operator, isPending } = useOperator()
  if (isPending) return <Spinner />
  return operator ? <Navigate to="/" replace /> : <Outlet />
}
