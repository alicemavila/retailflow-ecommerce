#!/usr/bin/env bash
# ==============================================================================
# Script de Inicialização dos Bancos PostgreSQL (RetailFlow)
# Executado automaticamente pelo Docker entrypoint apenas em volumes vazios.
# ==============================================================================

set -e

echo "==> [PostgreSQL Init] Iniciando provisionamento dos bancos e usuários do RetailFlow..."

# Validação estrita de variáveis obrigatórias para evitar inicialização com senhas inseguras
if [ -z "$POSTGRES_DEV_PASSWORD" ]; then
    echo "==> [PostgreSQL Init ERRO] A variável POSTGRES_DEV_PASSWORD é obrigatória e não foi informada." >&2
    exit 1
fi

if [ -z "$POSTGRES_TEST_PASSWORD" ]; then
    echo "==> [PostgreSQL Init ERRO] A variável POSTGRES_TEST_PASSWORD é obrigatória e não foi informada." >&2
    exit 1
fi

DEV_DB="${POSTGRES_DEV_DB:-retailflow_dev}"
DEV_USER="${POSTGRES_DEV_USER:-retailflow_dev_user}"
DEV_PASSWORD="$POSTGRES_DEV_PASSWORD"

TEST_DB="${POSTGRES_TEST_DB:-retailflow_test}"
TEST_USER="${POSTGRES_TEST_USER:-retailflow_test_user}"
TEST_PASSWORD="$POSTGRES_TEST_PASSWORD"

# 1. Criação do Usuário e Banco de Desenvolvimento
echo "==> [PostgreSQL Init] Criando usuário e banco de desenvolvimento: '$DEV_DB' (user: '$DEV_USER')..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DEV_USER') THEN
            CREATE USER "$DEV_USER" WITH PASSWORD '$DEV_PASSWORD';
        END IF;
    END
    \$\$;

    SELECT 'CREATE DATABASE "$DEV_DB" OWNER "$DEV_USER"'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DEV_DB')\gexec

    REVOKE ALL ON DATABASE "$DEV_DB" FROM PUBLIC;
    GRANT CONNECT ON DATABASE "$DEV_DB" TO "$DEV_USER";
EOSQL

# Conceder permissões estritas no schema public do banco de desenvolvimento
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$DEV_DB" <<-EOSQL
    REVOKE ALL ON SCHEMA public FROM PUBLIC;
    GRANT ALL ON SCHEMA public TO "$DEV_USER";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "$DEV_USER";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "$DEV_USER";
EOSQL

# 2. Criação do Usuário e Banco de Testes
echo "==> [PostgreSQL Init] Criando usuário e banco de testes: '$TEST_DB' (user: '$TEST_USER')..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$TEST_USER') THEN
            CREATE USER "$TEST_USER" WITH PASSWORD '$TEST_PASSWORD';
        END IF;
    END
    \$\$;

    SELECT 'CREATE DATABASE "$TEST_DB" OWNER "$TEST_USER"'
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$TEST_DB')\gexec

    REVOKE ALL ON DATABASE "$TEST_DB" FROM PUBLIC;
    GRANT CONNECT ON DATABASE "$TEST_DB" TO "$TEST_USER";
EOSQL

# Conceder permissões estritas no schema public do banco de testes
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$TEST_DB" <<-EOSQL
    REVOKE ALL ON SCHEMA public FROM PUBLIC;
    GRANT ALL ON SCHEMA public TO "$TEST_USER";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "$TEST_USER";
    ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "$TEST_USER";
EOSQL

echo "==> [PostgreSQL Init] Provisionamento concluído com sucesso e privilégios isolados!"
