"""Alembic environment configuration for async SQLAlchemy migrations."""

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context
from src.app.core.config import get_settings

# Importar todos os modelos para que Base.metadata seja populado
import src.app.models  # noqa: F401 — carrega todos os modelos via __init__.py
from src.app.models.base import Base

# Objeto de configuração do Alembic
config = context.config

# Interpretação do arquivo de log
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Configuração dinâmica da URL de conexão a partir do settings
settings = get_settings()

# Suporte a --x-arg url=<custom_url> para migrações no banco de testes
x_args = context.get_x_argument(as_dictionary=True)
db_url = x_args.get("url") or settings.DATABASE_URL

config.set_main_option("sqlalchemy.url", db_url)

# Metadados reais dos modelos para autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Executa migrações no modo 'offline' sem conexão ativa com o banco."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        # Renderiza CREATE INDEX para índices funcionais/parciais
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Função síncrona de execução das migrações, invocada dentro de run_sync."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        render_as_batch=False,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Cria engine assíncrona e executa as migrações via run_sync."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Executa migrações no modo 'online' utilizando loop de eventos assíncrono."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
