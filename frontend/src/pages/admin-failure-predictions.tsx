import { AlertCircleIcon, ShieldAlertIcon } from 'lucide-react'

import { EmptyState, PageTitle } from '@/components/dashboard'
import { RiskBadge } from '@/components/risk-badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { useAllEquipment } from '@/lib/fleet'

function formatDate(iso: string | null): string {
  if (!iso) return 'Never'
  return new Date(iso).toLocaleDateString(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
}

export function AdminFailurePredictionsPage() {
  const equipment = useAllEquipment()

  return (
    <>
      <PageTitle title="Failure predictions" description="Every customer's equipment, worst risk first." />

      {equipment.isPending ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
      ) : equipment.isError ? (
        <Alert variant="destructive">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>Couldn't load equipment: {equipment.error.message}</AlertDescription>
        </Alert>
      ) : equipment.data.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={ShieldAlertIcon}
              title="No equipment registered yet"
              description="Risk scores will appear here once customers register equipment and technicians record readings."
            />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="divide-y p-0">
            {equipment.data.map((item) => (
              <div key={item.id} className="flex flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-5">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="truncate text-sm font-medium">{item.name}</p>
                    <span className="text-sm text-muted-foreground">· {item.type}</span>
                  </div>
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">
                    {item.customer.name} · {item.customer.phone} · Last reading: {formatDate(item.last_service_date)}
                  </p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <RiskBadge riskLevel={item.risk_level} />
                  {item.risk_score != null && (
                    <span className="text-xs tabular-nums text-muted-foreground">{Math.round(item.risk_score * 100)}%</span>
                  )}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </>
  )
}
