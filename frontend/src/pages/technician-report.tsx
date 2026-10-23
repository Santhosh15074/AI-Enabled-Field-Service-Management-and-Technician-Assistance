import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { AlertCircleIcon, CheckIcon, Loader2Icon, SparklesIcon } from 'lucide-react'

import { PageTitle } from '@/components/dashboard'
import { VoiceNotesPanel } from '@/components/voice-notes-panel'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Field, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { useCreateReport, useExtractReport, useReport } from '@/lib/reports'

export function TechnicianReportPage() {
  const { id } = useParams()
  const requestId = Number(id)
  const navigate = useNavigate()
  const existing = useReport(requestId)
  const extract = useExtractReport(requestId)
  const createReport = useCreateReport(requestId)

  const [reportText, setReportText] = useState('')
  const [issue, setIssue] = useState('')
  const [actionTaken, setActionTaken] = useState('')
  const [partsUsed, setPartsUsed] = useState('')
  const [timeSpent, setTimeSpent] = useState('')

  const addToReport = (more: string) => setReportText((text) => (text.trim() ? `${text.trim()}
${more}` : more))

  function applyExtraction() {
    extract.mutate(reportText, {
      onSuccess: (fields) => {
        setIssue(fields.issue ?? '')
        setActionTaken(fields.action_taken ?? '')
        setPartsUsed(fields.parts_used ?? '')
        setTimeSpent(fields.time_spent_minutes?.toString() ?? '')
      },
    })
  }

  function handleSubmit() {
    createReport.mutate(
      {
        report_text: reportText,
        issue: issue || null,
        action_taken: actionTaken || null,
        parts_used: partsUsed || null,
        time_spent_minutes: timeSpent ? Number(timeSpent) : null,
      },
      { onSuccess: () => navigate('/technician/jobs') },
    )
  }

  useEffect(() => {
    if (existing.data) {
      setReportText(existing.data.report_text)
      setIssue(existing.data.issue ?? '')
      setActionTaken(existing.data.action_taken ?? '')
      setPartsUsed(existing.data.parts_used ?? '')
      setTimeSpent(existing.data.time_spent_minutes?.toString() ?? '')
    }
  }, [existing.data])

  const readOnly = Boolean(existing.data)

  return (
    <>
      <PageTitle
        title={readOnly ? 'Service report' : 'Write a service report'}
        description={`Request #${requestId}${readOnly ? '' : ' — record what you found and did, or type it.'}`}
      />

      <Card className="max-w-2xl">
        <CardContent>
          {createReport.isError && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircleIcon aria-hidden="true" />
              <AlertDescription>{createReport.error.message}</AlertDescription>
            </Alert>
          )}

          <FieldGroup>
            {!readOnly && (
              <Field>
                <FieldLabel>Voice notes</FieldLabel>
                <VoiceNotesPanel requestId={requestId} onUseTranscript={addToReport} />
              </Field>
            )}

            <Field>
              <FieldLabel htmlFor="report-text">Report</FieldLabel>
              <Textarea
                id="report-text"
                rows={6}
                readOnly={readOnly}
                placeholder="Found a seized bearing on the motor shaft. Replaced the bearing and tested the unit under load. Took about 45 minutes."
                value={reportText}
                onChange={(e) => setReportText(e.target.value)}
              />
              {!readOnly && (
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={reportText.trim().length < 10 || extract.isPending}
                    onClick={applyExtraction}
                  >
                    {extract.isPending ? <Loader2Icon className="animate-spin" aria-hidden="true" /> : <SparklesIcon aria-hidden="true" />}
                    {extract.isPending ? 'Filling the report…' : 'Fill the report with AI'}
                  </Button>
                </div>
              )}
              {!readOnly && extract.data && (
                <p className="text-xs text-muted-foreground">
                  {extract.data.source === 'ai'
                    ? 'Filled in by AI from your notes, in English. Check each field before saving.'
                    : 'AI was unavailable, so the fields were filled by keyword rules. Check each field before saving.'}
                </p>
              )}
            </Field>

            <Field>
              <FieldLabel htmlFor="issue">Issue found</FieldLabel>
              <Textarea id="issue" rows={2} readOnly={readOnly} value={issue} onChange={(e) => setIssue(e.target.value)} />
            </Field>

            <Field>
              <FieldLabel htmlFor="action-taken">Action taken</FieldLabel>
              <Textarea
                id="action-taken"
                rows={2}
                readOnly={readOnly}
                value={actionTaken}
                onChange={(e) => setActionTaken(e.target.value)}
              />
            </Field>

            <div className="grid gap-4 sm:grid-cols-2">
              <Field>
                <FieldLabel htmlFor="parts-used">Parts used</FieldLabel>
                <Input id="parts-used" readOnly={readOnly} value={partsUsed} onChange={(e) => setPartsUsed(e.target.value)} />
              </Field>
              <Field>
                <FieldLabel htmlFor="time-spent">Time spent (minutes)</FieldLabel>
                <Input
                  id="time-spent"
                  type="number"
                  min={0}
                  readOnly={readOnly}
                  value={timeSpent}
                  onChange={(e) => setTimeSpent(e.target.value)}
                />
              </Field>
            </div>

            {!readOnly && (
              <Button
                size="lg"
                disabled={reportText.trim().length === 0 || createReport.isPending}
                onClick={handleSubmit}
              >
                {createReport.isPending ? <Loader2Icon className="animate-spin" aria-hidden="true" /> : <CheckIcon aria-hidden="true" />}
                {createReport.isPending ? 'Saving…' : 'Save report'}
              </Button>
            )}
          </FieldGroup>
        </CardContent>
      </Card>
    </>
  )
}
