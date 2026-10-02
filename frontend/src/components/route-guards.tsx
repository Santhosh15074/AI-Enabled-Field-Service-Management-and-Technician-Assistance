import { Navigate, Outlet } from 'react-router-dom'

import { FullPageSpinner } from '@/components/full-page-spinner'
import { ROLE_HOME, useCurrentUser, type Role } from '@/lib/auth'

/** Shows child routes only to logged-in users with one of the given roles. */
export function RequireRole({ roles }: { roles: Role[] }) {
  const { data: user, isPending } = useCurrentUser()

  if (isPending) return <FullPageSpinner />
  if (!user) return <Navigate to="/login" replace />
  if (!roles.includes(user.role)) return <Navigate to={ROLE_HOME[user.role]} replace />
  return <Outlet />
}

/** Sends logged-in users away from the login page to their dashboard. */
export function GuestOnly() {
  const { data: user, isPending } = useCurrentUser()

  if (isPending) return <FullPageSpinner />
  if (user) return <Navigate to={ROLE_HOME[user.role]} replace />
  return <Outlet />
}

export function HomeRedirect() {
  const { data: user, isPending } = useCurrentUser()

  if (isPending) return <FullPageSpinner />
  return <Navigate to={user ? ROLE_HOME[user.role] : '/login'} replace />
}
