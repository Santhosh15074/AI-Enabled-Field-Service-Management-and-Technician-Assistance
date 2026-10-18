import { Route, Routes } from 'react-router-dom'

import { AppShell } from '@/components/app-shell'
import { GuestOnly, HomeRedirect, RequireRole } from '@/components/route-guards'
import { AdminDashboard } from '@/pages/admin-dashboard'
import { AdminFailurePredictionsPage } from '@/pages/admin-failure-predictions'
import { AdminKnowledgeBasePage } from '@/pages/admin-knowledge-base'
import { AdminRequestsPage } from '@/pages/admin-requests'
import { AdminUsersPage } from '@/pages/admin-users'
import { CustomerDashboard } from '@/pages/customer-dashboard'
import { LoginPage } from '@/pages/login'
import { NotFoundPage } from '@/pages/not-found'
import { CustomerEquipmentPage } from '@/pages/portal/equipment'
import { CustomerLoginPage } from '@/pages/portal/login'
import { MyRequestsPage } from '@/pages/portal/my-requests'
import { NewRequestPage } from '@/pages/portal/new-request'
import { CustomerRegisterPage } from '@/pages/portal/register'
import { TechnicianDashboard } from '@/pages/technician-dashboard'
import { TechnicianJobsPage } from '@/pages/technician-jobs'
import { TechnicianReadingsPage } from '@/pages/technician-readings'
import { TechnicianReportPage } from '@/pages/technician-report'

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<HomeRedirect />} />

      {/* Staff: admin and technician. Accounts are created by an admin — no sign-up here. */}
      <Route element={<GuestOnly />}>
        <Route path="/login" element={<LoginPage />} />
      </Route>

      {/* Customer portal: the public can sign themselves up and log in here. */}
      <Route element={<GuestOnly />}>
        <Route path="/portal/login" element={<CustomerLoginPage />} />
        <Route path="/portal/register" element={<CustomerRegisterPage />} />
      </Route>

      <Route element={<RequireRole roles={['admin']} />}>
        <Route element={<AppShell />}>
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/requests" element={<AdminRequestsPage />} />
          <Route path="/admin/users" element={<AdminUsersPage />} />
          <Route path="/admin/failure-predictions" element={<AdminFailurePredictionsPage />} />
          <Route path="/admin/knowledge-base" element={<AdminKnowledgeBasePage />} />
        </Route>
      </Route>
      <Route element={<RequireRole roles={['customer']} />}>
        <Route element={<AppShell />}>
          <Route path="/portal" element={<CustomerDashboard />} />
          <Route path="/portal/equipment" element={<CustomerEquipmentPage />} />
          <Route path="/portal/requests" element={<MyRequestsPage />} />
          <Route path="/portal/requests/new" element={<NewRequestPage />} />
        </Route>
      </Route>
      <Route element={<RequireRole roles={['technician']} />}>
        <Route element={<AppShell />}>
          <Route path="/technician" element={<TechnicianDashboard />} />
          <Route path="/technician/jobs" element={<TechnicianJobsPage />} />
          <Route path="/technician/jobs/:id/report" element={<TechnicianReportPage />} />
          <Route path="/technician/equipment/:id/readings" element={<TechnicianReadingsPage />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  )
}
