"""Preprocessing audio dengan FFmpeg (Task 5).

Konversi input audio apa pun (webm/ogg/wav/m4a) menjadi PCM float32 mono 16 kHz —
format standar untuk faster-whisper & wav2vec2. Hanya butuh biner `ffmpeg` + numpy.
"""
from __future__ import annotations

import shutil
import subprocess
import wave

import numpy as np

TARGET_SR = 16000


class AudioError(RuntimeError):
    pass


def ffmpeg_available() -> bool:
    return shutil.which("ffmpeg") is not None


def to_mono16k(data: bytes) -> np.ndarray:
    """Decode bytes audio -> np.float32 mono 16 kHz, rentang [-1, 1]."""
    if not ffmpeg_available():
        raise AudioError("ffmpeg tidak ditemukan di PATH")
    proc = subprocess.run(
        ["ffmpeg", "-nostdin", "-i", "pipe:0", "-ar", str(TARGET_SR),
         "-ac", "1", "-f", "f32le", "pipe:1"],
        input=data,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0 or not proc.stdout:
        raise AudioError(f"ffmpeg gagal decode audio: {proc.stderr.decode()[-300:]}")
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()


def duration_seconds(samples: np.ndarray, sr: int = TARGET_SR) -> float:
    return round(len(samples) / sr, 3)


def write_wav_int16(path: str, samples: np.ndarray, sr: int = TARGET_SR) -> None:
    """Simpan float32 [-1,1] sebagai WAV PCM 16-bit (pakai stdlib `wave`)."""
    clipped = np.clip(samples, -1.0, 1.0)
    pcm = (clipped * 32767.0).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(pcm.tobytes())
