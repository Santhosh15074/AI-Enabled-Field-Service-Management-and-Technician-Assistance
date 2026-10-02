import { CheckCircle2Icon } from 'lucide-react'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { Brand } from '@/components/brand'
import { LoginForm } from '@/components/login-form'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { ROLE_HOME } from '@/lib/auth'

/** The customer portal's own login — distinct from staff login, with a sign-up link.
 * Accepts an email or a phone number, since email is optional at registration. */
export function CustomerLoginPage() {
  const navigate = useNavigate()
  const location = useLocation()
  const justRegistered = (location.state as { registeredIdentifier?: string } | null)?.registeredIdentifier

  return (
    <div className="flex min-h-svh flex-col items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Brand />
        </div>

        <h1 className="text-center text-xl font-semibold tracking-tight">Customer portal</h1>
        <p className="mt-1.5 text-center text-sm text-muted-foreground">Log in to submit and track service requests.</p>

        {justRegistered && (
          <Alert className="mt-6">
            <CheckCircle2Icon aria-hidden="true" />
            <AlertDescription>Your account is ready. Log in with your new password.</AlertDescription>
          </Alert>
        )}

        <LoginForm
          initialIdentifier={justRegistered}
          identifierLabel="Email or phone number"
          identifierType="text"
          identifierAutoComplete="username"
          identifierPlaceholder="name@example.com or phone number"
          onLoggedIn={(user) => navigate(ROLE_HOME[user.role], { replace: true })}
        />

        <p className="mt-8 text-center text-sm text-muted-foreground">
          New customer?{' '}
          <Link to="/portal/register" className="font-medium text-primary underline-offset-4 hover:underline">
            Create an account
          </Link>
        </p>
      </div>
    </div>
  )
}
