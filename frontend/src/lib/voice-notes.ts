import { useCallback, useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { api } from '@/lib/api'
import { listOutbox, newClientId, removeFromOutbox, saveToOutbox, type OutboxItem } from '@/lib/voice-outbox'

export type VoiceNoteStatus = 'pending' | 'transcribing' | 'done' | 'failed'

export type VoiceNote = {
  id: number
  request_id: number
  client_id: string
  status: VoiceNoteStatus
  transcript: string | null
  error: string | null
  duration_seconds: number | null
  engine: string | null
  created_at: string
  transcribed_at: string | null
}

// Matches Settings.voice_note_max_seconds on the server.
export const MAX_RECORDING_SECONDS = 5 * 60
// How often to try the outbox again while recordings are waiting for a signal.
const RETRY_MS = 15_000
const POLL_MS = 3_000

// In order of preference: Chrome on Android records WebM/Opus, Safari on iPhone only MP4/AAC.
const MIME_TYPES = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', 'audio/ogg;codecs=opus']

/** Microphone recording needs MediaRecorder and a secure page (HTTPS, or localhost). */
export const RECORDING_SUPPORTED =
  typeof window !== 'undefined' &&
  window.isSecureContext &&
  typeof MediaRecorder !== 'undefined' &&
  !!navigator.mediaDevices?.getUserMedia

const notesKey = (requestId: number) => ['requests', requestId, 'voice-notes']

/** Records from the microphone; hands the finished recording to onRecorded. */
export function useRecorder(onRecorded: (blob: Blob) => void) {
  const [recording, setRecording] = useState(false)
  // Between pressing Record and the browser's "allow microphone?" answer.
  const [starting, setStarting] = useState(false)
  const [seconds, setSeconds] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const recorderRef = useRef<MediaRecorder | null>(null)
  const onRecordedRef = useRef(onRecorded)
  useEffect(() => {
    onRecordedRef.current = onRecorded
  }, [onRecorded])

  const stop = useCallback(() => {
    if (recorderRef.current?.state === 'recording') recorderRef.current.stop()
  }, [])

  // Stops on unmount too, so leaving the page never leaves the microphone on.
  useEffect(() => stop, [stop])

  useEffect(() => {
    if (!recording) return
    const started = Date.now()
    const timer = window.setInterval(() => {
      const elapsed = Math.floor((Date.now() - started) / 1000)
      setSeconds(elapsed)
      if (elapsed >= MAX_RECORDING_SECONDS) stop()
    }, 250)
    return () => window.clearInterval(timer)
  }, [recording, stop])

  async function start() {
    if (starting || recording) return
    setError(null)
    setStarting(true)
    let stream: MediaStream
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
    } catch {
      setError('Allow the microphone for this site to record. Check the browser’s site settings.')
      return
    } finally {
      setStarting(false)
    }
    const mimeType = MIME_TYPES.find((type) => MediaRecorder.isTypeSupported(type))
    const recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined)
    const chunks: Blob[] = []
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunks.push(event.data)
    }
    recorder.onstop = () => {
      stream.getTracks().forEach((track) => track.stop())
      setRecording(false)
      const blob = new Blob(chunks, { type: recorder.mimeType || mimeType || 'audio/webm' })
      if (blob.size > 0) onRecordedRef.current(blob)
    }
    recorderRef.current = recorder
    // Collected every second, so a crash mid-recording loses at most the last second.
    recorder.start(1000)
    setSeconds(0)
    setRecording(true)
  }

  return { recording, starting, seconds, error, start, stop }
}

async function uploadOne(item: OutboxItem): Promise<'done' | 'retry' | { rejected: string }> {
  const form = new FormData()
  form.append('client_id', item.clientId)
  const extension = item.blob.type.includes('mp4') ? 'm4a' : item.blob.type.includes('ogg') ? 'ogg' : 'webm'
  form.append('audio', item.blob, `voice.${extension}`)
  let response: Response
  try {
    response = await fetch(`/api/requests/${item.requestId}/voice-notes`, {
      method: 'POST',
      body: form,
      credentials: 'same-origin',
    })
  } catch {
    return 'retry' // no signal
  }
  if (response.ok) return 'done'
  // Logged out, overloaded or a server fault: worth trying again later. Anything else won't change.
  if (response.status === 401 || response.status === 408 || response.status === 429 || response.status >= 500) {
    return 'retry'
  }
  const data = await response.json().catch(() => undefined)
  return { rejected: typeof data?.detail === 'string' ? data.detail : 'The server refused this recording.' }
}

/** A job's voice notes: those still on the phone waiting to upload, and those on the server. */
export function useVoiceNotes(requestId: number) {
  const queryClient = useQueryClient()
  const [outbox, setOutbox] = useState<OutboxItem[]>([])
  const [uploading, setUploading] = useState(false)
  const flushing = useRef(false)

  const notes = useQuery({
    queryKey: notesKey(requestId),
    queryFn: () => api<VoiceNote[]>(`/api/requests/${requestId}/voice-notes`),
    // Poll only while something is still being transcribed.
    refetchInterval: (query) =>
      query.state.data?.some((note) => note.status === 'pending' || note.status === 'transcribing') ? POLL_MS : false,
  })

  const refreshOutbox = useCallback(async () => setOutbox(await listOutbox(requestId)), [requestId])

  const flush = useCallback(async () => {
    if (flushing.current) return
    flushing.current = true
    setUploading(true)
    try {
      for (const item of await listOutbox(requestId)) {
        if (item.rejected) continue
        const result = await uploadOne(item)
        if (result === 'retry') break // still offline; the rest would fail too
        if (result === 'done') await removeFromOutbox(item.clientId)
        else await saveToOutbox({ ...item, rejected: result.rejected })
      }
    } finally {
      flushing.current = false
      setUploading(false)
      await refreshOutbox()
      queryClient.invalidateQueries({ queryKey: notesKey(requestId) })
    }
  }, [requestId, queryClient, refreshOutbox])

  // Try on opening the page, whenever the phone gets a connection back, and every few seconds
  // while recordings are waiting.
  useEffect(() => {
    void flush()
    window.addEventListener('online', flush)
    return () => window.removeEventListener('online', flush)
  }, [flush])

  const waiting = outbox.some((item) => !item.rejected)
  useEffect(() => {
    if (!waiting) return
    const timer = window.setInterval(flush, RETRY_MS)
    return () => window.clearInterval(timer)
  }, [waiting, flush])

  async function addRecording(blob: Blob) {
    await saveToOutbox({ clientId: newClientId(), requestId, blob, createdAt: Date.now() })
    await refreshOutbox()
    await flush()
  }

  async function discard(clientId: string) {
    await removeFromOutbox(clientId)
    await refreshOutbox()
  }

  return { notes, outbox, uploading, addRecording, discard }
}

export function useRetryVoiceNote(requestId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (noteId: number) => api<VoiceNote>(`/api/voice-notes/${noteId}/retry`, { method: 'POST' }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: notesKey(requestId) }),
  })
}

export function formatSeconds(total: number): string {
  const minutes = Math.floor(total / 60)
  return `${minutes}:${String(Math.floor(total % 60)).padStart(2, '0')}`
}
