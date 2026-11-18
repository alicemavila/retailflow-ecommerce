"""Funções de segurança compartilhadas — hash de senhas com Argon2id.

Apenas hashing de senha está implementado nesta etapa.
Geração e validação de JWT são reservadas à Etapa 3.
"""

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

# Instância compartilhada do hasher Argon2id
_password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(plain_password: str) -> str:
    """Gera um hash Argon2id da senha em texto puro.

    Nunca armazena a senha original. Nunca imprime o hash em logs de produção.
    """
    if not plain_password or len(plain_password.strip()) < 8:
        raise ValueError("Senha deve ter no mínimo 8 caracteres.")
    return _password_hash.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto puro corresponde ao hash armazenado."""
    try:
        return _password_hash.verify(plain_password, hashed_password)
    except Exception:
        return False
