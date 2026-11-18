"""Base declarativa centralizada para todos os modelos SQLAlchemy.

Convenção de nomenclatura:
  pk   = pk_%(table_name)s
  fk   = fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s
  uq   = uq_%(table_name)s_%(column_0_name)s
  ck   = ck_%(table_name)s_%(constraint_name)s
  ix   = ix_%(table_name)s_%(column_0_name)s
"""

from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

NAMING_CONVENTION: dict[str, str] = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "ix": "ix_%(table_name)s_%(column_0_name)s",
}


class Base(DeclarativeBase):
    """Classe base declarativa única para todos os modelos do RetailFlow."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
