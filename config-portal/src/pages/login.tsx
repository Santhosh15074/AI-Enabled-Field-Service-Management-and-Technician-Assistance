import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircleIcon, Loader2Icon } from 'lucide-react'

import { Brand } from '@/components/layout'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Field, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { useLogin } from '@/lib/auth'

/** Operator login. Operators are created with scripts/create_operator.py; there's no sign-up. */
export function LoginPage() {
  const navigate = useNavigate()
  const login = useLogin()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    login.mutate({ email, password }, { onSuccess: () => navigate('/', { replace: true }) })
  }

  return (
    <div className="flex min-h-svh flex-col items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Brand />
        </div>
        <h1 className="text-center text-xl font-semibold tracking-tight">Operator log in</h1>
        <p className="mt-1.5 text-center text-sm text-muted-foreground">
          For Sollu staff. Shop owners and technicians log in to the shop app instead.
        </p>

        {login.isError && (
          <Alert variant="destructive" className="mt-6" id="login-error">
            <AlertCircleIcon aria-hidden="true" />
            <AlertDescription>{login.error.message}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="mt-6" aria-describedby={login.isError ? 'login-error' : undefined}>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="email">Email</FieldLabel>
              <Input
                id="email"
                type="email"
                autoComplete="username"
                spellCheck={false}
                required
                autoFocus
                value={email}
                onChange={(e) => setEmail(e.target.value)}
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
              />
            </Field>
            <Button type="submit" size="lg" className="w-full" disabled={login.isPending}>
              {login.isPending && <Loader2Icon className="animate-spin" aria-hidden="true" />}
              {login.isPending ? 'Logging in…' : 'Log in'}
            </Button>
          </FieldGroup>
        </form>
      </div>
    </div>
  )
}
