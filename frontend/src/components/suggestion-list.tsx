import { LightbulbIcon } from 'lucide-react'

import type { Suggestion } from '@/lib/requests'

export function SuggestionList({ suggestions }: { suggestions: Suggestion[] }) {
  if (suggestions.length === 0) {
    return <p className="text-sm text-muted-foreground">Nothing in the knowledge base matches this closely yet.</p>
  }

  return (
    <ul className="space-y-3">
      {suggestions.map((suggestion, index) => (
        <li key={index} className="rounded-lg border border-border/60 bg-muted/30 p-3">
          <div className="flex items-start gap-2">
            <LightbulbIcon className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
            <div className="min-w-0">
              <p className="text-sm font-medium">{suggestion.issue_pattern}</p>
              <p className="mt-1 text-sm text-muted-foreground">{suggestion.suggested_fix}</p>
            </div>
          </div>
        </li>
      ))}
    </ul>
  )
}
