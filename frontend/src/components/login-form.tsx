import { useState, type FormEvent } from 'react'
import { AlertCircleIcon, Loader2Icon } from 'lucide-react'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Field, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { useLogin, type User } from '@/lib/auth'

// Checked once, not kept in sync with resizing: autoFocus only matters at mount, and
// popping the on-screen keyboard open on a phone's first paint does more harm than good.
const isDesktop = typeof window !== 'undefined' && window.matchMedia('(min-width: 1024px)').matches

/** The login form shared by staff login (email only) and the customer portal (email or phone). */
export function LoginForm({
  onLoggedIn,
  initialIdentifier = '',
  identifierLabel = 'Email',
  identifierType = 'email',
  identifierAutoComplete = 'email',
  identifierPlaceholder = 'name@example.com',
}: {
  onLoggedIn: (user: User) => void
  initialIdentifier?: string
  identifierLabel?: string
  identifierType?: 'email' | 'text'
  identifierAutoComplete?: 'email' | 'username'
  identifierPlaceholder?: string
}) {
  const [identifier, setIdentifier] = useState(initialIdentifier)
  const [password, setPassword] = useState('')
  const login = useLogin()

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    login.mutate({ identifier, password }, { onSuccess: onLoggedIn })
  }

  return (
    <>
      {login.isError && (
        <Alert variant="destructive" className="mt-6" id="login-error">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>{login.error.message}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="mt-6" aria-describedby={login.isError ? 'login-error' : undefined}>
        <FieldGroup>
          <Field>
            <FieldLabel htmlFor="identifier">{identifierLabel}</FieldLabel>
            <Input
              id="identifier"
              type={identifierType}
              autoComplete={identifierAutoComplete}
              spellCheck={false}
              placeholder={identifierPlaceholder}
              required
              autoFocus={isDesktop && !initialIdentifier}
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
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
              autoFocus={isDesktop && Boolean(initialIdentifier)}
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
    </>
  )
}
