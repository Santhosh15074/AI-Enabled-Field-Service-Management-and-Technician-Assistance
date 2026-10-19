import { useState } from 'react'
import { AlertCircleIcon, ActivityIcon, FileTextIcon, LightbulbIcon, PlusIcon, WrenchIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'

import { EmptyState, PageTitle } from '@/components/dashboard'
import { RequestStatusBadge } from '@/components/request-status-badge'
import { RiskBadge } from '@/components/risk-badge'
import { SuggestionList } from '@/components/suggestion-list'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { UrgencyBadge } from '@/components/urgency-badge'
import {
  STATUS_ORDER,
  useAssignedRequests,
  useRequestSuggestions,
  useUpdateRequest,
  type RequestStatus,
  type ServiceRequest,
} from '@/lib/requests'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

function JobCard({
  request,
  onAdvance,
  advancing,
}: {
  request: ServiceRequest
  onAdvance: (id: number, next: RequestStatus) => void
  advancing: boolean
}) {
  const [showSuggestions, setShowSuggestions] = useState(false)
  const suggestions = useRequestSuggestions(request.id, showSuggestions)
  const nextStatus = STATUS_ORDER[STATUS_ORDER.indexOf(request.status) + 1]

  return (
    <Card>
      <CardContent className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-muted-foreground">#{request.id}</span>
            <RequestStatusBadge status={request.status} />
            <UrgencyBadge urgency={request.urgency} />
            {request.equipment && (
              <>
                <span className="text-sm text-muted-foreground">· {request.equipment.name}</span>
                <RiskBadge riskLevel={request.equipment.risk_level} />
              </>
            )}
          </div>
          <p className="mt-1.5 text-sm">{request.description}</p>
          <p className="mt-1.5 text-xs text-muted-foreground">
            {request.customer.name} · {request.customer.phone} · {formatDate(request.created_at)}
          </p>

          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="-ml-2.5 mt-2 text-muted-foreground"
            onClick={() => setShowSuggestions((shown) => !shown)}
          >
            <LightbulbIcon aria-hidden="true" />
            {showSuggestions ? 'Hide suggested fix' : 'Suggested fix'}
          </Button>
          {showSuggestions && (
            <div className="mt-1.5">
              {suggestions.isPending ? (
                <p className="text-sm text-muted-foreground">Looking for a match…</p>
              ) : suggestions.isError ? (
                <p className="text-sm text-destructive">Couldn't load suggestions.</p>
              ) : (
                <SuggestionList suggestions={suggestions.data} />
              )}
            </div>
          )}
        </div>
        <div className="flex shrink-0 flex-col gap-2 sm:items-end">
          {nextStatus && (
            <Button
              variant={nextStatus === 'resolved' ? 'default' : 'outline'}
              disabled={advancing}
              onClick={() => onAdvance(request.id, nextStatus)}
            >
              Mark {nextStatus === 'resolved' ? 'resolved' : 'in progress'}
            </Button>
          )}
          {request.equipment && (
            <Button variant="outline" size="sm" asChild>
              <Link to={`/technician/equipment/${request.equipment.id}/readings`}>
                <ActivityIcon aria-hidden="true" />
                Record reading
              </Link>
            </Button>
          )}
          {request.status === 'resolved' && (
            <Button variant="outline" size="sm" asChild>
              <Link to={`/technician/jobs/${request.id}/report`}>
                <FileTextIcon aria-hidden="true" />
                Report
              </Link>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

export function TechnicianJobsPage() {
  const requests = useAssignedRequests()
  const update = useUpdateRequest()

  function advance(id: number, next: RequestStatus) {
    update.mutate({ id, status: next }, { onError: (error) => toast.error(error.message) })
  }

  return (
    <>
      <PageTitle
        title="My jobs"
        description="Service requests assigned to you, most urgent first."
        action={
          <Button asChild>
            <Link to="/technician/jobs/new">
              <PlusIcon aria-hidden="true" />
              New request
            </Link>
          </Button>
        }
      />

      {requests.isPending ? null : requests.isError ? (
        <Alert variant="destructive">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>Couldn't load your jobs: {requests.error.message}</AlertDescription>
        </Alert>
      ) : requests.data.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={WrenchIcon}
              title="No jobs assigned"
              description="When an admin assigns you a service request, it will show up here."
            />
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {requests.data.map((request) => (
            <JobCard key={request.id} request={request} onAdvance={advance} advancing={update.isPending} />
          ))}
        </div>
      )}
    </>
  )
}
