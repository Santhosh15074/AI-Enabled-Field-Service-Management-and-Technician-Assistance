import { Link } from 'react-router-dom'

import { Brand } from '@/components/brand'
import { Button } from '@/components/ui/button'

export function NotFoundPage() {
  return (
    <div className="flex min-h-svh flex-col items-center justify-center gap-6 p-6 text-center">
      <Brand />
      <div>
        <p className="text-sm font-medium text-primary">404</p>
        <h1 className="mt-2 text-3xl font-semibold tracking-tight">Page not found</h1>
        <p className="mt-2 text-muted-foreground">The page you're looking for doesn't exist or has moved.</p>
      </div>
      <Button asChild>
        <Link to="/">Go to my dashboard</Link>
      </Button>
    </div>
  )
}
