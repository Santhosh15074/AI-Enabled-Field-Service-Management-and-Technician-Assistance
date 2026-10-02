import { Loader2Icon } from 'lucide-react'

export function FullPageSpinner() {
  return (
    <div className="flex min-h-svh items-center justify-center" role="status">
      <Loader2Icon className="size-6 animate-spin text-muted-foreground" aria-hidden="true" />
      <span className="sr-only">Loading…</span>
    </div>
  )
}
