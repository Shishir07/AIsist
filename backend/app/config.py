from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Anthropic
    anthropic_api_key: str

    # Deepgram
    deepgram_api_key: str

    # Google
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str = "http://localhost:8000/auth/google/callback"

    # Database
    database_url: str = "postgresql+asyncpg://aisist:aisist_secret@db:5432/aisist"
    # Sync URL for Alembic
    @property
    def sync_database_url(self) -> str:
        return self.database_url.replace("+asyncpg", "+psycopg")

    # App
    app_secret_key: str = "change_this_to_a_random_string"
    environment: str = "development"

    # Timezone
    app_timezone: str = "America/Vancouver"

    # Voice
    deepgram_tts_model: str = "aura-asteria-en"   # Natural female voice
    deepgram_stt_model: str = "nova-2"             # Best accuracy STT


settings = Settings()
