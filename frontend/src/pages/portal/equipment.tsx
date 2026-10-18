import { useState, type FormEvent } from 'react'
import { AlertCircleIcon, HardDriveIcon, Loader2Icon, PlusIcon } from 'lucide-react'

import { EmptyState, PageTitle } from '@/components/dashboard'
import { RiskBadge } from '@/components/risk-badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Field, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import { useMyEquipment, useRegisterEquipment } from '@/lib/requests'

const EMPTY = { name: '', type: '', serial_number: '' }

export function CustomerEquipmentPage() {
  const equipment = useMyEquipment()
  const register = useRegisterEquipment()
  const [form, setForm] = useState(EMPTY)
  const [open, setOpen] = useState(false)

  const update = (key: keyof typeof EMPTY) => (e: { target: { value: string } }) =>
    setForm((current) => ({ ...current, [key]: e.target.value }))

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    register.mutate(
      { name: form.name, type: form.type, serial_number: form.serial_number || undefined },
      { onSuccess: () => { setForm(EMPTY); setOpen(false) } },
    )
  }

  return (
    <>
      <PageTitle
        title="My equipment"
        description="The devices you want serviced. Attach one when you raise a complaint."
        action={
          !open && (
            <Button onClick={() => setOpen(true)}>
              <PlusIcon aria-hidden="true" />
              Add equipment
            </Button>
          )
        }
      />

      {open && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>Add equipment</CardTitle>
            <CardDescription>A short name and type is enough to get started.</CardDescription>
          </CardHeader>
          <CardContent>
            {register.isError && (
              <Alert variant="destructive" className="mb-4" id="equipment-error">
                <AlertCircleIcon aria-hidden="true" />
                <AlertDescription>{register.error.message}</AlertDescription>
              </Alert>
            )}
            <form onSubmit={handleSubmit} aria-describedby={register.isError ? 'equipment-error' : undefined}>
              <FieldGroup>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field>
                    <FieldLabel htmlFor="eq-name">Name</FieldLabel>
                    <Input
                      id="eq-name"
                      placeholder="Lathe #1"
                      maxLength={100}
                      required
                      autoFocus
                      value={form.name}
                      onChange={update('name')}
                    />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="eq-type">Type</FieldLabel>
                    <Input
                      id="eq-type"
                      placeholder="Lathe, Compressor, HVAC unit…"
                      maxLength={50}
                      required
                      value={form.type}
                      onChange={update('type')}
                    />
                  </Field>
                </div>
                <Field>
                  <FieldLabel htmlFor="eq-serial">
                    Serial number <span className="font-normal text-muted-foreground">(optional)</span>
                  </FieldLabel>
                  <Input
                    id="eq-serial"
                    maxLength={100}
                    value={form.serial_number}
                    onChange={update('serial_number')}
                  />
                </Field>
                <div className="flex gap-2">
                  <Button type="submit" disabled={register.isPending}>
                    {register.isPending && <Loader2Icon className="animate-spin" aria-hidden="true" />}
                    {register.isPending ? 'Saving…' : 'Save equipment'}
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

      {equipment.isPending ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-28 rounded-xl" />
          ))}
        </div>
      ) : equipment.isError ? (
        <Alert variant="destructive">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>Couldn't load your equipment: {equipment.error.message}</AlertDescription>
        </Alert>
      ) : equipment.data.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState
              icon={HardDriveIcon}
              title="No equipment registered yet"
              description="Add a device above so you can attach it when something goes wrong with it."
            />
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {equipment.data.map((item) => (
            <Card key={item.id}>
              <CardHeader className="flex flex-row items-start gap-3">
                <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary">
                  <HardDriveIcon className="size-4.5" aria-hidden="true" />
                </div>
                <div className="min-w-0">
                  <CardTitle className="truncate">{item.name}</CardTitle>
                  <CardDescription>{item.type}</CardDescription>
                </div>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                {item.serial_number && <p className="text-xs text-muted-foreground">Serial: {item.serial_number}</p>}
                <RiskBadge riskLevel={item.risk_level} />
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </>
  )
}
