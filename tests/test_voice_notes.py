"""Voice notes: uploading a recording, transcribing it in the background, and who can reach it.

The speech model is swapped for a stand-in (FakeTranscriber), so these tests are about the
plumbing: storage, retries, statuses, errors and permissions. Real recordings are decoded for
real, from small WAV files made here.
"""

import io
import math
import wave

import pytest
from sqlalchemy import func, select

from app.config import get_settings
from app.models import Role, ServiceRequest, VoiceNote
from app.voice import processing
from app.voice.transcribers import Transcript
from tests.conftest import log_in


def make_wav(seconds: float = 1.0, rate: int = 8000) -> bytes:
    """A quiet tone, as WAV bytes: enough for the decoder to have real samples to read."""
    frames = b"".join(
        int(3000 * math.sin(2 * math.pi * 440 * n / rate)).to_bytes(2, "little", signed=True)
        for n in range(int(seconds * rate))
    )
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as out:
        out.setnchannels(1)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(frames)
    return buffer.getvalue()


class FakeTranscriber:
    name = "fake"

    def __init__(self):
        self.text = "compressor capacitor maathitten"
        self.error: Exception | None = None
        self.calls = 0

    def transcribe(self, audio):
        self.calls += 1
        if self.error:
            raise self.error
        return Transcript(text=self.text, engine="fake:test-model")


@pytest.fixture
def transcriber(monkeypatch):
    fake = FakeTranscriber()
    monkeypatch.setattr(processing, "get_transcriber", lambda: fake)
    return fake


@pytest.fixture
def technician(make_user):
    return make_user(Role.TECHNICIAN)


@pytest.fixture
def job(db_session, make_user, technician):
    customer = make_user(Role.CUSTOMER, email=None)
    request = ServiceRequest(customer_id=customer.customer.id, technician_id=technician.technician.id, description="Not cooling.")
    db_session.add(request)
    db_session.commit()
    return request


def upload(client, job_id, data=None, client_id="rec-0000000001", content_type="audio/wav"):
    return client.post(
        f"/api/requests/{job_id}/voice-notes",
        data={"client_id": client_id},
        files={"audio": ("note", data if data is not None else make_wav(), content_type)},
    )


def stored_files():
    return [path for path in get_settings().media_dir.rglob("*") if path.is_file()]


class TestUploadAndTranscribe:
    def test_upload_is_stored_then_transcribed_in_the_background(self, client, technician, job, transcriber):
        log_in(client, technician.email)

        response = upload(client, job.id)

        assert response.status_code == 201
        assert response.json()["status"] == "pending"  # answered before transcription ran
        note = client.get(f"/api/voice-notes/{response.json()['id']}").json()
        assert note["status"] == "done"
        assert note["transcript"] == "compressor capacitor maathitten"
        assert note["engine"] == "fake:test-model"
        assert note["duration_seconds"] == pytest.approx(1.0, abs=0.1)
        assert len(stored_files()) == 1

    def test_the_browser_s_codec_suffix_is_accepted(self, client, technician, job, transcriber):
        log_in(client, technician.email)

        assert upload(client, job.id, content_type="audio/webm;codecs=opus").status_code == 201

    def test_a_retried_upload_is_stored_once(self, client, db_session, technician, job, transcriber):
        log_in(client, technician.email)

        first = upload(client, job.id)
        second = upload(client, job.id)

        assert (first.status_code, second.status_code) == (201, 200)
        assert first.json()["id"] == second.json()["id"]
        assert db_session.scalar(select(func.count(VoiceNote.id))) == 1
        assert len(stored_files()) == 1
        assert transcriber.calls == 1

    def test_the_same_recording_cannot_move_to_another_job(self, client, db_session, technician, job, transcriber):
        other_job = ServiceRequest(customer_id=job.customer_id, technician_id=job.technician_id, description="Noisy.")
        db_session.add(other_job)
        db_session.commit()
        log_in(client, technician.email)
        upload(client, job.id)

        assert upload(client, other_job.id).status_code == 400

    def test_notes_are_listed_per_job(self, client, technician, job, transcriber):
        log_in(client, technician.email)
        upload(client, job.id, client_id="rec-0000000001")
        upload(client, job.id, client_id="rec-0000000002")

        notes = client.get(f"/api/requests/{job.id}/voice-notes").json()

        assert [n["client_id"] for n in notes] == ["rec-0000000001", "rec-0000000002"]

    def test_the_original_audio_can_be_played_back(self, client, technician, job, transcriber):
        log_in(client, technician.email)
        note_id = upload(client, job.id).json()["id"]

        response = client.get(f"/api/voice-notes/{note_id}/audio")

        assert response.status_code == 200
        assert response.content == make_wav()


class TestRejectedUploads:
    @pytest.mark.parametrize(
        ("kwargs", "status"),
        [
            ({"content_type": "image/png"}, 400),
            ({"content_type": "application/octet-stream"}, 400),
            ({"data": b""}, 400),
            ({"client_id": "short"}, 400),
            ({"client_id": "has spaces in it"}, 400),
        ],
    )
    def test_bad_uploads_store_nothing(self, client, technician, job, transcriber, kwargs, status):
        log_in(client, technician.email)

        assert upload(client, job.id, **kwargs).status_code == status
        assert stored_files() == []

    def test_too_large(self, client, technician, job, transcriber, monkeypatch):
        monkeypatch.setattr(get_settings(), "voice_note_max_bytes", 1000)
        log_in(client, technician.email)

        response = upload(client, job.id)

        assert response.status_code == 413
        assert stored_files() == []


class TestFailures:
    def test_audio_that_cannot_be_decoded(self, client, technician, job, transcriber):
        log_in(client, technician.email)

        note_id = upload(client, job.id, data=b"definitely not audio", content_type="audio/webm").json()["id"]

        note = client.get(f"/api/voice-notes/{note_id}").json()
        assert note["status"] == "failed"
        assert "couldn't be read" in note["error"]
        assert transcriber.calls == 0

    def test_too_long(self, client, technician, job, transcriber, monkeypatch):
        monkeypatch.setattr(get_settings(), "voice_note_max_seconds", 0)
        log_in(client, technician.email)

        note = client.get(f"/api/voice-notes/{upload(client, job.id).json()['id']}").json()

        assert note["status"] == "failed"
        assert "shorter parts" in note["error"]

    def test_no_speech_heard(self, client, technician, job, transcriber):
        transcriber.text = ""
        log_in(client, technician.email)

        note = client.get(f"/api/voice-notes/{upload(client, job.id).json()['id']}").json()

        assert (note["status"], note["error"]) == ("failed", "No speech was heard in the recording.")

    def test_engine_crash_then_retry(self, client, technician, job, transcriber):
        transcriber.error = RuntimeError("model exploded")
        log_in(client, technician.email)
        note_id = upload(client, job.id).json()["id"]

        failed = client.get(f"/api/voice-notes/{note_id}").json()
        assert failed["status"] == "failed"
        assert "model exploded" not in failed["error"]  # internals stay in the server log

        transcriber.error = None
        assert client.post(f"/api/voice-notes/{note_id}/retry").status_code == 200

        assert client.get(f"/api/voice-notes/{note_id}").json()["status"] == "done"

    def test_only_failed_notes_can_be_retried(self, client, technician, job, transcriber):
        log_in(client, technician.email)
        note_id = upload(client, job.id).json()["id"]

        assert client.post(f"/api/voice-notes/{note_id}/retry").status_code == 400

    def test_notes_left_unfinished_are_picked_up_after_a_restart(self, db_session, engine, technician, job, transcriber):
        path = get_settings().media_dir / "voice" / "left-over.wav"
        path.parent.mkdir(parents=True)
        path.write_bytes(make_wav())
        for status in ("pending", "transcribing"):
            db_session.add(
                VoiceNote(
                    request_id=job.id, client_id=f"rec-{status}-01", audio_path="voice/left-over.wav",
                    content_type="audio/wav", size_bytes=path.stat().st_size, status=status,
                )
            )
        db_session.commit()

        from sqlalchemy.orm import sessionmaker

        processing.resume_unfinished(sessionmaker(bind=engine, expire_on_commit=False))

        db_session.expire_all()
        assert set(db_session.scalars(select(VoiceNote.status))) == {"done"}


class TestWhoCanReachANote:
    def test_a_technician_not_on_the_job(self, client, make_user, job, transcriber):
        stranger = make_user(Role.TECHNICIAN, email="other@example.com")
        log_in(client, stranger.email)

        assert upload(client, job.id).status_code == 403

    def test_another_technician_cannot_read_the_note(self, client, make_user, technician, job, transcriber):
        log_in(client, technician.email)
        note_id = upload(client, job.id).json()["id"]
        stranger = make_user(Role.TECHNICIAN, email="other@example.com")
        log_in(client, stranger.email)

        assert client.get(f"/api/voice-notes/{note_id}").status_code == 404
        assert client.get(f"/api/voice-notes/{note_id}/audio").status_code == 404

    def test_the_shop_s_owner_can(self, client, make_user, technician, job, transcriber):
        log_in(client, technician.email)
        note_id = upload(client, job.id).json()["id"]
        log_in(client, make_user(Role.ADMIN).email)

        assert client.get(f"/api/voice-notes/{note_id}").status_code == 200

    def test_another_shop_s_owner_cannot(self, client, make_user, make_shop, technician, job, transcriber):
        log_in(client, technician.email)
        note_id = upload(client, job.id).json()["id"]
        other_owner = make_user(Role.ADMIN, email="owner@other.example", shop_id=make_shop().id)
        log_in(client, other_owner.email)

        assert client.get(f"/api/voice-notes/{note_id}").status_code == 404
        assert client.get(f"/api/requests/{job.id}/voice-notes").status_code == 404
        assert upload(client, job.id, client_id="rec-0000000009").status_code == 404

    def test_customers_cannot(self, client, db_session, technician, job, transcriber):
        customer = db_session.get(ServiceRequest, job.id).customer.user
        log_in(client, customer.customer.phone)

        assert upload(client, job.id).status_code == 403
        assert client.get(f"/api/requests/{job.id}/voice-notes").status_code == 403
