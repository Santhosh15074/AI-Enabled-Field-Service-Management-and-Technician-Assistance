import { ShieldAlertIcon, SparklesIcon } from 'lucide-react'

import type { ServiceRequest } from '@/lib/requests'

/** Why this request got its urgency (and its category, if AI picked it) — see app.ml.triage.
 * Nothing for requests the trained classifier triaged, which can't say why. */
export function TriageNote({ request }: { request: ServiceRequest }) {
  const aiCategory = request.category_source === 'ai' && request.category
  if (!request.urgency_reason && !aiCategory) return null

  const Icon = request.urgency_source === 'safety_rule' ? ShieldAlertIcon : SparklesIcon
  return (
    <p className="mt-1.5 flex items-start gap-1.5 text-xs text-muted-foreground">
      <Icon
        className={
          request.urgency_source === 'safety_rule'
            ? 'mt-px size-3.5 shrink-0 text-red-600 dark:text-red-400'
            : 'mt-px size-3.5 shrink-0 text-amber-600 dark:text-amber-400'
        }
        aria-hidden="true"
      />
      <span>
        {request.urgency_reason}
        {aiCategory && (
          <>
            {request.urgency_reason ? ' · ' : ''}
            Category {request.category!.category_name} picked by AI.
          </>
        )}
      </span>
    </p>
  )
}
