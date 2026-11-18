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
    """Tabela de endereços vinculados a usuários."""

    __tablename__ = "addresses"

    # Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # Chave Estrangeira para User
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Campos de endereço
    label: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recipient_name: Mapped[str] = mapped_column(String(255), nullable=False)
    street: Mapped[str] = mapped_column(String(255), nullable=False)
    number: Mapped[str] = mapped_column(String(20), nullable=False)
    complement: Mapped[str | None] = mapped_column(String(100), nullable=True)
    neighborhood: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False)
    zip_code: Mapped[str] = mapped_column(String(10), nullable=False)
    country: Mapped[str] = mapped_column(
        String(3), nullable=False, server_default=text("'BRA'")
    )

    # Endereço padrão
    is_default: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relacionamento
    user: Mapped[User] = relationship(
        "User",
        back_populates="addresses",
        lazy="raise",
    )

    __table_args__ = (
        # Índice de busca por usuário
        Index("ix_addresses_user_id", "user_id"),
        # Índice único PARCIAL: só um endereço padrão por usuário
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
