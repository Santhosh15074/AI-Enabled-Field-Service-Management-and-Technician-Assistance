import { RequestStatusBadge } from '@/components/request-status-badge'
import { UrgencyBadge } from '@/components/urgency-badge'
import type { ServiceRequest } from '@/lib/requests'

function shortDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short' })
}

/** One line per request in a dashboard list, ending with the date it was raised. The full card
 * lives on each role's requests page. */
export function RequestRow({ request, meta, showUrgency = false }: { request: ServiceRequest; meta: string; showUrgency?: boolean }) {
  return (
    <div className="flex items-start justify-between gap-3">
      <div className="min-w-0">
        <p className="truncate text-sm">
          <span className="text-muted-foreground">#{request.id}</span> {request.description}
        </p>
        <p className="mt-0.5 truncate text-xs text-muted-foreground">{meta} · {shortDate(request.created_at)}</p>
      </div>
      <div className="flex shrink-0 flex-wrap justify-end gap-1.5">
        {showUrgency && request.status !== 'resolved' && <UrgencyBadge urgency={request.urgency} />}
        <RequestStatusBadge status={request.status} />
      </div>
    </div>
  )
}
