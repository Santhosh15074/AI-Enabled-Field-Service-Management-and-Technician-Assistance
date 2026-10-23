import { Link } from 'react-router-dom'
import { BookPlusIcon, LightbulbIcon, SparklesIcon } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useCurrentUser } from '@/lib/auth'
import type { Suggestion } from '@/lib/requests'

export function SuggestionList({ suggestions }: { suggestions: Suggestion[] }) {
  const { data: user } = useCurrentUser()

  if (suggestions.length === 0) {
    return <p className="text-sm text-muted-foreground">Nothing in the knowledge base matches this closely yet.</p>
  }

  return (
    <ul className="space-y-3">
      {suggestions.map((suggestion, index) =>
        suggestion.source === 'ai' ? (
          // Generated because nothing in the knowledge base matched (app.ml.ai_fallback). A customer's
          // draft only holds steps that are safe without opening the unit.
          <li key={index} className="rounded-lg border border-dashed border-amber-500/50 bg-amber-500/5 p-3">
            <div className="flex items-start gap-2">
              <SparklesIcon className="mt-0.5 size-4 shrink-0 text-amber-600 dark:text-amber-400" aria-hidden="true" />
              <div className="min-w-0 flex-1">
                {user?.role === 'customer' ? (
                  <>
                    <p className="text-sm font-medium">Things you can safely try</p>
                    <p className="text-xs text-muted-foreground">
                      Suggested by AI, not yet checked by the shop. Don't open the unit. If these don't help, submit the
                      request below.
                    </p>
                  </>
                ) : (
                  <>
                    <p className="text-sm font-medium">AI draft, not checked</p>
                    <p className="text-xs text-muted-foreground">
                      Nothing in the knowledge base matched. Use your judgement before following these steps.
                    </p>
                  </>
                )}
                <p className="mt-2 whitespace-pre-wrap text-sm">{suggestion.suggested_fix}</p>
                {user?.role === 'admin' && (
                  <Button variant="outline" size="sm" className="mt-3" asChild>
                    <Link
                      to="/admin/knowledge-base"
                      state={{ draft: { issue_pattern: suggestion.issue_pattern, suggested_fix: suggestion.suggested_fix } }}
                    >
                      <BookPlusIcon aria-hidden="true" />
                      Check and save to knowledge base
                    </Link>
                  </Button>
                )}
              </div>
            </div>
          </li>
        ) : (
          <li key={index} className="rounded-lg border border-border/60 bg-muted/30 p-3">
            <div className="flex items-start gap-2">
              <LightbulbIcon className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
              <div className="min-w-0">
                <p className="text-sm font-medium">{suggestion.issue_pattern}</p>
                <p className="mt-1 text-sm text-muted-foreground">{suggestion.suggested_fix}</p>
              </div>
            </div>
          </li>
        ),
      )}
    </ul>
  )
}
