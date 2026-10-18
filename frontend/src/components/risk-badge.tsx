import { Badge } from '@/components/ui/badge'
import type { RiskLevel } from '@/lib/requests'
import { cn } from '@/lib/utils'

const LABEL: Record<RiskLevel, string> = {
  good: 'Low risk',
  moderate: 'Moderate risk',
  critical: 'Critical risk',
}

const TONE: Record<RiskLevel, string> = {
  good: 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-400',
  moderate: 'bg-amber-500/10 text-amber-700 dark:text-amber-400',
  critical: 'bg-red-500/10 text-red-700 dark:text-red-400',
}

export function RiskBadge({ riskLevel }: { riskLevel: RiskLevel | null }) {
  if (riskLevel === null) return <Badge className="bg-muted font-normal text-muted-foreground">No reading yet</Badge>
  return <Badge className={cn('font-normal', TONE[riskLevel])}>{LABEL[riskLevel]}</Badge>
}
