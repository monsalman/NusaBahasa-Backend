"""TTS dengan MMS-TTS (Meta) — Task 7, CPU-only, cache-first.

Model VITS per bahasa (facebook/mms-tts-ind, facebook/mms-tts-tnt).
Hasil di-cache sebagai WAV di disk agar tidak menghitung ulang.
"""
from __future__ import annotations

import hashlib
import os

from app.core.config import settings
from app.services.audio_utils import write_wav_int16

_models: dict[str, object] = {}
_tokenizers: dict[str, object] = {}


class AIUnavailable(RuntimeError):
    pass


def _load(lang: str):
    if lang not in _models:
        try:
            from transformers import AutoTokenizer, VitsModel
        except ImportError as e:
            raise AIUnavailable(
                "transformers/torch belum terpasang. Jalankan: pip install -r requirements-ai.txt"
            ) from e
        model_id = settings.TTS_MODEL_TEMPLATE.format(lang=lang)
        _tokenizers[lang] = AutoTokenizer.from_pretrained(model_id, cache_dir=settings.MODELS_DIR)
        m = VitsModel.from_pretrained(model_id, cache_dir=settings.MODELS_DIR)
        m.eval()
        _models[lang] = m
    return _models[lang], _tokenizers[lang]


def _cache_path(text: str, lang: str) -> str:
    os.makedirs(settings.TTS_CACHE_DIR, exist_ok=True)
    key = hashlib.sha1(f"{lang}:{text}".encode()).hexdigest()
    return os.path.join(settings.TTS_CACHE_DIR, f"{lang}-{key}.wav")


def synthesize(text: str, lang: str) -> str:
    """Kembalikan path WAV (cache-first)."""
    path = _cache_path(text, lang)
    if os.path.exists(path):
        return path

    import torch

    model, tokenizer = _load(lang)
    inputs = tokenizer(text, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs).waveform  # (1, n)
    samples = output.squeeze(0).cpu().numpy()
    sr = model.config.sampling_rate
    write_wav_int16(path, samples, sr=sr)
    return path
