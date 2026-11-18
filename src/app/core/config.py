"""Centralized application configuration using Pydantic Settings."""

from functools import lru_cache
from typing import Literal
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # Ambiente de Execução
    ENVIRONMENT: Literal["development", "test", "production"] = "development"
    DEBUG: bool = False
    APP_NAME: str = "RetailFlow E-Commerce"
    APP_HOST: str = "0.0.0.0"
    APP_PORT: int = 8000

    # Chave Secreta
    SECRET_KEY: str

    # Configuração de Banco de Dados
    DATABASE_URL: str
    TEST_DATABASE_URL: str | None = None

    # Parâmetros PostgreSQL
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DEV_DB: str = "retailflow_dev"
    POSTGRES_DEV_USER: str = "retailflow_dev_user"
    POSTGRES_DEV_PASSWORD: str = ""
    POSTGRES_TEST_DB: str = "retailflow_test"
    POSTGRES_TEST_USER: str = "retailflow_test_user"
    POSTGRES_TEST_PASSWORD: str = ""

    # Administrador Inicial
    INITIAL_ADMIN_EMAIL: str = "admin@retailflow.local"
    INITIAL_ADMIN_PASSWORD: str = ""

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key_strength(cls, v: str) -> str:
        if not v or len(v.strip()) < 32:
            raise ValueError(
                "SECRET_KEY deve ter no mínimo 32 caracteres para garantir a segurança criptográfica."
            )
        return v

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url_scheme(cls, v: str) -> str:
        if not v.startswith("postgresql+asyncpg://"):
            raise ValueError(
                "DATABASE_URL deve utilizar o driver assíncrono 'postgresql+asyncpg://'."
            )
        return v

    @model_validator(mode="after")
    def validate_environment_security(self) -> "Settings":
        # Bloquear valores padrão inseguros em produção
        if self.ENVIRONMENT == "production":
            if self.DEBUG:
                raise ValueError("DEBUG não pode estar ativo (True) em ambiente de produção.")
            if "change-this" in self.SECRET_KEY.lower():
                raise ValueError(
                    "SECRET_KEY contém valor de exemplo. Defina uma chave segura e aleatória em produção."
                )
            if not self.INITIAL_ADMIN_PASSWORD or "change_this" in self.INITIAL_ADMIN_PASSWORD.lower():
                raise ValueError(
                    "INITIAL_ADMIN_PASSWORD não pode conter valor de exemplo em produção."
                )
        return self


@lru_cache
def get_settings() -> Settings:
    """Retorna instância singleton com cache das configurações da aplicação."""
    return Settings()
