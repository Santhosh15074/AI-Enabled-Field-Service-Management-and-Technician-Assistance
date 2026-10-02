import { useQuery } from '@tanstack/react-query'
import { CheckCircle2Icon, FileTextIcon, InboxIcon, LightbulbIcon, TimerIcon, WrenchIcon } from 'lucide-react'

import { EmptyState, PageHeader, Roadmap, StatGrid } from '@/components/dashboard'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { api } from '@/lib/api'
import { useCurrentUser } from '@/lib/auth'

type TechnicianOverview = {
  assigned: number
  in_progress: number
  resolved: number
}

export function TechnicianDashboard() {
  const { data: user } = useCurrentUser()
  const overview = useQuery({
    queryKey: ['overview', 'technician'],
    queryFn: () => api<TechnicianOverview>('/api/overview/technician'),
  })
  const data = overview.data

  return (
    <>
      <PageHeader name={user!.name} description="Your jobs for today and what needs attention next." />
      <StatGrid
        error={overview.error}
        stats={[
          { label: 'New assignments', value: data?.assigned, icon: InboxIcon, hint: 'Not started yet' },
          { label: 'In progress', value: data?.in_progress, icon: TimerIcon, hint: 'Currently working on', tone: 'warning' },
          { label: 'Resolved', value: data?.resolved, icon: CheckCircle2Icon, hint: 'Jobs completed', tone: 'success' },
        ]}
      />

      <div className="mt-6 grid gap-6 lg:grid-cols-[1.4fr_1fr]">
        <Card>
          <CardHeader>
            <CardTitle>My job queue</CardTitle>
            <CardDescription>Service requests assigned to you, most urgent first.</CardDescription>
          </CardHeader>
          <CardContent>
            <EmptyState
              icon={WrenchIcon}
              title="No jobs assigned"
              description="When an admin assigns you a service request, it will show up here."
            />
          </CardContent>
        </Card>
        <Roadmap
          items={[
            { title: 'Job queue', description: 'Accept jobs and update their status.', phase: 2, icon: WrenchIcon },
            { title: 'AI troubleshooting', description: 'Top 3 likely causes and fixes for each job.', phase: 4, icon: LightbulbIcon },
            { title: 'Voice reports', description: 'Dictate a report; fields fill themselves.', phase: 5, icon: FileTextIcon },
          ]}
        />
      </div>
    </>
  )
}
