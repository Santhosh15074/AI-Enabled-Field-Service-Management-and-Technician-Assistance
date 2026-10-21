import { Link } from 'react-router-dom'
import { AlertCircleIcon, PlusIcon } from 'lucide-react'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { PLANS, useShops, type ShopSummary } from '@/lib/shops'
import { cn } from '@/lib/utils'

export function ShopsPage() {
  const shops = useShops()

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">Shops</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Every shop on Sollu, with this month's use against its plan.
          </p>
        </div>
        <Button asChild>
          <Link to="/shops/new">
            <PlusIcon aria-hidden="true" />
            New shop
          </Link>
        </Button>
      </div>

      {shops.isError && (
        <Alert variant="destructive">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>{shops.error.message}</AlertDescription>
        </Alert>
      )}

      <Card className="overflow-x-auto p-0">
        <table className="w-full text-sm">
          <thead className="border-b bg-muted/40 text-left text-xs text-muted-foreground">
            <tr>
              <th className="px-4 py-2.5 font-medium">Shop</th>
              <th className="px-4 py-2.5 font-medium">Plan</th>
              <th className="px-4 py-2.5 text-right font-medium">Technicians</th>
              <th className="px-4 py-2.5 text-right font-medium">Reports this month</th>
              <th className="px-4 py-2.5 text-right font-medium">Customers</th>
              <th className="px-4 py-2.5 font-medium">Contact</th>
            </tr>
          </thead>
          <tbody>
            {shops.isPending && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  Loading…
                </td>
              </tr>
            )}
            {shops.data?.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  No shops yet. Create the first one.
                </td>
              </tr>
            )}
            {shops.data?.map((shop) => <ShopRow key={shop.id} shop={shop} />)}
          </tbody>
        </table>
      </Card>
    </div>
  )
}

function ShopRow({ shop }: { shop: ShopSummary }) {
  return (
    <tr className={cn('border-b last:border-0 hover:bg-muted/30', !shop.is_active && 'text-muted-foreground')}>
      <td className="px-4 py-3">
        <Link to={`/shops/${shop.id}`} className="font-medium text-foreground underline-offset-4 hover:underline">
          {shop.name}
        </Link>
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{shop.slug}</span>
          {!shop.is_active && <Badge variant="destructive">Switched off</Badge>}
        </div>
      </td>
      <td className="px-4 py-3">{PLANS[shop.plan].label}</td>
      <td className="px-4 py-3 text-right tabular-nums">
        <Usage used={shop.active_technicians} limit={shop.technician_limit} />
      </td>
      <td className="px-4 py-3 text-right tabular-nums">
        <Usage used={shop.reports_this_month} limit={shop.monthly_report_limit} />
      </td>
      <td className="px-4 py-3 text-right tabular-nums">{shop.customers}</td>
      <td className="px-4 py-3">{shop.contact_phone ?? '—'}</td>
    </tr>
  )
}

/** "used / limit", in red once the limit is reached: the plan promises no overage charges,
 * so a shop that keeps going over gets a call about moving up a plan instead. */
function Usage({ used, limit }: { used: number; limit: number }) {
  return (
    <span className={cn(used >= limit && 'font-medium text-destructive')}>
      {used.toLocaleString('en-IN')} <span className="text-muted-foreground">/ {limit.toLocaleString('en-IN')}</span>
    </span>
  )
}
