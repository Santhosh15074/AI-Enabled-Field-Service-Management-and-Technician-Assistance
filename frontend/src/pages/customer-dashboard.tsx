import { useQuery } from '@tanstack/react-query'
import { CheckCircle2Icon, ClipboardListIcon, HardDriveIcon, MessageSquarePlusIcon, PlusIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

import { EmptyState, ListCard, PageHeader, StatGrid } from '@/components/dashboard'
import { RequestRow } from '@/components/request-row'
import { RiskBadge } from '@/components/risk-badge'
import { Button } from '@/components/ui/button'
import { api } from '@/lib/api'
import { useCurrentUser } from '@/lib/auth'
import { useMyEquipment, useMyRequests } from '@/lib/requests'

type CustomerOverview = {
  equipment: number
  open_requests: number
  resolved_requests: number
}

export function CustomerDashboard() {
  const { data: user } = useCurrentUser()
  const overview = useQuery({
    queryKey: ['overview', 'customer'],
    queryFn: () => api<CustomerOverview>('/api/overview/customer'),
  })
  const data = overview.data
  const requests = useMyRequests()
  const equipment = useMyEquipment()

  return (
    <>
      <PageHeader name={user!.name} description="Track your service requests and keep your equipment running." />
      <StatGrid
        error={overview.error}
        stats={[
          { label: 'Open requests', value: data?.open_requests, icon: ClipboardListIcon, hint: 'Waiting or being worked on' },
          { label: 'Resolved', value: data?.resolved_requests, icon: CheckCircle2Icon, hint: 'Completed visits', tone: 'success' },
          { label: 'My equipment', value: data?.equipment, icon: HardDriveIcon, hint: 'Registered devices', tone: 'warning' },
        ]}
      />

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <ListCard
          title="My service requests"
          description="Your latest complaints and where they stand."
          viewAll={{ to: '/portal/requests', label: 'All requests' }}
          query={requests}
          empty={
            <EmptyState
              icon={MessageSquarePlusIcon}
              title="You haven't raised any requests"
              description="When something goes wrong with your equipment, describe it and we'll send the right technician."
              action={
                <Button asChild>
                  <Link to="/portal/requests/new">
                    <MessageSquarePlusIcon aria-hidden="true" />
                    New complaint
                  </Link>
                </Button>
              }
            />
          }
          renderItem={(request) => (
            <RequestRow
              request={request}
              meta={request.technician ? `Technician: ${request.technician.name}` : 'Waiting for a technician'}
            />
          )}
        />
        <ListCard
          title="My equipment"
          description="Failure risk from your technician's latest readings."
          viewAll={{ to: '/portal/equipment', label: 'Manage' }}
          query={equipment}
          empty={
            <EmptyState
              icon={HardDriveIcon}
              title="No equipment registered"
              description="Register the equipment you want serviced so complaints can be linked to it."
              action={
                <Button asChild variant="outline">
                  <Link to="/portal/equipment">
                    <PlusIcon aria-hidden="true" />
                    Add equipment
                  </Link>
                </Button>
              }
            />
          }
          renderItem={(item) => (
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <p className="truncate text-sm">{item.name}</p>
                <p className="mt-0.5 truncate text-xs text-muted-foreground">{item.type}</p>
              </div>
              <RiskBadge riskLevel={item.risk_level} />
            </div>
          )}
        />
      </div>
    </>
  )
}
