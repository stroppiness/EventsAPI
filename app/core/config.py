from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    db_user: str = Field(
        default="postgres",
        validation_alias=AliasChoices("POSTGRES_USERNAME", "POSTGRES_USER"),
    )
    db_password: str = Field(
        default="postgres",
        validation_alias=AliasChoices("POSTGRES_PASSWORD", "DB_PASSWORD"),
    )
    db_host: str = Field(
        default="localhost",
        validation_alias=AliasChoices("POSTGRES_HOST", "DB_HOST"),
    )
    db_port: int = Field(
        default=5432,
        validation_alias=AliasChoices("POSTGRES_PORT", "DB_PORT"),
    )
    db_name: str = Field(
        default="postgres",
        validation_alias=AliasChoices("POSTGRES_DATABASE_NAME", "POSTGRES_DB"),
    )

    provider_url: str = "http://student-system-events-provider-web.student-system-events-provider.svc:8000"
    api_key: str = ''

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )


settings = Settings()
