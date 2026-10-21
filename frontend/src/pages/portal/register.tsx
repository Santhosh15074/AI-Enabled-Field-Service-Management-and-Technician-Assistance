import { useState, type FormEvent } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { AlertCircleIcon, Loader2Icon } from 'lucide-react'

import { FullPageSpinner } from '@/components/full-page-spinner'

import { Brand } from '@/components/brand'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Field, FieldDescription, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { useRegister, useShop, type Shop } from '@/lib/auth'

const EMPTY = { name: '', phone: '', email: '', password: '', confirm: '' }

/** Customer self-sign-up, through a shop's own link (/portal/register?shop=<slug>), so the
 * customer joins that shop. Admin and technician accounts are created by the shop's owner instead. */
export function CustomerRegisterPage() {
  const [params] = useSearchParams()
  const slug = params.get('shop')
  const shop = useShop(slug)

  if (slug && shop.isPending) return <FullPageSpinner />
  if (!slug || !shop.data) {
    return (
      <div className="flex min-h-svh flex-col items-center justify-center p-6">
        <div className="w-full max-w-sm text-center">
          <div className="mb-8 flex justify-center">
            <Brand />
          </div>
          <h1 className="text-xl font-semibold tracking-tight">Use your service company's link</h1>
          <p className="mt-1.5 text-sm text-muted-foreground">
            {shop.isError
              ? shop.error.message
              : 'Sign up through the link your AC or appliance service company sent you, so your requests go to them.'}
          </p>
          <p className="mt-8 text-sm text-muted-foreground">
            Already registered?{' '}
            <Link to="/portal/login" className="font-medium text-primary underline-offset-4 hover:underline">
              Log in
            </Link>
          </p>
        </div>
      </div>
    )
  }
  return <RegisterForm shop={shop.data} />
}

function RegisterForm({ shop }: { shop: Shop }) {
  const navigate = useNavigate()
  const register = useRegister()
  const [form, setForm] = useState(EMPTY)
  const [mismatch, setMismatch] = useState(false)

  const update = (key: keyof typeof EMPTY) => (e: { target: { value: string } }) => {
    setForm((current) => ({ ...current, [key]: e.target.value }))
    if (key === 'password' || key === 'confirm') setMismatch(false)
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (form.password !== form.confirm) {
      setMismatch(true)
      return
    }
    register.mutate(
      {
        shop: shop.slug,
        name: form.name,
        phone: form.phone,
        password: form.password,
        email: form.email || undefined,
      },
      {
        // Log in with whichever identifier they'll actually have: their email if they gave
        // one, their phone otherwise (user.email comes back null when they skipped it).
        onSuccess: (user) => navigate('/portal/login', { state: { registeredIdentifier: user.email ?? form.phone } }),
      },
    )
  }

  const error = mismatch ? 'The two passwords do not match.' : register.isError ? register.error.message : null

  return (
    <div className="flex min-h-svh flex-col items-center justify-center p-6">
      <div className="w-full max-w-sm">
        <div className="mb-8 flex justify-center">
          <Brand />
        </div>

        <h1 className="text-center text-xl font-semibold tracking-tight">Create your account</h1>
        <p className="mt-1.5 text-center text-sm text-muted-foreground">
          For customers of <span className="font-medium text-foreground">{shop.name}</span>. Staff accounts are created by
          the shop's owner.
        </p>

        {error && (
          <Alert variant="destructive" className="mt-6" id="register-error">
            <AlertCircleIcon aria-hidden="true" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="mt-6" aria-describedby={error ? 'register-error' : undefined}>
          <FieldGroup>
            <Field>
              <FieldLabel htmlFor="name">Full name</FieldLabel>
              <Input id="name" autoComplete="name" maxLength={100} required autoFocus value={form.name} onChange={update('name')} />
            </Field>
            <Field>
              <FieldLabel htmlFor="phone">Phone</FieldLabel>
              <Input
                id="phone"
                type="tel"
                inputMode="tel"
                autoComplete="tel"
                placeholder="+91 98765 43210"
                maxLength={20}
                required
                value={form.phone}
                onChange={update('phone')}
                aria-describedby="phone-hint"
              />
              <FieldDescription id="phone-hint">Used to log in, and for technicians to reach you.</FieldDescription>
            </Field>
            <Field>
              <FieldLabel htmlFor="email">
                Email <span className="font-normal text-muted-foreground">(optional)</span>
              </FieldLabel>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                spellCheck={false}
                placeholder="name@example.com"
                maxLength={255}
                value={form.email}
                onChange={update('email')}
              />
            </Field>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field>
                <FieldLabel htmlFor="password">Password</FieldLabel>
                <Input
                  id="password"
                  type="password"
                  autoComplete="new-password"
                  minLength={8}
                  required
                  value={form.password}
                  onChange={update('password')}
                  aria-describedby="password-hint"
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="confirm">Confirm password</FieldLabel>
                <Input
                  id="confirm"
                  type="password"
                  autoComplete="new-password"
                  minLength={8}
                  required
                  value={form.confirm}
                  onChange={update('confirm')}
                  aria-invalid={mismatch || undefined}
                />
              </Field>
            </div>
            <FieldDescription id="password-hint" className="-mt-3">
              At least 8 characters.
            </FieldDescription>
            <Button type="submit" size="lg" className="w-full" disabled={register.isPending}>
              {register.isPending && <Loader2Icon className="animate-spin" aria-hidden="true" />}
              {register.isPending ? 'Creating account…' : 'Create account'}
            </Button>
          </FieldGroup>
        </form>

        <p className="mt-8 text-center text-sm text-muted-foreground">
          Already registered?{' '}
          <Link to="/portal/login" className="font-medium text-primary underline-offset-4 hover:underline">
            Log in
          </Link>
        </p>
      </div>
    </div>
  )
}
