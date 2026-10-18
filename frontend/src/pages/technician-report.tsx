import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { AlertCircleIcon, CheckIcon, Loader2Icon, MicIcon, SearchIcon, SquareIcon } from 'lucide-react'

import { PageTitle } from '@/components/dashboard'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Field, FieldDescription, FieldGroup, FieldLabel } from '@/components/ui/field'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { useCreateReport, useExtractReport, useReport } from '@/lib/reports'
import { SPEECH_TO_TEXT_SUPPORTED, useSpeechToText } from '@/lib/speech-to-text'

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

  const speech = useSpeechToText((phrase) => setReportText((text) => (text ? `${text} ${phrase}` : phrase)))

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
        description={`Request #${requestId}${readOnly ? '' : ' — describe what you found and did; type or dictate it.'}`}
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
                  {SPEECH_TO_TEXT_SUPPORTED && (
                    <Button type="button" variant="outline" size="sm" onClick={speech.toggle}>
                      {speech.listening ? <SquareIcon aria-hidden="true" /> : <MicIcon aria-hidden="true" />}
                      {speech.listening ? 'Stop dictating' : 'Dictate'}
                    </Button>
                  )}
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={reportText.trim().length < 10 || extract.isPending}
                    onClick={applyExtraction}
                  >
                    {extract.isPending ? <Loader2Icon className="animate-spin" aria-hidden="true" /> : <SearchIcon aria-hidden="true" />}
                    Extract details
                  </Button>
                </div>
              )}
              {!SPEECH_TO_TEXT_SUPPORTED && !readOnly && (
                <FieldDescription>Dictation isn't supported in this browser — try Chrome, or just type the report.</FieldDescription>
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
