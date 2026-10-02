import { Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/app-shell'
import { GuestOnly, HomeRedirect, RequireRole } from '@/components/route-guards'
import { AdminDashboard } from '@/pages/admin-dashboard'
import { CustomerDashboard } from '@/pages/customer-dashboard'
import { LoginPage } from '@/pages/login'
import { NotFoundPage } from '@/pages/not-found'
import { TechnicianDashboard } from '@/pages/technician-dashboard'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />

      <Route element={<GuestOnly />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      <Route element={<RequireRole roles={['admin']} />}>
        <Route element={<AppShell />}>
          <Route path="/admin" element={<AdminDashboard />} />
        </Route>
      </Route>
      <Route element={<RequireRole roles={['customer']} />}>
        <Route element={<AppShell />}>
          <Route path="/customer" element={<CustomerDashboard />} />
        </Route>
      </Route>
      <Route element={<RequireRole roles={['technician']} />}>
        <Route element={<AppShell />}>
          <Route path="/technician" element={<TechnicianDashboard />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
