import { useState, type FormEvent, type ReactNode } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AlertCircleIcon, ArrowLeftIcon, CopyIcon, Loader2Icon } from 'lucide-react'
import { toast } from 'sonner'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Field, FieldDescription, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { NativeSelect } from '@/components/ui/native-select'
import {
  PLANS,
  ROLE_LABEL,
  signUpLink,
  useAddStaff,
  useResetPassword,
  useSetStaffActive,
  useShop,
  useUpdateShop,
  type Plan,
  type ShopDetail,
  type Staff,
  type StaffRole,
} from '@/lib/shops'
import { cn } from '@/lib/utils'

export function ShopPage() {
  const shopId = Number(useParams().shopId)
  const shop = useShop(shopId)

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2.5">
        <Link to="/">
          <ArrowLeftIcon aria-hidden="true" />
          All shops
        </Link>
      </Button>

      {shop.isPending && <p className="text-sm text-muted-foreground">Loading…</p>}
      {shop.isError && <ErrorAlert message={shop.error.message} />}
      {/* Keyed on the shop's own values, so the forms reset to what the server saved after every change. */}
      {shop.data && <ShopSettings key={JSON.stringify(shop.data)} shop={shop.data} />}
    </div>
  )
}

function ShopSettings({ shop }: { shop: ShopDetail }) {
  return (
    <>
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-2xl font-semibold tracking-tight">{shop.name}</h1>
        {shop.is_active ? <Badge variant="secondary">Active</Badge> : <Badge variant="destructive">Switched off</Badge>}
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat label="Active technicians" used={shop.active_technicians} limit={shop.technician_limit} />
        <Stat label="Reports this month" used={shop.reports_this_month} limit={shop.monthly_report_limit} />
        <Stat label="Customers" used={shop.customers} />
      </div>

      <SignUpLinkCard slug={shop.slug} />
      <div className="grid gap-6 lg:grid-cols-2">
        <DetailsCard shop={shop} />
        <PlanCard shop={shop} />
      </div>
      <StaffCard shop={shop} />
      <SwitchOffCard shop={shop} />
    </>
  )
}

function ErrorAlert({ message, id }: { message: string; id?: string }) {
  return (
    <Alert variant="destructive" id={id}>
      <AlertCircleIcon aria-hidden="true" />
      <AlertDescription>{message}</AlertDescription>
    </Alert>
  )
}

function SaveButton({ pending, children }: { pending: boolean; children: ReactNode }) {
  return (
    <Button type="submit" disabled={pending}>
      {pending && <Loader2Icon className="animate-spin" aria-hidden="true" />}
      {children}
    </Button>
  )
}

function Stat({ label, used, limit }: { label: string; used: number; limit?: number }) {
  const over = limit !== undefined && used >= limit
  return (
    <Card className="gap-1 px-5 py-4">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className={cn('text-2xl font-semibold tabular-nums', over && 'text-destructive')}>
        {used.toLocaleString('en-IN')}
        {limit !== undefined && (
          <span className="text-base font-normal text-muted-foreground"> / {limit.toLocaleString('en-IN')}</span>
        )}
      </p>
    </Card>
  )
}

function SignUpLinkCard({ slug }: { slug: string }) {
  const link = signUpLink(slug)

  async function copy() {
    try {
      await navigator.clipboard.writeText(link)
      toast.success('Sign-up link copied.')
    } catch {
      toast.error("Couldn't copy. Select the link and copy it instead.")
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Customer sign-up link</CardTitle>
        <CardDescription>Customers who sign up through this link join this shop and no other.</CardDescription>
      </CardHeader>
      <CardContent className="flex flex-wrap items-center gap-2">
        <code className="min-w-0 flex-1 truncate rounded-md bg-muted px-3 py-1.5 text-sm">{link}</code>
        <Button type="button" variant="outline" onClick={copy}>
          <CopyIcon aria-hidden="true" />
          Copy
        </Button>
      </CardContent>
    </Card>
  )
}

function DetailsCard({ shop }: { shop: ShopDetail }) {
  const update = useUpdateShop(shop.id)
  const [form, setForm] = useState({ name: shop.name, slug: shop.slug, contact_phone: shop.contact_phone ?? '' })
  const set = (key: keyof typeof form) => (e: { target: { value: string } }) =>
    setForm((current) => ({ ...current, [key]: e.target.value }))

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (
      form.slug !== shop.slug &&
      !window.confirm(`Changing the slug breaks the old sign-up link (?shop=${shop.slug}). Customers already signed up aren't affected. Continue?`)
    ) {
      return
    }
    update.mutate(form, { onSuccess: () => toast.success('Shop details saved.') })
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Details</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <FieldGroup>
            {update.isError && <ErrorAlert message={update.error.message} />}
            <Field>
              <FieldLabel htmlFor="shop-name">Shop name</FieldLabel>
              <Input id="shop-name" required maxLength={100} value={form.name} onChange={set('name')} />
            </Field>
            <Field>
              <FieldLabel htmlFor="shop-slug">Slug</FieldLabel>
              <Input id="shop-slug" required minLength={3} maxLength={40} spellCheck={false} value={form.slug} onChange={set('slug')} />
            </Field>
            <Field>
              <FieldLabel htmlFor="shop-phone">Contact phone</FieldLabel>
              <Input
                id="shop-phone"
                type="tel"
                inputMode="tel"
                placeholder="+91 98765 43210"
                maxLength={20}
                value={form.contact_phone}
                onChange={set('contact_phone')}
              />
            </Field>
            <div className="flex justify-end">
              <SaveButton pending={update.isPending}>Save details</SaveButton>
            </div>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  )
}

function PlanCard({ shop }: { shop: ShopDetail }) {
  const update = useUpdateShop(shop.id)
  const [plan, setPlan] = useState<Plan>(shop.plan)
  const [technicians, setTechnicians] = useState(String(shop.technician_limit))
  const [reports, setReports] = useState(String(shop.monthly_report_limit))

  function choosePlan(next: Plan) {
    // A new plan brings its own limits; they can still be adjusted for this shop before saving.
    setPlan(next)
    setTechnicians(String(PLANS[next].technicians))
    setReports(String(PLANS[next].reports))
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    update.mutate(
      { plan, technician_limit: Number(technicians), monthly_report_limit: Number(reports) },
      { onSuccess: () => toast.success('Plan saved.') },
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Plan and limits</CardTitle>
        <CardDescription>
          The technician limit is enforced. The report limit isn't (no overage charges): call a shop that keeps going over.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit}>
          <FieldGroup>
            {update.isError && <ErrorAlert message={update.error.message} />}
            <Field>
              <FieldLabel htmlFor="plan">Plan</FieldLabel>
              <NativeSelect id="plan" value={plan} onChange={(e) => choosePlan(e.target.value as Plan)}>
                {(Object.keys(PLANS) as Plan[]).map((key) => (
                  <option key={key} value={key}>
                    {PLANS[key].label} · {PLANS[key].price} a month
                  </option>
                ))}
              </NativeSelect>
            </Field>
            <div className="grid gap-5 sm:grid-cols-2">
              <Field>
                <FieldLabel htmlFor="technician-limit">Technicians</FieldLabel>
                <Input
                  id="technician-limit"
                  type="number"
                  min={0}
                  max={100000}
                  required
                  value={technicians}
                  onChange={(e) => setTechnicians(e.target.value)}
                />
              </Field>
              <Field>
                <FieldLabel htmlFor="report-limit">Reports a month</FieldLabel>
                <Input
                  id="report-limit"
                  type="number"
                  min={0}
                  max={100000}
                  required
                  value={reports}
                  onChange={(e) => setReports(e.target.value)}
                />
              </Field>
            </div>
            <div className="flex justify-end">
              <SaveButton pending={update.isPending}>Save plan</SaveButton>
            </div>
          </FieldGroup>
        </form>
      </CardContent>
    </Card>
  )
}

function StaffCard({ shop }: { shop: ShopDetail }) {
  const setActive = useSetStaffActive()
  const [resetting, setResetting] = useState<number | null>(null)

  function toggle(person: Staff) {
    setActive.mutate(
      { userId: person.id, is_active: !person.is_active },
      {
        onSuccess: () => toast.success(`${person.name} ${person.is_active ? 'deactivated' : 'reactivated'}.`),
        onError: (error) => toast.error(error.message),
      },
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Owners and technicians</CardTitle>
        <CardDescription>
          Owners see everything in the shop and can add their own technicians, up to the plan's limit. Customers aren't
          listed here.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-sm">
            <thead className="border-b bg-muted/40 text-left text-xs text-muted-foreground">
              <tr>
                <th className="px-4 py-2.5 font-medium">Name</th>
                <th className="px-4 py-2.5 font-medium">Role</th>
                <th className="px-4 py-2.5 font-medium">Status</th>
                <th className="px-4 py-2.5 text-right font-medium">
                  <span className="sr-only">Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {shop.staff.map((person) => (
                <StaffRow
                  key={person.id}
                  person={person}
                  resetting={resetting === person.id}
                  onReset={() => setResetting(resetting === person.id ? null : person.id)}
                  onToggle={() => toggle(person)}
                  toggling={setActive.isPending && setActive.variables?.userId === person.id}
                />
              ))}
            </tbody>
          </table>
        </div>
        <AddStaffForm shopId={shop.id} />
      </CardContent>
    </Card>
  )
}

function StaffRow({
  person,
  resetting,
  onReset,
  onToggle,
  toggling,
}: {
  person: Staff
  resetting: boolean
  onReset: () => void
  onToggle: () => void
  toggling: boolean
}) {
  return (
    <>
      <tr className={cn('border-b last:border-0', !person.is_active && 'text-muted-foreground')}>
        <td className="px-4 py-3">
          <div className="font-medium">{person.name}</div>
          <div className="text-xs text-muted-foreground">
            {person.email}
            {person.skill_area && ` · ${person.skill_area}`}
          </div>
        </td>
        <td className="px-4 py-3">{ROLE_LABEL[person.role]}</td>
        <td className="px-4 py-3">
          {person.is_active ? <Badge variant="secondary">Active</Badge> : <Badge variant="outline">Deactivated</Badge>}
        </td>
        <td className="px-4 py-3">
          <div className="flex justify-end gap-1">
            <Button type="button" variant="ghost" size="sm" onClick={onReset} aria-expanded={resetting}>
              Reset password
            </Button>
            <Button type="button" variant="ghost" size="sm" onClick={onToggle} disabled={toggling}>
              {person.is_active ? 'Deactivate' : 'Reactivate'}
            </Button>
          </div>
        </td>
      </tr>
      {resetting && (
        <tr className="border-b bg-muted/30 last:border-0">
          <td colSpan={4} className="px-4 py-3">
            <ResetPasswordForm person={person} onDone={onReset} />
          </td>
        </tr>
      )}
    </>
  )
}

function ResetPasswordForm({ person, onDone }: { person: Staff; onDone: () => void }) {
  const reset = useResetPassword()
  const [password, setPassword] = useState('')

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    reset.mutate(
      { userId: person.id, password },
      {
        onSuccess: () => {
          toast.success(`New password set for ${person.name}. Tell them in person or by phone.`)
          onDone()
        },
      },
    )
  }

  const inputId = `new-password-${person.id}`
  return (
    <form onSubmit={handleSubmit} className="flex flex-wrap items-end gap-2">
      <Field className="min-w-56 flex-1">
        <FieldLabel htmlFor={inputId}>New password for {person.name}</FieldLabel>
        <Input
          id={inputId}
          type="password"
          autoComplete="new-password"
          minLength={8}
          required
          autoFocus
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
      </Field>
      <SaveButton pending={reset.isPending}>Set password</SaveButton>
      {reset.isError && <p className="w-full text-sm text-destructive">{reset.error.message}</p>}
    </form>
  )
}

const EMPTY_STAFF = { name: '', email: '', password: '', role: 'technician' as StaffRole, skill_area: '' }

function AddStaffForm({ shopId }: { shopId: number }) {
  const add = useAddStaff(shopId)
  const [form, setForm] = useState(EMPTY_STAFF)
  const set = (key: keyof typeof EMPTY_STAFF) => (e: { target: { value: string } }) =>
    setForm((current) => ({ ...current, [key]: e.target.value }))

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    add.mutate(
      { ...form, skill_area: form.role === 'technician' ? form.skill_area || undefined : undefined },
      { onSuccess: () => toast.success(`${form.name} added.`) },
    )
  }

  return (
    <form onSubmit={handleSubmit} aria-describedby={add.isError ? 'add-staff-error' : undefined}>
      <h3 className="mb-3 text-sm font-medium">Add an owner or technician</h3>
      <FieldGroup>
        {add.isError && <ErrorAlert id="add-staff-error" message={add.error.message} />}
        <div className="grid gap-5 sm:grid-cols-2">
          <Field>
            <FieldLabel htmlFor="staff-name">Name</FieldLabel>
            <Input id="staff-name" required maxLength={100} value={form.name} onChange={set('name')} />
          </Field>
          <Field>
            <FieldLabel htmlFor="staff-role">Role</FieldLabel>
            <NativeSelect id="staff-role" value={form.role} onChange={set('role')}>
              <option value="technician">Technician</option>
              <option value="admin">Owner (sees everything in the shop)</option>
            </NativeSelect>
          </Field>
          <Field>
            <FieldLabel htmlFor="staff-email">Email</FieldLabel>
            <Input id="staff-email" type="email" required spellCheck={false} autoComplete="off" value={form.email} onChange={set('email')} />
          </Field>
          <Field>
            <FieldLabel htmlFor="staff-password">Password</FieldLabel>
            <Input
              id="staff-password"
              type="password"
              required
              minLength={8}
              autoComplete="new-password"
              value={form.password}
              onChange={set('password')}
            />
          </Field>
          {form.role === 'technician' && (
            <Field>
              <FieldLabel htmlFor="staff-skill">
                Skill area <span className="font-normal text-muted-foreground">(optional)</span>
              </FieldLabel>
              <Input id="staff-skill" maxLength={100} placeholder="e.g. Split AC, Washing machines" value={form.skill_area} onChange={set('skill_area')} />
            </Field>
          )}
        </div>
        <FieldDescription className="-mt-2">Tell them their password in person; they log in to the shop app.</FieldDescription>
        <div className="flex justify-end">
          <SaveButton pending={add.isPending}>Add</SaveButton>
        </div>
      </FieldGroup>
    </form>
  )
}

function SwitchOffCard({ shop }: { shop: ShopDetail }) {
  const update = useUpdateShop(shop.id)

  function toggle() {
    if (
      shop.is_active &&
      !window.confirm(
        `Switch off ${shop.name}? Its owners, technicians and customers are logged out and can't log in, and its sign-up link stops working. Nothing is deleted; you can switch it back on.`,
      )
    ) {
      return
    }
    update.mutate(
      { is_active: !shop.is_active },
      {
        onSuccess: (saved) => toast.success(`${saved.name} switched ${saved.is_active ? 'on' : 'off'}.`),
        onError: (error) => toast.error(error.message),
      },
    )
  }

  return (
    <Card className={cn(shop.is_active && 'border-destructive/30')}>
      <CardHeader>
        <CardTitle>{shop.is_active ? 'Switch off this shop' : 'Switch this shop back on'}</CardTitle>
        <CardDescription>
          {shop.is_active
            ? 'For a shop that has stopped paying or left. Everyone in it is locked out; their data is kept.'
            : 'Everyone in the shop can log in again, and the sign-up link works again.'}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button type="button" variant={shop.is_active ? 'destructive' : 'default'} onClick={toggle} disabled={update.isPending}>
          {update.isPending && <Loader2Icon className="animate-spin" aria-hidden="true" />}
          {shop.is_active ? 'Switch off' : 'Switch on'}
        </Button>
      </CardContent>
    </Card>
  )
}
