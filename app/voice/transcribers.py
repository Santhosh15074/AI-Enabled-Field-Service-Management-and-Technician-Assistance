"""Speech-to-text engines. One interface, chosen by Settings.stt_engine, so the local model used
today can be swapped for a hosted one (Sarvam) without touching anything that calls it.

Only "local" exists so far: faster-whisper (Whisper on CTranslate2, int8 on the CPU). It was picked
over plain transformers after testing both on this project's laptop: it was about three times
faster, its voice-activity filter returns nothing for silence where plain Whisper invented a loop of
Tamil words, and its repetition guards stop the runaway output Whisper otherwise produces when the
forced language doesn't match the speech. Even so it runs at about three times real time on a
laptop CPU — fine for development, too slow for real shops.

The first transcription after a restart downloads the model if it isn't cached yet, then loads it.
"""

import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Protocol

import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class Transcript:
    text: str
    engine: str  # recorded on the voice note, so a transcript can always be traced to what made it


class Transcriber(Protocol):
    name: str

    def transcribe(self, audio: np.ndarray) -> Transcript: ...


class LocalWhisper:
    def __init__(self, model: str, language: str):
        self.model_name = model
        # None lets Whisper detect the language per recording, which matters for Tanglish: forcing
        # Tamil on a mostly-English note produced nonsense in testing.
        self.language = language or None
        self.name = f"local:faster-whisper/{model}"
        self._model = None

    def _load(self):
        if self._model is None:
            from faster_whisper import WhisperModel  # deferred until the first voice note

            logger.info("Loading speech-to-text model %s", self.model_name)
            self._model = WhisperModel(self.model_name, device="cpu", compute_type="int8")
        return self._model

    def transcribe(self, audio: np.ndarray) -> Transcript:
        segments, _info = self._load().transcribe(
            audio,
            language=self.language,
            task="transcribe",
            vad_filter=True,  # skip silence instead of inventing words for it
            condition_on_previous_text=False,  # one bad segment can't drag the rest into a loop
        )
        text = " ".join(segment.text.strip() for segment in segments)
        return Transcript(text=text.strip(), engine=self.name)


@lru_cache(maxsize=1)
def _local(model: str, language: str) -> LocalWhisper:
    return LocalWhisper(model, language)


def get_transcriber() -> Transcriber:
    settings = get_settings()
    if settings.stt_engine == "local":
        return _local(settings.stt_local_model, settings.stt_language)
    raise ValueError(f"Unknown STT_ENGINE {settings.stt_engine!r}; the only engine so far is 'local'.")
