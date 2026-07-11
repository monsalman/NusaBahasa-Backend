"""Pronunciation scoring language-agnostic (Task 6/7, CPU-only).

wav2vec2 embeddings (mean-pooled last_hidden_state) + cosine similarity.
Audio penutur asli vs audio pembelajar → skor [0..1] + label.
"""
from __future__ import annotations

import numpy as np

from app.core.config import settings
from app.services.audio_utils import to_mono16k

_model = None
_processor = None


class AIUnavailable(RuntimeError):
    pass


def _load():
    global _model, _processor
    if _model is None:
        try:
            import torch  # noqa: F401
            from transformers import Wav2Vec2Model, Wav2Vec2Processor
        except ImportError as e:
            raise AIUnavailable(
                "transformers/torch belum terpasang. Jalankan: pip install -r requirements-ai.txt"
            ) from e
        _processor = Wav2Vec2Processor.from_pretrained(
            settings.SCORING_MODEL, cache_dir=settings.MODELS_DIR
        )
        _model = Wav2Vec2Model.from_pretrained(
            settings.SCORING_MODEL, cache_dir=settings.MODELS_DIR
        )
        _model.eval()
    return _model, _processor


def embed(audio_bytes: bytes) -> list[float]:
    """Hasilkan embedding 768-dim (float) dari audio."""
    import torch

    samples = to_mono16k(audio_bytes)
    model, processor = _load()
    inputs = processor(samples, sampling_rate=16000, return_tensors="pt")
    with torch.no_grad():
        out = model(**inputs)
    vec = out.last_hidden_state.mean(dim=1).squeeze(0)  # (768,)
    vec = torch.nn.functional.normalize(vec, dim=0)      # unit vector
    return vec.cpu().numpy().astype("float32").tolist()


def cosine(a: list[float] | np.ndarray, b: list[float] | np.ndarray) -> float:
    a = np.asarray(a, dtype="float32")
    b = np.asarray(b, dtype="float32")
    denom = (np.linalg.norm(a) * np.linalg.norm(b)) or 1e-9
    return float(np.dot(a, b) / denom)


def score_against(reference_embedding: list[float], learner_audio: bytes) -> dict:
    learner = embed(learner_audio)
    sim = cosine(reference_embedding, learner)
    # Embedding sudah dinormalisasi; untuk ucapan cosine umumnya positif.
    # Pakai cosine langsung (clamp ke [0,1]) agar lebih diskriminatif.
    score = max(0.0, min(1.0, sim))
    label = "Bagus" if score >= settings.SCORE_PASS_THRESHOLD else "Ulangi"
    return {"score": round(score, 3), "label": label}
