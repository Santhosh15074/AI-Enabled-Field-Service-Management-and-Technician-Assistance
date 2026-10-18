import type { ServiceReport } from '@/lib/reports'

export function ReportSummary({ report }: { report: ServiceReport }) {
  return (
    <dl className="space-y-2 rounded-lg border border-border/60 bg-muted/30 p-3 text-sm">
      {report.issue && (
        <div>
          <dt className="font-medium">Issue found</dt>
          <dd className="text-muted-foreground">{report.issue}</dd>
        </div>
      )}
      {report.action_taken && (
        <div>
          <dt className="font-medium">Action taken</dt>
          <dd className="text-muted-foreground">{report.action_taken}</dd>
        </div>
      )}
      <div className="flex flex-wrap gap-x-6 gap-y-1">
        {report.parts_used && (
          <div>
            <dt className="inline font-medium">Parts used: </dt>
            <dd className="inline text-muted-foreground">{report.parts_used}</dd>
          </div>
        )}
        {report.time_spent_minutes != null && (
          <div>
            <dt className="inline font-medium">Time spent: </dt>
            <dd className="inline text-muted-foreground">{report.time_spent_minutes} min</dd>
          </div>
        )}
      </div>
    </dl>
  )
}
