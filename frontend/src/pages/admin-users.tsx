import { useState, type FormEvent } from 'react'
import { AlertCircleIcon, Loader2Icon, PlusIcon, UsersIcon } from 'lucide-react'
import { toast } from 'sonner'

import { EmptyState, PageTitle } from '@/components/dashboard'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Field, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { NativeSelect } from '@/components/ui/native-select'
import { Skeleton } from '@/components/ui/skeleton'
import { useCurrentUser } from '@/lib/auth'
import { useCreateStaffUser, useSetUserActive, useUsers, type StaffRole } from '@/lib/users'

const EMPTY = { name: '', email: '', password: '', role: 'technician' as StaffRole, skill_area: '' }

const ROLE_LABEL: Record<string, string> = { admin: 'Owner / admin', technician: 'Technician', customer: 'Customer' }

export function AdminUsersPage() {
  const { data: me } = useCurrentUser()
  const users = useUsers()
  const createStaffUser = useCreateStaffUser()
  const setActive = useSetUserActive()
  const [form, setForm] = useState(EMPTY)
  const [open, setOpen] = useState(false)

  const update = (key: keyof typeof EMPTY) => (e: { target: { value: string } }) =>
    setForm((current) => ({ ...current, [key]: e.target.value }) as typeof EMPTY)

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    createStaffUser.mutate(
      {
        name: form.name,
        email: form.email,
        password: form.password,
        role: form.role,
        skill_area: form.role === 'technician' ? form.skill_area || undefined : undefined,
      },
      { onSuccess: () => { setForm(EMPTY); setOpen(false) } },
    )
  }

  function toggleActive(id: number, isActive: boolean) {
    setActive.mutate({ id, is_active: !isActive }, { onError: (error) => toast.error(error.message) })
  }

  return (
    <>
      <PageTitle
        title="Users"
        description="Admins and technicians on your team. Customers sign themselves up through the portal."
        action={
          !open && (
            <Button onClick={() => setOpen(true)}>
              <PlusIcon aria-hidden="true" />
              Add staff
            </Button>
          )
        }
      />

      {open && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Add staff</CardTitle>
            <CardDescription>They can log in with this email and password right away.</CardDescription>
          </CardHeader>
          <CardContent>
            {createStaffUser.isError && (
              <Alert variant="destructive" className="mb-4" id="staff-error">
                <AlertCircleIcon aria-hidden="true" />
                <AlertDescription>{createStaffUser.error.message}</AlertDescription>
              </Alert>
            )}
            <form onSubmit={handleSubmit} aria-describedby={createStaffUser.isError ? 'staff-error' : undefined}>
              <FieldGroup>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field>
                    <FieldLabel htmlFor="staff-name">Name</FieldLabel>
                    <Input id="staff-name" required autoFocus value={form.name} onChange={update('name')} />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="staff-role">Role</FieldLabel>
                    <NativeSelect id="staff-role" value={form.role} onChange={update('role')}>
                      <option value="technician">Technician</option>
                      <option value="admin">Owner / admin (sees everything in the shop)</option>
                    </NativeSelect>
                  </Field>
                </div>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field>
                    <FieldLabel htmlFor="staff-email">Email</FieldLabel>
                    <Input id="staff-email" type="email" required value={form.email} onChange={update('email')} />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="staff-password">Password</FieldLabel>
                    <Input id="staff-password" type="password" required value={form.password} onChange={update('password')} />
                  </Field>
                </div>
                {form.role === 'technician' && (
                  <Field>
                    <FieldLabel htmlFor="staff-skill">
                      Skill area <span className="font-normal text-muted-foreground">(optional)</span>
                    </FieldLabel>
                    <Input id="staff-skill" placeholder="Electrical, HVAC, Plumbing…" value={form.skill_area} onChange={update('skill_area')} />
                  </Field>
                )}
                <div className="flex gap-2">
                  <Button type="submit" disabled={createStaffUser.isPending}>
                    {createStaffUser.isPending && <Loader2Icon className="animate-spin" aria-hidden="true" />}
                    {createStaffUser.isPending ? 'Creating…' : 'Create account'}
                  </Button>
                  <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
                    Cancel
                  </Button>
                </div>
              </FieldGroup>
            </form>
          </CardContent>
        </Card>
      )}

      {users.isPending ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-16 rounded-xl" />
          ))}
        </div>
      ) : users.isError ? (
        <Alert variant="destructive">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>Couldn't load users: {users.error.message}</AlertDescription>
        </Alert>
      ) : users.data.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState icon={UsersIcon} title="No users yet" description="Add your first teammate above." />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="divide-y p-0">
            {users.data.map((user) => (
              <div key={user.id} className="flex items-center justify-between gap-4 px-4 py-3 sm:px-5">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <p className="truncate text-sm font-medium">{user.name}</p>
                    <Badge variant="outline" className="font-normal">
                      {ROLE_LABEL[user.role] ?? user.role}
                    </Badge>
                    {!user.is_active && <Badge className="bg-muted font-normal text-muted-foreground">Deactivated</Badge>}
                  </div>
                  <p className="mt-0.5 truncate text-xs text-muted-foreground">
                    {user.email ?? user.phone}
                    {user.skill_area && ` · ${user.skill_area}`}
                  </p>
                </div>
                {user.role !== 'customer' && user.id !== me?.id && (
                  <Button
                    variant="outline"
                    size="sm"
                    className="shrink-0"
                    disabled={setActive.isPending}
                    onClick={() => toggleActive(user.id, user.is_active)}
                  >
                    {user.is_active ? 'Deactivate' : 'Activate'}
                  </Button>
                )}
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </>
  )
}
