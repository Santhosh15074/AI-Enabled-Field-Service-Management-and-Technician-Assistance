import { toast } from 'sonner'
import { AlertCircleIcon, CloudOffIcon, Loader2Icon, MicIcon, PlusIcon, RotateCcwIcon, SquareIcon, Trash2Icon } from 'lucide-react'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import {
  formatSeconds,
  MAX_RECORDING_SECONDS,
  RECORDING_SUPPORTED,
  useRecorder,
  useRetryVoiceNote,
  useVoiceNotes,
  type VoiceNote,
} from '@/lib/voice-notes'
import type { OutboxItem } from '@/lib/voice-outbox'

/** Record the job in Tamil, English or both; each recording is uploaded (retrying until there's
 * signal) and transcribed on the server, then its text can be added to the report in one tap. */
export function VoiceNotesPanel({ requestId, onUseTranscript }: { requestId: number; onUseTranscript: (text: string) => void }) {
  const voice = useVoiceNotes(requestId)
  const recorder = useRecorder((blob) => void voice.addRecording(blob))
  const retry = useRetryVoiceNote(requestId)

  if (!RECORDING_SUPPORTED) {
    return (
      <p className="text-sm text-muted-foreground">
        Recording needs a secure (https) page and a current browser. Type the report instead, or open this page over https.
      </p>
    )
  }

  const notes = voice.notes.data ?? []
  const pending = voice.outbox

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        {recorder.recording ? (
          <Button type="button" variant="destructive" onClick={recorder.stop}>
            <SquareIcon aria-hidden="true" />
            Stop · {formatSeconds(recorder.seconds)}
          </Button>
        ) : (
          <Button type="button" onClick={recorder.start} disabled={recorder.starting}>
            {recorder.starting ? <Loader2Icon className="animate-spin" aria-hidden="true" /> : <MicIcon aria-hidden="true" />}
            {recorder.starting ? 'Waiting for the microphone…' : 'Record the job'}
          </Button>
        )}
        <span className="text-xs text-muted-foreground">
          {recorder.recording
            ? `Recording… stops by itself at ${formatSeconds(MAX_RECORDING_SECONDS)}.`
            : 'Tamil, English or both. Say what was wrong, what you did, the parts and the time.'}
        </span>
      </div>

      {recorder.error && (
        <Alert variant="destructive">
          <AlertCircleIcon aria-hidden="true" />
          <AlertDescription>{recorder.error}</AlertDescription>
        </Alert>
      )}

      {(pending.length > 0 || notes.length > 0) && (
        <ul className="divide-y rounded-lg border" aria-live="polite">
          {pending.map((item) => (
            <OutboxRow key={item.clientId} item={item} uploading={voice.uploading} onDiscard={() => void voice.discard(item.clientId)} />
          ))}
          {notes.map((note) => (
            <NoteRow
              key={note.id}
              note={note}
              onUse={() => note.transcript && onUseTranscript(note.transcript)}
              onRetry={() => retry.mutate(note.id, { onError: (error) => toast.error(error.message) })}
              retrying={retry.isPending && retry.variables === note.id}
            />
          ))}
        </ul>
      )}
    </div>
  )
}

function OutboxRow({ item, uploading, onDiscard }: { item: OutboxItem; uploading: boolean; onDiscard: () => void }) {
  return (
    <li className="flex items-center gap-3 px-3 py-2.5 text-sm">
      {item.rejected ? (
        <>
          <AlertCircleIcon className="size-4 shrink-0 text-destructive" aria-hidden="true" />
          <span className="flex-1 text-destructive">Not uploaded: {item.rejected}</span>
          <Button type="button" variant="ghost" size="sm" onClick={onDiscard}>
            <Trash2Icon aria-hidden="true" />
            Discard
          </Button>
        </>
      ) : uploading ? (
        <>
          <Loader2Icon className="size-4 shrink-0 animate-spin text-muted-foreground" aria-hidden="true" />
          <span className="flex-1 text-muted-foreground">Uploading…</span>
        </>
      ) : (
        <>
          <CloudOffIcon className="size-4 shrink-0 text-muted-foreground" aria-hidden="true" />
          <span className="flex-1 text-muted-foreground">Saved on this phone. It uploads by itself when there's signal.</span>
        </>
      )}
    </li>
  )
}

function NoteRow({
  note,
  onUse,
  onRetry,
  retrying,
}: {
  note: VoiceNote
  onUse: () => void
  onRetry: () => void
  retrying: boolean
}) {
  return (
    <li className="space-y-2 px-3 py-2.5 text-sm">
      <div className="flex items-center gap-3">
        {(note.status === 'pending' || note.status === 'transcribing') && (
          <>
            <Loader2Icon className="size-4 shrink-0 animate-spin text-muted-foreground" aria-hidden="true" />
            <span className="flex-1 text-muted-foreground">
              {note.status === 'pending' ? 'Uploaded. Waiting to be turned into text…' : 'Turning the recording into text…'}
            </span>
          </>
        )}
        {note.status === 'failed' && (
          <>
            <AlertCircleIcon className="size-4 shrink-0 text-destructive" aria-hidden="true" />
            <span className="flex-1 text-destructive">{note.error}</span>
            <Button type="button" variant="ghost" size="sm" onClick={onRetry} disabled={retrying}>
              <RotateCcwIcon aria-hidden="true" />
              Try again
            </Button>
          </>
        )}
        {note.status === 'done' && (
          <>
            <p className="flex-1 whitespace-pre-wrap">{note.transcript}</p>
            <Button type="button" variant="outline" size="sm" onClick={onUse}>
              <PlusIcon aria-hidden="true" />
              Add to report
            </Button>
          </>
        )}
      </div>
      <audio controls preload="none" src={`/api/voice-notes/${note.id}/audio`} className="h-8 w-full">
        <track kind="captions" />
      </audio>
    </li>
  )
}
