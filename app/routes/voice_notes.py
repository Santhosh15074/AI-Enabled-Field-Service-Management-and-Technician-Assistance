"""Voice notes: a technician records what they did, in Tamil, English or both, and the server
turns it into text for the service report.

Uploading only stores the audio; transcription happens afterwards in the background (see
app.voice.processing), and the phone polls GET /api/voice-notes/{id} until it's done. Uploads are
safe to retry: the phone sends the same client_id each time, so a recording that was sent twice
over a weak connection is still stored once.

Only the shop's own staff can reach a note — a technician only for jobs assigned to them, the same
rule as service reports (app.routes.service_reports.get_request_for). Customers never see the raw
audio or transcript; they get the checked report instead.
"""

import re
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database import get_db
from app.deps import require_role
from app.models import Role, User, VoiceNote, VoiceNoteStatus
from app.routes.service_reports import get_request_for
from app.schemas import VoiceNoteOut
from app.voice.processing import transcribe_note

router = APIRouter(tags=["voice notes"])

STAFF = (Role.ADMIN, Role.TECHNICIAN)
CLIENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]{8,64}$")
# What phones actually record, and the extension each is stored under. Decoding looks at the
# file's contents, not this, so a mislabelled upload still works; this only rejects non-audio.
EXTENSIONS = {
    "audio/webm": ".webm",
    "audio/ogg": ".ogg",
    "audio/mp4": ".m4a",
    "audio/x-m4a": ".m4a",
    "audio/aac": ".aac",
    "audio/mpeg": ".mp3",
    "audio/wav": ".wav",
    "audio/x-wav": ".wav",
}
CHUNK_BYTES = 1024 * 1024


def _session_factory(db: Session):
    # The background run outlives this request's session, so it opens its own on the same database.
    return sessionmaker(bind=db.get_bind(), autoflush=False, expire_on_commit=False)


def _get_note(db: Session, note_id: int, user: User) -> VoiceNote:
    note = db.get(VoiceNote, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="That voice note doesn't exist.")
    try:
        get_request_for(note.request_id, user, db)
    except HTTPException as error:
        # Another shop's note, or a job that isn't yours: indistinguishable from a missing one.
        raise HTTPException(status_code=404, detail="That voice note doesn't exist.") from error
    return note


@router.post("/api/requests/{request_id}/voice-notes", response_model=VoiceNoteOut, status_code=201)
async def upload_voice_note(
    request_id: int,
    response: Response,
    background: BackgroundTasks,
    audio: UploadFile = File(...),
    client_id: str = Form(...),
    user: User = Depends(require_role(*STAFF)),
    db: Session = Depends(get_db),
):
    request = get_request_for(request_id, user, db)
    if not CLIENT_ID_PATTERN.match(client_id):
        raise HTTPException(status_code=400, detail="The recording's id is invalid. Record it again.")

    existing = db.scalar(select(VoiceNote).where(VoiceNote.client_id == client_id))
    if existing is not None:
        return _already_uploaded(existing, request_id, response)

    content_type = (audio.content_type or "").split(";")[0].strip().lower()
    if content_type not in EXTENSIONS:
        raise HTTPException(status_code=400, detail="That file isn't a supported audio recording.")

    settings = get_settings()
    relative = f"voice/{request.customer.user.shop_id}/{uuid.uuid4().hex}{EXTENSIONS[content_type]}"
    path = settings.media_dir / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    size = 0
    try:
        with path.open("wb") as out:
            while chunk := await audio.read(CHUNK_BYTES):
                size += len(chunk)
                if size > settings.voice_note_max_bytes:
                    raise HTTPException(
                        status_code=413,
                        detail=f"The recording is over {settings.voice_note_max_bytes // (1024 * 1024)} MB. Record the job in shorter parts.",
                    )
                out.write(chunk)
        if size == 0:
            raise HTTPException(status_code=400, detail="The recording is empty.")
    except BaseException:
        path.unlink(missing_ok=True)
        raise

    note = VoiceNote(
        request_id=request.id,
        recorded_by=user.id,
        client_id=client_id,
        audio_path=relative,
        content_type=content_type,
        size_bytes=size,
        status=VoiceNoteStatus.PENDING,
    )
    db.add(note)
    try:
        db.commit()
    except IntegrityError:
        # The same recording arriving twice at once (a retry racing the original): keep the first.
        db.rollback()
        path.unlink(missing_ok=True)
        existing = db.scalar(select(VoiceNote).where(VoiceNote.client_id == client_id))
        return _already_uploaded(existing, request_id, response)

    background.add_task(transcribe_note, _session_factory(db), note.id)
    return note


def _already_uploaded(note: VoiceNote, request_id: int, response: Response) -> VoiceNote:
    if note.request_id != request_id:
        raise HTTPException(status_code=400, detail="This recording was already uploaded for another job.")
    response.status_code = 200
    return note


@router.get("/api/requests/{request_id}/voice-notes", response_model=list[VoiceNoteOut])
def list_voice_notes(request_id: int, user: User = Depends(require_role(*STAFF)), db: Session = Depends(get_db)):
    get_request_for(request_id, user, db)
    return db.scalars(
        select(VoiceNote).where(VoiceNote.request_id == request_id).order_by(VoiceNote.created_at, VoiceNote.id)
    ).all()


@router.get("/api/voice-notes/{note_id}", response_model=VoiceNoteOut)
def get_voice_note(note_id: int, user: User = Depends(require_role(*STAFF)), db: Session = Depends(get_db)):
    return _get_note(db, note_id, user)


@router.post("/api/voice-notes/{note_id}/retry", response_model=VoiceNoteOut)
def retry_voice_note(
    note_id: int,
    background: BackgroundTasks,
    user: User = Depends(require_role(*STAFF)),
    db: Session = Depends(get_db),
):
    note = _get_note(db, note_id, user)
    if note.status != VoiceNoteStatus.FAILED:
        raise HTTPException(status_code=400, detail="Only a failed transcription can be retried.")
    note.status = VoiceNoteStatus.PENDING
    note.error = None
    db.commit()
    background.add_task(transcribe_note, _session_factory(db), note.id)
    return note


@router.get("/api/voice-notes/{note_id}/audio")
def get_voice_note_audio(note_id: int, user: User = Depends(require_role(*STAFF)), db: Session = Depends(get_db)):
    """The original recording, so an owner can hear what was said when a transcript looks wrong."""
    note = _get_note(db, note_id, user)
    path = get_settings().media_dir / note.audio_path
    if not path.is_file():
        raise HTTPException(status_code=404, detail="The recording's audio file is missing.")
    return FileResponse(path, media_type=note.content_type)
