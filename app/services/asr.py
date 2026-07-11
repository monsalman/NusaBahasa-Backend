"""ASR bahasa Indonesia dengan faster-whisper (Task 6, CPU-only).

Model di-load lazy sekali (singleton). Bila deps/model belum ada, pemanggil
mendapat AIUnavailable agar bisa dijadikan HTTP 503 yang informatif.
"""
from __future__ import annotations

import numpy as np

from app.core.config import settings
from app.services.audio_utils import to_mono16k

_model = None


class AIUnavailable(RuntimeError):
    pass


def _get_model():
    global _model
    if _model is None:
        try:
            from faster_whisper import WhisperModel
        except ImportError as e:
            raise AIUnavailable(
                "faster-whisper belum terpasang. Jalankan: pip install -r requirements-ai.txt"
            ) from e
        _model = WhisperModel(
            settings.ASR_MODEL,
            device="cpu",
            compute_type=settings.ASR_COMPUTE_TYPE,
            download_root=settings.MODELS_DIR,
        )
    return _model


def transcribe(audio_bytes: bytes, language: str = "id") -> str:
    samples: np.ndarray = to_mono16k(audio_bytes)
    model = _get_model()
    segments, _info = model.transcribe(samples, language=language, vad_filter=True)
    return " ".join(seg.text.strip() for seg in segments).strip()
