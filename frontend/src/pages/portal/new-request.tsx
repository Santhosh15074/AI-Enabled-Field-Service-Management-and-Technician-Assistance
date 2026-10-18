import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AlertCircleIcon, Loader2Icon, SearchIcon } from 'lucide-react'

import { PageTitle } from '@/components/dashboard'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Field, FieldDescription, FieldGroup, FieldLabel } from '@/components/ui/field'
import { NativeSelect } from '@/components/ui/native-select'
import { SuggestionList } from '@/components/suggestion-list'
import { Textarea } from '@/components/ui/textarea'
import { useCurrentUser } from '@/lib/auth'
import { useCategories, useCreateRequest, useMyEquipment, useSuggestFixes } from '@/lib/requests'

export function NewRequestPage() {
  const navigate = useNavigate()
  const { data: user } = useCurrentUser()
  const equipment = useMyEquipment()
  const categories = useCategories()
  const createRequest = useCreateRequest()
  const suggestFixes = useSuggestFixes()
  const [description, setDescription] = useState('')
  const [equipmentId, setEquipmentId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [address, setAddress] = useState('')

  // Asked once: if an address is already on file, this complaint doesn't need to repeat it.
  const needsAddress = !user?.address

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    createRequest.mutate(
      {
        description,
        equipment_id: equipmentId ? Number(equipmentId) : undefined,
        category_id: categoryId ? Number(categoryId) : undefined,
        address: needsAddress ? address : undefined,
      },
      { onSuccess: () => navigate('/portal/requests') },
    )
  }

  return (
    <>
      <PageTitle title="New complaint" description="Describe what's wrong and we'll route it to the right technician." />

      <Card className="max-w-xl">
        <CardContent>
          {createRequest.isError && (
            <Alert variant="destructive" className="mb-6" id="request-error">
              <AlertCircleIcon aria-hidden="true" />
              <AlertDescription>{createRequest.error.message}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} aria-describedby={createRequest.isError ? 'request-error' : undefined}>
            <FieldGroup>
              <Field>
                <FieldLabel htmlFor="description">What's the problem?</FieldLabel>
                <Textarea
                  id="description"
                  rows={4}
                  required
                  autoFocus
                  placeholder="The compressor is making a loud grinding noise and won't hold pressure…"
                  value={description}
                  onChange={(e) => {
                    setDescription(e.target.value)
                    if (suggestFixes.data) suggestFixes.reset()
                  }}
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  className="self-start"
                  disabled={description.trim().length < 10 || suggestFixes.isPending}
                  onClick={() => suggestFixes.mutate(description)}
                >
                  {suggestFixes.isPending ? (
                    <Loader2Icon className="animate-spin" aria-hidden="true" />
                  ) : (
                    <SearchIcon aria-hidden="true" />
                  )}
                  Check for a quick fix
                </Button>
                {suggestFixes.data && (
                  <div className="mt-1">
                    <SuggestionList suggestions={suggestFixes.data} />
                  </div>
                )}
              </Field>

              <Field>
                <FieldLabel htmlFor="equipment">
                  Equipment <span className="font-normal text-muted-foreground">(optional)</span>
                </FieldLabel>
                <NativeSelect
                  id="equipment"
                  value={equipmentId}
                  onChange={(e) => setEquipmentId(e.target.value)}
                  disabled={equipment.isPending || (equipment.data?.length ?? 0) === 0}
                >
                  <option value="">
                    {equipment.data?.length === 0 ? 'No equipment registered yet' : "I'm not sure, or it's general"}
                  </option>
                  {equipment.data?.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name} ({item.type})
                    </option>
                  ))}
                </NativeSelect>
                {equipment.data?.length === 0 && (
                  <FieldDescription>
                    You can register equipment from{' '}
                    <Link to="/portal/equipment" className="underline underline-offset-4">
                      My equipment
                    </Link>{' '}
                    first, or just submit without it.
                  </FieldDescription>
                )}
              </Field>

              <Field>
                <FieldLabel htmlFor="category">
                  Category <span className="font-normal text-muted-foreground">(optional)</span>
                </FieldLabel>
                <NativeSelect
                  id="category"
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  disabled={categories.isPending}
                >
                  <option value="">Not sure</option>
                  {categories.data?.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.category_name}
                    </option>
                  ))}
                </NativeSelect>
              </Field>

              {needsAddress && (
                <Field>
                  <FieldLabel htmlFor="address">Service address</FieldLabel>
                  <Textarea
                    id="address"
                    rows={2}
                    required
                    placeholder="Where should the technician go?"
                    value={address}
                    onChange={(e) => setAddress(e.target.value)}
                    aria-describedby="address-hint"
                  />
                  <FieldDescription id="address-hint">Asked once — saved for your future requests too.</FieldDescription>
                </Field>
              )}

              <Button type="submit" size="lg" disabled={createRequest.isPending}>
                {createRequest.isPending && <Loader2Icon className="animate-spin" aria-hidden="true" />}
                {createRequest.isPending ? 'Submitting…' : 'Submit complaint'}
              </Button>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </>
  )
}
