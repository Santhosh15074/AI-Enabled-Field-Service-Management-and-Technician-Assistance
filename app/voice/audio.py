"""Turning whatever a phone recorded into the 16 kHz mono samples speech models expect.

Chrome on Android records WebM/Opus and iPhones record MP4/AAC, so decoding goes through PyAV
(FFmpeg's libraries, bundled in its wheel; nothing to install separately). The file's own
contents decide the format, never the content type the browser claimed.
"""

from pathlib import Path

import av
import numpy as np

SAMPLE_RATE = 16_000


class AudioError(ValueError):
    """The file isn't audio this server can decode."""


def decode(path: Path) -> np.ndarray:
    """The recording as float32 samples in [-1, 1], mono, at SAMPLE_RATE."""
    resampler = av.AudioResampler(format="flt", layout="mono", rate=SAMPLE_RATE)
    chunks: list[np.ndarray] = []
    try:
        with av.open(str(path)) as container:
            if not container.streams.audio:
                raise AudioError("The file has no audio in it.")
            for frame in container.decode(audio=0):
                chunks.extend(f.to_ndarray().reshape(-1) for f in resampler.resample(frame))
            chunks.extend(f.to_ndarray().reshape(-1) for f in resampler.resample(None))
    except av.FFmpegError as error:
        raise AudioError(f"The recording couldn't be read ({error}).") from error
    if not chunks:
        raise AudioError("The recording is empty.")
    return np.concatenate(chunks).astype(np.float32)
