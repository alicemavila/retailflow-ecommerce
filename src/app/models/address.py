"""Modelo Address — endereços dos usuários."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.user import User


class Address(Base):
    """Tabela de endereços vinculados a usuários (11 colunas aprovadas no planejamento)."""

    __tablename__ = "addresses"

    # 1. Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # 2. Chave Estrangeira para User
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 3. Logradouro
    street: Mapped[str] = mapped_column(String(255), nullable=False)

    # 4. Número
    number: Mapped[str] = mapped_column(String(50), nullable=False)

    # 5. Complemento
    complement: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # 6. Bairro
    neighborhood: Mapped[str] = mapped_column(String(100), nullable=False)

    # 7. Cidade
    city: Mapped[str] = mapped_column(String(100), nullable=False)

    # 8. Estado / UF
    state: Mapped[str] = mapped_column(String(2), nullable=False)

    # 9. CEP
    zip_code: Mapped[str] = mapped_column(String(20), nullable=False)

    # 10. Endereço padrão
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=text("false")
    )

    # 11. Data de criação
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relacionamento
    user: Mapped[User] = relationship(
        "User",
        back_populates="addresses",
        lazy="raise",
    )

    __table_args__ = (
        Index("ix_addresses_user_id", "user_id"),
        Index("ix_addresses_zip_code", "zip_code"),
        Index(
            "uq_addresses_user_id_is_default",
            "user_id",
            unique=True,
            postgresql_where=text("is_default = true"),
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Address id={self.id} user_id={self.user_id} "
            f"city={self.city!r} default={self.is_default}>"
        )
