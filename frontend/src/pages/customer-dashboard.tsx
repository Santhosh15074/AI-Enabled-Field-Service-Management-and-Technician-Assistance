import { useQuery } from '@tanstack/react-query'
import {
  BellRingIcon,
  CheckCircle2Icon,
  ClipboardListIcon,
  HardDriveIcon,
  MessageSquarePlusIcon,
  MicIcon,
} from 'lucide-react'

import { EmptyState, PageHeader, Roadmap, StatGrid } from '@/components/dashboard'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { useCurrentUser } from '@/lib/auth'

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
        <Card>
          <CardHeader>
            <CardTitle>My service requests</CardTitle>
            <CardDescription>Every complaint you raise and where it stands.</CardDescription>
          </CardHeader>
          <CardContent>
            <EmptyState
              icon={MessageSquarePlusIcon}
              title="You haven't raised any requests"
              description="When something goes wrong with your equipment, describe it and we'll send the right technician."
              action={
                <Button disabled title="Available in Phase 2">
                  <MessageSquarePlusIcon aria-hidden="true" />
                  New complaint
                </Button>
              }
            />
          </CardContent>
        </Card>
        <Roadmap
          items={[
            { title: 'Register equipment', description: 'Add the devices you want serviced.', phase: 2, icon: HardDriveIcon },
            { title: 'Raise complaints', description: 'Describe an issue and track it to resolution.', phase: 2, icon: MessageSquarePlusIcon },
            { title: 'Voice complaints', description: 'Speak instead of typing.', phase: 5, icon: MicIcon },
            { title: 'Preventive alerts', description: "Hear about problems before they happen.", phase: 6, icon: BellRingIcon },
          ]}
        />
      </div>
    </>
  )
}
