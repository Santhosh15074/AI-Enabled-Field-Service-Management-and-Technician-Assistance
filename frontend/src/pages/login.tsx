import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircleIcon, Loader2Icon } from 'lucide-react'

import { AuthLayout } from '@/components/auth-layout'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Field, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { ROLE_HOME, useLogin } from '@/lib/auth'

export function LoginPage() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const login = useLogin()

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    login.mutate(
      { email, password },
      { onSuccess: (user) => navigate(ROLE_HOME[user.role], { replace: true }) },
    )
  }

  return (
    <AuthLayout title="Welcome back" description="Log in to your FieldAssist AI account.">
      {login.isError && (
        <Alert variant="destructive" className="mb-6" id="login-error">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>{login.error.message}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} aria-describedby={login.isError ? 'login-error' : undefined}>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="email">Email</FieldLabel>
            <Input
              id="email"
              type="email"
              autoComplete="email"
              spellCheck={false}
              placeholder="name@example.com"
              required
              autoFocus
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              aria-invalid={login.isError || undefined}
            />
          </Field>
          <Field>
            <FieldLabel htmlFor="password">Password</FieldLabel>
            <Input
              id="password"
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              aria-invalid={login.isError || undefined}
            />
          </Field>
          <Button type="submit" size="lg" className="w-full" disabled={login.isPending}>
            {login.isPending && <Loader2Icon className="animate-spin" aria-hidden="true" />}
            {login.isPending ? 'Logging in…' : 'Log in'}
          </Button>
        </FieldGroup>
      </form>

      <p className="mt-8 text-center text-sm text-muted-foreground">
        Don't have an account? Ask your organization's admin to set one up for you.
      </p>
    </AuthLayout>
  )
}
