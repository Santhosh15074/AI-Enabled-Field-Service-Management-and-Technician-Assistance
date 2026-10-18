import { Badge } from '@/components/ui/badge'
import { cn } from '@/lib/utils'

type Urgency = 'low' | 'medium' | 'high'

const LABEL: Record<Urgency, string> = {
  low: 'Low urgency',
  medium: 'Medium urgency',
  high: 'High urgency',
}

const TONE: Record<Urgency, string> = {
  low: 'bg-muted text-muted-foreground',
  medium: 'bg-amber-500/10 text-amber-700 dark:text-amber-400',
  high: 'bg-red-500/10 text-red-700 dark:text-red-400',
}

export function UrgencyBadge({ urgency }: { urgency: Urgency }) {
  return <Badge className={cn('font-normal', TONE[urgency])}>{LABEL[urgency]}</Badge>
}
