import { CheckCircle2Icon, ClipboardListIcon, ShieldAlertIcon, TimerIcon, WrenchIcon } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Legend, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

import { EmptyState, PageTitle, StatGrid } from '@/components/dashboard'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useAnalytics, type Analytics, type NamedCount } from '@/lib/analytics'
import { cn } from '@/lib/utils'

/** "45 min", "6.5 h" or "3.2 days" — whichever reads naturally for the size of the number. */
function formatHours(hours: number | null): string {
  if (hours === null) return '—'
  if (hours < 1) return `${Math.max(1, Math.round(hours * 60))} min`
  if (hours < 48) return `${hours.toFixed(1)} h`
  return `${(hours / 24).toFixed(1)} days`
}

function shortDate(iso: string): string {
  // The API's dates are plain UTC days; parse as UTC so the label doesn't shift a day.
  return new Date(`${iso}T00:00:00Z`).toLocaleDateString(undefined, { day: 'numeric', month: 'short', timeZone: 'UTC' })
}

const TOOLTIP_STYLE = {
  borderRadius: 8,
  border: '1px solid var(--border)',
  background: 'var(--popover)',
  color: 'var(--popover-foreground)',
  fontSize: 12,
}

// Same colours as the status, urgency and risk badges, so a level reads the same everywhere.
const BREAKDOWNS: Record<string, { label: string; bar: string }> = {
  open: { label: 'Open', bar: 'bg-amber-500' },
  in_progress: { label: 'In progress', bar: 'bg-primary' },
  resolved: { label: 'Resolved', bar: 'bg-emerald-500' },
  low: { label: 'Low', bar: 'bg-muted-foreground/40' },
  medium: { label: 'Medium', bar: 'bg-amber-500' },
  high: { label: 'High', bar: 'bg-red-500' },
  good: { label: 'Low risk', bar: 'bg-emerald-500' },
  moderate: { label: 'Moderate risk', bar: 'bg-amber-500' },
  critical: { label: 'Critical risk', bar: 'bg-red-500' },
  unscored: { label: 'No reading yet', bar: 'bg-muted-foreground/40' },
}

export function AdminAnalyticsPage() {
  const analytics = useAnalytics()
  const data = analytics.data

  return (
    <>
      <PageTitle title="Analytics" description="Request trends, technician workload and equipment risk." />

      <StatGrid
        error={analytics.error}
        stats={[
          {
            label: `Requests, last ${data?.days ?? 30} days`,
            value: data?.daily.reduce((sum, day) => sum + day.created, 0),
            icon: ClipboardListIcon,
            hint: 'Complaints raised',
          },
          {
            label: `Resolved, last ${data?.days ?? 30} days`,
            value: data?.daily.reduce((sum, day) => sum + day.resolved, 0),
            icon: CheckCircle2Icon,
            hint: 'Marked resolved',
            tone: 'success',
          },
          {
            label: 'Average resolution',
            value: data && formatHours(data.avg_resolution_hours),
            icon: TimerIcon,
            hint: 'From complaint to resolved, all time',
            tone: 'warning',
          },
          {
            label: 'Critical equipment',
            value: data?.equipment_risk.find((item) => item.name === 'critical')?.count,
            icon: ShieldAlertIcon,
            hint: 'Latest prediction is critical',
            tone: 'danger',
          },
        ]}
      />

      {analytics.isPending ? (
        <div className="mt-6 grid gap-6 lg:grid-cols-2">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-72 rounded-xl" />
          ))}
        </div>
      ) : analytics.isError ? null : (
        <Charts data={analytics.data} />
      )}
    </>
  )
}

function Charts({ data }: { data: Analytics }) {
  const daily = data.daily.map((day) => ({ ...day, label: shortDate(day.date) }))

  return (
    <div className="mt-6 grid gap-6 lg:grid-cols-2">
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Requests per day</CardTitle>
          <CardDescription>Complaints raised and resolved over the last {data.days} days (UTC).</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={daily} margin={{ top: 4, right: 4, bottom: 0, left: -20 }}>
                <CartesianGrid vertical={false} stroke="var(--border)" />
                <XAxis dataKey="label" tickLine={false} axisLine={false} fontSize={12} minTickGap={24} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={12} />
                <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'var(--muted)' }} />
                <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: 12 }} />
                <Bar dataKey="created" name="Raised" fill="var(--chart-1)" radius={[3, 3, 0, 0]} />
                <Bar dataKey="resolved" name="Resolved" fill="var(--chart-2)" radius={[3, 3, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Requests by status</CardTitle>
          <CardDescription>Every request, all time.</CardDescription>
        </CardHeader>
        <CardContent>
          <Breakdown items={data.by_status} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Requests by urgency</CardTitle>
          <CardDescription>As predicted by the complaint classifier.</CardDescription>
        </CardHeader>
        <CardContent>
          <Breakdown items={data.by_urgency} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Requests by category</CardTitle>
          <CardDescription>Most common complaint types first.</CardDescription>
        </CardHeader>
        <CardContent>
          {data.by_category.length === 0 ? (
            <EmptyState icon={ClipboardListIcon} title="No requests yet" description="Categories appear once customers raise complaints." />
          ) : (
            <div style={{ height: Math.max(120, data.by_category.length * 36) }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data.by_category} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 0 }}>
                  <XAxis type="number" allowDecimals={false} hide />
                  <YAxis type="category" dataKey="name" width={140} tickLine={false} axisLine={false} fontSize={12} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} cursor={{ fill: 'var(--muted)' }} />
                  <Bar dataKey="count" name="Requests" fill="var(--chart-1)" radius={[0, 3, 3, 0]} barSize={18} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Equipment risk</CardTitle>
          <CardDescription>Each item counted once, by its latest failure prediction.</CardDescription>
        </CardHeader>
        <CardContent>
          <Breakdown items={data.equipment_risk} />
        </CardContent>
      </Card>

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Technician workload</CardTitle>
          <CardDescription>Jobs in hand, jobs completed and how long they took, busiest first.</CardDescription>
        </CardHeader>
        <CardContent>
          <Workload technicians={data.technicians} />
        </CardContent>
      </Card>
    </div>
  )
}

/** Labelled proportion bars — easier to compare a handful of levels than a pie chart. */
function Breakdown({ items }: { items: NamedCount[] }) {
  const total = items.reduce((sum, item) => sum + item.count, 0)

  return (
    <ul className="space-y-3">
      {items.map((item) => {
        const style = BREAKDOWNS[item.name] ?? { label: item.name, bar: 'bg-primary' }
        const share = total ? item.count / total : 0
        return (
          <li key={item.name}>
            <div className="flex items-baseline justify-between gap-2 text-sm">
              <span>{style.label}</span>
              <span className="tabular-nums text-muted-foreground">
                {item.count.toLocaleString()}
                {total > 0 && <span className="ml-1.5 text-xs">({Math.round(share * 100)}%)</span>}
              </span>
            </div>
            <div className="mt-1.5 h-2 overflow-hidden rounded-full bg-muted">
              <div className={cn('h-full rounded-full', style.bar)} style={{ width: `${share * 100}%` }} />
            </div>
          </li>
        )
      })}
    </ul>
  )
}

function Workload({ technicians }: { technicians: Analytics['technicians'] }) {
  if (technicians.length === 0) {
    return (
      <EmptyState icon={WrenchIcon} title="No technicians yet" description="Create technician accounts on the Users page." />
    )
  }
  const busiest = Math.max(1, ...technicians.map((t) => t.active + t.resolved))

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b text-left text-xs text-muted-foreground">
            <th className="pb-2 font-medium">Technician</th>
            <th className="pb-2 text-right font-medium">In hand</th>
            <th className="pb-2 text-right font-medium">Resolved</th>
            <th className="pb-2 text-right font-medium">Avg. resolution</th>
            <th className="hidden w-1/3 pb-2 pl-6 font-medium sm:table-cell">
              <span className="sr-only">Share of jobs</span>
            </th>
          </tr>
        </thead>
        <tbody className="divide-y">
          {technicians.map((t) => (
            <tr key={t.id}>
              <td className="py-2.5 font-medium">{t.name}</td>
              <td className="py-2.5 text-right tabular-nums">{t.active}</td>
              <td className="py-2.5 text-right tabular-nums">{t.resolved}</td>
              <td className="py-2.5 text-right tabular-nums text-muted-foreground">{formatHours(t.avg_resolution_hours)}</td>
              <td className="hidden py-2.5 pl-6 sm:table-cell">
                <div className="flex h-2 overflow-hidden rounded-full bg-muted" aria-hidden="true">
                  <div className="bg-primary" style={{ width: `${(t.active / busiest) * 100}%` }} />
                  <div className="bg-emerald-500" style={{ width: `${(t.resolved / busiest) * 100}%` }} />
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <p className="mt-3 flex items-center gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-primary" /> In hand
        </span>
        <span className="flex items-center gap-1.5">
          <span className="size-2 rounded-full bg-emerald-500" /> Resolved
        </span>
      </p>
    </div>
  )
}
