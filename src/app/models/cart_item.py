"""Modelo CartItem — itens do carrinho de compras."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.cart import Cart
    from src.app.models.product import Product


class CartItem(Base):
    """Tabela de itens do carrinho — UNIQUE(cart_id, product_id)."""

    __tablename__ = "cart_items"

    # Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # FK para Cart
    cart_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # FK para Product — SET NULL não aplicável aqui; item é removido se produto for deletado
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Quantidade
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

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
    cart: Mapped[Cart] = relationship(
        "Cart",
        back_populates="items",
        lazy="raise",
    )
    product: Mapped[Product] = relationship(
        "Product",
        back_populates="cart_items",
        lazy="raise",
    )

    __table_args__ = (
        # Um produto por carrinho (sem duplicidade)
        UniqueConstraint("cart_id", "product_id", name="uq_cart_items_cart_id_product_id"),
        # Quantidade deve ser positiva
        CheckConstraint("quantity > 0", name="quantity_positive"),
    )

    def __repr__(self) -> str:
        return (
            f"<CartItem id={self.id} cart_id={self.cart_id} "
            f"product_id={self.product_id} qty={self.quantity}>"
        )
