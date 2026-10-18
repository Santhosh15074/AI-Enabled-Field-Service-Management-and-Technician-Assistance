import { useState } from 'react'
import { AlertCircleIcon, ClipboardListIcon, FileTextIcon, MessageSquarePlusIcon, WrenchIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

import { EmptyState, PageTitle } from '@/components/dashboard'
import { RequestStatusBadge } from '@/components/request-status-badge'
import { ReportSummary } from '@/components/report-summary'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useMyRequests, type ServiceRequest } from '@/lib/requests'
import { useReport } from '@/lib/reports'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

function RequestCard({ request }: { request: ServiceRequest }) {
  const [showReport, setShowReport] = useState(false)
  const report = useReport(request.id, showReport)

  return (
    <Card>
      <CardContent className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-muted-foreground">#{request.id}</span>
            <RequestStatusBadge status={request.status} />
            {request.category && <span className="text-sm text-muted-foreground">· {request.category.category_name}</span>}
            {request.equipment && <span className="text-sm text-muted-foreground">· {request.equipment.name}</span>}
          </div>
          <p className="mt-1.5 text-sm">{request.description}</p>
          {request.technician && (
            <p className="mt-1.5 flex items-center gap-1.5 text-xs text-muted-foreground">
              <WrenchIcon className="size-3.5" aria-hidden="true" />
              {request.technician.name}
            </p>
          )}
          {request.status === 'resolved' && (
            <>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                className="-ml-2.5 mt-1.5 text-muted-foreground"
                onClick={() => setShowReport((shown) => !shown)}
              >
                <FileTextIcon aria-hidden="true" />
                {showReport ? 'Hide service report' : 'Service report'}
              </Button>
              {showReport && (
                <div className="mt-1.5">
                  {report.isPending ? (
                    <p className="text-sm text-muted-foreground">Loading…</p>
                  ) : report.data ? (
                    <ReportSummary report={report.data} />
                  ) : (
                    <p className="text-sm text-muted-foreground">No report has been written for this yet.</p>
                  )}
                </div>
              )}
            </>
          )}
        </div>
        <span className="shrink-0 text-xs text-muted-foreground">{formatDate(request.created_at)}</span>
      </CardContent>
    </Card>
  )
}

export function MyRequestsPage() {
  const requests = useMyRequests()

  return (
    <>
      <PageTitle
        title="My requests"
        description="Every complaint you've raised and where it stands."
        action={
          <Button asChild>
            <Link to="/portal/requests/new">
              <MessageSquarePlusIcon aria-hidden="true" />
              New complaint
            </Link>
          </Button>
        }
      />

      {requests.isPending ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-24 rounded-xl" />
          ))}
        </div>
      ) : requests.isError ? (
        <Alert variant="destructive">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>Couldn't load your requests: {requests.error.message}</AlertDescription>
        </Alert>
      ) : requests.data.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={ClipboardListIcon}
              title="No requests yet"
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
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {requests.data.map((request) => (
            <RequestCard key={request.id} request={request} />
          ))}
        </div>
      )}
    </>
  )
}
