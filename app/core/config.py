from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql+psycopg2://nusa:nusa@localhost:5432/nusabahasa"
    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 hari
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:5174"

    # R2 (dipakai router audio/ai milik Salman)
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET: str = "nusabahasa"
    R2_PUBLIC_BASE: str = ""  # custom domain / public URL R2 untuk playback (opsional)

    # --- AI (CPU-only) ---
    MODELS_DIR: str = "ai_models"         # cache bobot (volume; gitignored)
    TTS_CACHE_DIR: str = "ai_models/tts_cache"
    ASR_MODEL: str = "small"              # faster-whisper: tiny|base|small|medium
    ASR_COMPUTE_TYPE: str = "int8"        # int8 hemat memori di CPU
    SCORING_MODEL: str = "facebook/wav2vec2-base"   # hidden size 768 (cocok Vector(768))
    TTS_MODEL_TEMPLATE: str = "facebook/mms-tts-{lang}"  # mms-tts-ind, mms-tts-tnt
    SCORE_PASS_THRESHOLD: float = 0.6     # ambang label "Bagus"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]

    @property
    def r2_endpoint(self) -> str:
        return f"https://{self.R2_ACCOUNT_ID}.r2.cloudflarestorage.com"

    @property
    def r2_configured(self) -> bool:
        return bool(self.R2_ACCOUNT_ID and self.R2_ACCESS_KEY_ID and self.R2_SECRET_ACCESS_KEY)


settings = Settings()
