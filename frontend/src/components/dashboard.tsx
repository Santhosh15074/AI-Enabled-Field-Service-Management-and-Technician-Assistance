import type { ReactNode } from 'react'
import type { UseQueryResult } from '@tanstack/react-query'
import { AlertCircleIcon, ArrowRightIcon, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardAction, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
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
      <h1 className="text-[1.75rem] font-semibold tracking-tight sm:text-3xl">
        {greeting()}, {name.split(' ')[0]}
      </h1>
      <p className="mt-1.5 text-muted-foreground">{description}</p>
    </div>
  )
}

/** The plain (non-greeting) heading used by sub-pages reached from a dashboard, e.g. "My equipment". */
export function PageTitle({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <div className="mb-8 flex items-start justify-between gap-4">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        <p className="mt-1.5 text-muted-foreground">{description}</p>
      </div>
      {action}
    </div>
  )
}

export type Stat = {
  label: string
  /** A count, or preformatted text such as a duration; undefined while loading. */
  value: number | string | undefined
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

// One elevated strip with internal dividers, not N identical boxed cards — the same
// numbers read as a single coherent summary instead of a row of repeated widgets.
export function StatGrid({ stats, error }: { stats: Stat[]; error?: Error | null }) {
  return (
    <>
      {error && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>Couldn't load the numbers: {error.message}</AlertDescription>
        </Alert>
      )}
      <div
        className={cn(
          'grid grid-cols-2 divide-x divide-y divide-border/60 overflow-hidden rounded-xl border border-border/60 bg-card shadow-[0_1px_2px_hsl(var(--shadow-color)/0.06),0_4px_10px_-4px_hsl(var(--shadow-color)/0.1)] sm:divide-y-0',
          stats.length === 4 ? 'sm:grid-cols-4' : 'sm:grid-cols-3',
        )}
      >
        {stats.map((stat) => (
          <StatCell key={stat.label} {...stat} />
        ))}
      </div>
    </>
  )
}

function StatCell({ label, value, icon: Icon, hint, tone = 'default' }: Stat) {
  return (
    <div className="min-w-0 p-4 sm:p-5">
      <div className="flex items-center justify-between gap-2">
        <p className="truncate text-sm font-medium text-foreground/80">{label}</p>
        <div className={cn('flex size-7 shrink-0 items-center justify-center rounded-md', TONES[tone])}>
          <Icon className="size-3.5" aria-hidden="true" />
        </div>
      </div>
      {value === undefined ? (
        <Skeleton className="mt-2.5 h-8 w-14" />
      ) : (
        <p className="mt-1.5 text-2xl font-semibold tracking-tight tabular-nums">
          {typeof value === 'number' ? value.toLocaleString() : value}
        </p>
      )}
      <p className="mt-1 truncate text-xs text-muted-foreground">{hint}</p>
    </div>
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

/** A dashboard card listing the first few items of a query, with a link to the full page. */
export function ListCard<T extends { id: number }>({
  title,
  description,
  viewAll,
  query,
  filter = () => true,
  limit = 5,
  empty,
  renderItem,
}: {
  title: string
  description: string
  viewAll: { to: string; label: string }
  query: UseQueryResult<T[]>
  /** Only list items that pass; "View all" still shows whenever the query has any. */
  filter?: (item: T) => boolean
  limit?: number
  empty: ReactNode
  renderItem: (item: T) => ReactNode
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
        {query.data && query.data.length > 0 && (
          <CardAction>
            <Button asChild variant="ghost" size="sm" className="-mr-2 text-muted-foreground">
              <Link to={viewAll.to}>
                {viewAll.label}
                <ArrowRightIcon aria-hidden="true" />
              </Link>
            </Button>
          </CardAction>
        )}
      </CardHeader>
      <CardContent>
        {query.isPending ? (
          <div className="space-y-3">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-12 rounded-lg" />
            ))}
          </div>
        ) : query.isError ? (
          <Alert variant="destructive">
            <AlertCircleIcon aria-hidden="true" />
            <AlertDescription>Couldn't load this: {query.error.message}</AlertDescription>
          </Alert>
        ) : !query.data.some(filter) ? (
          empty
        ) : (
          <ul className="divide-y">
            {query.data.filter(filter).slice(0, limit).map((item) => (
              <li key={item.id} className="py-3 first:pt-0 last:pb-0">
                {renderItem(item)}
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}
