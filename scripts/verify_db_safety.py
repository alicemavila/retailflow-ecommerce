"""Script de salvaguarda e validação de segurança para o ambiente de testes.

Garante que nenhuma rotina de teste aponte acidentalmente para o banco de
desenvolvimento ou produção. NUNCA executa operações destrutivas (DROP/TRUNCATE).
"""

import os
import sys
from urllib.parse import urlparse

# Tenta utilizar make_url do SQLAlchemy para interpretação especializada de URLs
try:
    from sqlalchemy.engine import make_url
except ImportError:
    make_url = None

# Definições estritas de alvos autorizados para ambiente de testes
ALLOWED_TEST_DB_NAME = "retailflow_test"
ALLOWED_TEST_USERS = ("retailflow_test_user",)
ALLOWED_TEST_HOSTS = ("localhost", "127.0.0.1", "db", "retailflow_postgres", "postgres")


def sanitize_url(raw_url: str) -> str:
    """Retorna a URL de conexão com a senha estritamente mascarada por asteriscos."""
    if not raw_url:
        return "[NENHUMA URL FORNECIDA]"

    if make_url is not None:
        try:
            return make_url(raw_url).render_as_string(hide_password=True)
        except Exception:
            pass

    try:
        parsed = urlparse(raw_url)
        username = parsed.username or "anonymous"
        host = parsed.hostname or "unknown"
        port = f":{parsed.port}" if parsed.port else ""
        path = parsed.path
        scheme = parsed.scheme
        return f"{scheme}://{username}:***@{host}{port}{path}"
    except Exception:
        return "[URL NÃO PÔDE SER PARSEADA]"


def parse_connection_url(db_url: str) -> tuple[str, str, str]:
    """Extrai (database, username, host) da URL utilizando make_url ou urlparse como fallback."""
    if make_url is not None:
        try:
            url_obj = make_url(db_url)
            return (
                url_obj.database or "",
                url_obj.username or "",
                url_obj.host or "",
            )
        except Exception as exc:
            raise RuntimeError("VIOLAÇÃO DE SEGURANÇA: URL de banco inválida ou malformada.") from exc

    try:
        parsed = urlparse(db_url)
        return (
            (parsed.path or "").lstrip("/"),
            parsed.username or "",
            parsed.hostname or "",
        )
    except Exception as exc:
        raise RuntimeError("VIOLAÇÃO DE SEGURANÇA: URL de banco inválida ou malformada.") from exc


def assert_safe_test_environment(
    db_url: str,
    environment: str,
    allowed_db_name: str = ALLOWED_TEST_DB_NAME,
    allowed_users: tuple[str, ...] = ALLOWED_TEST_USERS,
    allowed_hosts: tuple[str, ...] = ALLOWED_TEST_HOSTS,
) -> None:
    """Valida se a conexão e o ambiente correspondem estritamente à base de testes.

    Valida obrigatoriamente:
    1. ENVIRONMENT exatamente igual a 'test'.
    2. Nome do banco exatamente igual a 'retailflow_test'.
    3. Host pertencente à lista de hosts autorizados para testes.
    4. Usuário pertencente à lista de usuários autorizados para testes.

    Lança RuntimeError com mensagem sanitizada se qualquer inconsistência for identificada.
    NUNCA imprime credenciais ou senhas em texto puro.
    """
    if not db_url:
        raise RuntimeError("VIOLAÇÃO DE SEGURANÇA: URL de conexão com o banco não fornecida.")

    if not environment or environment.strip().lower() != "test":
        raise RuntimeError(
            f"VIOLAÇÃO DE SEGURANÇA: Ambiente incorreto para testes! "
            f"Esperado: 'test' | Atual: '{environment}'."
        )

    db_name, user, host = parse_connection_url(db_url)

    # 1. Validação estrita do nome do banco de dados
    if db_name != allowed_db_name:
        raise RuntimeError(
            f"VIOLAÇÃO DE SEGURANÇA: O banco de testes deve ser estritamente '{allowed_db_name}'. "
            f"Banco alvo identificado: '{db_name}'. Operação abortada!"
        )

    # 2. Validação do usuário de banco
    if user not in allowed_users:
        raise RuntimeError(
            f"VIOLAÇÃO DE SEGURANÇA: O usuário de conexão para testes deve pertencer a {allowed_users}. "
            f"Usuário identificado: '{user}'. Operação abortada!"
        )

    # 3. Validação do host
    if host not in allowed_hosts:
        raise RuntimeError(
            f"VIOLAÇÃO DE SEGURANÇA: O host de testes deve pertencer a {allowed_hosts}. "
            f"Host identificado: '{host}'. Operação abortada!"
        )


def main() -> int:
    """Execução via CLI para verificação pré-teste."""
    env = os.getenv("ENVIRONMENT", "")
    test_db_url = os.getenv("TEST_DATABASE_URL", "")

    # Se TEST_DATABASE_URL não estiver explícita, verifica DATABASE_URL caso ENVIRONMENT=test
    if not test_db_url and env.lower() == "test":
        test_db_url = os.getenv("DATABASE_URL", "")

    sanitized = sanitize_url(test_db_url)

    try:
        assert_safe_test_environment(db_url=test_db_url, environment=env)
        print("✓ [SALVAGUARDA OK] Conexão e ambiente validados com sucesso para TESTES.")
        print(f"  Ambiente: {env}")
        print(f"  Alvo seguro: {sanitized}")
        return 0
    except RuntimeError as err:
        print(f"✗ [ERRO DE SALVAGUARDA] {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
