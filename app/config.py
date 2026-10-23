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

    # Google Gemini, for the AI features: troubleshooting fallback, triage, report structuring and
    # assignment suggestions (app.ml.gemini). Empty key = all of them off, and the app works as before.
    gemini_api_key: str = ""
    # Gemini for every AI feature (app.ml.gemini): a fast "lite" model with thinking turned down,
    # usually about 1 s. If it hasn't answered after ai_hedge_after_seconds the backup model is
    # asked too, and the first answer wins. Empty backup = no hedging.
    ai_fallback_model: str = "gemini-3.5-flash-lite"
    ai_backup_model: str = "gemini-3.5-flash"
    ai_hedge_after_seconds: float = 3.0
    # Past this each feature gives up and does what it did before AI existed.
    ai_fallback_timeout_seconds: float = 8.0
    # Load the knowledge-base matching model at startup, so the first "Suggested fix" is instant.
    # Off in the tests.
    preload_troubleshooting_model: bool = True


@lru_cache
def get_settings() -> Settings:
    return Settings()
