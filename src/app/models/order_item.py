"""Modelo OrderItem — itens de cada pedido."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.app.models.base import Base

if TYPE_CHECKING:
    from src.app.models.order import Order
    from src.app.models.product import Product


class OrderItem(Base):
    """Tabela de itens de pedido — UNIQUE(order_id, product_id)."""

    __tablename__ = "order_items"

    # Chave Primária
    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    # FK para Order
    order_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )

    # FK para Product — SET NULL para preservar histórico do pedido
    product_id: Mapped[UUID | None] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Snapshot do nome do produto no momento da compra
    product_name_snapshot: Mapped[str] = mapped_column(String(255), nullable=False)

    # Valores financeiros
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relacionamentos
    order: Mapped[Order] = relationship(
        "Order",
        back_populates="items",
        lazy="raise",
    )
    product: Mapped[Product | None] = relationship(
        "Product",
        back_populates="order_items",
        lazy="raise",
    )

    __table_args__ = (
        # Produto único por pedido
        UniqueConstraint("order_id", "product_id", name="uq_order_items_order_id_product_id"),
        # Consistência financeira: line_total = unit_price * quantity
        CheckConstraint(
            "line_total = unit_price * quantity",
            name="line_total_math",
        ),
        # Valores positivos
        CheckConstraint("unit_price > 0", name="unit_price_positive"),
        CheckConstraint("quantity > 0", name="quantity_positive"),
        CheckConstraint("line_total > 0", name="line_total_positive"),
    )

    def __repr__(self) -> str:
        return (
            f"<OrderItem id={self.id} order_id={self.order_id} "
            f"product_id={self.product_id} qty={self.quantity} total={self.line_total}>"
        )
