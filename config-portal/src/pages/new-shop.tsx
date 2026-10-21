import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AlertCircleIcon, ArrowLeftIcon, Loader2Icon } from 'lucide-react'
import { toast } from 'sonner'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Field, FieldDescription, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { NativeSelect } from '@/components/ui/native-select'
import { PLANS, useCreateShop, type Plan } from '@/lib/shops'

const EMPTY = {
  name: '',
  slug: '',
  plan: 'starter' as Plan,
  contact_phone: '',
  owner_name: '',
  owner_email: '',
  owner_password: '',
}

/** "Ravi Aircon Services" -> "ravi-aircon-services": a starting point the operator can edit. */
function slugify(name: string): string {
  return name
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 40)
    .replace(/-+$/, '')
}

export function NewShopPage() {
  const navigate = useNavigate()
  const create = useCreateShop()
  const [form, setForm] = useState(EMPTY)
  // The slug follows the name until the operator edits it themselves.
  const [slugEdited, setSlugEdited] = useState(false)

  function update(key: keyof typeof EMPTY) {
    return (e: { target: { value: string } }) => {
      const value = e.target.value
      setForm((current) => ({
        ...current,
        [key]: value,
        ...(key === 'name' && !slugEdited ? { slug: slugify(value) } : {}),
      }))
      if (key === 'slug') setSlugEdited(true)
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    create.mutate(
      { ...form, contact_phone: form.contact_phone || undefined },
      {
        onSuccess: (shop) => {
          toast.success(`${shop.name} is set up. ${form.owner_name} can log in now.`)
          navigate(`/shops/${shop.id}`)
        },
      },
    )
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <Button asChild variant="ghost" size="sm" className="-ml-2.5">
          <Link to="/">
            <ArrowLeftIcon aria-hidden="true" />
            All shops
          </Link>
        </Button>
        <h1 className="mt-2 text-2xl font-semibold tracking-tight">New shop</h1>
        <p className="mt-1 text-sm text-muted-foreground">Creates the shop and its owner's login together.</p>
      </div>

      {create.isError && (
        <Alert variant="destructive" id="create-error">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>{create.error.message}</AlertDescription>
        </Alert>
      )}

      <form onSubmit={handleSubmit} className="space-y-6" aria-describedby={create.isError ? 'create-error' : undefined}>
        <Card>
          <CardHeader>
            <CardTitle>The shop</CardTitle>
          </CardHeader>
          <CardContent>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="name">Shop name</FieldLabel>
                <Input id="name" required maxLength={100} autoFocus value={form.name} onChange={update('name')} />
              </Field>
              <Field>
                <FieldLabel htmlFor="slug">Slug</FieldLabel>
                <Input
                  id="slug"
                  required
                  minLength={3}
                  maxLength={40}
                  spellCheck={false}
                  value={form.slug}
                  onChange={update('slug')}
                  aria-describedby="slug-hint"
                />
                <FieldDescription id="slug-hint">
                  Lowercase letters, digits and dashes. Goes in the customer sign-up link:{' '}
                  <span className="font-mono">/portal/register?shop={form.slug || '…'}</span>
                </FieldDescription>
              </Field>
              <div className="grid gap-5 sm:grid-cols-2">
                <Field>
                  <FieldLabel htmlFor="plan">Plan</FieldLabel>
                  <NativeSelect id="plan" value={form.plan} onChange={update('plan')}>
                    {(Object.keys(PLANS) as Plan[]).map((plan) => (
                      <option key={plan} value={plan}>
                        {PLANS[plan].label} · {PLANS[plan].price} · {PLANS[plan].technicians} technicians
                      </option>
                    ))}
                  </NativeSelect>
                </Field>
                <Field>
                  <FieldLabel htmlFor="contact_phone">
                    Contact phone <span className="font-normal text-muted-foreground">(optional)</span>
                  </FieldLabel>
                  <Input
                    id="contact_phone"
                    type="tel"
                    inputMode="tel"
                    placeholder="+91 98765 43210"
                    maxLength={20}
                    value={form.contact_phone}
                    onChange={update('contact_phone')}
                  />
                </Field>
              </div>
            </FieldGroup>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>The owner</CardTitle>
            <CardDescription>
              Logs in to the shop app with this email and sees only this shop. Tell them the password in person.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="owner_name">Name</FieldLabel>
                <Input id="owner_name" required maxLength={100} value={form.owner_name} onChange={update('owner_name')} />
              </Field>
              <div className="grid gap-5 sm:grid-cols-2">
                <Field>
                  <FieldLabel htmlFor="owner_email">Email</FieldLabel>
                  <Input
                    id="owner_email"
                    type="email"
                    required
                    spellCheck={false}
                    autoComplete="off"
                    value={form.owner_email}
                    onChange={update('owner_email')}
                  />
                </Field>
                <Field>
                  <FieldLabel htmlFor="owner_password">Password</FieldLabel>
                  <Input
                    id="owner_password"
                    type="password"
                    required
                    minLength={8}
                    autoComplete="new-password"
                    value={form.owner_password}
                    onChange={update('owner_password')}
                    aria-describedby="owner-password-hint"
                  />
                  <FieldDescription id="owner-password-hint">At least 8 characters.</FieldDescription>
                </Field>
              </div>
            </FieldGroup>
          </CardContent>
        </Card>

        <div className="flex justify-end gap-2">
          <Button asChild variant="outline">
            <Link to="/">Cancel</Link>
          </Button>
          <Button type="submit" disabled={create.isPending}>
            {create.isPending && <Loader2Icon className="animate-spin" aria-hidden="true" />}
            {create.isPending ? 'Creating…' : 'Create shop'}
          </Button>
        </div>
      </form>
    </div>
  )
}
