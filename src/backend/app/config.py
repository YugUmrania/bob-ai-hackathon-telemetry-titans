from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import dotenv_values


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        protected_namespaces=(),
    )

    # Points at data team's SQLite output by default.
    # Can be overridden in .env with DATABASE_URL=sqlite:///./custom.db
    database_url: str = "sqlite:///../data/output/grid_data.db"
    cors_origin: str = "http://localhost:5173"
    port: int = 8000
    openweathermap_api_key: str = ""

    # Paths (relative to src/backend/)
    processed_data_dir: str = "../data/processed"
    model_path: str = "../data/output/gridhealth_model.pkl"

    @model_validator(mode="after")
    def _load_owm_key_from_data_env(self) -> "Settings":
        """Fallback: read ONLY the OWM key from src/data/.env.

        We intentionally do NOT scan that file as a whole (it also contains a
        placeholder DATABASE_URL that would override our sqlite default).
        """
        if self.openweathermap_api_key:
            return self
        data_env = Path(__file__).resolve().parents[2] / "data" / ".env"
        if data_env.is_file():
            vals = dotenv_values(data_env)
            self.openweathermap_api_key = vals.get("OPENWEATHERMAP_API_KEY", "") or ""
        return self


settings = Settings()