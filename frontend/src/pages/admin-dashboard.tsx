import { useQuery } from '@tanstack/react-query'
import {
  BarChart3Icon,
  BookOpenIcon,
  BrainCircuitIcon,
  ClipboardListIcon,
  ShieldAlertIcon,
  UsersIcon,
  WrenchIcon,
} from 'lucide-react'

import { EmptyState, PageHeader, Roadmap, StatGrid } from '@/components/dashboard'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { useCurrentUser } from '@/lib/auth'

type AdminOverview = {
  customers: number
  technicians: number
  open_requests: number
  critical_equipment: number
}

export function AdminDashboard() {
  const { data: user } = useCurrentUser()
  const overview = useQuery({
    queryKey: ['overview', 'admin'],
    queryFn: () => api<AdminOverview>('/api/overview/admin'),
  })
  const data = overview.data

  return (
    <>
      <PageHeader name={user!.name} description="Here's what's happening across your field service operation." />
      <StatGrid
        error={overview.error}
        stats={[
          { label: 'Open requests', value: data?.open_requests, icon: ClipboardListIcon, hint: 'Open or in progress' },
          { label: 'Customers', value: data?.customers, icon: UsersIcon, hint: 'Registered accounts', tone: 'success' },
          { label: 'Technicians', value: data?.technicians, icon: WrenchIcon, hint: 'Active in the field', tone: 'warning' },
          {
            label: 'Critical equipment',
            value: data?.critical_equipment,
            icon: ShieldAlertIcon,
            hint: 'Flagged by failure prediction',
            tone: 'danger',
          },
        ]}
      />

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>Recent service requests</CardTitle>
            <CardDescription>The latest complaints from customers.</CardDescription>
          </CardHeader>
          <CardContent>
            <EmptyState
              icon={ClipboardListIcon}
              title="No service requests yet"
              description="Requests will appear here as soon as customers start submitting complaints."
            />
          </CardContent>
        </Card>
        <Roadmap
          items={[
            { title: 'Request management', description: 'Assign technicians and track every status change.', phase: 2, icon: ClipboardListIcon },
            { title: 'AI complaint triage', description: 'Auto-classify type and urgency on arrival.', phase: 3, icon: BrainCircuitIcon },
            { title: 'Knowledge base', description: 'Issue and fix pairs that power troubleshooting.', phase: 4, icon: BookOpenIcon },
            { title: 'Failure prediction', description: 'Daily risk scores for every piece of equipment.', phase: 6, icon: ShieldAlertIcon },
            { title: 'Analytics', description: 'Trends, workload and risk charts.', phase: 7, icon: BarChart3Icon },
          ]}
        />
      </div>
    </>
  )
}
