import { WrenchIcon } from 'lucide-react'

import { cn } from '@/lib/utils'

export function BrandMark({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        'flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground',
        className,
      )}
    >
      <WrenchIcon className="size-4" aria-hidden="true" />
    </div>
  )
}

export function Brand() {
  return (
    <div className="flex items-center gap-2.5">
      <BrandMark />
      <span className="font-semibold tracking-tight">{'FieldAssist AI'}</span>
    </div>
  )
}
