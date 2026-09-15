from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Points at data team's SQLite output by default.
    # Can be overridden in .env with DATABASE_URL=sqlite:///./custom.db
    database_url: str = "sqlite:///../data/output/grid_data.db"
    cors_origin: str = "http://localhost:5173"
    port: int = 8000
    openweathermap_api_key: str = ""

    # Paths (relative to src/backend/)
    processed_data_dir: str = "../data/processed"
    model_path: str = "../data/output/gridhealth_model.pkl"


settings = Settings()
