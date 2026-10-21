"""Transcribing voice notes in the background, after the upload has already been answered.

A transcription takes seconds to minutes on a CPU, far too long to keep a technician's phone
waiting, so uploads only store the audio and queue the note (FastAPI BackgroundTasks); the phone
polls for the result. Notes are transcribed one at a time — the model already uses every core, so
running two at once would only make both slower.

Each run opens its own database session from the factory it's given, because the request's own
session is closed by the time this runs.
"""

import logging
import threading
from collections.abc import Callable
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import VoiceNote, VoiceNoteStatus
from app.voice.audio import SAMPLE_RATE, AudioError, decode
from app.voice.transcribers import get_transcriber

logger = logging.getLogger(__name__)

_one_at_a_time = threading.Lock()

SessionFactory = Callable[[], Session]


def transcribe_note(session_factory: SessionFactory, note_id: int) -> None:
    with _one_at_a_time, session_factory() as db:
        note = db.get(VoiceNote, note_id)
        if note is None or note.status not in (VoiceNoteStatus.PENDING, VoiceNoteStatus.TRANSCRIBING):
            return  # deleted, or already handled by an earlier run
        note.status = VoiceNoteStatus.TRANSCRIBING
        note.error = None
        db.commit()

        settings = get_settings()
        try:
            audio = decode(settings.media_dir / note.audio_path)
            note.duration_seconds = round(len(audio) / SAMPLE_RATE, 1)
            if note.duration_seconds > settings.voice_note_max_seconds:
                raise AudioError(
                    f"The recording is {note.duration_seconds / 60:.1f} minutes long; the limit is "
                    f"{settings.voice_note_max_seconds // 60} minutes. Record the job in shorter parts."
                )
            transcript = get_transcriber().transcribe(audio)
            if not transcript.text:
                raise AudioError("No speech was heard in the recording.")
        except AudioError as error:
            _fail(db, note, str(error))
            return
        except Exception:
            logger.exception("Transcribing voice note %s failed", note.id)
            _fail(db, note, "Transcription failed on the server. Try again, or type the report.")
            return

        note.status = VoiceNoteStatus.DONE
        note.transcript = transcript.text
        note.engine = transcript.engine
        note.transcribed_at = datetime.now(UTC)
        db.commit()


def _fail(db: Session, note: VoiceNote, message: str) -> None:
    note.status = VoiceNoteStatus.FAILED
    note.error = message
    db.commit()


def resume_unfinished(session_factory: SessionFactory) -> None:
    """Notes left pending or half-done when the server last stopped. Run once at startup, on its own thread."""
    with session_factory() as db:
        ids = db.scalars(
            select(VoiceNote.id)
            .where(VoiceNote.status.in_((VoiceNoteStatus.PENDING, VoiceNoteStatus.TRANSCRIBING)))
            .order_by(VoiceNote.id)
        ).all()
    for note_id in ids:
        transcribe_note(session_factory, note_id)
