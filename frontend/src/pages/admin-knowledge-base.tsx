import { useState, type FormEvent } from 'react'
import { AlertCircleIcon, BookOpenIcon, Loader2Icon, PencilIcon, PlusIcon, Trash2Icon } from 'lucide-react'
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
import { Textarea } from '@/components/ui/textarea'
import { useCategories } from '@/lib/requests'
import {
  useCreateKnowledgeBaseEntry,
  useDeleteKnowledgeBaseEntry,
  useKnowledgeBase,
  useUpdateKnowledgeBaseEntry,
  type KnowledgeBaseEntry,
} from '@/lib/knowledge-base'

const EMPTY = { category_id: '', equipment_type: '', issue_pattern: '', suggested_fix: '' }

export function AdminKnowledgeBasePage() {
  const entries = useKnowledgeBase()
  const categories = useCategories()
  const createEntry = useCreateKnowledgeBaseEntry()
  const updateEntry = useUpdateKnowledgeBaseEntry()
  const deleteEntry = useDeleteKnowledgeBaseEntry()
  const [open, setOpen] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form, setForm] = useState(EMPTY)

  const saving = editingId === null ? createEntry : updateEntry
  const update = (key: keyof typeof EMPTY) => (e: { target: { value: string } }) =>
    setForm((current) => ({ ...current, [key]: e.target.value }))

  function startCreate() {
    setForm(EMPTY)
    setEditingId(null)
    setOpen(true)
  }

  function startEdit(entry: KnowledgeBaseEntry) {
    setForm({
      category_id: String(entry.category_id),
      equipment_type: entry.equipment_type ?? '',
      issue_pattern: entry.issue_pattern,
      suggested_fix: entry.suggested_fix,
    })
    setEditingId(entry.id)
    setOpen(true)
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const body = {
      category_id: Number(form.category_id),
      equipment_type: form.equipment_type || undefined,
      issue_pattern: form.issue_pattern,
      suggested_fix: form.suggested_fix,
    }
    if (editingId === null) {
      createEntry.mutate(body, { onSuccess: () => setOpen(false) })
    } else {
      updateEntry.mutate({ id: editingId, ...body }, { onSuccess: () => setOpen(false) })
    }
  }

  function remove(id: number) {
    deleteEntry.mutate(id, { onError: (error) => toast.error(error.message) })
  }

  return (
    <>
      <PageTitle
        title="Knowledge base"
        description="Matched against a complaint's description by meaning — see the troubleshooting assistant."
        action={
          !open && (
            <Button onClick={startCreate}>
              <PlusIcon aria-hidden="true" />
              Add entry
            </Button>
          )
        }
      />

      {open && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle>{editingId === null ? 'Add entry' : 'Edit entry'}</CardTitle>
            <CardDescription>A short issue description and the fix to suggest for it.</CardDescription>
          </CardHeader>
          <CardContent>
            {saving.isError && (
              <Alert variant="destructive" className="mb-4" id="kb-error">
                <AlertCircleIcon aria-hidden="true" />
                <AlertDescription>{saving.error.message}</AlertDescription>
              </Alert>
            )}
            <form onSubmit={handleSubmit} aria-describedby={saving.isError ? 'kb-error' : undefined}>
              <FieldGroup>
                <div className="grid gap-4 sm:grid-cols-2">
                  <Field>
                    <FieldLabel htmlFor="kb-category">Category</FieldLabel>
                    <NativeSelect id="kb-category" required value={form.category_id} onChange={update('category_id')}>
                      <option value="" disabled>
                        Select a category
                      </option>
                      {categories.data?.map((category) => (
                        <option key={category.id} value={category.id}>
                          {category.category_name}
                        </option>
                      ))}
                    </NativeSelect>
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="kb-equipment-type">
                      Equipment type <span className="font-normal text-muted-foreground">(optional)</span>
                    </FieldLabel>
                    <Input id="kb-equipment-type" value={form.equipment_type} onChange={update('equipment_type')} />
                  </Field>
                </div>
                <Field>
                  <FieldLabel htmlFor="kb-issue">Issue</FieldLabel>
                  <Textarea id="kb-issue" rows={2} required value={form.issue_pattern} onChange={update('issue_pattern')} />
                </Field>
                <Field>
                  <FieldLabel htmlFor="kb-fix">Suggested fix</FieldLabel>
                  <Textarea id="kb-fix" rows={3} required value={form.suggested_fix} onChange={update('suggested_fix')} />
                </Field>
                <div className="flex gap-2">
                  <Button type="submit" disabled={saving.isPending}>
                    {saving.isPending && <Loader2Icon className="animate-spin" aria-hidden="true" />}
                    {saving.isPending ? 'Saving…' : editingId === null ? 'Add entry' : 'Save changes'}
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

      {entries.isPending ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-20 rounded-xl" />
          ))}
        </div>
      ) : entries.isError ? (
        <Alert variant="destructive">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>Couldn't load the knowledge base: {entries.error.message}</AlertDescription>
        </Alert>
      ) : entries.data.length === 0 ? (
        <Card>
          <CardContent>
            <EmptyState icon={BookOpenIcon} title="No entries yet" description="Add your first troubleshooting entry above." />
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardContent className="divide-y p-0">
            {entries.data.map((entry) => (
              <div key={entry.id} className="flex items-start justify-between gap-4 px-4 py-3 sm:px-5">
                <div className="min-w-0">
                  <div className="flex flex-wrap items-center gap-2">
                    <Badge variant="outline" className="font-normal">
                      {entry.category_name}
                    </Badge>
                    {entry.equipment_type && <span className="text-xs text-muted-foreground">{entry.equipment_type}</span>}
                  </div>
                  <p className="mt-1.5 text-sm font-medium">{entry.issue_pattern}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{entry.suggested_fix}</p>
                </div>
                <div className="flex shrink-0 gap-1">
                  <Button variant="ghost" size="icon" aria-label="Edit entry" onClick={() => startEdit(entry)}>
                    <PencilIcon aria-hidden="true" />
                  </Button>
                  <Button variant="ghost" size="icon" aria-label="Delete entry" onClick={() => remove(entry.id)}>
                    <Trash2Icon aria-hidden="true" />
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </>
  )
}
