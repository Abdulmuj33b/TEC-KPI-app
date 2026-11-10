from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
    )

    database_url: str = (
        "postgresql://tec_kpi:development_only@db:5432/tec_kpi"
    )
    jwt_secret_key: str
    access_token_minutes: int = 30


settings = Settings()
