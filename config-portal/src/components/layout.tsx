import { Link, Outlet, useNavigate } from 'react-router-dom'
import { LogOutIcon, SlidersHorizontalIcon } from 'lucide-react'
import { toast } from 'sonner'

import { Button } from '@/components/ui/button'
import { useLogout, useOperator } from '@/lib/auth'
import { cn } from '@/lib/utils'

export function Brand({ className }: { className?: string }) {
  return (
    <div className={cn('flex items-center gap-2.5', className)}>
      <div className="flex size-8 shrink-0 items-center justify-center rounded-lg bg-primary text-primary-foreground">
        <SlidersHorizontalIcon className="size-4" aria-hidden="true" />
      </div>
      <span className="font-semibold tracking-tight">
        Sollu <span className="font-normal text-muted-foreground">config</span>
      </span>
    </div>
  )
}

export function Layout() {
  const { data: operator } = useOperator()
  const logout = useLogout()
  const navigate = useNavigate()

  function handleLogout() {
    logout.mutate(undefined, {
      onSuccess: () => navigate('/login', { replace: true }),
      onError: (error) => toast.error(error.message),
    })
  }

  return (
    <div className="min-h-svh">
      <header className="sticky top-0 z-10 border-b bg-background/80 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center gap-4 px-4 sm:px-6">
          <Link to="/" aria-label="All shops">
            <Brand />
          </Link>
          <div className="ml-auto flex items-center gap-3">
            <span className="hidden text-sm text-muted-foreground sm:inline">{operator?.email}</span>
            <Button variant="ghost" size="sm" onClick={handleLogout} disabled={logout.isPending}>
              <LogOutIcon aria-hidden="true" />
              Log out
            </Button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl p-4 sm:p-6 lg:p-8">
        <Outlet />
      </main>
    </div>
  )
}
