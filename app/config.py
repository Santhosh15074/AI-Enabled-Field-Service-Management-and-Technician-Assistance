from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://postgres@localhost:5432/aitechnician"
    secret_key: str = "change-me"
    session_https_only: bool = False
    session_max_age_seconds: int = 8 * 60 * 60

    # Uploaded files (voice notes today). Kept outside the code; back this folder up with the database.
    media_dir: Path = ROOT / "media"

    # Speech-to-text for voice notes — see app.voice.transcribers. "local" runs Whisper on this
    # machine (faster-whisper); a hosted engine (Sarvam) can be added later behind the same setting.
    stt_engine: str = "local"
    # A faster-whisper model: a size ("base", "small", "medium", "large-v3") or a CTranslate2 model
    # on Hugging Face. Bigger is more accurate on Tamil and much slower on a CPU.
    stt_local_model: str = "small"
    # A language code such as "ta" forces that language. Empty (the default) detects it per
    # recording, which copes with mostly-English notes; forcing "ta" on those produced nonsense.
    stt_language: str = ""
    voice_note_max_bytes: int = 15 * 1024 * 1024
    voice_note_max_seconds: int = 5 * 60
    # Pick up voice notes left untranscribed when the server last stopped. Off in the tests.
    resume_voice_notes_on_startup: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
