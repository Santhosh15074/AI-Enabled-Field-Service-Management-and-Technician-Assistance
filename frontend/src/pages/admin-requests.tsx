import { useState } from 'react'
import { AlertCircleIcon, ClipboardListIcon, FileTextIcon } from 'lucide-react'
import { toast } from 'sonner'

import { EmptyState, PageTitle } from '@/components/dashboard'
import { ReportSummary } from '@/components/report-summary'
import { RequestStatusBadge } from '@/components/request-status-badge'
import { RiskBadge } from '@/components/risk-badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { NativeSelect } from '@/components/ui/native-select'
import { UrgencyBadge } from '@/components/urgency-badge'
import { Skeleton } from '@/components/ui/skeleton'
import { useReport } from '@/lib/reports'
import {
  STATUS_LABEL,
  STATUS_ORDER,
  useAllRequests,
  useTechnicians,
  useUpdateRequest,
  type RequestStatus,
  type ServiceRequest,
  type TechnicianSummary,
} from '@/lib/requests'

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

function RequestRow({
  request,
  technicians,
  onAssign,
  onChangeStatus,
  updating,
}: {
  request: ServiceRequest
  technicians: TechnicianSummary[] | undefined
  onAssign: (id: number, technicianId: string) => void
  onChangeStatus: (id: number, status: string) => void
  updating: boolean
}) {
  const [showReport, setShowReport] = useState(false)
  const report = useReport(request.id, showReport)
  // A request can only move forward, so earlier statuses aren't offered once passed.
  const availableStatuses = STATUS_ORDER.filter((status) => STATUS_ORDER.indexOf(status) >= STATUS_ORDER.indexOf(request.status))

  return (
    <Card>
      <CardContent className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-2">
            <span className="text-sm font-medium text-muted-foreground">#{request.id}</span>
            <RequestStatusBadge status={request.status} />
            <UrgencyBadge urgency={request.urgency} />
            {request.category && <span className="text-sm text-muted-foreground">· {request.category.category_name}</span>}
            {request.equipment && (
              <>
                <span className="text-sm text-muted-foreground">· {request.equipment.name}</span>
                <RiskBadge riskLevel={request.equipment.risk_level} />
              </>
            )}
            <span className="ml-auto text-xs text-muted-foreground lg:ml-0">{formatDate(request.created_at)}</span>
          </div>
          <p className="mt-1.5 text-sm">{request.description}</p>
          <p className="mt-1.5 text-xs text-muted-foreground">
            {request.customer.name} · {request.customer.phone}
          </p>
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

        <div className="grid shrink-0 grid-cols-2 gap-2 lg:w-72">
          <NativeSelect
            aria-label={`Technician for request ${request.id}`}
            value={request.technician?.id ?? ''}
            disabled={!technicians || updating}
            onChange={(e) => onAssign(request.id, e.target.value)}
          >
            <option value="" disabled>
              {request.technician ? request.technician.name : 'Assign technician'}
            </option>
            {technicians?.map((technician) => (
              <option key={technician.id} value={technician.id}>
                {technician.name}
              </option>
            ))}
          </NativeSelect>
          <NativeSelect
            aria-label={`Status for request ${request.id}`}
            value={request.status}
            disabled={updating}
            onChange={(e) => onChangeStatus(request.id, e.target.value)}
          >
            {availableStatuses.map((status) => (
              <option key={status} value={status}>
                {STATUS_LABEL[status]}
              </option>
            ))}
          </NativeSelect>
        </div>
      </CardContent>
    </Card>
  )
}

export function AdminRequestsPage() {
  const requests = useAllRequests()
  const technicians = useTechnicians()
  const update = useUpdateRequest()

  function assign(id: number, technicianId: string) {
    if (!technicianId) return
    update.mutate({ id, technician_id: Number(technicianId) }, { onError: (error) => toast.error(error.message) })
  }

  function changeStatus(id: number, status: string) {
    update.mutate({ id, status: status as RequestStatus }, { onError: (error) => toast.error(error.message) })
  }

  return (
    <>
      <PageTitle title="Service requests" description="Every complaint, across every customer." />

      {requests.isPending ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      ) : requests.isError ? (
        <Alert variant="destructive">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>Couldn't load requests: {requests.error.message}</AlertDescription>
        </Alert>
      ) : requests.data.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={ClipboardListIcon}
              title="No service requests yet"
              description="Requests will appear here as soon as customers start submitting complaints."
            />
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-3">
          {requests.data.map((request) => (
            <RequestRow
              key={request.id}
              request={request}
              technicians={technicians.data}
              onAssign={assign}
              onChangeStatus={changeStatus}
              updating={update.isPending}
            />
          ))}
        </div>
      )}
    </>
  )
}
