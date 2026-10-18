import { useEffect, useRef, useState } from 'react'

// The Web Speech API has no official TypeScript lib yet and is vendor-prefixed in Chromium.
type SpeechRecognitionLike = {
  continuous: boolean
  interimResults: boolean
  lang: string
  onresult: ((event: { resultIndex: number; results: ArrayLike<ArrayLike<{ transcript: string }> & { isFinal: boolean }> }) => void) | null
  onerror: (() => void) | null
  onend: (() => void) | null
  start(): void
  stop(): void
}

function getSpeechRecognition(): (new () => SpeechRecognitionLike) | null {
  const w = window as unknown as Record<string, unknown>
  return (w.SpeechRecognition ?? w.webkitSpeechRecognition ?? null) as (new () => SpeechRecognitionLike) | null
}

export const SPEECH_TO_TEXT_SUPPORTED = typeof window !== 'undefined' && getSpeechRecognition() !== null

/** Dictation for a report: appends each final phrase to whatever's already in the field, rather
 * than replacing it, so a technician can pause, review, and keep going. Chrome-only today — see
 * SPEECH_TO_TEXT_SUPPORTED, which callers should check before showing a mic button at all. */
export function useSpeechToText(onPhrase: (text: string) => void) {
  const [listening, setListening] = useState(false)
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null)
  const onPhraseRef = useRef(onPhrase)
  onPhraseRef.current = onPhrase

  useEffect(() => {
    return () => recognitionRef.current?.stop()
  }, [])

  function toggle() {
    if (listening) {
      recognitionRef.current?.stop()
      return
    }
    const SpeechRecognition = getSpeechRecognition()
    if (!SpeechRecognition) return

    const recognition = new SpeechRecognition()
    recognition.continuous = true
    recognition.interimResults = false
    recognition.lang = 'en-IN'
    recognition.onresult = (event) => {
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i]
        if (result.isFinal) onPhraseRef.current(result[0].transcript.trim())
      }
    }
    recognition.onerror = () => setListening(false)
    recognition.onend = () => setListening(false)
    recognitionRef.current = recognition
    recognition.start()
    setListening(true)
  }

  return { listening, toggle }
}
