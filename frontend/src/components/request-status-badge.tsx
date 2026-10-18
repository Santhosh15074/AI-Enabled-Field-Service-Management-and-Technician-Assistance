import { Badge } from '@/components/ui/badge'
import { STATUS_LABEL, type RequestStatus } from '@/lib/requests'
import { cn } from '@/lib/utils'

const TONE: Record<RequestStatus, string> = {
  open: 'bg-amber-500/10 text-amber-700 dark:text-amber-400',
  in_progress: 'bg-primary/10 text-primary',
  resolved: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
}

export function RequestStatusBadge({ status }: { status: RequestStatus }) {
  return <Badge className={cn('font-normal', TONE[status])}>{STATUS_LABEL[status]}</Badge>
}
