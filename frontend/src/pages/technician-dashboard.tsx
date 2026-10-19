import { useQuery } from '@tanstack/react-query'
import { CheckCircle2Icon, InboxIcon, TimerIcon, WrenchIcon } from 'lucide-react'

import { EmptyState, ListCard, PageHeader, StatGrid } from '@/components/dashboard'
import { RequestRow } from '@/components/request-row'
import { api } from '@/lib/api'
import { useCurrentUser } from '@/lib/auth'
import { useAssignedRequests, type ServiceRequest } from '@/lib/requests'

function jobMeta(job: ServiceRequest): string {
  return [job.customer.name, job.equipment?.name, job.category?.category_name].filter(Boolean).join(' · ')
}

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
  const jobs = useAssignedRequests()

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
        <ListCard
          title="My job queue"
          description="Jobs still to finish, newest first."
          viewAll={{ to: '/technician/jobs', label: 'All jobs' }}
          query={jobs}
          filter={(job) => job.status !== 'resolved'}
          empty={
            <EmptyState
              icon={WrenchIcon}
              title="No jobs waiting"
              description="When an admin assigns you a service request, it will show up here."
            />
          }
          renderItem={(job) => <RequestRow request={job} showUrgency meta={jobMeta(job)} />}
        />
        <ListCard
          title="Completed jobs"
          description="Jobs you've completed, newest first."
          viewAll={{ to: '/technician/jobs', label: 'All jobs' }}
          query={jobs}
          filter={(job) => job.status === 'resolved'}
          empty={
            <EmptyState
              icon={CheckCircle2Icon}
              title="Nothing resolved yet"
              description="Jobs you mark resolved will be listed here."
            />
          }
          renderItem={(job) => <RequestRow request={job} meta={jobMeta(job)} />}
        />
      </div>
    </>
  )
}
