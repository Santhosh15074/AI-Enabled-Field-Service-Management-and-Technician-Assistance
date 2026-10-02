import type { ReactNode } from 'react'
import { AlertCircleIcon, type LucideIcon } from 'lucide-react'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { cn } from '@/lib/utils'

function greeting(date = new Date()): string {
  const hour = date.getHours()
  if (hour < 12) return 'Good morning'
  if (hour < 17) return 'Good afternoon'
  return 'Good evening'
}

export function PageHeader({ name, description }: { name: string; description: string }) {
  return (
    <div className="mb-8">
      <h1 className="text-2xl font-semibold tracking-tight">
        {greeting()}, {name.split(' ')[0]}
      </h1>
      <p className="mt-1 text-muted-foreground">{description}</p>
    </div>
  )
}

export type Stat = {
  label: string
  value: number | undefined
  icon: LucideIcon
  hint: string
  tone?: 'default' | 'warning' | 'danger' | 'success'
}

const TONES = {
  default: 'bg-primary/10 text-primary',
  success: 'bg-emerald-500/10 text-emerald-600',
  warning: 'bg-amber-500/10 text-amber-600',
  danger: 'bg-red-500/10 text-red-600',
}

export function StatGrid({ stats, error }: { stats: Stat[]; error?: Error | null }) {
  return (
    <>
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>Couldn't load the numbers: {error.message}</AlertDescription>
        </Alert>
      )}
      <div className={cn('grid grid-cols-2 gap-3 sm:gap-4', stats.length === 4 ? 'xl:grid-cols-4' : 'lg:grid-cols-3')}>
        {stats.map((stat) => (
          <StatCard key={stat.label} {...stat} />
        ))}
      </div>
    </>
  )
}

function StatCard({ label, value, icon: Icon, hint, tone = 'default' }: Stat) {
  return (
    <Card className="gap-3">
      <CardHeader className="flex flex-row items-center justify-between">
        <CardDescription className="font-medium text-foreground/80">{label}</CardDescription>
        <div className={cn('flex size-9 items-center justify-center rounded-lg', TONES[tone])}>
          <Icon className="size-4.5" aria-hidden="true" />
        </div>
      </CardHeader>
      <CardContent>
        {value === undefined ? (
          <Skeleton className="h-9 w-16" />
        ) : (
          <p className="text-3xl font-semibold tracking-tight tabular-nums">{value.toLocaleString()}</p>
        )}
        <p className="mt-1 text-xs text-muted-foreground">{hint}</p>
      </CardContent>
    </Card>
  )
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
}: {
  icon: LucideIcon
  title: string
  description: string
  action?: ReactNode
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed px-6 py-14 text-center">
      <div className="flex size-12 items-center justify-center rounded-full bg-muted">
        <Icon className="size-5 text-muted-foreground" aria-hidden="true" />
      </div>
      <h3 className="mt-4 font-medium">{title}</h3>
      <p className="mt-1 max-w-sm text-sm text-muted-foreground">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  )
}

export type RoadmapItem = { title: string; description: string; phase: number; icon: LucideIcon }

export function Roadmap({ items }: { items: RoadmapItem[] }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Coming next</CardTitle>
        <CardDescription>Features being added in upcoming build phases.</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="divide-y">
          {items.map(({ title, description, phase, icon: Icon }) => (
            <li key={title} className="flex items-start gap-3 py-3 first:pt-0 last:pb-0">
              <div className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md bg-muted">
                <Icon className="size-4 text-muted-foreground" aria-hidden="true" />
              </div>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-medium">{title}</p>
                <p className="text-sm text-muted-foreground">{description}</p>
              </div>
              <Badge variant="outline" className="shrink-0 font-normal">
                Phase {phase}
              </Badge>
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
