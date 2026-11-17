from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    supabase_jwt_secret: str = ""
    web_origin: str = "http://localhost:3000"
    max_file_bytes: int = 10 * 1024 * 1024
    max_pdfs: int = 200
    max_rows: int = 50_000
    firm_daily_tokens: int = 200_000
    firm_daily_inr: str = "50"
