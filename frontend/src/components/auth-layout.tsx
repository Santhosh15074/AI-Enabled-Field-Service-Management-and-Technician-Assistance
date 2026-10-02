import type { ReactNode } from 'react'
import { BrainCircuitIcon, ClipboardCheckIcon, ShieldAlertIcon, type LucideIcon } from 'lucide-react'

import { Brand } from '@/components/brand'

const HIGHLIGHTS: { icon: LucideIcon; title: string; text: string }[] = [
  {
    icon: BrainCircuitIcon,
    title: 'Instant complaint triage',
    text: 'Every complaint is classified by type and urgency the moment it arrives.',
  },
  {
    icon: ClipboardCheckIcon,
    title: 'Guided troubleshooting',
    text: 'Technicians get ranked causes and fixes from a shared knowledge base.',
  },
  {
    icon: ShieldAlertIcon,
    title: 'Failures caught early',
    text: 'At-risk equipment is flagged for a preventive visit before it breaks.',
  },
]

export function AuthLayout({ title, description, children }: { title: string; description: ReactNode; children: ReactNode }) {
  return (
    <div className="grid min-h-svh lg:grid-cols-[1fr_1.1fr]">
      <aside className="relative hidden overflow-hidden bg-primary p-10 text-primary-foreground lg:flex lg:flex-col">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,oklch(1_0_0/0.18),transparent_45%),radial-gradient(circle_at_85%_90%,oklch(0.35_0.15_262/0.6),transparent_55%)]"
        />
        <div className="relative flex items-center gap-2.5 font-semibold tracking-tight">
          <div className="flex size-8 items-center justify-center rounded-lg bg-white/15 ring-1 ring-white/25">
            <BrainCircuitIcon className="size-4" aria-hidden="true" />
          </div>
          FieldAssist AI
        </div>

        <div className="relative mt-auto max-w-md">
          <h2 className="text-3xl font-semibold leading-tight tracking-tight">
            Field service that fixes problems before customers notice them.
          </h2>
          <ul className="mt-10 space-y-6">
            {HIGHLIGHTS.map(({ icon: Icon, title, text }) => (
              <li key={title} className="flex gap-4">
                <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-white/10 ring-1 ring-white/20">
                  <Icon className="size-5" aria-hidden="true" />
                </div>
                <div>
                  <p className="font-medium">{title}</p>
                  <p className="text-sm text-primary-foreground/75">{text}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
        <p className="relative mt-16 text-xs text-primary-foreground/60">
          © {new Date().getFullYear()} FieldAssist AI
        </p>
      </aside>

      <main className="flex flex-col p-6 sm:p-10">
        <div className="lg:hidden">
          <Brand />
        </div>
        <div className="mx-auto flex w-full max-w-sm flex-1 flex-col justify-center py-10">
          <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">{description}</p>
          <div className="mt-8">{children}</div>
        </div>
      </main>
    </div>
  )
}
