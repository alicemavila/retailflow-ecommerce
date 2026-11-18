"""Modelo CartItem — itens do carrinho de compras."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
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
    """Tabela de itens do carrinho (5 colunas aprovadas no planejamento)."""

    __tablename__ = "cart_items"

    # 1. Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # 2. FK para Cart
    cart_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("carts.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 3. FK para Product
    product_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
    )

    # 4. Quantidade
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)

    # 5. Timestamp de criação (sem updated_at conforme planejamento consolidado)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
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
        UniqueConstraint("cart_id", "product_id", name="uq_cart_items_cart_id_product_id"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        Index("ix_cart_items_product_id", "product_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<CartItem id={self.id} cart_id={self.cart_id} "
            f"product_id={self.product_id} qty={self.quantity}>"
        )
