"""Modelo Cart — carrinho de compras (um por usuário)."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, func, text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.cart_item import CartItem
    from src.app.models.user import User


class Cart(Base):
    """Tabela de carrinhos — um carrinho por usuário (UNIQUE em user_id)."""

    __tablename__ = "carts"

    # Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # FK para User — carrinho é excluído se usuário for excluído
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # garante um carrinho por usuário (sem índice ix redundante)
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

    # Relacionamentos
    user: Mapped[User] = relationship(
        "User",
        back_populates="cart",
        lazy="raise",
    )
    items: Mapped[list[CartItem]] = relationship(
        "CartItem",
        back_populates="cart",
        lazy="raise",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Cart id={self.id} user_id={self.user_id}>"
