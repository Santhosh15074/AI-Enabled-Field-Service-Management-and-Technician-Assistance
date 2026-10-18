import { useState, type FormEvent } from 'react'
import { useParams } from 'react-router-dom'
import { AlertCircleIcon, CheckIcon, Loader2Icon } from 'lucide-react'

import { PageTitle } from '@/components/dashboard'
import { RiskBadge } from '@/components/risk-badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Field, FieldDescription, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { NativeSelect } from '@/components/ui/native-select'
import { useRecordReadings } from '@/lib/requests'

const EMPTY = {
  quality_grade: 'M',
  air_temperature_k: '',
  process_temperature_k: '',
  rotational_speed_rpm: '',
  torque_nm: '',
  tool_wear_min: '',
}

export function TechnicianReadingsPage() {
  const { id } = useParams()
  const equipmentId = Number(id)
  const recordReadings = useRecordReadings(equipmentId)
  const [form, setForm] = useState(EMPTY)

  const update = (key: keyof typeof EMPTY) => (e: { target: { value: string } }) =>
    setForm((current) => ({ ...current, [key]: e.target.value }))

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    recordReadings.mutate({
      quality_grade: form.quality_grade,
      air_temperature_k: Number(form.air_temperature_k),
      process_temperature_k: Number(form.process_temperature_k),
      rotational_speed_rpm: Number(form.rotational_speed_rpm),
      torque_nm: Number(form.torque_nm),
      tool_wear_min: Number(form.tool_wear_min),
    })
  }

  return (
    <>
      <PageTitle title="Record equipment reading" description="Scored for failure risk as soon as you save it." />

      <Card className="max-w-xl">
        <CardContent>
          {recordReadings.isError && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircleIcon aria-hidden="true" />
              <AlertDescription>{recordReadings.error.message}</AlertDescription>
            </Alert>
          )}

          {recordReadings.isSuccess ? (
            <div className="flex flex-col items-start gap-3">
              <p className="text-sm">Reading saved.</p>
              <RiskBadge riskLevel={recordReadings.data.risk_level} />
              <Button variant="outline" size="sm" onClick={() => recordReadings.reset()}>
                Record another reading
              </Button>
            </div>
          ) : (
            <form onSubmit={handleSubmit}>
              <FieldGroup>
                <Field>
                  <FieldLabel htmlFor="quality-grade">Quality grade</FieldLabel>
                  <NativeSelect id="quality-grade" value={form.quality_grade} onChange={update('quality_grade')}>
                    <option value="L">L — low</option>
                    <option value="M">M — medium</option>
                    <option value="H">H — high</option>
                  </NativeSelect>
                  <FieldDescription>The equipment's manufacturing quality band, as labelled on it.</FieldDescription>
                </Field>

                <div className="grid gap-4 sm:grid-cols-2">
                  <Field>
                    <FieldLabel htmlFor="air-temp">Air temperature (K)</FieldLabel>
                    <Input
                      id="air-temp"
                      type="number"
                      step="0.1"
                      required
                      value={form.air_temperature_k}
                      onChange={update('air_temperature_k')}
                    />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="process-temp">Process temperature (K)</FieldLabel>
                    <Input
                      id="process-temp"
                      type="number"
                      step="0.1"
                      required
                      value={form.process_temperature_k}
                      onChange={update('process_temperature_k')}
                    />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="rpm">Rotational speed (rpm)</FieldLabel>
                    <Input
                      id="rpm"
                      type="number"
                      required
                      value={form.rotational_speed_rpm}
                      onChange={update('rotational_speed_rpm')}
                    />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="torque">Torque (Nm)</FieldLabel>
                    <Input id="torque" type="number" step="0.1" required value={form.torque_nm} onChange={update('torque_nm')} />
                  </Field>
                  <Field>
                    <FieldLabel htmlFor="tool-wear">Tool wear (min)</FieldLabel>
                    <Input
                      id="tool-wear"
                      type="number"
                      required
                      value={form.tool_wear_min}
                      onChange={update('tool_wear_min')}
                    />
                  </Field>
                </div>

                <Button type="submit" size="lg" disabled={recordReadings.isPending}>
                  {recordReadings.isPending ? <Loader2Icon className="animate-spin" aria-hidden="true" /> : <CheckIcon aria-hidden="true" />}
                  {recordReadings.isPending ? 'Scoring…' : 'Save reading'}
                </Button>
              </FieldGroup>
            </form>
          )}
        </CardContent>
      </Card>
    </>
  )
}
