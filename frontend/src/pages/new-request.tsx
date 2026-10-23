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
import { useCurrentUser, type Role } from '@/lib/auth'
import { useCategories, useCreateRequest, useCustomerChoices, useMyEquipment, useSuggestFixes } from '@/lib/requests'

// Where each role lands after submitting: the list the new request now appears in.
const AFTER_SUBMIT: Record<Role, string> = {
  customer: '/portal/requests',
  admin: '/admin/requests',
  technician: '/technician/jobs',
}

/** A customer's own complaint form; admins and technicians use it to raise a request on a
 * customer's behalf, so it first asks which customer. */
export function NewRequestPage() {
  const navigate = useNavigate()
  const { data: user } = useCurrentUser()
  const isStaff = user!.role !== 'customer'
  const myEquipment = useMyEquipment(!isStaff)
  const customers = useCustomerChoices(isStaff)
  const categories = useCategories()
  const createRequest = useCreateRequest()
  const suggestFixes = useSuggestFixes()
  const [customerId, setCustomerId] = useState('')
  const [description, setDescription] = useState('')
  const [equipmentId, setEquipmentId] = useState('')
  const [categoryId, setCategoryId] = useState('')
  const [address, setAddress] = useState('')

  const customer = customers.data?.find((item) => String(item.id) === customerId)
  const equipment = isStaff ? customer?.equipment : myEquipment.data
  const equipmentLoading = isStaff ? !customer : myEquipment.isPending
  // Asked once: if an address is already on file, this request doesn't need to repeat it.
  const needsAddress = isStaff ? customer != null && !customer.address : !user?.address

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    createRequest.mutate(
      {
        description,
        customer_id: isStaff ? Number(customerId) : undefined,
        equipment_id: equipmentId ? Number(equipmentId) : undefined,
        category_id: categoryId ? Number(categoryId) : undefined,
        address: needsAddress ? address : undefined,
      },
      { onSuccess: () => navigate(AFTER_SUBMIT[user!.role]) },
    )
  }

  return (
    <>
      {isStaff ? (
        <PageTitle
          title="New service request"
          description={
            user!.role === 'technician'
              ? "Raise a request for a customer. It's assigned to you."
              : 'Raise a request for a customer, then assign a technician from Service requests.'
          }
        />
      ) : (
        <PageTitle title="New complaint" description="Describe what's wrong and we'll route it to the right technician." />
      )}

      <Card className="max-w-xl">
        <CardContent>
          {createRequest.isError && (
            <Alert variant="destructive" className="mb-6" id="request-error">
              <AlertCircleIcon aria-hidden="true" />
              <AlertDescription>{createRequest.error.message}</AlertDescription>
            </Alert>
          )}
          {customers.isError && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircleIcon aria-hidden="true" />
              <AlertDescription>Couldn't load customers: {customers.error.message}</AlertDescription>
            </Alert>
          )}

          <form onSubmit={handleSubmit} aria-describedby={createRequest.isError ? 'request-error' : undefined}>
            <FieldGroup>
              {isStaff && (
                <Field>
                  <FieldLabel htmlFor="customer">Customer</FieldLabel>
                  <NativeSelect
                    id="customer"
                    required
                    autoFocus
                    value={customerId}
                    onChange={(e) => {
                      setCustomerId(e.target.value)
                      // Equipment belongs to one customer, so a previous pick no longer applies.
                      setEquipmentId('')
                    }}
                    disabled={customers.isPending}
                  >
                    <option value="">{customers.data?.length === 0 ? 'No customers registered yet' : 'Select a customer'}</option>
                    {customers.data?.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name} · {item.phone}
                      </option>
                    ))}
                  </NativeSelect>
                  {customer?.address && <FieldDescription>Service address: {customer.address}</FieldDescription>}
                </Field>
              )}

              <Field>
                <FieldLabel htmlFor="description">What's the problem?</FieldLabel>
                <Textarea
                  id="description"
                  rows={4}
                  required
                  autoFocus={!isStaff}
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
                  disabled={equipmentLoading || (equipment?.length ?? 0) === 0}
                >
                  <option value="">
                    {isStaff && !customer
                      ? 'Select a customer first'
                      : equipment?.length === 0
                        ? 'No equipment registered yet'
                        : "Not sure, or it's general"}
                  </option>
                  {equipment?.map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name} ({item.type})
                    </option>
                  ))}
                </NativeSelect>
                {!isStaff && equipment?.length === 0 && (
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
                  Category <span className="font-normal text-muted-foreground">(optional, AI picks one if you leave it)</span>
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
                  <FieldDescription id="address-hint">
                    {isStaff
                      ? "This customer has no address on file yet; it's saved to their profile."
                      : 'Asked once — saved for your future requests too.'}
                  </FieldDescription>
                </Field>
              )}

              <Button type="submit" size="lg" disabled={createRequest.isPending}>
                {createRequest.isPending && <Loader2Icon className="animate-spin" aria-hidden="true" />}
                {createRequest.isPending ? 'Submitting…' : isStaff ? 'Raise request' : 'Submit complaint'}
              </Button>
            </FieldGroup>
          </form>
        </CardContent>
      </Card>
    </>
  )
}
