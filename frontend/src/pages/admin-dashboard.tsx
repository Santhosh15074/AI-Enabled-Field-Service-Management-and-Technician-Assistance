import { useQuery } from '@tanstack/react-query'
import { ClipboardListIcon, ShieldAlertIcon, ShieldCheckIcon, UsersIcon, WrenchIcon } from 'lucide-react'

import { EmptyState, ListCard, PageHeader, StatGrid } from '@/components/dashboard'
import { RequestRow } from '@/components/request-row'
import { RiskBadge } from '@/components/risk-badge'
import { api } from '@/lib/api'
import { useCurrentUser } from '@/lib/auth'
import { useAllEquipment } from '@/lib/fleet'
import { useAllRequests } from '@/lib/requests'

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
  const requests = useAllRequests()
  const equipment = useAllEquipment()

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
        <ListCard
          title="Recent service requests"
          description="The latest complaints from customers."
          viewAll={{ to: '/admin/requests', label: 'All requests' }}
          query={requests}
          empty={
            <EmptyState
              icon={ClipboardListIcon}
              title="No service requests yet"
              description="Requests will appear here as soon as customers start submitting complaints."
            />
          }
          renderItem={(request) => (
            <RequestRow
              request={request}
              showUrgency
              meta={`${request.customer.name} · ${request.technician?.name ?? 'Not assigned'}`}
            />
          )}
        />
        <ListCard
          title="Equipment at risk"
          description="Critical or moderate on its latest failure prediction."
          viewAll={{ to: '/admin/failure-predictions', label: 'All equipment' }}
          query={equipment}
          filter={(item) => item.risk_level === 'critical' || item.risk_level === 'moderate'}
          empty={
            <EmptyState
              icon={ShieldCheckIcon}
              title="Nothing at risk"
              description="Equipment flagged by failure prediction will show up here."
            />
          }
          renderItem={(item) => (
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm">{item.name}</p>
                <p className="mt-0.5 truncate text-xs text-muted-foreground">
                  {item.type} · {item.customer.name}
                </p>
              </div>
              <RiskBadge riskLevel={item.risk_level} />
            </div>
          )}
        />
      </div>
    </>
  )
}
